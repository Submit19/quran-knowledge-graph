"""
Regression: chat._tool_cache_get reads `now = time.time()` OUTSIDE the lock.

The expiry check `if expires < now: ...` is inside the lock, but `now` is
captured before the lock is acquired. If a competing thread holds the lock
long enough for the entry to age past TTL, the stale `now` makes the
expired entry look fresh — and a stale value is returned.

To trigger the race deterministically:
  1. Put an entry with very short TTL.
  2. Acquire the cache lock in the test thread, holding it.
  3. Kick off a worker thread that calls `_tool_cache_get(key)`. With the
     buggy code, the worker reads `now = time.time()` immediately, then
     blocks on the lock.
  4. Sleep in the test thread past the TTL, then release the lock.
  5. The worker now acquires the lock, finds the (in real time) expired
     entry, but its stale `now` makes the comparison say "not expired" —
     and it returns the stale value.

Fix: move `now = time.time()` inside the lock so the read-then-validate
is genuinely atomic w.r.t. wall-clock progress while blocked.
"""

from __future__ import annotations

import threading
import time

import pytest

import chat


@pytest.fixture(autouse=True)
def _clean_cache_state():
    """Reset cache TTL + contents around each test, restore afterwards."""
    saved_ttl = chat._TOOL_CACHE_TTL
    saved_max = chat._TOOL_CACHE_MAX
    with chat._TOOL_CACHE_LOCK:
        chat._TOOL_CACHE.clear()
        for k in chat._TOOL_CACHE_STATS:
            chat._TOOL_CACHE_STATS[k] = 0
    yield
    chat._TOOL_CACHE_TTL = saved_ttl
    chat._TOOL_CACHE_MAX = saved_max
    with chat._TOOL_CACHE_LOCK:
        chat._TOOL_CACHE.clear()


@pytest.mark.xfail(
    strict=True,
    reason="Bug C: _tool_cache_get reads `now` outside the lock; Phase 3b fix",
)
def test_get_does_not_return_stale_entry_under_lock_contention():
    """The headline race: lock-blocked get must not return an expired entry."""
    chat._TOOL_CACHE_TTL = 0.05  # 50ms TTL

    chat._tool_cache_put("k", "v_stale")
    assert chat._tool_cache_get("k") == "v_stale", "sanity: fresh entry is readable"

    result_box: dict = {}

    def worker():
        # Buggy code captures `now = time.time()` HERE, before the lock.
        # Then it tries to acquire the lock — and blocks while the test
        # thread holds it. Time advances past TTL during the block.
        result_box["value"] = chat._tool_cache_get("k")

    # Acquire the lock from the test thread, then start the worker.
    chat._TOOL_CACHE_LOCK.acquire()
    t = threading.Thread(target=worker, daemon=True)
    t.start()

    # Give the worker time to enter _tool_cache_get and snapshot `now`,
    # then block on the lock. The exact sleep here is pragmatic — long
    # enough for the worker to make progress past the time.time() call,
    # short enough that we still hold the lock when it tries to acquire.
    time.sleep(0.02)

    # Now sleep PAST the TTL while still holding the lock. The entry is
    # now expired in real time.
    time.sleep(0.10)

    chat._TOOL_CACHE_LOCK.release()
    t.join(timeout=1.0)

    assert not t.is_alive(), "worker did not finish"
    assert result_box.get("value") is None, (
        f"stale entry returned under lock contention: {result_box.get('value')!r}"
    )


def test_get_returns_none_when_entry_aged_past_ttl_without_contention():
    """Single-threaded baseline: aged entry returns None. Pins existing behaviour."""
    chat._TOOL_CACHE_TTL = 0.05
    chat._tool_cache_put("k", "v_short")
    time.sleep(0.1)
    assert chat._tool_cache_get("k") is None


def test_get_returns_value_when_entry_fresh():
    """Sanity pin: fresh entry within TTL is returned."""
    chat._TOOL_CACHE_TTL = 5.0
    chat._tool_cache_put("k", "v_fresh")
    assert chat._tool_cache_get("k") == "v_fresh"

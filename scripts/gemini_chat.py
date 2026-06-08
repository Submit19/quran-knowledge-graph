"""Tiny Gemini smoke-test CLI.

Verifies GEMINI_API_KEY + network + the chosen model end-to-end, reusing the
same shared_agent._gemini_chat path the app uses.

Usage:
    python scripts/gemini_chat.py "respond OK"
    python scripts/gemini_chat.py "respond OK" --model gemini-2.0-flash

Exits 0 and prints the model's reply on success; exits 1 with the error on
failure (e.g. a 429 rate limit — wait 60s and retry).
"""

import argparse
import os
import sys
from pathlib import Path

# Load .env (same minimal parser app_free uses) before importing shared_agent.
_root = Path(__file__).resolve().parent.parent
_env = _root / ".env"
if _env.exists():
    for line in _env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            if v.strip():
                os.environ.setdefault(k.strip(), v.strip())

sys.path.insert(0, str(_root))
from shared_agent import _gemini_chat  # noqa: E402

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def main() -> int:
    ap = argparse.ArgumentParser(description="Gemini smoke-test CLI")
    ap.add_argument("prompt", help="user prompt to send")
    ap.add_argument("--model", default=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    ap.add_argument("--system", default="You are a concise assistant.")
    args = ap.parse_args()

    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        print("ERROR: GEMINI_API_KEY not set (.env or environment).", file=sys.stderr)
        return 1

    try:
        out = _gemini_chat(
            api_key=key,
            url=GEMINI_URL,
            model=args.model,
            system=args.system,
            messages=[{"role": "user", "content": args.prompt}],
        )
    except Exception as e:
        body = ""
        if hasattr(e, "response") and e.response is not None:
            try:
                body = f" | {e.response.text[:300]}"
            except Exception:
                pass
        print(f"ERROR: {e.__class__.__name__}: {e}{body}", file=sys.stderr)
        return 1

    reply = out["message"]["content"]
    print(
        reply if reply else "(no text — tool_calls: %s)" % out["message"]["tool_calls"]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

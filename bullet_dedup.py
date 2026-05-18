"""Post-stream verbatim-duplicate suppression for verse-explanation bullets.

The local-Ollama agent (qwen3:14b in particular) sometimes re-emits the
same `**[X:Y]** – "<quote>"` bullet inside multiple H2 sections of one
answer. The 2026-05-17 baseline measured a 31% verbatim-bug rate on
thematic ABSTRACT questions and confirmed every flagged duplicate was
character-identical on the first ~150 chars of the explanation — no
near-verbatim cases that strict-identity dedup would miss
(`data/research/repetition_bug_baseline_2026-05-17/REPORT.md`).

This module is a pure function: in goes the buffered streamed answer
text, out comes (cleaned_text, suppressed_verse_ids). Stateless w.r.t.
the rest of the system — one instance per request, no I/O.

Signature is `(verse_id, normalised_first_150_chars_of_rest_of_line)`.
"Rest of line" means everything after the `**[X:Y]**` citation marker,
stripped of surrounding whitespace. That is enough to distinguish
"same verse, same canonical quote" (suppress) from "same verse, fresh
angle" (preserve).
"""

from __future__ import annotations

import re

_BULLET_LINE = re.compile(
    # Lines that look like a citation bullet:
    #   - **[4:17]** – *"..."*
    #   * **[4:17]** ...
    #   | **[2:172]** | "..." | ... |     (table row)
    # The leading marker (-, *, or |) is required so we don't dedup
    # bold citations that appear inside flowing prose.
    r'^\s*[-*|]\s+\*\*\[(?P<verse>\d+:\d+)\]\*\*(?P<rest>.*)$'
)


class BulletDedup:
    """Per-request seen-signature set; call ``filter_text`` once at end of stream."""

    def __init__(self) -> None:
        # signature -> first line index (kept for potential future
        # debug logging, not used in the suppression decision today).
        self._seen: dict[tuple[str, str], int] = {}

    def filter_text(self, full_text: str) -> tuple[str, list[str]]:
        """Strip verbatim-duplicate citation bullets from ``full_text``.

        Returns ``(cleaned_text, suppressed_verses)``. A bullet is
        considered a duplicate iff a prior line in the same ``full_text``
        had:

        1. The exact same verse id inside `**[X:Y]**`, AND
        2. The same first 150 chars of the post-marker text after
           stripping surrounding whitespace.

        Non-bullet lines and bullets without a recognisable verse
        citation pass through unchanged.
        """
        if not full_text:
            return "", []

        suppressed: list[str] = []
        out_lines: list[str] = []
        for idx, line in enumerate(full_text.split("\n")):
            m = _BULLET_LINE.match(line)
            if m is None:
                out_lines.append(line)
                continue
            verse_id = m.group("verse")
            rest_norm = (m.group("rest") or "").strip()[:150]
            key = (verse_id, rest_norm)
            if key in self._seen:
                suppressed.append(verse_id)
                continue
            self._seen[key] = idx
            out_lines.append(line)
        return "\n".join(out_lines), suppressed

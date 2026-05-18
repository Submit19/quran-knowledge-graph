"""Guard the Arabic-root-augmentation directive in the system prompts.

Future edits to the prompt files must not silently delete the section that
tells the agent to call search_arabic_root and weave the canonical root
anchor into thematic answers. This is a pure-text test — no LLM call.
"""

from pathlib import Path

import pytest

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

# At minimum 5 of these canonical anchors must remain in the prompt.
# The full set lives in the prompt itself; this list catches accidental
# bulk deletion without pinning every anchor (so the operator can refine
# the list without breaking the test).
REQUIRED_ANCHORS = ["sabr", "shukr", "tawba", "rahma", "ikhlas"]

PROMPT_FILES = [
    PROMPTS_DIR / "system_prompt_free.txt",
    PROMPTS_DIR / "system_prompt.txt",
]


@pytest.mark.parametrize("prompt_path", PROMPT_FILES, ids=lambda p: p.name)
def test_prompt_contains_arabic_root_augmentation_section(prompt_path: Path) -> None:
    assert prompt_path.exists(), f"Prompt file missing: {prompt_path}"
    text = prompt_path.read_text(encoding="utf-8")
    lowered = text.lower()

    assert "arabic root augmentation" in lowered, (
        f"{prompt_path.name} is missing the 'Arabic root augmentation' "
        "section header — was it deleted by accident?"
    )

    assert "search_arabic_root" in text, (
        f"{prompt_path.name} no longer mentions search_arabic_root in the "
        "augmentation section — the agent will not know to call it."
    )

    present = [a for a in REQUIRED_ANCHORS if a in lowered]
    assert len(present) >= 5, (
        f"{prompt_path.name} only contains {len(present)} of the required "
        f"canonical anchors {REQUIRED_ANCHORS} (found: {present}). Restore "
        "the anchor table."
    )


@pytest.mark.parametrize("prompt_path", PROMPT_FILES, ids=lambda p: p.name)
def test_prompt_mandates_search_arabic_root_call(prompt_path: Path) -> None:
    """The directive must read as a mandate, not a suggestion.

    Spot-checking on qwen3:14b showed the agent would weave root strings into
    the answer from memory but never actually call search_arabic_root, which
    fails the [AR] eval assertion. The fix is to mark the call as MANDATORY
    in close proximity to the tool name so the model can't miss the link.
    """
    text = prompt_path.read_text(encoding="utf-8")
    lowered = text.lower()
    tool = "search_arabic_root"

    found_mandate_near_tool = False
    search_from = 0
    while True:
        tool_idx = lowered.find(tool, search_from)
        if tool_idx == -1:
            break
        window = lowered[max(0, tool_idx - 200) : tool_idx + len(tool) + 200]
        if "mandatory" in window:
            found_mandate_near_tool = True
            break
        search_from = tool_idx + 1

    assert found_mandate_near_tool, (
        f"{prompt_path.name} no longer marks any search_arabic_root mention as "
        "MANDATORY within 200 chars. The directive has been softened back to a "
        "suggestion — restore the mandate."
    )

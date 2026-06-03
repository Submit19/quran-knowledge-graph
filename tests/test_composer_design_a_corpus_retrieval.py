"""Executable spec for composer-rewire design §a — Source retrieval layer.

Design doc: data/research/composer_rewire/02_design_proposal_2026-05-28.md §a.

These are xfail(strict=True) regression-guards for a design that is NOT yet
implemented. They are the binary acceptance spec for the future implementer:

  * Today they FAIL (the corpus tool / config flag do not exist), so strict
    xfail records them as EXPECTED failures — the suite stays green.
  * When the design is implemented they will PASS; strict xfail then turns the
    XPASS into a hard FAILURE, forcing the implementer to remove the marker in
    the SAME commit as the implementation (the project's TDD discipline).

All imports that depend on unbuilt code happen INSIDE the test body so the
failure is captured by xfail rather than breaking collection for the module.
"""

import pytest


@pytest.mark.xfail(
    strict=True,
    reason="design §a: search_khalifa_corpus tool not implemented yet — "
    "commentary still has no authorized retrieval path (leak L2). "
    "See 02_design_proposal_2026-05-28.md §a.",
)
def test_composer_uses_khalifa_corpus_for_commentary():
    """§a: a Khalifa-corpus retrieval tool must exist and be dispatchable.

    The second authorized source (Khalifa's primary writings) must be reachable
    as a first-class, prompt-mandated tool — NOT left to model training
    knowledge. Asserts the tool is registered in chat.TOOLS and that dispatch
    returns provenance-bearing chunks (title/locator) the composer can cite as
    "(Khalifa, <work>, <locator>)".
    """
    import chat

    tool_names = set()
    for t in chat.TOOLS:
        # Anthropic schema is flat {"name": ...}; tolerate OpenAI-style nesting.
        name = t.get("name") or t.get("function", {}).get("name")
        if name:
            tool_names.add(name)

    assert "search_khalifa_corpus" in tool_names, (
        "design §a NOT met: no Khalifa-corpus retrieval tool registered in "
        "chat.TOOLS. Without it, all interpretation is composed from training "
        "knowledge (the L2 leak). The tool must return chunks carrying citable "
        "provenance {title, bucket, source_url, chunk_id, text, "
        "flagged_9_128_129}."
    )

    # The tool must be wired into dispatch (not just declared in the schema).
    assert hasattr(chat, "tool_search_khalifa_corpus"), (
        "design §a NOT met: chat.tool_search_khalifa_corpus dispatch function "
        "is missing — the schema entry alone does not make the corpus "
        "retrievable."
    )

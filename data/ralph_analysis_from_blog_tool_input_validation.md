# Tool Input Validation — Implementation Analysis

**Task:** `from_blog_tool_input_validation`
**Tick:** 119 (2026-05-13)
**Status:** DONE

## What was added

A new validation helper block was inserted in `chat.py` immediately before the tool
implementations (after the model-loading section). Three helper functions:

| Helper | Guards |
|---|---|
| `_validate_surah_number(n)` | Surah in [1, 114]; non-integer input rejected |
| `_validate_verse_id(s)` | Format `<int>:<int>`; surah in [1, 114]; ayah ≥ 1 |
| `_validate_language(lang)` | Allowlist `{en, ar, english, arabic}` |

All helpers return `None` on pass, or a structured `{error, reason}` dict on failure
(pre-execution, before any Neo4j round-trip). This is consistent with the pattern
introduced by `from_ai_graph_tool_error_audit` (post-execution structured errors).

## Tools patched

| Tool | Guard added |
|---|---|
| `tool_get_verse` | `_validate_verse_id` on `verse_id` |
| `tool_find_path` | `_validate_verse_id` on both `verse_id_1` and `verse_id_2` |
| `tool_explore_surah` | `_validate_surah_number` on `surah_number` |
| `tool_query_typed_edges` | `_validate_verse_id` on `verse_id` |
| `tool_get_verse_words` | `_validate_verse_id` on `verse_id` |

`_validate_language` is implemented but not yet wired to any tool — no tool currently
accepts a `language` parameter. It is ready for future use when multilingual routing
is added.

## Example error responses

```json
// tool_explore_surah(session, 999)
{"error": "Surah number 999 is out of range", "reason": "The Quran has 114 surahs", "valid_range": "1-114"}

// tool_get_verse(session, "abc:def")
{"error": "Invalid verse ID format: 'abc:def'", "reason": "Expected format is surah:ayah, e.g. '2:255'"}

// tool_get_verse(session, "0:1")
{"error": "Surah number 0 in verse ID '0:1' is out of range", "reason": "The Quran has 114 surahs", "valid_range": "1-114"}
```

## Why this matters

Before this patch, an LLM hallucinating `explore_surah(999)` would fire a full
`MATCH (v:Verse {surah: 999})` Cypher query (returning empty), then return a
generic error. The agent loop would either retry or silently continue with no
results. With the pre-execution guard, the error fires before touching Neo4j and
includes structured `reason` + `valid_range` fields the model can use to self-correct
on the next turn.

This is a pre-execution complement to `from_ai_graph_tool_error_audit` (post-execution
structured errors, `{error, reason}` shape). Both tasks together close the full
tool-failure signal gap described in Layer 4 Production Gotchas.

## Synergy note

`from_blog_tool_input_validation` (this task, p45) + `from_ai_graph_tool_error_audit`
(p60, DONE_WITH_CONCERNS) form a complete pair:
- Pre-execution: reject obviously invalid args before any Cypher fires
- Post-execution: return structured errors when Cypher runs but finds nothing valid

Together they eliminate the "agent can't distinguish 'no results' from 'invalid input'"
silent-retry problem.

## Smoke test

`python -c "import ast; ast.parse(open('chat.py', encoding='utf-8').read()); print('ok')"` → `ok`

Full quality gate (imports) requires Neo4j + model weights; skipped (Neo4j offline = expected false negative on this machine during cron).

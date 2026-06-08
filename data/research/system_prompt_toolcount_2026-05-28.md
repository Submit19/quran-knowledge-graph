# System-prompt tool-count audit (2026-05-28)

Ground-truth audit of the tool inventory each system prompt describes vs. the
tool registry the corresponding app actually exposes to the model. Triggered by
the architecture audit (`claude/architecture-audit-2026-05-22`), which flagged
`prompts/system_prompt.txt` ("15 tools") and `prompts/system_prompt_free.txt`
("10 tools") as under-describing the runtime tool surface.

## Headline finding: there are TWO registries, not one

The premise "both prompts under-describe a single 21-tool registry" is **partly
false**. The two prompts map to two *different* tool registries:

| Prompt | Loaded by | Real registry | Registry size | Prompt claimed | Verdict |
|---|---|---|---|---|---|
| `system_prompt.txt` | `app.py`, `app_full.py`, `app_lite.py`, `server.py`, `ui.py`, `evaluate.py` | `chat.TOOLS` | **20** | "15 tools" + lists 15 | **BUG** — under-describes by 5 |
| `system_prompt_free.txt` | `app_free.py` only | `app_free.OLLAMA_TOOLS` | **10** | "10 tools" | count correct; catalogue inconsistent |

The audit's "21" is off by one — `chat.TOOLS` has exactly **20** entries.

## Canonical count — `chat.TOOLS` (chat.py:1777–2358) = 20

Read directly from the list literal (not the docs). One bounded `TOOLS = [...]`
list, closed by `]` at line 2358. No other module redefines or extends it; every
importer uses it verbatim.

1. search_keyword (1779)
2. get_verse (1804)
3. traverse_topic (1828)
4. find_path (1858)
5. explore_surah (1885)
6. semantic_search (1909)
7. query_typed_edges (1942)
8. search_arabic_root (1975)
9. compare_arabic_usage (2000)
10. lookup_word (2025)
11. explore_root_family (2049)
12. get_verse_words (2074)
13. search_semantic_field (2098)
14. lookup_wujuh (2123)
15. search_morphological_pattern (2148)
16. concept_search (2179)
17. hybrid_search (2208)
18. recall_similar_query (2243)
19. run_cypher (2273)
20. get_code19_features (2327)

## Second registry — `app_free.OLLAMA_TOOLS` (app_free.py:80+) = 10

`app_free.py` does **not** drive the model with `chat.TOOLS`. It imports it
(`from chat import TOOLS as ANTHROPIC_TOOLS, dispatch_tool`) but **never
references `ANTHROPIC_TOOLS`** — a dead import. The agent loop is wired to a
separate, hand-maintained 10-entry list `OLLAMA_TOOLS` (OpenAI/Ollama
function-schema format), passed at app_free.py:383 `tools=OLLAMA_TOOLS`.

OLLAMA_TOOLS (10): search_keyword, semantic_search, traverse_topic, get_verse,
explore_surah, get_code19_features, concept_search, hybrid_search,
recall_similar_query, run_cypher.

## `system_prompt.txt` — tool-count strings

- **Line 23:** `You have 15 tools to explore the graph:` — WRONG. Should be 20.
- Catalogue lists exactly 15 (SEARCH & NAVIGATION ×9, ETYMOLOGY & WORD ANALYSIS ×6).
- **Missing from the catalogue entirely** (all 5 are real, exposed via chat.TOOLS):
  `concept_search`, `hybrid_search`, `recall_similar_query`,
  `get_code19_features`, `run_cypher`. The model cannot call what the prompt
  never names — this is the genuine under-use bug.

## `system_prompt_free.txt` — tool-count strings

- **Line 31:** `You have 10 retrieval/exploration tools. Choosing well matters.`
  — count is **correct** for OLLAMA_TOOLS (10).
- BUT the catalogue is inconsistent with OLLAMA_TOOLS in **both** directions:
  - **Lists `find_path`** (line 43) — NOT in OLLAMA_TOOLS. Prompt advertises a
    tool the local model cannot call.
  - **Omits `recall_similar_query`** — IS in OLLAMA_TOOLS but never described.
  - The "Arabic Root Augmentation" block (lines ~63–89) and the escalation line
    (~111) **mandate calling `search_arabic_root`**, which is NOT in
    OLLAMA_TOOLS. The prompt commands a tool the model cannot see.

## Other prompt files

`git ls-files prompts/` → only `system_prompt.txt`, `system_prompt_free.txt`,
and three `verse_analysis/` files. The verse_analysis prompts hardcode no tool
counts (grep for `\d+ (tools|functions|retrieval)` matches only the two lines
above).

## Existing tests asserting a tool count

None. No test references `len(TOOLS)`, `OLLAMA_TOOLS`, or a "N tools" string.

## Resolution taken (per operator decision, 2026-05-28)

- **`system_prompt.txt`:** add catalogue entries for the 5 missing tools, then
  "15 tools" → "20 tools".
- **`system_prompt_free.txt`:** make the catalogue match the runtime surface.
  Since `app_free.py` is the recommended production app and the Arabic-root
  augmentation is a real feature, **add `search_arabic_root` to OLLAMA_TOOLS**
  (free total → 11), drop `find_path` from the catalogue, add
  `recall_similar_query`, and update "10" → "11".
- Delete the dead `ANTHROPIC_TOOLS` import in `app_free.py`.
- Add `tests/test_tool_catalogue_consistency.py` (xfail-first) guarding
  prompt↔registry consistency in both directions, for both prompts.

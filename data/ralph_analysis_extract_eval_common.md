# extract_eval_common — analysis

## Task
Extract shared eval helper functions into `eval_common.py` — single canonical home for functions duplicated across 5 eval scripts with subtle drift.

## Functions extracted

| Function | Source files (before) | Notes |
|---|---|---|
| `expand_verse_range` | eval_qrcd_retrieval.py (as `expand_verse_range`), eval_qrcd_hipporag.py (as `expand`), eval_qrcd_hipporag_sweep.py (as `expand`), eval_ablation_retrieval.py (as `expand`) | Canonical name: `expand_verse_range`. eval_qrcd.py had a simplified variant `gold_verse_ids` (no comma-list support) — not replaced, left as domain-specific helper. |
| `load_qrcd_grouped` | eval_qrcd_retrieval.py (as `load_qrcd_grouped`), eval_qrcd_hipporag.py (inline in main), eval_qrcd_hipporag_sweep.py (as `load_questions`), eval_ablation_retrieval.py (as `load_questions`) | Canonical signature returns `list[dict]` with `gold` as sorted list; sweep/hipporag scripts wrap with `set()` conversion for their in-memory usage. |
| `hit_at_k` | All 5 files | Drift fixed: hipporag/sweep returned `any(...)` without explicit `bool` cast — canonical returns Python bool consistently. |
| `recall_at_k` | All 5 files | Drift fixed: hipporag/sweep returned `0` (int) on empty gold; canonical returns `0.0` (float). |
| `first_hit_rank` | 4 files (as `first_hit_rank` or `fhr`) | Canonical: `first_hit_rank`. `eval_ablation_retrieval.py` keeps `fhr = first_hit_rank` alias to avoid touching call sites. |
| `average_precision_at_k` | eval_qrcd_retrieval.py only | Moved to common module for future use. |

## Files modified
- `eval_common.py` — NEW canonical module
- `eval_qrcd_retrieval.py` — removed 4 inline functions, added import
- `eval_qrcd_hipporag.py` — removed 4 inline functions + expand, added import
- `eval_qrcd_hipporag_sweep.py` — removed 4 inline functions + expand + load_questions, added import
- `eval_ablation_retrieval.py` — removed 4 inline functions + expand + load_questions, added import with aliases
- `eval_qrcd.py` — removed 3 inline metric functions, added import

## Drift eliminated
- `recall_at_k` returning `0` vs `0.0` — now always `0.0`
- `expand` without comma-range support in some scripts vs full support in others — canonical handles both
- `load_questions` in sweep used `defaultdict(set)` directly; canonical uses `defaultdict(lambda: {"gold": set(), ...})` to also track `n_passages` metadata

## Acceptance: satisfied
Canonical `eval_common.py` exists and is >400 bytes.

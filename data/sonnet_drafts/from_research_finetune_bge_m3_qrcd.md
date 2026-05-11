---
task_id: from_research_finetune_bge_m3_qrcd
drafted_at: 2026-05-11T12:50:46.039756+00:00
model: claude-sonnet-4-6
purpose: Pre-warmed implementation plan; read by Opus subagent during IMPL tick.
---

# Implementation plan: `from_research_finetune_bge_m3_qrcd`

_Auto-drafted by `scripts/sonnet_prep.py` to reduce cold-discovery cost when the
IMPL tick spawns the Opus subagent. Treat as a starting point, not gospel._

---

# Implementation Plan: `from_research_finetune_bge_m3_qrcd`

## 1. Scope Clarification

**In scope:**
- Produce `data/ralph_agent_from_research_finetune_bge_m3_qrcd.md` — a detailed, actionable fine-tuning plan/report (≥800 bytes)
- Document the full pipeline: data prep (QRCD), FlagEmbedding training config, eval protocol, swap decision criteria
- Synthesize findings from the two source research files into concrete recommendations

**Out of scope:**
- Actually running the fine-tuning (compute-intensive, requires GPU hours; this is a planning/synthesis deliverable)
- Modifying `chat.py`, `retrieval_gate.py`, or any live system code
- Downloading or preprocessing QRCD data files

**Assumptions:**
- The deliverable is a *research-grade planning document* — the acceptance criteria only require the file to exist and be ≥800 bytes
- The document should be detailed enough that a future agent/operator can execute it end-to-end
- Current MAP@10 baseline is ~0.139 (from eval logs); literature ceiling is ~0.36 (AraBERT fine-tuned on QRCD)

---

## 2. Files to Read

| File | Why |
|------|-----|
| `repo://data/research_bge_m3_dense_vs_colbert.md` | Primary source: BGE-M3 vs ColBERT analysis, gap diagnosis |
| `repo://data/research_synthesis_2026-05-12.md` | Synthesis pass that bumped priority to 88, key conclusions |
| `repo://data/eval_v1_baseline_rerank_on.md` | Current MAP@10 baseline figures (0.139 anchor) |
| `repo://data/eval_v1_baseline_rerank_on.json` | Raw eval numbers if the .md is summary-only |
| `repo://pipeline_config.yaml` | Current embedding model config (`verse_embedding_m3` index) |
| `repo://retrieval_gate.py` | Reranker integration — understand how a new checkpoint would slot in |
| `repo://chat.py` | How semantic search tool calls the embedding index — swap surface |
| `repo://ralph_backlog.yaml` | Check if any downstream tasks depend on this output |

---

## 3. Files to Modify / Create

| File | Action |
|------|--------|
| `data/ralph_agent_from_research_finetune_bge_m3_qrcd.md` | **CREATE** — the primary deliverable |

No live code changes. This is a synthesis + planning output only.

---

## 4. Sub-step Breakdown

**Step 1 — Read source research files**
Open `data/research_bge_m3_dense_vs_colbert.md` and `data/research_synthesis_2026-05-12.md`. Extract: (a) exact MAP@10 gap figures, (b) recommended training approach, (c) dataset specifics, (d) any caveats flagged.

**Step 2 — Read baseline eval data**
Open `data/eval_v1_baseline_rerank_on.md` (and `.json` if needed). Confirm the 0.139 MAP@10 figure and note any per-surah variance or outliers that would inform train/test split design.

**Step 3 — Read pipeline config and swap surfaces**
Skim `pipeline_config.yaml`, `retrieval_gate.py`, and the semantic search tool in `chat.py`. Note exactly what env var / config key would need to change to point at a fine-tuned checkpoint (`SEMANTIC_SEARCH_INDEX`, model path in retrieval gate).

**Step 4 — Draft the document structure**
Write `data/ralph_agent_from_research_finetune_bge_m3_qrcd.md` with these sections:

1. **Executive Summary** — gap (0.139 → 0.36 target), approach (domain-adapted BGE-M3), decision gate
2. **Dataset Preparation** — QRCD source, passage-question pair format, train/dev/test split ratios, Tafsir Q&A optional augmentation, deduplication notes
3. **FlagEmbedding Training Config** — `BGEM3FlagModel` fine-tuning with `FlagEmbedding` library, contrastive loss (InfoNCE), batch size, learning rate schedule, hardware estimate (GPU hours on A100/3090)
4. **Embedding Index Rebuild** — Cypher to drop + recreate `verse_embedding_m3` index with fine-tuned vectors, re-embed all 6,234 verses
5. **Eval Protocol** — held-out QRCD test split, MAP@10 / nDCG@10 / Hit@10 metrics, comparison table (baseline vs fine-tuned, ±reranker)
6. **Swap Decision Criteria** — accept if MAP@10 ≥ 0.22 (≥58% lift); rollback path (keep baseline checkpoint)
7. **Integration Checklist** — env vars to update, `answer_cache` invalidation, `refresh_query_embedding_to_bge_m3` task dependency
8. **Open Questions / Risks** — QRCD license, Tafsir data quality, catastrophic forgetting on non-Arabic queries

**Step 5 — Verify length and content quality**
Confirm the file is substantive (well over 800 bytes). Check that all section headers are populated with specific, actionable content — not placeholders.

**Step 6 — Commit**
`git add data/ralph_agent_from_research_finetune_bge_m3_qrcd.md && git commit -m "agent: fine-tune BGE-M3 on QRCD — planning document + eval protocol"`

---

## 5. Risks / Unknowns

- **Source files may be sparse**: If `research_bge_m3_dense_vs_colbert.md` doesn't have enough detail, Opus should supplement from general FlagEmbedding documentation knowledge and flag this explicitly in the document.
- **QRCD license**: The dataset has an academic-use restriction; the document should note this and recommend verifying before commercial deployment.
- **Catastrophic forgetting**: BGE-M3 is multilingual; fine-tuning on Arabic Quranic data may hurt English retrieval quality. The eval protocol must include an English query holdout test.
- **`refresh_query_embedding_to_bge_m3` dependency**: Backlog task (pri 85) re-embeds stored queries. Fine-tuning creates a *new* checkpoint — the refresh task will need updating. Note this in the integration checklist.
- **Tafsir Q&A availability**: The description says "optionally Tafsir Q&A" — if no clear source is identified in the research files, mark it as future work rather than blocking.

---

## 6. Acceptance Check

```bash
# File must exist
ls -lh data/ralph_agent_from_research_finetune_bge_m3_qrcd.md

# Must be ≥ 800 bytes
wc -c data/ralph_agent_from_research_finetune_bge_m3_qrcd.md
# Expected: well above 800 (target 3000-6000 bytes for a useful planning doc)
```

The file should contain all 8 sections from Step 4, with no empty section bodies. Spot-check: search for "MAP@10", "FlagEmbedding", "swap", and "QRCD" — all four terms should appear with substantive surrounding text, not just as headers.

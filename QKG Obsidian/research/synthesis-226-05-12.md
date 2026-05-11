---
type: research
status: open
date_added: 2026-05-11
source: data/research_synthesis_2026-05-12.md
tags: [research, auto-stub]
---

# Research Synthesis 2026 05 12

_Stub auto-created by `vault_update.py`. Source artefact: `repo://data/research_synthesis_2026-05-12.md`._

## Source preamble

```
# Cross-research synthesis — 2026-05-12

## TL;DR (5 bullets)

- **The reranker is confirmed harmful on Arabic queries and must be disabled or replaced.** QRCD ablation shows `bge-reranker-v2-m3` drops hit@10 by 50% (0.6364→0.3182). Disabling it is the single highest-confidence, zero-cost quality fix available right now. Predicted eval_v1 lift: +4 to +10 avg cites/q.
- **Abstract-concept failures (meditation/reverence/Surah 55 cluster, 13–27 cites) are a routing problem, not a retrieval problem.** Six sources independently converge: those queries land in dense retrieval when `concept_search`→`traverse_topic` is the correct path. `from_neo4j_yt_router_agent` is DONE but the 50-question bucketed eval to confirm it works is still pending.
```

## Notes

_Distill the key findings from the source file here. Replace this stub when you do._

## Cross-references
- Source: `repo://data/research_synthesis_2026-05-12.md`
- [[../MOC]]

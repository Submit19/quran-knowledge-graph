# Research log

Aggregated index of research-loop findings. Each row links to the full
writeup in `data/research_<topic>.md`. Findings tagged `→ ralph` were
promoted into `ralph_backlog.yaml` as new tasks.

## Index

| date | topic | priority | status | summary | promoted? |
|------|-------|---------:|--------|---------|-----------|
| 2026-05-10 | [bge_m3_dense_vs_colbert](research_bge_m3_dense_vs_colbert.md) | 80 | done | Skip ColBERT — only +1.2 nDCG@10 lift on MIRACL Arabic; our 0.139→0.36 MAP gap is domain adaptation, not retrieval architecture. Fine-tune BGE-M3 dense on QRCD/Tafsir pairs first. | YES → `from_research_finetune_bge_m3_qrcd` |

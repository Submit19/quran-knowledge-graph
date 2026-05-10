---
type: research
status: done
priority: 70
tags: [research/retrieval, research/stack-review, research/benchmarks]
source: RESEARCH_2026-04-27.md
date_added: 2026-05-10
---

# Stack Critique and Extension Roadmap (2026-04-27)

> This is a distilled navigation note. The full 13-item table, skeptical analysis, and source URLs are in the source file at `repo://RESEARCH_2026-04-27.md` (~400 lines). Read that directly for the complete evidence base.

## TL;DR
- BGE-M3 was the #1 recommended upgrade; it has since been adopted. MiniLM is gone.
- MiniCheck-FT5 (Tang et al., EMNLP 2024) is the strongest citation verifier for verse-grounding — already integrated.
- Sefaria's architecture (Topic graph, RefTopicLink with bidirectional TF-IDF, `charLevelData`, provenance on every edge) is the highest-ROI architectural blueprint for QKG's typed-edge layer. See [[research-2026-04-28-deep-dive]] for detailed schema analysis.
- HippoRAG / PPR: built and evaluated — negative result on QRCD. See [[hipporag-negative-result]].
- QRCD benchmark: adopted and measured. See [[eval-qrcd-report]].

## Key findings (items not yet acted on)
- **Typed-edge taxonomy gap**: SUPPORTS/ELABORATES/QUALIFIES/CONTRASTS/REPEATS is hand-authored. Classical Islamic scholarship produced a richer set: *takhsis*, *bayan*, *naskh*, *takid*, *muhkam/mutashabih*. Altafsir.com (110+ tafsir works) + `tafsir_api` provide ground truth. Aligning to a scholarly-grounded 15–25 relation set is high-ROI but high-effort.
- **TF-IDF RELATED_TO ablation**: 51K TF-IDF edges may cluster vocabulary rather than meaning. Ablation needed: build same edge set with BGE-M3 cosine, compare retrieval-as-traversal recall on QRCD.
- **Reasoning memory underexploited**: the `(Query)-[:TRIGGERED]->(ReasoningTrace)...` subgraph is the HippoRAG substrate. PPR over it is built; the fix is better seeds. See [[hipporag-negative-result]].
- **Eval blind spots**: QIS metric has no abstention quality score and no theological/translator-stance fidelity check. Add RAGAS `answer_correctness` + a custom `stance_consistency` probe for Khalifa-specific framing.
- **Things confirmed as fine and should NOT change**: Neo4j substrate, Anthropic orchestration with Ollama/OpenRouter fallback, cache-with-dedupe-at-0.98, Three.js/Fibonacci-sphere viz.

## Action verdict
- ✅ Done — BGE-M3 adoption, MiniCheck, QRCD eval, HippoRAG eval, Sefaria schema study.
- 🔬 Research deeper — tafsir-grounded typed-edge taxonomy (Altafsir.com source). High effort, low risk.
- 🔬 Research deeper — TF-IDF RELATED_TO ablation vs BGE-M3 cosine edges.
- 🔬 Research deeper — `stance_consistency` probe for Khalifa-specific framing in answers.

## Cross-references
- [[research-2026-04-28-deep-dive]] — deep follow-up on Sefaria, MiniCheck, HippoRAG, GraphRAG-Bench
- [[eval-qrcd-report]] · [[hipporag-negative-result]] · [[bge-m3-dense-vs-colbert]]
- Source: `repo://RESEARCH_2026-04-27.md`

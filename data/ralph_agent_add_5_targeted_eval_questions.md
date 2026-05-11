# add_5_targeted_eval_questions

_Generated inline (agent_creative, no [opus] tag) by ralph cron tick 77._
_Output requires human review before downstream use._

---

## Deliverable — added to eval_v1.py as QUESTIONS_TARGETED constant

```python
QUESTIONS_TARGETED = [
    "How many times does the letter Qaf appear in Surah Qaf (50)?",
    "How many distinct verses mention Abraham (Ibrahim) across all surahs? Give the count.",
    "Find verses that contain the word 'kawthar' and explain its meaning.",
    "Compare the descriptions of the people of Lot across Surahs 7, 11, 26, and 27.",
    "Which verses use the concept of 'tawakkul' (trust in God) and what do they teach about it?",
]
```

## Rationale per question

1. **Qaf letter count in Surah 50** — directly exercises `get_code19_features`; forces the agent to call the Code-19 tool rather than hallucinating.
2. **Abraham verse count** — forces `run_cypher` aggregation (COUNT DISTINCT); cannot be answered by semantic search alone.
3. **Kawthar verses** — targets `hybrid_search` BM25 path: rare proper noun that may not embed well; exact-match is the correct path.
4. **People of Lot across surahs 7/11/26/27** — multi-hop traversal; forces `explore_surah` or `find_path` across 4 surah-verse combinations.
5. **Tawakkul concept** — exercises `concept_search` via Porter-stem ER / Concept node expansion; transliteration variants make keyword-only search unreliable.

## Notes

- Q "What was the previous question?" (original proposals) dropped — harness is stateless (history: []), zero signal value.
- `QUESTIONS_TARGETED` is defined in eval_v1.py but not yet wired into __main__ run_batch calls. Wire in when running targeted eval.


# Analysis: from_graphacademy_cypher_fewshots

**Task:** Add 5-8 QKG-specific few-shot Cypher examples to the `run_cypher` tool description in chat.py.

**Source:** GraphAcademy `llm-chatbot-python` course — few-shot Cypher tuning reduces hallucinated property names when an LLM uses `run_cypher` as an escape hatch.

## What was done

Added 8 few-shot Cypher example templates directly into the `run_cypher` tool description in `chat.py` (the `TOOLS` list entry at line ~2207). Examples cover every common QKG access pattern:

1. **Verse lookup by ID** — `MATCH (v:Verse {verseId: '2:255'}) RETURN v.verseId, v.text, v.arabicText`
2. **Count verses mentioning a keyword** — `MATCH (v:Verse)-[:MENTIONS]->(k:Keyword {keyword: 'patience'}) RETURN count(v) AS n`
3. **Root traversal** — `MATCH (v:Verse)-[:MENTIONS_ROOT]->(r:ArabicRoot {root: 'ص ب ر'}) RETURN v.verseId ...`
4. **RELATED_TO neighbors** — `MATCH (v:Verse {verseId: '2:255'})-[r:RELATED_TO]-(n:Verse) RETURN n.verseId, r.score ORDER BY r.score DESC`
5. **Semantic domain membership** — `MATCH (sd:SemanticDomain {name: 'faith'})<-[:IN_DOMAIN]-(v:Verse) RETURN v.verseId ...`
6. **Morphological pattern** — `MATCH (v:Verse)-[:HAS_WORD]->(:Lemma)-[:HAS_PATTERN]->(p:MorphPattern {pattern: 'فَعَّالٌ'}) RETURN DISTINCT v.verseId ...`
7. **Cross-surah co-occurrence** — `MATCH (v:Verse)-[:MENTIONS]->(:Keyword {keyword: 'Moses'}), (v)-[:MENTIONS]->(:Keyword {keyword: 'Pharaoh'}) RETURN ...`
8. **Aggregate** — `MATCH (s:Sura)-[:CONTAINS]->(v:Verse) RETURN s.number, count(v) AS verse_count ORDER BY s.number`

## Why this matters

The LLM frequently invents wrong property names (e.g., `v.surah_number` instead of `v.surah`, or `r.weight` instead of `r.score`) when writing Cypher cold. Inline few-shots provide a consistent property-name reference at the point of use — more reliable than hoping the schema summary alone is enough.

Also fixed a self-referential error in the existing description: "always prefer ... run_cypher etc. over raw Cypher" — changed to "always prefer ... other specialised tools over raw Cypher".

## Acceptance

`chat.py` file size is well above 1 byte. ✓

# from_neo4j_crawl_audit_indexes

```json
[
  {
    "name": "arabic_root_bw",
    "type": "RANGE",
    "labelsOrTypes": [
      "ArabicRoot"
    ],
    "properties": [
      "rootBW"
    ],
    "state": "ONLINE"
  },
  {
    "name": "arabic_root_id",
    "type": "RANGE",
    "labelsOrTypes": [
      "ArabicRoot"
    ],
    "properties": [
      "root"
    ],
    "state": "ONLINE"
  },
  {
    "name": "citation_check_id",
    "type": "RANGE",
    "labelsOrTypes": [
      "CitationCheck"
    ],
    "properties": [
      "checkId"
    ],
    "state": "ONLINE"
  },
  {
    "name": "citation_check_label",
    "type": "RANGE",
    "labelsOrTypes": [
      "CitationCheck"
    ],
    "properties": [
      "nli_label"
    ],
    "state": "ONLINE"
  },
  {
    "name": "citation_check_ref",
    "type": "RANGE",
    "labelsOrTypes": [
      "CitationCheck"
    ],
    "properties": [
      "ref"
    ],
    "state": "ONLINE"
  },
  {
    "name": "concept_stem_unique",
    "type": "RANGE",
    "labelsOrTypes": [
      "Concept"
    ],
    "properties": [
      "stem"
    ],
    "state": "ONLINE"
  },
  {
    "name": "index_1b9dcc97",
    "type": "LOOKUP",
    "labelsOrTypes": null,
    "properties": null,
    "state": "ONLINE"
  },
  {
    "name": "index_460996c0",
    "type": "LOOKUP",
    "labelsOrTypes": null,
    "properties": null,
    "state": "ONLINE"
  },
  {
    "name": "kw_id",
    "type": "RANGE",
    "labelsOrTypes": [
      "Keyword"
    ],
    "properties": [
      "keyword"
    ],
    "state": "ONLINE"
  },
  {
    "name": "lemma_id",
    "type": "RANGE",
    "labelsOrTypes": [
      "Lemma"
    ],
    "properties": [
      "lemma"
    ],
    "state": "ONLINE"
  },
  {
    "name": "lemma_root",
    "type": "RANGE",
    "labelsOrTypes": [
      "Lemma"
    ],
    "properties": [
      "root"
    ],
    "state": "ONLINE"
  },
  {
    "name": "morph_pattern_id",
    "type": "RANGE",
    "labelsOrTypes": [
      "MorphPattern"
    ],
    "properties": [
      "pattern"
    ],
    "state": "ONLINE"
  },
  {
    "name": "query_embedding",
    "type": "VECTOR",
    "labelsOrTypes": [
      "Query"
    ],
    "properties": [
      "textEmbedding"
    ],
    "state": "ONLINE"
  },
  {
    "name": "query_id",
    "type": "RANGE",
    "labelsOrTypes": [
      "Query"
    ],
    "properties": [
      "queryId"
    ],
    "state": "ONLINE"
  },
  {
    "name": "query_ts",
    "type": "RANGE",
    "labelsOrTypes": [
      "Query"
    ],
    "properties": [
      "timestamp"
    ],
    "state": "ONLINE"
  },
  {
    "name": "rel_contrasts_score",
    "type": "RANGE",
    "labelsOrTypes": [
      "CONTRASTS"
    ],
    "properties": [
      "score"
    ],
    "state": "ONLINE"
  },
  {
    "name": "rel_elaborates_score",
    "type": "RANGE",
    "labelsOrTypes": [
      "ELABORATES"
    ],
    "properties": [
      "score"
    ],
    "state": "ONLINE"
  },
  {
    "name": "rel_qualifies_score",
    "type": "RANGE",
    "labelsOrTypes": [
      "QUALIFIES"
    ],
    "properties": [
      "score"
    ],
    "state": "ONLINE"
  },
  {
    "name": "rel_repeats_score",
    "type": "RANGE",
    "labelsOrTypes": [
      "REPEATS"
    ],
    "properties": [
      "score"
    ],
    "state": "ONLINE"
  },
  {
    "name": "rel_supports_score",
    "type": "RANGE",
    "labelsOrTypes": [
      "SUPPORTS"
    ],
    "properties": [
      "score"
    ],
    "state": "ONLINE"
  },
  {
    "name": "retrieved_tool",
    "type": "RANGE",
    "labelsOrTypes": [
      "RETRIEVED"
    ],
    "properties": [
      "tool"
    ],
    "state": "ONLINE"
  },
  {
    "name": "semantic_domain_id",
    "type": "RANGE",
    "labelsOrTypes": [
      "SemanticDomain"
    ],
    "properties": [
      "domainId"
    ],
    "state": "ONLINE"
  },
  {
    "name": "sura_num",
    "type": "RANGE",
    "labelsOrTypes": [
      "Sura"
    ],
    "properties": [
      "number"
    ],
    "state": "ONLINE"
  },
  {
    "name": "toolcall_id",
    "type": "RANGE",
    "labelsOrTypes": [
      "ToolCall"
    ],
    "properties": [
      "callId"
    ],
    "state": "ONLINE"
  },
  {
    "name": "toolcall_name",
    "type": "RANGE",
    "labelsOrTypes": [
      "ToolCall"
    ],
    "properties": [
      "tool_name"
    ],
    "state": "ONLINE"
  },
  {
    "name": "trace_id",
    "type": "RANGE",
    "labelsOrTypes": [
      "ReasoningTrace"
    ],
    "properties": [
      "traceId"
    ],
    "state": "ONLINE"
  },
  {
    "name": "verse_arabic_fulltext",
    "type": "FULLTEXT",
    "labelsOrTypes": [
      "Verse"
    ],
    "properties": [
      "arabicPlain"
    ],
    "state": "ONLINE"
  },
  {
    "name": "verse_embedding",
    "type": "VECTOR",
    "labelsOrTypes": [
      "Verse"
    ],
    "properties": [
      "embedding"
    ],
    "state": "ONLINE"
  },
  {
    "name": "verse_embedding_m3",
    "type": "VECTOR",
    "labelsOrTypes": [
      "Verse"
    ],
    "properties": [
      "embedding_m3"
    ],
    "state": "ONLINE"
  },
  {
    "name": "verse_embedding_m3_ar",
    "type": "VECTOR",
    "labelsOrTypes": [
      "Verse"
    ],
    "properties": [
      "embedding_m3_ar"
    ],
    "state": "ONLINE"
  },
  {
    "name": "verse_id",
    "type": "RANGE",
    "labelsOrTypes": [
      "Verse"
    ],
    "properties": [
      "verseId"
    ],
    "state": "ONLINE"
  },
  {
    "name": "verse_ref",
    "type": "RANGE",
    "labelsOrTypes": [
      "Verse"
    ],
    "properties": [
      "reference"
    ],
    "state": "ONLINE"
  },
  {
    "name": "verse_surah",
    "type": "RANGE",
    "labelsOrTypes": [
      "Verse"
    ],
    "properties": [
      "surah"
    ],
    "state": "ONLINE"
  },
  {
    "name": "verse_text_fulltext",
    "type": "FULLTEXT",
    "labelsOrTypes": [
      "Verse"
    ],
    "properties": [
      "text"
    ],
    "state": "ONLINE"
  },
  {
    "name": "word_token_arabic",
    "type": "RANGE",
    "labelsOrTypes": [
      "WordToken"
    ],
    "properties": [
      "arabicClean"
    ],
    "state": "ONLINE"
  },
  {
    "name": "word_token_bw",
    "type": "RANGE",
    "labelsOrTypes": [
      "WordToken"
    ],
    "properties": [
      "translitBW"
    ],
    "state": "ONLINE"
  },
  {
    "name": "word_token_id",
    "type": "RANGE",
    "labelsOrTypes": [
      "WordToken"
    ],
    "properties": [
      "tokenId"
    ],
    "state": "ONLINE"
  },
  {
    "name": "word_token_lemma",
    "type": "RANGE",
    "labelsOrTypes": [
      "WordToken"
    ],
    "properties": [
      "lemma"
    ],
    "state": "ONLINE"
  },
  {
    "name": "word_token_pos",
    "type": "RANGE",
    "labelsOrTypes": [
      "WordToken"
    ],
    "properties": [
      "pos"
    ],
    "state": "ONLINE"
  },
  {
    "name": "word_token_root",
    "type": "RANGE",
    "labelsOrTypes": [
      "WordToken"
    ],
    "properties": [
      "root"
    ],
    "state": "ONLINE"
  },
  {
    "name": "word_token_verse",
    "type": "RANGE",
    "labelsOrTypes": [
      "WordToken"
    ],
    "properties": [
      "verseId"
    ],
    "state": "ONLINE"
  }
]
```

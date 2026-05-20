# Cache Coverage Report — 2026-05-21

Source: `data/answer_cache.json` (1612 entries, post-prune, post-enrich, with BGE-M3 question embeddings).

Read-only pass; no entries mutated.

## Surah coverage

**114 of 114** surahs cited at least once (100.0%).

Surahs with **zero** citations across the cache: 0

### Top 10 most-cited surahs

| Surah | Cache occurrences |
|---:|---:|
| 2 | 7617 |
| 6 | 3513 |
| 3 | 3311 |
| 9 | 3191 |
| 4 | 3180 |
| 5 | 2810 |
| 7 | 2541 |
| 33 | 2413 |
| 39 | 1832 |
| 24 | 1656 |

### Bottom 10 (non-zero) surahs by citations

| Surah | Cache occurrences |
|---:|---:|
| 113 | 25 |
| 105 | 30 |
| 106 | 30 |
| 108 | 32 |
| 109 | 34 |
| 111 | 38 |
| 114 | 39 |
| 112 | 45 |
| 103 | 49 |
| 104 | 49 |

## Prophet coverage

**24 of 25** named prophets appear in at least one cache entry's answer text (case-insensitive substring match across Anglicised + Arabic transliteration variants).

| Prophet | Entries mentioning |
|---|---:|
| Lut | 592 |
| Musa | 329 |
| Abraham | 219 |
| Muhammad | 165 |
| `Isa | 152 |
| Noah | 150 |
| Adam | 106 |
| Yusuf | 97 |
| Sulaiman | 69 |
| Ya`qub | 65 |
| Dawud | 53 |
| Hud | 50 |
| Ishaq | 46 |
| Harun | 44 |
| Ismail | 43 |
| Yunus | 25 |
| Ayyub | 23 |
| Salih | 16 |
| Yahya | 12 |
| Idris | 7 |
| Ilyas | 6 |
| Zakariya | 4 |
| Al-Yasa` | 3 |
| Dhul-Kifl | 1 |
| Shu`aib | 0 |

## Top 20 Arabic roots in cache answers

Heuristic: three-letter Arabic characters separated by hyphens or spaces. Includes spurious adjacencies; treat as directional, not authoritative.

| Root | Occurrences |
|---|---:|
| ت-و-ب | 2 |
| ن-ف-ق | 2 |
| ق-ر-أ | 1 |
| ر-ج-ع | 1 |
| ج-ن-ن | 1 |
| غ-ف-ر | 1 |
| ص-ب-ر | 1 |
| ح-م-ع | 1 |
| ز-ك-و | 1 |
| ش-ك-ر | 1 |
| ذ-ن-ب | 1 |
| ظ-ل-م | 1 |
| خ-ش-ع | 1 |
| ع-د-ل | 1 |
| ق-س-ط | 1 |
| ك-ب-ر | 1 |
| و-ك-ل | 1 |
| ش-ك-ك | 1 |
| ر-ي-ب | 1 |
| ي-ق-ن | 1 |

## Coverage gaps — main eval set

Cosine similarity (BGE-M3) of each main-set question to its best-matching cache entry. Lower = thinner coverage.

- 0 of 57 main questions have best-match similarity < 0.60.

### Bottom 15 main-set questions by best-match similarity

| ID | Bucket | sim | Question | Best match (cache) |
|---|---|---:|---|---|
| concrete-001 | CONCRETE | 0.944 | Tell me about Paradise. | Tell me about paradise |
| abstract-001 | ABSTRACT | 1.0 | Tell me what the Quran says about charity. | Tell me what the Quran says about charity. |
| abstract-002 | ABSTRACT | 1.0 | What does the Quran teach about forgiveness? | What does the Quran teach about forgiveness? |
| abstract-003 | ABSTRACT | 1.0 | How does the Quran portray gratitude? | How does the Quran portray gratitude? |
| abstract-004 | ABSTRACT | 1.0 | Describe what the Quran reveals about sin. | Describe what the Quran reveals about sin. |
| abstract-005 | ABSTRACT | 1.0 | What does the Quran say about patience? | What does the Quran say about patience? |
| abstract-006 | ABSTRACT | 1.0 | How is humility presented in the Quran? | How is humility presented in the Quran? |
| abstract-007 | ABSTRACT | 1.0 | What is the Quran's teaching on repentance? | What is the Quran's teaching on repentance? |
| abstract-008 | ABSTRACT | 1.0 | How does the Quran describe true belief? | How does the Quran describe true belief? |
| abstract-009 | ABSTRACT | 1.0 | What does the Quran reveal about hypocrisy? | What does the Quran reveal about hypocrisy? |
| abstract-010 | ABSTRACT | 1.0 | What is the Quran's view of justice? | What is the Quran's view of justice? |
| abstract-011 | ABSTRACT | 1.0 | How does the Quran warn about the consequences of arrogance? | How does the Quran warn about the consequences of arrogance? |
| abstract-012 | ABSTRACT | 1.0 | Walk me through the Quran's description of the path of righteousness. | Walk me through the Quran's description of the path of right |
| abstract-013 | ABSTRACT | 1.0 | What guidance does the Quran offer on trusting in God? | What guidance does the Quran offer on trusting in God? |
| abstract-014 | ABSTRACT | 1.0 | How does the Quran address doubt and certainty? | How does the Quran address doubt and certainty? |

## Top-5 candidate themes for next seeding pass

Drawn from the bottom of the main-set gap table above. These are themes the cache currently answers thinly — a future seeding pass should target them.

- `concrete-001` (sim 0.944): Tell me about Paradise.
- `abstract-001` (sim 1.0): Tell me what the Quran says about charity.
- `abstract-002` (sim 1.0): What does the Quran teach about forgiveness?
- `abstract-003` (sim 1.0): How does the Quran portray gratitude?
- `abstract-004` (sim 1.0): Describe what the Quran reveals about sin.

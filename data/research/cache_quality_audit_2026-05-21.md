# Cache Quality Audit — 2026-05-21

Source: `data/answer_cache.json` (1613 entries)

Read-only pass; no entries mutated.

## Tier distribution

| Tier | Count | % |
|---|---:|---:|
| HIGH (q ≥ 0.7) | 1387 | 86.0% |
| MEDIUM (q ≥ 0.3) | 143 | 8.9% |
| LOW (q ≥ 0.0) | 83 | 5.1% |

## Aggregate signals

- Citation validity overall: **84.83%** (5518 of 6505 unique cited verseIds resolve in Neo4j)
- Entries with zero citations: **118** (7.3%)
- Entries with repetition: **94** (5.8%)
- Entries with Arabic text: **340** (21.1%)
- Entries with tools_used field: **0** (0.0%)

## Quality score histogram

| Bucket | Count |
|---|---:|
| [0.00,0.10) | 7 |
| [0.10,0.20) | 0 |
| [0.20,0.30) | 76 |
| [0.30,0.40) | 39 |
| [0.40,0.50) | 76 |
| [0.50,0.60) | 15 |
| [0.60,0.70) | 13 |
| [0.70,0.80) | 30 |
| [0.80,0.90) | 1081 |
| [0.90,inf) | 276 |

## Cite count histogram

| Bucket | Count |
|---|---:|
| [0.00,1.00) | 118 |
| [1.00,3.00) | 9 |
| [3.00,5.00) | 19 |
| [5.00,10.00) | 65 |
| [10.00,20.00) | 314 |
| [20.00,40.00) | 425 |
| [40.00,inf) | 663 |

## Answer length histogram (chars)

| Bucket | Count |
|---|---:|
| [0.00,200.00) | 1 |
| [200.00,500.00) | 2 |
| [500.00,1000.00) | 7 |
| [1000.00,3000.00) | 32 |
| [3000.00,7000.00) | 689 |
| [7000.00,15000.00) | 801 |
| [15000.00,inf) | 81 |

## Top 20 most-cited verses

| Rank | VerseId | Cache occurrences |
|---:|---|---:|
| 1 | [6:55] | 1017 |
| 2 | [2:74] | 528 |
| 3 | [38:56] | 503 |
| 4 | [2:97] | 488 |
| 5 | [57:25] | 434 |
| 6 | [30:22] | 414 |
| 7 | [65:7] | 331 |
| 8 | [2:267] | 288 |
| 9 | [59:13] | 279 |
| 10 | [2:177] | 247 |
| 11 | [2:255] | 245 |
| 12 | [84:22] | 229 |
| 13 | [73:20] | 214 |
| 14 | [84:21] | 210 |
| 15 | [24:35] | 206 |
| 16 | [2:185] | 194 |
| 17 | [37:163] | 191 |
| 18 | [68:22] | 186 |
| 19 | [68:25] | 183 |
| 20 | [68:17] | 182 |

## Example entries — HIGH

- **Q:** What does the Quran say about the people of Thamud?
  - score=0.80 | cites=38 (valid=1.00) | len=5494 | rep=False | ar=False
- **Q:** What does the Quran say about paradise?
  - score=0.80 | cites=30 (valid=1.00) | len=5810 | rep=False | ar=False
- **Q:** What does the Quran say about hell?
  - score=0.80 | cites=47 (valid=1.00) | len=6728 | rep=False | ar=False
- **Q:** What does the Quran say about the Day of Judgment?
  - score=0.80 | cites=63 (valid=1.00) | len=10542 | rep=False | ar=False
- **Q:** What does the Quran say about death and the soul?
  - score=0.80 | cites=77 (valid=1.00) | len=11721 | rep=False | ar=False
- **Q:** What does the Quran say about resurrection?
  - score=0.90 | cites=22 (valid=1.00) | len=8116 | rep=False | ar=True
- **Q:** What does the Quran say about the Hour of Judgment?
  - score=0.80 | cites=29 (valid=1.00) | len=5894 | rep=False | ar=False
- **Q:** What does the Quran say about the scales of deeds?
  - score=0.77 | cites=27 (valid=0.91) | len=4160 | rep=False | ar=False
- **Q:** What does the Quran say about the records of deeds?
  - score=0.80 | cites=43 (valid=1.00) | len=8259 | rep=False | ar=False
- **Q:** What does the Quran say about intercession on Judgment Day?
  - score=0.80 | cites=28 (valid=1.00) | len=6432 | rep=False | ar=False

## Example entries — MEDIUM

- **Q:** What does the Quran say about eternal punishment?
  - score=0.40 | cites=71 (valid=1.00) | len=13766 | rep=True | ar=False
- **Q:** What does the Quran say about the signs of the Hour?
  - score=0.40 | cites=250 (valid=1.00) | len=11812 | rep=True | ar=False
- **Q:** What does the Quran say about the count of chapter-opening letters?
  - score=0.56 | cites=1 (valid=1.00) | len=816 | rep=False | ar=False
- **Q:** Explain Ayat al-Kursi (verse 2:255)
  - score=0.40 | cites=48 (valid=1.00) | len=9649 | rep=True | ar=False
- **Q:** What does the Quran teach about wisdom (hikmah)?
  - score=0.40 | cites=115 (valid=1.00) | len=10990 | rep=True | ar=False
- **Q:** What does the Quran say about the limits set by God?
  - score=0.40 | cites=344 (valid=1.00) | len=24887 | rep=True | ar=False
- **Q:** Explain Surah Al-Ma'idah chapter 5
  - score=0.40 | cites=237 (valid=1.00) | len=18970 | rep=True | ar=False
- **Q:** Explain Surah Al-Ahzab chapter 33
  - score=0.40 | cites=150 (valid=1.00) | len=13369 | rep=True | ar=False
- **Q:** Explain Surah Al-Mu'min chapter 40
  - score=0.56 | cites=1 (valid=1.00) | len=9990 | rep=False | ar=False
- **Q:** Explain Surah Al-Jumu'ah chapter 62
  - score=0.40 | cites=76 (valid=1.00) | len=11193 | rep=True | ar=False

## Example entries — LOW

- **Q:** Explain verse 2:186 — what does it promise about God answering prayers?
  - score=0.20 | cites=0 (valid=0.00) | len=8847 | rep=False | ar=False
- **Q:** Explain verse 7:180 — what does it teach about God's most beautiful names?
  - score=0.20 | cites=0 (valid=0.00) | len=7084 | rep=False | ar=False
- **Q:** Explain verse 9:51 — what does 'nothing befalls us but what God has written' teach?
  - score=0.20 | cites=0 (valid=0.00) | len=9936 | rep=False | ar=False
- **Q:** Explain verse 12:87 — what does 'do not despair of God's mercy' teach?
  - score=0.20 | cites=0 (valid=0.00) | len=3705 | rep=False | ar=False
- **Q:** Explain verse 14:7 — what does 'if you are grateful, I will increase you' teach?
  - score=0.20 | cites=0 (valid=0.00) | len=13410 | rep=False | ar=False
- **Q:** Explain verse 30:21 — what does it teach about marriage as a sign of God?
  - score=0.20 | cites=0 (valid=0.00) | len=9086 | rep=False | ar=False
- **Q:** what is the significance of the number 43 in the quran
  - score=0.00 | cites=0 (valid=0.00) | len=14253 | rep=True | ar=False
- **Q:** Explain verse 42:30 — what does it teach about affliction being from our own hands?
  - score=0.20 | cites=0 (valid=0.00) | len=6588 | rep=False | ar=False
- **Q:** What Quranic evidence supports the Dawn (Fajr) and Afternoon (Asr) prayers?
  - score=0.20 | cites=0 (valid=0.00) | len=7451 | rep=False | ar=False
- **Q:** What does the Quran say about the direction of Kaaba as a qiblah?
  - score=0.20 | cites=0 (valid=0.00) | len=5600 | rep=False | ar=False

## Missing-citation breakdown

Citations that don't resolve in Neo4j are classified to distinguish graph-integrity issues from cache-content hallucinations.

- **Impossible citations** (out-of-range surah or verseNum beyond surah size): **985 unique** (1170 occurrences) — these are model hallucinations, NOT graph bugs.
- **Other missing** (incl. Khalifa-excluded 9:128/9:129): **2 unique** (4 occurrences).

_Conclusion: the graph is healthy (6,234 verses, surahs sized correctly). The 15% citation invalidity is cache rot from older models hallucinating verseIds._

### Top 20 impossible citations

| VerseId | Reason | Occurrences |
|---|---|---:|
| [111:6] | verse_beyond_max(5) | 8 |
| [110:9] | verse_beyond_max(3) | 8 |
| [97:9] | verse_beyond_max(5) | 8 |
| [108:5] | verse_beyond_max(3) | 8 |
| [106:5] | verse_beyond_max(4) | 8 |
| [103:4] | verse_beyond_max(3) | 8 |
| [9:144] | verse_beyond_max(127) | 6 |
| [49:49] | verse_beyond_max(18) | 5 |
| [71:47] | verse_beyond_max(28) | 4 |
| [93:13] | verse_beyond_max(11) | 4 |
| [62:12] | verse_beyond_max(11) | 4 |
| [84:36] | verse_beyond_max(25) | 4 |
| [9:133] | verse_beyond_max(127) | 4 |
| [94:30] | verse_beyond_max(8) | 3 |
| [55:79] | verse_beyond_max(78) | 3 |
| [97:30] | verse_beyond_max(5) | 3 |
| [48:30] | verse_beyond_max(29) | 3 |
| [1:61] | verse_beyond_max(7) | 3 |
| [9:141] | verse_beyond_max(127) | 3 |
| [81:30] | verse_beyond_max(29) | 3 |

## Methodology

Quality score = 0.3·min(cite_count/5,1) + 0.3·cite_validity + 0.2·[len≥300] + 0.1·has_arabic − 0.4·has_repetition. Tiers: HIGH ≥0.7, MEDIUM 0.3–0.7, LOW <0.3.

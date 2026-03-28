"""
Step 2 — Build the knowledge graph CSV files using TF-IDF keyword extraction.

Reads data/verses.json and produces 4 CSVs in data/:
  verse_nodes.csv         — one row per verse
  keyword_nodes.csv       — one row per significant keyword
  verse_keyword_rels.csv  — MENTIONS edges (verse -> keyword, weighted by TF-IDF)
  verse_related_rels.csv  — RELATED_TO edges (verse ↔ verse via shared rare keywords)

TF-IDF settings:
  - Min score:      0.04
  - Max doc freq:   300 verses  (keywords in more than 300 verses are too common)
  - Max edges/verse: 12         (cap RELATED_TO edges per verse)
  - Lemmatization:  WordNet
  - Stopwords:      NLTK English + Quran-specific high-frequency low-signal words
"""

import csv
import json
import os
import re
from collections import defaultdict

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# ── Stopwords ────────────────────────────────────────────────────────────────

QURAN_STOPWORDS = {
    "god", "lord", "indeed", "surely", "verily", "thus", "therefore",
    "henceforth", "none", "nothing", "anyone", "everyone", "whoever",
    "whatever", "wherever", "whenever", "said", "says",
    # Additional high-frequency low-signal words in Khalifa translation
    "shall", "will", "upon", "unto", "thee", "thy", "thou", "thine",
    "hath", "doth", "ye", "yea", "nay", "thereof", "therein", "thereby",
    "herein", "hereby", "wherein", "whereby", "also", "even", "still",
    "yet", "well", "away", "back", "never", "ever", "always", "already",
    "truly", "certainly", "absolutely", "completely", "totally", "simply",
}

nltk_stops = set(stopwords.words('english'))
ALL_STOPWORDS = nltk_stops | QURAN_STOPWORDS

# ── Lemmatizer ───────────────────────────────────────────────────────────────

lemmatizer = WordNetLemmatizer()

def lemmatize_token(token: str) -> str:
    # Try verb form first, then noun
    verb = lemmatizer.lemmatize(token, pos='v')
    if verb != token:
        return verb
    return lemmatizer.lemmatize(token, pos='n')

def tokenize_and_lemmatize(text: str) -> list[str]:
    tokens = re.findall(r'[a-z]+', text.lower())
    result = []
    for t in tokens:
        if len(t) < 3:
            continue
        if t in ALL_STOPWORDS:
            continue
        lemma = lemmatize_token(t)
        if lemma in ALL_STOPWORDS:
            continue
        result.append(lemma)
    return result

# ── TF-IDF Analyzer ──────────────────────────────────────────────────────────

class LemmaAnalyzer:
    """Custom sklearn analyzer that lemmatizes tokens."""
    def __call__(self, text: str) -> list[str]:
        return tokenize_and_lemmatize(text)


# ── Main pipeline ─────────────────────────────────────────────────────────────

def load_verses(path: str = "data/verses.json") -> list[dict]:
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def build_tfidf(verses: list[dict]) -> tuple:
    """Fit TF-IDF on all verse texts. Returns (vectorizer, matrix, feature_names)."""
    print("Building TF-IDF matrix...")
    texts = [v['text'] for v in verses]

    # max_df: skip terms in more than 300 docs
    # min_df: term must appear in at least 2 verses
    vectorizer = TfidfVectorizer(
        analyzer=LemmaAnalyzer(),
        max_df=300,         # absolute count
        min_df=2,
        max_features=50000,
    )
    matrix = vectorizer.fit_transform(texts)
    feature_names = vectorizer.get_feature_names_out()
    print(f"  Vocabulary size: {len(feature_names):,} keywords")
    print(f"  Matrix shape:    {matrix.shape}")
    return vectorizer, matrix, feature_names


def write_verse_nodes(verses: list[dict], path: str) -> None:
    print(f"Writing {path}...")
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['verseId', 'surah', 'verseNum', 'surahName', 'text'])
        writer.writeheader()
        for v in verses:
            writer.writerow({
                'verseId':   v['verse_id'],
                'surah':     v['surah'],
                'verseNum':  v['verse'],
                'surahName': v['surah_name'],
                'text':      v['text'].replace('\n', ' '),
            })
    print(f"  {len(verses):,} verse nodes")


def write_keyword_nodes(feature_names: np.ndarray, path: str) -> None:
    print(f"Writing {path}...")
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['keyword'])
        writer.writeheader()
        for kw in feature_names:
            writer.writerow({'keyword': kw})
    print(f"  {len(feature_names):,} keyword nodes")


def write_verse_keyword_rels(
    verses: list[dict],
    matrix,
    feature_names: np.ndarray,
    path: str,
    min_score: float = 0.04,
) -> dict:
    """
    Write MENTIONS edges. Returns keyword_to_verse_ids mapping for RELATED_TO.
    """
    print(f"Writing {path} (min TF-IDF={min_score})...")

    keyword_to_verses: dict[str, list[tuple[str, float]]] = defaultdict(list)
    total_edges = 0

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['verseId', 'keyword', 'score'])
        writer.writeheader()

        # Iterate row by row (each row = one verse)
        cx = matrix.tocsr()
        for i, verse in enumerate(verses):
            row = cx.getrow(i)
            row_data = list(zip(row.indices, row.data))
            # Filter by min score
            significant = [(idx, score) for idx, score in row_data if score >= min_score]
            for idx, score in significant:
                kw = feature_names[idx]
                writer.writerow({
                    'verseId': verse['verse_id'],
                    'keyword': kw,
                    'score':   round(float(score), 6),
                })
                keyword_to_verses[kw].append((verse['verse_id'], float(score)))
                total_edges += 1

    print(f"  {total_edges:,} MENTIONS edges")
    return keyword_to_verses


def write_verse_related_rels(
    keyword_to_verses: dict,
    path: str,
    max_edges_per_verse: int = 12,
    max_verse_freq: int = 300,
) -> None:
    """
    Write RELATED_TO edges: verses sharing rare, high-scoring keywords.
    Skips keywords that appear in more than max_verse_freq verses.
    Caps edges per verse at max_edges_per_verse.
    """
    print(f"Writing {path}...")
    print(f"  Max keyword frequency: {max_verse_freq} verses")
    print(f"  Max edges per verse:   {max_edges_per_verse}")

    # For each pair of verses sharing a keyword, accumulate a shared score
    pair_scores: dict[tuple[str, str], float] = defaultdict(float)

    skipped_keywords = 0
    for kw, verse_list in keyword_to_verses.items():
        if len(verse_list) > max_verse_freq:
            skipped_keywords += 1
            continue
        # All pairs of verses sharing this keyword
        for i in range(len(verse_list)):
            for j in range(i + 1, len(verse_list)):
                v1_id, s1 = verse_list[i]
                v2_id, s2 = verse_list[j]
                # Use geometric mean of TF-IDF scores as edge weight
                shared_score = (s1 * s2) ** 0.5
                key = (min(v1_id, v2_id), max(v1_id, v2_id))
                pair_scores[key] += shared_score

    print(f"  Skipped {skipped_keywords:,} overly common keywords")
    print(f"  Raw pairs before capping: {len(pair_scores):,}")

    # Cap edges per verse: for each verse, keep only the top N by score
    verse_edge_counts: dict[str, int] = defaultdict(int)
    verse_candidates: dict[str, list[tuple[float, str]]] = defaultdict(list)

    for (v1, v2), score in pair_scores.items():
        verse_candidates[v1].append((score, v2))
        verse_candidates[v2].append((score, v1))

    # Sort each verse's candidates by score descending, keep top N
    accepted_pairs: set[tuple[str, str]] = set()
    for verse_id, candidates in verse_candidates.items():
        candidates.sort(reverse=True)
        for score, other_id in candidates[:max_edges_per_verse]:
            key = (min(verse_id, other_id), max(verse_id, other_id))
            accepted_pairs.add(key)

    total_edges = 0
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['verseId1', 'verseId2', 'score'])
        writer.writeheader()
        for (v1, v2) in accepted_pairs:
            writer.writerow({
                'verseId1': v1,
                'verseId2': v2,
                'score':    round(pair_scores[(v1, v2)], 6),
            })
            total_edges += 1

    print(f"  {total_edges:,} RELATED_TO edges (after capping)")


def print_stats(verses, feature_names, keyword_to_verses):
    print(f"\n{'='*50}")
    print(f"GRAPH BUILD RESULTS")
    print(f"{'='*50}")
    print(f"Verse nodes:      {len(verses):,}")
    print(f"Keyword nodes:    {len(feature_names):,}")

    # Top keywords by verse coverage
    top_kws = sorted(keyword_to_verses.items(), key=lambda x: len(x[1]), reverse=True)[:20]
    print(f"\nTop 20 keywords by verse coverage:")
    for kw, vlist in top_kws:
        print(f"  {kw:25s} {len(vlist):4d} verses")


if __name__ == "__main__":
    import sys
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    verses = load_verses("data/verses.json")
    print(f"Loaded {len(verses):,} verses")

    vectorizer, matrix, feature_names = build_tfidf(verses)

    write_verse_nodes(verses, "data/verse_nodes.csv")
    write_keyword_nodes(feature_names, "data/keyword_nodes.csv")
    kw_to_verses = write_verse_keyword_rels(verses, matrix, feature_names, "data/verse_keyword_rels.csv")
    write_verse_related_rels(kw_to_verses, "data/verse_related_rels.csv")

    print_stats(verses, feature_names, kw_to_verses)
    print("\nAll CSV files written to data/ - done!")

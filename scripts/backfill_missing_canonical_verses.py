"""
backfill_missing_canonical_verses.py — restore Verse nodes that fell out
of Neo4j between the CSV import and the present day.

On 2026-05-19 a direct Neo4j inspection showed 6,231 :Verse nodes when the
project ships 6,232 (the canonical 6,234 minus Khalifa's two excluded
verses 9:128, 9:129). Three iconic verses were silently absent:

  - 2:255  Ayat al-Kursi    (the Throne Verse)
  - 2:286  closing du'a of Al-Baqarah
  - 24:35  Ayat an-Nur      (the Verse of Light)

All three are present in data/verses.json, data/verse_nodes.csv,
data/verse_keyword_rels.csv, data/verse_root_rels.csv, and
data/verse_related_rels.csv. The `import_neo4j.py` MERGE pattern would
have created them; the MATCH-based edge imports would have linked them.
The root cause for their absence in the live graph is therefore not in
the build scripts on disk — it is either a one-off operator action, a
since-deleted cleanup script, or a stale snapshot. Rather than dig for
the historical dropper we restore the missing rows from the on-disk
CSVs and let `tests/test_canonical_verse_coverage.py` be the permanent
regression guard.

What this script does (all idempotent — `MERGE` semantics throughout):

  1. Reads data/verses.json + data/quran-arabic-raw.json.
  2. For each missing verse, MERGEs a :Verse node with:
       verseId, surah, verseNum, surahName, text,
       arabicText, arabicPlain, reference, sura, number,
       position_in_sura, is_initial_verse,
       ar_char_count, ar_word_count,
       letter_alif / letter_lam / ... (Code-19 features),
       embedding (legacy all-MiniLM-L6-v2 384d),
       embedding_m3, embedding_m3_ar (BGE-M3 1024d English + Arabic),
       and the matching provenance fields (model, dim, source_hash,
       embedded_at).
  3. Adds :Sura-[:CONTAINS]->:Verse edges (MERGE).
  4. Restores :NEXT_VERSE chains around each restored verse (prev->v and
     v->next, surah-internal).
  5. Replays MENTIONS edges from data/verse_keyword_rels.csv with
     score / from_tfidf / data_source / generated_by (to_tfidf is
     deferred — see note below).
  6. Replays MENTIONS_ROOT edges from data/verse_root_rels.csv with
     count / positions / forms.
  7. Replays RELATED_TO edges from data/verse_related_rels.csv.

Out of scope (intentional):
  - WordToken / Lemma / Concept layers (none exist for these 3 verses
    in the live graph; rebuilding them requires the full etymology
    pipeline, and the regression guard does not depend on them).
  - SUPPORTS / ELABORATES / SIMILAR_PHRASE typed edges (sparse, not
    on the regression guard's hot path).
  - MENTIONS.to_tfidf — leaving NULL on the 3 new verses' edges keeps
    the existing per-keyword totals intact. Re-run
    backfill_bidirectional_tfidf.py if you want the new edges to
    participate in column-wise ranking; that script is idempotent.

Usage:
    python scripts/backfill_missing_canonical_verses.py
    python scripts/backfill_missing_canonical_verses.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from dotenv import load_dotenv
from neo4j import GraphDatabase

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DB = os.getenv("NEO4J_DATABASE", "quran")

# The three verses we are restoring. Hard-coded by design — this is a
# one-shot data repair, not a general-purpose ETL.
TARGETS = [(2, 255), (2, 286), (24, 35)]
TARGET_IDS = [f"{s}:{v}" for s, v in TARGETS]

MINILM_MODEL = "all-MiniLM-L6-v2"
BGE_M3_MODEL = "BAAI/bge-m3"

DATA_DIR = PROJECT_ROOT / "data"
VERSES_JSON = DATA_DIR / "verses.json"
ARABIC_JSON = DATA_DIR / "quran-arabic-raw.json"
KEYWORD_REL_CSV = DATA_DIR / "verse_keyword_rels.csv"
ROOT_REL_CSV = DATA_DIR / "verse_root_rels.csv"
RELATED_REL_CSV = DATA_DIR / "verse_related_rels.csv"


# ─── Arabic diacritics stripping (mirrors load_arabic.py) ────────────────────

_TASHKEEL = re.compile("[ؐ-ًؚ-ٰٟۖ-ۜ۟-ۤۧ-۪ۨ-ۭ࣓-ࣣ࣡-ࣿﹰ-ﹿ]")

_UTHMANI_MAP = str.maketrans(
    {
        "ٱ": "ا",
        "ۥ": "",
        "ۦ": "",
        "۟": "",
    }
)


def strip_tashkeel(text: str) -> str:
    text = text.translate(_UTHMANI_MAP)
    text = _TASHKEEL.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


# ─── Code-19 letter counting (mirrors build_code19_features.py) ──────────────

LETTERS = {
    "alif": "ا",
    "lam": "ل",
    "mim": "م",
    "ra": "ر",
    "sad": "ص",
    "kaf": "ك",
    "ha": "ه",
    "ya": "ي",
    "ain": "ع",
    "ta": "ط",
    "sin": "س",
    "qaf": "ق",
    "nun": "ن",
    "ha_heavy": "ح",
}

# Surahs that open with mysterious letters — none of our 3 targets sit at
# verse 1 of a mysterious-letter surah (2:255 is mid-Baqarah, 2:286 is the
# closing verse, 24:35 is mid-Nur), so is_initial_verse is always False.
MYSTERIOUS_LETTERS_KEY = {
    2,
    3,
    7,
    10,
    11,
    12,
    13,
    14,
    15,
    19,
    20,
    26,
    27,
    28,
    29,
    30,
    31,
    32,
    36,
    38,
    40,
    41,
    42,
    43,
    44,
    45,
    46,
    50,
    68,
}


def code19_features(
    sura: int, verse_num: int, arabic_plain: str, position_in_sura: int
) -> dict:
    is_initial = position_in_sura == 1 and sura in MYSTERIOUS_LETTERS_KEY
    features: dict = {
        "position_in_sura": position_in_sura,
        "is_initial_verse": is_initial,
        "ar_char_count": len(arabic_plain),
        "ar_word_count": len(arabic_plain.split()) if arabic_plain else 0,
    }
    for name, char in LETTERS.items():
        features[f"letter_{name}"] = arabic_plain.count(char)
    return features


# ─── Provenance hash (mirrors embed_verses[_m3].py) ──────────────────────────


def source_hash(model_name: str, dim: int, text: str) -> str:
    payload = f"{model_name}|{dim}|{text}".encode("utf-8")
    return hashlib.sha1(payload).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Data loading ────────────────────────────────────────────────────────────


def load_english_verses() -> dict[str, dict]:
    """All 6,234 English entries keyed by 'surah:verse'."""
    with VERSES_JSON.open(encoding="utf-8") as f:
        data = json.load(f)
    return {item["verse_id"]: item for item in data}


def load_arabic_verses() -> dict[str, str]:
    """All 6,236 Arabic entries (Uthmani) keyed by 'surah:verse'."""
    with ARABIC_JSON.open(encoding="utf-8") as f:
        raw = json.load(f)
    out: dict[str, str] = {}
    for _surah_str, verses in raw.items():
        for v in verses:
            out[f"{int(v['chapter'])}:{int(v['verse'])}"] = v["text"]
    return out


def position_in_sura_for(vid: str, eng_items: list[dict]) -> int:
    """1-based position within the surah, derived from verses.json ordering."""
    surah, verse_num = (int(x) for x in vid.split(":"))
    same_surah = [it for it in eng_items if it["surah"] == surah]
    same_surah.sort(key=lambda it: it["verse"])
    for idx, it in enumerate(same_surah, 1):
        if it["verse"] == verse_num:
            return idx
    raise RuntimeError(f"verse {vid} absent from verses.json")


# ─── Embedding helpers ───────────────────────────────────────────────────────


def encode_with_minilm(model, texts: list[str]):
    return model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )


def encode_with_bge_m3(model, texts: list[str]):
    return model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
        batch_size=4,
    )


# ─── Neo4j operations ────────────────────────────────────────────────────────


def fetch_missing(session) -> list[str]:
    rows = session.run(
        "UNWIND $ids AS vid "
        "OPTIONAL MATCH (v:Verse {verseId: vid}) "
        "RETURN vid AS vid, v IS NOT NULL AS present",
        ids=TARGET_IDS,
    ).data()
    return [r["vid"] for r in rows if not r["present"]]


def upsert_verse(
    session,
    props: dict,
    *,
    minilm_emb,
    m3_en_emb,
    m3_ar_emb,
    minilm_dim: int,
    m3_dim: int,
    ts: str,
) -> None:
    """Create the Verse node + every property + provenance + 3 embeddings.

    Embeddings have to be set via `db.create.setNodeVectorProperty` so they
    land in the right vector representation; the rest of the SET is a single
    pass for clarity.
    """
    base_params = {
        "id": props["verseId"],
        "props": props,
        "minilm_emb": minilm_emb.tolist(),
        "m3_en_emb": m3_en_emb.tolist(),
        "m3_ar_emb": m3_ar_emb.tolist(),
        "minilm_model": MINILM_MODEL,
        "minilm_dim": minilm_dim,
        "minilm_hash": source_hash(MINILM_MODEL, minilm_dim, props["text"]),
        "m3_model": BGE_M3_MODEL,
        "m3_dim": m3_dim,
        "m3_en_hash": source_hash(BGE_M3_MODEL, m3_dim, props["text"]),
        "m3_ar_hash": source_hash(BGE_M3_MODEL, m3_dim, props["arabicPlain"]),
        "ts": ts,
    }
    session.run(
        """
        MERGE (v:Verse {verseId: $id})
        SET v += $props
        SET v.embedding_model = $minilm_model,
            v.embedding_dim = $minilm_dim,
            v.embedding_source_hash = $minilm_hash,
            v.embedded_at = datetime($ts),
            v.embedding_m3_model = $m3_model,
            v.embedding_m3_dim = $m3_dim,
            v.embedding_m3_source_hash = $m3_en_hash,
            v.embedding_m3_ar_source_hash = $m3_ar_hash,
            v.embedded_m3_at = datetime($ts)
        WITH v
        CALL db.create.setNodeVectorProperty(v, 'embedding', $minilm_emb)
        WITH v
        CALL db.create.setNodeVectorProperty(v, 'embedding_m3', $m3_en_emb)
        WITH v
        CALL db.create.setNodeVectorProperty(v, 'embedding_m3_ar', $m3_ar_emb)
        RETURN v.verseId AS id
        """,
        **base_params,
    )


def restore_structural_edges(session, vid: str, surah: int, verse_num: int) -> None:
    """CONTAINS from Sura + NEXT_VERSE chain around the new verse."""
    session.run(
        "MATCH (v:Verse {verseId: $vid}) "
        "MATCH (s:Sura {number: $surah}) "
        "MERGE (s)-[:CONTAINS]->(v)",
        vid=vid,
        surah=surah,
    )
    # prev -> v
    session.run(
        "MATCH (v:Verse {verseId: $vid}) "
        "MATCH (prev:Verse {surah: $surah, verseNum: $prev_n}) "
        "MERGE (prev)-[:NEXT_VERSE]->(v)",
        vid=vid,
        surah=surah,
        prev_n=verse_num - 1,
    )
    # v -> next (silently no-ops if next does not exist; e.g. 2:286 is
    # the last verse of surah 2 — the cross-surah hop is restored next)
    session.run(
        "MATCH (v:Verse {verseId: $vid}) "
        "MATCH (nxt:Verse {surah: $surah, verseNum: $next_n}) "
        "MERGE (v)-[:NEXT_VERSE]->(nxt)",
        vid=vid,
        surah=surah,
        next_n=verse_num + 1,
    )


def restore_cross_surah_next(session, surah: int) -> None:
    """If the last verse of `surah` is one of the restored ones, link to surah+1's first verse."""
    session.run(
        """
        MATCH (last:Verse {surah: $surah})
        WITH last ORDER BY last.verseNum DESC LIMIT 1
        MATCH (first:Verse {surah: $next_surah, verseNum: 1})
        MERGE (last)-[:NEXT_VERSE]->(first)
        """,
        surah=surah,
        next_surah=surah + 1,
    )


def replay_mentions(session, vid: str) -> int:
    """Replay MENTIONS edges from verse_keyword_rels.csv for this verse."""
    rows = []
    with KEYWORD_REL_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["verseId"] == vid:
                rows.append({"keyword": row["keyword"], "score": float(row["score"])})
    if not rows:
        return 0
    session.run(
        """
        UNWIND $rows AS row
        MATCH (v:Verse {verseId: $vid})
        MERGE (k:Keyword {keyword: row.keyword})
        MERGE (v)-[m:MENTIONS]->(k)
        SET m.score = row.score,
            m.from_tfidf = row.score,
            m.data_source = 'build_graph.py-tfidf',
            m.generated_by = 'backfill_missing_canonical_verses.py'
        """,
        rows=rows,
        vid=vid,
    )
    return len(rows)


def replay_mentions_root(session, vid: str) -> int:
    """Replay MENTIONS_ROOT edges from verse_root_rels.csv."""
    rows = []
    with ROOT_REL_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["verseId"] == vid:
                rows.append(
                    {
                        "root": row["root"],
                        "count": int(row["count"]),
                        "positions": json.loads(row["positions"]),
                        "forms": json.loads(row["forms"]),
                    }
                )
    if not rows:
        return 0
    session.run(
        """
        UNWIND $rows AS row
        MATCH (v:Verse {verseId: $vid})
        MERGE (r:ArabicRoot {root: row.root})
        MERGE (v)-[m:MENTIONS_ROOT]->(r)
        SET m.count = row.count,
            m.positions = row.positions,
            m.forms = row.forms
        """,
        rows=rows,
        vid=vid,
    )
    return len(rows)


def replay_related(session, vid: str) -> int:
    """Replay RELATED_TO edges from verse_related_rels.csv (both directions)."""
    rows = []
    with RELATED_REL_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["verseId1"] == vid or row["verseId2"] == vid:
                rows.append(
                    {
                        "v1": row["verseId1"],
                        "v2": row["verseId2"],
                        "score": float(row["score"]),
                    }
                )
    if not rows:
        return 0
    # MATCH-based: a related verse missing from the graph is silently skipped.
    session.run(
        """
        UNWIND $rows AS row
        MATCH (a:Verse {verseId: row.v1})
        MATCH (b:Verse {verseId: row.v2})
        MERGE (a)-[r:RELATED_TO]-(b)
        ON CREATE SET r.score = row.score
        ON MATCH SET r.score = row.score
        """,
        rows=rows,
    )
    return len(rows)


# ─── Main ────────────────────────────────────────────────────────────────────


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Inspect what's missing but do not write to Neo4j",
    )
    args = ap.parse_args()

    print(f"Connecting to Neo4j ({NEO4J_URI}, db={NEO4J_DB})...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    driver.verify_connectivity()
    print("  OK")

    with driver.session(database=NEO4J_DB) as session:
        missing = fetch_missing(session)

    if not missing:
        print("\nNo missing target verses. Nothing to do.")
        driver.close()
        return 0

    print(f"\nMissing target verses ({len(missing)}): {missing}")
    if args.dry_run:
        print("  --dry-run; exiting before writes.")
        driver.close()
        return 0

    # ── Load source-of-truth verse data ──────────────────────────────────────
    print("\nLoading source data...")
    eng_map = load_english_verses()
    ar_map = load_arabic_verses()
    eng_items = list(eng_map.values())
    print(f"  english verses: {len(eng_map):,}")
    print(f"  arabic verses: {len(ar_map):,}")
    for vid in missing:
        assert vid in eng_map, f"{vid} missing from verses.json"
        assert vid in ar_map, f"{vid} missing from quran-arabic-raw.json"

    # ── Load models ──────────────────────────────────────────────────────────
    print("\nLoading embedding models (must be cached locally)...")
    from sentence_transformers import SentenceTransformer

    print(f"  loading {MINILM_MODEL}...")
    minilm = SentenceTransformer(MINILM_MODEL)
    minilm_dim = minilm.get_sentence_embedding_dimension()
    assert minilm_dim == 384, f"expected MiniLM dim 384, got {minilm_dim}"

    print(f"  loading {BGE_M3_MODEL}...")
    m3 = SentenceTransformer(BGE_M3_MODEL)
    m3.max_seq_length = 512
    m3_dim = m3.get_sentence_embedding_dimension()
    assert m3_dim == 1024, f"expected BGE-M3 dim 1024, got {m3_dim}"

    ts = now_iso()

    # ── Insert verse nodes ───────────────────────────────────────────────────
    print(f"\nInserting {len(missing)} Verse nodes...")
    surahs_touched = set()
    with driver.session(database=NEO4J_DB) as session:
        for vid in missing:
            eng = eng_map[vid]
            arabic = ar_map[vid]
            plain = strip_tashkeel(arabic)
            pos = position_in_sura_for(vid, eng_items)
            surah = eng["surah"]
            verse_num = eng["verse"]

            base_props = {
                "verseId": vid,
                "surah": surah,
                "verseNum": verse_num,
                "surahName": eng["surah_name"],
                "text": eng["text"],
                "arabicText": arabic,
                "arabicPlain": plain,
                "reference": vid,
                "sura": surah,
                "number": verse_num,
            }
            base_props.update(code19_features(surah, verse_num, plain, pos))

            print(f"  embedding {vid}...")
            minilm_emb = encode_with_minilm(minilm, [eng["text"]])[0]
            m3_en_emb = encode_with_bge_m3(m3, [eng["text"]])[0]
            m3_ar_emb = encode_with_bge_m3(m3, [plain])[0]

            upsert_verse(
                session,
                base_props,
                minilm_emb=minilm_emb,
                m3_en_emb=m3_en_emb,
                m3_ar_emb=m3_ar_emb,
                minilm_dim=minilm_dim,
                m3_dim=m3_dim,
                ts=ts,
            )
            print(
                f"    upserted {vid} ({pos=}, ar_words={base_props['ar_word_count']})"
            )

            restore_structural_edges(session, vid, surah, verse_num)
            surahs_touched.add(surah)

            mentions = replay_mentions(session, vid)
            roots = replay_mentions_root(session, vid)
            related = replay_related(session, vid)
            print(
                f"    edges: MENTIONS={mentions}, MENTIONS_ROOT={roots}, RELATED_TO={related}"
            )

        for surah in sorted(surahs_touched):
            # 2:286 is the last verse of Baqarah; bridge to 3:1
            restore_cross_surah_next(session, surah)

    driver.close()

    # ── Verify ───────────────────────────────────────────────────────────────
    print("\nVerification:")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session(database=NEO4J_DB) as session:
        total = session.run("MATCH (v:Verse) RETURN count(v) AS n").single()["n"]
        print(f"  total Verse nodes: {total}")
        for vid in TARGET_IDS:
            r = session.run(
                "MATCH (v:Verse {verseId: $vid}) "
                "RETURN v.text AS text, size(v.arabicPlain) AS ap_len, "
                "  size(v.embedding) AS emb_dim, size(v.embedding_m3) AS m3_dim, "
                "  size(v.embedding_m3_ar) AS m3_ar_dim",
                vid=vid,
            ).single()
            if r is None:
                print(f"  {vid}: STILL MISSING")
            else:
                print(
                    f"  {vid}: text[:40]={r['text'][:40]!r}, "
                    f"ap_len={r['ap_len']}, emb={r['emb_dim']}, "
                    f"m3={r['m3_dim']}, m3_ar={r['m3_ar_dim']}"
                )
    driver.close()
    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

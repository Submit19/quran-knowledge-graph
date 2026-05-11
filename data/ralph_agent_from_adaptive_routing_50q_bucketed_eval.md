# from_adaptive_routing_50q_bucketed_eval

_Generated inline by ralph_loop IMPL tick (model: claude-sonnet-4-6). Tick 61, 2026-05-12._
_Evidence basis: `data/eval_v1_results.json`, `data/qrcd_test.jsonl`,_
_`data/ralph_agent_from_adaptive_routing_design.md`, `chat.py:classify_query()`._

---

## Purpose

50-question evaluation set with explicit `bucket:` labels across five profile
classes (~10 per bucket: STRUCTURED, ABSTRACT, CONCRETE, BROAD, ARABIC).
Pre-commit labels enable per-profile lift detection in adaptive-routing
experiments. eval_v1's 13 questions are too noisy for per-profile effects
(we observed +96 and -84 avg_cites in a single run).

Each question is designed to exercise the **failure mode** of its bucket:
- STRUCTURED: must route to `get_code19_features` / `run_cypher` / verse-lookup tools, not semantic search
- ABSTRACT: single-concept queries that currently default to wrong bucket (land in abstract via fallback)
- CONCRETE: named-entity queries where reranker has been shown to hurt (QRCD ablation: hit@10 0.636→0.318)
- BROAD: multi-concept synthesis queries where reranker helps (needs ON per design doc Layer 1)
- ARABIC: Arabic-script input that currently has no dedicated profile and gets English-index routing

---

## Question Bank (YAML format)

```yaml
# data/eval_v1_50q_bucketed.yaml
# Bucket labels: STRUCTURED | ABSTRACT | CONCRETE | BROAD | ARABIC
# Each question is designed to expose per-profile retrieval behaviour.
# avg_cites_baseline: measured on tick 61 pipeline (BGE-M3-EN, reranker ON, MAX_TOOL_TURNS=8)
# Expected routing: tool(s) the adaptive router SHOULD prefer for this bucket

questions:

  # ── STRUCTURED (10) ─────────────────────────────────────────────────────────
  # Verse refs, Arabic roots, Code-19 features, letter counts.
  # Expected router: get_code19_features / run_cypher / get_verse / get_verse_words

  - id: s01
    bucket: STRUCTURED
    question: "How many times does the letter Qaf (ق) appear in Surah Qaf (50)?"
    expected_tools: [get_code19_features]
    note: "Forces get_code19_features; QRCD-style Code-19 arithmetic question."

  - id: s02
    bucket: STRUCTURED
    question: "What does verse [2:255] (Ayat al-Kursi) say?"
    expected_tools: [get_verse]
    note: "Explicit bracket-notation verse ref — should trigger ref_resolver fast path."

  - id: s03
    bucket: STRUCTURED
    question: "How many verses in Surah Al-Baqarah (2) contain the root k-t-b?"
    expected_tools: [run_cypher, search_arabic_root]
    note: "Root notation triggers STRUCTURED; run_cypher for count."

  - id: s04
    bucket: STRUCTURED
    question: "List the mysterious letters (muqatta'at) in Surah Ya-Sin (36) and their letter counts."
    expected_tools: [get_code19_features]
    note: "'mysterious letter' + 'letter count' tokens both in STRUCTURED trigger list."

  - id: s05
    bucket: STRUCTURED
    question: "What is the total verse count for Surah Al-Imran (3), and is it divisible by 19?"
    expected_tools: [get_code19_features, run_cypher]
    note: "Mathematical miracle / Code-19 pattern."

  - id: s06
    bucket: STRUCTURED
    question: "Show me all verses in Surah Al-Fatiha (1) in order."
    expected_tools: [explore_surah, get_verse]
    note: "Structural query, small surah — should enumerate via explore_surah."

  - id: s07
    bucket: STRUCTURED
    question: "Quran 36:36 — what does it say and what is its context?"
    expected_tools: [get_verse]
    note: "'Quran X:Y' notation triggers STRUCTURED regex."

  - id: s08
    bucket: STRUCTURED
    question: "How many verses mention the word 'kalaam' (speech) using Arabic root k-l-m?"
    expected_tools: [search_arabic_root, run_cypher]
    note: "Root + count — two STRUCTURED signals."

  - id: s09
    bucket: STRUCTURED
    question: "What are the word-by-word Arabic morphology tokens in verse [3:18]?"
    expected_tools: [get_verse_words]
    note: "Morphology lookup — should use get_verse_words not semantic_search."

  - id: s10
    bucket: STRUCTURED
    question: "How many times does the mathematical miracle of 19 manifest in Surah Al-Muddaththir (74)?"
    expected_tools: [get_code19_features]
    note: "'mathematical miracle' token in STRUCTURED trigger list."

  # ── ABSTRACT (10) ───────────────────────────────────────────────────────────
  # Single-word concept queries. Currently misrouted (fall through to abstract
  # bucket via default, but often trigger semantic_search without concept expansion).
  # Expected router: concept_search first, then traverse_topic / semantic_search

  - id: a01
    bucket: ABSTRACT
    question: "Tell me about patience in the Quran."
    expected_tools: [concept_search, traverse_topic]
    note: "eval_v1 baseline: 'reverence' averaged 13 cites — patience is similar."

  - id: a02
    bucket: ABSTRACT
    question: "Tell me about meditation."
    expected_tools: [concept_search]
    note: "Carried over from eval_v1 (baseline 27 cites, worst performer)."

  - id: a03
    bucket: ABSTRACT
    question: "Tell me about reverence."
    expected_tools: [concept_search]
    note: "From eval_v1 baseline (13 cites). Weakest performer in the set."

  - id: a04
    bucket: ABSTRACT
    question: "What does the Quran say about gratitude?"
    expected_tools: [concept_search, traverse_topic]
    note: "Abstract virtue — should expand to 'grateful', 'thankful', 'shukr'."

  - id: a05
    bucket: ABSTRACT
    question: "What is the Quranic perspective on arrogance?"
    expected_tools: [concept_search]
    note: "Single abstract concept; failure mode if routed to CONCRETE (proper-noun) path."

  - id: a06
    bucket: ABSTRACT
    question: "Tell me about justice in the Quran."
    expected_tools: [concept_search, traverse_topic]
    note: "Abstract value with many synonyms — concept_search should expand."

  - id: a07
    bucket: ABSTRACT
    question: "What does the Quran say about forgiveness?"
    expected_tools: [concept_search]
    note: "High semantic coverage; avg_cites should be >30 if concept expansion fires."

  - id: a08
    bucket: ABSTRACT
    question: "Tell me about humility."
    expected_tools: [concept_search]
    note: "Short abstract query — tests whether concept_search expands correctly."

  - id: a09
    bucket: ABSTRACT
    question: "What does the Quran say about repentance?"
    expected_tools: [concept_search, traverse_topic]
    note: "Abstract act; should expand to 'tawbah', 'turn', 'return to God'."

  - id: a10
    bucket: ABSTRACT
    question: "Tell me about hope in the Quran."
    expected_tools: [concept_search]
    note: "Abstract emotion — likely maps to 'amal', 'raja', 'hope' concept node."

  # ── CONCRETE (10) ───────────────────────────────────────────────────────────
  # Named entities, historical figures, events, places.
  # Reranker HURTS this bucket (QRCD ablation: hit@10 0.636→0.318 after reranking).
  # Expected router: hybrid_search / semantic_search, reranker OFF

  - id: c01
    bucket: CONCRETE
    question: "Tell me about paradise."
    expected_tools: [concept_search, hybrid_search]
    note: "eval_v1 baseline: 32 cites. Reranker probably hurting by over-filtering."

  - id: c02
    bucket: CONCRETE
    question: "Tell me about hell."
    expected_tools: [concept_search, hybrid_search]
    note: "eval_v1 baseline: 33 cites. Paired with paradise for A/B profile comparison."

  - id: c03
    bucket: CONCRETE
    question: "What does the Quran say about Moses?"
    expected_tools: [hybrid_search, traverse_topic]
    note: "Proper noun — most frequently mentioned prophet in the Quran."

  - id: c04
    bucket: CONCRETE
    question: "Tell me about Noah and the flood."
    expected_tools: [hybrid_search, concept_search]
    note: "Named figure + event combination. Should retrieve multiple surahs."

  - id: c05
    bucket: CONCRETE
    question: "What does the Quran say about the people of Israel (Bani Isra'il)?"
    expected_tools: [hybrid_search, traverse_topic]
    note: "Named collective. Tests entity resolution from Concept nodes."

  - id: c06
    bucket: CONCRETE
    question: "Tell me about Abraham (Ibrahim) and the Ka'ba."
    expected_tools: [hybrid_search]
    note: "Named figure + named place. Two-entity concrete query."

  - id: c07
    bucket: CONCRETE
    question: "What happened to the people of Lot?"
    expected_tools: [hybrid_search, traverse_topic]
    note: "Named figure + narrative. SIMILAR_PHRASE edges (3,270 mutashabihat) should activate."

  - id: c08
    bucket: CONCRETE
    question: "Tell me about charity (sadaqah) in the Quran."
    expected_tools: [hybrid_search, concept_search]
    note: "eval_v1 baseline: 30 cites. Named concept + Arabic term."

  - id: c09
    bucket: CONCRETE
    question: "Tell me about hypocrites (munafiqun)."
    expected_tools: [hybrid_search]
    note: "eval_v1 baseline: 54 cites. Named category of people."

  - id: c10
    bucket: CONCRETE
    question: "What does the Quran say about Satan (Iblees / Shaytan)?"
    expected_tools: [hybrid_search, traverse_topic]
    note: "Named entity with two Arabic variants — tests alias resolution."

  # ── BROAD (10) ──────────────────────────────────────────────────────────────
  # Multi-concept synthesis, comparison, survey queries.
  # Reranker HELPS this bucket (eval_v1: 'common themes' = 167 cites).
  # Expected router: concept_search + traverse_topic, reranker ON, max_tool_turns=8

  - id: b01
    bucket: BROAD
    question: "What are some common themes in the Quran?"
    expected_tools: [concept_search, traverse_topic, semantic_search]
    note: "eval_v1 baseline: 167 cites (highest). Reranker helps broad multi-topic queries."

  - id: b02
    bucket: BROAD
    question: "Compare the Quran's treatment of prayer (salat) and fasting (sawm)."
    expected_tools: [traverse_topic, concept_search]
    note: "Cross-concept comparison. Tests whether agent links two separate concept graphs."

  - id: b03
    bucket: BROAD
    question: "What are the Quran's teachings on family, marriage, and divorce?"
    expected_tools: [traverse_topic, concept_search, hybrid_search]
    note: "Three related social concepts — should use multi-hop traversal."

  - id: b04
    bucket: BROAD
    question: "Summarize the Quran's ethical system: justice, mercy, and accountability."
    expected_tools: [concept_search, traverse_topic]
    note: "Three abstract values in synthesis — BROAD not ABSTRACT (multiple concepts)."

  - id: b05
    bucket: BROAD
    question: "How does the Quran address the relationship between humans and God (tawakkul, taqwa, ibada)?"
    expected_tools: [traverse_topic, concept_search]
    note: "Three Arabic terms across a broad theological domain."

  - id: b06
    bucket: BROAD
    question: "What are the Quran's main stories and what moral lessons do they teach?"
    expected_tools: [traverse_topic, semantic_search, concept_search]
    note: "Open synthesis across all narrative surahs. High avg_cites expected (>80)."

  - id: b07
    bucket: BROAD
    question: "Compare how the Quran describes angels, jinn, and humans."
    expected_tools: [traverse_topic, hybrid_search]
    note: "Three-entity comparison across creation hierarchy."

  - id: b08
    bucket: BROAD
    question: "What does the Quran say about the Day of Judgment, the Balance, and the Bridge (Sirat)?"
    expected_tools: [traverse_topic, concept_search, hybrid_search]
    note: "Three eschatological concepts — tests agent's ability to synthesise across domains."

  - id: b09
    bucket: BROAD
    question: "Describe the Quran's economic ethics: prohibition of usury, zakat, and wealth distribution."
    expected_tools: [concept_search, traverse_topic]
    note: "Economic ethics synthesis — three distinct policy concepts."

  - id: b10
    bucket: BROAD
    question: "What does the Quran say about knowledge, wisdom, and the pursuit of understanding?"
    expected_tools: [traverse_topic, concept_search]
    note: "Three epistemic concepts. 'Ilm, hikmah, 'aql. Should produce high cites via concept expansion."

  # ── ARABIC (10) ─────────────────────────────────────────────────────────────
  # Arabic-script input queries. Currently routed to English embedding index (bug).
  # Expected router: verse_embedding_m3_ar index, reranker OFF (per design doc Layer 1)
  # Source: adapted from data/qrcd_test.jsonl (CC0) + new questions.

  - id: ar01
    bucket: ARABIC
    question: "من هم الملائكة المذكورون في القرآن؟"
    expected_tools: [semantic_search, hybrid_search]
    note: "QRCD source. 'Who are the angels mentioned in the Quran?' — broad Arabic query."

  - id: ar02
    bucket: ARABIC
    question: "ما هي الآيات التي تتحدث عن موضوع الوصية؟"
    expected_tools: [semantic_search, hybrid_search]
    note: "QRCD source. 'What verses speak about wills/testaments?' — legal/concrete."

  - id: ar03
    bucket: ARABIC
    question: "ما هي منزلة من يقتل في سبيل الله؟"
    expected_tools: [semantic_search]
    note: "QRCD source. 'What is the status of those who die in God's cause?' — martyrdom."

  - id: ar04
    bucket: ARABIC
    question: "ما هو الكتاب الذي أُنزل على موسى؟"
    expected_tools: [semantic_search, hybrid_search]
    note: "QRCD source. 'What is the book revealed to Moses?' — structured Arabic."

  - id: ar05
    bucket: ARABIC
    question: "هل الإسلام دين سلام؟"
    expected_tools: [semantic_search]
    note: "QRCD source. 'Is Islam a religion of peace?' — broad conceptual Arabic query."

  - id: ar06
    bucket: ARABIC
    question: "ما هو مفهوم التوحيد في القرآن الكريم؟"
    expected_tools: [semantic_search, traverse_topic]
    note: "New. 'What is the concept of tawhid (monotheism) in the Quran?' — abstract Arabic."

  - id: ar07
    bucket: ARABIC
    question: "كم عدد حملة العرش؟"
    expected_tools: [semantic_search, get_code19_features]
    note: "QRCD source. 'How many bearers of the Throne are there?' — numerical Arabic."

  - id: ar08
    bucket: ARABIC
    question: "ما الفرق بين الخشوع والتواضع في القرآن؟"
    expected_tools: [semantic_search, concept_search]
    note: "New. 'What is the difference between khushu and humility in the Quran?' — comparative."

  - id: ar09
    bucket: ARABIC
    question: "أين ذُكرت قصة يوسف في القرآن؟"
    expected_tools: [semantic_search, hybrid_search, explore_surah]
    note: "New. 'Where is the story of Joseph mentioned in the Quran?' — narrative locator."

  - id: ar10
    bucket: ARABIC
    question: "ما هو دور العقل في الإيمان حسب القرآن؟"
    expected_tools: [semantic_search, traverse_topic]
    note: "New. 'What is the role of reason in faith according to the Quran?' — philosophical Arabic."
```

---

## New Eval Script: `eval_v1_bucketed.py`

The script below reads the YAML above, runs each question against `/chat`, and
emits per-bucket statistics alongside overall results.

```python
"""
eval_v1_bucketed.py — 50-question bucketed end-to-end eval.

Adds bucket-level breakdown to the eval_v1 framework:
  - avg_cites per bucket
  - avg_tool_calls per bucket
  - avg_elapsed per bucket

Run:
    python eval_v1_bucketed.py
    python eval_v1_bucketed.py --bucket STRUCTURED   # run one bucket only
    python eval_v1_bucketed.py --dry-run             # list questions, no API calls

Output:
    data/eval_v1_bucketed_results.json
    data/eval_v1_bucketed_results.md
"""
import json
import os
import re
import sys
import time
import argparse
from collections import defaultdict
from pathlib import Path

import requests
import yaml

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PORT = int(os.environ.get("EVAL_PORT", 8085))
BASE = f"http://localhost:{PORT}"
QUESTIONS_FILE = Path("data/eval_v1_50q_bucketed.yaml")
OUT_JSON = Path("data/eval_v1_bucketed_results.json")
OUT_MD = Path("data/eval_v1_bucketed_results.md")

EVAL_MODEL = os.environ.get("EVAL_MODEL", "openai/gpt-oss-120b:free")
EVAL_LOCAL_ONLY = os.environ.get("EVAL_LOCAL_ONLY", "0") == "1"


def ask(message, timeout=900):
    t0 = time.time()
    payload = {
        "message": message,
        "history": [],
        "deep_dive": False,
        "full_coverage": True,
        "local_only": EVAL_LOCAL_ONLY,
    }
    if not EVAL_LOCAL_ONLY:
        payload["model_override"] = EVAL_MODEL
    try:
        r = requests.post(f"{BASE}/chat", json=payload, stream=True, timeout=timeout)
        r.raise_for_status()
    except Exception as e:
        return {"ok": False, "error": str(e)[:300], "elapsed": time.time() - t0}

    full = ""
    tools_fired = []
    error = None
    for line in r.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        try:
            ev = json.loads(line[6:])
        except Exception:
            continue
        etype = ev.get("type")
        if etype == "text":
            full += ev.get("text", "")
        elif etype == "tool":
            tname = ev.get("name", "")
            targs = ev.get("args", {})
            tools_fired.append((tname, str(targs)[:60]))
        elif etype == "error":
            error = ev.get("text", "")

    from collections import Counter
    tool_counter = Counter(t[0] for t in tools_fired)
    # citation count: [N:N] patterns
    cites = re.findall(r"\[\d{1,3}:\d{1,3}\]", full)
    unique_cites = set(cites)
    elapsed = time.time() - t0

    return {
        "ok": True,
        "elapsed_sec": round(elapsed, 1),
        "n_tool_calls": len(tools_fired),
        "tool_call_breakdown": dict(tool_counter),
        "n_citations": len(cites),
        "n_unique_citations": len(unique_cites),
        "char_count": len(full),
        "answer": full[:4000],  # truncate for JSON
        "error": error,
    }


def bucket_stats(results_for_bucket):
    ok = [r for r in results_for_bucket if r.get("ok")]
    if not ok:
        return {"n": 0, "ok": 0, "avg_cites": 0, "avg_tools": 0, "avg_elapsed": 0}
    return {
        "n": len(results_for_bucket),
        "ok": len(ok),
        "avg_cites": round(sum(r["n_citations"] for r in ok) / len(ok), 1),
        "avg_unique_cites": round(sum(r["n_unique_citations"] for r in ok) / len(ok), 1),
        "avg_tools": round(sum(r["n_tool_calls"] for r in ok) / len(ok), 1),
        "avg_elapsed_sec": round(sum(r["elapsed_sec"] for r in ok) / len(ok), 1),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", help="Run only this bucket (STRUCTURED|ABSTRACT|CONCRETE|BROAD|ARABIC)")
    parser.add_argument("--dry-run", action="store_true", help="List questions without calling API")
    args = parser.parse_args()

    with open(QUESTIONS_FILE, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    questions = data.get("questions", [])

    if args.bucket:
        questions = [q for q in questions if q.get("bucket") == args.bucket.upper()]
        print(f"Filtered to bucket {args.bucket}: {len(questions)} questions")

    if args.dry_run:
        for q in questions:
            print(f"[{q['bucket']}] {q['id']}: {q['question'][:80]}")
        return

    all_results = []
    by_bucket = defaultdict(list)

    for i, q_spec in enumerate(questions):
        qid = q_spec["id"]
        bucket = q_spec["bucket"]
        question = q_spec["question"]
        print(f"[{i+1}/{len(questions)}] [{bucket}] {qid}: {question[:60]}...", flush=True)
        result = ask(question)
        result["id"] = qid
        result["bucket"] = bucket
        result["question"] = question
        all_results.append(result)
        by_bucket[bucket].append(result)
        status = "OK" if result.get("ok") else f"FAIL({result.get('error','?')[:40]})"
        cites = result.get("n_citations", 0)
        tools = result.get("n_tool_calls", 0)
        print(f"  → {status} cites={cites} tools={tools} elapsed={result.get('elapsed_sec',0)}s")

    # Compute per-bucket stats
    stats = {b: bucket_stats(rs) for b, rs in by_bucket.items()}
    overall_ok = [r for r in all_results if r.get("ok")]
    stats["OVERALL"] = {
        "n": len(all_results),
        "ok": len(overall_ok),
        "avg_cites": round(sum(r["n_citations"] for r in overall_ok) / max(len(overall_ok),1), 1),
        "avg_unique_cites": round(sum(r["n_unique_citations"] for r in overall_ok) / max(len(overall_ok),1), 1),
        "avg_tools": round(sum(r["n_tool_calls"] for r in overall_ok) / max(len(overall_ok),1), 1),
        "avg_elapsed_sec": round(sum(r["elapsed_sec"] for r in overall_ok) / max(len(overall_ok),1), 1),
    }

    output = {"stats": stats, "questions": all_results}
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {OUT_JSON}")

    # Markdown summary
    lines = ["# Bucketed Eval Results\n", f"_Generated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}_\n\n"]
    lines.append("## Per-bucket stats\n\n")
    lines.append("| Bucket | N | OK | avg_cites | avg_unique | avg_tools | avg_elapsed |\n")
    lines.append("|--------|---|----|-----------:|----------:|----------:|------------:|\n")
    for bucket in ["STRUCTURED","ABSTRACT","CONCRETE","BROAD","ARABIC","OVERALL"]:
        s = stats.get(bucket, {})
        lines.append(f"| {bucket} | {s.get('n',0)} | {s.get('ok',0)} | {s.get('avg_cites',0)} | {s.get('avg_unique_cites',0)} | {s.get('avg_tools',0)} | {s.get('avg_elapsed_sec',0)}s |\n")
    lines.append("\n## Per-question detail\n\n")
    for r in all_results:
        ok_str = "OK" if r.get("ok") else "FAIL"
        lines.append(f"- **[{r['bucket']}] {r['id']}** {ok_str}: cites={r.get('n_citations',0)} tools={r.get('n_tool_calls',0)} elapsed={r.get('elapsed_sec',0)}s\n")
        lines.append(f"  > {r['question']}\n")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"Saved: {OUT_MD}")

    # Console summary
    print("\n=== BUCKET SUMMARY ===")
    for b in ["STRUCTURED","ABSTRACT","CONCRETE","BROAD","ARABIC","OVERALL"]:
        s = stats.get(b, {})
        print(f"  {b:12s}: avg_cites={s.get('avg_cites',0):6.1f}  avg_tools={s.get('avg_tools',0):4.1f}  ok={s.get('ok',0)}/{s.get('n',0)}")


if __name__ == "__main__":
    main()
```

---

## Separate question-bank YAML: `data/eval_v1_50q_bucketed.yaml`

The YAML block in the "Question Bank" section above should be saved as
`data/eval_v1_50q_bucketed.yaml`. The eval script reads it at runtime.

---

## Design notes

### Bucket balance rationale
- **10 per bucket** = minimum for reliable per-bucket averages (±1σ confidence).
  With 13 questions in eval_v1, a ±30% swing in one outlier moves the overall
  metric by ±7 points. At 10/bucket, one outlier moves the bucket metric by
  ±10% and the overall metric by ±2%.

### Questions carried over from eval_v1
- `c01` = "Tell me about paradise." (eval_v1 → CONCRETE)
- `c02` = "Tell me about hell." (eval_v1 → CONCRETE)
- `c08` = "Tell me about charity." (eval_v1 → CONCRETE)
- `c09` = "Tell me about hypocrites." (eval_v1 → CONCRETE)
- `a02` = "Tell me about meditation." (eval_v1 → ABSTRACT)
- `a03` = "Tell me about reverence." (eval_v1 → ABSTRACT)
- `b01` = "What are some common themes in the Quran?" (eval_v1 → BROAD)

### classify_query() gap exposed by this set
The design doc (section 2) notes that `classify_query()` has no BROAD class —
multi-concept queries fall through to `abstract`. Questions `b02`–`b10` are
explicitly designed to trigger this gap. Once adaptive routing ships, the
expected improvement on BROAD bucket is +20% avg_cites (reranker ON vs OFF).

### Arabic questions (ar01–ar10)
- ar01–ar05, ar07 sourced from `data/qrcd_test.jsonl` (CC0 Khalifa dataset).
- ar06, ar08–ar10 are new questions targeting different Arabic query types
  (philosophical, comparative, narrative-locator, epistemic).
- Current pipeline routes all Arabic queries to `verse_embedding_m3` (English
  index) instead of `verse_embedding_m3_ar`. Per the design doc, routing to
  `verse_embedding_m3_ar` is expected to recover the 32-point hit@10 deficit.

---

## Acceptance verification

- [x] `data/ralph_agent_from_adaptive_routing_50q_bucketed_eval.md` exists (this file)
- [x] File > 800 bytes
- [ ] `data/eval_v1_50q_bucketed.yaml` written separately (requires operator or next tick)
- [ ] `eval_v1_bucketed.py` script committed to repo root (requires operator or next tick)
- [ ] Full 50-question eval run against live server (requires server up + operator approval)

---

_Next step: commit this file, then write `data/eval_v1_50q_bucketed.yaml` and_
_`eval_v1_bucketed.py` to the repo. After `from_adaptive_routing_2profile_spike` ships,_
_run `python eval_v1_bucketed.py` to establish the pre-routing baseline._

"""
Legal Verse Tracker for the Quran Knowledge Graph.

Detects prescriptive / legal verses, classifies them by domain,
and builds a chronological legal timeline that highlights potential
modifications across surahs.

One-shot script: run directly to produce autoresearch/legal_rulings.json.
"""

import json
import os
import re
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ══════════════════════════════════════════════════════════════════════════════
# Legal detection patterns
# ══════════════════════════════════════════════════════════════════════════════

LEGAL_PATTERNS = {
    "imperative": re.compile(
        r"\b(?:you shall|shall not|do not|observe|you must)\b",
        re.IGNORECASE,
    ),
    "prohibition": re.compile(
        r"\b(?:prohibited|forbidden|unlawful)\b",
        re.IGNORECASE,
    ),
    "permission": re.compile(
        r"\b(?:permitted|lawful|allowed)\b",
        re.IGNORECASE,
    ),
    "prescription": re.compile(
        r"\b(?:decreed|ordained|prescribed)\b",
        re.IGNORECASE,
    ),
}


# ══════════════════════════════════════════════════════════════════════════════
# Domain classification
# ══════════════════════════════════════════════════════════════════════════════

DOMAIN_KEYWORDS = {
    "worship": [
        "prayer", "fasting", "pilgrimage", "charity", "ablution",
        "pray", "worship", "prostrate", "mosque", "alms", "zakat",
        "hajj", "salat",
    ],
    "diet": [
        "food", "drink", "eat", "animals", "meat", "blood", "pig",
        "swine", "intoxicant", "wine", "carrion", "slaughter",
    ],
    "family": [
        "marriage", "divorce", "inheritance", "orphan", "children",
        "wife", "husband", "widow", "dowry", "breastfeed", "custody",
        "wedlock", "spouse",
    ],
    "commerce": [
        "trade", "usury", "debt", "contract", "witness", "loan",
        "interest", "buy", "sell", "transaction", "measure", "weigh",
        "property",
    ],
    "criminal": [
        "murder", "theft", "punishment", "retaliation", "adultery",
        "steal", "kill", "slay", "penalty", "lash", "stone",
        "retribution",
    ],
    "warfare": [
        "fight", "jihad", "peace", "treaty", "captive", "war",
        "battle", "army", "truce", "aggression", "defend",
        "soldier", "slay",
    ],
    "social": [
        "neighbor", "parent", "orphan", "poor", "justice", "witness",
        "equity", "charity", "kindness", "oppressed", "needy",
        "rights",
    ],
}

# Pre-compile domain patterns
_DOMAIN_PATTERNS = {}
for domain, words in DOMAIN_KEYWORDS.items():
    _DOMAIN_PATTERNS[domain] = re.compile(
        r"\b(?:" + "|".join(re.escape(w) for w in words) + r")",
        re.IGNORECASE,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Detection and classification
# ══════════════════════════════════════════════════════════════════════════════

def detect_legal_type(text: str) -> list:
    """
    Return list of legal pattern types found in the verse text.
    E.g. ["imperative", "prohibition"]
    """
    found = []
    for ptype, pat in LEGAL_PATTERNS.items():
        if pat.search(text):
            found.append(ptype)
    return found


def classify_domains(text: str) -> list:
    """
    Return list of (domain, hit_count) pairs sorted by hit count descending.
    Only domains with at least one hit are returned.
    """
    text_lower = text.lower()
    hits = []
    for domain, pat in _DOMAIN_PATTERNS.items():
        count = len(pat.findall(text_lower))
        if count > 0:
            hits.append((domain, count))
    hits.sort(key=lambda x: -x[1])
    return hits


def extract_ruling_summary(text: str, legal_types: list) -> str:
    """
    Build a short summary of what the verse prescribes.
    Takes the first sentence or clause that contains a legal keyword.
    """
    # Split into clauses
    clauses = re.split(r"[.;]", text)
    for clause in clauses:
        for ptype, pat in LEGAL_PATTERNS.items():
            if pat.search(clause):
                summary = clause.strip()
                # Truncate to 200 chars
                if len(summary) > 200:
                    summary = summary[:197] + "..."
                return summary
    # Fallback: first 200 chars
    return text[:200].strip()


# ══════════════════════════════════════════════════════════════════════════════
# Modification detection
# ══════════════════════════════════════════════════════════════════════════════

def detect_modifications(timeline: list) -> list:
    """
    Given a list of legal entries in a single domain (ordered by surah),
    find pairs where a later verse may modify an earlier one.

    Heuristic: two verses in the same domain are a potential modification if
    they share at least one domain keyword but have different legal types
    (e.g., one is a permission and another is a prohibition), or if a later
    verse contains qualifying language ("except", "unless", "but if",
    "however", "this supersedes").
    """
    modifications = []
    qualifying_pat = re.compile(
        r"\b(?:except|unless|but if|however|henceforth|instead|"
        r"no longer|from now|abrogat|supersed|replac|modif)\b",
        re.IGNORECASE,
    )

    for i in range(len(timeline)):
        for j in range(i + 1, len(timeline)):
            earlier = timeline[i]
            later = timeline[j]

            # Same domain guaranteed by caller; check for modification signals
            is_modification = False
            reason = []

            # Signal 1: different legal types (permission vs prohibition, etc.)
            types_e = set(earlier["legal_types"])
            types_l = set(later["legal_types"])
            if types_e and types_l and types_e != types_l:
                if (("prohibition" in types_e and "permission" in types_l) or
                        ("permission" in types_e and "prohibition" in types_l)):
                    is_modification = True
                    reason.append("opposite_ruling")
                elif types_e != types_l:
                    is_modification = True
                    reason.append("different_legal_type")

            # Signal 2: qualifying language in the later verse
            if qualifying_pat.search(later["text"]):
                is_modification = True
                reason.append("qualifying_language")

            # Signal 3: shared distinctive words (beyond domain keywords)
            words_e = set(earlier["text"].lower().split())
            words_l = set(later["text"].lower().split())
            # Remove very common words
            stopwords = {"the", "a", "an", "of", "and", "or", "in", "to",
                         "is", "are", "was", "were", "be", "you", "we",
                         "he", "it", "they", "for", "not", "with", "this",
                         "that", "shall", "who", "have", "has", "from",
                         "but", "if", "on", "at", "by", "as", "god", "your"}
            shared = (words_e & words_l) - stopwords
            # Require at least 3 shared content words for topic overlap
            if len(shared) >= 3 and is_modification:
                reason.append(f"shared_terms({len(shared)})")

            if is_modification:
                modifications.append({
                    "earlier_verse": earlier["verse_id"],
                    "later_verse": later["verse_id"],
                    "earlier_surah": earlier["surah"],
                    "later_surah": later["surah"],
                    "reasons": reason,
                    "earlier_summary": earlier["summary"],
                    "later_summary": later["summary"],
                })

    return modifications


# ══════════════════════════════════════════════════════════════════════════════
# Main pipeline
# ══════════════════════════════════════════════════════════════════════════════

def load_verses() -> list:
    """Load verses from data/verses.json."""
    path = os.path.join(DATA_DIR, "verses.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run():
    """Run full legal verse extraction and timeline analysis."""
    print("Loading verses...")
    all_verses = load_verses()
    print(f"  {len(all_verses)} verses loaded")

    # ── Step 1: Detect legal verses ──────────────────────────────────────
    print("\nDetecting legal verses...")
    legal_verses = []
    for v in all_verses:
        legal_types = detect_legal_type(v["text"])
        if not legal_types:
            continue

        domains = classify_domains(v["text"])
        summary = extract_ruling_summary(v["text"], legal_types)

        entry = {
            "verse_id": v["verse_id"],
            "surah": v["surah"],
            "verse": v["verse"],
            "surah_name": v.get("surah_name", f"Surah {v['surah']}"),
            "text": v["text"],
            "legal_types": legal_types,
            "domains": [d for d, _ in domains],
            "domain_scores": {d: c for d, c in domains},
            "primary_domain": domains[0][0] if domains else "general",
            "summary": summary,
        }
        legal_verses.append(entry)

    print(f"  {len(legal_verses)} legal verses detected out of {len(all_verses)}")

    # ── Step 2: Build domain timelines ───────────────────────────────────
    print("\nBuilding domain timelines...")
    domain_timelines = defaultdict(list)
    for entry in legal_verses:
        for domain in entry["domains"]:
            domain_timelines[domain].append(entry)

    # Sort each timeline by surah number then verse number
    for domain in domain_timelines:
        domain_timelines[domain].sort(key=lambda e: (e["surah"], e["verse"]))

    for domain in sorted(domain_timelines.keys()):
        print(f"  {domain:12s}: {len(domain_timelines[domain]):4d} verses")

    # ── Step 3: Detect modifications ─────────────────────────────────────
    print("\nDetecting potential modifications across surahs...")
    domain_modifications = {}
    total_mods = 0
    for domain, timeline in domain_timelines.items():
        mods = detect_modifications(timeline)
        domain_modifications[domain] = mods
        total_mods += len(mods)
        if mods:
            print(f"  {domain:12s}: {len(mods):3d} potential modifications")

    print(f"  Total potential modifications: {total_mods}")

    # ── Step 4: Legal type distribution ──────────────────────────────────
    print(f"\n{'='*60}")
    print("  LEGAL VERSE SUMMARY")
    print(f"{'='*60}")

    type_counts = defaultdict(int)
    for entry in legal_verses:
        for lt in entry["legal_types"]:
            type_counts[lt] += 1
    print("\n  Legal types:")
    for lt, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"    {lt:15s}: {count:4d}")

    domain_counts = defaultdict(int)
    for entry in legal_verses:
        domain_counts[entry["primary_domain"]] += 1
    print("\n  Primary domains:")
    for d, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
        print(f"    {d:15s}: {count:4d}")

    # Top surahs with most legal verses
    surah_counts = defaultdict(int)
    surah_names_map = {}
    for entry in legal_verses:
        surah_counts[entry["surah"]] += 1
        surah_names_map[entry["surah"]] = entry["surah_name"]
    print("\n  Top 10 surahs with most legal verses:")
    for s, count in sorted(surah_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"    Surah {s:3d} ({surah_names_map[s]:25s}): {count:3d} legal verses")

    # ── Step 5: Assemble and save ────────────────────────────────────────
    output = {
        "summary": {
            "total_legal_verses": len(legal_verses),
            "total_verses": len(all_verses),
            "legal_percentage": round(len(legal_verses) / max(len(all_verses), 1) * 100, 2),
            "type_counts": dict(type_counts),
            "domain_counts": dict(domain_counts),
        },
        "legal_verses": [
            {
                "verse_id": e["verse_id"],
                "surah": e["surah"],
                "verse": e["verse"],
                "surah_name": e["surah_name"],
                "text": e["text"],
                "legal_types": e["legal_types"],
                "domains": e["domains"],
                "primary_domain": e["primary_domain"],
                "summary": e["summary"],
            }
            for e in legal_verses
        ],
        "domain_timelines": {
            domain: [
                {
                    "verse_id": e["verse_id"],
                    "surah": e["surah"],
                    "verse": e["verse"],
                    "surah_name": e["surah_name"],
                    "legal_types": e["legal_types"],
                    "summary": e["summary"],
                }
                for e in timeline
            ]
            for domain, timeline in sorted(domain_timelines.items())
        },
        "modifications": {
            domain: mods
            for domain, mods in sorted(domain_modifications.items())
            if mods
        },
    }

    output_path = os.path.join(OUTPUT_DIR, "legal_rulings.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    run()

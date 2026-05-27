"""Export the per-entry audit results as a markdown table."""

import json
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

data = json.load(
    open("data/research/doctrinal_audit/audit_scan_2026-05-22.json", encoding="utf-8")
)


def short_question(q, n=70):
    q = q.strip()
    if len(q) <= n:
        return q
    return q[: n - 1] + "…"


def flag_summary(s):
    """One-line rationale for tier."""
    tier = s["tier"]
    if tier == "DRIFTED":
        return s["rationale"]
    if tier == "PARTIAL":
        return s["rationale"]
    # ALIGNED — pick the most informative marker
    flags = s["hard_flags"]
    if flags:
        # Some are negated — flag for review
        return f"{s['aligned_count']} markers; quoted-context flag: {','.join(set(f[0] for f in flags))}"
    return f"{s['aligned_count']} markers"


# Group by source
by_source = {}
for s in data:
    by_source.setdefault(s["source_file"], []).append(s)

print("# Per-Entry Doctrinal Audit — 2026-05-22\n")
print(
    "Score: **ALIGNED** | **PARTIAL** | **DRIFTED** per the catalog in `submitter_distinctive_catalog_2026-05-22.md`.\n"
)

# Aggregate
total_tier = Counter(s["tier"] for s in data)
print(f"**Total audited:** {len(data)} entries")
print(
    f"**Distribution:** ALIGNED = {total_tier['ALIGNED']} | PARTIAL = {total_tier['PARTIAL']} | DRIFTED = {total_tier['DRIFTED']}\n"
)
print("By source:\n")
for src in sorted(by_source):
    sub = by_source[src]
    c = Counter(s["tier"] for s in sub)
    print(
        f"- **{src}** — {len(sub)} entries: ALIGNED = {c['ALIGNED']}, PARTIAL = {c['PARTIAL']}, DRIFTED = {c['DRIFTED']}"
    )
print()

# Hard-flag summary
print("\n## Hard-flag raw matches (all reviewed)\n")
print("| flag | raw | contextually-negated | effective |")
print("|---|---|---|---|")
flag_raw = Counter()
flag_neg = Counter()
for s in data:
    for f in s["hard_flags"]:
        flag_raw[f[0]] += 1
        if f[3]:
            flag_neg[f[0]] += 1
for name, n in flag_raw.most_common():
    neg = flag_neg.get(name, 0)
    print(f"| `{name}` | {n} | {neg} | {n - neg} |")
print()

# PARTIAL + DRIFTED detail tables
print("\n## PARTIAL / DRIFTED entries (manual review required)\n")
print("| ID | Source | Bucket/Cat | Q | Aligned-markers | Rationale |")
print("|---|---|---|---|---|---|")
for s in data:
    if s["tier"] in ("PARTIAL", "DRIFTED"):
        cat = s.get("category", "") or s["bucket"]
        print(
            f"| `{s['id']}` | {s['source_file'].replace('.jsonl', '')} | {cat} | {short_question(s['question'])} | {s['aligned_count']} | {s['rationale']} |"
        )

print(
    "\n## Entries with raw hard-flag matches (all reclassified to ALIGNED — see note)\n"
)
print("| ID | Source | Flag | Negated? | Quoted-context evidence |")
print("|---|---|---|---|---|")
for s in data:
    for f in s["hard_flags"]:
        cat = s.get("category", "") or s["bucket"]
        evidence = f[2][:80].replace("|", "\\|") + "…"
        print(
            f"| `{s['id']}` | {s['source_file'].replace('.jsonl', '')} | `{f[0]}` | {'YES' if f[3] else 'NO'} | …{evidence} |"
        )

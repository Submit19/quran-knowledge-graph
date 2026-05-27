"""Drift-pattern analysis — by category, time window, topic concentration."""

import json
import os
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8")

JSONL_PATHS = [
    "C:/Users/alika/AppData/Local/Temp/expansion.jsonl",
    "C:/Users/alika/AppData/Local/Temp/worst30.jsonl",
    "C:/Users/alika/AppData/Local/Temp/baseline_plus_5.jsonl",
]

audit = json.load(
    open("data/research/doctrinal_audit/audit_scan_2026-05-22.json", encoding="utf-8")
)
audit_by_id = {s["id"]: s for s in audit}

# Load all raw records, merge audit fields
records = []
for fp in JSONL_PATHS:
    if not os.path.exists(fp):
        print(f"MISSING: {fp}", file=sys.stderr)
        continue
    src = os.path.basename(fp)
    with open(fp, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            r["_source"] = src
            r["_audit"] = audit_by_id.get(r["id"], {})
            records.append(r)

print(f"Loaded {len(records)} records from {len(JSONL_PATHS)} sources.\n")

# Citation analysis — aggregate all citations
all_cites = Counter()
for r in records:
    for c in r.get("citations", []) or []:
        if isinstance(c, str):
            v = c.strip("[]")
            all_cites[v] += 1

print(f"Total distinct verses cited: {len(all_cites)}")
print(f"Total citation occurrences: {sum(all_cites.values())}\n")

print("Top 25 most-cited verses:")
for v, n in all_cites.most_common(25):
    print(f"  {n:4d} {v}")

print()
print("9:128 / 9:129 (Khalifa-excluded — should be ZERO):")
print(f"  9:128 in citations[]: {all_cites.get('9:128', 0)}")
print(f"  9:129 in citations[]: {all_cites.get('9:129', 0)}")

# By category × tier
print("\n\n=== Tier by category (expansion only) ===")
by_cat = defaultdict(lambda: Counter())
for r in records:
    if r["_source"] == "expansion.jsonl":
        cat = r.get("category", "")
        tier = r["_audit"].get("tier", "?")
        by_cat[cat][tier] += 1
for cat, c in sorted(by_cat.items()):
    total = sum(c.values())
    partial = c.get("PARTIAL", 0)
    pct = 100 * partial / total if total else 0
    print(
        f"  {cat:18s} | total={total:4d} | aligned={c.get('ALIGNED', 0):3d} | partial={partial:3d} | partial%={pct:.1f}%"
    )

# By time window
print("\n=== Tier by time window (hour-bucketed) ===")
by_time = defaultdict(lambda: Counter())
for r in records:
    if r["_source"] in ("expansion.jsonl", "worst30.jsonl"):
        t = r.get("answered_at", "")[:13]
        tier = r["_audit"].get("tier", "?")
        by_time[t][tier] += 1
for t, c in sorted(by_time.items()):
    total = sum(c.values())
    partial = c.get("PARTIAL", 0)
    pct = 100 * partial / total if total else 0
    print(
        f"  {t} | total={total:4d} | aligned={c.get('ALIGNED', 0):3d} | partial={partial:3d} | partial%={pct:.1f}%"
    )

# Drift correlation — do PARTIAL entries cluster in time?
print("\n=== PARTIAL entry detail (when did each one get written) ===")
for r in records:
    if r["_audit"].get("tier") == "PARTIAL":
        print(
            f"  {r['_source']:25s} | {r['id']:18s} | {r.get('answered_at', '')[:16]} | cat={r.get('category', '')}"
        )

# Aligned-marker density
print("\n=== Marker density distribution ===")
density = Counter()
for s in audit:
    density[s["aligned_count"]] += 1
for cnt in sorted(density):
    bar = "█" * min(50, density[cnt] // 2)
    print(f"  {cnt:3d} markers: {density[cnt]:4d}  {bar}")

# Top markers
print("\n=== Most-used aligned markers ===")
m = Counter()
for s in audit:
    for marker in s["aligned_markers"]:
        m[marker] += 1
for name, n in m.most_common(25):
    print(f"  {n:4d} {name}")

# Drift-flag detail
print("\n=== Risk-topic engagement frequency ===")
risk_count = Counter()
for s in audit:
    for r in s.get("risk_topics", []):
        risk_count[r] += 1
for r, n in risk_count.most_common():
    print(f"  {n:4d} {r}")

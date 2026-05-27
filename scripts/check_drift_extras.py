"""Spot-check extra drift markers across all three JSONL sources."""

import json
import re
import sys
import os

sys.stdout.reconfigure(encoding="utf-8")

patterns = {
    "hadith_mention": re.compile(r"\bhadith(s|ic)?\b", re.I),
    "sunnah_neutral": re.compile(r"\bsunnah\b", re.I),
    "pbuh": re.compile(
        r"\bpbuh\b|peace and blessings be upon him|may peace be upon|sallallahu|sallahu",
        re.I,
    ),
    "holy_prophet": re.compile(r"\bholy prophet\b", re.I),
    "sahaba": re.compile(r"\bsahaba\b|companions of the prophet", re.I),
    "imam_title": re.compile(r"\bimam ali\b|imam hussain|\bhazrat\b|imam jafar", re.I),
    "caliph_positive": re.compile(
        r"\b(rightly[\s\-]guided|first|second|third|fourth)\s+caliph", re.I
    ),
    "shia_imam_doctrine": re.compile(r"\bimamate\b|infallible imam|twelve imams", re.I),
}

count = {k: [] for k in patterns}
files = [
    "C:/Users/alika/AppData/Local/Temp/expansion.jsonl",  # may not exist
    "/tmp/expansion.jsonl",
    "/tmp/worst30.jsonl",
    "/tmp/baseline_plus_5.jsonl",
]
# Just use the args
for fp in sys.argv[1:]:
    if not os.path.exists(fp):
        continue
    with open(fp, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            for name, rx in patterns.items():
                m = rx.search(r.get("answer", ""))
                if m:
                    a = r.get("answer", "")
                    ctx = a[max(0, m.start() - 50) : m.end() + 50].replace("\n", " ")
                    count[name].append((fp, r["id"], ctx))

for name, hits in count.items():
    print(f"{name}: {len(hits)} hits")
    for fp, rid, ctx in hits[:5]:
        print(f"  - {fp.split(os.sep)[-1]} {rid}: ...{ctx}...")

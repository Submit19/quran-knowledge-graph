"""Register the `sermons` bucket in the root Khalifa-corpus MANIFEST.

The scraped sermons live under data/khalifa_corpus/sermons/ with their own
MANIFEST.json. The ROOT manifest (data/khalifa_corpus/MANIFEST.json) is owned
by the khalifa-corpus-scrape branch and is NOT present on this (off-main)
branch — editing a copy here would create a merge conflict when the branches
are combined. So instead of vendoring + editing that file, this script
registers the bucket idempotently at run time, AFTER the branches are merged.

Run it once the root manifest exists:
    python scripts/register_sermons_bucket.py

It is schema-flexible (the root manifest's exact shape is owned elsewhere):
  - if the manifest has a dict under "buckets", it sets buckets["sermons"];
  - if "buckets" is a list, it upserts an entry with name == "sermons";
  - otherwise it adds/updates a top-level "sermons" key.
Re-running is a no-op beyond refreshing the rolled-up stats.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROOT_MANIFEST = ROOT / "data" / "khalifa_corpus" / "MANIFEST.json"
SERMONS_MANIFEST = ROOT / "data" / "khalifa_corpus" / "sermons" / "MANIFEST.json"


def build_bucket_entry() -> dict:
    sm = json.loads(SERMONS_MANIFEST.read_text(encoding="utf-8"))
    return {
        "name": "sermons",
        "path": "sermons/",
        "manifest": "sermons/MANIFEST.json",
        "description": sm.get("description", ""),
        "source_channel": sm.get("source_channel", "@asubmitter2god"),
        "stats": sm.get("stats", {}),
    }


def main() -> int:
    if not SERMONS_MANIFEST.exists():
        print(
            f"ERROR: {SERMONS_MANIFEST} missing — run build_sermons_manifest.py first"
        )
        return 1
    if not ROOT_MANIFEST.exists():
        print(
            f"ERROR: {ROOT_MANIFEST} missing — merge the khalifa-corpus-scrape "
            f"branch first, then re-run this script"
        )
        return 1

    entry = build_bucket_entry()
    manifest = json.loads(ROOT_MANIFEST.read_text(encoding="utf-8"))

    buckets = manifest.get("buckets")
    if isinstance(buckets, dict):
        buckets["sermons"] = entry
    elif isinstance(buckets, list):
        buckets[:] = [b for b in buckets if (b or {}).get("name") != "sermons"]
        buckets.append(entry)
    else:
        manifest["sermons"] = entry

    ROOT_MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"registered sermons bucket in {ROOT_MANIFEST} "
        f"({entry['stats'].get('videos_kept', '?')} videos, "
        f"{entry['stats'].get('total_rashad_words', '?')} words)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

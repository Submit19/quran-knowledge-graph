"""Extract question text only from eval v2 YAMLs.

Writes data/eval/v2/_questions_only.json with only id/bucket/question per
entry — asserts, rubric weights, and notes are intentionally stripped so
the advisor session can answer strict-blind without contaminating itself
by reading the ground-truth before the answer is composed.

Source resolution: prefers files on disk under data/eval/v2/<bucket>.yaml;
falls back to `git show origin/phase-4b-eval-questions:data/eval/v2/<bucket>.yaml`
when the parked branch hasn't been merged to main yet.
"""

import json
import subprocess
import sys
from pathlib import Path

import yaml

BUCKETS = ["abstract", "broad", "concrete", "structured"]
HOLDOUT = "_holdout"
EVAL_DIR = Path(__file__).resolve().parent.parent / "data" / "eval" / "v2"
PARKED_REF = "origin/phase-4b-eval-questions"


def _load(bucket: str) -> list[dict]:
    on_disk = EVAL_DIR / f"{bucket}.yaml"
    if on_disk.exists():
        with on_disk.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or []
    proc = subprocess.run(
        ["git", "show", f"{PARKED_REF}:data/eval/v2/{bucket}.yaml"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        raise SystemExit(
            f"could not load {bucket}.yaml from disk or {PARKED_REF}: {proc.stderr}"
        )
    return yaml.safe_load(proc.stdout) or []


def main() -> None:
    include_holdout = "--with-holdout" in sys.argv
    main_set = []
    for bucket in BUCKETS:
        for q in _load(bucket):
            main_set.append(
                {"id": q["id"], "bucket": q["bucket"], "question": q["question"]}
            )

    if include_holdout:
        for q in _load(HOLDOUT):
            q["heldout"] = True
            main_set.append(
                {
                    "id": q["id"],
                    "bucket": q["bucket"],
                    "question": q["question"],
                    "heldout": True,
                }
            )

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    out_path = EVAL_DIR / "_questions_only.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(main_set, f, indent=2, ensure_ascii=False)

    by_bucket: dict[str, int] = {}
    for q in main_set:
        by_bucket[q["bucket"]] = by_bucket.get(q["bucket"], 0) + 1
    print(f"wrote {len(main_set)} questions to {out_path}")
    for b, n in sorted(by_bucket.items()):
        print(f"  {b}: {n}")


if __name__ == "__main__":
    main()

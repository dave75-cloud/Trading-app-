#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RND = ROOT / "rnd"
TASK_RE = re.compile(r"^RND-[0-9]{4}$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

def git_head():
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()

def main():
    ap = argparse.ArgumentParser(description="Create an offline R&D experiment skeleton.")
    ap.add_argument("task_id")
    ap.add_argument("slug")
    ap.add_argument("title")
    a = ap.parse_args()

    if not TASK_RE.fullmatch(a.task_id):
        ap.error("task_id must look like RND-0001")
    if not SLUG_RE.fullmatch(a.slug):
        ap.error("slug must use lowercase letters, digits and hyphens")

    dt = datetime.now(timezone.utc).replace(microsecond=0)
    iso = dt.isoformat().replace("+00:00", "Z")
    exp_id = f"EXP-{dt.strftime('%Y%m%dT%H%M%SZ')}-{a.slug}"
    exp_dir = RND / "experiments" / exp_id

    if exp_dir.exists():
        raise SystemExit(f"experiment already exists: {exp_dir}")

    exp_dir.mkdir(parents=True)
    manifest = {
        "experiment_id": exp_id,
        "task_id": a.task_id,
        "title": a.title,
        "status": "planned",
        "created_utc": iso,
        "git_base": git_head(),
        "hypothesis": "",
        "inputs": [],
        "commands": [],
        "outputs": [],
        "result": "",
        "safety": {
            "broker_writes": False,
            "protected_paths_modified": False,
            "strategy_authority_changed": False,
            "human_promotion_required": True,
        },
    }

    (exp_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (exp_dir / "notes.md").write_text(
        f"# {a.title}\n\n"
        f"Experiment: `{exp_id}`\n\n"
        "## Question\n\nDescribe the research question.\n\n"
        "## Method\n\nRecord the reproducible method.\n\n"
        "## Observations\n\nRecord observations without promotion claims.\n"
    )

    event = {
        "experiment_id": exp_id,
        "timestamp_utc": iso,
        "status": "planned",
        "task_id": a.task_id,
        "title": a.title,
    }
    registry = RND / "registry" / "experiment_events.jsonl"
    with registry.open("a") as fh:
        fh.write(json.dumps(event, sort_keys=True) + "\n")

    print(f"created={exp_dir.relative_to(ROOT)}")
    print(f"git_base={manifest['git_base']}")
    print("broker_writes=FALSE")
    print("promotion_authority=HUMAN_ONLY")

if __name__ == "__main__":
    main()

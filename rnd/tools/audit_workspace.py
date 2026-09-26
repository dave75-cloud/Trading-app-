#!/usr/bin/env python3
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RND = ROOT / "rnd"
TASK_RE = re.compile(r"^RND-[0-9]{4}$")
EXP_RE = re.compile(r"^EXP-[0-9]{8}T[0-9]{6}Z-[a-z0-9][a-z0-9-]*$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
UTC_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
TASK_STATES = {"queued", "running", "blocked", "complete", "cancelled"}
EXP_STATES = {"planned", "running", "complete", "rejected", "archived"}
errors = []

def fail(msg):
    errors.append(msg)

def read_jsonl(path):
    rows = []
    if not path.is_file():
        fail(f"missing: {path.relative_to(ROOT)}")
        return rows
    for n, raw in enumerate(path.read_text().splitlines(), 1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except Exception as exc:
            fail(f"{path.relative_to(ROOT)}:{n}: {exc}")
            continue
        if not isinstance(row, dict):
            fail(f"{path.relative_to(ROOT)}:{n}: event must be an object")
            continue
        rows.append(row)
    return rows

for rel in [
    "rnd/README.md",
    "rnd/FRAMEWORK.md",
    "rnd/queue/task_events.jsonl",
    "rnd/registry/experiment_events.jsonl",
    "rnd/tools/new_experiment.py",
    "rnd/tools/audit_workspace.py",
]:
    if not (ROOT / rel).exists():
        fail(f"missing: {rel}")

tasks = {}
for row in read_jsonl(RND / "queue" / "task_events.jsonl"):
    tid = row.get("task_id")
    if not isinstance(tid, str) or not TASK_RE.fullmatch(tid):
        fail(f"invalid task_id: {tid!r}")
        continue
    if row.get("status") not in TASK_STATES:
        fail(f"{tid}: invalid task status")
    ts = row.get("timestamp_utc")
    if not isinstance(ts, str) or not UTC_RE.fullmatch(ts):
        fail(f"{tid}: invalid timestamp")
    if row.get("protected_paths_allowed") is not False:
        fail(f"{tid}: protected_paths_allowed must be false")
    if not isinstance(row.get("human_gate_required"), bool):
        fail(f"{tid}: human_gate_required must be boolean")
    tasks[tid] = row.get("status")

registry_ids = set()
for row in read_jsonl(RND / "registry" / "experiment_events.jsonl"):
    eid = row.get("experiment_id")
    if not isinstance(eid, str) or not EXP_RE.fullmatch(eid):
        fail(f"invalid registry experiment_id: {eid!r}")
        continue
    registry_ids.add(eid)
    if row.get("status") not in EXP_STATES:
        fail(f"{eid}: invalid registry status")

manifest_ids = set()
exp_root = RND / "experiments"
if exp_root.exists():
    for exp_dir in sorted(p for p in exp_root.iterdir() if p.is_dir()):
        mf = exp_dir / "manifest.json"
        if not mf.is_file():
            fail(f"{exp_dir.relative_to(ROOT)}: missing manifest.json")
            continue
        if not (exp_dir / "notes.md").is_file():
            fail(f"{exp_dir.relative_to(ROOT)}: missing notes.md")
        try:
            m = json.loads(mf.read_text())
        except Exception as exc:
            fail(f"{mf.relative_to(ROOT)}: {exc}")
            continue

        eid = m.get("experiment_id")
        if eid != exp_dir.name or not isinstance(eid, str) or not EXP_RE.fullmatch(eid):
            fail(f"{mf.relative_to(ROOT)}: experiment_id mismatch/invalid")
            continue
        manifest_ids.add(eid)

        if m.get("task_id") not in tasks:
            fail(f"{eid}: unknown task")
        if m.get("status") not in EXP_STATES:
            fail(f"{eid}: invalid status")
        if not isinstance(m.get("git_base"), str) or not SHA_RE.fullmatch(m["git_base"]):
            fail(f"{eid}: invalid git_base")
        for key in ("inputs", "commands", "outputs"):
            if not isinstance(m.get(key), list) or not all(isinstance(x, str) for x in m[key]):
                fail(f"{eid}: {key} must be list[str]")

        expected = {
            "broker_writes": False,
            "protected_paths_modified": False,
            "strategy_authority_changed": False,
            "human_promotion_required": True,
        }
        if m.get("safety") != expected:
            fail(f"{eid}: safety declaration is not fail-closed")

for eid in manifest_ids - registry_ids:
    fail(f"{eid}: manifest exists without registry event")
for eid in registry_ids - manifest_ids:
    fail(f"{eid}: registry event exists without manifest")

# Derive protected-path safety from Git state.
status = subprocess.run(
    ["git", "status", "--porcelain=v1", "--untracked-files=all"],
    cwd=ROOT,
    check=True,
    text=True,
    stdout=subprocess.PIPE,
).stdout.splitlines()

changed_paths = []

for raw in status:
    if not raw.strip():
        continue

    path_text = raw[3:]

    if " -> " in path_text:
        path_text = path_text.split(" -> ", 1)[1]

    changed_paths.append(path_text)

outside_rnd = [
    path
    for path in changed_paths
    if not (
        path == "rnd"
        or path.startswith("rnd/")
    )
]

for path in outside_rnd:
    fail(f"changed path outside rnd/: {path}")

# Derive broker/order safety by scanning R&D text.
PROHIBITED_PARTS = [
    "order_" + "send",
    "place_" + "order" + r"\s*\(",
    "api-fx" + "trade" + r"\.oanda\.com",
    "api-fx" + "practice" + r"\.oanda\.com",
    "OANDA_API_" + "TOKEN",
    "OANDA_ACCOUNT_" + "ID",
]

PROHIBITED = re.compile(
    "|".join(PROHIBITED_PARTS),
    re.IGNORECASE,
)

broker_hits = []

for path in sorted(RND.rglob("*")):
    if not path.is_file():
        continue

    # This audit file contains the prohibited patterns themselves.
    if path.resolve() == Path(__file__).resolve():
        continue

    try:
        body = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue

    for n, line in enumerate(body.splitlines(), 1):
        if PROHIBITED.search(line):
            broker_hits.append(
                f"{path.relative_to(ROOT)}:{n}"
            )

for hit in broker_hits:
    fail(f"prohibited broker/order token: {hit}")

if errors:
    print("RND_WORKSPACE_AUDIT: FAIL")
    for item in errors:
        print(f"- {item}")
    raise SystemExit(1)

print("RND_WORKSPACE_AUDIT: PASS")
print(f"tasks={len(tasks)}")
print(f"experiments={len(manifest_ids)}")
print("broker_writes=FALSE (derived_scan)")
print("protected_paths_modified=FALSE (derived_git_status)")
print("promotion_authority=HUMAN_ONLY")

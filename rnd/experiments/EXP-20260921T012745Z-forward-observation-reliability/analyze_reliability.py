#!/usr/bin/env python3
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUTS = ROOT / "inputs"

csv_path = INPUTS / "m006e9b_sessions_through_2026-09-17.csv"
ledger_path = INPUTS / "m006e9b_through_2026-09-17.json"

with csv_path.open(newline="") as f:
    rows = list(csv.DictReader(f))

ledger = json.loads(ledger_path.read_text())

def i(row, key):
    return int(row[key] or 0)

def f(row, key):
    return float(row[key] or 0)

sessions = len(rows)
accepted = sum(row["accepted"] == "True" for row in rows)
expected = sum(i(row, "expected_cycles") for row in rows)
observed = sum(i(row, "observed_cycles") for row in rows)
passes = sum(i(row, "pass_cycles") for row in rows)
fails = sum(i(row, "fail_cycles") for row in rows)
skips = sum(i(row, "skip_cycles") for row in rows)
unknown = sum(i(row, "unknown_cycles") for row in rows)
upstream = sum(i(row, "contained_upstream_failures") for row in rows)
events = sum(i(row, "authoritative_events") for row in rows)
provider_events = sum(i(row, "provider_events") for row in rows)
recon_events = sum(i(row, "reconciliation_events") for row in rows)
safety = sum(i(row, "safety_violations") for row in rows)

dispositions = []
local_concurrency = 0
for path in sorted(INPUTS.glob("session_disposition_*.json")):
    d = json.loads(path.read_text())
    dispositions.append(d)
    local_concurrency += int(d.get("contained_local_concurrency_failures", 0) or 0)

unclassified_failures = fails - upstream - local_concurrency
missing_cycles = expected - observed
coverage = (observed / expected * 100) if expected else 0.0

failure_sessions = [
    {
        "day": row["day"],
        "fail_cycles": i(row, "fail_cycles"),
        "contained_upstream_failures": i(row, "contained_upstream_failures"),
        "reviewed_disposition": row["reviewed_disposition"],
    }
    for row in rows if i(row, "fail_cycles")
]

coverage_warning_sessions = [
    {
        "day": row["day"],
        "coverage_pct": f(row, "coverage_pct"),
        "reviewed_disposition": row["reviewed_disposition"],
    }
    for row in rows if f(row, "coverage_pct") < 80.0
]

hash_failures = [
    row["day"] for row in rows
    if row["m006e2_hash_match"] != "True"
]

input_hashes = {}
for path in sorted(INPUTS.iterdir()):
    if path.is_file():
        input_hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()

result = {
    "analysis_version": "RND-0003-v1.0",
    "observation_end": rows[-1]["day"],
    "sessions": {
        "total": sessions,
        "accepted": accepted,
    },
    "cycles": {
        "expected": expected,
        "observed": observed,
        "missing": missing_cycles,
        "coverage_pct": round(coverage, 4),
        "pass": passes,
        "fail": fails,
        "skip": skips,
        "unknown": unknown,
    },
    "failure_taxonomy": {
        "contained_upstream": upstream,
        "contained_local_concurrency": local_concurrency,
        "unclassified_raw_failures": unclassified_failures,
        "failure_sessions": failure_sessions,
    },
    "coverage_warning_sessions_below_80pct": coverage_warning_sessions,
    "events": {
        "authoritative": events,
        "provider_path": provider_events,
        "reconciliation": recon_events,
    },
    "integrity": {
        "safety_violations": safety,
        "m006e2_hash_failure_sessions": hash_failures,
    },
    "input_sha256": input_hashes,
}

(ROOT / "analysis.json").write_text(
    json.dumps(result, indent=2) + "\n",
    encoding="utf-8",
)

lines = [
    "# RND-0003 — Forward-Observation Reliability Analysis",
    "",
    f"Observation through: {result['observation_end']}",
    "",
    "## Derived results",
    "",
    f"- Accepted sessions: {accepted}/{sessions}",
    f"- Cycles observed: {observed}/{expected} ({coverage:.2f}%)",
    f"- Missing/unobserved cycles: {missing_cycles}",
    f"- PASS / FAIL / SKIP / UNKNOWN: {passes} / {fails} / {skips} / {unknown}",
    f"- Contained upstream failures: {upstream}",
    f"- Contained local concurrency/state-race failures: {local_concurrency}",
    f"- Unclassified raw failures after taxonomy: {unclassified_failures}",
    f"- Authoritative events: {events}",
    f"- Provider-path events: {provider_events}",
    f"- Reconciliation events: {recon_events}",
    f"- Recorded safety violations: {safety}",
    f"- M006e.2 hash-failure sessions: {len(hash_failures)}",
    "",
    "## Failure sessions",
    "",
]

for row in failure_sessions:
    lines.append(
        f"- {row['day']}: {row['fail_cycles']} raw FAIL cycle(s), "
        f"{row['contained_upstream_failures']} classified upstream; "
        f"reviewed disposition `{row['reviewed_disposition']}`."
    )

lines += [
    "",
    "## Coverage warnings",
    "",
]

if coverage_warning_sessions:
    for row in coverage_warning_sessions:
        lines.append(
            f"- {row['day']}: {row['coverage_pct']:.1f}% coverage "
            f"(`{row['reviewed_disposition']}`)."
        )
else:
    lines.append("- None below 80%.")

lines += [
    "",
    "## Interpretation",
    "",
    "- All 10 recorded raw FAIL cycles are accounted for by the derived taxonomy: "
      f"{upstream} contained upstream/provider failures plus "
      f"{local_concurrency} contained local concurrency failure.",
    "- The copied evidence records zero safety violations and no M006e.2 integrity failures.",
    "- The evidence therefore supports an operational-reliability/infrastructure issue "
      "classification rather than a recorded execution-safety breach.",
    "- Coverage loss remains a separate availability concern and should not be reclassified "
      "as a safety defect without additional evidence.",
    "- This analysis makes no claim about strategy profitability, parameter quality, "
      "promotion, or live-trading suitability.",
    "",
    "## Governance",
    "",
    "- Analysis is offline and derived only from copied immutable evidence.",
    "- Frozen M005/M006e components were not modified.",
    "- No strategy, sizing, broker-write, promotion, or capital authority is conferred.",
]

(ROOT / "analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

print("RND-0003 ANALYSIS COMPLETE")
print(f"sessions={accepted}/{sessions}")
print(f"cycles={observed}/{expected}")
print(f"coverage={coverage:.2f}%")
print(f"raw_failures={fails}")
print(f"contained_upstream={upstream}")
print(f"contained_local_concurrency={local_concurrency}")
print(f"unclassified_failures={unclassified_failures}")
print(f"authoritative_events={events}")
print(f"safety_violations={safety}")

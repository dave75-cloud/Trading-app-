#!/usr/bin/env python3
"""Governed RND-0045 development heterogeneity outcome runner."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORCH = ROOT / "rnd" / "orchestration"
if str(ORCH) not in sys.path:
    sys.path.insert(0, str(ORCH))

from rnd0045_cross_pair_heterogeneity import analyze  # noqa: E402

EXPECTED_SOURCE_SHA256 = "8f30a8a12e13786bc1dc730d1468197e3b246c8141be4cee410bf3178547fc7b"
EXPECTED_CLASSIFICATIONS = {
    "COMMON_MECHANISM_SUPPORTED_FOR_CANDIDATE_REVIEW",
    "COMMON_MECHANISM_SUPPORTED_WITH_MATERIAL_HETEROGENEITY",
    "PAIR_DEPENDENT_MECHANISM",
    "COMMON_MECHANISM_FALSIFIED",
}


class RND0045OutcomeError(ValueError):
    pass


def req(condition, message):
    if not condition:
        raise RND0045OutcomeError(message)


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run(source_report):
    p = Path(source_report).expanduser().resolve()
    req(p.exists(), "RND-0044 source report missing")
    actual_sha = sha256_file(p)
    req(actual_sha == EXPECTED_SOURCE_SHA256, "RND-0044 source report SHA-256 mismatch")
    d = json.loads(p.read_text(encoding="utf-8"))
    req(d.get("task_id") == "RND-0044", "unexpected source task")
    req(d.get("classification") == "RATIO_ONLY_MIXED_OR_NON_MONOTONIC", "unexpected RND-0044 classification")
    arms = d.get("arms")
    req(isinstance(arms, dict) and "Q000" in arms and "Q003" in arms, "Q000/Q003 missing")
    req(d.get("validation_access") is False, "source report indicates validation access")
    req(d.get("reserved_final_open") is False, "source report indicates reserved final open")

    result = analyze(arms["Q000"], arms["Q003"])
    req(result["classification"] in EXPECTED_CLASSIFICATIONS, "unexpected RND-0045 classification")
    result["task_id"] = "RND-0045"
    result["source_report"] = str(p)
    result["source_report_sha256"] = actual_sha
    result["status"] = "COMPLETE_REQUIRES_HUMAN_REVIEW"
    result["authority"]["development_outcomes"] = True
    return result


def write_new(path, value):
    p = Path(path).expanduser().resolve()
    req(not p.exists(), "output report exists; overwrite prohibited")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return p


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-report", required=True)
    ap.add_argument("--report", required=True)
    a = ap.parse_args(argv)
    value = run(a.source_report)
    out = write_new(a.report, value)
    print("RND0045_CROSS_PAIR_HETEROGENEITY: COMPLETE")
    print(f"classification={value['classification']}")
    print(f"positive_full_period_pair_count={value['classification_details']['positive_full_period_pair_count']}")
    print(f"positive_aggregate_year_count={value['classification_details']['positive_aggregate_year_count']}")
    print(f"years_with_at_least_3_positive_pairs={value['classification_details']['years_with_at_least_3_positive_pairs']}")
    print(f"leave_one_pair_out_all_positive={value['classification_details']['leave_one_pair_out_all_positive']}")
    print(f"max_positive_pair_share={value['classification_details']['max_positive_pair_share']}")
    print("pair_dropping=FALSE")
    print("new_ratio_thresholds=FALSE")
    print("validation_access=FALSE")
    print("reserved_final_open=FALSE")
    print(f"report={out}")
    print(f"report_sha256={sha256_file(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

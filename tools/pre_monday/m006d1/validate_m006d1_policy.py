#!/usr/bin/env python3
import json, sys
from pathlib import Path

p = Path(__file__).with_name("m006d1_policy.json")
d = json.loads(p.read_text())
required = [
    ("mode", d.get("mode") == "PRACTICE_ONLY"),
    ("strategy_unchanged", d.get("strategy_changed") is False),
    ("primary_oanda", d["execution_authority"]["primary_feed"] == "OANDA"),
    ("validator_twelve", d["execution_authority"]["secondary_live_validator"] == "Twelve Data"),
    ("polygon_not_veto", d["polygon_policy"]["never_used_as_real_time_execution_veto"] is True),
    ("checkpoint_preserved", d["polygon_policy"]["original_10_session_checkpoint_result_preserved"] == "FAILED_7_OF_10"),
    ("master_default_no", d["write_safety"]["ENABLE_DEMO_EXECUTION_default"] == "NO"),
    ("writes_disabled", d["write_safety"]["order_writes_enabled_by_this_package"] is False),
]
print("KQTRL M006d.1 — POLICY VALIDATION")
print("="*64)
bad = 0
for name, ok in required:
    print(("PASS" if ok else "FAIL"), name)
    bad += 0 if ok else 1
print("POLICY_VALIDATION:", "PASS" if not bad else "FAIL")
return_code = 0 if not bad else 10
raise SystemExit(return_code)

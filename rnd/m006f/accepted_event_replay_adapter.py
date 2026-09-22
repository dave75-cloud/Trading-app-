#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

ALLOWED_PAIRS = {"AUDUSD", "EURUSD", "GBPUSD", "USDJPY"}


class ReplayError(ValueError):
    pass


def load_market(path):
    rows = {}
    if not path.exists():
        return rows

    for n, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        key = (str(row["event_id"]), str(row["leg"]))
        if key in rows:
            raise ReplayError(f"duplicate market evidence at line {n}: {key}")
        rows[key] = row
    return rows


def bridge_action(row, leg):
    matches = [
        x for x in row.get("bridge_actions", [])
        if x.get("leg") == leg
    ]
    if len(matches) > 1:
        raise ReplayError(f"duplicate bridge action: {row['event_id']} {leg}")
    return matches[0] if matches else None


def blocked(row, leg):
    return any(
        x.get("leg") == leg
        for x in row.get("blocked_entries", [])
    )


def side_from_position(value):
    s = str(value).strip().lower()
    if s not in {"long", "short"}:
        raise ReplayError(f"invalid entry side: {value!r}")
    return s


def approved_entry(row, leg):
    a = bridge_action(row, leg)
    if not a:
        return None
    if a.get("decision") != "ALLOW_DRY_RUN_PROPOSAL":
        return None

    units = a.get("approx_units")
    if units is None:
        raise ReplayError(f"{row['event_id']} {leg}: missing approved units")

    units = int(units)
    if units == 0:
        raise ReplayError(f"{row['event_id']} {leg}: zero approved units")

    side = side_from_position(row["new_position"])

    if side == "long" and units < 0:
        raise ReplayError(f"{row['event_id']} {leg}: unit sign mismatch")
    if side == "short" and units > 0:
        raise ReplayError(f"{row['event_id']} {leg}: unit sign mismatch")

    return {
        "event_id": row["event_id"],
        "timestamp_utc": row["bar_ts_utc"],
        "pair": row["pair"],
        "action": "entry",
        "side": side,
        "units": abs(units),
        "leg": leg,
    }


def approved_exit(row, leg):
    a = bridge_action(row, leg)
    if not a:
        return False
    return a.get("decision") == "ALLOW_RISK_REDUCING_EXIT"


def attach_market(primitive, market):
    key = (primitive["event_id"], primitive["leg"])
    m = market.get(key)
    if m is None:
        return None

    bid = float(m["bid"])
    ask = float(m["ask"])
    if bid <= 0 or ask <= 0 or ask < bid:
        raise ReplayError(f"{key}: invalid bid/ask")

    out = dict(primitive)
    out["bid"] = bid
    out["ask"] = ask

    if primitive["action"] == "entry":
        factor = float(m["base_to_aud"])
        if factor <= 0:
            raise ReplayError(f"{key}: invalid base_to_aud")
        out["base_to_aud"] = factor
    else:
        factor = float(m["quote_to_aud"])
        if factor <= 0:
            raise ReplayError(f"{key}: invalid quote_to_aud")
        out["quote_to_aud"] = factor

    out.pop("leg", None)
    return out



def load_dispositions(root):
    out = {}
    for p in sorted(root.glob("session_disposition_*.json")):
        d = json.loads(p.read_text())
        day = str(d.get("day", "")).strip()
        if not day:
            raise ReplayError(f"{p.name}: disposition missing day")
        if day in out:
            raise ReplayError(f"duplicate disposition day: {day}")
        out[day] = d
    return out


def accepted_reconciliation_files(session_root, recon_root, disposition_root):
    dispositions = load_dispositions(disposition_root)
    accepted = []
    days = set()

    for sp in sorted(session_root.glob("m006e9a_*.json")):
        sess = json.loads(sp.read_text())
        day = str(sess.get("day", "")).strip()

        if not day or day in days:
            raise ReplayError(f"{sp.name}: missing or duplicate session day")
        days.add(day)

        n_events = int(sess["events"]["authoritative_events"])

        integ = sess.get("integrity", {})
        safety = sess.get("safety", {})
        bridge = sess.get("bridge", {}).get("totals", {})
        validation = sess.get("validation", {}).get("totals", {})

        if integ.get("m006e2_hash_match") is not True:
            raise ReplayError(f"{day}: M006e.2 integrity gate failed")

        if safety.get("zero_unexplained_write_indicators") is not True:
            raise ReplayError(f"{day}: zero-write safety gate failed")

        if int(bridge.get("order_payloads", -1)) != 0:
            raise ReplayError(f"{day}: bridge payload count is nonzero")
        if int(bridge.get("write_requests", -1)) != 0:
            raise ReplayError(f"{day}: bridge write count is nonzero")

        if int(validation.get("oanda_network_calls", -1)) != 0:
            raise ReplayError(f"{day}: validator network count is nonzero")
        if int(validation.get("order_payloads", -1)) != 0:
            raise ReplayError(f"{day}: validator payload count is nonzero")
        if int(validation.get("write_requests", -1)) != 0:
            raise ReplayError(f"{day}: validator write count is nonzero")

        rmeta = sess.get("reconciliation", {})
        if rmeta.get("available") is not True:
            raise ReplayError(f"{day}: reconciliation unavailable")
        if rmeta.get("mode") != "READ_ONLY_POST_SESSION_RECONCILIATION":
            raise ReplayError(f"{day}: unexpected reconciliation mode")
        if int(rmeta.get("network_calls", -1)) != 0:
            raise ReplayError(f"{day}: reconciliation network count is nonzero")
        if rmeta.get("order_capability") is not False:
            raise ReplayError(f"{day}: reconciliation capability gate failed")

        rname = Path(str(rmeta.get("source_file", ""))).name
        rp = recon_root / rname
        if not rname or not rp.exists():
            raise ReplayError(f"{day}: referenced reconciliation missing")

        recon = json.loads(rp.read_text())

        if str(recon.get("day", "")) != day:
            raise ReplayError(f"{day}: reconciliation day mismatch")

        counts = [
            n_events,
            int(rmeta.get("events", -1)),
            int(rmeta.get("summary", {}).get("events", -1)),
            int(recon.get("summary", {}).get("events", -1)),
            len(recon.get("timeline", [])),
        ]
        if len(set(counts)) != 1:
            raise ReplayError(f"{day}: authoritative event counts disagree: {counts}")

        verdict = str(
            sess.get("orchestration", {}).get("verdict", "")
        ).strip().upper()

        if verdict != "CLEAN":
            disp = dispositions.get(day)
            if disp is None:
                raise ReplayError(f"{day}: non-CLEAN session lacks disposition")

            if disp.get("accepted") is not True:
                raise ReplayError(f"{day}: disposition not accepted")

            if int(disp.get("authoritative_events", -1)) != n_events:
                raise ReplayError(f"{day}: disposition event count mismatch")

            reviewed = str(disp.get("reviewed_disposition", ""))
            if not reviewed.startswith("ACCEPTED"):
                raise ReplayError(f"{day}: disposition not human-accepted")

            di = disp.get("integrity", {})
            if di.get("freeze_manifest_pass") is not True:
                raise ReplayError(f"{day}: disposition freeze gate failed")
            if di.get("m006e2_hash_match") is not True:
                raise ReplayError(f"{day}: disposition hash gate failed")
            if int(di.get("trading_order_writes", -1)) != 0:
                raise ReplayError(f"{day}: disposition write count is nonzero")

        accepted.append(rname)

    present = {x.name for x in recon_root.glob("*.json")}
    if present != set(accepted):
        raise ReplayError(
            "reconciliation snapshot contains files not authorized "
            "by the copied formal session records"
        )

    return accepted

def load_rows(root, accepted_names):
    rows = []
    for p in sorted(root.glob("*.json")):
        if p.name not in set(accepted_names):
            continue
        d = json.loads(p.read_text())
        for row in d.get("timeline", []):
            x = dict(row)
            x["_source"] = p.name
            rows.append(x)

    rows.sort(key=lambda x: (x["bar_ts_utc"], x["pair"]))
    return rows


def adapt(rows, market):
    source_legs = sum(
        2 if str(r.get("event_type", "")).lower() == "reversal" else 1
        for r in rows
    )
    classifications = []
    open_chain = {}
    completed = []
    source_ids = set()
    source_events = 0

    def classify(row, leg, status, detail=None):
        classifications.append({
            "event_id": row["event_id"],
            "timestamp_utc": row["bar_ts_utc"],
            "pair": row["pair"],
            "event_type": row["event_type"],
            "leg": leg,
            "status": status,
            "detail": detail,
        })

    def start_entry(row, leg):
        p = approved_entry(row, leg)
        if p is None:
            classify(row, leg, "UNCLASSIFIED_ENTRY")
            return

        pair = row["pair"]
        if pair in open_chain:
            raise ReplayError(f"{row['event_id']}: approved entry while pair open")

        open_chain[pair] = [p]
        classify(row, leg, "APPROVED_ENTRY")

    def do_exit(row, leg):
        pair = row["pair"]

        if not approved_exit(row, leg):
            classify(row, leg, "UNCLASSIFIED_EXIT")
            return

        if pair not in open_chain:
            classify(row, leg, "EXIT_WITHOUT_APPROVED_ENTRY")
            return

        primitive = {
            "event_id": row["event_id"],
            "timestamp_utc": row["bar_ts_utc"],
            "pair": pair,
            "action": "exit",
            "leg": leg,
        }

        chain = open_chain.pop(pair)
        chain.append(primitive)
        completed.append(chain)
        classify(row, leg, "APPROVED_EXIT")

    for row in rows:
        source_events += 1
        eid = str(row.get("event_id", ""))
        if not eid or eid in source_ids:
            raise ReplayError(f"missing or duplicate event_id: {eid!r}")
        source_ids.add(eid)

        pair = str(row.get("pair", ""))
        if pair not in ALLOWED_PAIRS:
            raise ReplayError(f"{eid}: unsupported pair")

        etype = str(row.get("event_type", "")).lower()

        if etype == "entry":
            if blocked(row, "entry"):
                classify(row, "entry", "BLOCKED_ENTRY")
            else:
                start_entry(row, "entry")

        elif etype == "exit":
            do_exit(row, "exit")

        elif etype == "reversal":
            do_exit(row, "reversal_exit")
            if blocked(row, "reversal_entry"):
                classify(row, "reversal_entry", "BLOCKED_ENTRY")
            else:
                start_entry(row, "reversal_entry")

        else:
            raise ReplayError(f"{eid}: unsupported event type {etype!r}")

    completed.extend(open_chain.values())

    replay = []
    suppressed_chains = 0

    for chain in completed:
        attached = [attach_market(x, market) for x in chain]

        if any(x is None for x in attached):
            suppressed_chains += 1
            missing = [
                f"{x['event_id']}:{x['leg']}"
                for x, y in zip(chain, attached)
                if y is None
            ]
            for x in chain:
                classifications.append({
                    "event_id": x["event_id"],
                    "timestamp_utc": x["timestamp_utc"],
                    "pair": x["pair"],
                    "event_type": x["action"],
                    "leg": x["leg"],
                    "status": "CHAIN_SUPPRESSED_MISSING_MARKET_EVIDENCE",
                    "detail": missing,
                })
            continue

        replay.extend(attached)

    summary = {
        "source_events": source_events,
        "source_legs": source_legs,
        "audit_records": len(classifications),
        "replay_events": len(replay),
        "suppressed_chains": suppressed_chains,
        "automatic_promotion": False,
        "human_review_required": True,
        "network_capability": False,
    }

    return {
        "summary": summary,
        "classifications": classifications,
        "replay_events": replay,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reconciliation-dir", required=True)
    ap.add_argument("--sessions-dir", required=True)
    ap.add_argument("--dispositions-dir", required=True)
    ap.add_argument("--market-evidence", required=True)
    ap.add_argument("--audit-out", required=True)
    ap.add_argument("--replay-out", required=True)
    args = ap.parse_args()

    recon_root = Path(args.reconciliation_dir)

    accepted_names = accepted_reconciliation_files(
        Path(args.sessions_dir),
        recon_root,
        Path(args.dispositions_dir),
    )

    rows = load_rows(recon_root, accepted_names)
    market = load_market(Path(args.market_evidence))
    result = adapt(rows, market)

    result["summary"]["accepted_sessions"] = len(accepted_names)
    result["summary"]["acceptance_gate_pass"] = True

    Path(args.audit_out).write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )

    with Path(args.replay_out).open("w") as f:
        for row in result["replay_events"]:
            f.write(json.dumps(row, sort_keys=True) + "\n")

    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

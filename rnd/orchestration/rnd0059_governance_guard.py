#!/usr/bin/env python3
"""Pure governance/dependency guard for RND-0059."""

REQUIRED_TRACKS = {
    "RND-0055": {"status": "VERIFIED", "broker_writes": False, "capital_authority": False},
    "RND-0056": {"status": "VERIFIED", "broker_writes": False, "capital_authority": False},
    "RND-0057": {"status": "VERIFIED", "broker_writes": False, "capital_authority": False},
    "RND-0058": {"status": "VERIFIED", "broker_writes": False, "capital_authority": False},
}


class GovernanceError(ValueError):
    pass


def _req(cond, message):
    if not cond:
        raise GovernanceError(message)


def validate_integration_manifest(manifest):
    _req(isinstance(manifest, dict), "manifest mapping required")
    _req(manifest.get("automatic_merge") is False, "automatic merge prohibited")
    _req(manifest.get("automatic_promotion") is False, "automatic promotion prohibited")
    _req(manifest.get("broker_writes") is False, "broker writes prohibited")
    _req(manifest.get("capital_authority") is False, "capital authority prohibited")
    _req(manifest.get("reserved_final_access") is False, "reserved-final access prohibited")
    tracks = manifest.get("tracks")
    _req(isinstance(tracks, dict) and set(tracks) == set(REQUIRED_TRACKS), "exact track set required")
    for name, expected in REQUIRED_TRACKS.items():
        item = tracks[name]
        _req(isinstance(item, dict), f"{name}: mapping required")
        _req(item.get("status") == expected["status"], f"{name}: verified status required")
        _req(item.get("broker_writes") is False, f"{name}: broker write escalation")
        _req(item.get("capital_authority") is False, f"{name}: capital authority escalation")
        sha = item.get("verification_commit")
        _req(isinstance(sha, str) and len(sha) == 40 and all(c in "0123456789abcdef" for c in sha), f"{name}: valid verification commit required")
    return {
        "status": "INTEGRATION_READY_FOR_HUMAN_REVIEW",
        "automatic_merge": False,
        "automatic_promotion": False,
        "broker_writes": False,
        "capital_authority": False,
        "reserved_final_access": False,
    }

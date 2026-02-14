"""Generate a latest-signal report and optionally post to Slack.

Designed for scheduled execution (GitHub Actions cron, ECS scheduled task, etc.).

Env:
  API_BASE_URL         If set, fetches from the running API.
  DATA_DIR             (default: ./data/market_candles)
  SYMBOL               (default: GBPUSD)
  HORIZON              (default: 30m)
  SLACK_WEBHOOK_URL    If set, posts a simple message payload.
"""

from __future__ import annotations

import json
import os
from datetime import datetime

import requests


def _fetch_from_api(api_base: str, horizon: str) -> dict:
    r = requests.get(f"{api_base}/signals/latest", params={"h": horizon}, timeout=30)
    r.raise_for_status()
    return r.json()


def _post_to_slack(webhook: str, payload: dict) -> None:
    side = str(payload.get("side", "?")).upper()
    prob = payload.get("prob_up", payload.get("p", None))
    sug = payload.get("suggestion", {}) or {}
    text = f"GBPUSD {payload.get('horizon','?')} → {side}"
    if prob is not None:
        try:
            text += f" | P(up)={float(prob):.3f}"
        except Exception:
            pass
    if sug:
        text += (
            f"\nentry={sug.get('entry_px')} sl={sug.get('sl_px')} tp={sug.get('tp_px')} "
            f"tif={sug.get('tif')} size={sug.get('size')}"
        )

    msg = {
        "text": text,
        "unfurl_links": False,
        "unfurl_media": False,
    }
    r = requests.post(webhook, json=msg, timeout=20)
    r.raise_for_status()


def main() -> int:
    api_base = os.getenv("API_BASE_URL")
    horizon = os.getenv("HORIZON", "30m")
    slack = os.getenv("SLACK_WEBHOOK_URL")

    if not api_base:
        # fallback: direct import path
        from services.inference_api.main import latest  # type: ignore

        payload = latest(h=horizon)
    else:
        payload = _fetch_from_api(api_base, horizon)

    payload = dict(payload)
    payload["generated_at"] = datetime.utcnow().isoformat()
    print(json.dumps(payload, indent=2, sort_keys=True))

    if slack:
        _post_to_slack(slack, payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

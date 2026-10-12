from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Optional

from rnd0066_fred_alfred_macro_provenance_backbone import ConsensusEvidence

PROVIDER = 'TRADING_ECONOMICS'
LINK_KEY = 'US_CPI_HEADLINE'
ECONOMY = 'United States'
CURRENCY = 'USD'
FROZEN_REFERENCE_PERIODS = {'2019-01', '2019-02', '2019-03'}
MAX_LIVE_REQUESTS = 10
PROHIBITED_MARKET_FIELDS = {
    'fx_return','pnl','equity','drawdown','hit_rate','win_rate','pair_rank',
    'directional_response','strategy_signal','strategy_outcome'
}
AUTHORITY_FALSE = {
    'provider_access_authority': False,
    'provider_purchase_authority': False,
    'strategy_outcome_open': False,
    'validation_open': False,
    'reserved_final_open': False,
    'prospective_outcomes_open': False,
    'promotion_authority': False,
    'broker_write_authority': False,
    'capital_authority': False,
    'live_execution_authority': False,
    'automatic_merge': False,
}


class RND0072Error(ValueError):
    pass


@dataclass(frozen=True)
class TEConsensusCandidate:
    calendar_id: str
    country: str
    category: str
    event: str
    reference_period: str
    event_timestamp_utc: str
    date_span: int
    forecast: Any
    te_forecast: Any
    point_in_time_snapshot_utc: str
    raw_hash: str
    source_identity: str


@dataclass
class RequestBudget:
    used: int = 0
    cap: int = MAX_LIVE_REQUESTS

    def consume(self) -> int:
        if self.cap != MAX_LIVE_REQUESTS:
            raise RND0072Error('pilot request cap is frozen at 10')
        if self.used >= self.cap:
            raise RND0072Error('live request cap exhausted before call')
        self.used += 1
        return self.used


def _utc(s: str) -> datetime:
    if not s:
        raise RND0072Error('missing timestamp')
    try:
        d = datetime.fromisoformat(str(s).replace('Z', '+00:00'))
    except ValueError as exc:
        raise RND0072Error('invalid timestamp') from exc
    if d.tzinfo is None:
        raise RND0072Error('timestamp must be timezone-aware')
    return d.astimezone(timezone.utc)


def _parse_numeric(value: Any, label: str) -> float:
    if value is None:
        raise RND0072Error(f'missing {label}')
    s = str(value).strip().replace(',', '')
    if not s:
        raise RND0072Error(f'missing {label}')
    m = re.fullmatch(r'([-+]?\d+(?:\.\d+)?)\s*([KMB%]?)', s, flags=re.I)
    if not m:
        raise RND0072Error(f'unparseable {label}')
    n = float(m.group(1))
    suffix = m.group(2).upper()
    if suffix == 'K':
        n *= 1_000.0
    elif suffix == 'M':
        n *= 1_000_000.0
    elif suffix == 'B':
        n *= 1_000_000_000.0
    return n


def validate_no_market_outcomes(payload: Any) -> None:
    if isinstance(payload, dict):
        lowered = {str(k).lower() for k in payload}
        if lowered.intersection(PROHIBITED_MARKET_FIELDS):
            raise RND0072Error('market outcome contamination prohibited')
        for value in payload.values():
            validate_no_market_outcomes(value)
    elif isinstance(payload, list):
        for value in payload:
            validate_no_market_outcomes(value)


def validate_secret_free(text: str) -> str:
    s = str(text or '')
    lowered = s.lower()
    if 'api_key=' in lowered or '?c=' in lowered or '&c=' in lowered:
        raise RND0072Error('credential-bearing text prohibited')
    return s


def canonical_raw_hash(payload: Any) -> str:
    validate_no_market_outcomes(payload)
    material = repr(payload).encode('utf-8')
    return sha256(material).hexdigest()


def admit_candidate(candidate: TEConsensusCandidate, *, expected_release_utc: str) -> Dict[str, Any]:
    if candidate.country != ECONOMY:
        raise RND0072Error('country mismatch')
    if candidate.reference_period not in FROZEN_REFERENCE_PERIODS:
        raise RND0072Error('reference period outside frozen pilot')
    if int(candidate.date_span) != 0:
        raise RND0072Error('estimated event timing is ineligible')
    category_event = f'{candidate.category} {candidate.event}'.lower()
    if 'consumer price' not in category_event and 'cpi' not in category_event and 'inflation' not in category_event:
        raise RND0072Error('event is not frozen CPI family')
    if not str(candidate.calendar_id).strip():
        raise RND0072Error('missing calendar identity')
    if not str(candidate.raw_hash).strip() or not str(candidate.source_identity).strip():
        raise RND0072Error('missing provenance')
    validate_secret_free(candidate.source_identity)

    event_time = _utc(candidate.event_timestamp_utc)
    expected_time = _utc(expected_release_utc)
    if event_time != expected_time:
        raise RND0072Error('provider event time disagrees with independent BLS timing')
    snapshot_time = _utc(candidate.point_in_time_snapshot_utc)
    if snapshot_time >= event_time:
        raise RND0072Error('point-in-time snapshot must be strictly pre-release')

    forecast_value = _parse_numeric(candidate.forecast, 'Forecast')
    te_forecast_value: Optional[float] = None
    if candidate.te_forecast not in (None, ''):
        te_forecast_value = _parse_numeric(candidate.te_forecast, 'TEForecast')

    evidence = ConsensusEvidence(
        provider=PROVIDER,
        provider_event_id=str(candidate.calendar_id),
        link_key=LINK_KEY,
        economy=ECONOMY,
        currency=CURRENCY,
        reference_period=candidate.reference_period,
        consensus=forecast_value,
        captured_at_utc=snapshot_time.isoformat().replace('+00:00', 'Z'),
        semantic='MARKET_CONSENSUS',
        historical_point_in_time=True,
        raw_hash=candidate.raw_hash,
        source_identity=candidate.source_identity,
    )
    return {
        'consensus_evidence': asdict(evidence),
        'te_forecast_auxiliary': te_forecast_value,
        'te_forecast_admissible_as_consensus': False,
        'timing_verified_against_bls': True,
        'eligibility_state': 'CONSENSUS_INPUT_STRUCTURALLY_ADMISSIBLE',
    }


def reject_teforecast_fallback(candidate: TEConsensusCandidate, *, expected_release_utc: str) -> None:
    if candidate.forecast in (None, '') and candidate.te_forecast not in (None, ''):
        raise RND0072Error('TEForecast may not substitute for missing Forecast')
    admit_candidate(candidate, expected_release_utc=expected_release_utc)


def authority_firewall() -> Dict[str, bool]:
    return dict(AUTHORITY_FALSE)

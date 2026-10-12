from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


class RND0071Error(ValueError):
    pass


@dataclass(frozen=True)
class ProviderEvidence:
    name: str
    point_in_time_documented: bool
    consensus_semantic_documented: bool
    model_forecast_separate: bool
    covers_2015_2020: bool
    historical_capture_proven: bool
    trial_or_low_cost: bool
    purchase_required_now: bool = False


AUTHORITY_FALSE = {
    'provider_purchase_authority': False,
    'trial_activation_authority': False,
    'strategy_outcome_open': False,
    'validation_open': False,
    'reserved_final_open': False,
    'prospective_outcomes_open': False,
    'broker_write_authority': False,
    'capital_authority': False,
    'live_execution_authority': False,
    'automatic_merge': False,
}


def classify_provider(p: ProviderEvidence) -> str:
    name = p.name.strip().upper()
    if not name:
        raise RND0071Error('provider name required')
    if not p.covers_2015_2020:
        return 'REJECT_INSUFFICIENT_HISTORY_FOR_DEVELOPMENT_2015_2020'
    if not p.point_in_time_documented:
        return 'NOT_ADMISSIBLE_WITH_CURRENT_PUBLIC_PROOF'
    if not p.consensus_semantic_documented:
        return 'NOT_ADMISSIBLE_WITH_CURRENT_PUBLIC_PROOF'
    if not p.historical_capture_proven:
        return 'NOT_ADMISSIBLE_WITH_CURRENT_PUBLIC_PROOF'
    if not p.model_forecast_separate:
        return 'NOT_ADMISSIBLE_WITH_CURRENT_PUBLIC_PROOF'
    if p.purchase_required_now:
        raise RND0071Error('RND-0071 cannot authorize provider purchase')
    if p.trial_or_low_cost:
        return 'PREFERRED_BOUNDED_PROVENANCE_PILOT_CANDIDATE'
    return 'ADMISSIBLE_BUT_NOT_COST_PREFERRED'


def provider_catalogue() -> Dict[str, ProviderEvidence]:
    return {
        'FMP': ProviderEvidence(
            name='FMP',
            point_in_time_documented=False,
            consensus_semantic_documented=False,
            model_forecast_separate=False,
            covers_2015_2020=True,
            historical_capture_proven=False,
            trial_or_low_cost=True,
        ),
        'FINNHUB': ProviderEvidence(
            name='Finnhub',
            point_in_time_documented=False,
            consensus_semantic_documented=False,
            model_forecast_separate=False,
            covers_2015_2020=False,
            historical_capture_proven=False,
            trial_or_low_cost=False,
        ),
        'EODHD': ProviderEvidence(
            name='EODHD',
            point_in_time_documented=False,
            consensus_semantic_documented=False,
            model_forecast_separate=False,
            covers_2015_2020=False,
            historical_capture_proven=False,
            trial_or_low_cost=True,
        ),
        'TRADING_ECONOMICS': ProviderEvidence(
            name='Trading Economics',
            point_in_time_documented=True,
            consensus_semantic_documented=True,
            model_forecast_separate=True,
            covers_2015_2020=True,
            historical_capture_proven=True,
            trial_or_low_cost=True,
        ),
    }


def decision_summary() -> Dict[str, object]:
    catalogue = provider_catalogue()
    classifications = {k: classify_provider(v) for k, v in catalogue.items()}
    out: Dict[str, object] = {
        'preferred_provider': 'TRADING_ECONOMICS',
        'preferred_access_path': 'STANDARD_USD49_ONE_WEEK_TRIAL_AFTER_OFFLINE_ADAPTER_VERIFICATION',
        'pilot_request_budget_max': 10,
        'pilot_scope': 'US_CPI_2019Q1_STRUCTURE_ONLY',
        'purchase_before_adapter_verification': False,
        'classifications': classifications,
    }
    out.update(AUTHORITY_FALSE)
    return out


def assert_offline_first(*, adapter_verified: bool, purchase_requested: bool) -> str:
    if purchase_requested and not adapter_verified:
        raise RND0071Error('provider spend prohibited before offline adapter verification')
    if purchase_requested:
        return 'HUMAN_DECISION_REQUIRED_FOR_TRIAL_ACTIVATION'
    return 'NO_PROVIDER_SPEND_AUTHORIZED'

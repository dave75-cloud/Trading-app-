from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any

AUTHORITY_FALSE = {
    'promotion_authority': False,
    'broker_write_authority': False,
    'capital_authority': False,
    'live_execution_authority': False,
    'automatic_merge': False,
}

class RND0062Error(ValueError):
    pass

@dataclass(frozen=True)
class ResearchProposal:
    task_id: str
    hypothesis_family_id: str
    family_trial_index: int
    lifetime_related_trial_count: int
    mechanism_statement: str
    independence_statement: str
    instruments_declared: bool
    timing_declared: bool
    signal_declared: bool
    direction_declared: bool
    lookback_declared: bool
    exit_declared: bool
    filters_declared: bool
    gap_semantics_declared: bool
    cost_model_declared: bool
    uses_midprice_executable_pnl: bool
    portfolio_rule_declared: bool
    missing_data_rule_declared: bool
    primary_metric_declared: bool
    secondary_diagnostics_declared: bool
    minimum_economic_effect_declared: bool
    sample_adequacy_rule_declared: bool
    degrees_of_freedom_declared: bool
    sibling_trials_declared: bool
    development_partition_only: bool
    prohibited_validation_access: bool
    prohibited_reserved_final_access: bool
    prospective_outcome_contamination: bool
    directional_strategy: bool=True

@dataclass(frozen=True)
class DevelopmentResult:
    primary_criterion_pass: bool
    minimum_economic_effect_pass: bool
    integrity_pass: bool
    cost_model_valid: bool
    reproducible: bool
    single_year_dependence: bool
    frozen_regime_exception_for_year: bool
    single_instrument_dependence: bool
    frozen_regime_exception_for_instrument: bool
    leave_one_year_out_all_positive: bool
    leave_one_instrument_out_all_positive: bool
    multi_instrument: bool
    hidden_rescue_or_tuning: bool
    prohibited_partition_access: bool
    undeclared_specification_change: bool


def _base() -> Dict[str, Any]:
    return dict(AUTHORITY_FALSE)


def classify_admission(p: ResearchProposal) -> Dict[str, Any]:
    reasons=[]
    if not p.task_id or not p.hypothesis_family_id: reasons.append('MISSING_IDENTITY')
    if not p.mechanism_statement.strip(): reasons.append('MISSING_MECHANISM')
    if not p.independence_statement.strip(): reasons.append('MISSING_INDEPENDENCE_STATEMENT')
    if p.family_trial_index < 1: reasons.append('INVALID_FAMILY_TRIAL_INDEX')
    if p.lifetime_related_trial_count < p.family_trial_index: reasons.append('HIDDEN_OR_INCONSISTENT_SIBLING_TRIAL_COUNT')
    required=[
        p.instruments_declared,p.timing_declared,p.signal_declared,p.direction_declared,
        p.lookback_declared,p.exit_declared,p.filters_declared,p.gap_semantics_declared,
        p.portfolio_rule_declared,p.missing_data_rule_declared,p.primary_metric_declared,
        p.secondary_diagnostics_declared,p.degrees_of_freedom_declared,p.sibling_trials_declared,
    ]
    if not all(required): reasons.append('UNDECLARED_PARAMETER_OR_DESIGN_FIELD')
    if p.directional_strategy and not p.cost_model_declared: reasons.append('MISSING_COST_MODEL')
    if p.directional_strategy and p.uses_midprice_executable_pnl: reasons.append('MIDPRICE_EXECUTABLE_PNL_PROHIBITED')
    if not p.minimum_economic_effect_declared: reasons.append('MISSING_MINIMUM_ECONOMIC_EFFECT')
    if not p.sample_adequacy_rule_declared: reasons.append('MISSING_SAMPLE_ADEQUACY_RULE')
    if not p.development_partition_only: reasons.append('NONDEVELOPMENT_PARTITION_DECLARED')
    if p.prohibited_validation_access: reasons.append('PROHIBITED_VALIDATION_ACCESS')
    if p.prohibited_reserved_final_access: reasons.append('PROHIBITED_RESERVED_FINAL_ACCESS')
    if p.prospective_outcome_contamination: reasons.append('PROSPECTIVE_OUTCOME_CONTAMINATION')
    out=_base()
    out.update({
        'task_id':p.task_id,
        'hypothesis_family_id':p.hypothesis_family_id,
        'family_trial_index':p.family_trial_index,
        'lifetime_related_trial_count':p.lifetime_related_trial_count,
        'classification':'REJECTED_ADMISSION' if reasons else 'ADMISSIBLE_FOR_DEVELOPMENT_TEST',
        'reasons':tuple(reasons),
        'candidate_freeze':False,
    })
    return out


def classify_advancement(p: ResearchProposal, r: DevelopmentResult) -> Dict[str, Any]:
    admission=classify_admission(p)
    reasons=[]
    if admission['classification']!='ADMISSIBLE_FOR_DEVELOPMENT_TEST':
        reasons.append('PROPOSAL_NOT_ADMITTED')
    if not r.primary_criterion_pass: reasons.append('PRIMARY_CRITERION_FAILED')
    if not r.minimum_economic_effect_pass: reasons.append('MINIMUM_ECONOMIC_EFFECT_FAILED')
    if not r.integrity_pass: reasons.append('INTEGRITY_FAILED')
    if not r.cost_model_valid: reasons.append('COST_MODEL_INVALID')
    if not r.reproducible: reasons.append('NOT_REPRODUCIBLE')
    if r.single_year_dependence and not r.frozen_regime_exception_for_year: reasons.append('SINGLE_YEAR_DEPENDENCE')
    if r.single_instrument_dependence and not r.frozen_regime_exception_for_instrument: reasons.append('SINGLE_INSTRUMENT_DEPENDENCE')
    if not r.leave_one_year_out_all_positive: reasons.append('LEAVE_ONE_YEAR_OUT_FAILED')
    if r.multi_instrument and not r.leave_one_instrument_out_all_positive: reasons.append('LEAVE_ONE_INSTRUMENT_OUT_FAILED')
    if r.hidden_rescue_or_tuning: reasons.append('RESCUE_OR_TUNING_DETECTED')
    if r.prohibited_partition_access: reasons.append('PROHIBITED_PARTITION_ACCESS')
    if r.undeclared_specification_change: reasons.append('UNDECLARED_SPECIFICATION_CHANGE')
    out=_base()
    out.update({
        'task_id':p.task_id,
        'classification':'DEVELOPMENT_FALSIFIED_OR_REJECTED' if reasons else 'ELIGIBLE_FOR_CANDIDATE_REVIEW',
        'reasons':tuple(reasons),
        'candidate_freeze':False,
        'candidate_review_human_only':True,
    })
    return out

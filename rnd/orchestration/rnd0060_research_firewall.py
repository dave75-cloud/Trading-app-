#!/usr/bin/env python3
"""Research firewall preventing contamination of Q003 and sealed/consumed evidence."""

FORBIDDEN_DATASETS = {"Q003_PROSPECTIVE", "VALIDATION_2021_2022", "RESERVED_FINAL_2023_2024"}
FORBIDDEN_REFERENCES = {"Q003", "RND-0044", "RND-0045", "RND-0046", "RND-0047", "RND-0048", "RND-0049"}
ALLOWED_DEVELOPMENT = {"DEVELOPMENT_2015_2020"}


class ResearchFirewallError(ValueError):
    pass


def _req(cond, message):
    if not cond:
        raise ResearchFirewallError(message)


def validate_research_declaration(declaration):
    _req(isinstance(declaration, dict), "declaration mapping required")
    _req(declaration.get("independent_of_q003") is True, "independence from Q003 required")
    _req(declaration.get("parameter_search") is False, "parameter search prohibited")
    _req(declaration.get("declared_trial_count") == 1, "exactly one declared trial required")
    _req(declaration.get("automatic_promotion") is False, "automatic promotion prohibited")
    _req(declaration.get("broker_writes") is False, "broker writes prohibited")
    _req(declaration.get("capital_authority") is False, "capital authority prohibited")
    datasets = set(declaration.get("datasets", ()))
    _req(datasets == ALLOWED_DEVELOPMENT, "development dataset must be exactly 2015-2020")
    _req(not datasets.intersection(FORBIDDEN_DATASETS), "forbidden evidence dataset referenced")
    references = set(declaration.get("strategy_references", ()))
    _req(not references.intersection(FORBIDDEN_REFERENCES), "Q003-adjacent strategy reference prohibited")
    hypothesis = declaration.get("hypothesis")
    _req(isinstance(hypothesis, str) and hypothesis.strip(), "fixed hypothesis required")
    params = declaration.get("fixed_parameters")
    _req(isinstance(params, dict) and params, "fixed parameters required")
    return {
        "status": "INDEPENDENT_RESEARCH_DECLARATION_ACCEPTED",
        "dataset": "DEVELOPMENT_2015_2020",
        "declared_trial_count": 1,
        "parameter_search": False,
        "automatic_promotion": False,
        "broker_writes": False,
        "capital_authority": False,
    }

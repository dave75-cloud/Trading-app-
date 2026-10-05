import unittest

from rnd0060_research_firewall import ResearchFirewallError, validate_research_declaration


def declaration(**overrides):
    out = {
        "independent_of_q003": True,
        "hypothesis": "Opening-range breakout has positive net development expectancy under fixed rules.",
        "fixed_parameters": {
            "timeframe": "M5",
            "opening_range_minutes": 30,
            "entry_buffer_pips": 0,
            "maximum_one_trade_per_day": True,
        },
        "datasets": ["DEVELOPMENT_2015_2020"],
        "strategy_references": [],
        "declared_trial_count": 1,
        "parameter_search": False,
        "automatic_promotion": False,
        "broker_writes": False,
        "capital_authority": False,
    }
    out.update(overrides)
    return out


class TestRND0060ResearchFirewall(unittest.TestCase):
    def test_fixed_independent_declaration_passes(self):
        out = validate_research_declaration(declaration())
        self.assertEqual(out["status"], "INDEPENDENT_RESEARCH_DECLARATION_ACCEPTED")

    def test_q003_reference_fails(self):
        with self.assertRaises(ResearchFirewallError):
            validate_research_declaration(declaration(strategy_references=["Q003"]))

    def test_consumed_validation_fails(self):
        with self.assertRaises(ResearchFirewallError):
            validate_research_declaration(declaration(datasets=["VALIDATION_2021_2022"]))

    def test_reserved_final_fails(self):
        with self.assertRaises(ResearchFirewallError):
            validate_research_declaration(declaration(datasets=["RESERVED_FINAL_2023_2024"]))

    def test_parameter_search_fails(self):
        with self.assertRaises(ResearchFirewallError):
            validate_research_declaration(declaration(parameter_search=True))

    def test_multiple_trials_fail(self):
        with self.assertRaises(ResearchFirewallError):
            validate_research_declaration(declaration(declared_trial_count=2))

    def test_broker_authority_fails(self):
        with self.assertRaises(ResearchFirewallError):
            validate_research_declaration(declaration(broker_writes=True))

    def test_missing_fixed_parameters_fails(self):
        with self.assertRaises(ResearchFirewallError):
            validate_research_declaration(declaration(fixed_parameters={}))


if __name__ == "__main__":
    unittest.main()

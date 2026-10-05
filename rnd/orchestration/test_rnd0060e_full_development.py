import sys
import unittest
from pathlib import Path

TOOLS=Path(__file__).resolve().parents[1]/"tools"
if str(TOOLS) not in sys.path: sys.path.insert(0,str(TOOLS))

from rnd0060e_full_development import classify,_declaration
from rnd0060_research_firewall import validate_research_declaration

SYMBOLS=("AUDUSD","EURUSD","GBPUSD","USDJPY")

def symbol_result(equity=1.02,net=0.04,annual=None):
    if annual is None: annual={2015:0.01,2016:0.01,2017:0.01,2018:0.01,2019:0.0,2020:0.0}
    return {"terminal_net_equity":equity,"realized_net_sum":net,"annual_realized_net":dict(annual)}

def results(**overrides):
    out={s:symbol_result() for s in SYMBOLS}; out.update(overrides); return out

def portfolio(**overrides):
    out={"final_equal_unit_normalized_equity_index":1.03,"realized_completed_trade_net_return_sum":0.16,"equal_unit_normalized_max_drawdown":-0.03,"status":"PASS"}; out.update(overrides); return out

class TestRND0060EFullDevelopment(unittest.TestCase):
    def test_frozen_declaration_passes_firewall(self):
        self.assertEqual(validate_research_declaration(_declaration())["status"],"INDEPENDENT_RESEARCH_DECLARATION_ACCEPTED")
    def test_all_criteria_pass_only_to_review(self):
        out=classify(results(),portfolio()); self.assertEqual(out["classification"],"ELIGIBLE_FOR_LATER_CANDIDATE_REVIEW"); self.assertTrue(all(out["criteria"].values()))
    def test_terminal_equity_failure_falsifies(self):
        self.assertEqual(classify(results(),portfolio(final_equal_unit_normalized_equity_index=1.0))["classification"],"DEVELOPMENT_FALSIFIED")
    def test_realized_net_failure_falsifies(self):
        self.assertEqual(classify(results(),portfolio(realized_completed_trade_net_return_sum=0.0))["classification"],"DEVELOPMENT_FALSIFIED")
    def test_fewer_than_three_positive_pairs_falsifies(self):
        vals=results(AUDUSD=symbol_result(equity=0.99),EURUSD=symbol_result(equity=0.99)); self.assertEqual(classify(vals,portfolio())["classification"],"DEVELOPMENT_FALSIFIED")
    def test_drawdown_failure_falsifies(self):
        self.assertEqual(classify(results(),portfolio(equal_unit_normalized_max_drawdown=-0.100001))["classification"],"DEVELOPMENT_FALSIFIED")
    def test_fewer_than_four_positive_years_falsifies(self):
        annual={2015:0.01,2016:0.01,2017:0.01,2018:-0.01,2019:-0.01,2020:-0.01}; vals={s:symbol_result(annual=annual) for s in SYMBOLS}; self.assertEqual(classify(vals,portfolio())["classification"],"DEVELOPMENT_FALSIFIED")
    def test_leave_one_pair_out_failure_falsifies(self):
        vals=results(AUDUSD=symbol_result(net=0.12),EURUSD=symbol_result(net=-0.03),GBPUSD=symbol_result(net=-0.03),USDJPY=symbol_result(net=-0.03)); self.assertEqual(classify(vals,portfolio(realized_completed_trade_net_return_sum=0.03))["classification"],"DEVELOPMENT_FALSIFIED")
    def test_integrity_failure_falsifies(self):
        self.assertEqual(classify(results(),portfolio(status="FAIL"))["classification"],"DEVELOPMENT_FALSIFIED")
    def test_no_extend_or_promotion_outcome(self):
        allowed={classify(results(),portfolio())["classification"],classify(results(),portfolio(status="FAIL"))["classification"]}; self.assertEqual(allowed,{"ELIGIBLE_FOR_LATER_CANDIDATE_REVIEW","DEVELOPMENT_FALSIFIED"})

if __name__=="__main__": unittest.main()

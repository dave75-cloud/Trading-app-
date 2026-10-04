#!/usr/bin/env python3
import unittest
from unittest import mock
import rnd0042_validation_adapter as a

class TestRND0042ValidationAdapter(unittest.TestCase):
    def test_frozen_constants(self):
        self.assertEqual(a.CANDIDATE_THRESHOLD,0.0006)
        self.assertEqual(a.VALIDATION_YEARS,frozenset({2020,2021,2022}))
    def test_restores_globals_after_success(self):
        oy=a.frozen.AUTHORIZED_YEARS; ot=a.frozen.VOL_THRESHOLD
        with mock.patch.object(a.frozen,"reconstruct_pair",return_value={"authorized_years":[2020,2021,2022]}):
            a.reconstruct_validation_candidate("AUDUSD",[])
        self.assertEqual(a.frozen.AUTHORIZED_YEARS,oy)
        self.assertEqual(a.frozen.VOL_THRESHOLD,ot)
    def test_restores_globals_after_failure(self):
        oy=a.frozen.AUTHORIZED_YEARS; ot=a.frozen.VOL_THRESHOLD
        with mock.patch.object(a.frozen,"reconstruct_pair",side_effect=RuntimeError("x")):
            with self.assertRaises(RuntimeError): a.reconstruct_validation_candidate("AUDUSD",[])
        self.assertEqual(a.frozen.AUTHORIZED_YEARS,oy)
        self.assertEqual(a.frozen.VOL_THRESHOLD,ot)

if __name__=="__main__": unittest.main()

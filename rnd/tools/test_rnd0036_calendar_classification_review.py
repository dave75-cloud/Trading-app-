#!/usr/bin/env python3

import unittest

from rnd0036_calendar_classification_review import _sum_bars


class TestRND0036CalendarClassificationReview(unittest.TestCase):
    def test_sum_bars_is_deterministic(self):
        classes = {
            "residual_short_gap": [
                {"bars": 1, "start_utc": "2020-01-01T00:00:00Z", "end_utc": "2020-01-01T00:00:00Z"},
                {"bars": 3, "start_utc": "2020-01-01T01:00:00Z", "end_utc": "2020-01-01T01:10:00Z"},
            ],
            "closure_shaped_candidate": [],
            "unclassified": [],
        }
        self.assertEqual(_sum_bars(classes, "residual_short_gap"), 4)

    def test_missing_class_defaults_zero(self):
        self.assertEqual(_sum_bars({}, "unclassified"), 0)


if __name__ == "__main__":
    unittest.main()

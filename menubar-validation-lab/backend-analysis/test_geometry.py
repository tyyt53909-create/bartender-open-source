#!/usr/bin/env python3
"""Meaningful boundary checks for the portable geometry verifier."""
import json
import unittest
from pathlib import Path
from geometry_verify import InputError, analyze, verify_samples

BASE = Path(__file__).resolve().parent


class GeometryBounds(unittest.TestCase):
    def test_pinned_case_expectations(self):
        report = verify_samples(json.loads((BASE / "geometry-samples.json").read_text()))
        self.assertTrue(report["all_arithmetic_expectations_match"])
        self.assertEqual(report["summary"]["macos_runtime_cases_executed"], 0)

    def test_wide_screen_capacity_rejected(self):
        report = analyze([{"width": 1512, "status_width": 663.5}, {"width": 3840}])
        self.assertEqual(report["maximum_span"], 3031)
        self.assertEqual(report["shortfall"], 809)
        self.assertEqual(report["candidate_action"], "do_not_collapse")
        self.assertEqual(report["macos_runtime_status"], "not_run")

    def test_one_half_point_beyond_capacity_changes_decision(self):
        inputs = [{"width": 1512, "status_width": 663.5}, {"width": 3031}]
        self.assertEqual(analyze(inputs)["shortfall"], 0)
        inputs[1]["width"] = 3031.5
        self.assertEqual(analyze(inputs)["shortfall"], 0.5)
        self.assertIn("capacity_shortfall", analyze(inputs)["violations"])

    def test_minimum_unit_can_break_margin_before_reaching_cliff(self):
        report = analyze([{"width": 450}])
        self.assertEqual(report["minimum_headroom"], 25)
        self.assertEqual(report["violations"], ["safety_margin_not_preserved"])

    def test_minimum_unit_can_reach_or_exceed_model_cliff(self):
        report = analyze([{"width": 390}])
        self.assertEqual(report["minimum_model_cliff"], 195)
        self.assertIn("unit_reaches_model_cliff", report["violations"])

    def test_missing_topology_is_not_success(self):
        with self.assertRaisesRegex(InputError, "^no_displays$"):
            analyze([])

    def test_nonfinite_and_boolean_widths_rejected(self):
        for width in [float("inf"), float("nan"), True]:
            with self.subTest(width=width), self.assertRaisesRegex(InputError, "^invalid_width$"):
                analyze([{"width": width}])

    def test_inconsistent_status_area_rejected(self):
        with self.assertRaisesRegex(InputError, "^invalid_status_width$"):
            analyze([{"width": 1000, "status_width": 1001}])

    def test_input_order_does_not_change_plan(self):
        inputs = [{"width": 1512, "status_width": 663.5}, {"width": 2560}]
        self.assertEqual(analyze(inputs), analyze(list(reversed(inputs))))

    def test_failed_expectation_does_not_report_success(self):
        document = json.loads((BASE / "geometry-samples.json").read_text())
        document["cases"][0]["expected"]["span"] = -1
        report = verify_samples(document)
        self.assertFalse(report["all_arithmetic_expectations_match"])

    def test_duplicate_case_id_is_rejected(self):
        document = json.loads((BASE / "geometry-samples.json").read_text())
        document["cases"].append(document["cases"][0])
        with self.assertRaisesRegex(InputError, "^invalid_or_duplicate_case_id$"):
            verify_samples(document)


if __name__ == "__main__":
    unittest.main()


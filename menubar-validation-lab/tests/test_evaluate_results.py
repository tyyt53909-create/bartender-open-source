"""Synthetic evaluator tests. These never run AppKit or represent Mac results."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("evaluate_results", ROOT / "tools/evaluate_results.py")
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)


class EvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        production = json.loads((ROOT / "protocol/test-cases.json").read_text())
        c = copy.deepcopy(next(x for x in production["cases"] if x["id"] == "MB-03"))
        c["required_coverage"] = [c["required_coverage"][0]]
        self.protocol = {
            "schema_version": "1.0",
            "protocol_id": "SYNTHETIC-unit-test-only",
            "fixture_contract": copy.deepcopy(production["fixture_contract"]),
            "cases": [c],
        }

    def tearDown(self):
        self.tmp.cleanup()

    def run_data(self, role="candidate"):
        run_id = "SYNTHETIC-" + role
        env = {
            "platform": "macOS",
            "machine_id": "SYNTHETIC-device",
            "os_version": "27.0-SYNTHETIC",
            "os_build": "SYNTHETIC-BUILD",
            "architecture": "arm64",
            "screen_topology": [{"id": "screen-1", "frame_points": [0, 0, 1512, 982],
                                 "scale": 2, "has_notch": True}],
            "menu_bar_auto_hide": False,
            "separate_spaces": True,
            "permission_profile": "ax_on_capture_off",
            "app_inventory": ["org.menuvalidation.Fixture"],
            "fixture_bundle_id": "org.menuvalidation.Fixture",
            "fixture_item_ids": ["org.menuvalidation.fixture." + item for item in ("alpha", "beta", "gamma")],
            "fixture_revision": {"kind": "source_sha256", "value": "a" * 64},
        }
        name = run_id + ".txt"
        (self.base / name).write_text("SYNTHETIC TEST DATA ONLY; no actual Mac observation.\n")
        evidence = {
            "id": run_id + "-observation",
            "kind": "operator_attested",
            "run_id": run_id,
            "case_id": "MB-03",
            "variant_id": "alpha",
            "observed_at_utc": "2026-11-20T01:00:30Z",
            "artifact": name,
            "sha256": ev.file_hash(self.base / name),
            "observer": "SYNTHETIC-test",
            "statement": "Synthetic test statement, never a real observation.",
        }
        return {
            "schema_version": "1.0",
            "protocol_id": self.protocol["protocol_id"],
            "protocol_sha256": ev.digest_json(self.protocol),
            "run_id": run_id,
            "comparison_group_id": "SYNTHETIC-group",
            "baseline_run_id": "SYNTHETIC-baseline" if role == "candidate" else None,
            "run_role": role,
            "run_kind": "mac_runtime",
            "started_at_utc": "2026-11-20T01:00:00Z",
            "finished_at_utc": "2026-11-20T01:01:00Z",
            "backend": {"id": "none" if role == "baseline" else "SYNTHETIC",
                        "strategy_id": "SYNTHETIC",
                        "revision": {"kind": "source_sha256", "value": "b" * 64},
                        "configuration_sha256": "c" * 64},
            "claimed_capabilities": ["activation_left"],
            "environment": env,
            "cases": [{"case_id": "MB-03", "coverage": [{
                "variant_id": "alpha",
                "status": "passed",
                "reason": "",
                "observations": "SYNTHETIC acceptance statement.",
                "context": {},
                "evidence": [evidence],
            }]}],
        }

    def record(self, run):
        return run["cases"][0]["coverage"][0]

    def evaluate(self, run, baseline=None):
        return ev.evaluate_run(run, self.protocol, self.base, baseline, self.base)

    def test_linux_preflight_cannot_pass(self):
        run = self.run_data()
        run["run_kind"] = "environment_preflight"
        run["environment"]["platform"] = "Linux"
        self.record(run).update(status="not_run", observations="", evidence=[])
        report = self.evaluate(run)
        self.assertEqual(report["release_verdict"], "blocked_by_environment")
        self.assertEqual(report["accepted_pass_variants"], 0)

    def test_linux_pass_claim_is_invalid(self):
        run = self.run_data()
        run["environment"]["platform"] = "Linux"
        self.assertEqual(self.evaluate(run)["release_verdict"], "invalid")

    def test_raw_event_does_not_prove_ui_acceptance(self):
        run = self.run_data()
        e = self.record(run)["evidence"][0]
        e["kind"] = "machine_observation"
        self.assertEqual(self.evaluate(run)["release_verdict"], "invalid")
        self.assertEqual(self.evaluate(run)["accepted_pass_variants"], 0)

    def test_missing_artifact_is_invalid(self):
        run = self.run_data()
        (self.base / self.record(run)["evidence"][0]["artifact"]).unlink()
        self.assertEqual(self.evaluate(run)["release_verdict"], "invalid")

    def test_tampered_artifact_is_invalid(self):
        run = self.run_data()
        (self.base / self.record(run)["evidence"][0]["artifact"]).write_text("changed")
        self.assertEqual(self.evaluate(run)["release_verdict"], "invalid")

    def test_unmatched_build_blocks_comparison(self):
        run, baseline = self.run_data(), self.run_data("baseline")
        baseline["environment"]["os_build"] = "DIFFERENT-SYNTHETIC"
        report = self.evaluate(run, baseline)
        self.assertEqual(report["release_verdict"], "invalid")
        self.assertIn("comparison_mismatch", {x["code"] for x in report["blocking_findings"]})

    def test_scope_does_not_turn_unsupported_into_pass(self):
        run = self.run_data()
        self.record(run).update(status="unsupported", reason="Synthetic unsupported case", evidence=[])
        report = self.evaluate(run)
        self.assertEqual(report["release_verdict"], "incomplete")
        self.assertEqual(report["suite_verdict"], "incomplete")
        self.assertEqual(report["accepted_pass_variants"], 0)

    def test_failure_is_release_blocking(self):
        run = self.run_data()
        self.record(run).update(status="failed", observations="Synthetic wrong target report.", evidence=[])
        report = self.evaluate(run)
        self.assertEqual(report["release_verdict"], "blocked")

    def test_full_attested_scope_with_matching_baseline_passes_only_scope(self):
        run, baseline = self.run_data(), self.run_data("baseline")
        report = self.evaluate(run, baseline)
        self.assertEqual(report["release_verdict"], "passed")
        self.assertEqual(report["comparison_verdict"], "matched")
        self.assertEqual(report["valid_evidence_counts"]["operator_attested"], 1)
        self.assertEqual(report["accepted_pass_variants"], 1)

    def test_unperformed_second_variant_is_incomplete(self):
        run, baseline = self.run_data(), self.run_data("baseline")
        self.protocol["cases"][0]["required_coverage"].append(
            {"id": "beta", "description": "Synthetic second variant", "requirements": {}})
        for r in (run, baseline):
            r["protocol_sha256"] = ev.digest_json(self.protocol)
        report = self.evaluate(run, baseline)
        self.assertEqual(report["release_verdict"], "incomplete")
        self.assertEqual(report["accepted_pass_variants"], 1)
        self.assertEqual(report["required_pending_variants"], 1)

    def test_wrong_run_evidence_is_invalid(self):
        run = self.run_data()
        self.record(run)["evidence"][0]["run_id"] = "SOME-OTHER-RUN"
        self.assertEqual(self.evaluate(run)["release_verdict"], "invalid")

    def test_missing_hardware_is_not_not_applicable(self):
        run = self.run_data()
        self.record(run).update(status="not_applicable", reason="No external screen", evidence=[])
        self.assertEqual(self.evaluate(run)["release_verdict"], "invalid")

    def test_protocol_change_requires_new_hash(self):
        run = self.run_data()
        self.protocol["cases"][0]["title"] = "Different meaning"
        self.assertEqual(self.evaluate(run)["release_verdict"], "invalid")

    def test_out_of_scope_feature_remains_exclusion_not_full_suite_success(self):
        run, baseline = self.run_data(), self.run_data("baseline")
        optional = copy.deepcopy(self.protocol["cases"][0])
        optional.update(id="OPTIONAL", capability="optional", applies_to=["candidate"], mandatory_for_candidate=False)
        self.protocol["cases"].append(optional)
        for r in (run, baseline):
            r["protocol_sha256"] = ev.digest_json(self.protocol)
        run["cases"].append({"case_id": "OPTIONAL", "coverage": [{
            "variant_id": "alpha", "status": "unsupported", "reason": "Excluded explicitly", "evidence": []}]})
        report = self.evaluate(run, baseline)
        self.assertEqual(report["release_verdict"], "passed")
        self.assertEqual(report["suite_verdict"], "incomplete")
        self.assertEqual(report["scope_exclusions"][0]["case_id"], "OPTIONAL")

    def test_failed_machine_assertion_cannot_be_relabelled_success(self):
        run = self.run_data()
        e = copy.deepcopy(self.record(run)["evidence"][0])
        e.update(id="SYNTHETIC-machine", kind="machine_verified",
                 assertion_id="fixture_action_count", verifier="SYNTHETIC",
                 verifier_revision={"kind": "source_sha256", "value": "d" * 64},
                 matched=True, expected=True, observed=1)
        self.record(run)["evidence"].append(e)
        self.assertEqual(self.evaluate(run)["release_verdict"], "invalid")

    def test_empty_capability_scope_never_passes_mac_acceptance(self):
        run, baseline = self.run_data(), self.run_data("baseline")
        run["claimed_capabilities"] = []
        self.assertEqual(self.evaluate(run, baseline)["release_verdict"], "invalid")
        baseline["claimed_capabilities"] = []
        self.assertEqual(self.evaluate(baseline)["release_verdict"], "invalid")

    def test_excluded_nonpass_cannot_hide_structured_failure(self):
        run, baseline = self.run_data(), self.run_data("baseline")
        optional = copy.deepcopy(self.protocol["cases"][0])
        optional.update(id="OPTIONAL", capability="optional", applies_to=["candidate"], mandatory_for_candidate=False)
        self.protocol["cases"].append(optional)
        for r in (run, baseline):
            r["protocol_sha256"] = ev.digest_json(self.protocol)
        record = {"variant_id": "alpha", "reason": "SYNTHETIC exclusion", "evidence": [{
            "id": "SYNTHETIC-negative-assertion", "kind": "machine_verified", "matched": False,
            "expected": "alpha", "observed": "beta"}]}
        run["cases"].append({"case_id": "OPTIONAL", "coverage": [record]})
        for state in ("unsupported", "blocked", "unknown", "not_run"):
            with self.subTest(state=state):
                record["status"] = state
                report = self.evaluate(run, baseline)
                self.assertEqual(report["release_verdict"], "blocked")
                self.assertIn("release_blocker", {f["code"] for f in report["blocking_findings"]})
        record["evidence"][0]["matched"] = True
        self.assertEqual(self.evaluate(run, baseline)["release_verdict"], "blocked")

    def test_variant_environment_must_match_baseline_variant(self):
        run, baseline = self.run_data(), self.run_data("baseline")
        self.record(run)["context"] = {"screen_topology": [
            {"id": "DIFFERENT-SYNTHETIC-screen", "frame_points": [0, 0, 3840, 2160],
             "scale": 1, "has_notch": False}]}
        report = self.evaluate(run, baseline)
        self.assertEqual(report["release_verdict"], "invalid")
        self.assertIn("comparison_mismatch", {f["code"] for f in report["blocking_findings"]})

    def test_context_patch_inherits_run_conditions(self):
        run, baseline = self.run_data(), self.run_data("baseline")
        self.record(run)["context"] = {"permission_profile": "ax_on_capture_off"}
        self.assertEqual(self.evaluate(run, baseline)["release_verdict"], "passed")

    def test_context_cannot_remove_required_screen_conditions(self):
        run, baseline = self.run_data(), self.run_data("baseline")
        self.record(run)["context"] = {"screen_topology": []}
        self.assertEqual(self.evaluate(run, baseline)["release_verdict"], "invalid")
        self.record(run)["context"] = {"permission_profile": "ax_on_capture_off"}
        self.protocol["cases"][0]["required_coverage"][0]["requirements"] = {"min_displays": 2}
        for r in (run, baseline):
            r["protocol_sha256"] = ev.digest_json(self.protocol)
        self.assertEqual(self.evaluate(run, baseline)["release_verdict"], "invalid")

    def test_matching_wrong_fixture_identity_still_fails_contract(self):
        run, baseline = self.run_data(), self.run_data("baseline")
        for r in (run, baseline):
            r["environment"]["fixture_bundle_id"] = "SYNTHETIC-wrong-fixture"
            r["environment"]["fixture_item_ids"] = ["SYNTHETIC-wrong-item"]
        report = self.evaluate(run, baseline)
        self.assertEqual(report["release_verdict"], "invalid")
        self.assertIn("invalid_environment", {f["code"] for f in report["blocking_findings"]})

    def test_candidate_strategy_identity_is_required(self):
        run, baseline = self.run_data(), self.run_data("baseline")
        run["backend"].pop("strategy_id")
        self.assertEqual(self.evaluate(run, baseline)["release_verdict"], "invalid")

    def test_nonfinite_screen_geometry_is_invalid(self):
        for field, value in (("scale", float("nan")), ("scale", float("inf")),
                             ("frame_points", [float("nan"), 0, 1512, 982]),
                             ("frame_points", [0, 0, float("inf"), 982])):
            with self.subTest(field=field, value=value):
                run, baseline = self.run_data(), self.run_data("baseline")
                for r in (run, baseline):
                    r["environment"]["screen_topology"][0][field] = value
                self.assertEqual(self.evaluate(run, baseline)["release_verdict"], "invalid")

    def test_passed_variant_needs_corresponding_baseline_even_outside_scope(self):
        run, baseline = self.run_data(), self.run_data("baseline")
        optional = copy.deepcopy(self.protocol["cases"][0])
        optional.update(id="OPTIONAL", capability="optional", mandatory_for_candidate=False)
        self.protocol["cases"].append(optional)
        for r in (run, baseline):
            r["protocol_sha256"] = ev.digest_json(self.protocol)
        record = copy.deepcopy(self.record(run))
        record["evidence"][0].update(id="SYNTHETIC-optional", case_id="OPTIONAL")
        run["cases"].append({"case_id": "OPTIONAL", "coverage": [record]})
        self.assertEqual(self.evaluate(run, baseline)["release_verdict"], "needs_baseline")


if __name__ == "__main__":
    unittest.main()


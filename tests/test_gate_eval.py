"""Synthetic, offline gate regressions. No fixture is a real acceptance receipt."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gate_eval", ROOT / "tools/gate_eval.py")
gate_eval = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gate_eval
spec.loader.exec_module(gate_eval)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


class Fixture:
    """Trust registries are inputs in this unit test, not signed real identities."""
    def __init__(self):
        self.artifacts = {}
        tasks = ["APP-02", "APP-04", "APP-05", "APP-06", "OPS-05", "OPS-06"]
        self.plan = {
            "tasks": [{"id": task, "task_spec_sha256": digest(task), "depends_on": [],
                       "execution_gates": []} for task in tasks],
            "gate_definitions": {}, "gate_policies": {}}
        authority = self.artifact("evidence/synthetic-authority.json", {"synthetic_only": True})
        self.runtime = {
            "now": "2026-11-20T13:00:00Z", "task_states": {}, "decisions": {}, "current_bindings": {},
            "authority_registry": {
                "principals": {"reviewer": {
                    "roles": ["reviewer", "lead"], "gate_ids": [], "authority_ref": authority,
                    "valid_from": "2026-11-20T10:00:00Z", "expires_at": "2026-11-20T18:00:00Z", "revoked": False}},
                "runs": {
                    "controller-run": {"principal_id": "controller", "parent_run_id": None},
                    "author-run": {"principal_id": "author", "parent_run_id": "controller-run"},
                    "reviewer-run": {"principal_id": "reviewer", "parent_run_id": "controller-run"}}}}
        for task in tasks:
            self.state(task, "planned")

    def artifact(self, path, content):
        body = content if isinstance(content, bytes) else json.dumps(content, sort_keys=True, ensure_ascii=False).encode()
        self.artifacts[path] = body
        return {"path": path, "sha256": hashlib.sha256(body).hexdigest()}

    def state(self, task, status):
        self.runtime["task_states"][task] = {"status": status, "task_spec_sha256": digest(task)}
        if status == "accepted":
            self.runtime["task_states"][task]["acceptance_ref"] = self.artifact(
                f"evidence/{task}-synthetic-acceptance.json", {"synthetic_only": True, "task_id": task, "status": status})

    def gate(self, gate, expression, source_tasks=("APP-02",), decision_required=True):
        self.plan["gate_definitions"][gate] = expression
        self.plan["gate_policies"][gate] = {
            "decision_required": decision_required, "permitted_source_tasks": list(source_tasks),
            "issuer_roles": ["reviewer", "lead"], "require_independent_run": True,
            "required_bindings": ["source", "scope", "context"]}
        self.runtime["authority_registry"]["principals"]["reviewer"]["gate_ids"].append(gate)

    def decision(self, gate, conditions, task="APP-02", decision="passed"):
        raw_result = self.artifact(f"evidence/{gate}-synthetic-worker.json", {"synthetic_only": True, "result": decision})
        run = self.artifact(f"evidence/{gate}-synthetic-run.json", {"synthetic_only": True, "run_id": "reviewer-run"})
        review = {
            "schema_version": "0.2", "record_type": "ReviewVerdict", "review_id": f"review-{gate}",
            "task_id": task, "author_attempt_id": "author-attempt", "author_run_id": "author-run",
            "reviewer_run_id": "reviewer-run", "reviewer_principal_id": "reviewer",
            "task_spec_sha256": digest(task), "contract_sha": "c" * 40,
            "reviewed_base_sha": "a" * 40, "reviewed_head_sha": "b" * 40,
            "verdict": "approved", "summary": "Synthetic review: deliverable quality is acceptable.",
            "findings": [], "coverage": {"checked": ["synthetic example"], "not_checked": ["real macOS behavior"]},
            "evidence_refs": [raw_result], "worker_result_ref": raw_result, "reviewer_manifest_ref": run,
            "effective_model_id": "synthetic-offline-model", "issued_at": "2026-11-20T11:00:00Z"}
        review_ref = self.artifact(f"evidence/{gate}-synthetic-review.json", review)
        scope_ref = self.artifact(f"evidence/{gate}-synthetic-scope.json", {"scope_id": "synthetic-scope", "synthetic_only": True})
        context_ref = self.artifact(f"evidence/{gate}-synthetic-context.json", {
            "context_id": "synthetic-context", "environment_ids": ["synthetic-mac26"], "synthetic_only": True})
        receipt = {
            "schema_version": "0.2", "record_type": "GateDecision", "decision_id": f"decision-{gate}",
            "gate_id": gate, "decision": decision, "issued_at": "2026-11-20T12:00:00Z",
            "expires_at": "2026-11-20T16:00:00Z",
            "source": {"repository_id": "synthetic-repository", "task_id": task,
                       "author_attempt_id": "author-attempt", "author_run_id": "author-run",
                       "task_spec_sha256": digest(task), "contract_sha": "c" * 40,
                       "base_sha": "a" * 40, "head_sha": "b" * 40, "candidate_sha": None,
                       "review_verdict_ref": review_ref},
            "scope": {"scope_id": "synthetic-scope", "manifest_ref": scope_ref},
            "context": {"context_id": "synthetic-context", "manifest_ref": context_ref},
            "issuer": {"principal_id": "reviewer", "role": "reviewer", "run_id": "reviewer-run",
                       "authority_ref": self.runtime["authority_registry"]["principals"]["reviewer"]["authority_ref"]},
            "evidence": [{"condition_name": condition, "outcome": outcome, "environment_id": "synthetic-mac26",
                          "artifact": self.artifact(f"evidence/{gate}-{condition}-synthetic-result.json",
                                                    {"synthetic_only": True, "condition": condition, "outcome": outcome})}
                         for condition, outcome in conditions.items()]}
        self.runtime["decisions"][gate] = receipt
        self.rebind(gate)
        return receipt

    def rebind(self, gate):
        receipt = self.runtime["decisions"][gate]
        self.runtime["current_bindings"][gate] = copy.deepcopy({key: receipt[key] for key in ("source", "scope", "context")})

    def revise_review(self, gate, changes):
        receipt = self.runtime["decisions"][gate]
        ref = receipt["source"]["review_verdict_ref"]
        review = json.loads(self.artifacts[ref["path"]])
        review.update(changes)
        receipt["source"]["review_verdict_ref"] = self.artifact(ref["path"], review)
        self.rebind(gate)

    def evaluate(self, gate):
        return gate_eval.Evaluator(self.plan, self.runtime, self.artifacts.__getitem__).gate(gate)

    def baseline(self):
        self.gate("M0_BASELINE_VERIFIED", {"all_of": [
            {"kind": "task_accepted", "task_id": "APP-02"},
            {"kind": "evidence_condition", "name": "selected_mac_baseline_verified", "requires_bound_artifacts": True}]})
        self.state("APP-02", "accepted")
        return self.decision("M0_BASELINE_VERIFIED", {"selected_mac_baseline_verified": "passed"})

    def add_subjects(self, gate="M0_BASELINE_VERIFIED"):
        required = ["APP-04", "APP-05"]
        self.plan["gate_policies"][gate]["required_subject_tasks"] = required
        records = []
        for task in required:
            self.state(task, "accepted")
            run = f"subject-{task}-run"
            self.runtime["authority_registry"]["runs"][run] = {"principal_id": f"subject-{task}", "parent_run_id": "controller-run"}
            records.append({"task_id": task, "task_spec_sha256": digest(task), "head_sha": "d" * 40, "author_run_ids": [run]})
        receipt = self.runtime["decisions"][gate]
        ref = receipt["context"]["manifest_ref"]
        manifest = json.loads(self.artifacts[ref["path"]])
        manifest["subject_bindings"] = records
        receipt["context"]["manifest_ref"] = self.artifact(ref["path"], manifest)
        self.runtime["subject_bindings"] = {record["task_id"]: copy.deepcopy(record) for record in records}
        self.rebind(gate)


class GateEvaluationTests(unittest.TestCase):
    def assert_code(self, result, code, status=gate_eval.UNKNOWN):
        self.assertEqual(result.status, status, result.as_dict(trace=True))
        self.assertIn(code, {item["code"] for item in result.blockers}, result.as_dict(trace=True))

    def test_complete_current_baseline_passes(self):
        fixture = Fixture()
        fixture.baseline()
        result = fixture.evaluate("M0_BASELINE_VERIFIED")
        self.assertTrue(result)
        self.assertEqual(result.status, gate_eval.TRUE)
        self.assertTrue(result.evidence_refs)
        self.assertEqual(result.blockers, ())

    def test_strong_kleene_truth_tables(self):
        expected = {
            "all_of": {(a, b): "false" if "false" in (a, b) else "unknown" if "unknown" in (a, b) else "true"
                       for a in ("true", "false", "unknown") for b in ("true", "false", "unknown")},
            "any_of": {(a, b): "true" if "true" in (a, b) else "unknown" if "unknown" in (a, b) else "false"
                       for a in ("true", "false", "unknown") for b in ("true", "false", "unknown")}}
        for operator, pairs in expected.items():
            for pair, answer in pairs.items():
                with self.subTest(operator=operator, pair=pair):
                    fixture = Fixture()
                    for task, status in zip(("OPS-05", "OPS-06"), pair):
                        if status == "unknown":
                            del fixture.runtime["task_states"][task]
                        else:
                            fixture.state(task, "accepted" if status == "true" else "planned")
                    evaluator = gate_eval.Evaluator(fixture.plan, fixture.runtime, fixture.artifacts.__getitem__)
                    result = evaluator.expression({operator: [{"kind": "task_accepted", "task_id": task}
                                                              for task in ("OPS-05", "OPS-06")]})
                    self.assertEqual(result.status, answer)
                    self.assertEqual(bool(result), answer == "true")

    def test_either_verified_runner_is_sufficient(self):
        for selected, condition in (("OPS-05", "codex_runner_verified"), ("OPS-06", "opencode_runner_verified")):
            with self.subTest(selected=selected):
                fixture = Fixture()
                fixture.gate("at_least_one_runner_ready", {"any_of": [
                    {"all_of": [{"kind": "task_accepted", "task_id": "OPS-05"},
                                {"kind": "evidence_condition", "name": "codex_runner_verified"}]},
                    {"all_of": [{"kind": "task_accepted", "task_id": "OPS-06"},
                                {"kind": "evidence_condition", "name": "opencode_runner_verified"}]}]},
                    source_tasks=("OPS-05", "OPS-06"))
                fixture.state(selected, "accepted")
                fixture.decision("at_least_one_runner_ready", {condition: "passed"}, task=selected)
                result = fixture.evaluate("at_least_one_runner_ready")
                self.assertEqual(result.status, "true", result.as_dict(trace=True))
                self.assertEqual(result.blockers, ())

    def test_accepted_failure_does_not_verify_baseline(self):
        fixture = Fixture()
        receipt = fixture.baseline()
        receipt["decision"] = "failed"
        receipt["evidence"][0]["outcome"] = "failed"
        result = fixture.evaluate("M0_BASELINE_VERIFIED")
        self.assert_code(result, "GATE_FAILED", "false")
        self.assertEqual(fixture.runtime["task_states"]["APP-02"]["status"], "accepted")

    def test_negative_research_can_reach_review_without_product_pass(self):
        fixture = Fixture()
        fixture.gate("M1_ROUTE_EVIDENCE_READY", {"all_of": [
            {"kind": "task_accepted", "task_id": "APP-04"},
            {"any_of": [{"kind": "task_accepted", "task_id": "APP-05"},
                        {"kind": "task_accepted", "task_id": "APP-06"}]},
            {"kind": "evidence_condition", "name": "complete_selected_route_research_with_matching_baseline"}]},
            source_tasks=("APP-05", "APP-06"))
        fixture.state("APP-04", "accepted")
        fixture.state("APP-05", "accepted")
        fixture.decision("M1_ROUTE_EVIDENCE_READY", {"complete_selected_route_research_with_matching_baseline": "passed"}, task="APP-05")
        fixture.runtime["task_states"]["APP-05"]["capability_verdict"] = "failed"
        fixture.gate("M1_PRODUCT_GATE_PASSED", {"kind": "evidence_condition", "name": "route_worked"}, source_tasks=("APP-05",))
        fixture.decision("M1_PRODUCT_GATE_PASSED", {"route_worked": "failed"}, task="APP-05", decision="failed")
        self.assertEqual(fixture.evaluate("M1_ROUTE_EVIDENCE_READY").status, "true")
        self.assertEqual(fixture.evaluate("M1_PRODUCT_GATE_PASSED").status, "false")

    def test_selected_evidence_source_must_itself_be_accepted(self):
        fixture = Fixture()
        fixture.gate("research", {"all_of": [
            {"any_of": [{"kind": "task_accepted", "task_id": "APP-05"},
                        {"kind": "task_accepted", "task_id": "APP-06"}]},
            {"kind": "evidence_condition", "name": "research_complete"}]},
            source_tasks=("APP-05", "APP-06"))
        fixture.state("APP-05", "accepted")
        fixture.decision("research", {"research_complete": "passed"}, task="APP-06")
        self.assert_code(fixture.evaluate("research"), "TASK_NOT_ACCEPTED", "false")

    def test_runner_condition_is_bound_to_its_own_adapter_task(self):
        fixture = Fixture()
        fixture.gate("runner", {"kind": "evidence_condition", "name": "codex_runner_verified"}, source_tasks=("OPS-05", "OPS-06"))
        fixture.plan["gate_policies"]["runner"]["condition_source_tasks"] = {"codex_runner_verified": ["OPS-05"], "opencode_runner_verified": ["OPS-06"]}
        fixture.state("OPS-06", "accepted")
        fixture.decision("runner", {"codex_runner_verified": "passed"}, task="OPS-06")
        self.assert_code(fixture.evaluate("runner"), "EVIDENCE_SOURCE_TASK_MISMATCH")

    def test_no_decision_means_unknown(self):
        fixture = Fixture()
        fixture.baseline()
        fixture.runtime["decisions"].clear()
        self.assert_code(fixture.evaluate("M0_BASELINE_VERIFIED"), "GATE_DECISION_MISSING")

    def test_worker_claim_cannot_substitute_task_state(self):
        fixture = Fixture()
        fixture.baseline()
        fixture.runtime["task_states"]["APP-02"] = {"claimed_outcome": "accepted", "task_spec_sha256": digest("APP-02")}
        self.assert_code(fixture.evaluate("M0_BASELINE_VERIFIED"), "TASK_STATE_UNKNOWN")

    def test_task_acceptance_without_bound_receipt_stays_unknown(self):
        fixture = Fixture()
        fixture.baseline()
        del fixture.runtime["task_states"]["APP-02"]["acceptance_ref"]
        self.assert_code(fixture.evaluate("M0_BASELINE_VERIFIED"), "INVALID_ARTIFACT_REFERENCE")

    def test_expired_future_invalid_and_timezone_free_times(self):
        cases = [("expires_at", "2026-11-20T12:30:00Z", "EXPIRED"),
                 ("issued_at", "2026-11-20T14:00:00Z", "INVALID_TIME_WINDOW"),
                 ("issued_at", "2026-02-30T12:00:00Z", None),
                 ("issued_at", "2026-11-20T12:00:00", None)]
        for key, value, code in cases:
            with self.subTest(key=key, value=value):
                fixture = Fixture()
                receipt = fixture.baseline()
                receipt[key] = value
                result = fixture.evaluate("M0_BASELINE_VERIFIED")
                self.assertEqual(result.status, "unknown")
                if code:
                    self.assert_code(result, code)

    def test_expiration_at_now_is_not_valid(self):
        fixture = Fixture()
        receipt = fixture.baseline()
        receipt["expires_at"] = fixture.runtime["now"]
        self.assert_code(fixture.evaluate("M0_BASELINE_VERIFIED"), "EXPIRED")

    def test_missing_current_clock_does_not_pass(self):
        fixture = Fixture()
        fixture.baseline()
        del fixture.runtime["now"]
        self.assert_code(fixture.evaluate("M0_BASELINE_VERIFIED"), "TIME_BINDING_MISSING")

    def test_source_contract_candidate_scope_and_context_changes_invalidate(self):
        for component, field, value, code in [
            ("source", "head_sha", "d" * 40, "SOURCE_BINDING_MISMATCH"),
            ("source", "contract_sha", "e" * 40, "SOURCE_BINDING_MISMATCH"),
            ("source", "candidate_sha", "f" * 40, "SOURCE_BINDING_MISMATCH"),
            ("scope", "scope_id", "other-scope", "SCOPE_BINDING_MISMATCH"),
            ("context", "context_id", "mac27-context", "CONTEXT_BINDING_MISMATCH")]:
            with self.subTest(component=component, field=field):
                fixture = Fixture()
                fixture.baseline()
                fixture.runtime["current_bindings"]["M0_BASELINE_VERIFIED"][component][field] = value
                self.assert_code(fixture.evaluate("M0_BASELINE_VERIFIED"), code)

    def test_changed_task_spec_invalidates_prior_acceptance_and_gate(self):
        fixture = Fixture()
        fixture.baseline()
        next(task for task in fixture.plan["tasks"] if task["id"] == "APP-02")["task_spec_sha256"] = digest("new task spec")
        result = fixture.evaluate("M0_BASELINE_VERIFIED")
        self.assert_code(result, "TASK_SPEC_CHANGED")
        self.assertIn("SOURCE_TASK_SPEC_CHANGED", {item["code"] for item in result.blockers})

    def test_missing_or_modified_artifact_fails_closed(self):
        for remove in (True, False):
            with self.subTest(remove=remove):
                fixture = Fixture()
                receipt = fixture.baseline()
                path = receipt["evidence"][0]["artifact"]["path"]
                if remove:
                    del fixture.artifacts[path]
                else:
                    fixture.artifacts[path] += b"modified"
                self.assert_code(fixture.evaluate("M0_BASELINE_VERIFIED"), "ARTIFACT_UNREADABLE" if remove else "ARTIFACT_HASH_MISMATCH")

    def test_hash_without_artifact_bytes_is_not_proof(self):
        fixture = Fixture()
        fixture.baseline()
        fixture.runtime["verified_artifacts"] = {path: hashlib.sha256(body).hexdigest() for path, body in fixture.artifacts.items()}
        result = gate_eval.Evaluator(fixture.plan, fixture.runtime).gate("M0_BASELINE_VERIFIED")
        self.assert_code(result, "ARTIFACT_LOADER_MISSING")

    def test_unknown_or_revoked_issuer_cannot_self_authorize(self):
        for change in ("unknown", "revoked", "wrong_gate", "wrong_role"):
            with self.subTest(change=change):
                fixture = Fixture()
                fixture.baseline()
                principal = fixture.runtime["authority_registry"]["principals"]["reviewer"]
                if change == "unknown":
                    fixture.runtime["authority_registry"]["principals"].clear()
                elif change == "revoked":
                    principal["revoked"] = True
                elif change == "wrong_gate":
                    principal["gate_ids"] = ["some-other-gate"]
                else:
                    principal["roles"] = ["author"]
                result = fixture.evaluate("M0_BASELINE_VERIFIED")
                self.assert_code(result, "UNKNOWN_AUTHORITY" if change == "unknown" else "UNAUTHORIZED_ISSUER")

    def test_author_or_author_descendant_is_not_an_independent_reviewer(self):
        for own_run in (True, False):
            with self.subTest(own_run=own_run):
                fixture = Fixture()
                receipt = fixture.baseline()
                if own_run:
                    receipt["issuer"]["run_id"] = "author-run"
                else:
                    fixture.runtime["authority_registry"]["runs"]["reviewer-run"]["parent_run_id"] = "author-run"
                self.assert_code(fixture.evaluate("M0_BASELINE_VERIFIED"), "NON_INDEPENDENT_REVIEW")

    def test_incomplete_or_cyclic_run_ancestry_is_unknown(self):
        for parent, code in (("missing-run", "RUN_ANCESTRY_INCOMPLETE"), ("reviewer-run", "RUN_ANCESTRY_CYCLE")):
            fixture = Fixture()
            fixture.baseline()
            fixture.runtime["authority_registry"]["runs"]["reviewer-run"]["parent_run_id"] = parent
            self.assert_code(fixture.evaluate("M0_BASELINE_VERIFIED"), code)

    def test_review_for_different_head_is_rejected(self):
        fixture = Fixture()
        fixture.baseline()
        fixture.revise_review("M0_BASELINE_VERIFIED", {"reviewed_head_sha": "e" * 40})
        self.assert_code(fixture.evaluate("M0_BASELINE_VERIFIED"), "REVIEW_SOURCE_MISMATCH")

    def test_unapproved_review_is_not_accepted(self):
        fixture = Fixture()
        fixture.baseline()
        fixture.revise_review("M0_BASELINE_VERIFIED", {"verdict": "changes_requested"})
        self.assert_code(fixture.evaluate("M0_BASELINE_VERIFIED"), "REVIEW_NOT_APPROVED", "false")

    def test_schema_invalid_receipt_fails_closed(self):
        fixture = Fixture()
        receipt = fixture.baseline()
        receipt["source"]["head_sha"] = None
        fixture.rebind("M0_BASELINE_VERIFIED")
        self.assert_code(fixture.evaluate("M0_BASELINE_VERIFIED"), "INVALID_RECEIPT_SCHEMA")

    def test_required_condition_cannot_be_replaced_with_other_success(self):
        fixture = Fixture()
        receipt = fixture.baseline()
        receipt["evidence"][0]["condition_name"] = "unrelated_success"
        self.assert_code(fixture.evaluate("M0_BASELINE_VERIFIED"), "REQUIRED_EVIDENCE_MISSING")

    def test_duplicate_evidence_condition_is_ambiguous(self):
        fixture = Fixture()
        receipt = fixture.baseline()
        receipt["evidence"].append(copy.deepcopy(receipt["evidence"][0]))
        self.assert_code(fixture.evaluate("M0_BASELINE_VERIFIED"), "DUPLICATE_EVIDENCE_CONDITION")

    def test_evidence_from_another_os_cannot_be_borrowed(self):
        fixture = Fixture()
        receipt = fixture.baseline()
        receipt["evidence"][0]["environment_id"] = "synthetic-mac27"
        self.assert_code(fixture.evaluate("M0_BASELINE_VERIFIED"), "EVIDENCE_ENVIRONMENT_MISMATCH")

    def test_context_manifest_must_name_the_current_environment(self):
        fixture = Fixture()
        receipt = fixture.baseline()
        receipt["context"]["manifest_ref"] = fixture.artifact("evidence/context-without-environments.json", {"context_id": "synthetic-context"})
        fixture.rebind("M0_BASELINE_VERIFIED")
        self.assert_code(fixture.evaluate("M0_BASELINE_VERIFIED"), "CONTEXT_ENVIRONMENTS_MISSING")

    def test_aggregate_gate_requires_all_current_subject_bindings(self):
        fixture = Fixture()
        fixture.baseline()
        fixture.add_subjects()
        self.assertEqual(fixture.evaluate("M0_BASELINE_VERIFIED").status, "true")
        del fixture.runtime["subject_bindings"]["APP-05"]
        self.assert_code(fixture.evaluate("M0_BASELINE_VERIFIED"), "SUBJECT_BINDING_MISMATCH")

    def test_aggregate_gate_cannot_omit_subject_manifest(self):
        fixture = Fixture()
        fixture.baseline()
        fixture.plan["gate_policies"]["M0_BASELINE_VERIFIED"]["required_subject_tasks"] = ["APP-04", "APP-05"]
        self.assert_code(fixture.evaluate("M0_BASELINE_VERIFIED"), "SUBJECT_BINDINGS_MISSING")

    def test_aggregate_gate_rejects_changed_subject_head_or_unaccepted_subject(self):
        for change in ("head", "acceptance"):
            with self.subTest(change=change):
                fixture = Fixture()
                fixture.baseline()
                fixture.add_subjects()
                if change == "head":
                    fixture.runtime["subject_bindings"]["APP-05"]["head_sha"] = "f" * 40
                    self.assert_code(fixture.evaluate("M0_BASELINE_VERIFIED"), "SUBJECT_BINDING_MISMATCH")
                else:
                    fixture.state("APP-05", "planned")
                    self.assert_code(fixture.evaluate("M0_BASELINE_VERIFIED"), "TASK_NOT_ACCEPTED", "false")

    def test_aggregate_author_reviewer_and_issuer_must_be_independent_of_all_subject_authors(self):
        for actor in ("aggregate_author", "reviewer", "issuer"):
            with self.subTest(actor=actor):
                fixture = Fixture()
                receipt = fixture.baseline()
                fixture.add_subjects()
                runs = fixture.runtime["authority_registry"]["runs"]
                if actor == "aggregate_author":
                    runs["author-run"]["parent_run_id"] = "subject-APP-05-run"
                elif actor == "reviewer":
                    runs["reviewer-run"]["parent_run_id"] = "subject-APP-05-run"
                else:
                    runs["gate-lead-run"] = {"principal_id": "reviewer", "parent_run_id": "subject-APP-05-run"}
                    receipt["issuer"]["run_id"] = "gate-lead-run"
                    receipt["issuer"]["role"] = "lead"
                self.assert_code(fixture.evaluate("M0_BASELINE_VERIFIED"), "NON_INDEPENDENT_REVIEW")

    def test_gate_reference_and_cycle(self):
        fixture = Fixture()
        fixture.baseline()
        fixture.gate("outer", {"kind": "gate_ref", "gate_id": "M0_BASELINE_VERIFIED"}, decision_required=False)
        self.assertEqual(fixture.evaluate("outer").status, "true")
        fixture.plan["gate_definitions"]["M0_BASELINE_VERIFIED"] = {"kind": "gate_ref", "gate_id": "outer"}
        self.assert_code(fixture.evaluate("outer"), "GATE_CYCLE")

    def test_empty_or_malformed_expressions_never_pass(self):
        evaluator = gate_eval.Evaluator({"tasks": []})
        for expr in ({"all_of": []}, {"any_of": []}, {}, "eval(1)",
                     {"all_of": [], "kind": "task_accepted"}, {"kind": "unknown"}):
            with self.subTest(expr=expr):
                self.assertEqual(evaluator.expression(expr).status, "unknown")

    def test_host_observation_is_bound_fresh_and_typed(self):
        fixture = Fixture()
        fixture.gate("host_macos_26", {"kind": "host_attribute", "attribute": "os_major", "equals": 26}, decision_required=False)
        host = {"host_id": "synthetic-host", "attributes": {"os_major": 26},
                "observed_at": "2026-11-20T12:00:00Z", "expires_at": "2026-11-20T14:00:00Z"}
        ref = fixture.artifact("evidence/synthetic-host.json", host)
        fixture.runtime["host"] = {**host, "manifest_ref": ref}
        fixture.runtime["selected_host_id"] = host["host_id"]
        self.assertEqual(fixture.evaluate("host_macos_26").status, "true")
        fixture.runtime["selected_host_id"] = "other-host"
        self.assert_code(fixture.evaluate("host_macos_26"), "HOST_CONTEXT_MISSING")
        fixture.runtime["selected_host_id"] = host["host_id"]
        fixture.runtime["now"] = "2026-11-20T15:00:00Z"
        self.assert_code(fixture.evaluate("host_macos_26"), "EXPIRED")

    def test_host_missing_id_cannot_pass_with_a_matching_empty_selection(self):
        fixture = Fixture()
        fixture.gate("host", {"kind": "host_attribute", "attribute": "os_major", "equals": 26}, decision_required=False)
        host = {"attributes": {"os_major": 26}, "observed_at": "2026-11-20T12:00:00Z", "expires_at": "2026-11-20T14:00:00Z"}
        fixture.runtime["host"] = {**host, "manifest_ref": fixture.artifact("evidence/idless-host.json", host)}
        self.assert_code(fixture.evaluate("host"), "HOST_CONTEXT_MISSING")

    def test_authority_grant_requires_bound_owner_authority(self):
        fixture = Fixture()
        gate = "pilot_participation_authorized"
        fixture.gate(gate, {"kind": "authority_condition", "name": gate}, decision_required=False)
        principal = fixture.runtime["authority_registry"]["principals"]["reviewer"]
        principal["roles"].append("product_owner")
        scope = {"scope_id": "pilot-scope", "manifest_ref": fixture.artifact("evidence/pilot-scope.json", {"scope_id": "pilot-scope"})}
        context = {"context_id": "pilot-context", "manifest_ref": fixture.artifact("evidence/pilot-context.json", {"context_id": "pilot-context"})}
        grant = {"gate_id": gate, "granted": True, "valid_from": "2026-11-20T12:00:00Z", "expires_at": "2026-11-20T14:00:00Z",
                 "scope": scope, "context": context,
                 "issuer": {"principal_id": "reviewer", "role": "product_owner", "authority_ref": principal["authority_ref"]}}
        grant_ref = fixture.artifact("evidence/pilot-grant.json", grant)
        fixture.runtime["authority_grants"] = {gate: {**grant, "grant_ref": grant_ref}}
        fixture.runtime["current_bindings"][gate] = {"scope": scope, "context": context}
        self.assertEqual(fixture.evaluate(gate).status, "true")
        fixture.runtime["authority_grants"][gate]["granted"] = False
        self.assert_code(fixture.evaluate(gate), "AUTHORITY_GRANT_MISMATCH")

    def test_graph_preserves_any_of_and_gate_ref_edges(self):
        fixture = Fixture()
        fixture.gate("runner", {"any_of": [{"kind": "task_accepted", "task_id": "OPS-05"},
                                          {"kind": "task_accepted", "task_id": "OPS-06"}]}, decision_required=False)
        fixture.gate("outer", {"kind": "gate_ref", "gate_id": "runner"}, decision_required=False)
        next(task for task in fixture.plan["tasks"] if task["id"] == "APP-02")["execution_gates"] = ["outer"]
        graph = gate_eval.dependency_graph(fixture.plan)
        self.assertEqual(graph["gate_requirements"]["runner"], fixture.plan["gate_definitions"]["runner"])
        self.assertIn("any_of", graph["gate_requirements"]["runner"])
        self.assertTrue(any(edge["from"] == "gate:outer" and edge["to"] == "gate:runner" for edge in graph["reference_edges"]))
        self.assertEqual(graph["errors"], [])
        self.assertEqual(graph["conservative_cycles"], [])

    def test_graph_reports_gate_cycles(self):
        plan = {"tasks": [], "gate_definitions": {"A": {"kind": "gate_ref", "gate_id": "B"}, "B": {"kind": "gate_ref", "gate_id": "A"}}}
        self.assertTrue(gate_eval.dependency_graph(plan)["conservative_cycles"])

    def test_artifact_loader_blocks_traversal_and_symlink_escape(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "root"
            root.mkdir()
            outside = Path(folder) / "outside.txt"
            outside.write_text("must not load")
            (root / "escape").symlink_to(outside)
            loader = gate_eval.local_artifact_loader(root)
            for path in ("../outside.txt", "escape", "/absolute/file", "C:\\file"):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    loader(path)

    def test_shipped_snapshot_does_not_fabricate_gate_evidence(self):
        plan = json.loads((ROOT / "coordination/tasks.json").read_text())
        evaluator = gate_eval.Evaluator(plan)
        for gate in plan["gate_definitions"]:
            with self.subTest(gate=gate):
                self.assertEqual(evaluator.gate(gate).status, "unknown")
        graph = gate_eval.dependency_graph(plan)
        self.assertEqual(graph["errors"], [])
        self.assertEqual(graph["conservative_cycles"], [])


if __name__ == "__main__":
    unittest.main()

"""Offline contract regression tests. Synthetic fixtures never authorize real runs."""

import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validator(stem):
    return Draft202012Validator(
        load(CONTRACTS / (stem + ".schema.json")), format_checker=FormatChecker()
    )


class ContractTests(unittest.TestCase):
    def test_all_schemas_are_valid_draft_2020_12(self):
        paths = sorted(CONTRACTS.glob("*.schema.json"))
        self.assertEqual(len(paths), 6)
        for path in paths:
            with self.subTest(schema=path.name):
                Draft202012Validator.check_schema(load(path))

    def test_valid_synthetic_receipts(self):
        manifest = load(CONTRACTS / "fixtures" / "manifest.json")
        for fixture in manifest["valid"]:
            with self.subTest(fixture=fixture["path"]):
                schema = load(CONTRACTS / fixture["schema"])
                Draft202012Validator(schema, format_checker=FormatChecker()).validate(
                    load(CONTRACTS / "fixtures" / fixture["path"])
                )

    def test_invalid_synthetic_receipts_are_rejected(self):
        manifest = load(CONTRACTS / "fixtures" / "manifest.json")
        for fixture in manifest["invalid"]:
            with self.subTest(fixture=fixture["path"]):
                schema = load(CONTRACTS / fixture["schema"])
                errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(
                    load(CONTRACTS / "fixtures" / fixture["path"])
                ))
                self.assertTrue(errors, fixture["case"])

    def test_all_template_envelopes_and_unfilled_payloads_are_rejected(self):
        for stem in ["worker-result", "run-manifest", "review-verdict", "integration-receipt", "gate-decision"]:
            template = load(ROOT / "templates" / (stem + ".json"))
            with self.subTest(record=stem):
                self.assertEqual(template["template_status"], "template_not_executed")
                self.assertFalse(validator(stem).is_valid(template))
                self.assertFalse(validator(stem).is_valid(template["payload"]))

    def test_content_hash_is_not_a_git_oid(self):
        gate = load(CONTRACTS / "fixtures" / "valid" / "gate-decision.synthetic.json")
        gate["source"]["contract_sha"] = "a" * 64
        self.assertTrue(validator("gate-decision").is_valid(gate))
        gate["source"]["task_spec_sha256"] = "a" * 40
        self.assertFalse(validator("gate-decision").is_valid(gate))

    def test_approved_review_cannot_hide_open_blocking_finding(self):
        review = load(CONTRACTS / "fixtures" / "valid" / "review-verdict.synthetic.json")
        review["findings"].append({
            "finding_id": "synthetic-blocker", "severity": "P0", "blocking": True,
            "status": "open", "description": "Synthetic blocking regression.",
            "evidence_refs": copy.deepcopy(review["evidence_refs"]),
        })
        self.assertFalse(validator("review-verdict").is_valid(review))
        review["verdict"] = "changes_requested"
        self.assertTrue(validator("review-verdict").is_valid(review))

    def test_terminal_run_does_not_claim_process_stopped_without_receipt(self):
        run = load(CONTRACTS / "fixtures" / "valid" / "run-manifest.synthetic.json")
        run["stop_receipt_ref"] = None
        self.assertFalse(validator("run-manifest").is_valid(run))
        run["stop_state"] = "unknown"
        self.assertTrue(validator("run-manifest").is_valid(run))

    def test_queue_receipt_is_valid_only_without_actual_merge_claim(self):
        receipt = load(CONTRACTS / "fixtures" / "valid" / "integration-receipt.synthetic.json")
        receipt.update(status="queued", merge_request_state="queued", merge_commit_sha=None,
                       merge_tree_oid=None, merge_parents=[], readback_evidence_ref=None,
                       actual_merge_confirmed_at=None)
        self.assertTrue(validator("integration-receipt").is_valid(receipt))

    def test_unknown_observation_cannot_be_promoted_by_shape_alone(self):
        worker = load(CONTRACTS / "fixtures" / "valid" / "worker-result.synthetic.json")
        check = worker["checks"][0]
        check.update(status="not_run", environment_id=None, evidence_ref=None,
                     reason="No real host available; no observation occurred.")
        self.assertTrue(validator("worker-result").is_valid(worker))
        check["status"] = "passed"
        self.assertFalse(validator("worker-result").is_valid(worker))

    def test_timestamp_format_is_enforced(self):
        gate = load(CONTRACTS / "fixtures" / "valid" / "gate-decision.synthetic.json")
        gate["issued_at"] = "whenever"
        self.assertFalse(validator("gate-decision").is_valid(gate))

    def test_schema_does_not_pretend_to_authenticate_issuer(self):
        gate = load(CONTRACTS / "fixtures" / "valid" / "gate-decision.synthetic.json")
        gate["issuer"]["run_id"] = gate["source"]["author_run_id"]
        # JSON Schema checks structure, not identity relationships. gate_eval must reject this.
        self.assertTrue(validator("gate-decision").is_valid(gate))


if __name__ == "__main__":
    unittest.main()

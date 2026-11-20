#!/usr/bin/env python3
"""Offline prerequisite evaluator; this is not a scheduler or an identity service.

Public API: Evaluator(plan, runtime, artifact_loader).gate(id), .task(id), and
dependency_graph(plan). Results use strong Kleene true/false/unknown. Only true
is satisfied. An accepted research task is a completed deliverable, not a claim
that the researched capability works.

The caller supplies an AUTHENTICATED, current coordinator snapshot:
  now: an explicit timezone-aware timestamp;
  task_states[id]: {status, task_spec_sha256, acceptance_ref (if accepted)};
  decisions[gate_id]: the single ACTIVE GateDecision, not an unordered history;
  current_bindings[gate_id]: {source, scope, context} from the current baseline;
  authority_registry.principals[id]: {roles, gate_ids, authority_ref,
                                    valid_from, expires_at, revoked};
  authority_registry.runs[id]: {principal_id, parent_run_id} (complete ancestry).

Scope manifest JSON contains scope_id. Context manifest JSON contains context_id
and a nonempty environment_ids list. Every evidence environment must be in that
CURRENT context; a successful result from another OS/host context is not borrowed.
For a gate with required_subject_tasks, that manifest also has subject_bindings:
[{task_id, task_spec_sha256, head_sha, author_run_ids}]. Each must exactly match
runtime.subject_bindings[task_id] from the trusted ledger. The aggregate author,
its reviewer, and its gate issuer must all be outside every subject-author subtree.

Artifact loader: relative POSIX path -> bytes. Every cited artifact is hashed
here; knowing a hash without having its bytes is insufficient. GateDecision and
ReviewVerdict are also schema-validated. Approval/source/run bindings and open
blocking findings in ReviewVerdict are checked. The upstream review process
remains responsible for the truth and completeness of its observations. This
tool cannot authenticate a caller-supplied registry, obtain live host evidence,
or decide whether an arbitrary test log proves a claim. Synthetic fixtures do
not authorize remote activity or establish a product capability.

Host observations use selected_host_id and host={host_id, attributes,
observed_at, expires_at, manifest_ref}; the manifest JSON equals the host object
without manifest_ref. Authority conditions use authority_grants[name]={gate_id,
granted, valid_from, expires_at, scope, context, issuer, grant_ref}; grant JSON
equals that object without grant_ref, issuer={principal_id, role, authority_ref},
and scope/context must match current_bindings. They also need an authorized
principal (default role product_owner) in the trusted registry. A receipt never
establishes its own trust root.

CLI examples (read-only; no network, subprocesses, database, or remote calls):
  python3 tools/gate_eval.py --gate M0_BASELINE_VERIFIED
  python3 tools/gate_eval.py --gate G --runtime state.json --artifact-root repo
  python3 tools/gate_eval.py --graph
Missing runtime evidence remains unknown. Exit 0 means the requested expression
is true, 2 false, 3 unknown, and 1 an input/usage error. --graph is an explanatory
conditional graph, not an all-required DAG or a numerical critical-path claim.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Callable, Mapping

ROOT = Path(__file__).resolve().parents[1]
TRUE, FALSE, UNKNOWN = "true", "false", "unknown"
ArtifactLoader = Callable[[str], bytes]


@dataclass(frozen=True)
class Result:
    status: str
    blockers: tuple[dict[str, Any], ...] = ()
    evidence_refs: tuple[dict[str, str], ...] = ()
    children: tuple["Result", ...] = field(default=(), repr=False)

    @property
    def satisfied(self) -> bool:
        return self.status == TRUE

    def __bool__(self) -> bool:
        # Avoid Python's default truthiness making Result("unknown") pass a gate.
        return self.satisfied

    def as_dict(self, *, trace: bool = False) -> dict[str, Any]:
        data = {"status": self.status, "satisfied": self.satisfied,
                "blockers": list(self.blockers), "evidence_refs": list(self.evidence_refs)}
        if trace and self.children:
            data["children"] = [child.as_dict(trace=True) for child in self.children]
        return data


def _result(status: str, code: str | None = None, path: str = "",
            detail: str = "", refs: tuple[dict[str, str], ...] = ()) -> Result:
    blockers = () if code is None else ({"code": code, "path": path, "detail": detail},)
    return Result(status, blockers, refs)


def _combine(operator: str, children: list[Result]) -> Result:
    states = [child.status for child in children]
    if operator == "all_of":
        state = FALSE if FALSE in states else UNKNOWN if UNKNOWN in states else TRUE
    else:
        state = TRUE if TRUE in states else UNKNOWN if UNKNOWN in states else FALSE
    refs: dict[tuple[str, str], dict[str, str]] = {}
    for child in children:
        for ref in child.evidence_refs:
            refs[(ref["path"], ref["sha256"])] = ref
    # Unselected alternatives are available in trace, not misreported as blockers
    # after one any_of branch has actually satisfied the requirement.
    unique_blockers = {json.dumps(blocker, sort_keys=True): blocker
                       for child in children for blocker in child.blockers}
    blockers = () if state == TRUE else tuple(unique_blockers.values())
    return Result(state, blockers, tuple(refs.values()), tuple(children))


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo is not None else None
    except ValueError:
        return None


def _safe_path(value: Any) -> bool:
    return (isinstance(value, str) and bool(value) and not value.startswith("/")
            and not any(c in value for c in "\\\x00\r\n:")
            and ".." not in PurePosixPath(value).parts)


def local_artifact_loader(root: Path) -> ArtifactLoader:
    """Resolve artifacts below one root, including symlink escape checks."""
    resolved_root = root.resolve()

    def read(relative_path: str) -> bytes:
        if not _safe_path(relative_path):
            raise ValueError("Unsafe artifact path")
        path = (resolved_root / relative_path).resolve()
        if not path.is_relative_to(resolved_root):
            raise ValueError("Artifact escapes its root")
        return path.read_bytes()

    return read


class Evaluator:
    def __init__(self, plan: Mapping[str, Any], runtime: Mapping[str, Any] | None = None,
                 artifact_loader: ArtifactLoader | None = None,
                 schema_root: Path | None = None):
        self.plan = copy.deepcopy(dict(plan))
        self.runtime = copy.deepcopy(dict(runtime or {}))
        self.loader = artifact_loader
        self.schema_root = schema_root or ROOT / "contracts"
        self.tasks = {task["id"]: task for task in self.plan.get("tasks", [])}
        self.gates = self.plan.get("gate_definitions", {})
        self.policies = self.plan.get("gate_policies", {})
        self.now = _timestamp(self.runtime.get("now"))
        # Cache only within this immutable evaluation snapshot. A new snapshot
        # must construct another Evaluator after a commit/context/authority change.
        self._decision_cache: dict[str, tuple[dict[str, Any] | None, Result]] = {}
        self._artifact_cache: dict[tuple[str, str], tuple[bytes | None, Result]] = {}

    def gate(self, gate_id: str) -> Result:
        return self._gate(gate_id, (), 0)

    def task(self, task_id: str) -> Result:
        """Evaluate prerequisites only, not leases, capacity, or dispatch authority."""
        task = self.tasks.get(task_id)
        if task is None:
            return _result(UNKNOWN, "UNKNOWN_TASK", task_id, "Task is absent from this plan")
        requirements = [{"kind": "task_accepted", "task_id": x}
                        for x in task.get("depends_on", [])]
        requirements += [{"kind": "gate_ref", "gate_id": x}
                         for x in task.get("execution_gates", [])]
        if not requirements:
            return _result(TRUE)
        return self.expression({"all_of": requirements}, path=f"task:{task_id}")

    def expression(self, expr: Any, *, gate_id: str | None = None,
                   path: str = "expression") -> Result:
        return self._eval(expr, gate_id, (), path, 0)

    def _gate(self, gate_id: str, stack: tuple[str, ...], depth: int) -> Result:
        path = f"gate:{gate_id}"
        if gate_id in stack:
            return _result(UNKNOWN, "GATE_CYCLE", path, " -> ".join((*stack, gate_id)))
        if gate_id not in self.gates:
            return _result(UNKNOWN, "UNKNOWN_GATE", path, "Gate is absent from this plan")
        result = self._eval(self.gates[gate_id], gate_id, (*stack, gate_id), path, depth + 1)
        policy = self.policies.get(gate_id, {})
        if policy.get("decision_required") is True:
            _, decision_result = self._decision(gate_id)
            result = _combine("all_of", [result, decision_result])
        return result

    def _eval(self, expr: Any, gate_id: str | None, stack: tuple[str, ...],
              path: str, depth: int) -> Result:
        if depth > 128:
            return _result(UNKNOWN, "EXPRESSION_DEPTH", path, "Expression nesting exceeds limit")
        if not isinstance(expr, dict):
            return _result(UNKNOWN, "INVALID_EXPRESSION", path, "Expected an expression object")
        operators = [key for key in ("all_of", "any_of", "kind") if key in expr]
        if len(operators) != 1:
            return _result(UNKNOWN, "INVALID_EXPRESSION", path, "Exactly one operator is required")
        op = operators[0]
        if op != "kind":
            branches = expr[op]
            if not isinstance(branches, list) or not branches:
                return _result(UNKNOWN, "INVALID_EXPRESSION", path, "Boolean groups must be nonempty lists")
            return _combine(op, [self._eval(child, gate_id, stack, f"{path}/{op}/{index}", depth + 1)
                                 for index, child in enumerate(branches)])
        kind = expr["kind"]
        if kind == "task_accepted":
            return self._task_accepted(expr.get("task_id"), path)
        if kind == "gate_ref":
            target = expr.get("gate_id")
            if not isinstance(target, str):
                return _result(UNKNOWN, "INVALID_GATE_REFERENCE", path)
            return self._gate(target, stack, depth + 1)
        if kind == "host_attribute":
            return self._host_attribute(expr, path)
        if kind == "evidence_condition":
            return self._evidence(expr, gate_id, path)
        if kind == "authority_condition":
            return self._authority_condition(expr, gate_id, path)
        return _result(UNKNOWN, "UNKNOWN_EXPRESSION_KIND", path, str(kind))

    def _artifact(self, ref: Any, path: str) -> tuple[bytes | None, Result]:
        if (not isinstance(ref, dict) or set(ref) != {"path", "sha256"}
                or not _safe_path(ref.get("path"))
                or not isinstance(ref.get("sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", ref["sha256"])):
            return None, _result(UNKNOWN, "INVALID_ARTIFACT_REFERENCE", path)
        key = (ref["path"], ref["sha256"])
        if key in self._artifact_cache:
            return self._artifact_cache[key]
        if self.loader is None:
            return None, _result(UNKNOWN, "ARTIFACT_LOADER_MISSING", path, ref["path"])
        try:
            body = self.loader(ref["path"])
            if not isinstance(body, bytes):
                raise TypeError("artifact_loader must return bytes")
        except (OSError, ValueError, TypeError, KeyError) as error:
            return None, _result(UNKNOWN, "ARTIFACT_UNREADABLE", path, f"{ref['path']}: {type(error).__name__}")
        if hashlib.sha256(body).hexdigest() != ref["sha256"]:
            return None, _result(UNKNOWN, "ARTIFACT_HASH_MISMATCH", path, ref["path"])
        result = _result(TRUE, refs=(copy.deepcopy(ref),))
        self._artifact_cache[key] = body, result
        return body, result

    def _json_artifact(self, ref: Any, path: str) -> tuple[Any, Result]:
        body, result = self._artifact(ref, path)
        if not result.satisfied:
            return None, result
        try:
            return json.loads(body), result
        except (ValueError, UnicodeDecodeError):
            return None, _result(UNKNOWN, "ARTIFACT_NOT_JSON", path)

    def _schema_check(self, data: Any, filename: str, path: str) -> Result:
        try:
            from jsonschema import Draft202012Validator, FormatChecker
        except ImportError:
            return _result(UNKNOWN, "SCHEMA_VALIDATOR_UNAVAILABLE", path, "Install the pinned tooling requirements")
        try:
            schema = json.loads((self.schema_root / filename).read_text(encoding="utf-8"))
            # Shipped schemas are self-contained. Never retrieve remote $refs.
            def external_ref(node: Any) -> bool:
                if isinstance(node, dict):
                    if "$ref" in node and not str(node["$ref"]).startswith("#"):
                        return True
                    return any(external_ref(v) for v in node.values())
                return isinstance(node, list) and any(external_ref(v) for v in node)
            if external_ref(schema):
                return _result(UNKNOWN, "EXTERNAL_SCHEMA_REFERENCE", path)
            errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(data))
        except (OSError, ValueError) as error:
            return _result(UNKNOWN, "SCHEMA_UNAVAILABLE", path, type(error).__name__)
        if errors:
            first = min(errors, key=lambda error: str(list(error.absolute_path)))
            return _result(UNKNOWN, "INVALID_RECEIPT_SCHEMA", path, f"{filename}: {list(first.absolute_path)}: {first.message}")
        return _result(TRUE)

    def _fresh(self, start: Any, end: Any, path: str) -> Result:
        issued, expires = _timestamp(start), _timestamp(end)
        if self.now is None or issued is None or expires is None:
            return _result(UNKNOWN, "TIME_BINDING_MISSING", path, "Timezone-aware now/start/end are required")
        if expires <= issued or issued > self.now:
            return _result(UNKNOWN, "INVALID_TIME_WINDOW", path)
        if expires <= self.now:
            return _result(UNKNOWN, "EXPIRED", path)
        return _result(TRUE)

    def _task_accepted(self, task_id: Any, path: str) -> Result:
        if not isinstance(task_id, str) or task_id not in self.tasks:
            return _result(UNKNOWN, "UNKNOWN_TASK", path, str(task_id))
        state = self.runtime.get("task_states", {}).get(task_id)
        if not isinstance(state, dict):
            return _result(UNKNOWN, "TASK_STATE_MISSING", path, task_id)
        digest = self.tasks[task_id].get("task_spec_sha256")
        if not digest or state.get("task_spec_sha256") != digest:
            return _result(UNKNOWN, "TASK_SPEC_CHANGED", path, task_id)
        status = state.get("status")
        allowed = {"planned", "ready", "running", "submitted", "validating", "merge_queued",
                   "integrated", "accepted", "changes_requested", "blocked", "cancelled"}
        if status not in allowed:
            return _result(UNKNOWN, "TASK_STATE_UNKNOWN", path, str(status))
        if status != "accepted":
            return _result(FALSE, "TASK_NOT_ACCEPTED", path, f"{task_id}: {status}")
        # Acceptance comes from a trusted coordinator record, never a worker's
        # claimed_outcome. Its bound receipt must still exist.
        _, artifact_result = self._artifact(state.get("acceptance_ref"), path + "/acceptance_ref")
        return artifact_result

    def _principal(self, principal_id: Any, role: Any, gate_id: str,
                   authority_ref: Any, path: str, at: datetime | None = None) -> Result:
        record = self.runtime.get("authority_registry", {}).get("principals", {}).get(principal_id)
        if not isinstance(record, dict):
            return _result(UNKNOWN, "UNKNOWN_AUTHORITY", path)
        if (record.get("revoked") is not False or role not in record.get("roles", [])
                or gate_id not in record.get("gate_ids", [])
                or authority_ref != record.get("authority_ref")):
            return _result(UNKNOWN, "UNAUTHORIZED_ISSUER", path)
        freshness = self._fresh(record.get("valid_from"), record.get("expires_at"), path)
        if not freshness.satisfied:
            return freshness
        if at is not None and not (_timestamp(record["valid_from"]) <= at < _timestamp(record["expires_at"])):
            return _result(UNKNOWN, "AUTHORITY_NOT_VALID_AT_ISSUE", path)
        _, proof = self._artifact(authority_ref, path + "/authority_ref")
        return proof

    def _independent(self, reviewer_run_id: Any, principal_id: Any,
                     author_run_id: Any, path: str) -> Result:
        runs = self.runtime.get("authority_registry", {}).get("runs", {})
        author = runs.get(author_run_id) if isinstance(author_run_id, str) else None
        if (not isinstance(author, dict) or not isinstance(author.get("principal_id"), str)
                or not author["principal_id"] or "parent_run_id" not in author):
            return _result(UNKNOWN, "AUTHOR_RUN_UNKNOWN", path)
        if not isinstance(reviewer_run_id, str):
            return _result(UNKNOWN, "REVIEW_RUN_UNKNOWN", path)
        seen: set[str] = set()
        run_id: str | None = reviewer_run_id
        while run_id is not None:
            if run_id == author_run_id:
                return _result(UNKNOWN, "NON_INDEPENDENT_REVIEW", path, "Reviewer belongs to author's run subtree")
            if run_id in seen:
                return _result(UNKNOWN, "RUN_ANCESTRY_CYCLE", path)
            seen.add(run_id)
            run = runs.get(run_id)
            if not isinstance(run, dict) or "parent_run_id" not in run:
                return _result(UNKNOWN, "RUN_ANCESTRY_INCOMPLETE", path, str(run_id))
            if run_id == reviewer_run_id and run.get("principal_id") != principal_id:
                return _result(UNKNOWN, "RUN_PRINCIPAL_MISMATCH", path)
            parent = run["parent_run_id"]
            if parent is not None and not isinstance(parent, str):
                return _result(UNKNOWN, "RUN_ANCESTRY_INCOMPLETE", path)
            run_id = parent
        return _result(TRUE)

    def _review(self, decision: dict[str, Any], path: str) -> Result:
        source = decision["source"]
        review, artifact_result = self._json_artifact(source["review_verdict_ref"], path)
        if not artifact_result.satisfied:
            return artifact_result
        schema = self._schema_check(review, "review-verdict.schema.json", path)
        if not schema.satisfied:
            return schema
        bindings = {"task_id": "task_id", "author_attempt_id": "author_attempt_id",
                    "author_run_id": "author_run_id", "task_spec_sha256": "task_spec_sha256",
                    "contract_sha": "contract_sha", "reviewed_base_sha": "base_sha",
                    "reviewed_head_sha": "head_sha"}
        if any(review[key] != source[target] for key, target in bindings.items()):
            return _result(UNKNOWN, "REVIEW_SOURCE_MISMATCH", path)
        if review["verdict"] != "approved":
            return _result(UNKNOWN if review["verdict"] == "unknown" else FALSE,
                           "REVIEW_NOT_APPROVED", path, review["verdict"])
        if any(finding["blocking"] and finding["status"] == "open" for finding in review["findings"]):
            return _result(FALSE, "OPEN_REVIEW_BLOCKER", path)
        issued = _timestamp(review["issued_at"])
        decision_issued = _timestamp(decision["issued_at"])
        if (issued is None or decision_issued is None or self.now is None
                or issued > self.now or issued > decision_issued):
            return _result(UNKNOWN, "REVIEW_TIME_MISMATCH", path)
        principal_id = review["reviewer_principal_id"]
        principal = self.runtime.get("authority_registry", {}).get("principals", {}).get(principal_id, {})
        checks = [artifact_result,
                  self._principal(principal_id, "reviewer", decision["gate_id"], principal.get("authority_ref"), path, issued),
                  self._independent(review["reviewer_run_id"], principal_id, source["author_run_id"], path)]
        references = [review["worker_result_ref"], review["reviewer_manifest_ref"], *review["evidence_refs"]]
        references.extend(ref for finding in review["findings"] for ref in finding["evidence_refs"])
        for index, ref in enumerate(references):
            _, proof = self._artifact(ref, f"{path}/references/{index}")
            checks.append(proof)
        return _combine("all_of", checks)

    def _subject_independence(self, decision: dict[str, Any], manifest: Any, path: str) -> Result:
        """Bind aggregate-gate subjects; do not infer authors from a single source."""
        required = self.policies.get(decision["gate_id"], {}).get("required_subject_tasks", [])
        if not required:
            return _result(TRUE)
        if (not isinstance(required, list) or any(not isinstance(task, str) for task in required)
                or len(required) != len(set(required))):
            return _result(UNKNOWN, "INVALID_SUBJECT_POLICY", path)
        records = manifest.get("subject_bindings") if isinstance(manifest, dict) else None
        if not isinstance(records, list):
            return _result(UNKNOWN, "SUBJECT_BINDINGS_MISSING", path)
        by_task = {}
        for record in records:
            if (not isinstance(record, dict)
                    or set(record) != {"task_id", "task_spec_sha256", "head_sha", "author_run_ids"}
                    or not isinstance(record["task_id"], str)
                    or not isinstance(record["head_sha"], str)
                    or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", record["head_sha"])
                    or not isinstance(record["author_run_ids"], list) or not record["author_run_ids"]
                    or any(not isinstance(run, str) or not run for run in record["author_run_ids"])
                    or len(record["author_run_ids"]) != len(set(record["author_run_ids"]))):
                return _result(UNKNOWN, "INVALID_SUBJECT_BINDING", path)
            if record["task_id"] in by_task:
                return _result(UNKNOWN, "DUPLICATE_SUBJECT_BINDING", path, record["task_id"])
            by_task[record["task_id"]] = record
        if not set(required).issubset(by_task):
            return _result(UNKNOWN, "SUBJECT_BINDINGS_MISSING", path, ",".join(sorted(set(required) - set(by_task))))
        review, review_proof = self._json_artifact(decision["source"]["review_verdict_ref"], path + "/review")
        if not review_proof.satisfied or not isinstance(review, dict):
            return _result(UNKNOWN, "SUBJECT_REVIEW_UNAVAILABLE", path)
        runs = self.runtime.get("authority_registry", {}).get("runs", {})
        aggregate_run = decision["source"]["author_run_id"]
        aggregate_record = runs.get(aggregate_run)
        aggregate_principal = aggregate_record.get("principal_id") if isinstance(aggregate_record, dict) else None
        actors = [(aggregate_run, aggregate_principal),
                  (review.get("reviewer_run_id"), review.get("reviewer_principal_id")),
                  (decision["issuer"]["run_id"], decision["issuer"]["principal_id"])]
        if any(not isinstance(run, str) or not isinstance(principal, str) or not principal for run, principal in actors):
            return _result(UNKNOWN, "SUBJECT_REVIEWER_IDENTITY_MISSING", path)
        current_records = self.runtime.get("subject_bindings", {})
        if not isinstance(current_records, dict):
            return _result(UNKNOWN, "SUBJECT_BINDINGS_MISSING", path)
        checks = [review_proof]
        for task, record in by_task.items():
            subject_path = f"{path}/{task}"
            if current_records.get(task) != record:
                checks.append(_result(UNKNOWN, "SUBJECT_BINDING_MISMATCH", subject_path))
                continue
            if task not in self.tasks or record["task_spec_sha256"] != self.tasks[task].get("task_spec_sha256"):
                checks.append(_result(UNKNOWN, "SUBJECT_TASK_SPEC_CHANGED", subject_path))
                continue
            checks.append(self._task_accepted(task, subject_path))
            for subject_author in record["author_run_ids"]:
                for actor_run, actor_principal in set(actors):
                    checks.append(self._independent(actor_run, actor_principal, subject_author, subject_path + "/" + actor_run))
        return _combine("all_of", checks)

    def _decision(self, gate_id: str) -> tuple[dict[str, Any] | None, Result]:
        if gate_id not in self._decision_cache:
            self._decision_cache[gate_id] = self._verify_decision(gate_id)
        return self._decision_cache[gate_id]

    def _verify_decision(self, gate_id: str) -> tuple[dict[str, Any] | None, Result]:
        path = f"gate:{gate_id}/decision"
        policy = self.policies.get(gate_id, {})
        if (policy.get("decision_required") is not True
                or policy.get("require_independent_run") is not True
                or not {"source", "scope", "context"}.issubset(set(policy.get("required_bindings", [])))):
            return None, _result(UNKNOWN, "GATE_POLICY_INCOMPLETE", path)
        decision = self.runtime.get("decisions", {}).get(gate_id)
        if not isinstance(decision, dict):
            return None, _result(UNKNOWN, "GATE_DECISION_MISSING", path)
        shape = self._schema_check(decision, "gate-decision.schema.json", path)
        if not shape.satisfied:
            return None, shape
        if decision["gate_id"] != gate_id:
            return None, _result(UNKNOWN, "DECISION_GATE_MISMATCH", path)
        current = self.runtime.get("current_bindings", {}).get(gate_id)
        if not isinstance(current, dict):
            return None, _result(UNKNOWN, "CURRENT_BINDING_MISSING", path)
        for key in ("source", "scope", "context"):
            if current.get(key) != decision[key]:
                return None, _result(UNKNOWN, key.upper() + "_BINDING_MISMATCH", path)
        source, issuer = decision["source"], decision["issuer"]
        if source["task_id"] not in policy.get("permitted_source_tasks", []):
            return None, _result(UNKNOWN, "UNAUTHORIZED_SOURCE_TASK", path)
        if issuer["role"] not in policy.get("issuer_roles", []):
            return None, _result(UNKNOWN, "UNAUTHORIZED_ISSUER_ROLE", path)
        planned_source = self.tasks.get(source["task_id"])
        if planned_source is None or planned_source.get("task_spec_sha256") != source["task_spec_sha256"]:
            return None, _result(UNKNOWN, "SOURCE_TASK_SPEC_CHANGED", path)
        checks = [self._task_accepted(source["task_id"], path + "/source_task"),
                  self._fresh(decision["issued_at"], decision["expires_at"], path),
                  self._principal(issuer["principal_id"], issuer["role"], gate_id, issuer["authority_ref"], path,
                                  _timestamp(decision["issued_at"])),
                  self._independent(issuer["run_id"], issuer["principal_id"], source["author_run_id"], path)]
        context_manifest = None
        for key in ("scope", "context"):
            manifest, proof = self._json_artifact(decision[key]["manifest_ref"], f"{path}/{key}")
            checks.append(proof)
            if proof.satisfied:
                if not isinstance(manifest, dict) or manifest.get(key + "_id") != decision[key][key + "_id"]:
                    checks.append(_result(UNKNOWN, key.upper() + "_MANIFEST_ID_MISMATCH", path))
                elif key == "context":
                    context_manifest = manifest
        environments = context_manifest.get("environment_ids") if isinstance(context_manifest, dict) else None
        if (not isinstance(environments, list) or not environments
                or any(not isinstance(item, str) or not item for item in environments)):
            checks.append(_result(UNKNOWN, "CONTEXT_ENVIRONMENTS_MISSING", path))
            environments = []
        checks.append(self._review(decision, path + "/review"))
        checks.append(self._subject_independence(decision, context_manifest, path + "/subjects"))
        names: set[str] = set()
        for index, evidence in enumerate(decision["evidence"]):
            if evidence["condition_name"] in names:
                checks.append(_result(UNKNOWN, "DUPLICATE_EVIDENCE_CONDITION", path, evidence["condition_name"]))
            names.add(evidence["condition_name"])
            if evidence["environment_id"] not in environments:
                checks.append(_result(UNKNOWN, "EVIDENCE_ENVIRONMENT_MISMATCH", path, evidence["environment_id"]))
            _, proof = self._artifact(evidence["artifact"], f"{path}/evidence/{index}")
            checks.append(proof)
        verification = _combine("all_of", checks)
        if not verification.satisfied:
            return None, verification
        verdict = decision["decision"]
        if verdict != "passed":
            status = UNKNOWN if verdict == "unknown" else FALSE
            return decision, _combine("all_of", [verification, _result(status, "GATE_" + verdict.upper(), path)])
        return decision, verification

    def _evidence(self, expr: dict[str, Any], gate_id: str | None, path: str) -> Result:
        if gate_id is None or not isinstance(expr.get("name"), str):
            return _result(UNKNOWN, "EVIDENCE_CONTEXT_MISSING", path)
        decision, proof = self._decision(gate_id)
        if not proof.satisfied:
            return proof
        matching = [item for item in decision["evidence"] if item["condition_name"] == expr["name"]]
        if len(matching) != 1:
            return _result(UNKNOWN, "REQUIRED_EVIDENCE_MISSING", path, expr["name"])
        outcome = matching[0]["outcome"]
        source_map = self.policies.get(gate_id, {}).get("condition_source_tasks", {})
        if expr["name"] in source_map and decision["source"]["task_id"] not in source_map[expr["name"]]:
            return _result(UNKNOWN, "EVIDENCE_SOURCE_TASK_MISMATCH", path, expr["name"])
        if outcome != "passed":
            return _result(FALSE if outcome == "failed" else UNKNOWN, "EVIDENCE_" + outcome.upper(), path)
        return proof

    def _host_attribute(self, expr: dict[str, Any], path: str) -> Result:
        host = self.runtime.get("host")
        if (not isinstance(host, dict) or not isinstance(host.get("host_id"), str)
                or not host["host_id"] or host["host_id"] != self.runtime.get("selected_host_id")):
            return _result(UNKNOWN, "HOST_CONTEXT_MISSING", path)
        manifest, proof = self._json_artifact(host.get("manifest_ref"), path + "/host")
        if not proof.satisfied:
            return proof
        if manifest != {k: v for k, v in host.items() if k != "manifest_ref"}:
            return _result(UNKNOWN, "HOST_MANIFEST_MISMATCH", path)
        freshness = self._fresh(host.get("observed_at"), host.get("expires_at"), path)
        if not freshness.satisfied:
            return freshness
        attr = expr.get("attribute")
        if not isinstance(attr, str) or attr not in host.get("attributes", {}) or "equals" not in expr:
            return _result(UNKNOWN, "HOST_ATTRIBUTE_MISSING", path, str(attr))
        actual, expected = host["attributes"][attr], expr["equals"]
        if actual is None or expected is None:
            return _result(UNKNOWN, "HOST_ATTRIBUTE_MISSING", path, attr)
        # JSON true must not compare equal to numeric 1 through Python coercion.
        if type(actual) is not type(expected) or actual != expected:
            return _result(FALSE, "HOST_ATTRIBUTE_MISMATCH", path, attr, proof.evidence_refs)
        return proof

    def _authority_condition(self, expr: dict[str, Any], gate_id: str | None, path: str) -> Result:
        name = expr.get("name")
        if gate_id is None or not isinstance(name, str):
            return _result(UNKNOWN, "AUTHORITY_CONTEXT_MISSING", path)
        grant = self.runtime.get("authority_grants", {}).get(name)
        if not isinstance(grant, dict) or grant.get("gate_id") != gate_id:
            return _result(UNKNOWN, "AUTHORITY_GRANT_MISSING", path)
        content, proof = self._json_artifact(grant.get("grant_ref"), path + "/grant")
        if not proof.satisfied:
            return proof
        if content != {k: v for k, v in grant.items() if k != "grant_ref"}:
            return _result(UNKNOWN, "AUTHORITY_GRANT_MISMATCH", path)
        binding = self.runtime.get("current_bindings", {}).get(gate_id, {})
        if any(not grant.get(key) or grant.get(key) != binding.get(key) for key in ("scope", "context")):
            return _result(UNKNOWN, "AUTHORITY_BINDING_MISMATCH", path)
        issuer = grant.get("issuer", {})
        allowed_roles = self.policies.get(gate_id, {}).get("authorization_roles", ["product_owner"])
        if issuer.get("role") not in allowed_roles:
            return _result(UNKNOWN, "UNAUTHORIZED_GRANT_ROLE", path)
        checks = [proof, self._fresh(grant.get("valid_from"), grant.get("expires_at"), path),
                  self._principal(issuer.get("principal_id"), issuer.get("role"), gate_id,
                                  issuer.get("authority_ref"), path, _timestamp(grant.get("valid_from")))]
        for key in ("scope", "context"):
            _, artifact = self._artifact(grant[key].get("manifest_ref"), f"{path}/{key}")
            checks.append(artifact)
        validity = _combine("all_of", checks)
        if not validity.satisfied:
            return validity
        if grant.get("granted") is True:
            return validity
        return _result(FALSE if grant.get("granted") is False else UNKNOWN, "AUTHORITY_NOT_GRANTED", path)


def dependency_graph(plan: Mapping[str, Any]) -> dict[str, Any]:
    """Preserve Boolean topology. Reference edges are for discovery, not ANDing."""
    tasks = {task["id"]: task for task in plan.get("tasks", [])}
    gates = plan.get("gate_definitions", {})
    requirements = {
        task_id: {"all_of": [*({"kind": "task_accepted", "task_id": dep} for dep in task.get("depends_on", [])),
                             *({"kind": "gate_ref", "gate_id": gate} for gate in task.get("execution_gates", []))]}
        for task_id, task in tasks.items()
    }
    edges, errors = [], []

    def walk(node: Any, owner: str, path: str) -> None:
        if not isinstance(node, dict):
            errors.append({"code": "INVALID_EXPRESSION", "path": path})
            return
        if len([key for key in ("all_of", "any_of", "kind") if key in node]) != 1:
            errors.append({"code": "INVALID_EXPRESSION", "path": path})
            return
        for op in ("all_of", "any_of"):
            if op in node:
                if not isinstance(node[op], list):
                    errors.append({"code": "INVALID_EXPRESSION", "path": path})
                    return
                for index, child in enumerate(node[op]):
                    walk(child, owner, f"{path}/{op}/{index}")
                return
        kind = node.get("kind")
        if kind in ("task_accepted", "gate_ref"):
            key, prefix, catalog = ("task_id", "task:", tasks) if kind == "task_accepted" else ("gate_id", "gate:", gates)
            target = node.get(key)
            if not isinstance(target, str) or target not in catalog:
                errors.append({"code": "MISSING_REFERENCE", "path": path, "reference": target})
                return
            edges.append({"from": owner, "to": prefix + target, "expression_path": path})
        elif kind not in ("host_attribute", "evidence_condition", "authority_condition"):
            errors.append({"code": "UNKNOWN_EXPRESSION_KIND", "path": path})

    for task_id, expression in requirements.items():
        walk(expression, "task:" + task_id, "task_requirements/" + task_id)
    for gate_id, expression in gates.items():
        walk(expression, "gate:" + gate_id, "gate_requirements/" + gate_id)
    adjacency: dict[str, list[str]] = {}
    for edge in edges:
        adjacency.setdefault(edge["from"], []).append(edge["to"])
    visited, active = set(), []
    cycles: list[list[str]] = []

    def visit(node: str) -> None:
        if node in active:
            cycles.append(active[active.index(node):] + [node])
            return
        if node in visited:
            return
        active.append(node)
        for target in adjacency.get(node, []):
            visit(target)
        active.pop()
        visited.add(node)

    for node in adjacency:
        visit(node)
    return {"format": "conditional_dependency_graph.v1", "task_requirements": requirements,
            "gate_requirements": copy.deepcopy(gates), "reference_edges": edges,
            "conservative_cycles": cycles, "errors": errors,
            "interpretation": "Keep all_of/any_of when evaluating or scheduling. Reference edges include alternatives; they are not all-required dependencies."}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=ROOT / "coordination/tasks.json")
    parser.add_argument("--runtime", type=Path)
    parser.add_argument("--artifact-root", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--gate")
    mode.add_argument("--task")
    mode.add_argument("--graph", action="store_true")
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args(argv)
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        if args.graph:
            graph = dependency_graph(plan)
            print(json.dumps(graph, ensure_ascii=False, indent=2))
            return 1 if graph["errors"] or graph["conservative_cycles"] else 0
        runtime = json.loads(args.runtime.read_text(encoding="utf-8")) if args.runtime else {}
        loader = local_artifact_loader(args.artifact_root) if args.artifact_root else None
        evaluator = Evaluator(plan, runtime, loader)
        result = evaluator.gate(args.gate) if args.gate else evaluator.task(args.task)
        print(json.dumps(result.as_dict(trace=args.trace), ensure_ascii=False, indent=2))
        return {TRUE: 0, FALSE: 2, UNKNOWN: 3}[result.status]
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({"status": "input_error", "error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

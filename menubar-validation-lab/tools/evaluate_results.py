#!/usr/bin/env python3
"""Evaluate collected menu-bar experiments; this is not a Mac UI test runner.

Exit 0: in-scope evidence and matched baseline passed.
Exit 2: environment blocked, incomplete, or not ready for comparison.
Exit 1: invalid evidence/input or a release-blocking failure.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import sys

SCHEMA_VERSION = "1.0"
STATUSES = {"not_run", "passed", "failed", "blocked", "unsupported", "not_applicable", "unknown"}
EVIDENCE_KINDS = {"machine_observation", "machine_verified", "operator_attested"}
REVISION_KINDS = {"git_commit": 40, "source_sha256": 64}
COMPARISON_KEYS = (
    "machine_id", "os_version", "os_build", "architecture", "screen_topology",
    "menu_bar_auto_hide", "separate_spaces", "permission_profile", "app_inventory",
    "fixture_bundle_id", "fixture_item_ids", "fixture_revision",
)


def digest_json(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("missing timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed


def revision_valid(value):
    if not isinstance(value, dict):
        return False
    size = REVISION_KINDS.get(value.get("kind"))
    return bool(size and re.fullmatch(r"[0-9a-f]{" + str(size) + "}", str(value.get("value", ""))))


def file_hash(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def environment_issues(env, fixture_contract=None):
    issues = []
    for key in ("machine_id", "os_version", "os_build", "architecture",
                "permission_profile", "fixture_bundle_id"):
        if not isinstance(env.get(key), str) or not env[key].strip():
            issues.append("environment." + key + " is required for a Mac run")
    for key in ("menu_bar_auto_hide", "separate_spaces"):
        if not isinstance(env.get(key), bool):
            issues.append("environment." + key + " must be boolean")
    for key in ("app_inventory", "fixture_item_ids"):
        value = env.get(key)
        if not isinstance(value, list) or not value or not all(isinstance(x, str) and x for x in value):
            issues.append("environment." + key + " must be a nonempty string list")
    if isinstance(fixture_contract, dict):
        if env.get("fixture_bundle_id") != fixture_contract.get("bundle_id"):
            issues.append("environment.fixture_bundle_id does not match the protocol fixture")
        item_ids = env.get("fixture_item_ids")
        expected_ids = fixture_contract.get("item_ids", [])
        if (not isinstance(item_ids, list) or
                sorted(str(x) for x in item_ids) != sorted(str(x) for x in expected_ids)):
            issues.append("environment.fixture_item_ids do not match the protocol fixture")
    if not revision_valid(env.get("fixture_revision")):
        issues.append("environment.fixture_revision must pin source or commit")
    screens = env.get("screen_topology")
    if not isinstance(screens, list) or not screens:
        issues.append("environment.screen_topology is required")
    else:
        ids = []
        for screen in screens:
            if not isinstance(screen, dict):
                issues.append("screen entry must be an object")
                continue
            ids.append(screen.get("id"))
            frame = screen.get("frame_points")
            if not isinstance(screen.get("id"), str) or not screen.get("id"):
                issues.append("screen requires an anonymous id")
            if not isinstance(screen.get("has_notch"), bool):
                issues.append("screen.has_notch must be boolean")
            scale = screen.get("scale")
            if (isinstance(scale, bool) or not isinstance(scale, (int, float)) or
                    not math.isfinite(scale) or scale <= 0):
                issues.append("screen.scale must be finite and positive")
            if (not isinstance(frame, list) or len(frame) != 4 or
                    any(isinstance(x, bool) or not isinstance(x, (int, float)) or
                        not math.isfinite(x) for x in frame) or
                    frame[2] <= 0 or frame[3] <= 0):
                issues.append("screen.frame_points must contain finite [x, y, positive width, positive height]")
        if len(set(str(x) for x in ids)) != len(ids):
            issues.append("duplicate screen ids")
    return issues


def effective_context(env, item):
    """A variant context is an explicit patch, never a replacement that drops constraints."""
    patch = item.get("context", {})
    if not isinstance(patch, dict):
        raise ValueError("variant context must be an object")
    return {**env, **patch}


def structured_failures(evidence):
    """Notice submitted contradictions even if their result was relabelled unsupported.

    This is not natural-language analysis or artifact replay. A failure report does
    not need an intact artifact to block release; it still needs investigation.
    """
    if not isinstance(evidence, list):
        return []
    failures = []
    for entry in evidence:
        if not isinstance(entry, dict) or entry.get("kind") != "machine_verified":
            continue
        if (entry.get("matched") is False or
                ("expected" in entry and "observed" in entry and
                 digest_json(entry["expected"]) != digest_json(entry["observed"]))):
            failures.append("Submitted machine assertion reports failure: " + str(entry.get("id", "unnamed")))
    return failures


def coverage_issues(requirements, context):
    screens = context.get("screen_topology", [])
    if not isinstance(screens, list):
        return ["variant screen_topology is not a list"]
    issues = []
    if len(screens) < requirements.get("min_displays", 0):
        issues.append("variant requires more connected displays")
    if requirements.get("has_notch") and not any(s.get("has_notch") is True for s in screens if isinstance(s, dict)):
        issues.append("variant requires a notched display")
    if requirements.get("mixed_scale") and len({s.get("scale") for s in screens if isinstance(s, dict)}) < 2:
        issues.append("variant requires different display scale factors")
    if requirements.get("vertical_arrangement"):
        ys = {s.get("frame_points", [None, None])[1] for s in screens
              if isinstance(s, dict) and isinstance(s.get("frame_points"), list)
              and len(s["frame_points"]) == 4}
        if len(ys) < 2:
            issues.append("variant requires vertically offset displays")
    if requirements.get("permission_profile") and context.get("permission_profile") != requirements["permission_profile"]:
        issues.append("variant permission profile does not match required profile")
    return issues


def evidence_issues(evidence, run, case, variant_id, base_dir, seen_ids):
    errors = []
    if not isinstance(evidence, list):
        return ["evidence must be a list"], Counter()
    kinds = Counter()
    for entry in evidence:
        if not isinstance(entry, dict):
            errors.append("evidence entry must be an object")
            continue
        kind = entry.get("kind")
        if kind not in EVIDENCE_KINDS:
            errors.append("unknown evidence kind")
            continue
        valid = True
        def error(message):
            nonlocal valid
            valid = False
            errors.append(message)
        if entry.get("run_id") != run.get("run_id") or entry.get("case_id") != case["id"] or entry.get("variant_id") != variant_id:
            error("evidence is not bound to this run/case/variant")
        evidence_id = entry.get("id")
        if not isinstance(evidence_id, str) or not evidence_id or evidence_id in seen_ids:
            error("missing or reused evidence id")
        else:
            seen_ids.add(evidence_id)
        try:
            when = timestamp(entry.get("observed_at_utc"))
            if not timestamp(run.get("started_at_utc")) <= when <= timestamp(run.get("finished_at_utc")):
                error("evidence timestamp is outside this run")
        except (ValueError, TypeError):
            error("invalid evidence or run timestamp")
        raw = entry.get("artifact")
        if not isinstance(raw, str) or not raw or Path(raw).is_absolute() or ".." in Path(raw).parts:
            error("artifact must be a relative path inside the run directory")
        else:
            target = (base_dir / raw).resolve()
            try:
                target.relative_to(base_dir.resolve())
            except ValueError:
                error("artifact resolves outside the run directory")
            else:
                if not target.is_file():
                    error("evidence artifact does not exist: " + raw)
                elif not re.fullmatch(r"[0-9a-f]{64}", str(entry.get("sha256", ""))) or file_hash(target) != entry["sha256"]:
                    error("evidence artifact hash mismatch: " + raw)
        if kind == "operator_attested":
            if not entry.get("observer") or not entry.get("statement"):
                error("operator attestation needs observer and statement")
        elif kind == "machine_verified":
            if entry.get("assertion_id") not in case.get("machine_assertions", []):
                error("machine assertion is not declared for this case")
            if not entry.get("verifier") or not revision_valid(entry.get("verifier_revision")):
                error("machine verification needs a pinned verifier")
            if entry.get("matched") is not True or "expected" not in entry or "observed" not in entry:
                error("machine verification must include a successful expected/observed comparison")
            elif digest_json(entry["expected"]) != digest_json(entry["observed"]):
                error("machine assertion expected and observed values differ")
        if valid:
            kinds[kind] += 1
    return errors, kinds


def evaluate_run(run, protocol, base_dir, baseline=None, baseline_dir=None):
    """Return a conservative evidence report. No UI claims are made by this function."""
    base_dir = Path(base_dir)
    findings = []
    counts = Counter()
    evidence_counts = Counter()
    by_case = []
    exclusions = []
    protocol_cases = protocol.get("cases", []) if isinstance(protocol, dict) else None
    if not isinstance(run, dict) or not isinstance(protocol_cases, list):
        return {"release_verdict": "invalid", "suite_verdict": "invalid",
                "blocking_findings": [{"code": "invalid_shape", "message": "run/protocol has invalid shape"}]}
    def add(code, message, case_id=None, variant_id=None):
        row = {"code": code, "message": message}
        if case_id:
            row["case_id"] = case_id
        if variant_id:
            row["variant_id"] = variant_id
        findings.append(row)

    if run.get("schema_version") != SCHEMA_VERSION:
        add("invalid_metadata", "unsupported run schema_version")
    if run.get("protocol_id") != protocol.get("protocol_id") or run.get("protocol_sha256") != digest_json(protocol):
        add("protocol_mismatch", "run does not pin this exact protocol content")
    role = run.get("run_role")
    if role not in {"baseline", "candidate"}:
        add("invalid_metadata", "run_role must be baseline or candidate")
    for key in ("run_id", "comparison_group_id"):
        if not isinstance(run.get(key), str) or not run[key].strip():
            add("invalid_metadata", key + " is required")
    env = run.get("environment", {})
    if not isinstance(env, dict):
        add("invalid_metadata", "environment must be an object")
        env = {}
    actual_mac = env.get("platform") == "macOS" and run.get("run_kind") == "mac_runtime"
    if not actual_mac:
        add("environment_unavailable", "No macOS runtime evidence: UI/backend behaviour remains untested")
    else:
        for problem in environment_issues(env, protocol.get("fixture_contract")):
            add("invalid_environment", problem)
        try:
            if timestamp(run.get("finished_at_utc")) < timestamp(run.get("started_at_utc")):
                add("invalid_metadata", "finished_at precedes started_at")
        except (TypeError, ValueError):
            add("invalid_metadata", "Mac runs need valid timezone-aware start/end timestamps")
        backend = run.get("backend", {})
        if not isinstance(backend, dict) or not backend.get("id"):
            add("invalid_metadata", "backend identity is missing")
        elif role == "candidate" and (not revision_valid(backend.get("revision")) or
                not re.fullmatch(r"[0-9a-f]{64}", str(backend.get("configuration_sha256", "")))):
            add("invalid_metadata", "candidate needs pinned source and configuration SHA-256")
        elif role == "candidate" and (not isinstance(backend.get("strategy_id"), str) or
                                       not backend["strategy_id"].strip()):
            add("invalid_metadata", "candidate needs a nonempty strategy_id")
        elif role == "baseline" and backend.get("id") != "none":
            add("invalid_metadata", "baseline must identify backend none")

    claimed = run.get("claimed_capabilities", [])
    known_capabilities = {c.get("capability") for c in protocol_cases}
    if not isinstance(claimed, list) or any(x not in known_capabilities for x in claimed):
        add("invalid_metadata", "claimed_capabilities contains unknown values")
        claimed = []
    if actual_mac and not claimed:
        add("invalid_metadata", "Mac acceptance needs a nonempty declared capability scope")
    raw_results = run.get("cases", [])
    if not isinstance(raw_results, list):
        add("invalid_shape", "cases must be a list")
        raw_results = []
    result_map = {}
    for row in raw_results:
        if not isinstance(row, dict) or row.get("case_id") in result_map:
            add("invalid_shape", "case record is invalid or duplicated")
            continue
        result_map[row.get("case_id")] = row
    unknown_cases = set(result_map) - {c["id"] for c in protocol_cases}
    if unknown_cases:
        add("invalid_shape", "unknown cases: " + ", ".join(str(x) for x in sorted(unknown_cases, key=str)))
    seen_ids = set()
    required_pending = 0
    suite_pending = 0
    applicable_total = 0
    passed_total = 0
    for case in protocol_cases:
        applies = role in case.get("applies_to", ["candidate"])
        required = applies and (case.get("mandatory_for_candidate") or case["capability"] in claimed)
        row = result_map.get(case["id"], {})
        raw_variants = row.get("coverage", [])
        if not isinstance(raw_variants, list):
            add("invalid_shape", "coverage must be a list", case["id"])
            raw_variants = []
        variants = {}
        for item in raw_variants:
            if not isinstance(item, dict) or item.get("variant_id") in variants:
                add("invalid_shape", "invalid or duplicate variant record", case["id"])
                continue
            variants[item.get("variant_id")] = item
        expected_ids = {v["id"] for v in case["required_coverage"]}
        if set(variants) - expected_ids:
            add("invalid_shape", "unknown variant", case["id"])
        case_rows = []
        for spec in case["required_coverage"]:
            item = variants.get(spec["id"], {})
            state = item.get("status", "not_run")
            if state not in STATUSES:
                add("invalid_shape", "unknown status", case["id"], spec["id"])
                state = "unknown"
            for problem in structured_failures(item.get("evidence", [])):
                add("release_blocker" if case.get("release_blocker") else "reported_failure",
                    problem, case["id"], spec["id"])
            if not applies:
                if state not in {"not_applicable", "not_run"}:
                    add("invalid_claim", "case does not apply to this run role", case["id"], spec["id"])
                case_rows.append({"variant_id": spec["id"], "status": "not_applicable", "in_scope": False})
                counts["not_applicable"] += 1
                continue
            applicable_total += 1
            counts[state] += 1
            valid_pass = False
            if state == "passed":
                if not actual_mac:
                    add("invalid_claim", "cannot claim Mac behaviour passed in a preflight/non-Mac run", case["id"], spec["id"])
                if not item.get("observations"):
                    add("missing_evidence", "passed result needs concrete observations", case["id"], spec["id"])
                problems, kinds = evidence_issues(item.get("evidence", []), run, case, spec["id"], base_dir, seen_ids)
                evidence_counts.update(kinds)
                try:
                    context = effective_context(env, item)
                    problems += environment_issues(context, protocol.get("fixture_contract"))
                    problems += coverage_issues(spec.get("requirements", {}), context)
                except ValueError as exc:
                    problems.append(str(exc))
                for problem in problems:
                    add("invalid_evidence", problem, case["id"], spec["id"])
                # Raw fixture logs and narrow machine assertions do not prove complete UI behaviour.
                if kinds["operator_attested"] < 1:
                    add("missing_evidence", "UI acceptance requires explicit operator_attested evidence", case["id"], spec["id"])
                valid_pass = actual_mac and not problems and kinds["operator_attested"] >= 1 and bool(item.get("observations"))
            elif state in {"unsupported", "blocked", "not_applicable", "unknown"} and not item.get("reason"):
                add("invalid_claim", "non-pass status needs an explanation", case["id"], spec["id"])
            if state == "not_applicable":
                add("invalid_claim", "missing hardware/permission is blocked, not not_applicable", case["id"], spec["id"])
            if state == "failed":
                add("release_blocker" if case.get("release_blocker") else "reported_failure",
                    item.get("observations") or "Failure reported; evidence should be attached", case["id"], spec["id"])
            if valid_pass:
                passed_total += 1
            else:
                suite_pending += 1
                if required:
                    required_pending += 1
                elif state in {"unsupported", "not_run", "blocked", "unknown"}:
                    exclusions.append({"case_id": case["id"], "variant_id": spec["id"], "status": state,
                                       "capability": case["capability"], "reason": item.get("reason", "Outside declared capability scope")})
            case_rows.append({"variant_id": spec["id"], "status": state, "accepted_pass": valid_pass, "in_scope": required})
        by_case.append({"case_id": case["id"], "capability": case["capability"], "coverage": case_rows})

    comparison = "not_required" if role == "baseline" else "pending"
    if role == "candidate" and actual_mac:
        if baseline is not None and not isinstance(baseline, dict):
            add("invalid_metadata", "baseline must be an object")
            baseline = None
        if baseline is None:
            add("missing_baseline", "candidate comparison requires a collected and passed no-manager baseline")
        else:
            if baseline.get("run_role") != "baseline":
                add("comparison_mismatch", "provided baseline is not a baseline run")
            baseline_report = evaluate_run(baseline, protocol, baseline_dir or base_dir)
            baseline_env = baseline.get("environment", {})
            if not isinstance(baseline_env, dict):
                baseline_env = {}
            mismatches = [k for k in COMPARISON_KEYS if digest_json(env.get(k)) != digest_json(baseline_env.get(k))]
            if run.get("comparison_group_id") != baseline.get("comparison_group_id"):
                mismatches.append("comparison_group_id")
            if run.get("baseline_run_id") != baseline.get("run_id"):
                mismatches.append("baseline_run_id")
            needed_baseline_caps = {c["capability"] for c in protocol_cases
                                    if "baseline" in c.get("applies_to", []) and c["capability"] in claimed}
            if not needed_baseline_caps.issubset(set(baseline.get("claimed_capabilities", []))):
                mismatches.append("baseline_capability_scope")
            baseline_rows = {row["case_id"]: row for row in baseline_report.get("cases", [])}
            baseline_inputs = {row["case_id"]: row for row in baseline.get("cases", []) if isinstance(row, dict)}
            missing_baseline_variants = []
            for case, case_report in zip(protocol_cases, by_case):
                if "baseline" not in case.get("applies_to", []):
                    continue
                accepted_baseline = {v["variant_id"] for v in baseline_rows.get(case["id"], {}).get("coverage", [])
                                     if v.get("accepted_pass")}
                baseline_variants = {v["variant_id"]: v for v in baseline_inputs.get(case["id"], {}).get("coverage", [])
                                     if isinstance(v, dict) and "variant_id" in v}
                candidate_variants = {v["variant_id"]: v for v in result_map.get(case["id"], {}).get("coverage", [])
                                      if isinstance(v, dict) and "variant_id" in v}
                for item_report in case_report["coverage"]:
                    if not item_report.get("accepted_pass"):
                        continue
                    variant_id = item_report["variant_id"]
                    if variant_id not in accepted_baseline:
                        missing_baseline_variants.append(case["id"] + "/" + variant_id)
                        continue
                    left = effective_context(env, candidate_variants[variant_id])
                    right = effective_context(baseline_env, baseline_variants[variant_id])
                    differing = [k for k in COMPARISON_KEYS if digest_json(left.get(k)) != digest_json(right.get(k))]
                    if differing:
                        mismatches.append(case["id"] + "/" + variant_id + ":" + ",".join(differing))
            if mismatches:
                add("comparison_mismatch", "baseline conditions differ: " + ", ".join(mismatches))
            if baseline_report.get("release_verdict") != "passed":
                add("baseline_incomplete", "baseline has not passed its required observations")
            if missing_baseline_variants:
                add("baseline_incomplete", "matching baseline variants have not passed: " + ", ".join(missing_baseline_variants))
            if not mismatches and not missing_baseline_variants and baseline_report.get("release_verdict") == "passed":
                comparison = "matched"

    codes = {x["code"] for x in findings}
    invalid_codes = {"invalid_metadata", "invalid_environment", "invalid_shape", "protocol_mismatch",
                     "invalid_claim", "invalid_evidence", "missing_evidence", "comparison_mismatch"}
    if codes & invalid_codes:
        verdict = "invalid"
    elif "environment_unavailable" in codes:
        verdict = "blocked_by_environment"
    elif "release_blocker" in codes or "reported_failure" in codes:
        verdict = "blocked"
    elif required_pending:
        verdict = "incomplete"
    elif role == "candidate" and comparison != "matched":
        verdict = "needs_baseline"
    else:
        verdict = "passed"
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": protocol.get("protocol_id"),
        "run_id": run.get("run_id"),
        "release_verdict": verdict,
        "suite_verdict": "complete" if actual_mac and not suite_pending and not codes & invalid_codes else "incomplete",
        "comparison_verdict": comparison,
        "meaning": "Structure/hash assessment of submitted evidence, not replay of verifiers or Mac UI execution. passed covers attested declared scope; it does not imply full Bartender parity or machine-only verification.",
        "evidence_validation_level": "structure_and_artifact_hash_only",
        "replayed_verifiers": 0,
        "applicable_variants": applicable_total,
        "accepted_pass_variants": passed_total,
        "required_pending_variants": required_pending,
        "status_counts": dict(counts),
        "valid_evidence_counts": dict(evidence_counts),
        "blocking_findings": findings,
        "scope_exclusions": exclusions,
        "cases": by_case,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    parser.add_argument("--protocol", type=Path, default=Path(__file__).resolve().parents[1] / "protocol/test-cases.json")
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
        run = json.loads(args.results.read_text(encoding="utf-8"))
        baseline = json.loads(args.baseline.read_text(encoding="utf-8")) if args.baseline else None
        report = evaluate_run(run, protocol, args.results.parent, baseline, args.baseline.parent if args.baseline else None)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        report = {"release_verdict": "invalid", "suite_verdict": "incomplete",
                  "blocking_findings": [{"code": "input_error", "message": str(exc)}]}
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")
    if report["release_verdict"] == "passed":
        return 0
    if report["release_verdict"] in {"invalid", "blocked"}:
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())


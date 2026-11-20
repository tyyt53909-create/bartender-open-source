#!/usr/bin/env python3
"""Check a pinned menu-bar geometry heuristic without using any macOS APIs.

This is a Python translation of the small CollapsedGeometry calculation in
MenubarHide commit a4476bfe81a9a84ac94f8dfb273c4eaad8f9e960. See
upstream/MenubarHide-LICENSE for the original MIT notice and THIRD_PARTY.md.
The validation wrapper and report format are local additions.

"model_satisfied" never means the macOS task passed. The threshold itself is an
upstream empirical heuristic, not a platform contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

MINIMUM_UNIT = 200
CLIFF_MARGIN = 64
NOTCHED_FACTOR = 0.75
MAX_SPACERS = 6


class InputError(ValueError):
    pass


def _finite_number(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def analyze(displays: list[dict]) -> dict:
    # Guards are ours; they intentionally reject cases where upstream would use
    # its fallback. Missing or inconsistent topology must not start hiding.
    if not isinstance(displays, list) or not displays:
        raise InputError("no_displays")
    normalized = []
    for display in displays:
        if not isinstance(display, dict):
            raise InputError("invalid_display")
        width = display.get("width")
        status_width = display.get("status_width", width)
        if not _finite_number(width) or width <= 0:
            raise InputError("invalid_width")
        if not _finite_number(status_width) or not 0 < status_width <= width:
            raise InputError("invalid_status_width")
        normalized.append((float(width), float(status_width)))

    # Source-equivalent formulas on finite 64-bit point inputs.
    cliffs = [
        status_width * NOTCHED_FACTOR if status_width < width else width / 2
        for width, status_width in normalized
    ]
    lowest = min(cliffs)
    widest = max(status_width for _, status_width in normalized)
    unit = max(MINIMUM_UNIT, math.floor(lowest - CLIFF_MARGIN))
    required = max(math.ceil(widest / unit) - 1, 0)
    active = min(required, MAX_SPACERS)
    span = unit * (1 + active)  # separator plus active spacer items
    shortfall = max(widest - span, 0)
    headroom = lowest - unit

    violations = []
    if shortfall > 0:
        violations.append("capacity_shortfall")
    if unit >= lowest:
        violations.append("unit_reaches_model_cliff")
    if headroom < CLIFF_MARGIN:
        violations.append("safety_margin_not_preserved")
    return {
        "unit": unit,
        "active_spacers": active,
        "required_spacers": required,
        "span": span,
        "maximum_span": unit * (1 + MAX_SPACERS),
        "widest_status_width": widest,
        "minimum_model_cliff": lowest,
        "minimum_headroom": headroom,
        "shortfall": shortfall,
        "violations": violations,
        "model_verdict": "model_violation" if violations else "model_satisfied_runtime_unverified",
        "macos_runtime_status": "not_run",
        "candidate_action": "do_not_collapse" if violations else "eligible_for_manual_runtime_experiment_only",
    }


def verify_samples(document: dict) -> dict:
    if document.get("schema_version") != 1 or not isinstance(document.get("cases"), list):
        raise InputError("invalid_sample_schema")
    results = []
    seen = set()
    for sample in document["cases"]:
        case_id = sample["id"]
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            raise InputError("invalid_or_duplicate_case_id")
        seen.add(case_id)
        try:
            calculation = analyze(sample.get("displays"))
        except InputError as exc:
            result = {
                "case_id": case_id,
                "kind": sample.get("kind"),
                "model_verdict": "invalid_input",
                "error": str(exc),
                "candidate_action": "do_not_collapse",
                "macos_runtime_status": "not_run",
                "arithmetic_expectation_match": sample.get("expected_error") == str(exc),
            }
        else:
            expected = sample.get("expected")
            matches = isinstance(expected, dict) and all(
                calculation.get(key) == value for key, value in expected.items()
            ) and "expected_error" not in sample
            result = {
                "case_id": case_id,
                "kind": sample.get("kind"),
                "displays": sample["displays"],
                **calculation,
                "arithmetic_expectation_match": matches,
            }
        results.append(result)
    return {
        "schema_version": 1,
        "evidence_kind": "portable_arithmetic",
        "claim_scope": "Pinned heuristic calculations and input guards only; no macOS behavior tested.",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "system": platform.system(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "model_source_commit": document["source_commit"],
        "all_arithmetic_expectations_match": bool(results) and all(
            row["arithmetic_expectation_match"] for row in results
        ),
        "summary": {
            "total_samples": len(results),
            "model_satisfied_runtime_unverified": sum(r["model_verdict"] == "model_satisfied_runtime_unverified" for r in results),
            "model_violations": sum(r["model_verdict"] == "model_violation" for r in results),
            "invalid_inputs_rejected": sum(r["model_verdict"] == "invalid_input" for r in results),
            "macos_runtime_cases_executed": 0,
        },
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=Path, default=base / "geometry-samples.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        sample_bytes = args.samples.read_bytes()
        document = json.loads(sample_bytes)
        report = verify_samples(document)
        report["input_sha256"] = hashlib.sha256(sample_bytes).hexdigest()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("geometry verification rejected input: " + str(exc), file=sys.stderr)
        return 2
    text = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(json.dumps({
        "arithmetic_expectations_match": report["all_arithmetic_expectations_match"],
        **report["summary"],
        "macos_runtime_status": "not_run",
    }, ensure_ascii=False))
    return 0 if report["all_arithmetic_expectations_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())


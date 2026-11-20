#!/usr/bin/env python3
"""Run only portable checks and save their real outputs; never launch Mac apps."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import platform
import plistlib
import re
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "results"

def now():
    return datetime.now(timezone.utc).isoformat()

def run_check(name, arguments, expected=0):
    started = now()
    result = subprocess.run(arguments, cwd=ROOT, capture_output=True, text=True, timeout=60)
    log = OUTPUT / (name + ".log")
    log.write_text("STDOUT\n" + result.stdout + "\nSTDERR\n" + result.stderr, encoding="utf-8")
    counts = re.findall(r"Ran (\d+) tests? in ", result.stderr)
    record = {
        "name": name, "command": arguments, "started_at_utc": started,
        "finished_at_utc": now(), "exit_code": result.returncode,
        "expected_exit_code": expected, "passed": result.returncode == expected,
        "log": log.relative_to(ROOT).as_posix(),
        "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest()
    }
    if counts:
        record["unit_tests_executed"] = sum(int(x) for x in counts)
    return record

def check_structure():
    details = []
    for path, expected_id, expected_binary in (
        ("Fixture/Info.plist", "org.menuvalidation.Fixture", "MenuBarFixture"),
        ("Controller/Info.plist", "org.menuvalidation.Controller", "MenuValidationController"),
    ):
        doc = plistlib.loads((ROOT / path).read_bytes())
        if (doc["CFBundleIdentifier"] != expected_id or doc["CFBundleExecutable"] != expected_binary
                or doc["LSMinimumSystemVersion"] != "14.0"):
            raise ValueError("bundle identity mismatch: " + path)
        details.append(path)
    for path in sorted((ROOT / "protocol").glob("*.json")):
        json.loads(path.read_text(encoding="utf-8"))
        details.append(path.relative_to(ROOT).as_posix())
    protocol = json.loads((ROOT / "protocol/test-cases.json").read_text(encoding="utf-8"))
    if len(protocol["cases"]) != 24 or sum(len(x["required_coverage"]) for x in protocol["cases"]) != 50:
        raise ValueError("unexpected protocol scope")
    manifest = json.loads((ROOT / "backend-analysis/source-manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["sources"]:
        source = ROOT / "backend-analysis" / entry["path"]
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        if actual != entry["sha256"]:
            raise ValueError("pinned source bytes changed: " + entry["path"])
        details.append(source.relative_to(ROOT).as_posix())
    return {"name": "structure_and_pinned_source_hashes", "passed": True, "files_checked": details,
            "claim_scope": "File parsing and packaged source hashes only; no platform execution."}

def main():
    OUTPUT.mkdir(exist_ok=True)
    started = now()
    checks = []
    try:
        checks.append(run_check("geometry-unit-tests", [sys.executable, "-m", "unittest", "discover", "-s", "backend-analysis", "-p", "test_*.py", "-v"]))
        checks.append(run_check("evaluator-unit-tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"]))
        checks.append(run_check("geometry-samples", [sys.executable, "backend-analysis/geometry_verify.py", "--output", "results/geometry-results.json"]))
        for name, script in (("fixture-shell", "Fixture/build.sh"),
                             ("controller-shell", "scripts/build-macos.sh"),
                             ("portable-shell", "scripts/run-portable-checks.sh")):
            checks.append(run_check(name, ["bash", "-n", script]))
        checks.append(check_structure())
        if platform.system() != "Darwin":
            checks.append(run_check("nonmac-build-guard", ["bash", "scripts/build-macos.sh"], expected=78))
        checks.append(run_check("current-preflight-evaluation",
                                [sys.executable, "tools/evaluate_results.py", "results/current-preflight-run.json",
                                 "--output", "results/current-evaluation.json"], expected=2))
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        checks.append({"name": "check_execution_error", "passed": False, "error": str(exc)})
    report = {
        "schema": "menuvalidation.portable-checks.v1",
        "started_at_utc": started, "finished_at_utc": now(),
        "platform": platform.system(), "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "portable_checks_passed": bool(checks) and all(x["passed"] for x in checks),
        "unit_tests_executed": sum(x.get("unit_tests_executed", 0) for x in checks),
        "macos_compilation": "not_run",
        "macos_runtime_cases_executed": 0,
        "private_assertion_activated": False,
        "meaning": "This runner never compiles Swift/Objective-C or executes AppKit UI. All test success is limited to the named portable checks.",
        "checks": checks
    }
    (OUTPUT / "portable-validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("portable_checks_passed", "unit_tests_executed",
                                             "macos_compilation", "macos_runtime_cases_executed")}, ensure_ascii=False))
    return 0 if report["portable_checks_passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())


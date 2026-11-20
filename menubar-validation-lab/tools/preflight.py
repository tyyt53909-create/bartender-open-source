#!/usr/bin/env python3
"""Read local build prerequisites without launching apps or changing permissions."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import shutil
import subprocess

def command(arguments):
    try:
        result = subprocess.run(arguments, capture_output=True, text=True, timeout=12)
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None

def collect():
    system = platform.system()
    is_mac = system == "Darwin"
    tool_presence = {name: shutil.which(name) is not None
                     for name in ("python3", "swift", "swiftc", "clang", "xcrun", "xcodebuild")}
    sdk = command(["xcrun", "--sdk", "macosx", "--show-sdk-version"]) if is_mac and tool_presence["xcrun"] else None
    return {
        "schema": "menuvalidation.preflight.v1",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "platform": "macOS" if is_mac else system,
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "os_version": command(["sw_vers", "-productVersion"]) if is_mac else platform.release(),
        "os_build": command(["sw_vers", "-buildVersion"]) if is_mac else None,
        "tool_presence": tool_presence,
        "macos_sdk_version": sdk,
        "build_preflight": "eligible_for_build_attempt" if is_mac and sdk else "blocked",
        "macos_build_status": "not_run",
        "macos_runtime_status": "not_run",
        "macos_runtime_cases_executed": 0,
        "private_assertion_activated": False,
        "machine_identity_collected": False,
        "note": "Prerequisite presence is not a successful compile or behavior test. No hostname, serial, user name, screen image, application inventory or TCC state was collected."
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = collect()
    content = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    print(content, end="")
    return 0 if report["build_preflight"] == "eligible_for_build_attempt" else 2

if __name__ == "__main__":
    raise SystemExit(main())


#!/bin/bash
set -euo pipefail
lab_root="$(cd "$(dirname "$0")/.." && pwd)"
python3 -m unittest discover -s "$lab_root/backend-analysis" -p 'test_*.py' -v
python3 -m unittest discover -s "$lab_root/tests" -p 'test_*.py' -v
printf '%s\n' 'Portable checks completed. This does not compile Swift or validate macOS UI behavior.'


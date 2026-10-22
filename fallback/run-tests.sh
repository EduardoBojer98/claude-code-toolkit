#!/usr/bin/env bash
# Run the ccfb test suite. No network, no credentials needed.
#   bash fallback/run-tests.sh          # unit + scenario tests
#   CCFB_E2E=1 bash fallback/run-tests.sh   # also drive the real Claude Code CLI (against local fakes)
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/tests"
python3 -m unittest discover -s . -p 'test_*.py' "$@" 2> >(grep -v -E '(switched to fallback|no fallback available|Claude is available|masked )' >&2)

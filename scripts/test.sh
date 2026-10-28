#!/usr/bin/env bash
# Run every offline check in the repo. No network, no credentials, no model calls.
#   bash scripts/test.sh
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"

echo "== JSON syntax"
find "$REPO" -name '*.json' -not -path '*/archive/*' -not -path '*/.git/*' -not -path '*/node_modules/*' -print0 \
  | xargs -0 -n1 python3 -m json.tool >/dev/null && echo "ok"

echo "== Shell syntax"
for f in "$REPO"/claude-code/install.sh "$REPO"/claude-code/hooks/*.sh "$REPO"/scripts/*.sh "$REPO"/fallback/install.sh; do
  bash -n "$f"
done && echo "ok"

echo "== Claude Code layer"
python3 -m unittest discover -s "$REPO/claude-code/tests"

echo "== Fallback (ccfb)"
bash "$REPO/fallback/run-tests.sh"

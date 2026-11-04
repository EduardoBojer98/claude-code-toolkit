#!/usr/bin/env bash
# PreToolUse hook (Bash): block shell commands that print credential files into the conversation.
# Permission deny rules cover the Read tool; this covers `cat .env`, `less ~/.ssh/id_ed25519`, etc.
# Best effort, not a sandbox. Exit 2 = block, reason on stderr goes back to Claude.
set -uo pipefail

input="$(cat)"
command -v jq >/dev/null || exit 0
cmd="$(jq -r '.tool_input.command // ""' <<<"$input")"
[[ -n "$cmd" ]] || exit 0

readers='(cat|less|more|head|tail|bat|batcat|strings|xxd|od|base64|grep|rg|awk|sed|cp|scp|curl|nc)'
secrets='(\.env(\.[A-Za-z0-9_-]+)?|\.ssh/id_[A-Za-z0-9_]+|\.credentials\.json|\.aws/credentials|\.npmrc|auth\.json|\.netrc|\.pgpass|server\.env|claude-free/token)'

# Template files are fine; counting/quiet matches don't print values.
check="$(sed -E -e 's/\.env\.(example|sample|dist|template)//g' \
  -e 's/(grep|rg)[[:space:]]+-[A-Za-z]*[cqlL][^;&|]*//g' <<<"$cmd")"

# A reader command whose arguments name a secret file as its own path token (not e.g. process.env).
if grep -qE "(^|[;&|[:space:]])${readers}[[:space:]]([^;&|]*[[:space:]/'\"=])?${secrets}(['\"]|[[:space:];&|]|$)" <<<"$check"; then
  echo "Blocked by guard-bash: this command would print a credential file into the conversation. Check for a variable instead (grep -q '^NAME=' .env && echo set) or ask the user." >&2
  exit 2
fi
exit 0

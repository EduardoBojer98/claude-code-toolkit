#!/usr/bin/env bash
# Stop hook: while a /council loop is running in this repo (.council/status = running), don't let Claude
# finish until the council approves. Statuses approved / escalated / waiting-user (or no .council/) pass.
# Own cap (COUNCIL_MAX_BLOCKS, default 6) so a stuck loop ends; Claude Code also caps at 8 in a row.
# stop_hook_active is ignored on purpose: one early exit would allow only a single review round.
set -uo pipefail

input="$(cat)"
command -v jq >/dev/null || exit 0
cwd="$(jq -r '.cwd // empty' <<<"$input")"
[[ -n "$cwd" ]] || cwd="$PWD"
root="$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null || echo "$cwd")"
dir="$root/.council"
[[ -f "$dir/status" ]] || exit 0

status="$(tr -d '[:space:]' < "$dir/status")"
[[ "$status" == "running" ]] || exit 0

blocks="$(cat "$dir/blocks" 2>/dev/null || echo 0)"
[[ "$blocks" =~ ^[0-9]+$ ]] || blocks=0
if (( blocks >= ${COUNCIL_MAX_BLOCKS:-6} )); then
  printf 'escalated\n' > "$dir/status"
  exit 0
fi
echo $(( blocks + 1 )) > "$dir/blocks"

round="$(cat "$dir/round" 2>/dev/null || echo 0)"
jq -n --arg r "Council gate: the /council loop is still running (round ${round:-0}, .council/status = running). Continue the loop: snapshot the change, convene the council, fix blocking items. Finish only when every member says APPROVE (set status to approved). If you need the user's answer, set status to waiting-user and ask; if the loop is stuck, set status to escalated and report the open items." \
  '{decision: "block", reason: $r}'

#!/usr/bin/env bash
# Stop hook for /po: while a Project Owner run is active (.po/status = planning|running|verifying), don't let
# Claude finish. status done is re-checked: every acceptance criterion ticked and .po/evidence/final.md present.
# waiting-user / waiting-agents / escalated (or no .po/) pass. Own cap (PO_MAX_BLOCKS, default 8 in a row,
# reset on any allowed stop) so a stuck run escalates.
set -uo pipefail

input="$(cat)"
command -v jq >/dev/null || exit 0
cwd="$(jq -r '.cwd // empty' <<<"$input")"
[[ -n "$cwd" ]] || cwd="$PWD"
root="$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null || echo "$cwd")"
dir="$root/.po"
[[ -f "$dir/status" ]] || exit 0

status="$(tr -d '[:space:]' < "$dir/status")"
reason=""
case "$status" in
  planning|running|verifying)
    reason="PO gate: the /po project is still $status (.po/status). Keep going: run or check the next workstream, or do final acceptance. To wait for PM agents set status to waiting-agents; to ask the user set waiting-user; if blocked set escalated and report." ;;
  done)
    open="$(grep -cE '^[[:space:]]*- \[ \]' "$dir/project.md" 2>/dev/null)"
    if [[ "${open:-0}" -gt 0 ]]; then
      reason="PO gate: status is done but $open acceptance criteria in .po/project.md are still unchecked. Prove each one (rerun its check, save evidence) or set status back to running."
    elif [[ ! -s "$dir/evidence/final.md" ]]; then
      reason="PO gate: status is done but .po/evidence/final.md is missing. Run final acceptance (fresh checks, independent qa, council for code) and write it."
    fi ;;
esac

if [[ -z "$reason" ]]; then
  rm -f "$dir/blocks"
  exit 0
fi

blocks="$(cat "$dir/blocks" 2>/dev/null || echo 0)"
[[ "$blocks" =~ ^[0-9]+$ ]] || blocks=0
if (( blocks >= ${PO_MAX_BLOCKS:-8} )); then
  printf 'escalated\n' > "$dir/status"
  rm -f "$dir/blocks"
  exit 0
fi
echo $(( blocks + 1 )) > "$dir/blocks"
jq -n --arg r "$reason" '{decision: "block", reason: $r}'

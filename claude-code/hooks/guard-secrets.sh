#!/usr/bin/env bash
# PreToolUse hook (Edit|Write|MultiEdit|NotebookEdit): block writing live-looking credentials into files.
# Exit 2 = block, reason on stderr goes back to Claude. Placeholders like <redacted> or YOUR_KEY pass.
set -uo pipefail

input="$(cat)"
command -v jq >/dev/null || exit 0

# Text being written: Write.content, Edit.new_string, MultiEdit.edits[].new_string, NotebookEdit.new_source
text="$(jq -r '[.tool_input.content, .tool_input.new_string, (.tool_input.edits // [] | .[].new_string), .tool_input.new_source] | map(select(. != null)) | join("\n")' <<<"$input" 2>/dev/null)"
[[ -n "$text" ]] || exit 0

file="$(jq -r '.tool_input.file_path // .tool_input.notebook_path // ""' <<<"$input")"
# Example/fixture files may hold fake keys on purpose.
case "$file" in
  *.example|*.example.*|*.sample|*/fixtures/*|*/__fixtures__/*|*/testdata/*) exit 0 ;;
esac

pattern='(sk-ant-[A-Za-z0-9_-]{20,}|sk-or-v1-[A-Za-z0-9]{20,}|sk-(proj-)?[A-Za-z0-9]{32,}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|gh[ousr]_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|xox[abpr]-[A-Za-z0-9-]{20,}|shp(at|ca|pa|ss)_[a-fA-F0-9]{32}|sk_live_[A-Za-z0-9]{20,}|-----BEGIN ([A-Z]+ )?PRIVATE KEY-----)'

if match="$(grep -oE "$pattern" <<<"$text" | head -n1)"; then
  echo "Blocked by guard-secrets: the content for ${file:-this file} contains what looks like a live credential (${match:0:12}…). Put secrets in a gitignored .env and reference them by name; use a placeholder in committed files." >&2
  exit 2
fi
exit 0

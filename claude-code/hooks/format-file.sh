#!/usr/bin/env bash
# PostToolUse hook (Edit|Write|MultiEdit): format the edited file with the project's own Prettier,
# only when the project has a Prettier config and a local install. Never installs anything,
# never formats ignored, vendor or build files. Silent on success; never blocks.
set -uo pipefail

input="$(cat)"
command -v jq >/dev/null || exit 0
file="$(jq -r '.tool_input.file_path // ""' <<<"$input")"
[[ -f "$file" ]] || exit 0

case "$file" in
  */node_modules/*|*/vendor/*|*/dist/*|*/build/*|*/.git/*|*.min.*|*.lock|*-lock.json) exit 0 ;;
  *.js|*.jsx|*.ts|*.tsx|*.mjs|*.cjs|*.css|*.scss|*.json|*.md|*.html|*.liquid|*.php|*.vue|*.yml|*.yaml) ;;
  *) exit 0 ;;
esac

# Walk up to the nearest package.json.
dir="$(dirname "$file")"
while [[ "$dir" != "/" && ! -f "$dir/package.json" ]]; do dir="$(dirname "$dir")"; done
[[ -f "$dir/package.json" ]] || exit 0

prettier="$dir/node_modules/.bin/prettier"
[[ -x "$prettier" ]] || exit 0
has_config=0
for c in .prettierrc .prettierrc.json .prettierrc.yml .prettierrc.yaml .prettierrc.js .prettierrc.cjs .prettierrc.mjs prettier.config.js prettier.config.cjs prettier.config.mjs .prettierrc.toml; do
  [[ -f "$dir/$c" ]] && { has_config=1; break; }
done
[[ $has_config -eq 1 ]] || jq -e '.prettier' "$dir/package.json" >/dev/null 2>&1 || exit 0

# --ignore-unknown skips files Prettier has no parser/plugin for (e.g. .php without @prettier/plugin-php).
(cd "$dir" && timeout 20 "$prettier" --write --ignore-unknown --log-level warn "$file" >/dev/null 2>&1) || true
exit 0

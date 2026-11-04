#!/usr/bin/env bash
# Turn on plugins that are off at user level for ONE project only, via its .claude/settings.local.json
# (personal, never committed). Run again with --off to turn them back off there.
#
#   bash claude-code/enable-plugins.sh wordpress [project-dir]   # WordPress Dev Skills + its dependency
#   bash claude-code/enable-plugins.sh seo [project-dir]         # searchfit-seo
#   bash claude-code/enable-plugins.sh figma [project-dir]       # Figma plugin + MCP (sign in via /mcp)
#   bash claude-code/enable-plugins.sh motion [project-dir]      # GSAP skills, only for projects that use GSAP
#   bash claude-code/enable-plugins.sh wordpress [dir] --off
set -euo pipefail

declare -A PROFILES=(
  [wordpress]="wp-dev-skills@synced wordpress-official-agent-skills@wordpress-official-agent-skills"
  [seo]="searchfit-seo@synced"
  [figma]="figma@claude-plugins-official"
  [motion]="gsap-skills@gsap-skills"
)

profile="${1:-}"; dir="."; value=true
shift || true
for a in "$@"; do
  case "$a" in --off) value=false ;; *) dir="$a" ;; esac
done
[[ -n "$profile" && -n "${PROFILES[$profile]:-}" ]] || {
  echo "Usage: $0 <$(IFS='|'; echo "${!PROFILES[*]}")> [project-dir] [--off]" >&2; exit 1; }
command -v jq >/dev/null || { echo "Missing jq (sudo pacman -S jq)." >&2; exit 1; }

dir="$(cd "$dir" && pwd)"
# Claude Code reads the local file at the repository root when inside git.
root="$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null || echo "$dir")"
file="$root/.claude/settings.local.json"
mkdir -p "$root/.claude"
[[ -f "$file" ]] || echo '{}' > "$file"

tmp="$(mktemp)"
jq --argjson v "$value" --arg ids "${PROFILES[$profile]}" \
  '.enabledPlugins = ((.enabledPlugins // {}) + ($ids | split(" ") | map({(.): $v}) | add))' "$file" > "$tmp"
mv "$tmp" "$file"

# Keep it out of commits: hand-made local files aren't auto-ignored.
if git -C "$root" rev-parse --git-dir >/dev/null 2>&1 && ! git -C "$root" check-ignore -q "$file"; then
  # --path-format=absolute: a relative --git-path resolves against the caller's cwd, not $root.
  echo ".claude/settings.local.json" >> "$(git -C "$root" rev-parse --path-format=absolute --git-path info/exclude)"
  echo "ignored .claude/settings.local.json via .git/info/exclude"
fi

echo "$profile plugins $([[ $value == true ]] && echo on || echo off) in $file"
echo "Start a new Claude Code session in $root to apply."

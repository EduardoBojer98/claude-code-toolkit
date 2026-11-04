#!/usr/bin/env bash
# Health check of the Claude Code setup on THIS machine. No model calls, no usage.
#   bash scripts/doctor.sh
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
fail=0
ok()   { printf '  ok    %s\n' "$*"; }
bad()  { printf '  FAIL  %s\n' "$*"; fail=1; }
info() { printf '  info  %s\n' "$*"; }

echo "== Tools"
for t in claude git gh jq python3 node npx rg docker lando; do
  if p="$(command -v "$t")"; then ok "$t ($p)"; else
    case "$t" in docker|lando|rg) info "$t not found (optional)";; *) bad "$t not found";; esac
  fi
done
command -v claude >/dev/null && info "$(claude --version 2>/dev/null)"
command -v node >/dev/null && info "node $(node --version)"

echo "== Links into $DEST"
check_link() {  # $1 target, $2 expected source
  if [[ -L "$1" && "$(readlink "$1")" == "$2" && -e "$1" ]]; then ok "${1#$DEST/}"; else bad "${1#$DEST/} (run: bash claude-code/install.sh)"; fi
}
check_link "$DEST/CLAUDE.md" "$REPO/claude-code/CLAUDE.md"
for f in "$REPO"/claude-code/agents/*.md; do check_link "$DEST/agents/$(basename "$f")" "$f"; done
check_link "$DEST/hooks/claude-setup" "$REPO/claude-code/hooks"
check_link "$DEST/skills/debug" "$REPO/claude-code/skills/debug"
check_link "$DEST/skills/web-dev-standards" "$REPO/skills/web-dev-standards"
for b in security-scan claude-free; do
  [[ "$(readlink "$HOME/.local/bin/$b")" == "$REPO/claude-code/bin/$b" ]] && ok "~/.local/bin/$b" || bad "~/.local/bin/$b (run: bash claude-code/install.sh)"
done
for h in "$REPO"/claude-code/hooks/*.sh; do [[ -x "$h" ]] || bad "hook not executable: $h"; done

echo "== Settings"
if jq empty "$DEST/settings.json" 2>/dev/null; then ok "settings.json is valid JSON"; else bad "settings.json invalid"; fi
missing="$(python3 - "$REPO/claude-code/settings.json" "$DEST/settings.json" <<'PY'
import json, sys
t, c = (json.load(open(p)) for p in sys.argv[1:3])
out = []
for k in ("allow", "ask", "deny"):
    out += [f"permissions.{k}: {r}" for r in t["permissions"][k] if r not in c.get("permissions", {}).get(k, [])]
for ev, groups in t["hooks"].items():
    out += [f"hooks.{ev}" for g in groups if g not in c.get("hooks", {}).get(ev, [])]
out += [f"skillOverrides.{k}" for k in t["skillOverrides"] if k not in c.get("skillOverrides", {})]
print("\n".join(out))
PY
)"
if [[ -z "$missing" ]]; then ok "template rules, hooks and skill overrides present"; else bad "missing from settings (re-run installer):"; echo "$missing" | sed 's/^/        /'; fi
info "model: $(jq -r '.model // "default (your /model choice)"' "$DEST/settings.json"), effort: $(jq -r '.effortLevel // "unset"' "$DEST/settings.json"), subagent default: $(jq -r '.env.CLAUDE_CODE_SUBAGENT_MODEL // "main model"' "$DEST/settings.json")"

echo "== Plugins (enabled = true in user settings)"
jq -r '.enabledPlugins // {} | to_entries[] | "  \(if .value then "on " else "off" end)   \(.key)"' "$DEST/settings.json"
if command -v claude >/dev/null; then
  claude plugin list 2>/dev/null | grep -B2 -E "Error" | grep -E "❯|Error" | sed 's/^/  FAIL  /' && fail=1
fi

echo "== MCP servers"
claude mcp list 2>/dev/null | grep -E "✔|✘|!" | sed -E 's/^/  /'
claude mcp list 2>/dev/null | grep -q "✘" && info "a server failed to connect (see above)"

echo "== Context per request (claude -p /context, free)"
(cd "$REPO" && timeout 150 claude -p "/context" 2>/dev/null) | grep -E "Tokens:|^\| (Skills|Memory files|Custom agents|System tools|MCP tools) " | sed 's/^/  /'

echo
if [[ $fail -eq 0 ]]; then echo "All checks passed."; else echo "Some checks FAILED (see above)."; fi
exit $fail

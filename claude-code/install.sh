#!/usr/bin/env bash
# Install the Claude Code user layer from this repo into ~/.claude (or $CLAUDE_CONFIG_DIR).
# Safe to re-run: links are refreshed, anything else in the way is moved to *.bak-<timestamp>
# (never deleted), and settings are merged - your existing values win, lists are unioned.
#
#   bash claude-code/install.sh            # install / update
#   bash claude-code/install.sh --dry-run  # show what would change
#   bash claude-code/install.sh --no-settings   # links only, leave settings.json alone
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
DEST="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
TS="$(date +%Y%m%d-%H%M%S)"
DRY=0; SETTINGS=1
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1 ;;
    --no-settings) SETTINGS=0 ;;
    -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
    *) echo "Unknown option: $a" >&2; exit 1 ;;
  esac
done

for dep in python3 jq; do
  command -v "$dep" >/dev/null || { echo "Missing $dep (CachyOS: sudo pacman -S $dep)." >&2; exit 1; }
done

run() { if [[ $DRY -eq 1 ]]; then echo "would: $*"; else "$@"; fi; }

# link <source> <target>: point target at source, moving anything else out of the way.
link() {
  local src="$1" dst="$2"
  if [[ -L "$dst" && "$(readlink "$dst")" == "$src" ]]; then echo "ok      $dst"; return; fi
  run mkdir -p "$(dirname "$dst")"
  if [[ -e "$dst" || -L "$dst" ]]; then
    run mv "$dst" "$dst.bak-$TS"; echo "backup  $dst -> $dst.bak-$TS"
  fi
  run ln -s "$src" "$dst"; echo "link    $dst -> $src"
}

link "$HERE/CLAUDE.md" "$DEST/CLAUDE.md"
for f in "$HERE"/agents/*.md; do link "$f" "$DEST/agents/$(basename "$f")"; done
link "$HERE/hooks" "$DEST/hooks/claude-setup"
link "$HERE/skills/debug" "$DEST/skills/debug"
link "$REPO/skills/web-dev-standards" "$DEST/skills/web-dev-standards"
link "$REPO/skills/toolkit-maintainer" "$DEST/skills/toolkit-maintainer"
chmod +x "$HERE"/hooks/*.sh

if [[ $SETTINGS -eq 1 ]]; then
  target="$DEST/settings.json"
  merged="$(python3 - "$HERE/settings.json" "$target" <<'PY'
import json, os, sys
template = json.load(open(sys.argv[1]))
current = json.load(open(sys.argv[2])) if os.path.exists(sys.argv[2]) else {}

def merge(cur, new):
    """Existing scalars win; dicts merge recursively; lists are unioned in order."""
    if isinstance(cur, dict) and isinstance(new, dict):
        out = dict(cur)
        for k, v in new.items():
            out[k] = merge(cur[k], v) if k in cur else v
        return out
    if isinstance(cur, list) and isinstance(new, list):
        out = list(cur)
        for item in new:
            if item not in out:
                out.append(item)
        return out
    return cur

print(json.dumps(merge(current, template), indent=2))
PY
)"
  if [[ -f "$target" ]] && diff -q <(jq -S . "$target") <(jq -S . <<<"$merged") >/dev/null; then
    echo "ok      $target (already contains the template)"
  else
    if [[ $DRY -eq 1 ]]; then
      echo "would merge into $target:"; diff <(jq -S . "$target" 2>/dev/null || echo '{}') <(jq -S . <<<"$merged") || true
    else
      [[ -f "$target" ]] && cp "$target" "$target.bak-$TS" && echo "backup  $target -> $target.bak-$TS"
      printf '%s\n' "$merged" > "$target"; echo "merged  $target"
    fi
  fi
fi

echo
echo "Done. Start a new Claude Code session, then check: /status (settings), /agents, /skills, /hooks, /context."

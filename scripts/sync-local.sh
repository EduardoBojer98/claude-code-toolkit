#!/usr/bin/env bash
# Back up the Claude Code setup on THIS machine into the repo (local/<hostname>/).
# Copies settings, global CLAUDE.md, installed plugins + marketplaces, MCP servers,
# own agents/commands/skills/hooks. Secrets are redacted; nothing is ever deleted
# from the repo except the previous copy of the same machine folder.
#
#   bash scripts/sync-local.sh           # copy + show what changed
#   bash scripts/sync-local.sh --push    # copy, commit and push
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
MACHINE="${CLAUDE_SYNC_MACHINE:-$(hostname -s)}"
OUT="$REPO/local/$MACHINE"

[[ -d "$SRC" ]] || { echo "No $SRC found - is Claude Code installed here?" >&2; exit 1; }
command -v python3 >/dev/null || { echo "python3 is needed (sudo apt install python3)." >&2; exit 1; }

rm -rf "$OUT"
mkdir -p "$OUT"

# Redact anything that looks like a secret: keys named *key/token/secret/password/auth*,
# plus env and headers blocks of MCP servers.
redact_json() {  # $1 = in, $2 = out, $3 = optional top-level key to keep
  python3 - "$1" "$2" "${3:-}" <<'PY'
import json, re, sys
src, dst, keep = sys.argv[1], sys.argv[2], sys.argv[3]
data = json.load(open(src))
if keep:
    data = {keep: data.get(keep, {})}
SECRET = re.compile(r"(key|token|secret|password|passwd|auth|cookie|credential)", re.I)
def walk(o, parent=""):
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            if parent in ("env", "headers") and isinstance(v, str):
                out[k] = "<redacted>"
            elif SECRET.search(k) and isinstance(v, (str, int)):
                out[k] = "<redacted>"
            else:
                out[k] = walk(v, k)
        return out
    if isinstance(o, list):
        return [walk(x, parent) for x in o]
    return o
json.dump(walk(data), open(dst, "w"), indent=2)
open(dst, "a").write("\n")
PY
}

copied=()
# Files
for f in settings.json keybindings.json; do
  [[ -f "$SRC/$f" ]] && { redact_json "$SRC/$f" "$OUT/$f"; copied+=("$f"); }
done
if [[ -L "$SRC/CLAUDE.md" ]]; then
  echo "CLAUDE.md -> $(readlink "$SRC/CLAUDE.md")" > "$OUT/CLAUDE.md.symlink.txt"; copied+=("CLAUDE.md (symlink)")
elif [[ -f "$SRC/CLAUDE.md" ]]; then
  cp "$SRC/CLAUDE.md" "$OUT/CLAUDE.md"; copied+=("CLAUDE.md")
fi
for f in installed_plugins.json known_marketplaces.json; do
  if [[ -f "$SRC/plugins/$f" ]]; then
    mkdir -p "$OUT/plugins"; redact_json "$SRC/plugins/$f" "$OUT/plugins/$f"; copied+=("plugins/$f")
  fi
done

# User-level MCP servers live in ~/.claude.json (which also holds history - only mcpServers is kept).
if [[ -f "$HOME/.claude.json" ]]; then
  redact_json "$HOME/.claude.json" "$OUT/mcp-servers.json" mcpServers; copied+=("mcp-servers.json")
fi

# Own folders. Symlinks (e.g. skills linked from this repo) are recorded, not copied.
for d in agents commands hooks skills output-styles; do
  [[ -d "$SRC/$d" ]] || continue
  mkdir -p "$OUT/$d"
  for item in "$SRC/$d"/*; do
    [[ -e "$item" || -L "$item" ]] || continue
    name="$(basename "$item")"
    # synced/ = claude.ai built-in skills Claude Code downloads; not ours, not backed up.
    [[ "$d/$name" == "skills/synced" ]] && continue
    if [[ -L "$item" ]]; then
      echo "$name -> $(readlink "$item")" >> "$OUT/$d/_symlinks.txt"
    else
      cp -r "$item" "$OUT/$d/$name"
    fi
  done
  copied+=("$d/")
done

# Status line script, if settings points to a file in ~/.claude.
for s in "$SRC"/statusline*; do [[ -f "$s" ]] && { cp "$s" "$OUT/"; copied+=("$(basename "$s")"); }; done

# Plain-text summary that is easy to read on GitHub.
{
  echo "# Claude Code on $MACHINE"
  echo
  echo "Synced: $(date -u +%Y-%m-%dT%H:%MZ) by scripts/sync-local.sh"
  echo "Claude Code: $(claude --version 2>/dev/null || echo 'not on PATH')"
  echo
  echo "## Copied"
  printf -- '- %s\n' "${copied[@]}"
  echo
  echo "## MCP servers (claude mcp list)"
  echo '```'
  (claude mcp list 2>/dev/null || echo "claude not on PATH") | sed -E 's/(token|key|secret)=[^ &]+/\1=<redacted>/Ig'
  echo '```'
} > "$OUT/README.md"

# Last guard: refuse to continue if something that looks like a live key slipped through.
if grep -rEn '(sk-ant-[A-Za-z0-9_-]{10,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AIza[0-9A-Za-z_-]{30,}|sk-or-[A-Za-z0-9-]{20,})' "$OUT" ; then
  echo "STOP: possible secret above - nothing was committed. Remove it from $OUT and re-run." >&2
  exit 1
fi

cd "$REPO"
git add "local/$MACHINE"
echo "Changes for local/$MACHINE:"
git status --short "local/$MACHINE" || true

if [[ "${1:-}" == "--push" ]]; then
  if git diff --cached --quiet; then echo "Already up to date."; exit 0; fi
  git commit -m "chore(local): sync Claude Code setup from $MACHINE"
  git pull --rebase --quiet
  git push
  echo "Pushed."
fi

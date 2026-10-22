#!/usr/bin/env bash
# Refresh plugins/ from the Claude session's synced copies, and warn if an own skill
# on the account differs from the repo version (the repo is the source of truth).
# Run from the repo root inside a Claude session:  bash scripts/refresh-snapshot.sh
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
PLUG_SRC="$(ls -d /root/.claude/plugins/synced/*/ 2>/dev/null | head -n1)"
SKILL_SRC="$(ls -d /root/.claude/skills/synced/*/ 2>/dev/null | head -n1)"

SKIP="brightdata-plugin"

[[ -n "$PLUG_SRC" ]] || { echo "No synced plugins found - run this inside a Claude session." >&2; exit 1; }

# Safety: archive/ is never touched by this script. Before plugins/ is rebuilt, any snapshot
# whose plugin is no longer enabled is moved to archive/plugins/ instead of being lost.
mkdir -p "$REPO/archive/plugins"
live_names=""
for dir in "$PLUG_SRC"*/; do
  m="$dir.claude-plugin/plugin.json"
  [[ -f "$m" ]] && live_names+=" $(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["name"])' "$m") "
done
for snap in "$REPO"/plugins/*/; do
  [[ -d "$snap" ]] || continue
  n="$(basename "$snap")"
  case "$live_names" in *" $n "*) continue ;; esac
  if [[ ! -d "$REPO/archive/plugins/$n" ]]; then
    mv "$snap" "$REPO/archive/plugins/$n"
    echo "ARCHIVED: $n is no longer enabled; its snapshot moved to archive/plugins/$n (add it to archive/README.md)."
  fi
done

# Map each synced plugin folder to a readable name using its plugin.json "name".
rm -rf "$REPO/plugins"
mkdir -p "$REPO/plugins"
for dir in "$PLUG_SRC"*/; do
  manifest="$dir.claude-plugin/plugin.json"
  [[ -f "$manifest" ]] || continue
  name="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["name"])' "$manifest")"
  # Plugins kept off by decision are not backed up (keep in sync with DECISIONS.md -> Skip).
  case " $SKIP " in *" $name "*) continue ;; esac
  cp -r "$dir" "$REPO/plugins/$name"
done

# Strip sync markers and nested git dirs.
find "$REPO/plugins" -name .in_use -prune -exec rm -rf {} +
find "$REPO/plugins" -mindepth 2 -name .git -prune -exec rm -rf {} +

# Body of a SKILL.md without YAML frontmatter.
strip_fm() { awk 'NR==1 && /^---$/ {fm=1; next} fm && /^---$/ {fm=0; next} !fm' "$1" | sed '/./,$!d'; }

# Compare own skills (account copy vs repo copy).
if [[ -n "$SKILL_SRC" ]]; then
  for skill in "$REPO"/skills/*/; do
    s="$(basename "$skill")"
    if [[ -f "$SKILL_SRC$s/SKILL.md" ]]; then
      diff -q <(strip_fm "$SKILL_SRC$s/SKILL.md") <(strip_fm "$skill/SKILL.md") >/dev/null 2>&1 \
        || echo "NOTE: $s on the account differs from the repo copy - review before committing."
    else
      echo "NOTE: $s is in the repo but not saved on the account."
    fi
  done
fi

echo "Snapshot refreshed: $(ls "$REPO/plugins" | wc -l) plugins."

#!/usr/bin/env bash
# One-time OmniRoute setup for claude-free: the "free-coding" combo (models in omniroute-combo.json)
# and an OmniRoute key restricted to that combo, saved to ~/.config/claude-free/token (mode 600).
# Safe to re-run: an existing combo is updated, an existing key file is kept.
# Needs: omniroute (npm i -g omniroute), jq, and provider keys added in the OmniRoute dashboard.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMBO_FILE="$HERE/omniroute-combo.json"
TOKEN_FILE="$HOME/.config/claude-free/token"
quiet() { grep -v 'Loaded env\|is ignored' || true; }

command -v omniroute >/dev/null || { echo "Install OmniRoute first: npm i -g omniroute" >&2; exit 1; }
command -v jq >/dev/null || { echo "Missing jq (sudo pacman -S jq)." >&2; exit 1; }
curl -fs --max-time 3 http://localhost:20128/api/health >/dev/null || omniroute serve --daemon --no-open >/dev/null 2>&1
for _ in $(seq 1 30); do curl -fs --max-time 2 http://localhost:20128/api/health >/dev/null && break; sleep 1; done

name="$(jq -r .name "$COMBO_FILE")"
id="$(omniroute --output json combo list 2>&1 | quiet | jq -r --arg n "$name" '.combos[] | select(.name == $n) | .id')"
if [[ -n "$id" ]]; then
  omniroute --output json api combos put-api-combos-id- --id "$id" --body "@$COMBO_FILE" 2>&1 | quiet | jq -e '.error == null' >/dev/null
  echo "updated combo $name"
else
  omniroute --output json api combos post-api-combos --body "@$COMBO_FILE" 2>&1 | quiet | jq -e '.error == null' >/dev/null
  echo "created combo $name"
fi

if [[ -s "$TOKEN_FILE" ]]; then
  echo "kept key $TOKEN_FILE"
else
  umask 077; mkdir -p "$(dirname "$TOKEN_FILE")"
  body="$(jq -nc --arg n "$name" '{name: $n, modelAccessMode: "restricted", allowedModels: [$n]}')"
  # The key is shown once, at creation: it goes straight into the file and is never printed.
  omniroute --output json api api-keys post-api-keys --body "$body" 2>&1 | quiet | jq -r '.key // .apiKey // empty' > "$TOKEN_FILE"
  [[ -s "$TOKEN_FILE" ]] || { rm -f "$TOKEN_FILE"; echo "Could not create the key; create one restricted to '$name' in the dashboard and save it to $TOKEN_FILE." >&2; exit 1; }
  echo "created key $name -> $TOKEN_FILE"
fi
echo "Done. Start it with: claude-free"

#!/usr/bin/env bash
# Install ccfb from this repository for the current user. Safe to re-run (also used to upgrade).
#   bash fallback/install.sh            # install or update
#   bash fallback/install.sh --settings # also add ccfb's status line + hooks to ~/.claude/settings.json (backup first)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${CCFB_BIN_DIR:-$HOME/.local/bin}"
CONFIG_DIR="${CCFB_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/claude-fallback}"

say() { printf '%s\n' "$*"; }
fail() { printf 'ccfb install: %s\n' "$*" >&2; exit 1; }

# 1. Prerequisites
command -v python3 >/dev/null || fail "python3 not found. Install Python 3.11+ (Ubuntu: sudo apt install python3)."
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' \
  || fail "Python $(python3 -c 'import platform; print(platform.python_version())') is too old; ccfb needs 3.11+."
python3 -c 'import zoneinfo, tomllib, ssl' 2>/dev/null || fail "Python is missing standard modules (zoneinfo/tomllib/ssl)."
command -v claude >/dev/null || say "note: Claude Code (claude) is not on PATH yet. Install it before using claude-fb."

# 2. Commands on PATH (symlinks into this repo, so `git pull` upgrades them)
mkdir -p "$BIN_DIR"
chmod +x "$HERE/bin/ccfb" "$HERE/bin/claude-fb"
ln -sf "$HERE/bin/ccfb" "$BIN_DIR/ccfb"
ln -sf "$HERE/bin/claude-fb" "$BIN_DIR/claude-fb"
case ":$PATH:" in *":$BIN_DIR:"*) ;; *) say "note: add $BIN_DIR to your PATH (e.g. in ~/.bashrc: export PATH=\"$BIN_DIR:\$PATH\")";; esac

# 3. Private config and secrets template (never overwritten)
mkdir -p "$CONFIG_DIR"
chmod 700 "$CONFIG_DIR"
if [ ! -f "$CONFIG_DIR/.env" ]; then
  cp "$HERE/.env.example" "$CONFIG_DIR/.env"
  say "created $CONFIG_DIR/.env: add at least one free API key there"
fi
chmod 600 "$CONFIG_DIR/.env"
if [ ! -f "$CONFIG_DIR/config.toml" ]; then
  cat > "$CONFIG_DIR/config.toml" <<'EOF'
# Personal overrides for ccfb. Same structure as fallback/config/providers.toml in the
# claude-setup repo; only the keys you set here change. Examples:
# [fallback]
# preferred_providers = ["gemini", "openrouter"]
# [recovery]
# probe_interval_minutes = 30
# [providers.ollama]
# enabled = true
EOF
fi

# 4. Optional Claude Code integration
if [ "${1:-}" = "--settings" ]; then
  "$HERE/bin/ccfb" install-settings --apply >/dev/null
fi

say "installed ccfb $("$HERE/bin/ccfb" --version | cut -d' ' -f2) -> $BIN_DIR"
say "next: edit $CONFIG_DIR/.env, then run: ccfb doctor"

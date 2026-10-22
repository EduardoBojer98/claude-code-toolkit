"""Where ccfb keeps user config, secrets and runtime state (never inside the repo)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_FALLBACK_DIR = Path(__file__).resolve().parent.parent  # <repo>/fallback


def _base(env_var: str, xdg_var: str, xdg_default: str, win_var: str) -> Path:
    override = os.environ.get(env_var)
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32":
        root = os.environ.get(win_var) or str(Path.home() / "AppData" / "Roaming")
        return Path(root) / "claude-fallback"
    root = os.environ.get(xdg_var) or str(Path.home() / xdg_default)
    return Path(root) / "claude-fallback"


def config_dir() -> Path:
    return _base("CCFB_CONFIG_DIR", "XDG_CONFIG_HOME", ".config", "APPDATA")


def state_dir() -> Path:
    return _base("CCFB_STATE_DIR", "XDG_STATE_HOME", ".local/state", "LOCALAPPDATA")


def user_config_file() -> Path:
    return config_dir() / "config.toml"


def secrets_file() -> Path:
    return config_dir() / ".env"


def state_file() -> Path:
    return state_dir() / "state.json"


def log_file() -> Path:
    return state_dir() / "gateway.log"


def pid_file() -> Path:
    return state_dir() / "gateway.pid"


def handoff_dir() -> Path:
    return state_dir() / "handoffs"


def default_registry() -> Path:
    return REPO_FALLBACK_DIR / "config" / "providers.toml"


def claude_projects_dir() -> Path:
    base = os.environ.get("CLAUDE_CONFIG_DIR")
    return (Path(base).expanduser() if base else Path.home() / ".claude") / "projects"


def ensure_private_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(0o700)
    except OSError:
        pass
    return path

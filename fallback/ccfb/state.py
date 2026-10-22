"""Persistent routing state shared by the gateway and the CLI.

Holds the routing mode, why it last changed, when Claude may be tried again,
and per-provider/model health and locally observed usage. Usage figures are
local observations, never claims about the provider's real remaining quota.
"""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from . import paths

MODE_CLAUDE = "claude"
MODE_FALLBACK = "fallback"


def next_day_reset(now: float, zone: str) -> float:
    """Epoch seconds of the next midnight in the provider's reset zone."""
    tz = ZoneInfo("America/Los_Angeles") if zone == "pacific" else timezone.utc
    local = datetime.fromtimestamp(now, tz)
    midnight = (local + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return midnight.timestamp()


def day_key(now: float, zone: str) -> str:
    tz = ZoneInfo("America/Los_Angeles") if zone == "pacific" else timezone.utc
    return datetime.fromtimestamp(now, tz).strftime("%Y-%m-%d")


@dataclass
class Health:
    cooldown_until: float = 0.0
    cooldown_reason: str = ""
    consecutive_failures: int = 0
    disabled_reason: str = ""          # e.g. credential rejected; cleared on restart or `ccfb reset`
    last_ok: float = 0.0
    last_error: str = ""
    # Locally observed usage (estimates). Windows are lists of request timestamps / (ts, tokens).
    minute_requests: list[float] = field(default_factory=list)
    minute_tokens: list[list[float]] = field(default_factory=list)
    day: str = ""
    day_requests: int = 0
    day_tokens: int = 0
    # Last values a provider reported in headers, with when they were seen.
    reported: dict[str, Any] = field(default_factory=dict)


@dataclass
class State:
    mode: str = MODE_CLAUDE
    mode_since: float = 0.0
    last_switch_reason: str = "start"
    claude_reset_at: float = 0.0         # best known reset time of the Claude limit (may be estimate)
    claude_reset_source: str = ""
    next_probe_at: float = 0.0
    manual_hold: bool = False            # set by `ccfb use-fallback`, cleared by `ccfb resume`
    current_fallback: str = ""           # provider/model key last used successfully
    current_since: float = 0.0
    last_route: dict[str, Any] = field(default_factory=dict)
    health: dict[str, Health] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)


class StateStore:
    """Thread-safe in-memory state with atomic JSON persistence."""

    MAX_EVENTS = 50

    def __init__(self, path: Path | None = None, clock=time.time):
        self.path = path or paths.state_file()
        self.clock = clock
        self.lock = threading.RLock()
        self.state = self._read()

    def _read(self) -> State:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return State(mode_since=self.clock())
        health = {k: Health(**v) for k, v in data.pop("health", {}).items()}
        known = set(State.__dataclass_fields__)
        state = State(**{k: v for k, v in data.items() if k in known})
        state.health = health
        return state

    def reload(self) -> None:
        with self.lock:
            self.state = self._read()

    def save(self) -> None:
        with self.lock:
            paths.ensure_private_dir(self.path.parent)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(asdict(self.state), indent=2), encoding="utf-8")
            os.replace(tmp, self.path)

    def health(self, key: str) -> Health:
        with self.lock:
            return self.state.health.setdefault(key, Health())

    def event(self, kind: str, **details: Any) -> None:
        with self.lock:
            self.state.events.append({"t": round(self.clock(), 3), "kind": kind, **details})
            del self.state.events[: -self.MAX_EVENTS]

    def set_mode(self, mode: str, reason: str) -> None:
        with self.lock:
            if self.state.mode != mode:
                self.state.mode = mode
                self.state.mode_since = self.clock()
                self.state.last_switch_reason = reason
                self.event("mode", mode=mode, reason=reason)
            self.save()

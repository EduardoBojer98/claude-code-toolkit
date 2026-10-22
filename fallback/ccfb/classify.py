"""Classify upstream responses.

Claude: Claude Code's own error docs (code.claude.com/docs/en/errors, checked 2026-10-22)
say a real plan limit (session/weekly/model-family) arrives as HTTP 429 carrying Anthropic's
"unified" quota headers, while a short server throttle arrives as 429 *without* them. Only
the former triggers fallback. Header names are matched by prefix because the docs describe
the header family but don't list every name.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Mapping

UNIFIED_PREFIX = "anthropic-ratelimit-unified"

# Categories
USAGE_LIMIT = "usage_limit"          # Claude plan limit: fall back
THROTTLE = "throttle"                # short-lived rate limit: let the client retry / back off
OVERLOADED = "overloaded"            # 529 / capacity: not a quota problem
AUTH = "auth"                        # 401/403: never treated as a usage limit
INVALID = "invalid_request"          # 400/404/413/422
CONTEXT = "context_too_long"         # 400 that says the prompt is too long
SERVER = "server_error"              # 5xx
NETWORK = "network_error"            # no HTTP response at all
OK = "ok"


@dataclass
class Verdict:
    category: str
    status: int
    reset_at: float = 0.0            # epoch seconds, 0 = unknown
    retry_after: float = 0.0         # seconds, 0 = unknown
    daily: bool = False              # provider said a per-day quota is exhausted
    detail: str = ""


def _lower(headers: Mapping[str, str]) -> dict[str, str]:
    return {k.lower(): v for k, v in headers.items()}


def parse_time(value: str, now: float | None = None) -> float:
    """Accept epoch seconds/ms, ISO-8601, HTTP dates, durations like '1m30s' or '12.5s'."""
    now = time.time() if now is None else now
    value = (value or "").strip()
    if not value:
        return 0.0
    if re.fullmatch(r"\d+(\.\d+)?", value):
        num = float(value)
        if num > 1e12:          # epoch milliseconds
            return num / 1000
        if num > 1e9:           # epoch seconds
            return num
        return now + num        # plain seconds from now
    m = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m(?!s))?(?:(\d+(?:\.\d+)?)s)?(?:(\d+)ms)?", value)
    if m and any(m.groups()):
        h, mi, s, ms = m.groups()
        return now + int(h or 0) * 3600 + int(mi or 0) * 60 + float(s or 0) + int(ms or 0) / 1000
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        pass
    try:
        return parsedate_to_datetime(value).timestamp()
    except (TypeError, ValueError):
        return 0.0


def retry_after_seconds(headers: Mapping[str, str], now: float | None = None) -> float:
    now = time.time() if now is None else now
    value = _lower(headers).get("retry-after", "")
    if not value:
        return 0.0
    at = parse_time(value, now)
    return max(0.0, at - now) if at else 0.0


def unified_reset(headers: Mapping[str, str], now: float | None = None) -> float:
    """Latest reset time found in any unified quota header (the binding window)."""
    now = time.time() if now is None else now
    best = 0.0
    for key, value in _lower(headers).items():
        if key.startswith(UNIFIED_PREFIX) and "reset" in key:
            t = parse_time(value, now)
            if t > now:
                best = max(best, t)
    return best


def has_unified_headers(headers: Mapping[str, str]) -> bool:
    return any(k.lower().startswith(UNIFIED_PREFIX) for k in headers)


def _message(body: bytes) -> str:
    try:
        data = json.loads(body.decode("utf-8", "replace"))
    except ValueError:
        return body[:300].decode("utf-8", "replace")
    err = data.get("error", data) if isinstance(data, dict) else data
    if isinstance(err, list) and err:
        err = err[0]
    if isinstance(err, dict):
        return str(err.get("message") or err.get("type") or "")[:300]
    return str(err)[:300]


_CONTEXT_RE = re.compile(r"prompt is too long|context length|context window|maximum context|too many tokens|reduce the length", re.I)
_DAILY_RE = re.compile(r"per.?day|daily|PerDay|RPD|TPD|requests per day|tokens per day", re.I)


def classify_claude(status: int, headers: Mapping[str, str], body: bytes = b"", now: float | None = None) -> Verdict:
    now = time.time() if now is None else now
    if 200 <= status < 300:
        return Verdict(OK, status)
    msg = _message(body)
    if status == 429:
        if has_unified_headers(headers):
            reset = unified_reset(headers, now)
            ra = retry_after_seconds(headers, now)
            if not reset and ra:
                reset = now + ra
            return Verdict(USAGE_LIMIT, status, reset_at=reset, retry_after=ra, detail=msg)
        return Verdict(THROTTLE, status, retry_after=retry_after_seconds(headers, now), detail=msg)
    if status == 529:
        return Verdict(OVERLOADED, status, detail=msg)
    if status in (401, 403):
        return Verdict(AUTH, status, detail=msg)
    if status in (400, 413) and _CONTEXT_RE.search(msg):
        return Verdict(CONTEXT, status, detail=msg)
    if 400 <= status < 500:
        return Verdict(INVALID, status, detail=msg)
    return Verdict(SERVER, status, detail=msg)


def classify_provider(status: int, headers: Mapping[str, str], body: bytes = b"", now: float | None = None) -> Verdict:
    """Free-provider errors. A provider 429 is a quota/rate problem for that provider only."""
    now = time.time() if now is None else now
    if 200 <= status < 300:
        return Verdict(OK, status)
    msg = _message(body)
    if status == 429:
        ra = retry_after_seconds(headers, now)
        lower = _lower(headers)
        reset = 0.0
        for key in ("x-ratelimit-reset", "x-ratelimit-reset-requests", "x-ratelimit-reset-tokens"):
            if lower.get(key):
                reset = max(reset, parse_time(lower[key], now))
        daily = bool(_DAILY_RE.search(msg)) or lower.get("x-ratelimit-remaining-requests") == "0" and not ra
        return Verdict(THROTTLE, status, reset_at=reset, retry_after=ra, daily=daily, detail=msg)
    if status in (401, 403):
        return Verdict(AUTH, status, detail=msg)
    if status in (400, 413, 422) and _CONTEXT_RE.search(msg):
        return Verdict(CONTEXT, status, detail=msg)
    if status == 529 or status == 503:
        return Verdict(OVERLOADED, status, retry_after=retry_after_seconds(headers, now), detail=msg)
    if 400 <= status < 500:
        return Verdict(INVALID, status, detail=msg)
    return Verdict(SERVER, status, detail=msg)

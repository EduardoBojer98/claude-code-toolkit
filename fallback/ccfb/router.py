"""Pick the best eligible free model for a request.

Ranking is explicit and explainable: user preference order, then the registry priority
(set from the cited sources in providers.toml), with a sticky bonus for the model already
in use so a working fallback isn't switched needlessly. Eligibility checks capabilities the
request actually needs (tools, images, context size) plus health, cooldowns and locally
observed quota. Nothing here estimates a provider's real remaining quota.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from .config import Config, Model, Provider
from .state import Health, StateStore, day_key, next_day_reset


@dataclass
class Needs:
    role: str = "main"
    tools: bool = False
    vision: bool = False
    est_tokens: int = 0


@dataclass
class Candidate:
    provider: Provider
    model: Model
    api_key: str


@dataclass
class Decision:
    candidates: list[Candidate]
    rejected: dict[str, str] = field(default_factory=dict)   # key -> reason


def estimate_tokens(body: dict[str, Any]) -> int:
    """Rough upper estimate: ~3.5 characters per token on the serialized request."""
    return int(len(json.dumps(body, ensure_ascii=False)) / 3.5) + 1


def _has_images(body: dict[str, Any]) -> bool:
    for msg in body.get("messages", []):
        content = msg.get("content")
        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "image":
                    return True
                if block.get("type") == "tool_result" and isinstance(block.get("content"), list):
                    if any(isinstance(b, dict) and b.get("type") == "image" for b in block["content"]):
                        return True
    return False


def needs_for(body: dict[str, Any]) -> Needs:
    model = str(body.get("model", "")).lower()
    role = "small" if "haiku" in model else "main"
    return Needs(
        role=role,
        tools=bool(body.get("tools")),
        vision=_has_images(body),
        est_tokens=estimate_tokens(body),
    )


class Router:
    def __init__(self, config: Config, store: StateStore, clock=time.time):
        self.config = config
        self.store = store
        self.clock = clock

    # ---- quota bookkeeping (local observations) -------------------------------------
    def _windows(self, h: Health, zone: str, now: float) -> None:
        h.minute_requests = [t for t in h.minute_requests if now - t < 60]
        h.minute_tokens = [x for x in h.minute_tokens if now - x[0] < 60]
        today = day_key(now, zone)
        if h.day != today:
            h.day, h.day_requests, h.day_tokens = today, 0, 0

    def quota_block(self, limits: dict[str, Any], h: Health, est_tokens: int, now: float) -> str:
        zone = limits.get("day_reset", "utc")
        self._windows(h, zone, now)
        if limits.get("rpm") and len(h.minute_requests) >= int(limits["rpm"]):
            return f"local count reached {limits['rpm']} requests/min"
        if limits.get("rpd") and h.day_requests >= int(limits["rpd"]):
            return f"local count reached {limits['rpd']} requests/day"
        if limits.get("tpm"):
            used = sum(x[1] for x in h.minute_tokens)
            if est_tokens > int(limits["tpm"]):
                return f"request (~{est_tokens} tokens) exceeds {limits['tpm']} tokens/min"
            if used + est_tokens > int(limits["tpm"]):
                return f"local count near {limits['tpm']} tokens/min"
        if limits.get("tpd") and h.day_tokens + est_tokens > int(limits["tpd"]):
            return f"local count near {limits['tpd']} tokens/day"
        return ""

    def record_success(self, cand: Candidate, tokens: int, reported: dict[str, Any] | None = None) -> None:
        now = self.clock()
        with self.store.lock:
            for key, limits in ((cand.provider.name, cand.provider.limits), (cand.model.key, cand.model.limits)):
                h = self.store.health(key)
                self._windows(h, limits.get("day_reset", cand.provider.limits.get("day_reset", "utc")), now)
                h.minute_requests.append(now)
                h.minute_tokens.append([now, tokens])
                h.day_requests += 1
                h.day_tokens += tokens
                h.consecutive_failures = 0
                h.last_ok = now
                if reported:
                    h.reported = {**reported, "seen_at": now}
            st = self.store.state
            if st.current_fallback != cand.model.key:
                st.current_fallback = cand.model.key
                st.current_since = now

    def record_failure(self, cand: Candidate, category: str, *, retry_after: float = 0.0,
                       reset_at: float = 0.0, daily: bool = False, detail: str = "") -> None:
        """Apply backoff. Daily quota -> provider cooldown until the provider's reset time."""
        now = self.clock()
        with self.store.lock:
            ph = self.store.health(cand.provider.name)
            mh = self.store.health(cand.model.key)
            mh.consecutive_failures += 1
            mh.last_error = f"{category}: {detail[:160]}"
            if category == "auth":
                ph.disabled_reason = "credential rejected (401/403); fix the key, then `ccfb reset`"
            elif category == "throttle":
                if daily:
                    zone = cand.provider.limits.get("day_reset", "utc")
                    until = max(reset_at, next_day_reset(now, zone))
                    ph.cooldown_until, ph.cooldown_reason = until, "daily quota reported exhausted"
                else:
                    wait = retry_after or (reset_at - now if reset_at > now else 0) or 60
                    ph.cooldown_until = max(ph.cooldown_until, now + min(wait, 3600))
                    ph.cooldown_reason = "rate limited (429)"
            elif category == "context_too_long":
                pass  # not a health problem; router moves on to a bigger model
            else:
                # outage / server / network / invalid response: exponential backoff on the model
                wait = min(30 * (2 ** (mh.consecutive_failures - 1)), 1800)
                mh.cooldown_until = now + wait
                mh.cooldown_reason = category
            if st_key := self.store.state.current_fallback:
                if st_key == cand.model.key and category != "context_too_long":
                    self.store.state.current_fallback = ""

    # ---- selection -------------------------------------------------------------------
    def candidates(self, needs: Needs) -> Decision:
        now = self.clock()
        fb = self.config.fallback
        preferred = list(fb.get("preferred_providers", []))
        excluded_models = set(fb.get("excluded_models", []))
        min_ctx = int(fb.get("min_context_tokens", 0))
        sticky_s = float(fb.get("sticky_minutes", 30)) * 60
        rejected: dict[str, str] = {}
        ranked: list[tuple[tuple, Candidate]] = []
        current = self.store.state.current_fallback
        sticky_ok = current and now - self.store.state.current_since < sticky_s

        for p in self.config.providers.values():
            for m in p.models:
                key = m.key
                if not p.enabled:
                    rejected[key] = "provider disabled"
                    continue
                if p.incompatible_reason:
                    rejected[key] = "incompatible: " + p.incompatible_reason.split(".")[0]
                    continue
                if p.name in fb.get("excluded_providers", []) or m.id in excluded_models or key in excluded_models:
                    rejected[key] = "excluded in config"
                    continue
                api_key = p.api_key(self.config.secrets)
                if not api_key:
                    rejected[key] = f"no credential ({p.key_env} not set)"
                    continue
                if needs.role not in m.roles and "main" not in m.roles:
                    rejected[key] = f"not configured for role '{needs.role}'"
                    continue
                if needs.tools and not m.tools:
                    rejected[key] = "request needs tool calling; model has none"
                    continue
                if needs.vision and not m.vision:
                    rejected[key] = "request contains images; model has no vision"
                    continue
                if m.context and m.context < min_ctx:
                    rejected[key] = f"context {m.context} < minimum {min_ctx}"
                    continue
                if m.context and needs.est_tokens > m.context * 0.9:
                    rejected[key] = f"request ~{needs.est_tokens} tokens exceeds context {m.context}"
                    continue
                with self.store.lock:
                    ph, mh = self.store.health(p.name), self.store.health(key)
                    if ph.disabled_reason:
                        rejected[key] = ph.disabled_reason
                        continue
                    for h in (ph, mh):
                        if h.cooldown_until > now:
                            rejected[key] = f"cooling down until {time.strftime('%H:%M:%S', time.localtime(h.cooldown_until))} ({h.cooldown_reason})"
                            break
                    else:
                        why = self.quota_block(p.limits, ph, needs.est_tokens, now) or \
                            self.quota_block(m.limits, mh, needs.est_tokens, now)
                        if why:
                            rejected[key] = why
                            continue
                        pref = preferred.index(p.name) if p.name in preferred else len(preferred)
                        role_fit = 0 if needs.role in m.roles else 1
                        sticky = 0 if (sticky_ok and key == current) else 1
                        ranked.append(((sticky, role_fit, pref, m.priority), Candidate(p, m, api_key)))
                        continue
        ranked.sort(key=lambda x: x[0])
        limit = int(fb.get("max_attempts", 4))
        return Decision([c for _, c in ranked][:limit], rejected)

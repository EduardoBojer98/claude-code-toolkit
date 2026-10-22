"""Load the provider registry, user overrides and secrets.

Precedence: repo registry (fallback/config/providers.toml) < user config
(~/.config/claude-fallback/config.toml) < environment variables for secrets.
"""

from __future__ import annotations

import copy
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from . import paths

ANTHROPIC_HOSTS = {"api.anthropic.com"}
VALID_KINDS = {"anthropic", "openai"}
VALID_ROLES = {"main", "small"}


class ConfigError(ValueError):
    pass


@dataclass
class Model:
    id: str
    provider: str
    context: int
    tools: bool
    vision: bool
    roles: list[str]
    priority: int
    source: str = ""
    context_verified: bool = True
    limits: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"{self.provider}/{self.id}"


@dataclass
class Provider:
    name: str
    kind: str
    base_url: str
    key_env: str
    enabled: bool
    free_kind: str
    limits: dict[str, Any]
    models: list[Model]
    static_key: str = ""
    privacy: str = ""
    signup: str = ""
    incompatible_reason: str = ""
    models_endpoint: str = ""

    def api_key(self, secrets: dict[str, str]) -> str:
        if self.static_key:
            return self.static_key
        if not self.key_env:
            return ""
        return os.environ.get(self.key_env) or secrets.get(self.key_env, "")

    @property
    def is_local(self) -> bool:
        host = urlparse(self.base_url).hostname or ""
        return host in {"127.0.0.1", "localhost", "::1"}


@dataclass
class Config:
    raw: dict[str, Any]
    providers: dict[str, Provider]
    secrets: dict[str, str]

    def section(self, name: str) -> dict[str, Any]:
        return self.raw.get(name, {})

    @property
    def fallback(self) -> dict[str, Any]:
        return self.section("fallback")

    @property
    def recovery(self) -> dict[str, Any]:
        return self.section("recovery")

    @property
    def gateway(self) -> dict[str, Any]:
        return self.section("gateway")

    @property
    def claude_upstream(self) -> str:
        return self.section("claude").get("upstream", "https://api.anthropic.com").rstrip("/")

    def usable_providers(self) -> list[Provider]:
        """Enabled, compatible providers that have the credential they need."""
        out = []
        excluded = set(self.fallback.get("excluded_providers", []))
        for p in self.providers.values():
            if not p.enabled or p.incompatible_reason or p.name in excluded:
                continue
            if not p.api_key(self.secrets):
                continue
            out.append(p)
        return out


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def parse_env_file(path: Path) -> dict[str, str]:
    """Minimal KEY=VALUE parser (no interpolation). Missing file -> {}."""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def _build_provider(name: str, data: dict[str, Any]) -> Provider:
    kind = data.get("kind", "")
    if kind not in VALID_KINDS:
        raise ConfigError(f"provider '{name}': kind must be one of {sorted(VALID_KINDS)}")
    base_url = str(data.get("base_url", "")).rstrip("/")
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ConfigError(f"provider '{name}': base_url must be an http(s) URL")
    if parsed.scheme == "http" and parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ConfigError(f"provider '{name}': plain http is only allowed for local servers")
    limits = dict(data.get("limits", {}))
    models = []
    for m in data.get("models", []):
        if "id" not in m:
            raise ConfigError(f"provider '{name}': every model needs an id")
        roles = list(m.get("roles", ["main"]))
        bad = set(roles) - VALID_ROLES
        if bad:
            raise ConfigError(f"model '{m['id']}': unknown roles {sorted(bad)}")
        models.append(
            Model(
                id=m["id"],
                provider=name,
                context=int(m.get("context", 0)),
                tools=bool(m.get("tools", False)),
                vision=bool(m.get("vision", False)),
                roles=roles,
                priority=int(m.get("priority", 100)),
                source=str(m.get("source", "")),
                context_verified=bool(m.get("context_verified", True)),
                limits=dict(m.get("limits", {})),
            )
        )
    return Provider(
        name=name,
        kind=kind,
        base_url=base_url,
        key_env=str(data.get("key_env", "")),
        enabled=bool(data.get("enabled", False)),
        free_kind=str(data.get("free_kind", "free-tier")),
        limits=limits,
        models=models,
        static_key=str(data.get("static_key", "")),
        privacy=str(data.get("privacy", "")),
        signup=str(data.get("signup", "")),
        incompatible_reason=str(data.get("incompatible_reason", "")),
        models_endpoint=str(data.get("models_endpoint", "")),
    )


def validate(raw: dict[str, Any]) -> None:
    upstream = raw.get("claude", {}).get("upstream", "https://api.anthropic.com")
    host = urlparse(upstream).hostname
    if urlparse(upstream).scheme != "https" or host not in ANTHROPIC_HOSTS:
        # The subscription's OAuth token is only ever sent to Anthropic.
        raise ConfigError("claude.upstream must be https://api.anthropic.com")
    gw = raw.get("gateway", {})
    if gw.get("host", "127.0.0.1") not in {"127.0.0.1", "localhost", "::1"}:
        raise ConfigError("gateway.host must be a loopback address; the gateway must not be reachable from the network")
    mode = raw.get("recovery", {}).get("mode", "auto")
    if mode not in {"auto", "manual"}:
        raise ConfigError("recovery.mode must be 'auto' or 'manual'")


def load(registry_path: Path | None = None, user_path: Path | None = None,
         secrets_path: Path | None = None) -> Config:
    registry_path = registry_path or paths.default_registry()
    user_path = user_path or paths.user_config_file()
    secrets_path = secrets_path or paths.secrets_file()
    with open(registry_path, "rb") as fh:
        raw = tomllib.load(fh)
    if user_path.exists():
        with open(user_path, "rb") as fh:
            raw = deep_merge(raw, tomllib.load(fh))
    validate(raw)
    providers = {name: _build_provider(name, data) for name, data in raw.get("providers", {}).items()}
    return Config(raw=raw, providers=providers, secrets=parse_env_file(secrets_path))

"""Prepare a Claude Code request for a non-Anthropic provider.

- Remove Claude-only request fields and blocks that other providers reject or can't verify
  (thinking signatures, context management, output config, server tools, beta tool fields).
- Optionally mask obvious secrets so they are not sent to a free provider. This is a
  pattern match on well-known key formats, not a guarantee; see README "Privacy".
"""

from __future__ import annotations

import copy
import re
from typing import Any

DROP_BODY_FIELDS = {"context_management", "output_config", "container", "mcp_servers",
                    "service_tier", "thinking", "metadata", "betas"}
DROP_TOOL_FIELDS = {"defer_loading", "strict", "cache_control", "eager_input_streaming", "input_examples"}
DROP_BLOCK_TYPES = {"thinking", "redacted_thinking", "server_tool_use", "web_search_tool_result",
                    "web_fetch_tool_result", "code_execution_tool_result", "mcp_tool_use",
                    "mcp_tool_result", "container_upload", "tool_reference"}

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]+?-----END [A-Z ]*PRIVATE KEY-----")),
    ("anthropic-key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("openai-style-key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_\-]{20,}")),
    ("openrouter-key", re.compile(r"\bsk-or-[A-Za-z0-9_\-]{20,}")),
    ("github-token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{40,}")),
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("slack-token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("stripe-key", re.compile(r"\b(?:sk|rk)_live_[A-Za-z0-9]{20,}")),
    ("groq-key", re.compile(r"\bgsk_[A-Za-z0-9]{40,}")),
    ("bearer-token", re.compile(r"(?i)(authorization:\s*bearer\s+)[A-Za-z0-9._\-]{20,}")),
    ("env-secret", re.compile(r"(?im)^((?:[A-Z0-9_]*(?:SECRET|PASSWORD|PASSWD|TOKEN|API_KEY|PRIVATE_KEY)[A-Z0-9_]*)\s*=\s*)(\S{6,})$")),
]


def redact_text(text: str, counter: dict[str, int]) -> str:
    for name, pattern in SECRET_PATTERNS:
        def repl(m: re.Match[str], name: str = name) -> str:
            counter[name] = counter.get(name, 0) + 1
            if name in {"bearer-token", "env-secret"}:
                return m.group(1) + f"[REDACTED:{name}]"
            return f"[REDACTED:{name}]"
        text = pattern.sub(repl, text)
    return text


def _redact_any(value: Any, counter: dict[str, int]) -> Any:
    if isinstance(value, str):
        return redact_text(value, counter)
    if isinstance(value, list):
        return [_redact_any(v, counter) for v in value]
    if isinstance(value, dict):
        # never touch base64 image payloads or ids
        return {k: (v if k in {"data", "id", "tool_use_id", "media_type", "type"} else _redact_any(v, counter))
                for k, v in value.items()}
    return value


def _clean_content(content: Any) -> Any:
    if not isinstance(content, list):
        return content
    out = []
    for block in content:
        if not isinstance(block, dict):
            out.append(block)
            continue
        if block.get("type") in DROP_BLOCK_TYPES:
            continue
        block = {k: v for k, v in block.items() if k != "cache_control"}
        if block.get("type") == "tool_result" and isinstance(block.get("content"), list):
            block["content"] = _clean_content(block["content"])
        out.append(block)
    return out


def for_third_party(body: dict[str, Any], *, redact: bool) -> tuple[dict[str, Any], dict[str, int]]:
    """Return a cleaned copy and a count of redactions by kind."""
    clean = {k: copy.deepcopy(v) for k, v in body.items() if k not in DROP_BODY_FIELDS}
    clean["messages"] = []
    for msg in body.get("messages", []):
        content = _clean_content(copy.deepcopy(msg.get("content")))
        if isinstance(content, list) and not content:
            content = [{"type": "text", "text": "(content omitted: not supported by fallback model)"}]
        clean["messages"].append({"role": msg.get("role"), "content": content})
    if isinstance(clean.get("system"), list):
        clean["system"] = [{k: v for k, v in b.items() if k != "cache_control"}
                           for b in clean["system"] if isinstance(b, dict)]
    tools = []
    for tool in clean.get("tools", []) or []:
        if "input_schema" not in tool:      # Anthropic server tools (web search etc.)
            continue
        tools.append({k: v for k, v in tool.items() if k not in DROP_TOOL_FIELDS})
    if tools:
        clean["tools"] = tools
    else:
        clean.pop("tools", None)
        clean.pop("tool_choice", None)
    counter: dict[str, int] = {}
    if redact:
        clean["messages"] = _redact_any(clean["messages"], counter)
        if "system" in clean:
            clean["system"] = _redact_any(clean["system"], counter)
    return clean, counter

"""Test doubles: scripted fake upstream servers and a gateway wired to them."""

from __future__ import annotations

import http.client
import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ccfb import config as cfgmod  # noqa: E402
from ccfb.gateway import Gateway, make_server  # noqa: E402
from ccfb.state import StateStore  # noqa: E402


class Clock:
    def __init__(self, t: float = 1_800_000_000.0):
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


class Scripted:
    """A response the fake server will send: status, headers, body or SSE chunks."""

    def __init__(self, status: int = 200, body: Any = None, headers: dict[str, str] | None = None,
                 sse: list[bytes] | None = None):
        self.status, self.body, self.headers, self.sse = status, body, headers or {}, sse


class FakeServer:
    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.queue: list[Scripted] = []
        self.default: Scripted | Callable[[dict[str, Any]], Scripted] = Scripted(200, {"ok": True})
        outer = self

        class H(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *a: Any) -> None:
                pass

            def _handle(self) -> None:
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length) if length else b""
                req = {"method": self.command, "path": self.path, "headers": dict(self.headers), "raw": raw}
                try:
                    req["json"] = json.loads(raw) if raw else None
                except ValueError:
                    req["json"] = None
                outer.requests.append(req)
                script = outer.queue.pop(0) if outer.queue else outer.default
                if callable(script):
                    script = script(req)
                self.send_response(script.status)
                for k, v in script.headers.items():
                    self.send_header(k, v)
                if script.sse is not None:
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Transfer-Encoding", "chunked")
                    self.end_headers()
                    for chunk in script.sse:
                        self.wfile.write(f"{len(chunk):x}\r\n".encode() + chunk + b"\r\n")
                    self.wfile.write(b"0\r\n\r\n")
                    return
                payload = script.body if isinstance(script.body, bytes) else json.dumps(script.body).encode()
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_POST = do_GET = _handle

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.server.daemon_threads = True
        self.port = self.server.server_address[1]
        self.url = f"http://127.0.0.1:{self.port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


def anthropic_ok(text: str = "hello from claude") -> dict[str, Any]:
    return {"id": "msg_1", "type": "message", "role": "assistant", "model": "claude-sonnet-5",
            "content": [{"type": "text", "text": text}], "stop_reason": "end_turn",
            "stop_sequence": None, "usage": {"input_tokens": 10, "output_tokens": 3}}


def openai_ok(text: str = "hello from free model", tool: dict[str, Any] | None = None) -> dict[str, Any]:
    msg: dict[str, Any] = {"role": "assistant", "content": text}
    if tool:
        msg["tool_calls"] = [{"id": "call_1", "type": "function",
                              "function": {"name": tool["name"], "arguments": json.dumps(tool["input"])}}]
    return {"id": "x", "object": "chat.completion", "choices": [{"index": 0, "message": msg,
            "finish_reason": "tool_calls" if tool else "stop"}], "usage": {"prompt_tokens": 50, "completion_tokens": 7}}


LIMIT_HEADERS = {"anthropic-ratelimit-unified-status": "rejected",
                 "anthropic-ratelimit-unified-reset": "1800018000"}   # Clock() + 5h


def limit_429() -> Scripted:
    return Scripted(429, {"type": "error", "error": {"type": "rate_limit_error",
                                                     "message": "You've hit your session limit"}}, LIMIT_HEADERS)


class Env:
    """Isolated config/state dirs, fake Claude + two fake providers, and a running gateway."""

    def __init__(self, provider_keys: bool = True, extra_toml: str = "", heartbeat: float = 15.0):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.config_dir, self.state_dir, self.home = base / "config", base / "state", base / "home"
        for d in (self.config_dir, self.state_dir, self.home / ".claude" / "projects"):
            d.mkdir(parents=True)
        self._old_env = {k: os.environ.get(k) for k in ("CCFB_CONFIG_DIR", "CCFB_STATE_DIR", "CLAUDE_CONFIG_DIR",
                                                        "OPENROUTER_API_KEY", "GEMINI_API_KEY")}
        os.environ["CCFB_CONFIG_DIR"] = str(self.config_dir)
        os.environ["CCFB_STATE_DIR"] = str(self.state_dir)
        os.environ["CLAUDE_CONFIG_DIR"] = str(self.home / ".claude")
        os.environ.pop("OPENROUTER_API_KEY", None)
        os.environ.pop("GEMINI_API_KEY", None)

        self.claude = FakeServer()
        self.claude.default = Scripted(200, anthropic_ok())
        self.anthro = FakeServer()      # Anthropic-compatible free provider (like OpenRouter)
        self.anthro.default = Scripted(200, anthropic_ok("hello from anthropic-compatible free model"))
        self.oai = FakeServer()         # OpenAI-compatible free provider (like Gemini)
        self.oai.default = Scripted(200, openai_ok())

        toml = f"""
[fallback]
preferred_providers = ["freeanthro", "freeoai"]
min_context_tokens = 1000
[recovery]
probe_interval_minutes = 15
[providers.openrouter]
enabled = false
[providers.gemini]
enabled = false
[providers.freeanthro]
kind = "anthropic"
base_url = "{self.anthro.url}"
key_env = "FREEANTHRO_KEY"
enabled = true
limits = {{ rpm = 20, rpd = 50, day_reset = "utc" }}
[[providers.freeanthro.models]]
id = "free/coder:free"
context = 200000
tools = true
vision = false
roles = ["main", "small"]
priority = 10
[providers.freeoai]
kind = "openai"
base_url = "{self.oai.url}"
key_env = "FREEOAI_KEY"
enabled = true
limits = {{ rpm = 10, day_reset = "pacific" }}
[[providers.freeoai.models]]
id = "oai-flash"
context = 1000000
tools = true
vision = true
roles = ["main", "small"]
priority = 20
{extra_toml}
"""
        (self.config_dir / "config.toml").write_text(toml)
        if provider_keys:
            (self.config_dir / ".env").write_text("FREEANTHRO_KEY=sk-free-anthro-key-123456\nFREEOAI_KEY=free-oai-key-abcdef\n")
        self.clock = Clock()
        self.cfg = cfgmod.load()
        self.cfg.raw["claude"]["upstream"] = self.claude.url     # tests only: real config must be api.anthropic.com
        self.store = StateStore(self.state_dir / "state.json", clock=self.clock)
        self.gateway = Gateway(self.cfg, self.store, clock=self.clock, heartbeat_seconds=heartbeat)
        self.server = make_server(self.gateway, port=0)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def post(self, body: dict[str, Any], headers: dict[str, str] | None = None,
             path: str = "/v1/messages?beta=true") -> tuple[int, dict[str, str], bytes]:
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        h = {"Content-Type": "application/json", "Authorization": "Bearer oauth-subscription-token",
             "anthropic-beta": "oauth-2025-04-20,fine-grained-tool-streaming",
             "anthropic-version": "2023-06-01", "x-claude-code-session-id": "sess-123"}
        h.update(headers or {})
        conn.request("POST", path, body=json.dumps(body), headers=h)
        resp = conn.getresponse()
        data = resp.read()
        hdrs = {k.lower(): v for k, v in resp.getheaders()}
        conn.close()
        return resp.status, hdrs, data

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        for s in (self.claude, self.anthro, self.oai):
            s.close()
        for k, v in self._old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.tmp.cleanup()


def user_turn(text: str = "please fix the bug", tools: bool = True, stream: bool = False,
              model: str = "claude-sonnet-5") -> dict[str, Any]:
    body: dict[str, Any] = {"model": model, "max_tokens": 1024, "stream": stream,
                            "system": [{"type": "text", "text": "You are Claude Code."}],
                            "messages": [{"role": "user", "content": [{"type": "text", "text": text}]}]}
    if tools:
        body["tools"] = [{"name": "Read", "description": "Read a file",
                          "input_schema": {"$schema": "http://json-schema.org/draft-07/schema#", "type": "object",
                                           "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]}}]
    return body


def tool_result_turn() -> dict[str, Any]:
    body = user_turn()
    body["messages"] += [
        {"role": "assistant", "content": [{"type": "thinking", "thinking": "hmm", "signature": "sig"},
                                          {"type": "tool_use", "id": "toolu_1", "name": "Read", "input": {"file_path": "a.py"}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_1", "content": "print('hi')"}]},
    ]
    return body

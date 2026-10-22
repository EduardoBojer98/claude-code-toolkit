"""The local gateway Claude Code talks to (ANTHROPIC_BASE_URL=http://127.0.0.1:<port>).

Claude mode (default): every request is relayed to https://api.anthropic.com unchanged,
including the claude.ai login's Authorization and anthropic-beta headers, as documented in
code.claude.com/docs/en/llm-gateway ("Subscriptions and gateways"). Responses stream back
byte for byte.

Fallback mode: entered only when Claude answers 429 *with* unified quota headers (a plan
limit). That 429 is not shown to Claude Code; the same request is answered by the best
eligible free model instead, so the session continues with its full history. Claude is
retried with a real request at most once per probe interval, never before the reported
reset time, and by default only at the start of a new user turn.
"""

from __future__ import annotations

import gzip
import json
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from . import __version__, classify, handoff, paths, sanitize, translate, upstream
from .config import Config
from .router import Candidate, Router, needs_for
from .state import MODE_CLAUDE, MODE_FALLBACK, StateStore

log = logging.getLogger("ccfb")

HOP_BY_HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te",
              "trailers", "transfer-encoding", "upgrade", "host", "content-length"}
PING = b'event: ping\ndata: {"type":"ping"}\n\n'
DEFAULT_NOTE = ("You are running inside Claude Code as a fallback model because the user's Claude "
                "usage limit was reached. Follow the tool schemas exactly, call one tool at a time "
                "when unsure, never invent file contents, and keep answers concise.")


def _new_user_turn(body: dict[str, Any]) -> bool:
    msgs = body.get("messages") or []
    if not msgs or msgs[-1].get("role") != "user":
        return False
    content = msgs[-1].get("content")
    if isinstance(content, str):
        return True
    return not any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content or [])


class Gateway:
    def __init__(self, config: Config, store: StateStore | None = None, clock=time.time,
                 heartbeat_seconds: float = 15.0):
        self.config = config
        self.clock = clock
        self.store = store or StateStore(clock=clock)
        self.router = Router(config, self.store, clock)
        self.heartbeat = heartbeat_seconds
        self.started_at = clock()
        self._probe_lock = threading.Lock()

    # ---------------------------------------------------------------- settings
    @property
    def fb(self) -> dict[str, Any]:
        return self.config.fallback

    def _timeouts(self) -> dict[str, float]:
        return {"connect_timeout": float(self.fb.get("connect_timeout_seconds", 15)),
                "read_timeout": float(self.fb.get("request_timeout_seconds", 300))}

    # ---------------------------------------------------------------- status
    def status(self) -> dict[str, Any]:
        st = self.store.state
        now = self.clock()
        providers = {}
        for p in self.config.providers.values():
            h = self.store.health(p.name)
            reason = ""
            if not p.enabled:
                reason = "disabled"
            elif p.incompatible_reason:
                reason = "incompatible"
            elif not p.api_key(self.config.secrets):
                reason = f"missing {p.key_env}"
            elif h.disabled_reason:
                reason = h.disabled_reason
            elif h.cooldown_until > now:
                reason = f"cooldown {int(h.cooldown_until - now)}s ({h.cooldown_reason})"
            providers[p.name] = {
                "state": reason or "ready",
                "free_kind": p.free_kind,
                "today_requests_observed": h.day_requests,
                "reported": {k: v for k, v in h.reported.items() if "remaining" in k or k == "seen_at"},
            }
        return {
            "version": __version__,
            "mode": st.mode,
            "mode_since": st.mode_since,
            "last_switch_reason": st.last_switch_reason,
            "waiting_for_claude": st.mode == MODE_FALLBACK,
            "claude_reset_at": st.claude_reset_at or None,
            "next_claude_check_at": st.next_probe_at or None,
            "manual_hold": st.manual_hold,
            "current_fallback": st.current_fallback or None,
            "last_route": st.last_route,
            "fallback_enabled": bool(self.fb.get("enabled", True)),
            "recovery_mode": self.config.recovery.get("mode", "auto"),
            "providers": providers,
            "recent_events": st.events[-10:],
        }

    # ---------------------------------------------------------------- state transitions
    def _enter_fallback(self, verdict: classify.Verdict, session_id: str) -> None:
        now = self.clock()
        interval = float(self.config.recovery.get("probe_interval_minutes", 15)) * 60
        with self.store.lock:
            st = self.store.state
            if verdict.reset_at:
                st.claude_reset_at, st.claude_reset_source = verdict.reset_at, "Anthropic response headers"
            st.next_probe_at = max(now + interval, (verdict.reset_at + 30) if verdict.reset_at else 0)
            reason = "Claude usage limit (429 with quota headers)"
            if verdict.detail:
                reason += f": {verdict.detail[:120]}"
            self.store.set_mode(MODE_FALLBACK, reason)
        log.warning("switched to fallback: %s; next Claude check %s", reason,
                    time.strftime("%H:%M", time.localtime(self.store.state.next_probe_at)))
        if session_id:
            threading.Thread(target=self._write_handoff, args=(session_id, reason), daemon=True).start()

    def _write_handoff(self, session_id: str, reason: str) -> None:
        try:
            path = handoff.write_handoff(session_id, reason)
            if path:
                self.store.event("handoff", session=session_id, file=str(path))
                self.store.save()
        except Exception as exc:  # a handoff must never break routing
            log.debug("handoff failed: %s", exc)

    def _should_probe(self, body: dict[str, Any]) -> bool:
        st = self.store.state
        rec = self.config.recovery
        if st.manual_hold or rec.get("mode", "auto") != "auto":
            return False
        if self.clock() < st.next_probe_at:
            return False
        if rec.get("turn_boundary_only", True) and not _new_user_turn(body):
            return False
        return True

    def _probe_failed(self, verdict: classify.Verdict | None) -> None:
        now = self.clock()
        interval = float(self.config.recovery.get("probe_interval_minutes", 15)) * 60
        with self.store.lock:
            st = self.store.state
            if verdict and verdict.reset_at:
                st.claude_reset_at = verdict.reset_at
            st.next_probe_at = max(now + interval, (st.claude_reset_at + 30) if st.claude_reset_at > now else 0)
            self.store.event("claude_check", result=verdict.category if verdict else "network_error")
            self.store.save()

    # ---------------------------------------------------------------- Claude pass-through
    def _claude_headers(self, headers: dict[str, str], body_len: int) -> dict[str, str]:
        out = {k: v for k, v in headers.items() if k.lower() not in HOP_BY_HOP}
        out["Content-Length"] = str(body_len)
        return out

    def call_claude(self, method: str, path: str, headers: dict[str, str], body: bytes) -> upstream.Response:
        url = self.config.claude_upstream + path
        return upstream.request(method, url, self._claude_headers(headers, len(body)), body or None,
                                **self._timeouts())

    # ---------------------------------------------------------------- free providers
    def _provider_request(self, cand: Candidate, body: dict[str, Any], stream: bool) -> tuple[str, dict[str, str], bytes]:
        redact = bool(self.fb.get("redact_secrets", True))
        clean, redacted = sanitize.for_third_party(body, redact=redact)
        if redacted:
            log.info("masked %s secret-looking value(s) before sending to %s", sum(redacted.values()), cand.provider.name)
        note = self.fb.get("system_note", DEFAULT_NOTE)
        headers = {"Content-Type": "application/json", "Accept": "text/event-stream" if stream else "application/json"}
        if cand.api_key:
            headers["Authorization"] = f"Bearer {cand.api_key}"
        if cand.provider.kind == "anthropic":
            clean["model"] = cand.model.id
            clean["stream"] = stream
            if note:
                system = clean.get("system")
                if isinstance(system, list):
                    clean["system"] = [{"type": "text", "text": note}] + system
                else:
                    clean["system"] = (note + "\n\n" + (system or "")).strip()
            headers["anthropic-version"] = "2023-06-01"
            return cand.provider.base_url + "/v1/messages", headers, json.dumps(clean).encode()
        req = translate.to_openai_request(clean, cand.model.id, stream=stream, system_note=note,
                                          include_usage=bool(cand.provider.limits.get("stream_usage", False)))
        return cand.provider.base_url + "/chat/completions", headers, json.dumps(req).encode()

    def serve_fallback(self, handler: "Handler", body: dict[str, Any], session_id: str) -> None:
        needs = needs_for(body)
        stream = bool(body.get("stream"))
        decision = self.router.candidates(needs)
        reply_model = str(body.get("model", "claude"))
        failures: list[str] = []
        for cand in decision.candidates:
            url, headers, payload = self._provider_request(cand, body, stream)
            started = self.clock()
            try:
                resp = upstream.request("POST", url, headers, payload, **self._timeouts())
            except upstream.NetworkError as exc:
                self.router.record_failure(cand, classify.NETWORK, detail=str(exc))
                failures.append(f"{cand.model.key}: network error")
                log.info("fallback %s network error", cand.model.key)
                continue
            if resp.status != 200:
                raw = resp.read_all(65536)
                verdict = classify.classify_provider(resp.status, resp.header_map(), raw, self.clock())
                self.router.record_failure(cand, verdict.category, retry_after=verdict.retry_after,
                                           reset_at=verdict.reset_at, daily=verdict.daily, detail=verdict.detail)
                failures.append(f"{cand.model.key}: {verdict.category} ({resp.status})")
                log.info("fallback %s -> %s %s", cand.model.key, resp.status, verdict.category)
                self.store.save()
                continue
            reported = {k: v for k, v in resp.header_map().items() if k.startswith("x-ratelimit")}
            out_tokens = self._relay_provider(handler, cand, resp, stream, reply_model, needs.est_tokens)
            self.router.record_success(cand, needs.est_tokens + out_tokens, reported)
            with self.store.lock:
                self.store.state.last_route = {
                    "provider": cand.provider.name, "model": cand.model.id, "role": needs.role,
                    "at": round(self.clock(), 1), "seconds": round(self.clock() - started, 2),
                    "skipped": failures[:5],
                }
            self.store.save()
            log.info("served by %s in %.1fs", cand.model.key, self.clock() - started)
            return
        quiet = ("provider disabled", "incompatible", "excluded in config")
        reasons = failures + [f"{k}: {v}" for k, v in decision.rejected.items() if not v.startswith(quiet)]
        if not reasons:
            reasons = ["no free provider is enabled in the ccfb config"]
        st = self.store.state
        when = time.strftime("%a %H:%M", time.localtime(st.claude_reset_at)) if st.claude_reset_at else "unknown"
        hint = " Run `ccfb doctor` to see what's missing." if any("no credential" in r for r in reasons) else ""
        msg = (f"Claude usage limit reached (resets {when}) and no free fallback model could take this request."
               f"{hint} Details: " + "; ".join(reasons[:10]))
        self.store.event("no_fallback", reasons=reasons[:10])
        self.store.save()
        log.warning("no fallback available: %s", "; ".join(reasons[:5]))
        handler.send_json(429, translate.anthropic_error(msg), extra={"x-should-retry": "false"})

    def _relay_provider(self, handler: "Handler", cand: Candidate, resp: upstream.Response, stream: bool,
                        reply_model: str, est_input: int) -> int:
        """Send a successful provider response to Claude Code. Returns output tokens (best known)."""
        if not stream:
            raw = resp.read_all()
            data = json.loads(raw.decode("utf-8", "replace"))
            if cand.provider.kind == "openai":
                data = translate.from_openai_response(data, reply_model, est_input)
            else:
                data["model"] = reply_model
            handler.send_json(200, json.dumps(data).encode())
            return int((data.get("usage") or {}).get("output_tokens") or 0)

        handler.start_stream(200, {"Content-Type": "text/event-stream", "Cache-Control": "no-cache"})
        out_tokens = 0
        try:
            if cand.provider.kind == "anthropic":
                at_boundary = True
                for line in upstream.with_heartbeat(resp.iter_lines(), self.heartbeat):
                    if line is None:
                        if at_boundary:
                            handler.write_chunk(PING)
                        continue
                    handler.write_chunk(line)
                    at_boundary = line.strip() == b""
                    if line.startswith(b"data:") and b'"output_tokens"' in line:
                        try:
                            out_tokens = int(json.loads(line[5:]).get("usage", {}).get("output_tokens") or out_tokens)
                        except (ValueError, AttributeError):
                            pass
            else:
                tr = translate.StreamTranslator(reply_model, est_input)
                for line in upstream.with_heartbeat(resp.iter_lines(), self.heartbeat):
                    if line is None:
                        handler.write_chunk(PING)
                        continue
                    text = line.decode("utf-8", "replace").strip()
                    if not text.startswith("data:"):
                        continue
                    payload = text[5:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                    except ValueError:
                        continue
                    if "error" in chunk:
                        raise upstream.NetworkError(str(chunk["error"])[:200])
                    for event in tr.feed(chunk):
                        handler.write_chunk(event)
                for event in tr.finish_stream():
                    handler.write_chunk(event)
                out_tokens = tr.output_tokens
        except (upstream.NetworkError, OSError) as exc:
            log.info("stream from %s broke: %s", cand.model.key, exc)
            try:
                handler.write_chunk(translate.StreamTranslator.error_event(
                    f"Fallback model {cand.model.key} stopped mid-response: {exc}", "overloaded_error"))
            except OSError:
                pass
            self.router.record_failure(cand, classify.SERVER, detail=str(exc))
        finally:
            handler.end_stream()
        return out_tokens

    # ---------------------------------------------------------------- request entry points
    def handle_messages(self, handler: "Handler", path: str, raw_body: bytes) -> None:
        headers = handler.header_dict()
        session_id = headers.get("x-claude-code-session-id", "")
        try:
            body = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except ValueError:
            body = {}
        enabled = bool(self.fb.get("enabled", True))
        st = self.store.state

        if st.mode == MODE_FALLBACK and enabled:
            if not self._should_probe(body):
                return self.serve_fallback(handler, body, session_id)
            # Only one request may check Claude per interval: reserve the slot first so
            # concurrent requests keep using the fallback instead of piling onto Claude.
            with self._probe_lock:
                if self.store.state.mode == MODE_FALLBACK and self.clock() < self.store.state.next_probe_at:
                    return self.serve_fallback(handler, body, session_id)
                probing = self.store.state.mode == MODE_FALLBACK
                if probing:
                    interval = float(self.config.recovery.get("probe_interval_minutes", 15)) * 60
                    self.store.state.next_probe_at = self.clock() + interval
            if probing:
                try:
                    resp = self.call_claude("POST", path, headers, raw_body)
                except upstream.NetworkError as exc:
                    log.info("Claude check: network error %s", exc)
                    self._probe_failed(None)
                    return self.serve_fallback(handler, body, session_id)
                if resp.status == 429:
                    raw = resp.read_all(65536)
                    verdict = classify.classify_claude(429, resp.header_map(), _decoded(resp, raw), self.clock())
                    self._probe_failed(verdict)
                    return self.serve_fallback(handler, body, session_id)
                if resp.status in (401, 403):
                    # Not a usage limit: let Claude Code show the real login problem.
                    self.store.set_mode(MODE_CLAUDE, "Claude check returned an authentication error")
                    return handler.relay_upstream(resp)
                if resp.status >= 500:
                    self._probe_failed(classify.Verdict(classify.SERVER, resp.status))
                    resp.close()
                    return self.serve_fallback(handler, body, session_id)
                with self.store.lock:
                    self.store.state.claude_reset_at = 0.0
                    self.store.state.current_fallback = ""
                self.store.set_mode(MODE_CLAUDE, "Claude answered again (recovered)")
                log.warning("Claude is available again; back to normal routing")
                return handler.relay_upstream(resp)

        # Claude mode (or fallback disabled): relay, intercepting only plan-limit 429s.
        try:
            resp = self.call_claude("POST", path, headers, raw_body)
        except upstream.NetworkError as exc:
            # A network problem is not a usage limit: report it, never fall back or retry here.
            log.info("Claude unreachable: %s", exc)
            return handler.send_json(502, translate.anthropic_error(
                f"ccfb gateway could not reach Anthropic: {exc}", "api_error"))
        if resp.status == 429 and enabled:
            raw = resp.read_all(65536)
            verdict = classify.classify_claude(429, resp.header_map(), _decoded(resp, raw), self.clock())
            if verdict.category == classify.USAGE_LIMIT:
                self._enter_fallback(verdict, session_id)
                return self.serve_fallback(handler, body, session_id)
            return handler.send_raw(resp.status, resp.headers, raw)
        return handler.relay_upstream(resp)

    def handle_count_tokens(self, handler: "Handler", path: str, raw_body: bytes) -> None:
        if self.store.state.mode == MODE_FALLBACK and self.fb.get("enabled", True):
            try:
                body = json.loads(raw_body.decode("utf-8"))
            except ValueError:
                body = {}
            from .router import estimate_tokens
            return handler.send_json(200, json.dumps({"input_tokens": estimate_tokens(body)}).encode())
        return self.passthrough(handler, "POST", path, raw_body)

    def passthrough(self, handler: "Handler", method: str, path: str, raw_body: bytes) -> None:
        try:
            resp = self.call_claude(method, path, handler.header_dict(), raw_body)
        except upstream.NetworkError as exc:
            return handler.send_json(502, translate.anthropic_error(f"ccfb gateway could not reach Anthropic: {exc}", "api_error"))
        return handler.relay_upstream(resp)


def _decoded(resp: upstream.Response, raw: bytes) -> bytes:
    if resp.header_map().get("content-encoding", "") == "gzip":
        try:
            return gzip.decompress(raw)
        except OSError:
            return b""
    return raw


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "ccfb/" + __version__
    gateway: Gateway  # set on the subclass by make_server

    # --- plumbing ---
    def log_message(self, fmt: str, *args: Any) -> None:  # silence default stderr access log
        log.debug("http %s", fmt % args)

    def header_dict(self) -> dict[str, str]:
        return {k: v for k, v in self.headers.items()}

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length) if length else b""

    def send_json(self, status: int, payload: bytes, extra: dict[str, str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(payload)

    def send_raw(self, status: int, headers: list[tuple[str, str]], payload: bytes) -> None:
        self.send_response(status)
        for k, v in headers:
            if k.lower() not in HOP_BY_HOP:
                self.send_header(k, v)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def start_stream(self, status: int, headers: dict[str, str] | list[tuple[str, str]]) -> None:
        self.send_response(status)
        items = headers.items() if isinstance(headers, dict) else headers
        for k, v in items:
            if k.lower() not in HOP_BY_HOP:
                self.send_header(k, v)
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()

    def write_chunk(self, data: bytes) -> None:
        if data:
            self.wfile.write(f"{len(data):x}\r\n".encode() + data + b"\r\n")
            self.wfile.flush()

    def end_stream(self) -> None:
        try:
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
        except OSError:
            pass

    def relay_upstream(self, resp: upstream.Response) -> None:
        self.start_stream(resp.status, resp.headers)
        try:
            for chunk in resp.iter_raw():
                self.write_chunk(chunk)
        except OSError:
            pass
        finally:
            self.end_stream()

    # --- routes ---
    def do_HEAD(self) -> None:
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            return self.send_json(200, json.dumps({"ok": True, "version": __version__}).encode())
        if path == "/status":
            return self.send_json(200, json.dumps(self.gateway.status(), indent=2).encode())
        return self.gateway.passthrough(self, "GET", self.path, b"")

    def do_POST(self) -> None:
        body = self._read_body()
        path = urlparse(self.path).path
        if path == "/v1/messages":
            return self.gateway.handle_messages(self, self.path, body)
        if path == "/v1/messages/count_tokens":
            return self.gateway.handle_count_tokens(self, self.path, body)
        if path == "/ccfb/resume":
            with self.gateway.store.lock:
                self.gateway.store.state.manual_hold = False
                self.gateway.store.state.next_probe_at = 0
            self.gateway.store.set_mode(MODE_CLAUDE, "manual resume (ccfb resume)")
            return self.send_json(200, b'{"ok":true}')
        if path == "/ccfb/use-fallback":
            with self.gateway.store.lock:
                self.gateway.store.state.manual_hold = True
            self.gateway.store.set_mode(MODE_FALLBACK, "manual switch (ccfb use-fallback)")
            return self.send_json(200, b'{"ok":true}')
        if path == "/ccfb/reset":
            with self.gateway.store.lock:
                self.gateway.store.state.health = {}
            self.gateway.store.save()
            return self.send_json(200, b'{"ok":true}')
        return self.gateway.passthrough(self, "POST", self.path, body)


def check_no_loop(config: Config) -> None:
    gw = config.gateway
    me = (gw.get("host", "127.0.0.1"), int(gw.get("port", 8787)))
    for p in config.providers.values():
        u = urlparse(p.base_url)
        port = u.port or (443 if u.scheme == "https" else 80)
        if (u.hostname in {"127.0.0.1", "localhost"} and port == me[1]):
            raise ValueError(f"provider '{p.name}' points at the gateway itself; that would loop")


def make_server(gateway: Gateway, host: str | None = None, port: int | None = None) -> ThreadingHTTPServer:
    check_no_loop(gateway.config)
    gw = gateway.config.gateway
    handler = type("BoundHandler", (Handler,), {"gateway": gateway})
    server = ThreadingHTTPServer((host or gw.get("host", "127.0.0.1"), port if port is not None else int(gw.get("port", 8787))), handler)
    server.daemon_threads = True
    return server


def setup_logging(level: str = "info", to_file: bool = True) -> None:
    handlers: list[logging.Handler] = []
    if to_file:
        paths.ensure_private_dir(paths.state_dir())
        handlers.append(logging.FileHandler(paths.log_file(), encoding="utf-8"))
    handlers.append(logging.StreamHandler())
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO),
                        format="%(asctime)s %(levelname)s %(message)s", handlers=handlers, force=True)

"""`ccfb` command line: run the gateway, launch Claude Code through it, inspect and repair."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from . import __version__, config as cfgmod, handoff, paths
from .router import Router, Needs
from .state import MODE_CLAUDE, MODE_FALLBACK, StateStore

MIN_PY = (3, 11)


# ------------------------------------------------------------------ helpers
def load_config() -> cfgmod.Config:
    cfg = cfgmod.load()
    apply_model_cache(cfg)
    return cfg


def cache_file() -> Path:
    return paths.config_dir() / "models-cache.json"


def apply_model_cache(cfg: cfgmod.Config) -> None:
    try:
        cache = json.loads(cache_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    for p in cfg.providers.values():
        for m in p.models:
            ctx = cache.get(m.key, {}).get("context")
            if ctx:
                m.context, m.context_verified = int(ctx), True


def base_url(cfg: cfgmod.Config) -> str:
    gw = cfg.gateway
    return f"http://{gw.get('host', '127.0.0.1')}:{int(gw.get('port', 8787))}"


def gateway_get(cfg: cfgmod.Config, path: str, timeout: float = 2) -> dict[str, Any] | None:
    try:
        with urllib.request.urlopen(base_url(cfg) + path, timeout=timeout) as r:
            return json.loads(r.read())
    except (urllib.error.URLError, OSError, ValueError):
        return None


def gateway_post(cfg: cfgmod.Config, path: str) -> bool:
    req = urllib.request.Request(base_url(cfg) + path, data=b"{}", method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=3):
            return True
    except (urllib.error.URLError, OSError):
        return False


def fmt_time(ts: float | None) -> str:
    if not ts:
        return "unknown"
    return time.strftime("%a %H:%M", time.localtime(ts))


def mask(value: str) -> str:
    return "set (" + value[:4] + "…)" if len(value) > 8 else "set"


# ------------------------------------------------------------------ serve / start / stop
def cmd_serve(args: argparse.Namespace) -> int:
    from .gateway import Gateway, make_server, setup_logging
    cfg = load_config()
    setup_logging(cfg.gateway.get("log_level", "info"))
    gw = Gateway(cfg)
    server = make_server(gw, port=args.port)
    host, port = server.server_address[:2]
    paths.ensure_private_dir(paths.state_dir())
    paths.pid_file().write_text(str(os.getpid()))
    print(f"ccfb {__version__} listening on http://{host}:{port} (mode: {gw.store.state.mode})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        try:
            paths.pid_file().unlink()
        except OSError:
            pass
    return 0


def ensure_running(cfg: cfgmod.Config, quiet: bool = False) -> bool:
    if gateway_get(cfg, "/health"):
        return True
    paths.ensure_private_dir(paths.state_dir())
    log = open(paths.state_dir() / "gateway.out", "ab")
    cmd = [sys.executable, str(paths.REPO_FALLBACK_DIR / "bin" / "ccfb"), "serve"]
    kwargs: dict[str, Any] = {"stdout": log, "stderr": log, "stdin": subprocess.DEVNULL}
    if os.name == "nt":
        kwargs["creationflags"] = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen(cmd, **kwargs)
    for _ in range(50):
        time.sleep(0.1)
        if gateway_get(cfg, "/health", timeout=0.5):
            if not quiet:
                print(f"ccfb gateway started on {base_url(cfg)}")
            return True
    print(f"ccfb: gateway did not start; see {paths.state_dir() / 'gateway.out'}", file=sys.stderr)
    return False


def cmd_start(args: argparse.Namespace) -> int:
    return 0 if ensure_running(load_config()) else 1


def cmd_stop(args: argparse.Namespace) -> int:
    try:
        pid = int(paths.pid_file().read_text().strip())
    except (OSError, ValueError):
        print("ccfb gateway is not running (no pid file)")
        return 0
    try:
        os.kill(pid, signal.SIGTERM if os.name != "nt" else signal.SIGINT)
        print(f"stopped ccfb gateway (pid {pid})")
    except OSError:
        print("ccfb gateway was not running")
    try:
        paths.pid_file().unlink()
    except OSError:
        pass
    return 0


# ------------------------------------------------------------------ run Claude Code through the gateway
def cmd_run(args: argparse.Namespace) -> int:
    cfg = load_config()
    claude = shutil.which("claude")
    if not claude:
        print("ccfb: `claude` is not on PATH. Install Claude Code first (see SETUP-LINUX.md).", file=sys.stderr)
        return 127
    if not ensure_running(cfg, quiet=True):
        print("ccfb: starting Claude Code without the fallback gateway.", file=sys.stderr)
        os.execv(claude, [claude, *args.claude_args]) if os.name != "nt" else subprocess.call([claude, *args.claude_args])
        return 1
    env = dict(os.environ)
    env["ANTHROPIC_BASE_URL"] = base_url(cfg)
    for var in ("ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY"):
        if env.get(var):
            print(f"ccfb: note: {var} is set, so Claude Code uses it instead of your claude.ai login.", file=sys.stderr)
    argv = [claude, *args.claude_args]
    if os.name == "nt":
        return subprocess.call(argv, env=env)
    os.execve(claude, argv, env)
    return 0


# ------------------------------------------------------------------ status / control
def _status_data(cfg: cfgmod.Config) -> tuple[dict[str, Any], bool]:
    live = gateway_get(cfg, "/status")
    if live:
        return live, True
    st = StateStore().state
    return {"mode": st.mode, "last_switch_reason": st.last_switch_reason, "claude_reset_at": st.claude_reset_at,
            "next_claude_check_at": st.next_probe_at, "current_fallback": st.current_fallback,
            "manual_hold": st.manual_hold, "waiting_for_claude": st.mode == MODE_FALLBACK,
            "last_route": st.last_route, "providers": {}, "recent_events": st.events[-10:]}, False


def cmd_status(args: argparse.Namespace) -> int:
    cfg = load_config()
    data, running = _status_data(cfg)
    if args.json:
        print(json.dumps({"running": running, **data}, indent=2))
        return 0
    print(f"gateway:        {'running on ' + base_url(cfg) if running else 'not running'}")
    print(f"mode:           {data['mode']}{' (held manually)' if data.get('manual_hold') else ''}")
    print(f"last switch:    {data.get('last_switch_reason', '')}")
    if data["mode"] == MODE_FALLBACK:
        print(f"Claude resets:  {fmt_time(data.get('claude_reset_at'))} (from Anthropic's headers; may be approximate)")
        print(f"next Claude try:{' ' + fmt_time(data.get('next_claude_check_at'))}")
    route = data.get("last_route") or {}
    if route:
        print(f"last fallback:  {route.get('provider')}/{route.get('model')} ({route.get('seconds')}s)")
        if route.get("skipped"):
            print(f"  skipped:      {'; '.join(route['skipped'])}")
    for name, p in (data.get("providers") or {}).items():
        print(f"provider {name:11} {p['state']:<38} today (observed): {p['today_requests_observed']} req")
    return 0


def cmd_control(args: argparse.Namespace) -> int:
    cfg = load_config()
    route = {"resume": "/ccfb/resume", "use-fallback": "/ccfb/use-fallback", "reset": "/ccfb/reset"}[args.command]
    if gateway_post(cfg, route):
        print(f"ok: {args.command}")
        return 0
    store = StateStore()
    with store.lock:
        if args.command == "resume":
            store.state.manual_hold, store.state.next_probe_at = False, 0
            store.set_mode(MODE_CLAUDE, "manual resume (ccfb resume)")
        elif args.command == "use-fallback":
            store.state.manual_hold = True
            store.set_mode(MODE_FALLBACK, "manual switch (ccfb use-fallback)")
        else:
            store.state.health = {}
            store.save()
    print(f"ok: {args.command} (gateway not running; state file updated)")
    return 0


# ------------------------------------------------------------------ doctor
def cmd_doctor(args: argparse.Namespace) -> int:
    problems = 0

    def line(ok: bool | None, text: str) -> None:
        nonlocal problems
        mark = {True: "ok  ", False: "FAIL", None: "note"}[ok]
        if ok is False:
            problems += 1
        print(f"[{mark}] {text}")

    line(sys.version_info >= MIN_PY, f"Python {sys.version.split()[0]} (needs 3.11+)")
    try:
        cfg = load_config()
        line(True, f"config: {paths.default_registry()} + {paths.user_config_file()}"
                   f"{'' if paths.user_config_file().exists() else ' (no user overrides)'}")
    except (cfgmod.ConfigError, OSError, ValueError) as exc:
        line(False, f"config error: {exc}")
        return 1
    line(bool(shutil.which("claude")), "Claude Code (`claude`) on PATH" if shutil.which("claude")
         else "Claude Code not found on PATH: install it, then run `ccfb run`")
    sf = paths.secrets_file()
    if sf.exists():
        perms_ok = os.name == "nt" or (sf.stat().st_mode & 0o077) == 0
        line(perms_ok, f"secrets file {sf}" + ("" if perms_ok else " is readable by other users: chmod 600 it"))
    else:
        line(None, f"no secrets file at {sf}; keys can also come from environment variables")
    usable = cfg.usable_providers()
    for p in cfg.providers.values():
        if not p.enabled:
            line(None, f"{p.name}: disabled ({p.free_kind})" + (f" - {p.incompatible_reason.split('.')[0]}" if p.incompatible_reason else ""))
            continue
        if p.incompatible_reason:
            line(None, f"{p.name}: enabled but incompatible - {p.incompatible_reason.split('.')[0]}")
            continue
        key = p.api_key(cfg.secrets)
        if p.static_key or key:
            line(True, f"{p.name}: credential {'not needed (local)' if p.static_key else mask(key)}")
        else:
            # Only a problem when no other provider can take over; reported below.
            line(None, f"{p.name}: {p.key_env} is not set. Get a free key at {p.signup} and add it to {sf}")
    if not usable:
        line(False, "no usable free provider: fallback cannot work until at least one key is configured")
    router = Router(cfg, StateStore())
    picks = router.candidates(Needs(role="main", tools=True, est_tokens=30000)).candidates
    line(bool(picks), "would use for a typical Claude Code request: " +
         (", ".join(c.model.key for c in picks) if picks else "nothing"))
    running = gateway_get(cfg, "/health")
    line(None, f"gateway {'running' if running else 'not running (starts automatically with `ccfb run`)'} at {base_url(cfg)}")
    if args.online:
        for p in usable:
            ok, detail = online_check(cfg, p)
            line(ok, f"{p.name}: live test {detail}")
    else:
        line(None, "skipped live provider tests (add --online; each test uses 1 free request)")
    return 1 if problems else 0


def online_check(cfg: cfgmod.Config, p: cfgmod.Provider) -> tuple[bool, str]:
    from . import upstream
    model = sorted(p.models, key=lambda m: m.priority)[0]
    key = p.api_key(cfg.secrets)
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    if p.kind == "anthropic":
        url = p.base_url + "/v1/messages"
        headers["anthropic-version"] = "2023-06-01"
        body = {"model": model.id, "max_tokens": 8, "messages": [{"role": "user", "content": "Reply OK"}]}
    else:
        url = p.base_url + "/chat/completions"
        body = {"model": model.id, "max_tokens": 8, "messages": [{"role": "user", "content": "Reply OK"}]}
    try:
        resp = upstream.request("POST", url, headers, json.dumps(body).encode(), read_timeout=60)
        raw = resp.read_all(4096)
    except upstream.NetworkError as exc:
        return False, f"network error: {exc}"
    if resp.status == 200:
        return True, f"OK ({model.id})"
    return False, f"HTTP {resp.status}: {raw[:160].decode('utf-8', 'replace')}"


# ------------------------------------------------------------------ models
def cmd_models(args: argparse.Namespace) -> int:
    cfg = load_config()
    if args.refresh:
        refresh_models(cfg)
        apply_model_cache(cfg)
    router = Router(cfg, StateStore())
    decision = router.candidates(Needs(role="main", tools=True, est_tokens=30000))
    chosen = {c.model.key for c in decision.candidates}
    for p in cfg.providers.values():
        for m in sorted(p.models, key=lambda m: m.priority):
            state = "eligible" if m.key in chosen else decision.rejected.get(m.key, "lower priority")
            ctx = f"{m.context:,}" + ("" if m.context_verified else "?")
            print(f"{m.key:48} ctx {ctx:>11}  tools={'y' if m.tools else 'n'} vision={'y' if m.vision else 'n'}  {state}")
    print("\n? = context window not yet confirmed from the provider's API (run `ccfb models --refresh`)")
    return 0


def refresh_models(cfg: cfgmod.Config) -> None:
    cache: dict[str, Any] = {}
    try:
        cache = json.loads(cache_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    for p in cfg.providers.values():
        if not p.models_endpoint:
            continue
        key = p.api_key(cfg.secrets)
        if p.name == "gemini":
            if not key:
                continue
            req = urllib.request.Request(p.models_endpoint + "?pageSize=1000", headers={"x-goog-api-key": key})
        else:
            req = urllib.request.Request(p.models_endpoint, headers={"Authorization": f"Bearer {key}"} if key else {})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read())
        except (urllib.error.URLError, OSError, ValueError) as exc:
            print(f"{p.name}: could not refresh ({exc})")
            continue
        found = 0
        wanted = {m.id: m for m in p.models}
        for item in data.get("data", []) + data.get("models", []):
            mid = str(item.get("id") or item.get("name", "")).removeprefix("models/")
            ctx = item.get("context_length") or item.get("inputTokenLimit")
            if mid in wanted and ctx:
                cache[wanted[mid].key] = {"context": int(ctx), "checked": time.strftime("%Y-%m-%d")}
                found += 1
        missing = set(wanted) - {k.split("/", 1)[1] for k in cache if k.startswith(p.name + "/")}
        print(f"{p.name}: refreshed {found} model(s)" + (f"; not listed by the provider: {', '.join(sorted(missing))}" if missing else ""))
    paths.ensure_private_dir(paths.config_dir())
    cache_file().write_text(json.dumps(cache, indent=2), encoding="utf-8")


# ------------------------------------------------------------------ handoff
def cmd_handoff(args: argparse.Namespace) -> int:
    sid = args.session
    if not sid:
        projects = paths.claude_projects_dir()
        files = sorted(projects.glob("*/*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True) if projects.exists() else []
        if not files:
            print("no Claude Code transcripts found", file=sys.stderr)
            return 1
        sid = files[0].stem
    path = handoff.write_handoff(sid, "manual handoff (ccfb handoff)")
    if not path:
        print(f"no transcript for session {sid}", file=sys.stderr)
        return 1
    print(path)
    return 0


# ------------------------------------------------------------------ Claude Code integrations
def cmd_statusline(args: argparse.Namespace) -> int:
    try:
        info = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        info = {}
    st = StateStore().state
    model = (info.get("model") or {}).get("display_name", "")
    if st.mode == MODE_FALLBACK:
        route = st.last_route.get("model") or "free model"
        print(f"FALLBACK {route} · Claude back ~{fmt_time(st.claude_reset_at or st.next_probe_at)}")
        return 0
    rl = info.get("rate_limits") or {}
    bits = [model] if model else []
    for name, label in (("five_hour", "5h"), ("seven_day", "7d")):
        pct = (rl.get(name) or {}).get("used_percentage")
        if pct is not None:
            bits.append(f"{label} {int(pct)}%")
    print(" · ".join(bits) if bits else "claude")
    return 0


def cmd_hook(args: argparse.Namespace) -> int:
    try:
        info = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        info = {}
    store = StateStore()
    if args.event == "stop-failure":
        store.event("claude_code_stop_failure", error=str(info.get("error") or info.get("error_type") or "unknown")[:80],
                    session=str(info.get("session_id", ""))[:64])
        store.save()
        return 0
    if args.event == "session-start" and store.state.mode == MODE_FALLBACK:
        msg = ("Note: the user's Claude usage limit is reached, so this session runs on a free fallback model "
               f"through ccfb (Claude expected back around {fmt_time(store.state.claude_reset_at)}). "
               "Work in small, verifiable steps.")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": msg}}))
    return 0


def settings_patch(ccfb_bin: str) -> dict[str, Any]:
    return {
        "statusLine": {"type": "command", "command": f"{ccfb_bin} statusline"},
        "hooks": {
            "StopFailure": [{"hooks": [{"type": "command", "command": f"{ccfb_bin} hook stop-failure"}]}],
            "SessionStart": [{"hooks": [{"type": "command", "command": f"{ccfb_bin} hook session-start"}]}],
        },
    }


def cmd_install_settings(args: argparse.Namespace) -> int:
    settings = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude")).expanduser() / "settings.json"
    ccfb_bin = shutil.which("ccfb") or str(paths.REPO_FALLBACK_DIR / "bin" / "ccfb")
    patch = settings_patch(ccfb_bin)
    current: dict[str, Any] = {}
    if settings.exists():
        current = json.loads(settings.read_text(encoding="utf-8") or "{}")
    merged = json.loads(json.dumps(current))
    notes = []
    if "statusLine" in current and "ccfb" not in json.dumps(current["statusLine"]):
        notes.append("kept your existing statusLine (ccfb's status line not added)")
    else:
        merged["statusLine"] = patch["statusLine"]
    hooks = merged.setdefault("hooks", {})
    for event, entries in patch["hooks"].items():
        existing = hooks.setdefault(event, [])
        if not any("ccfb" in json.dumps(e) for e in existing):
            existing.extend(entries)
    print(json.dumps(merged, indent=2))
    for n in notes:
        print("note:", n, file=sys.stderr)
    if not args.apply:
        print(f"\n(dry run) Re-run with --apply to write {settings}; a backup is made first.", file=sys.stderr)
        return 0
    if settings.exists():
        backup = settings.with_name(f"settings.json.bak-{time.strftime('%Y%m%d-%H%M%S')}")
        shutil.copy2(settings, backup)
        print(f"backup: {backup}", file=sys.stderr)
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    print(f"updated {settings}", file=sys.stderr)
    return 0


# ------------------------------------------------------------------ main
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="ccfb", description="Claude Code free-LLM fallback gateway")
    ap.add_argument("--version", action="version", version=f"ccfb {__version__}")
    sub = ap.add_subparsers(dest="command", required=True)
    s = sub.add_parser("serve", help="run the gateway in the foreground")
    s.add_argument("--port", type=int, default=None)
    s.set_defaults(func=cmd_serve)
    sub.add_parser("start", help="start the gateway in the background").set_defaults(func=cmd_start)
    sub.add_parser("stop", help="stop the background gateway").set_defaults(func=cmd_stop)
    r = sub.add_parser("run", help="start Claude Code through the gateway (extra args go to claude)")
    r.add_argument("claude_args", nargs=argparse.REMAINDER)
    r.set_defaults(func=cmd_run)
    st = sub.add_parser("status", help="routing mode, providers, last switch")
    st.add_argument("--json", action="store_true")
    st.set_defaults(func=cmd_status)
    for name, text in (("resume", "go back to Claude now and clear a manual hold"),
                       ("use-fallback", "use free models until `ccfb resume`"),
                       ("reset", "clear provider cooldowns and disabled flags")):
        sub.add_parser(name, help=text).set_defaults(func=cmd_control)
    d = sub.add_parser("doctor", help="check prerequisites, config and credentials")
    d.add_argument("--online", action="store_true", help="send one tiny request to each usable provider")
    d.set_defaults(func=cmd_doctor)
    m = sub.add_parser("models", help="list models and why each is or isn't eligible")
    m.add_argument("--refresh", action="store_true", help="read context windows from provider APIs")
    m.set_defaults(func=cmd_models)
    h = sub.add_parser("handoff", help="write a handoff summary for a session (default: latest)")
    h.add_argument("--session")
    h.set_defaults(func=cmd_handoff)
    sub.add_parser("statusline", help="status line command for Claude Code").set_defaults(func=cmd_statusline)
    hk = sub.add_parser("hook", help="Claude Code hook entry point")
    hk.add_argument("event", choices=["stop-failure", "session-start"])
    hk.set_defaults(func=cmd_hook)
    i = sub.add_parser("install-settings", help="add ccfb's status line and hooks to ~/.claude/settings.json")
    i.add_argument("--apply", action="store_true")
    i.set_defaults(func=cmd_install_settings)
    return ap


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < MIN_PY:
        print(f"ccfb needs Python {MIN_PY[0]}.{MIN_PY[1]}+ (found {sys.version.split()[0]})", file=sys.stderr)
        return 1
    args = build_parser().parse_args(argv)
    if getattr(args, "claude_args", None) and args.claude_args[:1] == ["--"]:
        args.claude_args = args.claude_args[1:]
    try:
        return int(args.func(args) or 0)
    except cfgmod.ConfigError as exc:
        print(f"ccfb: config error: {exc}", file=sys.stderr)
        return 2

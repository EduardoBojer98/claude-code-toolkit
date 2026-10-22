"""Build a task handoff from a Claude Code session transcript (no LLM call, no network).

The gateway keeps the same Claude Code session going across a switch, so a handoff is a
safety net: if a fallback model struggles, start a new session (on any model) and paste or
@-mention the handoff file. It records the objective, recent requests, files touched,
the latest todo list and the last assistant message.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from . import paths

EDIT_TOOLS = {"Edit", "MultiEdit", "Write", "NotebookEdit"}


def find_transcript(session_id: str, projects: Path | None = None) -> Path | None:
    projects = projects or paths.claude_projects_dir()
    if not session_id or not projects.exists():
        return None
    safe = "".join(c for c in session_id if c.isalnum() or c in "-_")
    matches = sorted(projects.glob(f"*/{safe}.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def _blocks(entry: dict[str, Any]) -> list[dict[str, Any]]:
    msg = entry.get("message") or {}
    content = msg.get("content")
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return [b for b in content or [] if isinstance(b, dict)]


def summarize(transcript: Path, max_requests: int = 5) -> dict[str, Any]:
    user_texts: list[str] = []
    files: list[str] = []
    commands: list[str] = []
    todos: list[dict[str, Any]] = []
    last_assistant = ""
    cwd = ""
    for line in transcript.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        cwd = entry.get("cwd", cwd) or cwd
        etype = entry.get("type")
        if etype == "user":
            for b in _blocks(entry):
                if b.get("type") == "text":
                    text = b.get("text", "").strip()
                    if text and not text.startswith("<") and "tool_result" not in text:
                        user_texts.append(text)
        elif etype == "assistant":
            for b in _blocks(entry):
                if b.get("type") == "text" and b.get("text", "").strip():
                    last_assistant = b["text"].strip()
                elif b.get("type") == "tool_use":
                    name, inp = b.get("name"), b.get("input") or {}
                    if name in EDIT_TOOLS:
                        fp = inp.get("file_path") or inp.get("notebook_path")
                        if fp and fp not in files:
                            files.append(fp)
                    elif name == "Bash" and inp.get("command"):
                        commands.append(str(inp["command"])[:200])
                    elif name == "TodoWrite" and isinstance(inp.get("todos"), list):
                        todos = inp["todos"]
    return {
        "objective": user_texts[0] if user_texts else "",
        "recent_requests": user_texts[-max_requests:],
        "files_changed": files,
        "recent_commands": commands[-8:],
        "todos": todos,
        "last_assistant": last_assistant[-2000:],
        "cwd": cwd,
    }


def render(session_id: str, summary: dict[str, Any], reason: str) -> str:
    when = time.strftime("%Y-%m-%d %H:%M", time.localtime())
    lines = [
        f"# Handoff: Claude Code session {session_id}",
        "",
        f"_{when} · {reason}_",
        "",
        "Continue this task. Read the files listed below before changing anything.",
        "",
        f"**Working directory:** `{summary['cwd'] or 'unknown'}`",
        "",
        "## Objective",
        "",
        summary["objective"] or "(not found in transcript)",
        "",
        "## Most recent requests",
        "",
    ]
    lines += [f"- {t[:500]}" for t in summary["recent_requests"]] or ["- (none)"]
    lines += ["", "## Files changed in this session", ""]
    lines += [f"- `{f}`" for f in summary["files_changed"]] or ["- (none)"]
    lines += ["", "## Open work (latest todo list)", ""]
    open_todos = [t for t in summary["todos"] if t.get("status") != "completed"]
    lines += [f"- [{'x' if t.get('status') == 'completed' else ' '}] {t.get('content', '')} ({t.get('status', '')})"
              for t in open_todos] or ["- (no open todos recorded)"]
    lines += ["", "## Recent commands", ""]
    lines += [f"- `{c}`" for c in summary["recent_commands"]] or ["- (none)"]
    lines += ["", "## Last assistant message", "", summary["last_assistant"] or "(none)", ""]
    return "\n".join(lines)


def write_handoff(session_id: str, reason: str, projects: Path | None = None) -> Path | None:
    transcript = find_transcript(session_id, projects)
    if not transcript:
        return None
    out_dir = paths.ensure_private_dir(paths.handoff_dir())
    target = out_dir / f"{session_id}.md"
    target.write_text(render(session_id, summarize(transcript), reason), encoding="utf-8")
    return target

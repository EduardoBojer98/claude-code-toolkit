"""Optional end-to-end test with the real Claude Code CLI against fake upstreams.

Runs only with CCFB_E2E=1 and `claude` on PATH. No real API is contacted: the gateway's
"Anthropic" is a local fake that answers with a plan-limit 429, and the fallback provider
is a local fake OpenAI-compatible server. It checks that the real client accepts the
gateway's responses, runs a tool the fallback model asked for, and finishes the task.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest

from helpers import Env, Scripted, limit_429


def _sse(*chunks: dict) -> Scripted:
    return Scripted(200, sse=[f"data: {json.dumps(c)}\n\n".encode() for c in chunks] + [b"data: [DONE]\n\n"])


def _fake_model(req: dict) -> Scripted:
    body = req["json"] or {}
    if not body.get("tools"):
        return _sse({"choices": [{"index": 0, "delta": {"content": "title"}, "finish_reason": "stop"}]})
    if any(m.get("role") == "tool" for m in body.get("messages", [])):
        return _sse({"choices": [{"index": 0, "delta": {"content": "DONE-AFTER-TOOL"}, "finish_reason": "stop"}]})
    args = json.dumps({"command": "echo E2E-TOOL-RAN", "description": "e2e test"})
    return _sse(
        {"choices": [{"index": 0, "delta": {"tool_calls": [{"index": 0, "id": "call_abc", "type": "function",
                                                            "function": {"name": "Bash", "arguments": ""}}]}}]},
        {"choices": [{"index": 0, "delta": {"tool_calls": [{"index": 0, "function": {"arguments": args}}]},
                      "finish_reason": "tool_calls"}]},
    )


@unittest.skipUnless(os.environ.get("CCFB_E2E") == "1" and shutil.which("claude"), "set CCFB_E2E=1 with Claude Code installed")
class TestRealClaudeCode(unittest.TestCase):
    def test_tool_loop_on_fallback(self) -> None:
        env = Env()
        try:
            env.cfg.providers["freeanthro"].enabled = False
            env.oai.default = _fake_model
            env.claude.default = limit_429()
            e = {k: v for k, v in os.environ.items() if not k.startswith(("ANTHROPIC_", "CLAUDE_CODE_OAUTH"))}
            for k in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
                e.pop(k, None)
            e.update({"ANTHROPIC_BASE_URL": f"http://127.0.0.1:{env.port}", "ANTHROPIC_API_KEY": "sk-ant-dummy-test",
                      "HOME": str(env.home), "CLAUDE_CONFIG_DIR": str(env.home / ".claude"),
                      "DISABLE_TELEMETRY": "1", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
                      "DISABLE_AUTOUPDATER": "1", "NO_PROXY": "127.0.0.1,localhost"})
            work = tempfile.mkdtemp()
            r = subprocess.run(["claude", "-p", "Run the e2e echo", "--output-format", "json", "--max-turns", "3",
                                "--allowedTools", "Bash(echo:*)"], env=e, capture_output=True, text=True,
                               timeout=180, cwd=work, stdin=subprocess.DEVNULL)
            self.assertEqual(r.returncode, 0, r.stderr[-500:])
            out = json.loads(r.stdout)
            self.assertEqual(out.get("result"), "DONE-AFTER-TOOL")
            tool_msgs = [m for q in env.oai.requests for m in (q["json"] or {}).get("messages", []) if m.get("role") == "tool"]
            self.assertTrue(any("E2E-TOOL-RAN" in str(m.get("content")) for m in tool_msgs))
            claude_calls = [q for q in env.claude.requests if q["path"].startswith("/v1/messages")]
            self.assertEqual(len(claude_calls), 1)       # no retry loop against Claude while limited
        finally:
            env.close()


if __name__ == "__main__":
    unittest.main()

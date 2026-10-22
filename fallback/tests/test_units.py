"""Unit tests: classification, translation, config validation, handoff, CLI, fresh install."""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from helpers import ROOT, Env

from ccfb import classify, config as cfgmod, handoff, sanitize, translate
from ccfb.cli import main as cli_main

NOW = 1_800_000_000.0


class TestClassify(unittest.TestCase):
    def test_usage_limit_needs_unified_headers(self) -> None:
        v = classify.classify_claude(429, {"Anthropic-Ratelimit-Unified-Reset": str(int(NOW + 600))}, b"{}", NOW)
        self.assertEqual(v.category, classify.USAGE_LIMIT)
        self.assertEqual(v.reset_at, NOW + 600)
        self.assertEqual(classify.classify_claude(429, {"retry-after": "3"}, b"{}", NOW).category, classify.THROTTLE)

    def test_other_claude_errors(self) -> None:
        self.assertEqual(classify.classify_claude(529, {}, b"", NOW).category, classify.OVERLOADED)
        self.assertEqual(classify.classify_claude(401, {}, b"", NOW).category, classify.AUTH)
        self.assertEqual(classify.classify_claude(403, {}, b"", NOW).category, classify.AUTH)
        self.assertEqual(classify.classify_claude(500, {}, b"", NOW).category, classify.SERVER)
        body = json.dumps({"error": {"message": "prompt is too long: 250000 tokens"}}).encode()
        self.assertEqual(classify.classify_claude(400, {}, body, NOW).category, classify.CONTEXT)

    def test_reset_formats(self) -> None:
        self.assertEqual(classify.parse_time("1800000600", NOW), 1800000600)
        self.assertEqual(classify.parse_time("1800000600000", NOW), 1800000600)
        self.assertEqual(classify.parse_time("90", NOW), NOW + 90)
        self.assertEqual(classify.parse_time("1m30s", NOW), NOW + 90)
        self.assertEqual(classify.parse_time("2027-01-01T00:00:00Z", NOW), 1798761600)
        self.assertEqual(classify.parse_time("", NOW), 0)

    def test_provider_daily_detection(self) -> None:
        v = classify.classify_provider(429, {}, b'{"error":{"message":"Quota exceeded for GenerateRequestsPerDay"}}', NOW)
        self.assertTrue(v.daily)
        v = classify.classify_provider(429, {"retry-after": "20"}, b'{"error":{"message":"too fast"}}', NOW)
        self.assertFalse(v.daily)
        self.assertEqual(v.retry_after, 20)


class TestTranslate(unittest.TestCase):
    def test_request_mapping(self) -> None:
        body = {
            "model": "claude-x", "max_tokens": 100, "system": [{"type": "text", "text": "SYS"}],
            "tools": [{"name": "Bash", "description": "run", "input_schema": {"type": "object"}},
                      {"type": "web_search_20250305", "name": "web_search"}],
            "tool_choice": {"type": "any"},
            "messages": [
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": [{"type": "text", "text": "ok"},
                                                  {"type": "tool_use", "id": "toolu_1", "name": "Bash", "input": {"command": "ls"}}]},
                {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_1", "content": [{"type": "text", "text": "a.py"}]},
                                             {"type": "text", "text": "now?"}]},
            ],
        }
        out = translate.to_openai_request(body, "m", stream=False)
        roles = [m["role"] for m in out["messages"]]
        self.assertEqual(roles, ["system", "user", "assistant", "tool", "user"])
        self.assertEqual(out["messages"][2]["tool_calls"][0]["function"]["arguments"], '{"command": "ls"}')
        self.assertEqual(out["messages"][3], {"role": "tool", "tool_call_id": "toolu_1", "content": "a.py"})
        self.assertEqual(len(out["tools"]), 1)                       # server tool dropped
        self.assertEqual(out["tool_choice"], "required")

    def test_response_mapping(self) -> None:
        data = {"choices": [{"message": {"content": None, "tool_calls": [
            {"id": "call/1", "function": {"name": "Edit", "arguments": "not json"}}]}, "finish_reason": "stop"}]}
        out = translate.from_openai_response(data, "claude-x", 12)
        self.assertEqual(out["stop_reason"], "tool_use")
        self.assertEqual(out["content"][0]["id"], "toolu_fb_call_1")
        self.assertEqual(out["content"][0]["input"], {"_unparsed_arguments": "not json"})
        self.assertEqual(out["usage"]["input_tokens"], 12)


class TestSanitize(unittest.TestCase):
    def test_env_and_keys_masked_images_kept(self) -> None:
        body = {"messages": [{"role": "user", "content": [
            {"type": "text", "text": "DB_PASSWORD=hunter2hunter2\nkey sk-ant-api03-" + "x" * 30},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "AKIAABCDEFGHIJKLMNOP"}}]}]}
        clean, counts = sanitize.for_third_party(body, redact=True)
        text = clean["messages"][0]["content"][0]["text"]
        self.assertIn("DB_PASSWORD=[REDACTED:env-secret]", text)
        self.assertIn("[REDACTED:anthropic-key]", text)
        self.assertEqual(clean["messages"][0]["content"][1]["source"]["data"], "AKIAABCDEFGHIJKLMNOP")
        self.assertEqual(sum(counts.values()), 2)

    def test_redaction_can_be_turned_off(self) -> None:
        body = {"messages": [{"role": "user", "content": "AKIAABCDEFGHIJKLMNOP"}]}
        clean, counts = sanitize.for_third_party(body, redact=False)
        self.assertEqual(clean["messages"][0]["content"], "AKIAABCDEFGHIJKLMNOP")


class TestConfigValidation(unittest.TestCase):
    def test_upstream_must_be_anthropic(self) -> None:
        with self.assertRaises(cfgmod.ConfigError):
            cfgmod.validate({"claude": {"upstream": "https://evil.example"}})

    def test_gateway_must_be_loopback(self) -> None:
        with self.assertRaises(cfgmod.ConfigError):
            cfgmod.validate({"gateway": {"host": "0.0.0.0"}})

    def test_plain_http_only_for_local(self) -> None:
        with self.assertRaises(cfgmod.ConfigError):
            cfgmod._build_provider("x", {"kind": "openai", "base_url": "http://example.com"})

    def test_env_file_parser(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".env"
            p.write_text('# c\nexport A="1"\nB=two\n\nC=\n')
            self.assertEqual(cfgmod.parse_env_file(p), {"A": "1", "B": "two", "C": ""})

    def test_repo_registry_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            cfg = cfgmod.load(user_path=Path(d) / "none.toml", secrets_path=Path(d) / "none.env")
            self.assertIn("openrouter", cfg.providers)
            self.assertTrue(all(m.source for p in cfg.providers.values() for m in p.models))


class TestHandoff(unittest.TestCase):
    def test_summary_from_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            proj = Path(d) / "projects" / "-home-me-site"
            proj.mkdir(parents=True)
            lines = [
                {"type": "user", "cwd": "/home/me/site", "message": {"role": "user", "content": "Build the pricing page"}},
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "name": "Write", "input": {"file_path": "/home/me/site/pricing.html"}},
                    {"type": "tool_use", "name": "TodoWrite", "input": {"todos": [
                        {"content": "Add FAQ", "status": "pending"}, {"content": "Hero", "status": "completed"}]}},
                    {"type": "text", "text": "Hero done, FAQ next."}]}},
            ]
            (proj / "sess-9.jsonl").write_text("\n".join(json.dumps(x) for x in lines))
            os.environ["CCFB_STATE_DIR"] = d
            try:
                path = handoff.write_handoff("sess-9", "test", projects=Path(d) / "projects")
            finally:
                os.environ.pop("CCFB_STATE_DIR")
            text = path.read_text()
            self.assertIn("Build the pricing page", text)
            self.assertIn("/home/me/site/pricing.html", text)
            self.assertIn("Add FAQ", text)
            self.assertNotIn("[x] Hero", text)
            self.assertIn("Hero done, FAQ next.", text)


class TestCliMissingCredentials(unittest.TestCase):
    """Scenario 10 (CLI side): doctor explains which key to add and where."""

    def test_doctor_reports_missing_keys(self) -> None:
        env = Env(provider_keys=False)
        try:
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(["doctor"])
            text = out.getvalue()
            self.assertEqual(code, 1)
            self.assertIn("FREEANTHRO_KEY is not set", text)
            self.assertIn("no usable free provider", text)
            self.assertNotIn("sk-", text)
        finally:
            env.close()


@unittest.skipUnless(shutil.which("git") and shutil.which("bash"), "needs git and bash")
class TestFreshInstall(unittest.TestCase):
    """Scenarios 11 and 12: a clean clone on a 'new machine' (empty HOME) installs and runs
    using only files in the repository."""

    def test_clone_install_doctor(self) -> None:
        repo = ROOT.parent
        with tempfile.TemporaryDirectory() as d:
            home = Path(d) / "home"
            home.mkdir()
            clone = Path(d) / "claude-setup"
            subprocess.run(["git", "clone", "-q", str(repo), str(clone)], check=True)
            # copy the working tree's fallback/ in case this runs before the files are committed
            shutil.rmtree(clone / "fallback", ignore_errors=True)
            shutil.copytree(repo / "fallback", clone / "fallback", ignore=shutil.ignore_patterns("__pycache__"))
            env = {"HOME": str(home), "PATH": f"{home}/.local/bin:/usr/bin:/bin", "LANG": "C.UTF-8"}
            r = subprocess.run(["bash", str(clone / "fallback" / "install.sh")], env=env, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            self.assertTrue((home / ".local/bin/ccfb").is_symlink())
            envfile = home / ".config/claude-fallback/.env"
            self.assertEqual(envfile.stat().st_mode & 0o777, 0o600)
            # re-running is safe and keeps the user's keys
            envfile.write_text("OPENROUTER_API_KEY=sk-or-test-1234567890\n")
            r = subprocess.run(["bash", str(clone / "fallback" / "install.sh")], env=env, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0)
            self.assertIn("sk-or-test", envfile.read_text())
            r = subprocess.run([str(home / ".local/bin/ccfb"), "doctor"], env=env, capture_output=True, text=True)
            self.assertIn("openrouter: credential set", r.stdout)
            self.assertIn("would use for a typical Claude Code request: openrouter/", r.stdout)
            self.assertNotIn("1234567890", r.stdout)
            r = subprocess.run([str(home / ".local/bin/ccfb"), "status"], env=env, capture_output=True, text=True)
            self.assertIn("mode:           claude", r.stdout)


if __name__ == "__main__":
    unittest.main()

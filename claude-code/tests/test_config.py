"""Checks for the Claude Code user layer: config syntax, agent/skill frontmatter, hooks, installer.
No network, no credentials, no model calls.  Run:  python3 -m unittest discover -s claude-code/tests
"""
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAYER = HERE.parent
REPO = LAYER.parent
HOOKS = LAYER / "hooks"

# Documented subagent frontmatter (code.claude.com/docs/en/sub-agents, checked 2026-10-28).
AGENT_FIELDS = {"name", "description", "tools", "disallowedTools", "model", "permissionMode", "maxTurns",
                "autoCompactWindow", "skills", "mcpServers", "hooks", "memory", "background", "omitClaudeMd",
                "effort", "isolation", "color", "initialPrompt", "experimental"}
AGENT_MODELS = {"sonnet", "opus", "haiku", "fable", "inherit"}
EFFORTS = {"low", "medium", "high", "xhigh", "max"}
# Keys claude.ai accepts in an uploaded skill (other keys are a hard error there).
CLAUDE_AI_SKILL_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}


def frontmatter(path):
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path} has no frontmatter"
    fields = {}
    for line in m.group(1).splitlines():
        if line and not line.startswith(" ") and ":" in line:
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip()
    return fields, text[m.end():]


def run_hook(name, payload):
    p = subprocess.run([str(HOOKS / name)], input=json.dumps(payload), capture_output=True, text=True, timeout=30)
    return p.returncode, p.stderr


class ConfigFiles(unittest.TestCase):
    def test_settings_template_is_valid_json_with_known_shape(self):
        s = json.loads((LAYER / "settings.json").read_text())
        for key in ("allow", "ask", "deny"):
            self.assertIsInstance(s["permissions"][key], list)
        self.assertIn(s["effortLevel"], EFFORTS)
        self.assertIn(s["env"]["CLAUDE_CODE_SUBAGENT_MODEL"], AGENT_MODELS)
        for state in s["skillOverrides"].values():
            self.assertIn(state, {"on", "name-only", "user-invocable-only", "off"})
        for event, groups in s["hooks"].items():
            for g in groups:
                for h in g["hooks"]:
                    script = h["command"].replace("~/.claude/hooks/claude-setup/", "")
                    self.assertTrue((HOOKS / script).is_file(), f"{event}: missing {script}")

    def test_global_claude_md_stays_small(self):
        lines = (LAYER / "CLAUDE.md").read_text().splitlines()
        self.assertLess(len(lines), 100, "keep the global CLAUDE.md short; move detail into skills")

    def test_agents_use_documented_fields_and_models(self):
        agents = sorted((LAYER / "agents").glob("*.md"))
        self.assertTrue(agents)
        for a in agents:
            fields, body = frontmatter(a)
            self.assertTrue({"name", "description"} <= fields.keys(), a.name)
            self.assertEqual(fields["name"], a.stem)
            self.assertFalse(set(fields) - AGENT_FIELDS, f"{a.name}: unknown fields {set(fields) - AGENT_FIELDS}")
            self.assertIn(fields.get("model", "inherit"), AGENT_MODELS, a.name)
            if "effort" in fields:
                self.assertIn(fields["effort"], EFFORTS, a.name)
            no_spawn = "Agent" in fields.get("disallowedTools", "") or (
                "tools" in fields and "Agent" not in fields["tools"])
            self.assertTrue(no_spawn, f"{a.name} must not spawn further agents")
            self.assertIn("Output", body, f"{a.name} needs an explicit output format")

    def test_skills_frontmatter_and_links(self):
        skills = [LAYER / "skills" / "debug", REPO / "skills" / "web-dev-standards", REPO / "skills" / "toolkit-maintainer"]
        for d in skills:
            fields, body = frontmatter(d / "SKILL.md")
            self.assertEqual(fields["name"], d.name)
            self.assertLessEqual(len(fields["description"]), 1536, f"{d.name}: description is truncated in listings")
            self.assertLess(len(body.splitlines()), 500, d.name)
            if d.parent == REPO / "skills":  # also uploaded to claude.ai
                self.assertFalse(set(fields) - CLAUDE_AI_SKILL_FIELDS, f"{d.name}: key not allowed on claude.ai")
            for link in re.findall(r"\]\(((?:references|scripts)/[^)]+)\)", body):
                self.assertTrue((d / link).is_file(), f"{d.name}: broken link {link}")


class Hooks(unittest.TestCase):
    def test_guard_secrets_blocks_live_keys(self):
        key = "sk-ant-api03-" + "A" * 40
        code, err = run_hook("guard-secrets.sh", {"tool_name": "Write", "tool_input": {"file_path": "/p/config.php", "content": f"define('K', '{key}');"}})
        self.assertEqual(code, 2)
        self.assertIn("guard-secrets", err)
        self.assertNotIn(key, err, "the hook must not echo the full secret")
        code, _ = run_hook("guard-secrets.sh", {"tool_name": "Edit", "tool_input": {"file_path": "/p/a.js", "new_string": "const t = 'ghp_" + "b" * 36 + "';"}})
        self.assertEqual(code, 2)

    def test_guard_secrets_allows_placeholders_and_examples(self):
        for payload in (
            {"tool_input": {"file_path": "/p/.env.example", "content": "ANTHROPIC_API_KEY=sk-ant-" + "x" * 30}},
            {"tool_input": {"file_path": "/p/a.md", "content": "ANTHROPIC_API_KEY=<redacted>\nOPENROUTER_API_KEY=your-key"}},
            {"tool_input": {"file_path": "/p/a.ts", "new_string": "const key = process.env.API_KEY;"}},
        ):
            self.assertEqual(run_hook("guard-secrets.sh", payload)[0], 0, payload)

    def test_guard_bash(self):
        blocked = ["cat .env", "cat ./app/.env.local", "less ~/.ssh/id_ed25519", "head -5 ~/.claude/.credentials.json",
                   "cd x && cat .env", "grep KEY .env", "cat .env.example .env",
                   "grep -q x .env; cat .env"]
        allowed = ["cat .env.example", "grep -q '^DB_NAME=' .env && echo set", "rg process.env src/", "ls -la",
                   "npm test", "git diff", "cat README.md"]
        for c in blocked:
            self.assertEqual(run_hook("guard-bash.sh", {"tool_input": {"command": c}})[0], 2, c)
        for c in allowed:
            self.assertEqual(run_hook("guard-bash.sh", {"tool_input": {"command": c}})[0], 0, c)

    def test_format_file_is_a_noop_without_prettier(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "a.js"
            f.write_text("const a   =  1\n")
            self.assertEqual(run_hook("format-file.sh", {"tool_input": {"file_path": str(f)}})[0], 0)
            self.assertEqual(f.read_text(), "const a   =  1\n")


class Installer(unittest.TestCase):
    def install(self, home, *args):
        env = dict(os.environ, HOME=home)
        env.pop("CLAUDE_CONFIG_DIR", None)
        return subprocess.run(["bash", str(LAYER / "install.sh"), *args], env=env, capture_output=True, text=True, timeout=60)

    def test_install_is_idempotent_and_keeps_user_values(self):
        with tempfile.TemporaryDirectory() as home:
            cfg = Path(home, ".claude")
            cfg.mkdir()
            (cfg / "settings.json").write_text(json.dumps({"theme": "dark", "effortLevel": "xhigh",
                                                           "permissions": {"allow": ["Bash(make *)"]}}))
            (cfg / "CLAUDE.md").write_text("old personal notes\n")
            (cfg / "skills" / "debug").mkdir(parents=True)
            (cfg / "skills" / "debug" / "SKILL.md").write_text("old copy\n")

            dry = self.install(home, "--dry-run")
            self.assertEqual(dry.returncode, 0, dry.stderr)
            self.assertFalse((cfg / "CLAUDE.md").is_symlink(), "dry run must not change anything")

            first = self.install(home)
            self.assertEqual(first.returncode, 0, first.stderr)
            s = json.loads((cfg / "settings.json").read_text())
            self.assertEqual(s["theme"], "dark")
            self.assertEqual(s["effortLevel"], "xhigh", "existing values win")
            self.assertIn("Bash(make *)", s["permissions"]["allow"])
            self.assertIn("Bash(git diff *)", s["permissions"]["allow"])
            self.assertTrue((cfg / "CLAUDE.md").is_symlink())
            self.assertEqual(len(list(cfg.glob("claude-setup-backups/*/.claude/CLAUDE.md"))), 1, "old CLAUDE.md is kept as a backup")
            self.assertFalse(list(cfg.glob("**/*.bak-*")), "no backups next to live files")
            self.assertTrue((cfg / "agents" / "Explore.md").is_symlink())
            self.assertEqual([p.name for p in (cfg / "skills").iterdir() if not p.is_symlink()], [],
                             "an old skill folder must not stay in skills/, where it would load as a duplicate")
            self.assertTrue((cfg / "skills" / "web-dev-standards" / "references" / "wordpress.md").is_file())
            self.assertTrue(os.access(cfg / "hooks" / "claude-setup" / "guard-bash.sh", os.X_OK))
            self.assertTrue(os.access(Path(home, ".local", "bin", "security-scan"), os.X_OK))

            second = self.install(home)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("already contains the template", second.stdout)
            self.assertNotIn("backup", second.stdout)
            self.assertEqual(json.loads((cfg / "settings.json").read_text()), s)


class EnablePlugins(unittest.TestCase):
    def test_profile_on_and_off_in_local_settings(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            local = Path(d, ".claude", "settings.local.json")
            local.parent.mkdir()
            local.write_text(json.dumps({"permissions": {"allow": ["Bash(make *)"]}}))
            script = str(LAYER / "enable-plugins.sh")

            on = subprocess.run(["bash", script, "wordpress", d], capture_output=True, text=True)
            self.assertEqual(on.returncode, 0, on.stderr)
            s = json.loads(local.read_text())
            self.assertTrue(s["enabledPlugins"]["wp-dev-skills@synced"])
            self.assertTrue(s["enabledPlugins"]["wordpress-official-agent-skills@wordpress-official-agent-skills"])
            self.assertEqual(s["permissions"]["allow"], ["Bash(make *)"], "other keys are kept")
            ignored = subprocess.run(["git", "-C", d, "check-ignore", "-q", str(local)])
            self.assertEqual(ignored.returncode, 0, "local settings must stay out of commits")

            off = subprocess.run(["bash", script, "wordpress", d, "--off"], capture_output=True, text=True)
            self.assertEqual(off.returncode, 0, off.stderr)
            self.assertFalse(json.loads(local.read_text())["enabledPlugins"]["wp-dev-skills@synced"])
            self.assertNotEqual(subprocess.run(["bash", script, "nope", d], capture_output=True).returncode, 0)

            for profile, plugin in (("design", "impeccable@impeccable"), ("motion", "gsap-skills@gsap-skills")):
                r = subprocess.run(["bash", script, profile, d], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertTrue(json.loads(local.read_text())["enabledPlugins"][plugin])
                tmpl = json.loads((LAYER / "settings.json").read_text())["enabledPlugins"]
                self.assertIs(tmpl[plugin], False, f"{plugin} must stay off globally")


class SecurityScan(unittest.TestCase):
    def test_wp_vuln_version_ranges(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("wpv", LAYER / "bin" / "wp-vuln-check.py")
        wpv = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(wpv)
        lt = {"max_version": "5.3.2", "max_operator": "lt"}
        self.assertTrue(wpv.affected("5.3.1", lt))
        self.assertFalse(wpv.affected("5.3.2", lt))
        self.assertTrue(wpv.affected("5.3.2", {"max_version": "5.3.2", "max_operator": "le"}))
        self.assertFalse(wpv.affected("5.10", {"max_version": "5.9.9", "max_operator": "le"}))
        rng = {"min_version": "2.0", "min_operator": "ge", "max_version": "2.4", "max_operator": "lt"}
        self.assertFalse(wpv.affected("1.9", rng))
        self.assertTrue(wpv.affected("2.0", rng))
        self.assertTrue(wpv.affected("9.9", {"unfixed": "1"}), "unfixed with no range affects every version")
        self.assertFalse(wpv.affected("9.9", {}))

    def test_scan_skips_missing_tools_and_never_needs_network_to_start(self):
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ, PATH="/usr/bin:/bin")  # no ~/.local tools; gitleaks may be in /usr/bin
            r = subprocess.run(["bash", str(LAYER / "bin" / "security-scan"), d], env=env,
                               capture_output=True, text=True, timeout=60)
            self.assertIn("WordPress plugins", r.stdout)
            self.assertIn("security-scan:", r.stdout)

    def test_osv_without_lockfiles_is_not_a_finding(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as fake:
            Path(fake, "osv-scanner").write_text("#!/bin/sh\nexit 128\n")
            os.chmod(Path(fake, "osv-scanner"), 0o755)
            env = dict(os.environ, PATH=f"{fake}:/bin")  # only the fake scanner; other tools skip
            r = subprocess.run(["bash", str(LAYER / "bin" / "security-scan"), d], env=env,
                               capture_output=True, text=True, timeout=60)
            self.assertIn("no lockfiles", r.stdout)
            self.assertIn("security-scan: no findings", r.stdout)
            self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()

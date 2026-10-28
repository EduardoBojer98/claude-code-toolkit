# Usage

Day-to-day use of the Claude Code setup. Architecture: [ARCHITECTURE.md](ARCHITECTURE.md).

## Install or update on a machine

```bash
cd ~/Documents/projects/claude-setup && git pull
bash claude-code/install.sh --dry-run   # see what changes
bash claude-code/install.sh
bash scripts/test.sh                    # offline checks
```

Then start a new session and check `/agents` (Explore, implementer, researcher, test-runner), `/skills`,
`/hooks` and `/status`.

## Everyday work

You don't need to name agents; the global CLAUDE.md tells the lead when to delegate. Examples:

| You say | What happens |
|---|---|
| "Where is the cart total calculated?" | Lead greps itself, or sends `Explore` (Haiku) across a big repo |
| "Run the tests and tell me what fails" | `test-runner` (Haiku) runs them; only failures come back |
| "What changed in ACF 6.4 for blocks?" | `researcher` (Sonnet) with Context7 + official docs, returns sources |
| "Add a `featured` toggle to the hero section" | Lead plans; may hand `implementer` (Sonnet) the exact files + check |
| "The checkout is 500ing" | `debug` skill: reproduce → isolate → prove cause → minimal fix |
| "Build/review this landing page" | `web-dev-standards` loads + only the stack reference it needs |

Force a route when you want one:
- "Use the Explore agent to …", "Have test-runner run `npm test`", "Ask the researcher …"
- Cheap whole session: `/model sonnet` (or `claude --model sonnet`); hard problem: `/model opus`, `/effort xhigh`.
- Review: `/code-review` (correctness), `/security-review` (pending changes), `/simplify` (cleanup).

## Workflows

- **Debug**: `/debug` or describe the bug. Stack commands (Lando, WP-CLI, Shopify, Vite, CI) are in
  `claude-code/skills/debug/references/stack-diagnostics.md`.
- **Web build/review**: `web-dev-standards` → Definition of Done in its §4.
- **Toolkit review / "is there something better?"**: `toolkit-maintainer`.
- **New client project**: copy `templates/CLAUDE.md` to the repo root and fill in commands. WordPress sites
  on the CodeMate starter already have `AGENTS.md`.

## Keep context and usage down

- `/clear` between unrelated tasks; `/compact keep goal, decisions, files changed, failing checks` for long ones.
- `/usage` shows plan usage and what consumed it (skills, agents, MCP); `/context` shows what loads each turn.
- Name files/functions in requests; vague asks cause broad scans.
- Plugins only useful for one kind of project are off globally. Turn them on for one project (writes its
  gitignored `.claude/settings.local.json`; `--off` reverts):

  ```bash
  bash ~/Documents/projects/claude-setup/claude-code/enable-plugins.sh wordpress ~/path/to/wp-site
  bash ~/Documents/projects/claude-setup/claude-code/enable-plugins.sh seo ~/path/to/site
  ```

  `wordpress` = WordPress Dev Skills + wordpress-official-agent-skills (~3.6k tokens/request), `seo` = searchfit-seo.
  Add a profile by editing `PROFILES` in that script.

## Swap in a better tool (example: a design skill)

1. Try it in Claude Code first: `/plugin marketplace add <owner/repo>` + `/plugin install <name>`, or put a
   skill folder in `claude-code/skills/<name>/` and re-run the installer.
2. If it replaces something, hide the old one in `claude-code/settings.json`:
   `skillOverrides: {"<skill>": "off"}` for skills, `enabledPlugins: {"<plugin>@<marketplace>": false}` for plugins;
   re-run `bash claude-code/install.sh`.
3. Point routing at it: edit the "New page, section, redesign" row in `skills/web-dev-standards/SKILL.md` §2
   (one design skill at a time).
4. Archive the old one under `archive/` with a row in `archive/README.md` (never delete).
5. `claude -p "/context"` to check the token cost, `bash scripts/test.sh`, then note it in `DECISIONS.md`,
   `manifest.json` and `CHANGELOG.md`. If the skill should also exist on claude.ai, upload the folder there
   (Settings → Capabilities → Skills) and add `"anthropic-skills:<name>": "off"` to `skillOverrides` so it doesn't list twice.

Or ask: *"Use toolkit-maintainer to replace <old> with <new>"*: section 8b of that skill follows the same steps.

## Change routing

- Agent model: edit `model:` in `claude-code/agents/<agent>.md` (`haiku` | `sonnet` | `opus` | `fable` | `inherit`).
- Default for unnamed agents: `env.CLAUDE_CODE_SUBAGENT_MODEL` in `~/.claude/settings.json`.
- New agent: add `claude-code/agents/<name>.md` (copy an existing one; keep `disallowedTools: Agent` and an
  Output section), re-run the installer, add a row to the routing table in `claude-code/CLAUDE.md`.

## Troubleshooting

| Symptom | Check |
|---|---|
| Agent/skill missing | `ls -l ~/.claude/agents ~/.claude/skills`; re-run installer; new session |
| A command is blocked "by guard-bash/guard-secrets" | Intended for secrets. False positive → adjust the pattern in `claude-code/hooks/`, add a test in `claude-code/tests/test_config.py` |
| Settings ignored | `/status` (Setting sources), `claude doctor`; a project `.claude/settings.json` overrides yours |
| Playwright / Shopify MCP "failed to connect" | Node isn't installed: see SETUP-LINUX.md §2 |
| Figma "needs authentication" | `/mcp` → Figma → authenticate (or disable the connector on claude.ai) |
| Undo the install | Remove the symlinks in `~/.claude` and restore `~/.claude/settings.json.bak-<time>` |

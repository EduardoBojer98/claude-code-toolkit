# How to — manual for every part of this setup

Everything you can do by hand, with the exact command. Paths assume the repo is at
`~/Documents/projects/claude-setup`. In the commands below, `$R` means that path; set it once per terminal:

```bash
set -x R ~/Documents/projects/claude-setup     # fish
# export R=~/Documents/projects/claude-setup  # bash/zsh
```

Commands starting with `/` are typed **inside** a Claude Code session; everything else runs in a terminal.
How the pieces fit: [ARCHITECTURE.md](ARCHITECTURE.md). Why: [AUDIT.md](AUDIT.md), [DECISIONS.md](DECISIONS.md). Numbers: [BENCHMARKS.md](BENCHMARKS.md).

---

## Quick reference

| I want to… | Do this |
|---|---|
| Check that everything works | `bash $R/scripts/doctor.sh` (live, free) and `bash $R/scripts/test.sh` (offline) |
| Install / update the setup | `git -C $R pull && bash $R/claude-code/install.sh` |
| Use a cheaper / stronger model now | `/model sonnet` · `/model opus` · `/model haiku` |
| Think harder / cheaper on this task | `/effort xhigh` · `/effort medium` |
| Run a search or tests without filling my context | "Use the Explore agent to…" · "Have test-runner run …" |
| Debug something | `/debug` or describe the bug |
| Build/review a website | just ask; `web-dev-standards` loads itself |
| WordPress skills in a WP project | `bash $R/claude-code/enable-plugins.sh wordpress <project-dir>` |
| Design tools (Impeccable) in a project | `bash $R/claude-code/enable-plugins.sh design <project-dir>`, new session, `/impeccable craft` |
| GSAP skills in a project that uses GSAP | `bash $R/claude-code/enable-plugins.sh motion <project-dir>` |
| Security check before deploy | `security-scan` in the project, then `/security-review` in Claude Code ([§19](#19-security-scan)) |
| Set up claude.ai | [claude-ai/SETUP.md](claude-ai/SETUP.md) |
| Use Figma | `claude plugin enable figma@claude-plugins-official`, new session, `/mcp` → Figma → sign in |
| See what fills my context / usage | `/context` · `/usage` |
| Start fresh between tasks | `/clear` |
| Back up this machine's setup | `bash $R/scripts/sync-local.sh` |
| Replace a tool with a better one | [Swap a tool](#14-swap-in-a-better-tool-example-a-design-skill) |

---

## 1. Check health

```bash
bash $R/scripts/doctor.sh     # tools, links, settings, plugins, MCP servers, context size. No model calls.
bash $R/scripts/test.sh       # JSON/shell syntax, layer tests (agents, skills, hooks, installer), ccfb tests
claude doctor                 # Claude Code's own install check
```

Inside a session: `/status` (which settings files loaded), `/agents`, `/skills`, `/hooks`, `/mcp`, `/plugin`.

## 2. Install, update, undo

| Task | Command |
|---|---|
| First install on a machine | follow [SETUP-LINUX.md](SETUP-LINUX.md), then `bash $R/claude-code/install.sh` |
| Preview what the installer changes | `bash $R/claude-code/install.sh --dry-run` |
| Links only, don't touch settings | `bash $R/claude-code/install.sh --no-settings` |
| Pull repo changes | `git -C $R pull`. Skills, agents, hooks and CLAUDE.md are symlinks, so they update immediately; start a new session |
| Apply a change to `claude-code/settings.json` | re-run `bash $R/claude-code/install.sh` (your existing values win; lists are merged) |
| Undo | delete the symlinks (`~/.claude/CLAUDE.md`, `~/.claude/agents/*.md`, `~/.claude/skills/{debug,web-dev-standards,toolkit-maintainer}`, `~/.claude/hooks/claude-setup`) and restore `~/.claude/settings.json.bak-<time>` |
| Update Claude Code itself | `claude update` |

The installer never deletes: anything in its way becomes `*.bak-<time>`. Re-running it is safe.

## 3. Models and effort

| Task | How |
|---|---|
| Switch model for this session | `/model` (picker) or `/model sonnet`, `/model opus`, `/model haiku`; at start: `claude --model sonnet` |
| Set the default model | `/model` saves your pick; or `"model": "claude-opus-5-5"` in `~/.claude/settings.json` |
| Effort (thinking depth) | `/effort low|medium|high|xhigh|max`; default is `effortLevel` in `~/.claude/settings.json` (`high`) |
| One session with other settings | `claude --settings '{"effortLevel":"xhigh"}'` |

Rule of thumb: Sonnet + `high` for normal work; Opus or `xhigh` for architecture, security, nasty bugs;
Haiku for quick lookups. Switching model mid-session re-reads the context uncached once.

## 4. Agents (delegation to cheaper models)

| Agent | Model | Use it for | Ask like |
|---|---|---|---|
| `Explore` | Haiku | find files, definitions, usages (read-only) | "Use the Explore agent to find where the cart total is calculated (medium)" |
| `test-runner` | Haiku | run tests/lint/build, get only failures | "Have test-runner run `npm test` and `npm run lint`" |
| `researcher` | Sonnet | docs/web question with sources | "Ask the researcher what changed in ACF 6.4 block registration" |
| `implementer` | Sonnet | a change you've already specified | "Have implementer add X to `a.php` and `b.js`; check with `npm test`" |
| `general-purpose` | Sonnet (default) | other independent multi-step work | "Use a general-purpose agent to …" |

- Usually you don't name them: the global CLAUDE.md tells the main session when to delegate.
- Force Opus for one delegated job: "use an agent with model opus to …".
- **Change an agent's model:** edit `model:` in `$R/claude-code/agents/<name>.md` (`haiku`, `sonnet`, `opus`, `fable`, `inherit`). Takes effect next session.
- **Default model for unnamed agents:** `env.CLAUDE_CODE_SUBAGENT_MODEL` in `~/.claude/settings.json`.
- **Add an agent:** copy an existing file in `$R/claude-code/agents/`, change `name`, `description`, `model`, `tools`; keep `disallowedTools: …Agent` and an `Output` section. Run `bash $R/claude-code/install.sh`, then `bash $R/scripts/test.sh`. Add a row to the routing table in `$R/claude-code/CLAUDE.md`.
- **Remove an agent:** delete its file in the repo and the symlink in `~/.claude/agents/`.
- See what agents exist: `/agents`. Plugins add their own (e.g. `impeccable:*`).

## 5. Skills

| Task | How |
|---|---|
| List skills | `/skills` |
| Use one explicitly | `/debug`, `/web-dev-standards`, `/toolkit-maintainer`, `/impeccable`, … |
| Edit an own skill | edit `$R/skills/<name>/SKILL.md` (or `$R/claude-code/skills/debug/`); it's live next session |
| Add a Claude Code-only skill | `mkdir $R/claude-code/skills/<name>` with a `SKILL.md` (`name`, `description` frontmatter), add a `link` line for it in `claude-code/install.sh`, re-run the installer |
| Add a skill for claude.ai too | put it in `$R/skills/<name>/`, zip the folder, upload in claude.ai **Settings → Capabilities → Skills**; add `"anthropic-skills:<name>": "off"` to `skillOverrides` so Claude Code doesn't list the synced copy twice |
| Hide a skill / show only its name | `skillOverrides` in `~/.claude/settings.json` (or the repo template + installer): `"off"`, `"name-only"`, `"user-invocable-only"`, `"on"`. Or `/skills`, Space to cycle, Esc to save (saves for the current project only) |
| Big skills | keep `SKILL.md` short; put detail in `references/*.md` and link it (see `skills/web-dev-standards/`) |

Own skills: `web-dev-standards` (standards + routing; per-stack files in `references/`),
`debug` (root-cause workflow + `references/stack-diagnostics.md`), `toolkit-maintainer` (reviews this repo).

## 6. Plugins

| Task | Command |
|---|---|
| List with status | `claude plugin list` |
| What a plugin adds and its token cost | `claude plugin details <name>` |
| Turn on / off everywhere | `claude plugin enable <name>@<marketplace>` / `claude plugin disable <name>@<marketplace>` |
| Turn on for one project only | `bash $R/claude-code/enable-plugins.sh <profile> <project-dir>` (`--off` to undo) |
| Install | `claude plugin marketplace add <owner/repo>` then `claude plugin install <name>@<marketplace> --scope user` |
| Update | `claude plugin marketplace update` then `claude plugin update <name>@<marketplace>` |
| Options | `claude plugin configure <name>@<marketplace>`; or in a session `/plugin` |
| Uninstall | `claude plugin uninstall <name>@<marketplace>` |

Per-project profiles (in `claude-code/enable-plugins.sh`, edit `PROFILES` to add your own):

| Profile | Plugins | Cost when on |
|---|---|---|
| `wordpress` | WordPress Dev Skills + wordpress-official-agent-skills | ~3.6k tokens/request |
| `seo` | searchfit-seo | ~2k |
| `figma` | figma | ~2.4k |
| `design` | impeccable | ~0.2k listing + its hooks' output after edits |
| `motion` | gsap-skills (8 skills) | ~0.8k (estimate) |

What's installed and why:

| Plugin | Default | Notes |
|---|---|---|
| a11y-enforcer, perf-profiler, playwright, caveman | on (synced from claude.ai) | caveman only acts when you say "caveman mode" |
| impeccable | off (profile `design`) | the design skill: `/impeccable craft`, `critique`, `polish`, `audit`; telemetry off (`npx impeccable telemetry off`) |
| gsap-skills | off (profile `motion`) | install once: `claude plugin marketplace add greensock/gsap-skills && claude plugin install gsap-skills@gsap-skills --scope user`, then `claude plugin disable gsap-skills@gsap-skills` |
| ponytail | on | minimal-code style; levels `lite`/`full`/`ultra` ("ponytail lite"); avoid `ultra` on client sites; `/ponytail-help` |
| session-dashboard (own) | on | band above the prompt + `/dash` panel: agents (type, model, status, cost, tools, skills), skills and who loaded them, tokens, cost, context, tools, files. Options: `claude plugin configure session-dashboard@claude-setup`. After a repo change: `claude plugin marketplace update claude-setup && claude plugin update session-dashboard@claude-setup` |
| figma | off | see [§8](#8-figma-sign-in-when-needed-switch-accounts) |
| searchfit-seo, WordPress Dev Skills (+ dependency) | off | per-project profiles above |

## 7. MCP servers

| Task | Command |
|---|---|
| Status | `claude mcp list` (or `/mcp` in a session) |
| Details | `claude mcp get <name>` |
| Add (user-wide) | `claude mcp add --scope user --transport stdio <name> -- <command> <args>` / `--transport http <name> <url>` |
| Remove | `claude mcp remove <name> --scope user` |
| Sign in / out | `/mcp` → server → authenticate / clear; or `claude mcp login <name>` / `claude mcp logout <name>` |

Current servers: **Context7** and **Claude Docs** (claude.ai connectors), **Playwright** (plugin, uses Google Chrome),
**shopify-dev-mcp** pinned to 1.18.0. Upgrade Shopify:
`claude mcp remove shopify-dev-mcp --scope user` then
`claude mcp add --scope user --transport stdio shopify-dev-mcp -- npx -y @shopify/dev-mcp@<version>`
(latest: `npm view @shopify/dev-mcp version`).

## 8. Figma: sign in when needed, switch accounts

1. `claude plugin enable figma@claude-plugins-official` (or `bash $R/claude-code/enable-plugins.sh figma <project-dir>` for one project).
2. Start a new session → `/mcp` → **figma** → Authenticate → sign in with the Figma account for this job.
3. Switch account: `/mcp` → figma → Clear authentication (or `claude mcp logout plugin:figma:figma`), then authenticate again with the other account.
4. Done: `claude plugin disable figma@claude-plugins-official` (saves ~2.4k tokens per request).

The claude.ai "Figma" connector also shows "needs authentication". That's harmless, because nothing loads until it's used. Disconnect it on claude.ai if it bothers you.

## 9. Hooks (automatic guards)

| Hook | When | Does |
|---|---|---|
| `guard-secrets.sh` | before Edit/Write | blocks content with live-looking API keys or private keys (allows `*.example`, fixtures, placeholders) |
| `guard-bash.sh` | before Bash | blocks commands that print `.env`, SSH private keys, `.credentials.json`, cloud/npm creds (allows `.env.example`, `grep -q`/`-c`) |
| `format-file.sh` | after Edit/Write | runs the project's own Prettier on that file, only if the project has a Prettier config + local install |

- See them: `/hooks`. Files: `$R/claude-code/hooks/` (linked to `~/.claude/hooks/claude-setup/`).
- **False positive?** Edit the pattern in the script, add a case to `$R/claude-code/tests/test_config.py`, run `bash $R/scripts/test.sh`.
- **Need to read a secret yourself?** Do it in your own terminal; the guard only applies to Claude.
- **Turn one off:** remove its entry under `hooks` in `~/.claude/settings.json` (re-running the installer adds it back).
- **Test a hook by hand:** `echo '{"tool_input":{"command":"cat .env"}}' | ~/.claude/hooks/claude-setup/guard-bash.sh; echo $status` (fish) → `2` = blocked.

## 10. Permissions

Rules live in `~/.claude/settings.json` → `permissions` (template: `$R/claude-code/settings.json`).

- `allow`: runs without asking (read-only git/gh, `rg`, lint/test/build scripts, docs sites).
- `ask`: always confirms (push, `reset --hard`, `rm -rf`, DB imports, Lando rebuild/destroy, `shopify theme push/publish`, edits in `vendor/`, `node_modules/`, WP core, lockfiles).
- `deny`: never (reading `.env*` except examples, SSH keys, credentials; `git push --force`; `gh repo delete`).

Add a rule: append to the list in the repo template and re-run the installer (or edit `~/.claude/settings.json`
directly). Syntax: `Bash(npm run e2e *)`, `Read(~/secrets/**)`, `Edit(**/dist/**)`, `WebFetch(domain:example.com)`.
Answering "Yes, don't ask again" saves the rule in the project's `.claude/settings.local.json`.

## 11. Instructions (CLAUDE.md)

| File | Scope | Edit |
|---|---|---|
| `$R/claude-code/CLAUDE.md` → `~/.claude/CLAUDE.md` | every project | keep it < 100 lines (a test checks); move detail into skills |
| `<project>/CLAUDE.md` or `AGENTS.md` | one project, committed | start from `$R/templates/CLAUDE.md` (stack, commands, "done means", don't-touch list) |
| `<project>/CLAUDE.local.md` | you, one project | personal notes, not committed |

## 12. Context and usage

| Task | How |
|---|---|
| What loads every request | `/context` (or free from the terminal: `claude -p "/context"`) |
| Plan usage + what consumed it | `/usage` (`d`/`w` for day/week; `f` applies fixes) |
| New task, drop old context | `/clear` (free) |
| Long task, keep the essentials | `/compact keep goal, decisions, files changed, failing checks` |
| Re-measure like BENCHMARKS.md | `claude -p "/context" \| sed -n '1,25p'` |

Habits: name files/functions in requests; one task per session; let agents absorb noisy output.

## 13. Projects by stack

| Stack | First time in a project |
|---|---|
| WordPress (Lando) | `bash $R/claude-code/enable-plugins.sh wordpress .`; CodeMate starter projects already have `AGENTS.md`; others: copy `$R/templates/CLAUDE.md` |
| Shopify theme | Shopify Dev MCP is on; ask to "validate with Theme Check"; `shopify theme dev` on an unpublished theme |
| React + Vite | `npx skills add vercel-labs/agent-skills --skill react-best-practices` in the project |
| SEO work | `bash $R/claude-code/enable-plugins.sh seo .` |
| Any | `cp $R/templates/CLAUDE.md ./CLAUDE.md` and fill in commands |

Node: `nvm install <version>` (fish, nvm.fish), then re-run `bash $R/claude-code/install.sh` so Claude Code sees the new Node.

## 14. Swap in a better tool (example: a design skill)

1. Install the candidate (plugin: §6; skill: §5).
2. Compare it with the current one on a real page: `/impeccable` vs the new one.
3. If it wins, hide the old one: `claude plugin disable impeccable@impeccable` (or `skillOverrides` for a skill), and add the same to `$R/claude-code/settings.json` so new machines match.
4. Point routing at it: edit the "New page, section, redesign" and "UI work about to be called done" rows in `$R/skills/web-dev-standards/SKILL.md` §2 (one design skill at a time).
5. Archive the old one in `$R/archive/` + a row in `$R/archive/README.md` (never delete).
6. `claude -p "/context"` for the cost, `bash $R/scripts/test.sh`, then note it in `DECISIONS.md`, `manifest.json`, `CHANGELOG.md`.
7. If claude.ai should use it too, upload/enable it there.

Or say: *"Use toolkit-maintainer to replace <old> with <new>"*. Section 8b of that skill follows these steps.

## 15. Backups and this repo

| Task | Command |
|---|---|
| Snapshot this machine's Claude Code setup (secrets redacted) | `bash $R/scripts/sync-local.sh` (add `--push` to commit + push) |
| Refresh claude.ai plugin snapshots | `bash $R/scripts/refresh-snapshot.sh` (inside a claude.ai session only) |
| Retire something | move it to `archive/`, add a row to `archive/README.md`. Nothing is deleted |
| Save repo changes | `git -C $R add -A && git -C $R commit -m "chore: …" && git -C $R push` |

Git identity isn't set globally on this machine. Set it once with
`git config --global user.name "Eduardo Eugen Bojer"` and `git config --global user.email <email>`.

## 16. Monthly toolkit review

Manual since 2026-11-01 (the scheduled task is disabled): ask *"run the monthly toolkit review"* once a month.
It writes `reviews/YYYY-MM.md` and opens a PR. On demand: *"review my toolkit"* or *"is there something better than X?"*. Process: [MAINTENANCE.md](MAINTENANCE.md).

## 17. Free-model fallback (ccfb, optional)

```bash
bash $R/fallback/install.sh --settings
nano ~/.config/claude-fallback/.env      # OPENROUTER_API_KEY / GEMINI_API_KEY (free)
ccfb doctor
claude-fb                                # start Claude Code through the fallback
```

Details: [fallback/README.md](fallback/README.md).

## 18. Troubleshooting

| Symptom | Fix |
|---|---|
| `doctor.sh` says a link is missing | `bash $R/claude-code/install.sh` |
| Agent or skill not showing | new session; `ls -l ~/.claude/agents ~/.claude/skills`; `/agents`, `/skills` |
| Settings ignored | `/status` → Setting sources; a project `.claude/settings.json` or `settings.local.json` overrides yours; `claude doctor` |
| MCP "failed to connect … npx" | Node not visible: `bash $R/claude-code/install.sh` (links nvm Node into `~/.local/bin`) |
| Plugin shows `Error: Dependency … not installed` | `claude plugin list`, install the named dependency (`claude plugin marketplace add` + `install`) |
| "Blocked by guard-…" | intended for secrets; see §9 for false positives |
| Too many permission prompts | add `allow` rules (§10) or run `/fewer-permission-prompts` |
| Usage climbing fast | `/usage` attribution; `/clear` between tasks; lower `/effort`; disable unused plugins (§6) |
| Figma "needs authentication" | expected until you need it (§8) |

## 19. Security scan

One-time install (CachyOS):

```bash
sudo pacman -S gitleaks osv-scanner python-pipx
pipx install semgrep
```

| Task | Command |
|---|---|
| Scan a project before deploy | `security-scan` (in the project) or `security-scan <dir>` |
| Then the AI review of your changes | `/security-review` inside Claude Code |
| Only secrets / only dependencies | `gitleaks git . --redact -v` · `osv-scanner scan source -r .` |
| WordPress plugins only | `lando wp plugin list --format=json \| python3 $R/claude-code/bin/wp-vuln-check.py` |
| A finding is a false positive | gitleaks: add the path to a `.gitleaks.toml` allowlist (see this repo's); semgrep: `// nosemgrep` on that line with a reason |

What leaves your machine: OSV-Scanner sends package names + versions to osv.dev; the WordPress check sends plugin
slugs + versions to wpvulnerability.net; semgrep downloads rules (`--metrics=off`). Secrets and code stay local.
Missing tools are skipped with the install command; the scan exits 1 when anything is found.

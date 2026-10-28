# Changelog

## 2026-10-28: session-dashboard 0.2.0
- The mod now shows every subagent (type, model, status, duration, tokens, cost, task, tools, skills, nested by who spawned it), the cost split lead/agents and agents per model, plus every skill loaded and who loaded it (lead, an agent, or you). Band: `N agents (k running) · M skills`. Tests cover the new views; validated and type-checked.

## 2026-10-28 (evening): manual and health check
- `HOW-TO.md` (replaces `USAGE.md`): every feature with its manual command: install/undo, models/effort, agents, skills, plugins and per-project profiles, MCP, Figma sign-in and account switching, hooks, permissions, CLAUDE.md, context/usage, stacks, swapping tools, backups, review, fallback, troubleshooting.
- `scripts/doctor.sh`: live health check (tools, links, settings vs template, plugins, MCP status, context size); no model calls.
- Re-verified: doctor all green, 53 offline tests pass, live smoke test (Explore + test-runner on Haiku, guard-bash and guard-secrets blocking) passed at $0.008 list.

## 2026-10-28 (later): local tools on CachyOS
- Node 24.22.1 via nvm.fish; `install.sh` links the newest nvm Node into `~/.local/bin` so Claude Code finds `npx` (fish nvm hooks don't apply to it).
- Playwright MCP connected (uses Google Chrome); Shopify Dev MCP 1.18.0 added (pinned).
- Installed plugins: figma, impeccable (telemetry off), session-dashboard, ponytail (ledger on, no webhook).
- WordPress Dev Skills v1.3.0 was disabled (missing dependency); installed `wordpress-official-agent-skills` 1.0.0 on approval, so it loads again (+3.6k tokens/request).
- WordPress Dev Skills and its dependency scoped to WordPress projects: off in user settings, on per project with the new `claude-code/enable-plugins.sh wordpress <dir>` (also `seo` for searchfit-seo). Saves ~3.6k tokens/request elsewhere.
- Figma plugin off by default (used rarely, accounts switch per job): enable when needed (`claude plugin enable figma@claude-plugins-official` or `enable-plugins.sh figma <dir>`), sign in via `/mcp` then. Skills listing 6.4k → 4k.
- Context: skills listing 3.2k → 6.4k with the new plugins, 10k with the WordPress plugins (BENCHMARKS.md).

## 2026-10-28: Claude Code layer, model routing, CachyOS
- New `claude-code/` installed into `~/.claude` by an idempotent `install.sh` (symlinks; settings merged with your values winning; backups `*.bak-<time>`, nothing deleted):
  - Global `CLAUDE.md` (~60 lines): recon before editing, root cause first, minimal diffs, verify-then-report, model routing table, git safety, context hygiene.
  - Agents: `Explore` (overrides the built-in; Haiku, read-only), `test-runner` (Haiku), `researcher` (Sonnet), `implementer` (Sonnet). None can spawn agents; all have `maxTurns` and a fixed output format.
  - Settings template: `CLAUDE_CODE_SUBAGENT_MODEL=sonnet`, `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=2`, `effortLevel: high` (if unset), allow/ask/deny permissions, hooks, `skillOverrides` for 13 synced claude.ai skills and the duplicate synced copies of own skills, `searchfit-seo@synced` off in Claude Code.
  - Hooks: `guard-secrets` (blocks writing live keys), `guard-bash` (blocks printing credential files), `format-file` (project Prettier only).
  - `debug` skill with per-stack diagnostics reference (Lando/WP-CLI, Shopify, Vite, Node, CI).
  - Tests (`claude-code/tests/`) and `scripts/test.sh` for every offline check.
- `web-dev-standards` v2.2: same rules, split into a 6 KB core + per-stack `references/` (progressive disclosure); delegation line follows the global routing; routes bugs to `debug`. v2.1 archived.
- `toolkit-maintainer` v1.3: checks the Claude Code layer; new "Replacing a tool" procedure. v1.2 archived.
- `SETUP-LINUX.md` rewritten for CachyOS (pacman, fish, fnm). `local/Flow-X13` (WSL) archived; new `local/rog-flow-x13`. `sync-local.sh` records a symlinked CLAUDE.md instead of copying it.
- New docs: `AUDIT.md`, `ARCHITECTURE.md`, `USAGE.md`, `BENCHMARKS.md`.
- Measured: skills listing 7.9k → 3.2k tokens per request; Haiku Explore 45% cheaper (list price) than the built-in on the same search with the same answer.

**Migration:** `git pull && bash claude-code/install.sh`, then a new session. To undo: remove the symlinks in `~/.claude` and restore `~/.claude/settings.json.bak-<time>`. To use SEO tools in one project: `{"enabledPlugins": {"searchfit-seo@synced": true}}` in its `.claude/settings.local.json`.

## 2026-10-24: sync + local Claude Code backup
- Synced with claude.ai: 6 plugins, 2 own skills and connectors match the manifest; plugin snapshots and own skills unchanged (no drift).
- New `scripts/sync-local.sh`: copies the Claude Code setup of the machine it runs on (settings, global CLAUDE.md, installed plugins and marketplaces, user MCP servers, own agents/commands/hooks/skills, status line) into `local/<machine>/`, with secrets redacted and a guard that stops on anything that looks like a live key. `--push` commits and pushes.
- First local sync from Flow-X13 (WSL). Claude Code 2.1.308; plugins figma 2.2.157, impeccable 4.7.0, ponytail 5.3.0, session-dashboard 0.1.0; MCP shopify-dev-mcp 1.17.0. Drift: hyperframes and mattpocock-skills are still enabled there. `sync-local.sh` now skips the downloaded claude.ai built-in skills (`skills/synced/`).

## 2026-10-24: session-dashboard mod
- New `mods/session-dashboard/` (v0.1.0): Claude Code mod with a band above the prompt and a `/dash` panel (tokens, estimated cost, time, context, tool calls, files edited), optional cost alert. Modeled on savvy-progress (claude-kit, MIT).
- Repo is now a plugin marketplace (`.claude-plugin/marketplace.json`) so own mods install with `/plugin install <mod> --marketplace EduardoBojer98/claude-setup`. Mods stay out of `plugins/`, which `refresh-snapshot.sh` rebuilds.

## 2026-10-22: repo cleanup and review record
- Merged all open work into `main` (fallback, Claude Code review).
- Added `reviews/2026-10.md` (first review report); removed the 16 Oct status spreadsheet `docs/web-dev-toolkit.xlsx` (superseded by DECISIONS.md and the review; still in Git history).
- `toolkit-maintainer` v1.2: checks local Claude Code tools and the fallback provider registry, runs the fallback tests; v1.1 archived.
- Monthly review task prompt v3 (CodeMate starter, fallback re-check, local tools, open items); v2 archived.
- README, MAINTENANCE (rule numbering), DECISIONS (standards v2.1, duplicate row) and manifest (skill versions/descriptions, connector status) made consistent.

## 2026-10-22: free-model fallback (ccfb)
- New `fallback/`: local gateway that passes Claude Code traffic to Anthropic unchanged and, on a plan-limit 429, serves the same session from free models (OpenRouter, Gemini; Ollama/Cerebras optional), then returns to Claude after the reset.
- `ccfb` CLI (run, status, doctor, models, handoff, resume, use-fallback), `claude-fb` launcher, `install.sh`, provider registry with sources, 43 tests (1 opt-in with the real Claude Code CLI).

## 2026-10-22: Claude Code review (WSL)
- Figma kept in Claude Code (62 uses of design-to-code in 20 days); ponytail kept by preference; hyperframes and mattpocock-skills disabled.
- 13 claude.ai-synced skills unused in Claude Code disabled per machine (~2,370 tokens a turn); duplicate user-level copies of own skills disabled.

## 2026-10-22: caveman restored
- Re-enabled by user preference; snapshot moved from `archive/plugins/` back to `plugins/`. Opt-in only ("caveman mode").

## 2026-10-22: web-dev-standards 2.1
- WordPress client sites start from the CodeMate starter (classic theme, SCF page sections, runtime CSS tokens, Lando); its `AGENTS.md` and ADR 0001 rule there. Block themes only when the Site Editor or native blocks are needed; Elementor + ACF rules apply to existing sites built that way.
- Replaces PR #1 (written against v1.0, which v2.0 replaced); its intent is carried over in full.

## 2026-10-22: lean design + engineering setup
- Added `archive/` (never deleted): VectorLab UI/UX Skills (first backup; it had been enabled outside a review), frontend-design plugin copy, caveman, figma, github; v1.0 of both own skills; the monthly task prompt. All copies verified identical to the live versions.
- `scripts/refresh-snapshot.sh` now moves snapshots of no-longer-enabled plugins to `archive/plugins/` instead of deleting them.
- `web-dev-standards` v2.0: routing per stack (WordPress/Elementor/ACF, Shopify, nopCommerce, React+Vite), working rules, pinned Context7 IDs; 1,817 words (v1.0: 2,620), all v1.0 rules kept in shorter form.
- `toolkit-maintainer` v1.1: free-first (paid only with strong evidence), archive-never-delete rule, new stack keywords.
- Added `templates/CLAUDE.md` for client projects.
- Adopted in Claude Code: Shopify Dev MCP; Impeccable (trial); Vercel react-best-practices per React project.

## 2026-10-16: initial setup
- Added own skills: `web-dev-standards` v1.0, `toolkit-maintainer` v1.0
- Installed: WordPress Dev Skills, github, playwright, A11y Enforcer, Perf Profiler; connector Context7
- Kept: frontend-design, searchfit-seo, figma, caveman
- Disabled: brightdata-plugin (needs paid account/API key)
- Created this backup repo with plugin snapshot, manifest, decisions log and monthly review process

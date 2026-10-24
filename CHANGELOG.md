# Changelog

## 2026-10-24: sync + local Claude Code backup
- Synced with claude.ai: 6 plugins, 2 own skills and connectors match the manifest; plugin snapshots and own skills unchanged (no drift).
- New `scripts/sync-local.sh`: copies the Claude Code setup of the machine it runs on (settings, global CLAUDE.md, installed plugins and marketplaces, user MCP servers, own agents/commands/hooks/skills, status line) into `local/<machine>/`, with secrets redacted and a guard that stops on anything that looks like a live key. `--push` commits and pushes.

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

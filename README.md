# Claude setup

My Claude setup for client web work (WordPress with the CodeMate starter, Elementor and ACF; Shopify;
nopCommerce; React + Vite). It holds two things:
- **Claude Code configuration** that installs into `~/.claude` on any Linux machine.
- **A backup of my claude.ai skills, plugins and connectors**, so they can be restored on a new account and kept current by a monthly review.

Last updated: 28 Oct 2026. Everything here is free to use.

**How do I…? → [HOW-TO.md](HOW-TO.md)**: every feature with the manual command.
**New machine?** Follow [SETUP-LINUX.md](SETUP-LINUX.md).
**How it works:** [ARCHITECTURE.md](ARCHITECTURE.md). **Why it looks like this:** [AUDIT.md](AUDIT.md), [BENCHMARKS.md](BENCHMARKS.md), [DECISIONS.md](DECISIONS.md).

## What's in here

| Folder / file | Contents |
|---|---|
| `claude-code/` | **Claude Code user layer**: global `CLAUDE.md`, routed subagents (Haiku/Sonnet), `debug` skill, safety and format hooks, settings template, `install.sh`, tests |
| `skills/web-dev-standards/` | **My own skill** (v2.2): standards, routing per stack, quality floors, Definition of Done. Per-stack rules are in `references/` |
| `skills/toolkit-maintainer/` | My own skill that reviews and updates this setup ([MAINTENANCE.md](MAINTENANCE.md)) |
| `mods/session-dashboard/` | My own Claude Code mod: tokens, estimated cost, time and context in a band and a `/dash` panel ([README](mods/session-dashboard/README.md)) |
| `fallback/` | **ccfb**: keeps Claude Code working on free models when the plan limit is reached ([README](fallback/README.md)) |
| `local/<machine>/` | Snapshot of each machine's Claude Code setup, written by `scripts/sync-local.sh`, secrets redacted |
| `templates/CLAUDE.md` | Starter project file for client repos |
| `plugins/` | Snapshot of every enabled claude.ai plugin, a fallback if one leaves the directory |
| `archive/` | Retired plugins, old skill versions, old snapshots and task prompts, with restore steps. Never deleted |
| `reviews/` | One report per toolkit review |
| `scripts/` | `doctor.sh` (live health check of this machine, no model calls), `test.sh` (all offline checks), `sync-local.sh` (machine snapshot), `refresh-snapshot.sh` (plugin snapshot from a claude.ai session) |
| `manifest.json`, `DECISIONS.md`, `CHANGELOG.md` | What is installed, why, and what changed |

Plugins are third-party, open-licensed (see each folder's `LICENSE`). The copies are a fallback; installing
from the plugin directory is preferred because it gets updates.

## Claude Code in one minute

```bash
bash claude-code/install.sh
bash scripts/test.sh
```

The installer links the global instructions, agents, hooks and skills into `~/.claude` and merges the settings
template; your own values win and re-running it changes nothing. The main session acts as tech lead.
Searches and test runs go to Haiku agents, docs research and bounded edits to Sonnet agents, and hard or
risky work stays on the main model. Secret reads and writes are blocked, and destructive commands ask first.

## Restore claude.ai items on a new account

1. **Own skills**: zip `skills/web-dev-standards` (include `references/`) and `skills/toolkit-maintainer`, then upload each in **Settings → Capabilities → Skills**.
2. **Plugins**: ask Claude *"Install the plugins listed in manifest.json of my claude-setup repo"*, or install them by name from the directory: WordPress Dev Skills, playwright, A11y Enforcer, Perf Profiler, searchfit-seo, caveman. If one has disappeared, upload its folder from `plugins/`.
3. **Connectors**: Context7 (free account). The GitHub plugin isn't needed because the `gh` CLI covers it.
4. **Claude Code mods**: `/plugin install session-dashboard --marketplace EduardoBojer98/claude-setup`. The repo is private, so run `gh auth login && gh auth setup-git` first.

## Updating

- Change a skill, agent or CLAUDE.md here, then run `git pull` on the machine. The files are symlinked, so nothing else is needed.
- Change `claude-code/settings.json` → re-run `bash claude-code/install.sh`.
- Swap a tool (e.g. a better design skill) → [HOW-TO.md § Swap in a better tool](HOW-TO.md#14-swap-in-a-better-tool-example-a-design-skill).
- Monthly or on demand: *"review my toolkit"* (toolkit-maintainer).

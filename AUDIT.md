# Audit — 2026-10-28

Audit of `claude-setup` and the Claude Code install on rog-flow-x13 (CachyOS, Claude Code 2.1.310,
claude.ai Pro/Max subscription), against the official docs at code.claude.com (sub-agents, skills, settings,
permissions, hooks, memory, costs; read 2026-10-28).

## Starting point

- **Repo** = backup and maintenance record for claude.ai account items (own skills, plugin snapshots,
  decisions, archive), plus ccfb (`fallback/`), the session-dashboard mod and machine snapshots. It held **no
  Claude Code configuration that was actually installed** on this machine.
- **Machine** = fresh install (2 days old): `~/.claude/settings.json` had only `theme`; no CLAUDE.md, agents,
  hooks, own skills, permissions, MCP servers or local plugins. Everything came from claude.ai sync.
- Every subagent ran on the main model (Opus); built-in Explore uses Opus on subscriptions per the docs.

## Inventory

| Component | Path | State | Overhead | Security | Action |
|---|---|---|---|---|---|
| web-dev-standards v2.1 | `skills/web-dev-standards/` (synced) | Active, valuable, but loads all stacks at once (14 KB) and said "no helper agents" | ~180 tokens listed; ~3.5k when used | — | **Improved** → v2.2: core + per-stack `references/`; delegation line updated; linked into `~/.claude/skills` |
| toolkit-maintainer v1.2 | `skills/toolkit-maintainer/` (synced) | Active, claude.ai-oriented, rarely used in Claude Code | ~120 tokens listed | — | **Improved** → v1.3 (knows `claude-code/`, swap procedure); `name-only` in Claude Code |
| 13 claude.ai built-in skills | `~/.claude/skills/synced/` | Synced, mostly unused in a terminal (prior review found zero use) | ~3.6k tokens/request | — | `off` (morning, google-workspace, import-memory, computer-use) or `name-only` (docs, docx, pptx, xlsx, pdf, skill-creator, deep-research, browsers) |
| Duplicate synced own skills | `anthropic-skills:web-dev-standards`, `…:toolkit-maintainer` | Would list twice once linked locally | ~300 tokens | — | Hidden with `skillOverrides` |
| searchfit-seo plugin | synced | 11 skills + 6 commands + 3 agents; occasional use; promotes SearchFit | ~2k tokens/request | Low | **Disabled in Claude Code** (`enabledPlugins`); still on claude.ai; re-enable per project |
| a11y-enforcer, perf-profiler | synced | Active review tools with local scripts | ~270 tokens | Local only | Keep |
| caveman | synced | Opt-in style, user preference | ~130 tokens | — | Keep |
| playwright plugin | synced, `npx @playwright/mcp@latest` | **Broken: Node not installed** | deferred | Unpinned `@latest` | Keep; install Node (SETUP-LINUX §2); pin if a release breaks |
| Context7, Claude Docs connectors | claude.ai | Connected | ~4k deferred | OAuth on claude.ai | Keep |
| Figma connector | claude.ai | **Drift**: enabled on claude.ai, needs auth; DECISIONS said disconnected | deferred | OAuth | Decide: authenticate (you implement Figma designs) or disconnect on claude.ai |
| Shopify Dev MCP, figma/impeccable/ponytail/session-dashboard plugins | were on the WSL install | Not installed on CachyOS | — | — | Reinstall when needed (SETUP-LINUX §7); Node required |
| hyperframes, mattpocock-skills | WSL only | Already retired | — | — | Stay off |
| ccfb fallback | `fallback/` | Not installed here; 43 tests pass | 0 unless used | Sees the OAuth token (stdlib only, by design) | Keep; install when wanted |
| session-dashboard mod | `mods/` | Not installed here | small | Local | Keep |
| sync-local.sh | `scripts/` | Works; copied a symlinked CLAUDE.md as a duplicate file | — | Redaction + key guard OK | Fixed: records symlinks |
| refresh-snapshot.sh | `scripts/` | claude.ai cloud-session only (`/root/.claude`) | — | — | Keep |
| WSL snapshot | `local/Flow-X13/` | Superseded by CachyOS | — | Redacted | **Archived** to `archive/local/Flow-X13-wsl` |
| SETUP-LINUX.md | | Ubuntu/apt commands; this machine is CachyOS | — | — | Rewritten for pacman/CachyOS |
| Permissions | none | Every Bash/edit prompted or relied on auto mode; nothing denied | — | **No secret-read protection** | Added allow/ask/deny rules |
| Hooks | none | — | — | **Nothing prevented writing keys into files** | Added 3 hooks |
| Effort | WSL had `xhigh` | Highest token spend per turn | high | — | Template default `high` (only if unset) |

## Problems found

1. The repo described the setup but didn't install anything in Claude Code; a new machine started empty.
2. No delegation design: all subagents (including built-in Explore) used the most expensive model.
3. ~6k tokens per request of skill/agent listings that are rarely used in a terminal.
4. No permission rules or hooks: `.env` and SSH keys were readable, force-push not gated, secrets could be written.
5. Node missing → playwright MCP (and later Shopify Dev MCP, Impeccable) can't start.
6. Drift: claude.ai Figma connector enabled despite the 2026-10-22 decision; SETUP-LINUX targeted Ubuntu.

## Changes made

See [CHANGELOG.md](CHANGELOG.md) (2026-10-28) and [ARCHITECTURE.md](ARCHITECTURE.md). In short: new `claude-code/` user
layer (CLAUDE.md, 4 routed agents, `debug` skill, 3 hooks, settings template, idempotent installer, tests);
web-dev-standards v2.2 with progressive disclosure; toolkit-maintainer v1.3; synced-skill and plugin trimming;
permissions; CachyOS setup guide; WSL snapshot archived; measured results in [BENCHMARKS.md](BENCHMARKS.md).

## Verified vs not

| Claim | Status |
|---|---|
| Agent frontmatter fields, model aliases, env vars, `skillOverrides`, `enabledPlugins`, hook schema | Per official docs, and checked by tests |
| `skillOverrides` works on synced claude.ai skills (short and `anthropic-skills:` names) | Verified with `/context` |
| `enabledPlugins: {"searchfit-seo@synced": false}` hides it; a higher scope can turn it back on | Verified with `/context` |
| Explore runs on Haiku; guard-bash blocks in a live session | Verified (stream-json smoke test) |
| `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` for general-purpose | Documented; not separately run |
| `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=2` | Documented; not separately run |
| Plan-usage savings over a real week | Not yet measurable; see BENCHMARKS.md |

## Manual steps left for you

1. ~~Install Node~~ Done 2026-10-28 (nvm.fish v24.22.1, linked by the installer). Playwright and Shopify Dev MCP connect; figma, impeccable, session-dashboard and ponytail are installed.
2. Figma: installed but **off by default** (you switch between Figma accounts and use it rarely). Turn it on when needed, then sign in with `/mcp` for the account you need at that time.
2b. ~~WordPress Dev Skills dependency~~ Installed 2026-10-28 on approval; WP Dev Skills loads again.
3. Upload `skills/web-dev-standards` (now a folder with `references/`) and `skills/toolkit-maintainer` to claude.ai
   so the account copies match v2.2 / v1.3 (Settings → Capabilities → Skills → upload zip).
4. After a week, check `/usage` attribution and add it to BENCHMARKS.md.

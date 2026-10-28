# Architecture

How the setup fits together (Claude Code 2.1.310, CachyOS, claude.ai subscription). Last updated 2026-10-28.

## Two homes, one repo

| Where it runs | What it gets | Source of truth here |
|---|---|---|
| **claude.ai** (chat, Cowork, cloud sessions) | Account skills, plugins, connectors | `skills/`, `plugins/` snapshots, `manifest.json` |
| **Claude Code on this machine** | `~/.claude` user layer + whatever claude.ai syncs down | `claude-code/` (linked in by `claude-code/install.sh`) |

claude.ai items sync into Claude Code automatically (skills to `~/.claude/skills/synced/`, plugins as `@synced`).
The `claude-code/settings.json` template trims that sync to what is useful in a terminal.

## Layers and precedence

Highest wins for scalar settings; permission lists merge across files (docs: code.claude.com/docs/en/settings).

```
managed (none on a Pro/Max plan)
└─ --settings / flags (one session)
   └─ <project>/.claude/settings.local.json   personal, per project, gitignored
      └─ <project>/.claude/settings.json      committed with a client repo
         └─ ~/.claude/settings.json           ← merged from claude-code/settings.json
```

Instructions load the same way: `~/.claude/CLAUDE.md` (global, this repo) → project `CLAUDE.md` or `AGENTS.md`
(project wins on specifics) → nested `CLAUDE.md` files load when Claude touches that subdirectory.

## Components

| Component | File(s) | Loaded when | Cost |
|---|---|---|---|
| Global instructions | `claude-code/CLAUDE.md` → `~/.claude/CLAUDE.md` | Every session | ~1.3k tokens |
| Subagents | `claude-code/agents/*.md` → `~/.claude/agents/` | Descriptions always (~340 tokens); body when spawned | per use |
| Own skills | `skills/web-dev-standards`, `skills/toolkit-maintainer`, `claude-code/skills/debug` → `~/.claude/skills/` | Description always; body on use; `references/` only when the stack needs it | per use |
| Hooks | `claude-code/hooks/*.sh` → `~/.claude/hooks/claude-setup/` | Every matching tool call (shell, < 50 ms) | no tokens unless they block |
| Settings | `claude-code/settings.json` merged into `~/.claude/settings.json` | Startup / live reload | — |
| Synced claude.ai skills | managed by claude.ai | Listing trimmed via `skillOverrides` | ~20 tokens each when `name-only` |
| Plugins | claude.ai sync (a11y-enforcer, perf-profiler, playwright, caveman) + local (figma, impeccable, ponytail, session-dashboard). Off globally, on per project with `claude-code/enable-plugins.sh`: searchfit-seo (`seo`), WordPress Dev Skills + wordpress-official-agent-skills (`wordpress`) | Skills/commands listed | see BENCHMARKS.md |
| MCP | claude.ai connectors (Context7, Claude Docs, Figma); playwright via plugin | Tool names deferred until used | ~4.7k incl. deferred |

## Model routing

The main session is the tech lead (your `/model` choice, normally Opus). Work is pushed down only when it is
independent and its output is bulky:

| Tier | Work | Mechanism | Model |
|---|---|---|---|
| 1 | Search/locate across files | `Explore` (overrides the built-in, read-only, skips CLAUDE.md) | `haiku` |
| 1 | Run tests/lint/build, summarise failures | `test-runner` (no edits) | `haiku` |
| 2 | Docs/web research with sources | `researcher` (no edits, no Bash) | `sonnet` |
| 2 | Bounded implementation with file list + check | `implementer` | `sonnet` |
| 2 | Anything else delegated | `general-purpose` via `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` | `sonnet` |
| 3 | Architecture, security, ambiguous or repeatedly failing work | Main session, or Agent tool `model: "opus"` | `opus` |

Resolution order (docs, sub-agents → "Model resolution"): per-call `model` → agent frontmatter →
`CLAUDE_CODE_SUBAGENT_MODEL` → main model. So agents pin their own tier, the default for unnamed agents is
Sonnet, and the lead can still escalate one call to Opus.

Guards against runaway delegation: custom agents cannot spawn agents (`disallowedTools: Agent`),
`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=2`, `maxTurns` on every agent, and the CLAUDE.md rules
(≤ 3 parallel agents, no two agents on the same files, no agent for a single Grep/Read).

Effort: `effortLevel: "high"` default (applied only if you have no value set). Raise per task with `/effort xhigh`.

## Delegation and verification flow

```
request → lead classifies (size, risk, uncertainty)
   ├─ small / sequential ─────────────► lead does it, verifies, reports
   └─ has independent bulky parts
        ├─ Explore (haiku): where is X?          → path:line list
        ├─ researcher (sonnet): how does API Y?  → answer + sources
        ├─ implementer (sonnet): change files A,B so check C passes → changed + verified
        └─ test-runner (haiku): run checks       → PASS/FAIL + failing items
   lead: reads the cited lines it relies on, integrates, reviews `git diff`,
         runs/assigns the targeted checks, reports files changed, checks run, open items
```

Independent review uses the built-in `/code-review` and `/security-review` skills rather than a custom agent.

## Hooks

| Event | Script | Does | On failure |
|---|---|---|---|
| PreToolUse `Edit\|Write\|MultiEdit\|NotebookEdit` | `guard-secrets.sh` | Blocks content containing live-looking keys (Anthropic, OpenRouter, OpenAI, GitHub, AWS, Google, Slack, Shopify, Stripe live, private keys). Skips `*.example`, fixtures | exit 2 → Claude is told why |
| PreToolUse `Bash` | `guard-bash.sh` | Blocks `cat/less/grep/curl …` of `.env`, SSH private keys, `.credentials.json`, cloud/npm creds. Allows `.env.example` and `grep -q/-c` | exit 2 |
| PostToolUse `Edit\|Write\|MultiEdit` | `format-file.sh` | Runs the project's own Prettier on the edited file, only if the project has a Prettier config and a local install | never blocks |

Permission rules do the deterministic part: `deny` secret reads and force-push, `ask` for pushes, resets,
DB imports, Lando rebuilds, Shopify push/publish and edits under `vendor/`, `node_modules/`, WordPress core and lockfiles,
`allow` for read-only git/gh, lint/test/build scripts and docs domains.

## Install and update

`bash claude-code/install.sh` symlinks files into `~/.claude` (anything in the way is moved to `*.bak-<time>`),
then merges the settings template: your existing scalar values win, lists are unioned. Re-running is a no-op.
Because the skills, agents and CLAUDE.md are symlinks, `git pull` updates them; only settings changes need
the installer again.

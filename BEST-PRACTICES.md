# Best practices: quality per token

Checked 2026-11-04. Sources are official Anthropic docs unless marked **(community)**.
CC = https://code.claude.com/docs/en, PL = https://platform.claude.com/docs (agent skills).
Token impact: **every turn** = paid on each request (mostly cached); **on use** = only when loaded.

## Checklist

| # | Do this | Why (source) | Token impact |
|---|---|---|---|
| 1 | Global and project `CLAUDE.md` under ~200 lines (ours: < 100, tested); concrete, checkable rules; add a rule only after the same mistake twice | Longer files cost more and are followed less ([CC/memory](https://code.claude.com/docs/en/memory), [CC/costs](https://code.claude.com/docs/en/costs)) | every turn: 1.9k for ours (measured 2026-11-04) |
| 2 | Maintainer notes in `<!-- -->` comments | Block HTML comments are stripped before injection (CC/memory) | saves the comment's tokens every turn |
| 3 | `@imports` only for organisation | Imported files load with the parent; no saving (CC/memory) | none |
| 4 | File-type rules in `.claude/rules/*.md` with `paths:` | Loaded only when matching files are touched (CC/memory) | moves them from every turn to on use |
| 5 | Procedures and reference → skills; keep `SKILL.md` < 500 lines, detail one level deep in `references/` | Only the description loads every turn; body on invoke; references when read ([CC/skills](https://code.claude.com/docs/en/skills), [PL best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)) | ~100 tokens/skill every turn |
| 6 | Skill descriptions: what + when, trigger words first, third person; ≤ 1,024 chars for claude.ai, 1,536 in Claude Code | Truncated beyond that; the description is how Claude picks it (CC/skills, PL overview) | every turn |
| 7 | Hide skills you rarely use: `skillOverrides` `name-only`/`user-invocable-only`/`off` (not for plugin skills: those go off per plugin); plugins you need in one project → per-project profile | Listings are paid every turn; `skillOverrides` doesn't affect plugin skills ([CC/skills](https://code.claude.com/docs/en/skills#override-skill-visibility-from-settings)) | **−1.6k/turn here** (measured 2026-11-04: 4.3k → 2.7k) |
| 8 | Must-always-hold rules → hooks, not prose | CLAUDE.md is context, not enforcement; hooks cost 0 tokens unless they print ([CC/features-overview](https://code.claude.com/docs/en/features-overview), CC/costs) | 0 |
| 9 | Deterministic checks → scripts/CLIs (`security-scan`, tests) | Only their output enters context (PL best practices) | output only |
| 10 | Prefer CLIs (`gh`, `rg`, `lando`, `shopify`) over MCP; disable unused MCP servers | MCP tool search defers schemas, but names + server instructions still load (CC/costs, [CC/mcp](https://code.claude.com/docs/en/mcp)) | ~10.5k deferred names here |
| 11 | Subagents for noisy or isolated work (search, test runs, docs); main thread for iterative work | Keeps logs out of the main context; their tokens still count ([CC/sub-agents](https://code.claude.com/docs/en/sub-agents)) | moves bulk off the main context |
| 12 | Cheap models for cheap work: Explore/test-runner on Haiku, research/bounded edits on Sonnet, the decision on the main model | Agents inherit the main model unless set (CC/sub-agents); measured −45% list cost on a repo search (2026-10-28) | large on delegated work |
| 13 | Effort by task: `low` renames/quick edits, `medium` routine work (the default on Opus/Sonnet/Haiku 5.5), `high` bugs and edge cases, `xhigh`/`max` hard problems. On 5.5 set it per model with `/effort` (saved in `modelSettings`); a top-level `effortLevel` in user settings doesn't apply to Opus 5.5 | Opus 5.5 at `medium` matches or beats Opus 5 at `high` in Anthropic's tests ([CC/model-config](https://code.claude.com/docs/en/model-config#adjust-effort-level)) | thinking is billed as output |
| 14 | Pick model and effort at session start | Changing model breaks the prompt cache (so does a skill with `model:` frontmatter); effort changes keep it on the 5.5 models and Fable 5.1 ([CC/prompt-caching](https://code.claude.com/docs/en/prompt-caching)) | a cache miss re-reads everything once |
| 15 | `/clear` between unrelated tasks (`/rename` first to find it later) | Free and resets context (CC/costs) | biggest single saver |
| 16 | `/compact <focus>` at a natural break, not mid-task; `/rewind` when you went down a wrong path | Compaction is itself a large request; rewind keeps the cache (CC/prompt-caching) | — |
| 17 | Plan mode (Shift+Tab) for multi-file or unclear changes; Esc early to correct | Avoids expensive rework (CC/costs) | saves wasted turns |
| 18 | Requests name files/functions, say what "done" looks like, give a check (test, screenshot) | Vague requests trigger broad scanning (CC/costs); context engineering: smallest high-signal context ([Anthropic engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)) | fewer reads |
| 19 | claude.ai: short preferences; one project per client with short instructions; remove stale knowledge; memory isolated per client project | Instructions and knowledge apply to every chat in the project ([support 9519177](https://support.claude.com/en/articles/9519177), [11817273](https://support.claude.com/en/articles/11817273), [11647753](https://support.claude.com/en/articles/11647753)) | per chat |
| 20 | Check what loads: `/context`, `/usage`, `/skill-doctor`, `/doctor prompt-audit` | Built-in measurement; `/usage` also shows the prompt-cache hit rate; `/doctor prompt-audit` needs the bundled `claude-api` skill not `off` (`name-only` is fine) ([CC/memory](https://code.claude.com/docs/en/memory), [CC/costs](https://code.claude.com/docs/en/costs)) | — |
| 21 | Subagents that get everything from the brief: `omitClaudeMd: true` (ours: all but `implementer`) | Skips CLAUDE.md in that subagent ([CC/sub-agents](https://code.claude.com/docs/en/sub-agents#supported-frontmatter-fields), v2.1.271+) | −1.9k per spawn |

Not verified this time: the claude.ai Styles help page (404), MCP tool-search token figures, a community
source with measured savings beyond our own measurements, changelog entries 2.1.300–2.1.303.

## Audit of this setup (2026-11-04)

**Already matched:** global CLAUDE.md < 100 lines with a size test; skills split into `SKILL.md` + `references/`;
routed Haiku/Sonnet agents with `maxTurns` and no nested spawning; secret guards as hooks; CLIs before MCP;
WordPress/SEO/Figma plugins per project; compact instructions; settings template + tests.

**Changed:**
| Change | Item # | Impact |
|---|---|---|
| Template hides `dataviz`, `claude-api`, `artifact-capabilities` listings (name-only) and the unused synced `cowork-plugin-management` plugin | 7 | skills listing 4.3k → 2.7k (with the re-applied template) |
| Impeccable moved to a per-project `design` profile (its 3 hooks run on every edit and stop); GSAP skills as a `motion` profile | 7, 8 | 0 every turn outside design projects |
| `security-scan` command (gitleaks, OSV-Scanner, Semgrep, WordPress advisories) + `/security-review`, in CLAUDE.md and the Definition of Done | 8, 9 | 0 tokens for the scan; output only |
| CLAUDE.md maintainer note moved into an HTML comment; per-project setup section folded in (the live file had drifted: graphify's installer replaced the symlink with a copy) | 2 | ≈ same size, drift removed |
| Project template: instructions in a comment, `.claude/rules` hint, security in "Done means" | 2, 4 | ~70 tokens less per project |
| claude.ai preferences, project instructions, memory, styles: [claude-ai/SETUP.md](claude-ai/SETUP.md) | 19 | per chat |

**Kept, consciously:** `effortLevel: high` in the template (applies to pre-5.5 models only; Opus 5.5 runs at its own
`medium` default, which the docs rate ≥ Opus 5 at `high`: raise with `/effort high` on bugs, item 13);
ponytail and caveman (your choice); Playwright on globally (used on most UI work).

**Removed from the always-on set:** nothing deleted. `npm audit` + `composer audit` are replaced in the routing by
OSV-Scanner (one tool for both); the permission rules stay so old habits still work.

## Re-audit (2026-11-04, afternoon)

| Change | Item # | Impact |
|---|---|---|
| Effort: Opus 5.5 ignores the user-level `effortLevel` and runs at `medium`; docs and README now say so, `doctor.sh` prints the real per-model level | 13 | already saving thinking tokens; no config change |
| Checklist: `skillOverrides` doesn't cover plugin skills; `/doctor prompt-audit` needs `claude-api` not `off`; skill `model:` breaks the cache; `omitClaudeMd` (item 21) | 7, 14, 20, 21 | docs only (all agents but `implementer` already use it) |
| OmniRoute: bound to 127.0.0.1 (it served `/v1` anonymously on 0.0.0.0); dropped Kimi K2.6 (now paid) and Gemma 4 (Google trains on free prompts); free-worker marked "never client code" (NVIDIA trial terms §3.3) | — | +~10 tokens/turn in CLAUDE.md and the agent description |

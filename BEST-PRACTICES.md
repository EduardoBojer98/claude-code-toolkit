# Best practices: quality per token

Checked 2026-11-04. Sources are official Anthropic docs unless marked **(community)**.
CC = https://code.claude.com/docs/en, PL = https://platform.claude.com/docs (agent skills).
Token impact: **every turn** = paid on each request (mostly cached); **on use** = only when loaded.

## Checklist

| # | Do this | Why (source) | Token impact |
|---|---|---|---|
| 1 | Global and project `CLAUDE.md` under ~200 lines (ours: < 100, tested); concrete, checkable rules; add a rule only after the same mistake twice | Longer files cost more and are followed less ([CC/memory](https://code.claude.com/docs/en/memory), [CC/costs](https://code.claude.com/docs/en/costs)) | every turn: ~1k for ours |
| 2 | Maintainer notes in `<!-- -->` comments | Block HTML comments are stripped before injection (CC/memory) | saves the comment's tokens every turn |
| 3 | `@imports` only for organisation | Imported files load with the parent; no saving (CC/memory) | none |
| 4 | File-type rules in `.claude/rules/*.md` with `paths:` | Loaded only when matching files are touched (CC/memory) | moves them from every turn to on use |
| 5 | Procedures and reference → skills; keep `SKILL.md` < 500 lines, detail one level deep in `references/` | Only the description loads every turn; body on invoke; references when read ([CC/skills](https://code.claude.com/docs/en/skills), [PL best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)) | ~100 tokens/skill every turn |
| 6 | Skill descriptions: what + when, trigger words first, third person; ≤ 1,024 chars for claude.ai, 1,536 in Claude Code | Truncated beyond that; the description is how Claude picks it (CC/skills, PL overview) | every turn |
| 7 | Hide skills you rarely use: `skillOverrides` `name-only`/`off`; plugins you need in one project → per-project profile | Listings are paid every turn (CC/skills) | **−1.6k/turn here** (measured, BENCHMARKS §5) |
| 8 | Must-always-hold rules → hooks, not prose | CLAUDE.md is context, not enforcement; hooks cost 0 tokens unless they print ([CC/features-overview](https://code.claude.com/docs/en/features-overview), CC/costs) | 0 |
| 9 | Deterministic checks → scripts/CLIs (`security-scan`, tests) | Only their output enters context (PL best practices) | output only |
| 10 | Prefer CLIs (`gh`, `rg`, `lando`, `shopify`) over MCP; disable unused MCP servers | MCP tool search defers schemas, but names + server instructions still load (CC/costs, [CC/mcp](https://code.claude.com/docs/en/mcp)) | ~10.5k deferred names here |
| 11 | Subagents for noisy or isolated work (search, test runs, docs); main thread for iterative work | Keeps logs out of the main context; their tokens still count ([CC/sub-agents](https://code.claude.com/docs/en/sub-agents)) | moves bulk off the main context |
| 12 | Cheap models for cheap work: Explore/test-runner on Haiku, research/bounded edits on Sonnet, the decision on the main model | Agents inherit the main model unless set (CC/sub-agents); measured −45% on a search (BENCHMARKS §3) | large on delegated work |
| 13 | Effort by task: `low` renames/quick edits, `medium` routine scoped work, `high` bugs and edge cases (our default), `xhigh`/`max` hard problems | Official guidance; Claude Code's own default is `medium` ([CC/model-config](https://code.claude.com/docs/en/model-config)) | thinking is billed as output |
| 14 | Pick model and effort at session start | Changing model breaks the prompt cache; effort changes keep it on the 5.5 models ([CC/prompt-caching](https://code.claude.com/docs/en/prompt-caching)) | a cache miss re-reads everything once |
| 15 | `/clear` between unrelated tasks (`/rename` first to find it later) | Free and resets context (CC/costs) | biggest single saver |
| 16 | `/compact <focus>` at a natural break, not mid-task; `/rewind` when you went down a wrong path | Compaction is itself a large request; rewind keeps the cache (CC/prompt-caching) | — |
| 17 | Plan mode (Shift+Tab) for multi-file or unclear changes; Esc early to correct | Avoids expensive rework (CC/costs) | saves wasted turns |
| 18 | Requests name files/functions, say what "done" looks like, give a check (test, screenshot) | Vague requests trigger broad scanning (CC/costs); context engineering: smallest high-signal context ([Anthropic engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)) | fewer reads |
| 19 | claude.ai: short preferences; one project per client with short instructions; remove stale knowledge; memory isolated per client project | Instructions and knowledge apply to every chat in the project ([support 9519177](https://support.claude.com/en/articles/9519177), [11817273](https://support.claude.com/en/articles/11817273), [11647753](https://support.claude.com/en/articles/11647753)) | per chat |
| 20 | Check what loads: `/context`, `/usage`, `/skill-doctor`, `/doctor prompt-audit` | Built-in measurement (CC/memory, CC/skills) | — |

Not verified this time: the claude.ai Styles help page (404), MCP tool-search token figures, a community
source with measured savings beyond our own BENCHMARKS.md.

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

**Kept, consciously:** default effort `high` (quality first; use `/effort medium` for routine work, item 13);
ponytail and caveman (your choice); Playwright on globally (used on most UI work).

**Removed from the always-on set:** nothing deleted. `npm audit` + `composer audit` are replaced in the routing by
OSV-Scanner (one tool for both); the permission rules stay so old habits still work.

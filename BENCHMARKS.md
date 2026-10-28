# Benchmarks

Measured 2026-10-28 on rog-flow-x13 (CachyOS), Claude Code 2.1.310, claude.ai subscription.
Dollar figures are Claude Code's **list-price estimates** (`total_cost_usd`/`costUSD`). On a subscription they are a proxy
for share of plan usage, not a bill. Raw outputs were not committed; the commands are given so you can re-run them.

## 1. Startup context (every request carries this, mostly as cached input)

Command: `claude -p "/context"` (free: no model call). Main model Opus 5.5.

| Category | Before | After | Change | Why |
|---|---|---|---|---|
| Skills listing | 7.9k | 3.2k | **−4.7k** | 13 synced claude.ai skills off/name-only, searchfit-seo off in Claude Code, duplicate synced copies of own skills hidden |
| Custom agents | 373 (searchfit-seo) | 343 (4 own) | −30 | searchfit agents gone, routing agents added |
| Memory files (CLAUDE.md) | 0 | 1.3k | +1.3k | new global instructions |
| **Attributable net** | | | **≈ −3.4k / request** | |
| Reported total | 23.1k–24.6k | 25.4k | see note | |

Note on the total: the "System tools" category moved from 12k (baseline runs) to 15.9k–17.4k in later runs,
**including a run with all user settings excluded** (`--setting-sources project`, 17.4k). That drift happened
independently of this setup (likely feature-flag/tool changes picked up during the session), so the totals are not
comparable. Identical repeated runs also vary by about ±1.5k depending on which MCP connectors finished connecting.
Only the category rows above are attributed to this work.

Per-skill load size when invoked: `web-dev-standards` went from 14.1 KB (all stacks) to 6.3 KB core + one 1–3 KB
stack reference, so a Shopify task no longer loads WordPress/nopCommerce/React rules.

### After installing the local plugins (same day)

Figma, Impeccable, session-dashboard and ponytail installed; Shopify Dev MCP added. `claude -p "/context"`:

| Category | Before plugins | After | Main contributors |
|---|---|---|---|
| Skills listing | 3.2k | 6.4k | figma ~2.4k (16 skills), ponytail ~0.6k, impeccable ~0.5k |
| Custom agents | 343 | 602 | plugin agents |
| Messages at start | 10 | 1.5k | rules ponytail injects into each session |
| MCP tools (deferred, names only until used) | 3.2k | 16.4k | figma, playwright, shopify-dev-mcp |

Adding WordPress Dev Skills' dependency (WP Dev Skills 20 + wordpress-official-agent-skills 17 skills) takes the skills listing to **10k**, now above the 7.9k baseline. These are only useful in WordPress repos, so they are now **off at user level and on per project** (`claude-code/enable-plugins.sh wordpress <dir>`). Verified: 6.4k skills / 0 WordPress skills in other folders, 10k / 37 in an enabled project.

That was still below the 7.9k skills baseline before the WordPress plugins. If you stop using Figma or ponytail, disabling them is the
biggest remaining lever (`claude plugin disable <name>`).

With the figma plugin also off by default (enabled only when needed): **skills listing 4k** per request,
half the 7.9k baseline.

## 2. Delegation smoke test (routing actually happens)

Scratch repo with two JS files and a fake `.env`. Lead on Sonnet:
`claude -p "Step 1: use the Explore agent to find where priceWithTax is defined and used. Step 2: run cat .env …" --model sonnet --output-format stream-json --verbose`

| Check | Result |
|---|---|
| Subagent model observed in the stream | `claude-haiku-5-5` (lead `claude-sonnet-5-5`) |
| Explore answer | correct: `src/price.js:1` definition, `src/main.js:1-2` import and call |
| `cat .env` | blocked by `guard-bash` hook; value never reached the transcript |
| Cost (list) | lead $0.070, Explore $0.0012; 1 turn, 4.4 s |

## 3. Repo search: built-in Explore vs Haiku Explore

Same prompt in this repo ("find where ccfb switches to a fallback after a plan-limit 429 and where it switches back",
breadth medium), lead on Sonnet. Built-in condition: `--setting-sources=project,local` (removes the user-level
Explore override). One run each, so treat as indicative.

| | Built-in Explore | Haiku Explore (this setup) |
|---|---|---|
| Subagent model | Sonnet 5.5 (inherited from the lead in this run) | Haiku 5.5 |
| Subagent tool calls | 5 | 5 |
| Wall time | 32 s | 29 s |
| Output tokens (all models) | 3,433 | 3,285 |
| Total cost (list) | $0.149 | **$0.082 (−45%)** |
| Answer quality | correct, `gateway.py:371-376`, `classify.py:117-128`, switch-back path | correct, same locations (`classify.py:122-129`), switch-back via probe interval |

The docs say the built-in Explore runs on the `opus` alias for subscription accounts; in this headless run it
inherited Sonnet, so against an Opus lead the saving is likely larger. Not measured.

## 4. Offline checks

`bash scripts/test.sh`: JSON + shell syntax, 9 layer tests (settings shape, agent/skill frontmatter against the
documented fields, hook allow/block cases, installer dry-run/idempotency/user-values-win), 43 ccfb tests. All pass.

## Not measured (and why)

- Bounded implementation and complex debugging scenarios end to end: they need real client repos and many
  model calls; not run to avoid spending plan usage. Re-run with the pattern in §3 on a real task when convenient.
- Plan-usage share: `/usage` → attribution (skills/agents/MCP) over a week of normal use is the right comparison.
  Check it after a week and record it here.
- Quality impact of `effortLevel: high` vs your previous `xhigh`: not benchmarked; raise per task with `/effort`.

## Re-run

```bash
claude -p "/context" | sed -n '1,25p'
claude -p "<task>" --model sonnet --output-format stream-json --verbose --allowedTools=Agent > run.jsonl
```
Read `modelUsage` and `total_cost_usd` from the final `result` line; subagent messages carry `parent_tool_use_id`.

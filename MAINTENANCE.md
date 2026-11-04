# Maintenance

This repo is kept current by the `toolkit-maintainer` skill (`skills/toolkit-maintainer/SKILL.md`).

## Cadence
- **Manual** (since 2026-11-01): run the review yourself when you have time: ask Claude *"run the monthly toolkit review"*. It researches, writes
  `reviews/YYYY-MM.md`, and opens a PR on a `review/YYYY-MM` branch. Nothing changes on the Claude account until you approve.
  The old scheduled task "Monthly toolkit review" is disabled; its prompt is in `archive/scheduled-tasks/monthly-review-2026-10-22-v3.md`.
- **On demand:** ask Claude *"review my toolkit"* or *"is there something better than X?"*.

## Rules every review follows
1. **Free first:** paid tools only with strong evidence; pricing is re-verified on the web each time, with the date.
2. **Archive, never delete:** retired tools and old skill versions go to `archive/` with restore steps.
3. **Better, not newer:** a candidate must beat the current tool for this work; ties keep the incumbent.
4. **No overlap:** two tools for one job means one goes.
5. **Every change has a source** and a click-by-click way to apply it.
6. **You approve:** installs, removals and skill edits are shown first; Claude can't do them silently.

## What gets updated
- Tools: add / remove / update / watch (see `DECISIONS.md`)
- `web-dev-standards`: facts and practices that changed (WordPress, CodeMate starter, Elementor, ACF, Shopify, nopCommerce, PHP, React, Vite, Tailwind, WCAG, Core Web Vitals, CSS)
- `fallback/config/providers.toml`: free-provider limits and models (each entry cites its source and date)
- Snapshot of plugin files (`scripts/refresh-snapshot.sh`), `manifest.json`, `CHANGELOG.md`
- Claude Code layer (`claude-code/`): run `bash scripts/test.sh`; on the machine compare `claude -p "/context"` with `BENCHMARKS.md`; swapping a tool follows [HOW-TO.md](HOW-TO.md#14-swap-in-a-better-tool-example-a-design-skill)

## Approving a review
1. Open the PR, read `reviews/YYYY-MM.md`.
2. In a Claude chat: *"Apply the YYYY-MM toolkit review."* Claude shows install cards and skill proposals, and tells you what to switch off.
3. Claude confirms what's live, merges the PR, and pushes the final state.

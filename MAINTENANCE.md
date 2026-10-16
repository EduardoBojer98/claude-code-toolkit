# Maintenance

This repo is kept current by the `toolkit-maintainer` skill (`skills/toolkit-maintainer/SKILL.md`).

## Cadence
- **Monthly** scheduled review (1st of each month, 08:54 Belgrade time; Claude scheduled task "Monthly toolkit review"). It runs unattended: it researches, writes
  `reviews/YYYY-MM.md`, and opens a PR on a `review/YYYY-MM` branch. Nothing changes on the Claude account until you approve.
- **On demand:** ask Claude *"review my toolkit"* or *"is there something better than X?"*.

## Rules every review follows
1. **Free only:** pricing is re-verified on the web each time, with the date.
2. **Better, not newer:** a candidate must beat the current tool for this work; ties keep the incumbent.
3. **No overlap:** two tools for one job means one goes.
4. **Every change has a source** and a click-by-click way to apply it.
5. **You approve:** installs, removals and skill edits are shown first; Claude can't do them silently.

## What gets updated
- Tools: add / remove / update / watch (see `DECISIONS.md`)
- `web-dev-standards`: facts and practices that changed (WordPress, PHP, theme.json, Next.js, React, Tailwind, WCAG, Core Web Vitals, CSS)
- Snapshot of plugin files (`scripts/refresh-snapshot.sh`), `manifest.json`, `CHANGELOG.md`

## Approving a review
1. Open the PR, read `reviews/YYYY-MM.md`.
2. In a Claude chat: *"Apply the YYYY-MM toolkit review."* Claude shows install cards and skill proposals, and tells you what to switch off.
3. Claude confirms what's live, merges the PR, and pushes the final state.

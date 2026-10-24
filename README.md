# Claude setup backup

My Claude skills, plugins, connectors and Claude Code setup for client web work (WordPress with
the CodeMate starter, Elementor and ACF; Shopify; nopCommerce; React + Vite), so the same setup can
be restored on a new machine, OS or account, and kept current by a monthly review.

Last updated: 22 Oct 2026. Everything here is free to use (no paid plans or paid API keys).

**New Linux machine?** Follow [SETUP-LINUX.md](SETUP-LINUX.md).

## What's in here

| Folder / file | Contents |
|---|---|
| `skills/web-dev-standards/` | **My own skill** (v2.1): design, code, platform rules per stack, accessibility, performance, SEO, security and the Definition of Done. The important one. |
| `skills/toolkit-maintainer/` | My own skill that reviews and updates this setup ([MAINTENANCE.md](MAINTENANCE.md)). |
| `mods/session-dashboard/` | **My own Claude Code mod**: band above the prompt and a `/dash` panel with tokens, estimated cost, time, context, tools and files edited. [README](mods/session-dashboard/README.md) |
| `fallback/` | **ccfb**: keeps Claude Code working on free models when the Claude plan limit is reached, then switches back. [fallback/README.md](fallback/README.md) |
| `SETUP-LINUX.md` | Clean Claude Code setup on a new Linux machine. |
| `local/<machine>/` | Claude Code setup of each machine (settings, plugins, MCP, CLAUDE.md), written by `scripts/sync-local.sh`, secrets redacted. |
| `templates/CLAUDE.md` | Starter project file for client repos (WordPress sites use the CodeMate starter's own). |
| `DECISIONS.md` | Why each tool is in, archived, watched or skipped, with sources and re-check dates. |
| `reviews/` | One report per toolkit review (`YYYY-MM.md`). |
| `CHANGELOG.md` | What changed and when. |
| `manifest.json` | Machine-readable list of skills, plugins, connectors and local Claude Code tools, with status. |
| `plugins/` | Snapshot of every enabled plugin's files, a fallback if one leaves the directory. |
| `archive/` | Retired plugins, old skill versions and old task prompts, with restore steps. Never deleted. |
| `scripts/refresh-snapshot.sh` | Refreshes `plugins/` from a Claude session; moves no-longer-enabled plugins to `archive/`. |

Plugins are third-party, open-licensed (see each folder's `LICENSE`). The copies are a fallback;
installing the current version from the plugin directory is preferred, since it gets updates.

## Restore on a new machine

Your claude.ai account keeps skills, plugins and connectors in the cloud, so a new OS usually
needs nothing restored — just sign in. Use this guide if you change accounts or something was removed.

### 1. Custom skill (web-dev-standards)
Easiest: open Claude and say:
> "Read `skills/web-dev-standards/SKILL.md` from my claude-setup repo and save it as my web-dev-standards skill."

Manual: zip the `skills/web-dev-standards` folder and upload it in **Settings → Capabilities → Skills → Upload skill**.

### 2. Plugins
Ask Claude: *"Install the plugins listed in manifest.json of my claude-setup repo"* — it will show install cards.
Or install each by name from the plugin directory (names in `manifest.json` → `directoryName`):
WordPress Dev Skills, playwright, A11y Enforcer, Perf Profiler, searchfit-seo, caveman.
Retired ones (frontend-design plugin, figma, github, VectorLab) stay off; see `archive/README.md`. Leave **brightdata-plugin** off.

If a plugin disappears from the directory, upload its folder from `plugins/` as a custom plugin
(zip the folder; ask Claude to help with the cowork-plugin skill).

### 3. Connectors
- **Context7**: connect from the connector directory, sign in with a free account.
- **Figma**: not on claude.ai (archived); used in Claude Code through its plugin (see SETUP-LINUX.md).
- **GitHub**: use the `gh` command line tool; the GitHub plugin is archived.

### 4. Claude Code on a computer
Follow [SETUP-LINUX.md](SETUP-LINUX.md): local tools (Shopify Dev MCP, Impeccable, Figma, optional
Ponytail), the free-model fallback, and which synced skills to switch off in Claude Code.

### 5. Claude Code mods
Own mods live in `mods/`; this repo is their marketplace (`.claude-plugin/marketplace.json`). In a terminal Claude Code session:
```
/plugin install session-dashboard --marketplace EduardoBojer98/claude-setup
```
The repo is private, so run `gh auth login` and `gh auth setup-git` on the machine first.

### 6. Check it works
Ask: *"List my skills, plugins and connectors and test that Context7 and Playwright respond."*

## Updating this backup
Ask Claude: *"Update my claude-setup backup repo"* after adding or changing skills/plugins.

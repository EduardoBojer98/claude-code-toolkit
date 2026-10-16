# Claude setup backup

My Claude skills, plugins and connectors for web development (WordPress + custom projects),
so I can restore the same setup on a new machine, OS or account.

Backed up: 16 Oct 2026. Everything here is free to use (no paid plans or API keys).

## What's in here

| Folder / file | Contents |
|---|---|
| `skills/web-dev-standards/` | **My own skill** — design, code, WordPress, accessibility, performance, SEO, security standards and the Definition of Done checklist. This is the important one. |
| `plugins/` | Snapshot of every enabled plugin's files (skills, commands, MCP configs) at backup time. |
| `skills/toolkit-maintainer/` | My own skill that reviews and updates this setup (see MAINTENANCE.md). |
| `DECISIONS.md` / `CHANGELOG.md` | Why each tool is in or out; history of reviews. |
| `manifest.json` | Exact list of skills, plugins (with directory names) and connectors, and which ones are on/off. |
| `docs/web-dev-toolkit.xlsx` | What each tool is for, example prompts, next steps. |

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
frontend-design, WordPress Dev Skills, github, playwright, A11y Enforcer, Perf Profiler, searchfit-seo
(optional: figma, caveman). Leave **brightdata-plugin** off.

If a plugin disappears from the directory, upload its folder from `plugins/` as a custom plugin
(zip the folder; ask Claude to help with the cowork-plugin skill).

### 3. Connectors
- **Context7**: connect from the connector directory, sign in with a free account.
- **GitHub**: after installing the github plugin, click Connect → sign in → Authorize.
- **Figma** (optional).

### 4. Check it works
Ask: *"List my skills, plugins and connectors and test that Context7 and Playwright respond."*

## Updating this backup
Ask Claude: *"Update my claude-setup backup repo"* after adding or changing skills/plugins.

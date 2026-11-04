# Claude setup

My Claude setup for client web work: WordPress (CodeMate starter, ACF/SCF, Elementor, WooCommerce), Shopify,
nopCommerce, React + Vite + TS + Tailwind and plain HTML/CSS/JS. It installs Claude Code's config on any Linux
machine, backs up my claude.ai skills and plugins, and keeps both current with a monthly review. Everything is free.

Last updated: 4 Nov 2026 · Manual for every feature: **[HOW-TO.md](HOW-TO.md)** · Why things are set up this way: **[BEST-PRACTICES.md](BEST-PRACTICES.md)**

---

## 1. What's in here

| Path | What it is |
|---|---|
| `claude-code/` | Claude Code config: global `CLAUDE.md`, cheap helper agents (Haiku/Sonnet), `debug` skill, safety hooks, `security-scan`, settings template, installer, tests |
| `skills/` | My own skills, used in both apps: `web-dev-standards` (rules + routing per stack) and `toolkit-maintainer` (reviews this setup) |
| `claude-ai/SETUP.md` | What to paste into claude.ai: preferences, project instructions, memory, skills |
| `templates/CLAUDE.md` | Starter instructions file for a client project |
| `fallback/` | Keeps Claude Code running on free models when the plan limit is hit ([README](fallback/README.md)) |
| `mods/session-dashboard/` | Token/cost/agent dashboard inside Claude Code ([README](mods/session-dashboard/README.md)) |
| `plugins/`, `archive/`, `local/` | Plugin backups, retired tools (never deleted), machine snapshots |
| `DECISIONS.md`, `manifest.json`, `CHANGELOG.md`, `BENCHMARKS.md`, `reviews/` | What's installed, why, what changed, measured token costs |

## 2. Quick start on a new Linux machine

Full walkthrough (Node, Lando, Docker): [SETUP-LINUX.md](SETUP-LINUX.md). The short version, on CachyOS/Arch:

```bash
sudo pacman -S --needed git github-cli jq ripgrep python python-pipx gitleaks osv-scanner
```

```bash
pipx install semgrep
```

```bash
gh auth login && gh auth setup-git
```

```bash
git clone https://github.com/EduardoBojer98/claude-setup.git ~/Documents/projects/claude-setup
```

```bash
cd ~/Documents/projects/claude-setup && bash claude-code/install.sh && bash scripts/test.sh
```

```bash
bash scripts/doctor.sh
```

The installer links everything into `~/.claude` (and `security-scan` into `~/.local/bin`) and merges the settings:
your own values win, and running it twice changes nothing. Then install the plugins once:

```bash
claude plugin marketplace add pbakaus/impeccable && claude plugin install impeccable@impeccable --scope user && claude plugin disable impeccable@impeccable
```

```bash
claude plugin marketplace add greensock/gsap-skills && claude plugin install gsap-skills@gsap-skills --scope user && claude plugin disable gsap-skills@gsap-skills
```

```bash
npx impeccable telemetry off
```

Both stay **off** everywhere and are turned on per project (§5). The other plugins sync from claude.ai.

## 3. Daily use

Just describe the task; the right skill loads itself. These phrases and commands are the shortcuts:

| You want to… | Say or type | What happens |
|---|---|---|
| Design a page or section | *"Design a landing page hero for `<client>`: audience …, tone …, goal: book a call"* | `web-dev-standards` + `/impeccable craft` (design projects) or `frontend-design` (claude.ai) |
| Critique / polish UI | `/impeccable critique` then `/impeccable polish` | Design review against 62 rules, then fixes |
| Add animation | *"Add a scroll reveal to the cards, CSS only"* | CSS first; GSAP skills only if the project uses GSAP |
| Security check before deploy | `security-scan` in a terminal, then `/security-review` in Claude Code | Secrets, dependencies, code patterns, WordPress plugins; then an AI review of your diff |
| Debug | `/debug` or *"The cart total is wrong after a coupon, reproduce it first"* | Reproduce → root cause → smallest fix → regression check |
| Review the toolkit | *"review my toolkit"* | `toolkit-maintainer` researches, writes `reviews/YYYY-MM.md`, opens a PR |
| Set up a project | *"set up this project"* | CLAUDE.md from the template, per-project tools, graph, Playwright ignore |

## 4. Workflows

### Design (new page, section or redesign)

1. Once per project: `bash ~/Documents/projects/claude-setup/claude-code/enable-plugins.sh design .` and start a new session.
2. Give the brief: audience, tone, the one action the page should drive, brand colours/fonts (or say "propose").
3. Claude writes a 2–3 line direction first. Approve or adjust it before any code.
4. Build: `/impeccable craft` (or just ask). Tokens for colour, type, spacing; mobile first.
5. Motion last, CSS first (transitions, scroll-driven animation, View Transitions), always with a reduced-motion fallback.
   A GSAP project: `enable-plugins.sh motion .` first.
6. Check: *"screenshot at 375, 768 and 1280 with Playwright"*, then `/impeccable critique` → `/impeccable polish`.
7. Done when the Definition of Done in `web-dev-standards` passes (accessibility, performance, no console errors).

### Security (before every deploy or client merge)

1. `security-scan` in the project folder. It runs gitleaks (secrets), OSV-Scanner (npm + Composer), Semgrep
   (code patterns) and, for WordPress with Lando or WP-CLI, a plugin advisory check. Missing tools are skipped with the install command.
2. In Claude Code: `/security-review` for the AI review of the branch's changes.
3. Fix each finding or write down why it's a false positive. Re-run until `security-scan: no findings`.
4. WordPress code: nonces + capability checks on every action, `$wpdb->prepare`, sanitize input, escape output.

Details and false positives: [HOW-TO.md §19](HOW-TO.md#19-security-scan).

## 5. Best results for fewer tokens

**Write a good request:** say *what* and *where* (file, function), what *done* looks like, and any constraint.
"Add a sticky header in `header.php` + `header.css`; no layout shift; keyboard reachable" beats "improve the header".
Paste the exact error. One task per session.

**Keep context clean:**
- `/clear` when you switch to an unrelated task (free; `/rename` first if you want to `/resume` it later).
- `/compact keep the goal, decisions, files changed, failing checks` at a natural break in a long task.
- `/rewind` when Claude went the wrong way, instead of arguing it back.
- Shift+Tab for plan mode before multi-file or unclear changes.
- `/context` shows what loads every request; `/usage` shows what used your plan.

**Model and effort** (pick at the start; switching model mid-session re-reads everything once):

| Work | Model | Effort |
|---|---|---|
| Renames, copy changes, quick fixes | Sonnet | `/effort low` or `medium` |
| Normal feature work | Sonnet or Opus | `medium`–`high` |
| Bugs, edge cases, security, architecture | Opus | `high` (default) or `xhigh` |
| Searches, test runs | Haiku agents (automatic) | low |

**What's on and off:**

| Always on | Off, on per project |
|---|---|
| web-dev-standards, debug, Playwright, ponytail, caveman (only when asked), Context7, Shopify Dev MCP; on claude.ai also A11y Enforcer and Perf Profiler | `wordpress`, `design` (Impeccable), `motion` (GSAP), `seo`, `figma` |

Turn a profile on: `bash ~/Documents/projects/claude-setup/claude-code/enable-plugins.sh <profile> <project-dir>`
(add `--off` to undo), then start a new session. It writes the project's `.claude/settings.local.json`, which is never committed.

## 6. claude.ai setup

Follow [claude-ai/SETUP.md](claude-ai/SETUP.md). In short:
1. **Settings → General → personal preferences:** paste the block from §1 of that file.
2. **Projects:** one per client; paste the project-instructions template; keep knowledge files few and current.
3. **Memory:** on; in client projects turn off "Use account memory".
4. **Skills:** upload `web-dev-standards` 2.4 and `toolkit-maintainer` 1.4 as zips (the account still has 2.1 / 1.2).

Nothing in this repo changes your account by itself.

## 7. Restore on a new claude.ai account

1. **Own skills:** zip and upload as in [claude-ai/SETUP.md §5](claude-ai/SETUP.md#5-skills-settings--capabilities--skills-some-accounts-show-features).
2. **Plugins:** ask Claude *"Install the plugins listed in manifest.json of my claude-setup repo"*, or install by name from the directory:
   WordPress Dev Skills, playwright, A11y Enforcer, Perf Profiler, searchfit-seo, caveman. If one has disappeared, upload its folder from `plugins/`.
3. **Connectors:** Context7 (free account). GitHub isn't needed; `gh` covers it.
4. **Preferences, projects, memory:** [claude-ai/SETUP.md](claude-ai/SETUP.md) §1–3.
5. **Claude Code mod:** `/plugin install session-dashboard --marketplace EduardoBojer98/claude-setup` (after `gh auth setup-git`).

## 8. Updating and the monthly review

```bash
git -C ~/Documents/projects/claude-setup pull && bash ~/Documents/projects/claude-setup/claude-code/install.sh
```

- Skills, agents and `CLAUDE.md` are symlinked, so a `git pull` is enough; re-run the installer after a `settings.json` change.
- Edit `CLAUDE.md` in the repo, never in `~/.claude` (other installers can replace the link with a copy; the installer fixes it).
- Once a month: *"run the monthly toolkit review"*. It writes `reviews/YYYY-MM.md` and opens a PR; you approve each change.
  Rules: free first, archive never delete, better not newer, one tool per job ([MAINTENANCE.md](MAINTENANCE.md)).
- Swap a tool for a better one: [HOW-TO.md §14](HOW-TO.md#14-swap-in-a-better-tool-example-a-design-skill).

## 9. More docs

| Doc | For |
|---|---|
| [HOW-TO.md](HOW-TO.md) | Every feature with its command |
| [SETUP-LINUX.md](SETUP-LINUX.md) | New machine, step by step |
| [BEST-PRACTICES.md](BEST-PRACTICES.md) | The checklist behind this setup, with sources |
| [ARCHITECTURE.md](ARCHITECTURE.md) | How the pieces fit |
| [DECISIONS.md](DECISIONS.md) | Every tool: in, watched, skipped, and why |
| [BENCHMARKS.md](BENCHMARKS.md) | Measured token costs |
| [MAINTENANCE.md](MAINTENANCE.md) | How reviews work |
| [AUDIT.md](AUDIT.md) | The October 2026 audit |
| [archive/README.md](archive/README.md) | Retired tools and how to restore them |

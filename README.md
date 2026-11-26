# Claude Code Toolkit

A ready-to-install [Claude Code](https://code.claude.com) configuration for full-stack web developers:
global instructions, helper agents, skills, safety hooks, a pre-deploy security scanner, and a way to keep
working on free models when your Claude plan limit is hit.

It's my personal daily setup (WordPress, Shopify, nopCommerce, React + Vite, plain HTML/CSS/JS, plus business
planning), published so you can fork it, take pieces, or install the lot on a Linux machine with one script.

**Highlights**

- **Short, direct replies** and a "tech lead" workflow in [`claude-code/CLAUDE.md`](claude-code/CLAUDE.md):
  read before editing, smallest diff, verify before claiming done.
- **Local model first:** digests of test output, logs, diffs and long files go to a local Ollama model
  (`local-llm`, free, nothing leaves the device); edits go to Haiku/Sonnet agents. Say "no local" for a task
  to keep it on Claude. No paid service besides the Claude subscription.
- **`/po <task>`:** an agent owns the task end to end with PM, dev and QA agents, and says done only when every acceptance criterion is proven.
- **`/council <goal>`:** build, then loop with read-only correctness, security and simplicity reviewers until all approve.
- **Safety hooks:** block secrets from being printed or written, guard risky shell commands, auto-format after edits.
- **`security-scan`:** gitleaks + OSV-Scanner + Semgrep + WordPress plugin advisories, all local CLIs.
- **`web-dev-standards` skill:** design, accessibility, performance, security and per-stack rules.
- **`/dash` session dashboard** mod: context, cost, tokens, agents and files for the current session.

**Quick start** (Linux, Claude Code installed)

```bash
git clone https://github.com/EduardoBojer98/claude-code-toolkit.git ~/Documents/projects/claude-setup
```

```bash
cd ~/Documents/projects/claude-setup && bash claude-code/install.sh && bash scripts/test.sh
```

The installer symlinks into `~/.claude`, merges settings (your existing values win) and backs up anything it
replaces. Scripts expect the clone at `~/Documents/projects/claude-setup`. Read `claude-code/CLAUDE.md` and
`claude-code/settings.json` first and adapt them to how you work: they reflect my stack and preferences.

---

## What's in here

| Path | What it is | Used by |
|---|---|---|
| `claude-code/CLAUDE.md` | Global instructions: how to work, short "caveman lite" replies, model routing, git safety | Claude Code, every session |
| `claude-code/agents/` | Helper agents: `Explore` + `test-runner` (Haiku), `researcher` + `implementer` (Sonnet), `free-worker` (Ollama Cloud, parked) | Claude Code delegates to them |
| `claude-code/skills/debug/` | Root-cause debugging workflow | Claude Code, on a bug |
| `claude-code/skills/council/` + `agents/council-*` | `/council <goal>`: build, then loop with 3 read-only reviewers (correctness, security, simplicity) until all approve; `--free` runs them on Ollama Cloud (needs credits) | Claude Code, on request |
| `claude-code/skills/po/` + `agents/po-pm`, `agents/qa` | `/po <task>`: the session is Project Owner - writes acceptance criteria, you approve the plan once, `po-pm` agents run each workstream (dev on free models, `implementer` fallback, `qa` tests), then the PO reruns every check, runs a fresh QA and `/council`, and only then says done | Claude Code, on request |
| `claude-code/hooks/` | Block secrets being printed or written; run the project's Prettier after edits; keep a `/council` loop going until approved; keep a `/po` project going until every criterion is proven | Claude Code, automatically |
| `claude-code/settings.json` | Settings template: permissions, hooks, hidden skills, plugins off by default | merged into `~/.claude/settings.json` |
| `claude-code/bin/security-scan` | Pre-deploy scan: secrets, dependencies, code patterns, WordPress plugins | you or Claude, in a project |
| `claude-code/bin/claude-free` | Claude Code on Ollama Cloud, through the local Ollama (off: needs credits) | you, only if you add credits |
| `claude-code/bin/local-llm`, `local-llm-bench` | One-shot prompt to a local Ollama model (`-m general\|code\|write`), and its benchmark | Claude (delegation), or you |
| `claude-code/skills/local-models/` | `/local-models`: find, benchmark and switch to better local models | Claude Code, on request |
| `claude-code/enable-plugins.sh` | Turns a tool group on for one project only | you, per project |
| `claude-code/install.sh` | Links all of the above into `~/.claude` and `~/.local/bin` | once, and after changes |
| `skills/web-dev-standards/` | My web standards: design, accessibility, performance, security, Definition of Done, per-stack rules | Claude Code and claude.ai |
| `mods/session-dashboard/` | `/dash` panel: context, cost, tokens, agents, skills, files | Claude Code |
| `claude-ai/SETUP.md` | What to paste into claude.ai: preferences, projects, memory, skills | claude.ai |
| `templates/CLAUDE.md` | Starter instructions file for a project | new projects |
| `scripts/doctor.sh`, `scripts/test.sh` | Live health check; offline tests | you |
| `BEST-PRACTICES.md` | The checklist this setup follows, with sources | reference |
| `prompts/audit-and-setup.md` | One prompt that audits and fixes the whole setup (incl. Ollama) | you, every month or two |

---

## 1. New machine (CachyOS / Arch)

**Packages**

```bash
sudo pacman -S --needed git curl unzip base-devel python python-pipx jq ripgrep fd github-cli docker docker-compose gitleaks osv-scanner
```

```bash
pipx install semgrep
```

**Node 24** (fish + nvm.fish; Claude Code needs it for MCP servers and plugins)

```bash
fish -c 'fisher install jorgebucaran/nvm.fish; nvm install lts; set --universal nvm_default_version 24'
```

**Claude Code** (then run `claude` once and log in with your claude.ai account)

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**GitHub** (for pushing your own fork)

```bash
gh auth login && gh auth setup-git
```

**This repo + install**

```bash
git clone https://github.com/EduardoBojer98/claude-code-toolkit.git ~/Documents/projects/claude-setup
```

```bash
cd ~/Documents/projects/claude-setup && bash claude-code/install.sh && bash scripts/test.sh && bash scripts/doctor.sh
```

The installer links everything (edit files in the repo, never in `~/.claude`), merges the settings (your own
values win), moves anything in the way to `~/.claude/claude-setup-backups/<time>/`, and is safe to re-run.

**Plugins** (install once; Impeccable and Taste Skill are on everywhere and load on design requests; motion stays off until a project turns it on)

```bash
claude plugin marketplace add pbakaus/impeccable && claude plugin install impeccable@impeccable --scope user && npx impeccable telemetry off
```

```bash
claude plugin marketplace add leonxlnx/taste-skill && claude plugin install taste-skill@taste-skill --scope user
```

Modern Web Guidance (Chrome team): web platform + Baseline guides, fetched on demand via `npx modern-web-guidance`. On everywhere.

```bash
claude plugin marketplace add GoogleChrome/modern-web-guidance && claude plugin install modern-web-guidance@googlechrome --scope user
```

Animation skills (Emil Kowalski, MIT, plain SKILL.md, no scripts): `animate`, `choreograph`, `animation-performance`,
`review-animations`, `improve-animations`, `emil-design-eng`. On everywhere, loaded on motion requests.

```bash
npx skills@latest add emilkowalski/skills --skill animate --skill choreograph --skill animation-performance --skill review-animations --skill improve-animations --skill emil-design-eng
```

```bash
claude plugin marketplace add greensock/gsap-skills && claude plugin install gsap-skills@gsap-skills --scope user && claude plugin disable gsap-skills@gsap-skills
```

```bash
claude plugin marketplace add mralaminahamed/wordpress-official-agent-skills && claude plugin install wordpress-official-agent-skills@wordpress-official-agent-skills --scope user
```

```bash
claude mcp add --scope user --transport stdio shopify-dev-mcp -- npx -y @shopify/dev-mcp@1.18.0
```

In a Claude Code session: `/plugin install session-dashboard --marketplace EduardoBojer98/claude-code-toolkit`.
Optional: ponytail (`/plugin marketplace add DietrichGebert/ponytail`).
Synced from claude.ai automatically: Playwright, WordPress Dev Skills, searchfit-seo, caveman, Context7.

**Docker + Lando** (WordPress sites; log out and in after the second command)

```bash
sudo systemctl enable --now docker.socket && sudo usermod -aG docker $USER
```

```bash
/bin/bash -c "$(curl -fsSL https://get.lando.dev/setup-lando.sh)"
```

**Ollama** (free models for delegation; see §5)

```bash
sudo pacman -S ollama-cuda && sudo systemctl enable --now ollama
```

```bash
ollama signin
```

```bash
ollama pull qwen3.5:4b && ollama pull qwen2.5-coder:3b && ollama pull phi4-mini
```

**Alpaca** (native desktop chat app for Ollama). In Preferences → Instances add an **Ollama** instance at
`http://127.0.0.1:11434` with no key, so it uses this Ollama instead of installing its own.

```bash
flatpak install flathub com.jeffser.Alpaca
```

**Open WebUI** (optional browser dashboard at http://127.0.0.1:3000; create the admin account on first open)

```bash
docker run -d --name open-webui --restart always --network host -e HOST=127.0.0.1 -e PORT=3000 -e OLLAMA_BASE_URL=http://127.0.0.1:11434 -v open-webui:/app/backend/data ghcr.io/open-webui/open-webui:main
```

---

## 2. Daily use

Describe the task in plain words; the right skill or agent loads itself. Shortcuts:

| You want to… | Say or type |
|---|---|
| Build or fix a website | just ask; `web-dev-standards` loads for web work |
| Debug | `/debug`, or "X is broken, reproduce it first" |
| Build with review until approved | `/council <goal>`; add `--free` on your own code to run every reviewer on free models |
| Design a page | "Design a landing page for …: audience …, goal …" (`/impeccable craft`) |
| Polish UI | `/impeccable critique`, then `/impeccable polish` |
| Security check before deploy | `security-scan` in the project, then `/security-review` in Claude Code |
| Plan or think through a business question | ask; add "plan mode" (Shift+Tab) for anything multi-step |
| Search a codebase cheaply | "Use the Explore agent to find …" (runs on Haiku) |
| Run tests without flooding the chat | "Have test-runner run `npm test`" |
| Save Claude usage | automatic: Claude digests long output with `local-llm` (local, free) before reading it or calling an agent |
| See what this session uses | `/dash` (panel), `/context`, `/usage` |
| Set up a project | "set up this project" (template CLAUDE.md, tools, graph) |

**Replies are short by default** ("caveman lite" in `CLAUDE.md`): answer first, no filler. Say "caveman" for
even terser, "normal mode" for full prose.

### Turn tools on for one project

Rarely used tools are off everywhere so they cost no tokens. Turn a group on in a project (new session to apply):

```bash
bash ~/Documents/projects/claude-setup/claude-code/enable-plugins.sh <profile> <project-dir>
```

| Profile | Turns on | Cost per request when on |
|---|---|---|
| `wordpress` | WordPress Dev Skills + WordPress agent skills | ~3.6k tokens |
| `motion` | GSAP skills (only for projects using GSAP) | ~1k |
| `seo` | searchfit-seo | ~2k |
| `figma` | Figma plugin (then `/mcp` → Figma → sign in) | ~2.4k |

Add `--off` to turn it back off. It writes the project's `.claude/settings.local.json`, which is never committed.

---

## 3. Design workflow

1. Brief: audience, tone, the one action the page should drive, brand colours/fonts (or "propose").
2. Claude writes a 2–3 line direction first: approve or change it before any code.
3. Build (`/impeccable craft`). Motion last, CSS first, with a reduced-motion fallback.
4. Check: "screenshot at 375, 768 and 1280 with Playwright", then `/impeccable critique` → `polish`.

## 4. Security workflow (before every deploy or client merge)

1. `security-scan` in the project: gitleaks (secrets), OSV-Scanner (npm + Composer), Semgrep (code patterns),
   and for WordPress (Lando or WP-CLI) a plugin advisory check via wpvulnerability.net.
2. `/security-review` in Claude Code for the changes on the branch.
3. Fix each finding or note why it's a false positive; re-run until `security-scan: no findings`.

What leaves the machine: package names + versions (osv.dev), plugin slugs + versions (wpvulnerability.net),
Semgrep rule downloads. Secrets and code stay local.

---

## 5. Local model: `local-llm` (and the parked `claude-free`)

```bash
git diff | local-llm -m code "List what changed, one line per file"
```

A one-shot prompt to a local model on your GPU: free, and nothing leaves the device. Claude uses it
**by default** before any Claude agent for reading work, and picks the model by task with `-m`:

| Role (`-m`) | Model | Used for | Speed | GPU fit | Size |
|---|---|---|---|---|---|
| `general` (default) | `qwen3.5:4b` | digests of test/build output and logs, extraction | 19 tok/s | 39% CPU | 3.3 GB |
| `code` | `qwen2.5-coder:3b` | diffs, code files, snippets | 47 tok/s | full | 1.9 GB |
| `write` | `phi4-mini` | prose drafts (commit bodies, notes) | 26 tok/s | 41% CPU | 2.5 GB |

All three passed every `local-llm-bench` check (2026-11-26, RTX 3050 4 GB). Say **"no local"** or
**"use Claude"** for a task and it skips them for that task.

**Keep the models current:** type **`/local-models`**. Claude checks ollama.com for newer local models that
fit the GPU, benchmarks them against the current ones with `local-llm-bench`, switches a role only when the
new model passes and is clearly faster, updates `local-llm` and this table, and removes the losers (it asks
before removing a model you used). Run it every month or two:

```bash
local-llm-bench qwen3.5:4b qwen2.5-coder:3b phi4-mini | column -t -s $'\t'
```

It can't edit or run tools, and a 4B model can be wrong, so Claude confirms what it acts on with a Grep/Read.
Edits go to the `implementer` agent (Sonnet, your subscription).

**Why local models don't edit here:** on an RTX 3050 (4 GB VRAM) Claude Code's ~20k-token prompt takes
minutes per turn at ~60 tokens/s. Tested 2026-11-26: a one-line fix took 5–8 minutes on `qwen3.5:4b`/`2b`,
and one run reported a fix it never made. A direct `local-llm` call answers in ~10 s.

**`claude-free` (parked):** Claude Code on an Ollama Cloud model through the local Ollama. Signed in on
2026-11-26, but the free plan refused all 17 cloud models tried ("Add usage credits"), so it is off and
nothing routes to it. `/council --free` and `free-worker` use it too. It fails fast with the reason:

```bash
claude-free -p "Reply OK"
```

### Dashboard: Open WebUI

http://127.0.0.1:3000 (local only). Chat with any model, pull and delete models, set model defaults.
Install command in §1. Update: `docker pull ghcr.io/open-webui/open-webui:main`, then remove and re-run
the container (data stays in the `open-webui` volume). `ollama ps` shows what is loaded and on CPU/GPU.

---

## 6. Fewer tokens, better results

- **Write the request well:** what + where (file, function, page), what "done" looks like, constraints.
  One task per session. Paste the exact error.
- `/clear` between unrelated tasks (free). `/compact <what to keep>` at a natural break in a long task.
  `/rewind` when it went the wrong way. Shift+Tab (plan mode) before multi-step changes.
- **Model and effort** (pick at the start; changing model mid-session re-reads everything once):

| Work | Model | Effort |
|---|---|---|
| Quick edits, renames, copy | Sonnet | `/effort low`–`medium` |
| Normal features, writing, planning | Sonnet or Opus | `medium`–`high` |
| Bugs, security, architecture, strategy decisions | Opus | `/effort high` or `xhigh` (Opus 5.5 starts at `medium`) |
| Searches, test runs | Haiku agents (automatic) | low |

- **Long sessions are the main cost.** Every turn re-sends the whole conversation: a fresh session starts at
  ~29k tokens, but audited 2026-11-26 the median turn re-sent 172k, and 78% of all tokens came from turns
  above 150k. So auto-compact starts at **150k** (`autoCompactWindow`), and Claude tells you once when an
  unrelated task would be cheaper after `/clear`.
- Rarely used skills are hidden (`skillOverrides` in the settings template), the 6 animation skills included
  (they still run by name, e.g. `/animate`); tool groups are per project (§2).
- Details and sources: [BEST-PRACTICES.md](BEST-PRACTICES.md).

---

## 7. claude.ai

Follow [claude-ai/SETUP.md](claude-ai/SETUP.md): paste the preferences (same short-reply rules), one project per
client or topic, memory isolated per client project, upload `web-dev-standards` as a zip. Nothing in this repo
changes the account by itself.

On a new claude.ai account: do the same, then install the plugins by name from the directory (Playwright,
WordPress Dev Skills, A11y Enforcer, Perf Profiler, searchfit-seo, caveman) and connect Context7.

---

## 8. Keep it current

```bash
git -C ~/Documents/projects/claude-setup pull && bash ~/Documents/projects/claude-setup/claude-code/install.sh
```

- Skills, agents and `CLAUDE.md` are links: a `git pull` is enough. Re-run the installer after a settings change.
- Updates: `claude plugin marketplace update` then `claude plugin update <name>@<marketplace>`;
  `sudo pacman -Syu` (Ollama); `docker pull ghcr.io/open-webui/open-webui:main`.
- Found a better tool? Ask Claude to compare it with what's here and to add or replace it.
- Full audit + fix of everything (tools, skills, Ollama, docs): paste the prompt in [prompts/audit-and-setup.md](prompts/audit-and-setup.md).
- Health: `bash scripts/doctor.sh` (live, free); `bash scripts/test.sh` (offline tests).

## 9. Commands reference

| Task | Command |
|---|---|
| Plugins: list / on / off | `claude plugin list` · `claude plugin enable <id>` · `claude plugin disable <id>` |
| MCP servers | `claude mcp list` · `/mcp` to sign in |
| Skills shown to Claude | `/skills`; hide one with `skillOverrides` in `claude-code/settings.json` |
| Agents | `/agents`; change a model in `claude-code/agents/<name>.md` (`model:`) |
| Hooks | `/hooks`; scripts in `claude-code/hooks/` |
| Permissions | `permissions` in `claude-code/settings.json` (`allow` / `ask` / `deny`), then re-run the installer |
| Project instructions | `cp ~/Documents/projects/claude-setup/templates/CLAUDE.md ./CLAUDE.md` |
| Ollama | `ollama ps` · `ollama list` · `/local-models` · Alpaca app (or Open WebUI at http://127.0.0.1:3000) |

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| `doctor.sh` says a link is missing | `bash claude-code/install.sh` |
| Agent or skill not showing | new session; `/agents`, `/skills` |
| Settings ignored | `/status` → setting sources; a project's `.claude/settings*.json` overrides yours |
| MCP "failed to connect … npx" | re-run the installer (links nvm's Node into `~/.local/bin`) |
| "Blocked by guard-…" | intended for secrets; read the secret yourself in a terminal |
| Too many permission prompts | `/fewer-permission-prompts`, or add `allow` rules |
| `claude-free`: "not signed in" | `ollama signin` |
| `claude-free`: "refused … Add usage credits" | expected on the free plan; it is parked, Claude agents do the work |
| `local-llm` slow | first call loads the model (~10 s); `ollama ps` shows CPU/GPU split |
| Usage climbing fast | `/usage`; `/clear` between tasks; lower `/effort`; turn off unused profiles |

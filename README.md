# Claude setup

My Claude setup for everything I do with Claude: client work (WordPress, Shopify, nopCommerce, React + Vite,
plain HTML/CSS/JS), business strategy and planning, and weekend projects. It installs Claude Code's config on
any Linux machine, holds what to paste into claude.ai, and runs Claude Code on free models through OmniRoute
when the Claude plan limit is hit.

---

## What's in here

| Path | What it is | Used by |
|---|---|---|
| `claude-code/CLAUDE.md` | Global instructions: how to work, short "caveman lite" replies, model routing, git safety | Claude Code, every session |
| `claude-code/agents/` | 5 helper agents: `Explore` + `test-runner` (Haiku), `researcher` + `implementer` (Sonnet), `free-worker` (free models via OmniRoute) | Claude Code delegates to them |
| `claude-code/skills/debug/` | Root-cause debugging workflow | Claude Code, on a bug |
| `claude-code/hooks/` | Block secrets being printed or written; run the project's Prettier after edits | Claude Code, automatically |
| `claude-code/settings.json` | Settings template: permissions, hooks, hidden skills, plugins off by default | merged into `~/.claude/settings.json` |
| `claude-code/bin/security-scan` | Pre-deploy scan: secrets, dependencies, code patterns, WordPress plugins | you or Claude, in a project |
| `claude-code/bin/claude-free` | Claude Code on free models through OmniRoute | you, when the plan limit is hit |
| `claude-code/omniroute-setup.sh`, `omniroute-combo.json` | Creates the `free-coding` combo + its key in OmniRoute | once per machine |
| `claude-code/enable-plugins.sh` | Turns a tool group on for one project only | you, per project |
| `claude-code/install.sh` | Links all of the above into `~/.claude` and `~/.local/bin` | once, and after changes |
| `skills/web-dev-standards/` | My web standards: design, accessibility, performance, security, Definition of Done, per-stack rules | Claude Code and claude.ai |
| `mods/session-dashboard/` | `/dash` panel: context, cost, tokens, agents, skills, files | Claude Code |
| `claude-ai/SETUP.md` | What to paste into claude.ai: preferences, projects, memory, skills | claude.ai |
| `templates/CLAUDE.md` | Starter instructions file for a project | new projects |
| `scripts/doctor.sh`, `scripts/test.sh` | Live health check; offline tests | you |
| `BEST-PRACTICES.md` | The checklist this setup follows, with sources | reference |
| `prompts/audit-and-setup.md` | One prompt that audits and fixes the whole setup (incl. OmniRoute) | you, every month or two |

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

**GitHub** (the repo is private)

```bash
gh auth login && gh auth setup-git
```

**This repo + install**

```bash
git clone https://github.com/EduardoBojer98/claude-setup.git ~/Documents/projects/claude-setup
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

In a Claude Code session: `/plugin install session-dashboard --marketplace EduardoBojer98/claude-setup`.
Optional: ponytail (`/plugin marketplace add DietrichGebert/ponytail`).
Synced from claude.ai automatically: Playwright, WordPress Dev Skills, searchfit-seo, caveman, Context7.

**Docker + Lando** (WordPress sites; log out and in after the second command)

```bash
sudo systemctl enable --now docker.socket && sudo usermod -aG docker $USER
```

```bash
/bin/bash -c "$(curl -fsSL https://get.lando.dev/setup-lando.sh)"
```

**OmniRoute** (free models when the Claude limit is hit; see §5)

```bash
npm i -g omniroute && omniroute serve --daemon --no-open
```

Open http://localhost:20128, add provider keys (OpenRouter, NVIDIA, Ollama Cloud: free accounts), then:

```bash
bash ~/Documents/projects/claude-setup/claude-code/omniroute-setup.sh
```

---

## 2. Daily use

Describe the task in plain words; the right skill or agent loads itself. Shortcuts:

| You want to… | Say or type |
|---|---|
| Build or fix a website | just ask; `web-dev-standards` loads for web work |
| Debug | `/debug`, or "X is broken, reproduce it first" |
| Design a page | "Design a landing page for …: audience …, goal …" (`/impeccable craft`) |
| Polish UI | `/impeccable critique`, then `/impeccable polish` |
| Security check before deploy | `security-scan` in the project, then `/security-review` in Claude Code |
| Plan or think through a business question | ask; add "plan mode" (Shift+Tab) for anything multi-step |
| Search a codebase cheaply | "Use the Explore agent to find …" (runs on Haiku) |
| Run tests without flooding the chat | "Have test-runner run `npm test`" |
| Save Claude usage on simple work | "Use free-worker to …" (drafts, boilerplate, summaries, specified edits) |
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

## 5. When the Claude plan limit is hit: `claude-free`

```bash
claude-free
```

Starts Claude Code on free models through OmniRoute (it starts OmniRoute if needed). Same flags as `claude`:
`claude-free -c` continues the last session, `claude-free -p "…"` for one question.

- Uses the OmniRoute combo **`free-coding`**: NVIDIA Nemotron 3 Ultra → OpenRouter free models
  (Nemotron 3 Ultra, Nemotron 3.5 Super VL, North Mini Code). Tested 2026-11-04.
- **Not for client code.** NVIDIA's trial terms let it use prompts to improve its models
  ([API Trial Terms §3.3](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf));
  OpenRouter's Nemotron `:free` endpoints are served by NVIDIA. Use it for your own and weekend projects.
- OmniRoute listens on 127.0.0.1 only (set by `omniroute-setup.sh`): it serves `/v1` without checking keys.
  The first model that answers wins; the next is tried on an error or quota limit. Edit the order in
  `claude-code/omniroute-combo.json`, then re-run `omniroute-setup.sh`.
- Every model alias points at that combo. The key (`~/.config/claude-free/token`) is meant to allow only
  that combo, but OmniRoute 3.8.52 doesn't enforce it (it logs "invalid bearer" and serves the request
  anonymously). What keeps your Claude subscription out is that the `claude` provider stays inactive.
- Normal `claude` is untouched: it always uses your Claude subscription directly.
- Free models are weaker than Claude: use them to keep going on clear tasks, not for hard decisions.

**Don't connect your Claude subscription inside OmniRoute.** Anthropic only allows subscription logins in
Claude Code and its own apps, and forbids routing them through third-party tools
([legal and compliance](https://code.claude.com/docs/en/legal-and-compliance)): it can get the account
suspended. OmniRoute itself marks Antigravity and Kiro connections "avoid" for the same reason.

OmniRoute dashboard: http://localhost:20128 (providers, combos, usage, logs).

### Free agents inside normal Claude Code: `free-worker`

Your normal `claude` session (on the subscription) can hand bounded, low-risk work to the **free-worker** agent.
It runs the task through `claude-free -p` on the free models, then checks the diff and reports back. Only the
small Haiku wrapper uses Claude usage (≈ $0.002 list per task, measured). Claude picks it on its own for drafts,
boilerplate, summaries and fully specified edits, or ask: "use free-worker to …". It never handles security,
architecture, unknown bugs or final decisions, and you review its diff like any other change.

### More free providers (sign up, then add the key in the dashboard → Providers)

Re-checked 2026-11-04 (afternoon) with real requests and each provider's terms. Only you can create accounts.
**No sign-up is worth it right now**; the table says why.

| Provider (OmniRoute id) | Status | Why |
|---|---|---|
| Groq (`groq`) | key added, **not in the combo** | answers small prompts, but the free tier returns 413 on a Claude Code-sized request (~39k tokens, tested) |
| Cloudflare Workers AI (`cloudflare-ai`) | best for client code if it ever fits | only provider with a primary-source "no training" statement ([data usage](https://developers.cloudflare.com/workers-ai/platform/data-usage/)); Kimi K2.6 now needs Workers Paid ([pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/)) |
| SambaNova (`sambanova`) | skip | 20 requests/day ([rate limits](https://docs.sambanova.ai/docs/en/models/rate-limits)): one Claude Code task uses more |
| Cerebras (`cerebras`) | skip | free context 64–65k, below the 128k Claude Code needs ([models](https://inference-docs.cerebras.ai/models/overview)) |
| Ollama Cloud (`ollama-cloud`) | key kept, dropped from combo | Kimi K2.6 now returns 402 (paid) |
| Gemini (`gemini`), OpenRouter `gemma-4-31b-it:free` | skip | Google's unpaid tier trains on prompts with human review ([terms](https://aistudio.google.com/docs/terms)) |

After adding a provider: put its models in `claude-code/omniroute-combo.json` (best first) and run
`bash claude-code/omniroute-setup.sh`, or ask Claude to do it with the audit prompt below.

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

- Rarely used skills are hidden (`skillOverrides` in the settings template); tool groups are per project (§2).
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
  `npm i -g omniroute`; `sudo pacman -Syu`.
- Found a better tool? Ask Claude to compare it with what's here and to add or replace it.
- Full audit + fix of everything (tools, skills, OmniRoute, docs): paste the prompt in [prompts/audit-and-setup.md](prompts/audit-and-setup.md).
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
| OmniRoute | `omniroute status` · `omniroute combo list` · `omniroute logs` · dashboard at :20128 |

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| `doctor.sh` says a link is missing | `bash claude-code/install.sh` |
| Agent or skill not showing | new session; `/agents`, `/skills` |
| Settings ignored | `/status` → setting sources; a project's `.claude/settings*.json` overrides yours |
| MCP "failed to connect … npx" | re-run the installer (links nvm's Node into `~/.local/bin`) |
| "Blocked by guard-…" | intended for secrets; read the secret yourself in a terminal |
| Too many permission prompts | `/fewer-permission-prompts`, or add `allow` rules |
| `claude-free`: "no key" | run `claude-code/omniroute-setup.sh` |
| `claude-free` answers slowly or errors | free quota used up on the first models: `omniroute logs`; it falls through the list |
| Usage climbing fast | `/usage`; `/clear` between tasks; lower `/effort`; turn off unused profiles |

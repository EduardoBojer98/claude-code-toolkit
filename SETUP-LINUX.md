# Linux setup (CachyOS / Arch)

Clean Claude Code setup on a new machine. Commands are for **CachyOS / Arch** (pacman, fish shell);
Ubuntu/Debian equivalents are noted. Install only what is listed; retired tools are in `archive/README.md`.

_Last checked: 2026-10-28 on rog-flow-x13 (CachyOS, Claude Code 2.1.310)._

## 0. What needs nothing

Signing in to claude.ai brings the account items with it: the `web-dev-standards` and `toolkit-maintainer`
skills, the plugins (A11y Enforcer, Perf Profiler, WordPress Dev Skills, Playwright, searchfit-seo, caveman),
Context7 and the "Monthly toolkit review" task. They sync into Claude Code when you log in there.

## 1. Base packages

```bash
sudo pacman -S --needed git curl unzip base-devel python jq ripgrep fd github-cli docker docker-compose
# Ubuntu: sudo apt install -y git curl unzip build-essential python3 jq ripgrep fd-find gh
```

`jq` and `python` are needed by the installer and hooks; `rg`/`fd` make searches cheap.

## 2. Node.js 24 (LTS) — needed for Playwright, Shopify Dev MCP, Impeccable, React work

With fish, use nvm.fish (it reads `.nvmrc`; the CodeMate starter pins Node 24):

```bash
fish -c 'fisher install jorgebucaran/nvm.fish; nvm install lts; set --universal nvm_default_version 24'
```

Claude Code doesn't load fish's nvm hooks. `claude-code/install.sh` (step 6) links the newest nvm Node into
`~/.local/bin` so MCP servers can find `npx`. After installing a new Node version, re-run the installer.

## 3. Claude Code

```bash
curl -fsSL https://claude.ai/install.sh | bash
claude --version
```

Run `claude` once and log in with your claude.ai account.

## 4. GitHub CLI and Git

```bash
gh auth login
gh auth setup-git
git config --global user.name "Eduardo Bojer"
```

## 5. Docker and Lando (WordPress sites)

```bash
sudo systemctl enable --now docker.socket
sudo usermod -aG docker $USER
```

Log out and back in, then install Lando: `/bin/bash -c "$(curl -fsSL https://get.lando.dev/setup-lando.sh)"` and check `lando version`.

## 6. This repo and the Claude Code layer

```bash
git clone https://github.com/EduardoBojer98/claude-setup ~/Documents/projects/claude-setup
cd ~/Documents/projects/claude-setup
bash claude-code/install.sh
bash scripts/test.sh
```

This links the global CLAUDE.md, the routed agents, the hooks and the own skills into `~/.claude`, and merges
the settings template (permissions, hooks, skill trimming, subagent model). Details: [ARCHITECTURE.md](ARCHITECTURE.md),
daily use: [USAGE.md](USAGE.md).

## 7. Optional Claude Code tools (need Node)

Playwright MCP and Lighthouse use the installed Google Chrome (`google-chrome-stable`); no extra browser download is needed.

```bash
V=$(npm view @shopify/dev-mcp version)
claude mcp add --scope user --transport stdio shopify-dev-mcp -- npx -y @shopify/dev-mcp@$V
```

Plugins can also be installed from the terminal: `claude plugin marketplace add <owner/repo>` then
`claude plugin install <name>@<marketplace> --scope user`. Inside Claude Code:
- **figma** (you implement Figma designs): `/plugin` → install `figma` from `claude-plugins-official`, then `/mcp` to sign in.
- **Impeccable** (design critique/polish trial): `/plugin marketplace add pbakaus/impeccable`, install, then `npx impeccable telemetry off`.
- **session-dashboard** (own mod): `/plugin install session-dashboard --marketplace EduardoBojer98/claude-setup`.
- **ponytail** (optional): `/plugin marketplace add DietrichGebert/ponytail`; keep it on `lite`/`full`. It injects rules every turn, so check `/context` to see its cost.
- **WordPress Dev Skills** (synced from claude.ai) needs its dependency: `claude plugin marketplace add mralaminahamed/wordpress-official-agent-skills` then `claude plugin install wordpress-official-agent-skills@wordpress-official-agent-skills --scope user`.
- **React projects only**, in the project: `npx skills add vercel-labs/agent-skills --skill react-best-practices`.

## 8. Free-model fallback (optional)

```bash
bash fallback/install.sh --settings
```

Then add your free keys to `~/.config/claude-fallback/.env` and run `ccfb doctor`. Start with `claude-fb`. See [fallback/README.md](fallback/README.md).

## 9. Check it worked

```bash
claude mcp list
claude -p "/context" | sed -n '1,25p'
```

Compare `claude -p "/context"` with [BENCHMARKS.md](BENCHMARKS.md). In a session: `/agents` lists Explore,
implementer, researcher and test-runner; `/hooks` lists the three claude-setup hooks.

Then back up the machine's state: `bash scripts/sync-local.sh` (writes `local/<hostname>/`, secrets redacted).

## Don't install (retired)

VectorLab UI/UX Skills, the frontend-design plugin, the GitHub plugin, hyperframes, mattpocock-skills. See `archive/README.md`.

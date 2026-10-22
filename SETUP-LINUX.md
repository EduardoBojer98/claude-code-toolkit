# Linux setup (new machine)

Clean setup for Claude Code on a new Linux machine. Commands are for **Ubuntu / Debian**; Fedora
equivalents are noted where they differ. Install only what is listed here: the rest was retired on
2026-10-22 (see `DECISIONS.md` and `archive/README.md`).

_Last checked: 2026-10-22._

## 0. What needs nothing

Signing in to claude.ai brings everything account-level with it, on any OS:
your skills (`web-dev-standards`, `toolkit-maintainer`), the 5 active plugins (A11y Enforcer,
Perf Profiler, WordPress Dev Skills, Playwright, searchfit-seo), the Context7 connector and the
"Monthly toolkit review" scheduled task. Plugins also sync into Claude Code once you log in there.

## 1. Base packages

```bash
sudo apt update && sudo apt install -y git curl unzip build-essential python3
# Fedora: sudo dnf install -y git curl unzip gcc-c++ make python3
```

Python 3 is used by the A11y Enforcer and Perf Profiler scripts.

## 2. Node.js 24 (LTS)

The CodeMate starter pins Node 24 (`.nvmrc`); Shopify Dev MCP, Impeccable and Playwright run on Node.
Install nvm from <https://github.com/nvm-sh/nvm#installing-and-updating>, open a new terminal, then:

```bash
nvm install 24 && nvm alias default 24
node --version   # v24.x
```

Install Node only once, on Linux itself. Don't share `node_modules` with another OS.

## 3. Claude Code

```bash
curl -fsSL https://claude.ai/install.sh | bash
# open a new terminal
claude --version
claude          # log in with your claude.ai account on first run
```

Native installs update themselves. (Alternatives: apt/dnf packages; see
<https://code.claude.com/docs/en/setup>.)

## 4. GitHub CLI

Install `gh` following the official Linux instructions:
<https://github.com/cli/cli/blob/trunk/docs/install_linux.md>, then:

```bash
gh auth login        # GitHub.com → HTTPS → log in with a browser
git config --global user.name  "Eduardo Bojer"
git config --global user.email "<your email>"
```

Claude Code uses `gh` for branches and pull requests, so the GitHub plugin isn't needed.

## 5. Docker and Lando (WordPress sites)

```bash
/bin/bash -c "$(curl -fsSL https://get.lando.dev/setup-lando.sh)"
lando version
docker --version
```

If `docker --version` fails, install Docker Engine (not Docker Desktop) from
<https://docs.docker.com/engine/install/>, then `sudo usermod -aG docker $USER` and log out and back in.
Requirements: <https://docs.lando.dev/getting-started/requirements>.

## 6. Browser for screenshots and checks

Playwright (breakpoint screenshots), Perf Profiler (Lighthouse) and Impeccable (URL scans) need a browser:

```bash
npx playwright install --with-deps chromium
```

Installing Google Chrome or Chromium as a normal browser also works for Lighthouse.

## 7. Claude Code tools kept by the plan

```bash
# Shopify Dev MCP: Liquid docs + Theme Check validation (pin the version)
V=$(npm view @shopify/dev-mcp version) && npm cache add @shopify/dev-mcp@$V
claude mcp add --scope user --transport stdio shopify-dev-mcp -- npx -y @shopify/dev-mcp@$V

# Impeccable: design critique / audit / polish, with usage reporting off
npx impeccable telemetry off
```

Then inside Claude Code: `/plugin marketplace add pbakaus/impeccable`, and install **impeccable** from `/plugin`.

**React projects only**, inside each project folder:

```bash
npx skills add vercel-labs/agent-skills --skill react-best-practices
```

## 8. This repo and client projects

```bash
git clone https://github.com/EduardoBojer98/claude-setup ~/claude-setup
```

- Ask Claude Code "which skills do you have?". If `web-dev-standards` is **not** listed (account skills
  not synced to Claude Code), link it: `mkdir -p ~/.claude/skills && ln -s ~/claude-setup/skills/web-dev-standards ~/.claude/skills/web-dev-standards`.
  If it **is** listed, don't link it, or it loads twice. After a linked skill changes, `git -C ~/claude-setup pull`.
- New WordPress client site: copy the CodeMate starter (`github.com/EduardoBojer98/wordpress-starter`) and follow its `docs/new-project.md`.
- Any other client project: copy `templates/CLAUDE.md` to the project root and fill it in.

## 9. Don't install (retired 2026-10-22)

caveman, VectorLab UI/UX Skills, the frontend-design plugin (it's built in), Figma plugin/MCP,
GitHub plugin, hyperframes, ponytail, mattpocock-skills. Restore steps are in `archive/README.md`
if one is ever needed.

## 10. Check it worked

```bash
claude mcp list        # shopify-dev-mcp ✔ Connected, and playwright
```

In Claude Code:
- `/plugin`: A11y Enforcer, Perf Profiler, WordPress Dev Skills, playwright, searchfit-seo, impeccable, and nothing from section 9.
- `/context`: note the number for skills and tools. That's the baseline for the next toolkit review.

Then tell Claude "check my Claude Code setup against SETUP-LINUX.md in claude-setup".

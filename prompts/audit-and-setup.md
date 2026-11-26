# Prompt: audit and set up the whole Claude setup

Paste everything in the box into Claude Code, started in the repo with `cd ~/Documents/projects/claude-setup && claude`
(Opus, `/effort high`). It audits, fixes what it can, and leaves you a PR plus a short list of what only you can do.
Run it on a new machine, after a big Claude Code or Ollama update, or every month or two.

```text
Audit and set up my Claude setup in this repo (github.com/EduardoBojer98/claude-code-toolkit) and on this machine,
so I can keep working. Today's date matters: verify every external fact live, your training data is old.

Rules
- Branch from main (audit/YYYY-MM-DD); commit with Conventional Commits; push and open a PR into main. Don't merge.
- Free first: a paid tool only if it clearly beats every free option (give price + date). Better, not newer:
  ties keep what's installed. One tool per job. Every claim gets a source URL.
- Never break provider terms: my Claude subscription login is only for Claude Code and claude.ai, never inside
  a router or proxy.
- Never type passwords, API keys or tokens into anything, never create accounts: tell me what to sign up for.
- Ask me before deleting data, force-pushing or changing my claude.ai account. Everything else: decide and note it.
- Keep replies short (my CLAUDE.md "Replies" rules). Use Explore/test-runner/researcher agents for bulky work.

1. Read first: README.md, BEST-PRACTICES.md, claude-code/CLAUDE.md, claude-code/settings.json, claude-code/agents/,
   claude-code/hooks/, claude-code/bin/, skills/web-dev-standards/ (SKILL.md +
   references), mods/session-dashboard/, claude-ai/SETUP.md, templates/CLAUDE.md.
2. Machine health: `bash scripts/test.sh`, `bash scripts/doctor.sh`, `claude --version`, `claude plugin list`,
   `claude mcp list`, `claude -p "/context"`. Fix every failure (re-run `bash claude-code/install.sh` if links drifted).
   Record per-request context (skills, memory, agents, MCP) and compare with BEST-PRACTICES.md.
3. Best practices: re-check code.claude.com/docs (memory, skills, subagents, hooks, settings, costs, model-config,
   prompt-caching) and docs.claude.com skill-authoring guidance for changes since BEST-PRACTICES.md was written.
   Update the checklist and apply anything that saves tokens without losing quality. Anything loaded every turn
   must earn its place.
4. Tools: for each installed plugin, MCP server, skill and CLI (Impeccable, GSAP skills, Playwright, ponytail,
   caveman, WordPress Dev Skills, Shopify Dev MCP, Context7, gitleaks, osv-scanner, semgrep, Ollama, Open WebUI) check the
   latest release, licence/price and security notices; update pinned versions; look for a clearly better free option
   for design, motion, security, WordPress, Shopify, React and business/planning work. Keep rarely used tools off
   globally (per-project profiles in claude-code/enable-plugins.sh).
5. Ollama (http://127.0.0.1:11434; dashboard Open WebUI at http://127.0.0.1:3000):
   - `ollama --version`, `ollama ps`, `ollama list`; `claude-free --models`.
   - `claude-free -p "Reply OK"` answers (if "not signed in", tell me to run `ollama signin`).
   - Re-check Ollama Cloud: which models the free tier serves, its limits and privacy terms (ollama.com/pricing,
     docs.ollama.com/cloud). Test the best coding candidates with a real one-file edit in a scratch git repo;
     set the default in claude-code/bin/claude-free (CLAUDE_FREE_MODEL) to the one that edits correctly.
   - Local: `printf 'x' | local-llm "Reply OK"` answers; check for a better local model that fits this GPU.
   - Verify delegation: in a scratch git repo, have a Claude session use the free-worker agent for a one-function
     edit and check the diff.
6. Skills: web-dev-standards facts (WordPress, Elementor, ACF, Shopify, nopCommerce, PHP, React, Vite, Tailwind,
   WCAG, Core Web Vitals, CSS Baseline) still current? Bump its Version line for any change. If the skill changed,
   give me the zip command for claude.ai.
7. session-dashboard: `claude plugin validate` + `claude plugin test mods/session-dashboard`; it must draw nothing
   outside its /dash pane (other mods own the band and status line).
8. README.md: still direct and correct for every command and path; fix anything stale.
9. Finish: run step 2 again, commit, push, open the PR. Reply with: what changed (one line each), token impact,
   what failed or is unverified, the exact sign-ups/clicks only I can do, and the PR link.
```

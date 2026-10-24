# session-dashboard

A Claude Code mod that shows what the current session is using, in the spirit of
[savvy-progress](https://github.com/JohnnyVizz/claude-kit/tree/main/plugins/savvy-progress).

- **Band above the prompt**: estimated cost, total tokens, elapsed time, tool calls, files edited and
  how full the context is (green under 50%, yellow under 80%, red after), plus a **Dashboard** button.
  It appears after the first request of the session.
- **Panel** (`/dash` shows or hides it, `/dash open` opens it, `/dash reset` starts the counts over):
  time, model, requests (main and subagent), cost, input/output/cache tokens, a context bar, the
  most used tools with failures, and the files edited, newest first.

Counts include subagents. The context bar is the main conversation's.

Cost is a rough estimate from token counts and a per-model price table (`PRICES` in
`hooks/register.tsx`, adapted from savvy-progress, list prices as of 2026-10-10), not a bill. On a
subscription it shows what the same usage would cost on the API.

## Settings

Set in `/config`, or in `~/.claude/settings.json`:

```json
{ "pluginConfigs": { "session-dashboard": { "options": { "band": "on", "budget": "5" } } } }
```

- `band`: `on` (default) or `off` (panel only).
- `budget`: `none` (default), `1`, `2`, `5`, `10` or `25`: a toast once the session's estimated
  cost passes that many dollars.

## Install

At the prompt of a terminal Claude Code session:

```
/plugin install session-dashboard --marketplace EduardoBojer98/claude-setup
```

Answer `y` to add the marketplace, then pick the user scope. From a shell:

```
claude plugin install session-dashboard --marketplace EduardoBojer98/claude-setup
```

The repository is private: the machine needs a GitHub credential first
(`gh auth login`, then `gh auth setup-git`, or an SSH key); the install never asks for one.

## Develop

```
claude plugin validate mods/session-dashboard
claude plugin test mods/session-dashboard
claude --plugin-dir mods/session-dashboard   # run it from the folder, reloads on save
```

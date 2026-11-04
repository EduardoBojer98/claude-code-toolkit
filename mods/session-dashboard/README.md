# session-dashboard

A Claude Code mod: a `/dash` panel with what the current session is using.

**Draws nothing outside its panel.** No band above the prompt and no status line, so it never covers or
crowds other mods that use those spots (ponytail's band). The only thing shown outside the panel is the
opt-in cost toast.

## Use

| Command | Does |
|---|---|
| `/dash` | show or hide the panel (a sidebar in fullscreen terminal and the desktop app) |
| `/dash open` | open it |
| `/dash reset` | start the counts over (also the **Reset counts** button) |

The panel, top to bottom:
- model · elapsed time · requests (and how many came from agents)
- **Context**: bar and % of the main conversation's window (green < 50%, yellow < 80%, red after; a hint to
  `/compact` or `/clear` when nearly full)
- **Cost (estimate)**: total, lead vs agents, the alert amount if set
- **Tokens**: input, output, cache read/write, **cache hit %** (high = cheap and fast)
- **Agents**: every subagent nested under who spawned it: status (● running, ✓ done, ✗ failed, ■ stopped),
  type, model family, time, tokens, cost, task, top tools, skills it loaded; plus count per model
- **Skills**: each skill loaded, how often, and by whom (`lead`, an agent such as `Explore#1a2b`, or `you`)
- **Tools** (most used, failures) and **Files edited** (newest first)

Cost is an estimate from token counts and list prices in `hooks/register.tsx` (`PRICES`, as of 2026-10-10),
not a bill: on a subscription it shows what the same usage would cost on the API.

## Settings

`budget` (in `/config`, or `~/.claude/settings.json`): `none` (default), `1`, `2`, `5`, `10` or `25` dollars;
a toast once the session's estimated cost passes it.

`autoOpen`: `on` (default) opens the panel when a session starts; `off` leaves it to `/dash`.

```json
{ "pluginConfigs": { "session-dashboard": { "options": { "budget": "5" } } } }
```

## Install

```
/plugin install session-dashboard --marketplace EduardoBojer98/claude-setup
```

The repository is private: run `gh auth login` and `gh auth setup-git` first. Update after a repo change:
`claude plugin marketplace update claude-setup && claude plugin update session-dashboard@claude-setup`.

## Develop

```
claude plugin validate mods/session-dashboard
claude plugin test mods/session-dashboard
```

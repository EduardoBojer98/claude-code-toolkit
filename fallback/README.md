# ccfb: free-model fallback for Claude Code

Keeps Claude Code working when your Claude plan hits its session or weekly limit. You
start Claude Code with `claude-fb` instead of `claude`. While Claude is available nothing
changes: every request goes to Anthropic with your normal login. When Anthropic reports a
plan limit, the same session carries on with a free model (OpenRouter, Gemini, optionally
a local Ollama model), and it switches back when Claude answers again.

How it works, what was researched and why: [DESIGN.md](DESIGN.md).

> Anthropic doesn't support running Claude Code on non-Claude models. It works, but a free
> model is weaker and some features won't. Treat fallback as "keep going on simple work",
> not as a replacement for Claude.

## Install

Needs Python 3.11+ (standard library only, nothing to pip install) and Claude Code.

```bash
cd ~/claude-setup            # this repository
bash fallback/install.sh     # links ccfb + claude-fb into ~/.local/bin, creates ~/.config/claude-fallback/
```

Add at least one free key to `~/.config/claude-fallback/.env`:

| Key | Where | Free terms (checked 2026-10-22) |
|---|---|---|
| `OPENROUTER_API_KEY` | <https://openrouter.ai/keys> | 20 requests/min, 50/day on free models (1000/day after a one-time 10-credit purchase) |
| `GEMINI_API_KEY` | <https://aistudio.google.com/apikey> | Free tier; limits shown per project in AI Studio |

Two keys are better than one: each tool step is a request, so a single free quota runs out fast.

```bash
ccfb doctor            # checks Python, Claude Code, config and keys; shows which model it would use
ccfb doctor --online   # also sends one tiny request to each provider (uses 1 free request each)
bash fallback/install.sh --settings   # optional: adds ccfb's status line and hooks to ~/.claude/settings.json (backup first)
```

## Use

```bash
claude-fb                 # instead of `claude`; any claude arguments work: claude-fb --continue, claude-fb -p "…"
ccfb status               # mode, why it last switched, provider health, when Claude is expected back
```

Plain `claude` keeps working exactly as before; it just doesn't get the fallback.

| Command | What it does |
|---|---|
| `ccfb status [--json]` | Current mode (claude/fallback), last switch reason, last model used, providers ready or cooling down |
| `ccfb models [--refresh]` | Every model and why it is or isn't eligible; `--refresh` reads context windows from provider APIs |
| `ccfb use-fallback` | Use free models now (e.g. to save your Claude quota) until `ccfb resume` |
| `ccfb resume` | Go back to Claude now and clear a manual hold |
| `ccfb reset` | Clear provider cooldowns/disabled flags (after fixing a key) |
| `ccfb handoff [--session ID]` | Write a handoff summary of a session (default: the latest) |
| `ccfb start` / `ccfb stop` | Run or stop the background gateway (`claude-fb` starts it automatically) |
| `ccfb serve` | Run the gateway in the foreground with live logs |

The optional status line shows `FALLBACK <model> · Claude back ~Fri 14:00` while on a free
model, or your 5-hour/7-day usage while on Claude.

## Settings

Defaults live in [`config/providers.toml`](config/providers.toml). Override any of them in
`~/.config/claude-fallback/config.toml` (tables merge key by key):

```toml
[fallback]
enabled = true                       # false = pure pass-through, never fall back
preferred_providers = ["openrouter", "gemini"]
excluded_providers = []
excluded_models = []
min_context_tokens = 64000
max_attempts = 4
redact_secrets = true                # mask obvious keys before sending to a free provider
sticky_minutes = 30

[recovery]
mode = "auto"                        # or "manual": stay on fallback until `ccfb resume`
probe_interval_minutes = 15
turn_boundary_only = true            # only try Claude again at the start of a new user turn

[gateway]
port = 8787
log_level = "info"                   # "debug" for routing details (never secrets or prompts)

[providers.ollama]                   # optional local model
enabled = true
[[providers.ollama.models]]
id = "qwen3-coder:30b"
context = 65536
tools = true
roles = ["main", "small"]
priority = 5
```

Logs: `~/.local/state/claude-fallback/gateway.log`. State: `state.json` in the same folder.
Handoffs: `~/.local/state/claude-fallback/handoffs/`.

## Privacy

On a free tier, the provider may log or train on what you send (Gemini's free tier says it
may use prompts to improve Google's products; OpenRouter free endpoints depend on the
model's provider). In fallback mode your prompt, the files Claude Code reads and tool
output go to that provider. ccfb masks common secret formats first (API keys, tokens,
private keys, `*_PASSWORD=` lines), but that is pattern matching, not a guarantee. For
client code you may not share, set `[fallback] enabled = false` in that client's
environment, use `ccfb use-fallback` only on your own projects, or run a local Ollama model.

A masked value can end up in a file if a fallback model copies it back; check diffs of
`.env`-style files written during fallback.

## Troubleshooting

| Symptom | Fix |
|---|---|
| "no free fallback model could take this request" | `ccfb doctor`: no key set, all providers cooling down, or the request is too large; `ccfb status` shows which |
| Claude Code shows "You've hit your … limit" even with `claude-fb` | Check `ccfb status`: if mode is still `claude`, the limit response didn't carry the expected headers; run `ccfb use-fallback` and open an issue in this repo with the time |
| Fallback answers are poor or tools misbehave | Switch model priority in config, add another provider, or start a new session from the handoff file |
| `claude-fb` starts plain Claude Code | The gateway failed to start: see `~/.local/state/claude-fallback/gateway.out`; port in use → set `[gateway] port` |
| A provider shows "credential rejected" | Fix the key in `.env`, then `ccfb reset` |
| Want Claude back before the reset time | `ccfb resume` (the next request goes to Claude) |

## Tests

```bash
bash fallback/run-tests.sh              # 42 tests, local fakes only, no keys or network
CCFB_E2E=1 bash fallback/run-tests.sh   # plus 1 test driving the real Claude Code CLI against local fakes
```

Scenarios covered (`tests/test_scenarios.py`, `tests/test_units.py`):

1. Claude available: requests and streams pass through byte for byte, credentials and betas forwarded, no fallback contacted.
2. Plan-limit 429 (with quota headers): switch to fallback, same request answered, reset time recorded.
3. First provider's daily quota exhausted (reported or counted): next provider used; cooldown until its reset.
4. Provider rate limit: backoff by `Retry-After`, alternative used, preferred provider returns after the sticky window.
5. Provider outage (500, connection refused): next provider; all down gives a clear, non-retried error.
6. Authentication errors: Claude 401 is relayed, never treated as a limit; a provider 401 disables only that provider.
7. Network error to Anthropic: reported once (502), no fallback, no retry loop.
8. Recovery: no Claude check before the reset time or mid tool loop; back to Claude at the next user turn; still limited waits a full interval; manual mode never checks.
9. Capabilities: images skip non-vision models; models without tool calling are rejected.
10. Missing credentials: the error and `ccfb doctor` name the variable to set.
11. Fresh install from a clean clone into an empty home directory: install, re-run (keys kept), doctor, status.
12. Migration: the clean-clone test uses only repository files plus the user's own `.env`.

Also: OpenAI stream → Anthropic event translation (text + tool call), thinking blocks and
secrets never reach a free provider, status output contains no secrets.

## Moving to a new machine

1. Install Claude Code and Python 3.11+.
2. `git clone https://github.com/EduardoBojer98/claude-setup ~/claude-setup && bash ~/claude-setup/fallback/install.sh`
3. Recreate `~/.config/claude-fallback/.env` with your keys (they are deliberately not in Git).
   Copy `config.toml` too if you changed settings.
4. `ccfb doctor`, then use `claude-fb`.

Upgrading: `git -C ~/claude-setup pull` (the commands are symlinks into the repo), then
`ccfb stop` so the next `claude-fb` starts the new version.

Windows without WSL: run `python fallback\bin\ccfb run -- <claude args>`; `install.sh` and
`claude-fb` are for Linux/macOS/WSL.

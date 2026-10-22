# ccfb design: research, decisions and limits

_Researched and built 2026-10-22 against Claude Code 2.1.308._

## The problem in one line

When a claude.ai plan limit (session, weekly or model-family) stops Claude Code, keep the
same session working on a free model, and go back to Claude when the limit resets, without
paid APIs and without touching anything when Claude is available.

## What Claude Code supports (verified in its docs)

| Question | Finding | Source |
|---|---|---|
| Can a subscription login go through a local gateway? | Yes. Setting only `ANTHROPIC_BASE_URL` (no gateway credential) keeps the claude.ai login as the active credential; the gateway must forward `anthropic-beta` (it carries the OAuth capability) | [llm-gateway: Subscriptions and gateways](https://code.claude.com/docs/en/llm-gateway), [gateway protocol](https://code.claude.com/docs/en/llm-gateway-protocol) |
| What must a gateway implement? | `POST /v1/messages` (streamed, pings forwarded, 300 s idle watchdog), optional `/v1/messages/count_tokens`; forward `anthropic-*` headers and body unchanged | gateway protocol |
| Are non-Claude models supported? | **No.** Anthropic "doesn't support routing Claude Code to non-Claude models through any gateway". It works technically (OpenRouter and Ollama document it), but it is unsupported | llm-gateway |
| How is a plan limit signalled? | HTTP 429 carrying Anthropic's "unified" quota headers; a short server throttle is a 429 *without* them. Messages: "You've hit your session/weekly/Opus/Sonnet limit · resets …" | [errors](https://code.claude.com/docs/en/errors) |
| Can a hook detect it? | `StopFailure` fires on API errors (`rate_limit`, `billing_error`, …) but its output is ignored, so it can't switch providers. Used only for logging | [hooks](https://code.claude.com/docs/en/hooks) |
| Reset times available? | Status line input has `rate_limits.five_hour/seven_day.used_percentage` and `resets_at` for Pro/Max | [statusline](https://code.claude.com/docs/en/statusline) |
| Switch model mid-session? | Not for a different provider from inside Claude Code. But a gateway sees every request, and Claude Code sends the full history each time, so the gateway can change who answers between two requests | gateway protocol |

## Free providers (checked 2026-10-22)

| Provider | Free terms | Fit for Claude Code | Decision |
|---|---|---|---|
| OpenRouter `:free` models | 20 req/min; 50 req/day (1000/day after a one-time 10-credit purchase). [limits](https://openrouter.ai/docs/api-reference/limits) | Anthropic-compatible endpoint, documented for Claude Code ([guide](https://openrouter.ai/docs/cookbook/coding-agents/claude-code-integration.md)); free models with tools and 256K–1M context ([list](https://costgoat.com/pricing/openrouter-free-models)) | **Default #1** |
| Google Gemini API | Free tier; exact per-project limits only in AI Studio; daily quota resets at midnight Pacific. [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits). Free-tier prompts may be used to improve Google products | OpenAI-compatible endpoint with tools + streaming ([docs](https://ai.google.dev/gemini-api/docs/openai)); current stable `gemini-3.8-flash`, `gemini-3.5-flash-lite` ([models](https://ai.google.dev/gemini-api/docs/models)) | **Default #2** |
| Cerebras | **Free trial**, not a permanent tier: 5 RPM, 30K uncached TPM, 1M TPD. [rate limits](https://inference-docs.cerebras.ai/support/rate-limits) | Works, but tight per-minute token budget | In registry, **off** |
| Groq | Free: 8K tokens/min on the useful models. [rate limits](https://console.groq.com/docs/rate-limits) | One Claude Code request (system prompt + tool schemas, ~15–30K tokens) exceeds 8K TPM | **Marked incompatible** |
| Ollama (local) | Free, local. [Anthropic compatibility](https://docs.ollama.com/api/anthropic-compatibility) | Native `/v1/messages` with tools; quality depends on your GPU/RAM | In registry, **off** (opt-in) |

Free tiers change. Limits in `config/providers.toml` carry their source and date; the
gateway also reacts to real 429s and rate-limit headers, and `ccfb models --refresh`
re-reads context windows from provider APIs.

## Existing tools considered

| Option | Why not used as the core |
|---|---|
| LiteLLM proxy | Translation and fallbacks are mature, but it is a large dependency tree and its PyPI package was compromised in March 2026 (credential-stealing versions 1.82.7/1.82.8, [NetSPI](https://www.netspi.com/blog/executive-blog/ai-ml-pentesting/litellm-supply-chain-compromise/)). This gateway handles the claude.ai OAuth token, so supply-chain risk matters most here |
| claude-code-router (musistudio) | Good for always routing Claude Code to other models (MIT, Node 22+, [overview](https://www.morphllm.com/claude-code-router)); no documented "Claude first, fall back only on plan limit" behaviour or subscription pass-through. Would still need our own detection and recovery layer in front |
| A `StopFailure` hook + relaunch | Hook output can't change routing; relaunching loses the in-flight turn |

**Decision:** a small gateway on Python's standard library only (no third-party packages,
nothing to pip-install, nothing to compromise), about 2,500 lines plus about 850 lines of tests that use local fakes.

## Architecture

```
Claude Code ──(ANTHROPIC_BASE_URL=http://127.0.0.1:8787)──> ccfb gateway
                                                              │
        Claude mode: relay unchanged ─────────────────────────┼──> api.anthropic.com (your subscription)
        429 + unified quota headers ──> fallback mode         │
        Fallback mode: best eligible free model ──────────────┼──> OpenRouter (Anthropic format, relayed)
                                                              ├──> Gemini (OpenAI format, translated)
                                                              └──> Ollama / others (optional)
```

- **Detection**: only a 429 *with* `anthropic-ratelimit-unified-*` headers counts. Throttles
  (429 without them), 529 overload, 401/403, 400s, 5xx and network failures are relayed or
  reported, never treated as a plan limit. The limit 429 itself is not shown to Claude Code;
  the same request is answered by the fallback, so Claude Code never enters its own
  "wait for reset" state.
- **Routing**: candidates are filtered by credential, health, cooldown, local quota counts,
  context size vs. estimated request size, tool support (Claude Code always sends tools) and
  vision (if the request has images). They are ranked by your preferred providers, then
  registry priority, with a 30-minute sticky preference for the model already working. Up to
  4 candidates are tried per request before giving up.
- **Quota**: per-provider and per-model counters (requests/min, requests/day, tokens/min,
  tokens/day) are local observations. Provider 429s set cooldowns: `Retry-After` or reset
  headers when given, otherwise 60 s; a reported daily quota cools the provider down until
  its documented reset (UTC or Pacific midnight). 401/403 disables only that provider.
- **Recovery**: in fallback mode the gateway sends one real request to Claude no earlier
  than the reported reset time and at most once per `probe_interval_minutes` (default 15),
  by default only at the start of a new user turn so an active tool loop isn't switched
  mid-way. Success switches back; another limit schedules the next check. `manual` mode
  waits for `ccfb resume`.
- **Context**: the same Claude Code session continues (history is in every request). As a
  safety net, switching writes a handoff file built from the session transcript (objective,
  recent requests, files changed, open todos, last message) under the state directory.
- **Translation** (OpenAI-format providers): text, images, tool definitions, tool calls,
  tool results, streaming (`text_delta`, `input_json_delta`), stop reasons and usage. Tool
  ids are normalised so the conversation stays valid when it returns to Claude.

## Security

- The claude.ai OAuth token is only forwarded to `https://api.anthropic.com` (enforced in
  config validation). Free providers receive only their own key.
- The gateway binds to loopback only (validated); a provider pointing at the gateway itself
  is rejected (no loops).
- Before a request goes to a free provider: Claude-only fields and thinking signatures are
  removed, and common secret formats are masked (`redact_secrets`, on by default). This is
  pattern matching, not a guarantee.
- Status, logs and doctor output never contain keys, tokens or prompt text.
- Keys live in environment variables or `~/.config/claude-fallback/.env` (mode 600), never
  in the repository.

## Known limitations

1. **Unsupported by Anthropic**: routing Claude Code to non-Claude models is not supported
   by Anthropic. Claude Code features may break on a fallback model; quality is lower.
2. **Not verified against a real plan limit.** Detection follows the documented signal and
   is tested with simulated 429s. The exact unified header names aren't listed in the docs,
   so the gateway matches the `anthropic-ratelimit-unified-` prefix. If a real limit response
   lacks those headers, Claude Code shows the normal limit message and nothing switches
   (fails safe). Use `ccfb use-fallback` manually in that case and report it.
3. **Free quotas are small for agent work.** Each tool step is one request. OpenRouter's
   50 requests/day can be used up in one task; add a Gemini key so the router has a second
   provider.
4. **Claude Code still believes it talks to Claude**: its context bar, cost estimates and
   model label reflect the Claude model, not the fallback. The ccfb status line and
   `ccfb status` show the real route.
5. **Context window**: Claude Code may build requests larger than a fallback model accepts;
   such models are skipped. If none fits, run `/compact` or start a new session with the
   handoff file.
6. **Prompt caching, extended thinking, server tools (web search) and fast mode** don't
   carry over to fallback models.
7. Only Claude Code sessions launched through `claude-fb` (or with `ANTHROPIC_BASE_URL`
   pointing at the gateway) are covered. The claude.ai app and Desktop chats are not.

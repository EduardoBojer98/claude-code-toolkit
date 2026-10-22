"""End-to-end scenarios against fake upstreams (no real network, no real credentials).

Numbers match the scenario list in fallback/README.md -> "Tests".
"""

from __future__ import annotations

import json
import unittest

from helpers import (LIMIT_HEADERS, Env, Scripted, anthropic_ok, limit_429, openai_ok, tool_result_turn,
                     user_turn)

from ccfb.state import MODE_CLAUDE, MODE_FALLBACK


class Base(unittest.TestCase):
    env_kwargs: dict = {}

    def setUp(self) -> None:
        self.env = Env(**self.env_kwargs)

    def tearDown(self) -> None:
        self.env.close()

    def enter_fallback(self) -> None:
        self.env.claude.queue.append(limit_429())
        status, _, _ = self.env.post(user_turn())
        self.assertEqual(status, 200)
        self.assertEqual(self.env.store.state.mode, MODE_FALLBACK)


class TestScenario01ClaudeAvailable(Base):
    def test_passthrough_is_unchanged(self) -> None:
        body = user_turn()
        status, headers, data = self.env.post(body)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(data), anthropic_ok())
        self.assertEqual(self.env.store.state.mode, MODE_CLAUDE)
        sent = self.env.claude.requests[0]
        # subscription credentials and betas reach Anthropic unchanged; body is byte-identical
        self.assertEqual(sent["headers"]["Authorization"], "Bearer oauth-subscription-token")
        self.assertIn("oauth-2025-04-20", sent["headers"]["anthropic-beta"])
        self.assertEqual(sent["json"], body)
        self.assertEqual(sent["path"], "/v1/messages?beta=true")
        self.assertEqual(self.env.anthro.requests, [])
        self.assertEqual(self.env.oai.requests, [])

    def test_streaming_passthrough(self) -> None:
        events = [b'event: message_start\ndata: {"type":"message_start"}\n\n', b'event: message_stop\ndata: {"type":"message_stop"}\n\n']
        self.env.claude.queue.append(Scripted(200, sse=events))
        status, _, data = self.env.post(user_turn(stream=True))
        self.assertEqual(status, 200)
        self.assertEqual(data, b"".join(events))

    def test_short_throttle_is_not_a_usage_limit(self) -> None:
        self.env.claude.queue.append(Scripted(429, {"type": "error", "error": {"type": "rate_limit_error",
                                                                               "message": "slow down"}}, {"retry-after": "5"}))
        status, headers, _ = self.env.post(user_turn())
        self.assertEqual(status, 429)            # relayed: Claude Code retries throttles itself
        self.assertEqual(headers.get("retry-after"), "5")
        self.assertEqual(self.env.store.state.mode, MODE_CLAUDE)
        self.assertEqual(self.env.anthro.requests, [])


class TestScenario02UsageLimitTriggersFallback(Base):
    def test_limit_switches_and_serves_same_request(self) -> None:
        self.env.claude.queue.append(limit_429())
        status, _, data = self.env.post(user_turn())
        self.assertEqual(status, 200)
        reply = json.loads(data)
        self.assertEqual(reply["content"][0]["text"], "hello from anthropic-compatible free model")
        self.assertEqual(reply["model"], "claude-sonnet-5")      # Claude Code keeps its model label
        st = self.env.store.state
        self.assertEqual(st.mode, MODE_FALLBACK)
        self.assertEqual(st.claude_reset_at, float(LIMIT_HEADERS["anthropic-ratelimit-unified-reset"]))
        self.assertGreaterEqual(st.next_probe_at, st.claude_reset_at)
        sent = self.env.anthro.requests[0]
        self.assertEqual(sent["json"]["model"], "free/coder:free")
        # the subscription token never leaves for a third party
        self.assertEqual(sent["headers"]["Authorization"], "Bearer sk-free-anthro-key-123456")
        self.assertNotIn("anthropic-beta", {k.lower() for k in sent["headers"]})

    def test_following_requests_skip_claude(self) -> None:
        self.enter_fallback()
        self.env.post(user_turn("second"))
        self.assertEqual(len(self.env.claude.requests), 1)
        self.assertEqual(len(self.env.anthro.requests), 2)

    def test_fallback_disabled_relays_limit(self) -> None:
        self.env.cfg.raw["fallback"]["enabled"] = False
        self.env.claude.queue.append(limit_429())
        status, _, _ = self.env.post(user_turn())
        self.assertEqual(status, 429)
        self.assertEqual(self.env.store.state.mode, MODE_CLAUDE)


class TestScenario03ProviderExhausted(Base):
    def test_daily_quota_moves_to_next_provider(self) -> None:
        self.env.claude.queue.append(limit_429())
        self.env.anthro.queue.append(Scripted(429, {"error": {"message": "Rate limit exceeded: free-models-per-day"}},
                                              {"X-RateLimit-Remaining": "0"}))
        status, _, data = self.env.post(user_turn())
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(data)["content"][0]["text"], "hello from free model")
        h = self.env.store.health("freeanthro")
        self.assertGreater(h.cooldown_until, self.env.clock() + 3600)          # until next UTC midnight
        self.assertIn("daily", h.cooldown_reason)
        # next request goes straight to the second provider
        self.env.post(user_turn("again"))
        self.assertEqual(len(self.env.anthro.requests), 1)
        self.assertEqual(len(self.env.oai.requests), 2)

    def test_local_daily_count_skips_provider(self) -> None:
        self.enter_fallback()
        self.env.store.health("freeanthro").day_requests = 50                 # registry says rpd = 50
        self.env.post(user_turn("again"))
        self.assertEqual(len(self.env.anthro.requests), 1)
        self.assertEqual(len(self.env.oai.requests), 1)


class TestScenario04ProviderRateLimit(Base):
    def test_backoff_then_alternative_then_return(self) -> None:
        self.enter_fallback()
        self.env.anthro.queue.append(Scripted(429, {"error": {"message": "slow down"}}, {"Retry-After": "30"}))
        status, _, _ = self.env.post(user_turn("x"))
        self.assertEqual(status, 200)
        self.assertEqual(len(self.env.oai.requests), 1)
        h = self.env.store.health("freeanthro")
        self.assertAlmostEqual(h.cooldown_until, self.env.clock() + 30, delta=1)
        self.env.clock.advance(31)
        self.env.post(user_turn("y"))
        self.assertEqual(len(self.env.oai.requests), 2)                      # sticky: no needless switch back
        self.env.clock.advance(31 * 60)                                      # sticky window (30 min) over
        self.env.post(user_turn("z"))
        self.assertEqual(len(self.env.anthro.requests), 3)                   # preferred provider used again


class TestScenario05Outage(Base):
    def test_server_error_and_dead_provider(self) -> None:
        self.enter_fallback()
        self.env.anthro.queue.append(Scripted(500, {"error": {"message": "boom"}}))
        status, _, _ = self.env.post(user_turn("x"))
        self.assertEqual(status, 200)
        self.assertEqual(len(self.env.oai.requests), 1)
        self.assertGreater(self.env.store.health("freeanthro/free/coder:free").cooldown_until, self.env.clock())
        # whole provider unreachable (connection refused) -> still served
        self.env.anthro.close()
        self.env.clock.advance(3600)
        status, _, _ = self.env.post(user_turn("y"))
        self.assertEqual(status, 200)
        self.assertEqual(len(self.env.oai.requests), 2)

    def test_all_providers_down_returns_clear_non_retry_error(self) -> None:
        self.enter_fallback()
        self.env.anthro.default = Scripted(503, {"error": {"message": "down"}})
        self.env.oai.default = Scripted(500, {"error": {"message": "down"}})
        status, headers, data = self.env.post(user_turn("x"))
        self.assertEqual(status, 429)
        self.assertEqual(headers.get("x-should-retry"), "false")
        self.assertIn("no free fallback model", json.loads(data)["error"]["message"])
        self.assertEqual(self.env.store.state.mode, MODE_FALLBACK)


class TestScenario06AuthErrors(Base):
    def test_claude_401_is_not_a_usage_limit(self) -> None:
        self.env.claude.queue.append(Scripted(401, {"type": "error", "error": {"type": "authentication_error",
                                                                               "message": "invalid token"}}))
        status, _, _ = self.env.post(user_turn())
        self.assertEqual(status, 401)
        self.assertEqual(self.env.store.state.mode, MODE_CLAUDE)
        self.assertEqual(self.env.anthro.requests, [])

    def test_provider_401_disables_that_provider_only(self) -> None:
        self.env.claude.queue.append(limit_429())
        self.env.anthro.queue.append(Scripted(401, {"error": {"message": "bad key"}}))
        status, _, _ = self.env.post(user_turn())
        self.assertEqual(status, 200)
        self.assertIn("credential rejected", self.env.store.health("freeanthro").disabled_reason)


class TestScenario07NetworkError(Base):
    def test_claude_unreachable_reports_without_retry_loop(self) -> None:
        self.env.claude.close()
        status, _, data = self.env.post(user_turn())
        self.assertEqual(status, 502)
        self.assertIn("could not reach Anthropic", json.loads(data)["error"]["message"])
        self.assertEqual(self.env.store.state.mode, MODE_CLAUDE)
        self.assertEqual(self.env.anthro.requests, [])


class TestScenario08Recovery(Base):
    def test_no_probe_before_reset_or_mid_tool_loop(self) -> None:
        self.enter_fallback()
        self.env.clock.advance(16 * 60)                      # past interval but before reported reset
        self.env.post(user_turn("x"))
        self.assertEqual(len(self.env.claude.requests), 1)
        self.env.clock.advance(6 * 3600)                     # past reset, but a tool-result continuation
        self.env.post(tool_result_turn())
        self.assertEqual(len(self.env.claude.requests), 1)
        self.assertEqual(self.env.store.state.mode, MODE_FALLBACK)

    def test_recovers_at_next_user_turn(self) -> None:
        self.enter_fallback()
        self.env.clock.advance(6 * 3600)
        status, _, data = self.env.post(user_turn("new task"))
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(data)["content"][0]["text"], "hello from claude")
        self.assertEqual(self.env.store.state.mode, MODE_CLAUDE)

    def test_still_limited_waits_a_full_interval(self) -> None:
        self.enter_fallback()
        self.env.clock.advance(6 * 3600)
        self.env.claude.queue.append(Scripted(429, {"error": {"message": "weekly limit"}},
                                              {"anthropic-ratelimit-unified-status": "rejected"}))
        status, _, _ = self.env.post(user_turn("x"))
        self.assertEqual(status, 200)                        # served by fallback, not shown the 429
        self.assertEqual(self.env.store.state.mode, MODE_FALLBACK)
        self.env.post(user_turn("y"))                        # immediately after: no second Claude call
        self.assertEqual(len(self.env.claude.requests), 2)
        self.assertGreaterEqual(self.env.store.state.next_probe_at, self.env.clock() + 15 * 60 - 1)

    def test_manual_mode_never_probes(self) -> None:
        self.env.cfg.raw["recovery"]["mode"] = "manual"
        self.enter_fallback()
        self.env.clock.advance(24 * 3600)
        self.env.post(user_turn("x"))
        self.assertEqual(len(self.env.claude.requests), 1)


class TestScenario09Capabilities(Base):
    def test_images_skip_models_without_vision(self) -> None:
        self.enter_fallback()
        body = user_turn()
        body["messages"][0]["content"].append({"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                                                            "data": "iVBORw0KGgo="}})
        status, _, _ = self.env.post(body)
        self.assertEqual(status, 200)
        self.assertEqual(len(self.env.anthro.requests), 1)   # only the first (text) request
        self.assertEqual(len(self.env.oai.requests), 1)
        sent = self.env.oai.requests[0]["json"]
        self.assertEqual(sent["messages"][-1]["content"][1]["type"], "image_url")

    def test_model_without_tools_is_rejected(self) -> None:
        for m in self.env.cfg.providers["freeanthro"].models:
            m.tools = False
        self.enter_fallback()
        self.assertEqual(len(self.env.anthro.requests), 0)
        self.assertEqual(len(self.env.oai.requests), 1)


class TestScenario10MissingCredentials(Base):
    env_kwargs = {"provider_keys": False}

    def test_explains_what_to_configure(self) -> None:
        self.env.claude.queue.append(limit_429())
        status, headers, data = self.env.post(user_turn())
        self.assertEqual(status, 429)
        self.assertEqual(headers.get("x-should-retry"), "false")
        msg = json.loads(data)["error"]["message"]
        self.assertIn("ccfb doctor", msg)
        self.assertIn("FREEANTHRO_KEY", msg)


class TestFallbackTranslationOverHTTP(Base):
    def test_openai_provider_tool_call_round_trip(self) -> None:
        self.env.cfg.raw["fallback"]["preferred_providers"] = ["freeoai"]
        self.env.cfg.providers["freeanthro"].enabled = False
        self.env.oai.queue.append(Scripted(200, openai_ok("", {"name": "Read", "input": {"file_path": "a.py"}})))
        self.enter_fallback()
        sent = self.env.oai.requests[0]["json"]
        self.assertEqual(sent["model"], "oai-flash")
        self.assertNotIn("$schema", sent["tools"][0]["function"]["parameters"])
        self.assertEqual(sent["messages"][0]["role"], "system")

    def test_openai_stream_becomes_anthropic_events(self) -> None:
        self.env.cfg.providers["freeanthro"].enabled = False
        chunks = [
            b'data: {"choices":[{"index":0,"delta":{"role":"assistant","content":"Hel"}}]}\n\n',
            b'data: {"choices":[{"index":0,"delta":{"content":"lo"}}]}\n\n',
            b'data: {"choices":[{"index":0,"delta":{"tool_calls":[{"index":0,"id":"call_9","type":"function","function":{"name":"Read","arguments":"{\\"file_"}}]}}]}\n\n',
            b'data: {"choices":[{"index":0,"delta":{"tool_calls":[{"index":0,"function":{"arguments":"path\\":\\"a.py\\"}"}}]},"finish_reason":"tool_calls"}],"usage":{"prompt_tokens":40,"completion_tokens":9}}\n\n',
            b"data: [DONE]\n\n",
        ]
        self.env.claude.queue.append(limit_429())
        self.env.oai.queue.append(Scripted(200, sse=chunks))
        status, _, data = self.env.post(user_turn(stream=True))
        self.assertEqual(status, 200)
        events = [json.loads(line[6:]) for line in data.decode().splitlines() if line.startswith("data: ")]
        kinds = [e["type"] for e in events]
        self.assertEqual(kinds[0], "message_start")
        self.assertEqual(kinds[-1], "message_stop")
        text = "".join(e["delta"]["text"] for e in events if e["type"] == "content_block_delta" and e["delta"]["type"] == "text_delta")
        self.assertEqual(text, "Hello")
        tool_start = next(e for e in events if e["type"] == "content_block_start" and e["content_block"]["type"] == "tool_use")
        self.assertEqual(tool_start["content_block"]["id"], "toolu_fb_call_9")
        args = "".join(e["delta"]["partial_json"] for e in events if e["type"] == "content_block_delta" and e["delta"]["type"] == "input_json_delta")
        self.assertEqual(json.loads(args), {"file_path": "a.py"})
        delta = next(e for e in events if e["type"] == "message_delta")
        self.assertEqual(delta["delta"]["stop_reason"], "tool_use")
        self.assertEqual(delta["usage"]["output_tokens"], 9)

    def test_thinking_blocks_and_secrets_never_reach_free_provider(self) -> None:
        body = tool_result_turn()
        body["messages"][-1]["content"][0]["content"] = "AWS key AKIAABCDEFGHIJKLMNOP and ghp_" + "a" * 36
        self.env.claude.queue.append(limit_429())
        self.env.post(body)
        sent = json.dumps(self.env.anthro.requests[0]["json"])
        self.assertNotIn('"thinking"', sent)
        self.assertNotIn("AKIAABCDEFGHIJKLMNOP", sent)
        self.assertIn("[REDACTED:aws-access-key]", sent)
        self.assertIn("[REDACTED:github-token]", sent)


class TestControlsAndStatus(Base):
    def test_status_never_contains_secrets(self) -> None:
        self.enter_fallback()
        text = json.dumps(self.env.gateway.status())
        for secret in ("sk-free-anthro-key-123456", "free-oai-key-abcdef", "oauth-subscription-token"):
            self.assertNotIn(secret, text)
        log_events = json.dumps(self.env.store.state.events)
        self.assertNotIn("oauth-subscription-token", log_events)

    def test_count_tokens_in_fallback_is_local(self) -> None:
        self.enter_fallback()
        status, _, data = self.env.post(user_turn(), path="/v1/messages/count_tokens?beta=true")
        self.assertEqual(status, 200)
        self.assertGreater(json.loads(data)["input_tokens"], 0)
        self.assertEqual(len(self.env.claude.requests), 1)


if __name__ == "__main__":
    unittest.main()

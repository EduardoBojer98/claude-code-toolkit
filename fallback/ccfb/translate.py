"""Anthropic Messages <-> OpenAI Chat Completions translation (requests, responses, streams).

Only what Claude Code needs is mapped: text, images, tool definitions, tool calls and tool
results, stop reasons and usage. Claude-only features (thinking signatures, prompt-cache
markers, server tools, context management) are dropped before a request leaves for a
non-Anthropic provider, because other models can't honour them.
"""

from __future__ import annotations

import json
import re
import uuid
from typing import Any, Iterable, Iterator

STOP_REASONS = {
    "stop": "end_turn",
    "length": "max_tokens",
    "tool_calls": "tool_use",
    "function_call": "tool_use",
    "content_filter": "end_turn",
}

_TOOL_ID_RE = re.compile(r"[^a-zA-Z0-9_-]")


def safe_tool_id(raw: str | None) -> str:
    """Tool ids must match ^[a-zA-Z0-9_-]+$ to be valid if the conversation returns to Claude."""
    if not raw:
        return "toolu_fb_" + uuid.uuid4().hex[:20]
    cleaned = _TOOL_ID_RE.sub("_", raw)
    return cleaned if cleaned.startswith("toolu_") else "toolu_fb_" + cleaned


def _text_of(content: Any) -> str:
    if isinstance(content, str):
        return content
    parts = []
    for block in content or []:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "\n".join(parts)


def _image_url(block: dict[str, Any]) -> str | None:
    src = block.get("source", {})
    if src.get("type") == "base64":
        return f"data:{src.get('media_type', 'image/png')};base64,{src.get('data', '')}"
    if src.get("type") == "url":
        return src.get("url")
    return None


def _clean_schema(schema: Any) -> Any:
    if isinstance(schema, dict):
        return {k: _clean_schema(v) for k, v in schema.items() if k not in {"$schema", "$id"}}
    if isinstance(schema, list):
        return [_clean_schema(v) for v in schema]
    return schema


def to_openai_request(body: dict[str, Any], model: str, *, stream: bool, system_note: str = "",
                      include_usage: bool = False) -> dict[str, Any]:
    messages: list[dict[str, Any]] = []
    system = body.get("system")
    system_text = system if isinstance(system, str) else _text_of(system)
    if system_note:
        system_text = (system_note + "\n\n" + system_text).strip()
    if system_text:
        messages.append({"role": "system", "content": system_text})

    for msg in body.get("messages", []):
        role = msg.get("role")
        content = msg.get("content")
        if isinstance(content, str):
            messages.append({"role": role, "content": content})
            continue
        if role == "assistant":
            text_parts, tool_calls = [], []
            for block in content or []:
                btype = block.get("type")
                if btype == "text":
                    text_parts.append(block.get("text", ""))
                elif btype == "tool_use":
                    tool_calls.append({
                        "id": block.get("id"),
                        "type": "function",
                        "function": {"name": block.get("name"), "arguments": json.dumps(block.get("input", {}))},
                    })
                # thinking / redacted_thinking / server tool blocks are dropped
            out: dict[str, Any] = {"role": "assistant", "content": "\n".join(text_parts) or None}
            if tool_calls:
                out["tool_calls"] = tool_calls
            if out["content"] is None and not tool_calls:
                out["content"] = ""
            messages.append(out)
            continue
        # user message: tool results become `tool` messages, the rest stays a user message
        parts: list[dict[str, Any]] = []
        for block in content or []:
            btype = block.get("type")
            if btype == "tool_result":
                inner = block.get("content")
                text = inner if isinstance(inner, str) else _text_of(inner)
                if block.get("is_error"):
                    text = "[tool error] " + text
                messages.append({"role": "tool", "tool_call_id": block.get("tool_use_id"), "content": text or "(no output)"})
                if isinstance(inner, list):
                    for sub in inner:
                        if isinstance(sub, dict) and sub.get("type") == "image" and _image_url(sub):
                            parts.append({"type": "image_url", "image_url": {"url": _image_url(sub)}})
            elif btype == "text":
                parts.append({"type": "text", "text": block.get("text", "")})
            elif btype == "image" and _image_url(block):
                parts.append({"type": "image_url", "image_url": {"url": _image_url(block)}})
            elif btype == "document":
                parts.append({"type": "text", "text": "[a document was attached but this fallback model can't read documents]"})
        if parts:
            if all(p["type"] == "text" for p in parts):
                messages.append({"role": "user", "content": "\n".join(p["text"] for p in parts)})
            else:
                messages.append({"role": "user", "content": parts})

    req: dict[str, Any] = {"model": model, "messages": messages, "stream": stream}
    if body.get("max_tokens"):
        req["max_tokens"] = body["max_tokens"]
    for src, dst in (("temperature", "temperature"), ("top_p", "top_p")):
        if src in body:
            req[dst] = body[src]
    if body.get("stop_sequences"):
        req["stop"] = body["stop_sequences"][:4]
    tools = [t for t in body.get("tools", []) if "input_schema" in t]   # server tools have no schema
    if tools:
        req["tools"] = [{
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": _clean_schema(t.get("input_schema", {"type": "object", "properties": {}})),
            },
        } for t in tools]
        choice = body.get("tool_choice") or {}
        ctype = choice.get("type")
        if ctype == "any":
            req["tool_choice"] = "required"
        elif ctype == "tool" and choice.get("name"):
            req["tool_choice"] = {"type": "function", "function": {"name": choice["name"]}}
        elif ctype == "none":
            req["tool_choice"] = "none"
    if stream and include_usage:
        req["stream_options"] = {"include_usage": True}
    return req


def _parse_args(raw: str) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else {"value": value}
    except ValueError:
        return {"_unparsed_arguments": raw}


def from_openai_response(data: dict[str, Any], reply_model: str, est_input: int = 0) -> dict[str, Any]:
    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    content: list[dict[str, Any]] = []
    text = message.get("content")
    if isinstance(text, list):
        text = "".join(p.get("text", "") for p in text if isinstance(p, dict))
    if text:
        content.append({"type": "text", "text": text})
    for call in message.get("tool_calls") or []:
        fn = call.get("function", {})
        content.append({
            "type": "tool_use",
            "id": safe_tool_id(call.get("id")),
            "name": fn.get("name", ""),
            "input": _parse_args(fn.get("arguments", "")),
        })
    stop = STOP_REASONS.get(choice.get("finish_reason") or "stop", "end_turn")
    if any(b["type"] == "tool_use" for b in content):
        stop = "tool_use"
    usage = data.get("usage") or {}
    return {
        "id": "msg_fb_" + uuid.uuid4().hex[:24],
        "type": "message",
        "role": "assistant",
        "model": reply_model,
        "content": content or [{"type": "text", "text": ""}],
        "stop_reason": stop,
        "stop_sequence": None,
        "usage": {
            "input_tokens": int(usage.get("prompt_tokens") or est_input),
            "output_tokens": int(usage.get("completion_tokens") or 0),
        },
    }


def sse(event: str, data: dict[str, Any]) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data, separators=(',', ':'))}\n\n".encode()


def iter_sse_data(lines: Iterable[bytes]) -> Iterator[str]:
    """Yield `data:` payloads from an SSE byte-line stream (OpenAI style)."""
    for raw in lines:
        line = raw.decode("utf-8", "replace").rstrip("\r\n")
        if line.startswith("data:"):
            yield line[5:].strip()


class StreamTranslator:
    """Feed OpenAI chat.completion.chunk dicts, get Anthropic SSE event bytes out."""

    def __init__(self, reply_model: str, est_input: int = 0):
        self.reply_model = reply_model
        self.est_input = est_input
        self.started = False
        self.block_index = -1
        self.open_kind: str | None = None          # "text" | "tool"
        self.tool_blocks: dict[int, int] = {}       # openai tool index -> anthropic block index
        self.current_tool: int | None = None
        self.output_tokens = 0
        self.input_tokens = 0
        self.finish: str | None = None
        self.saw_tool = False

    def _start(self) -> list[bytes]:
        self.started = True
        return [sse("message_start", {"type": "message_start", "message": {
            "id": "msg_fb_" + uuid.uuid4().hex[:24], "type": "message", "role": "assistant",
            "model": self.reply_model, "content": [], "stop_reason": None, "stop_sequence": None,
            "usage": {"input_tokens": self.est_input, "output_tokens": 0}}})]

    def _close_open(self) -> list[bytes]:
        if self.open_kind is None:
            return []
        self.open_kind = None
        self.current_tool = None
        return [sse("content_block_stop", {"type": "content_block_stop", "index": self.block_index})]

    def feed(self, chunk: dict[str, Any]) -> list[bytes]:
        out: list[bytes] = [] if self.started else self._start()
        usage = chunk.get("usage")
        if usage:
            self.input_tokens = int(usage.get("prompt_tokens") or self.input_tokens)
            self.output_tokens = int(usage.get("completion_tokens") or self.output_tokens)
        for choice in chunk.get("choices") or []:
            delta = choice.get("delta") or {}
            text = delta.get("content")
            if text:
                if self.open_kind != "text":
                    out += self._close_open()
                    self.block_index += 1
                    self.open_kind = "text"
                    out.append(sse("content_block_start", {"type": "content_block_start", "index": self.block_index,
                                                           "content_block": {"type": "text", "text": ""}}))
                out.append(sse("content_block_delta", {"type": "content_block_delta", "index": self.block_index,
                                                       "delta": {"type": "text_delta", "text": text}}))
            for call in delta.get("tool_calls") or []:
                idx = int(call.get("index", 0))
                fn = call.get("function") or {}
                if idx not in self.tool_blocks:
                    out += self._close_open()
                    self.block_index += 1
                    self.tool_blocks[idx] = self.block_index
                    self.open_kind = "tool"
                    self.current_tool = idx
                    self.saw_tool = True
                    out.append(sse("content_block_start", {"type": "content_block_start", "index": self.block_index,
                                                           "content_block": {"type": "tool_use", "id": safe_tool_id(call.get("id")),
                                                                             "name": fn.get("name", ""), "input": {}}}))
                elif self.current_tool != idx:
                    # Arguments for an earlier call after another block started: can't reopen a block.
                    continue
                args = fn.get("arguments")
                if args:
                    out.append(sse("content_block_delta", {"type": "content_block_delta", "index": self.tool_blocks[idx],
                                                           "delta": {"type": "input_json_delta", "partial_json": args}}))
            if choice.get("finish_reason"):
                self.finish = choice["finish_reason"]
        return out

    def finish_stream(self) -> list[bytes]:
        out: list[bytes] = [] if self.started else self._start()
        out += self._close_open()
        stop = "tool_use" if self.saw_tool else STOP_REASONS.get(self.finish or "stop", "end_turn")
        out.append(sse("message_delta", {"type": "message_delta", "delta": {"stop_reason": stop, "stop_sequence": None},
                                         "usage": {"output_tokens": self.output_tokens}}))
        out.append(sse("message_stop", {"type": "message_stop"}))
        return out

    @staticmethod
    def error_event(message: str, etype: str = "api_error") -> bytes:
        return sse("error", {"type": "error", "error": {"type": etype, "message": message}})


def anthropic_error(message: str, etype: str = "rate_limit_error") -> bytes:
    return json.dumps({"type": "error", "error": {"type": etype, "message": message}}).encode()

"""Minimal HTTP(S) client on the standard library, with streaming and timeouts."""

from __future__ import annotations

import http.client
import queue
import ssl
import threading
from dataclasses import dataclass
from typing import Iterator
from urllib.parse import urlparse

_SSL = ssl.create_default_context()


class NetworkError(Exception):
    pass


@dataclass
class Response:
    status: int
    headers: list[tuple[str, str]]
    _resp: http.client.HTTPResponse
    _conn: http.client.HTTPConnection

    def header_map(self) -> dict[str, str]:
        return {k.lower(): v for k, v in self.headers}

    def read_all(self, limit: int = 20 * 1024 * 1024) -> bytes:
        try:
            return self._resp.read(limit)
        finally:
            self.close()

    def iter_raw(self, size: int = 65536) -> Iterator[bytes]:
        """Yield bytes as soon as they arrive (decoded from chunked transfer)."""
        try:
            while True:
                chunk = self._resp.read1(size)
                if not chunk:
                    break
                yield chunk
        finally:
            self.close()

    def iter_lines(self) -> Iterator[bytes]:
        try:
            while True:
                line = self._resp.readline()
                if not line:
                    break
                yield line
        finally:
            self.close()

    def close(self) -> None:
        try:
            self._resp.close()
        finally:
            self._conn.close()


def request(method: str, url: str, headers: dict[str, str], body: bytes | None, *,
            connect_timeout: float = 15, read_timeout: float = 300) -> Response:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    port = parsed.port
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    try:
        if parsed.scheme == "https":
            conn: http.client.HTTPConnection = http.client.HTTPSConnection(host, port, timeout=connect_timeout, context=_SSL)
        else:
            conn = http.client.HTTPConnection(host, port, timeout=connect_timeout)
        conn.connect()
        conn.sock.settimeout(read_timeout)
        conn.request(method, path, body=body, headers=headers)
        resp = conn.getresponse()
    except (OSError, http.client.HTTPException) as exc:
        raise NetworkError(f"{type(exc).__name__}: {exc}") from None
    return Response(resp.status, resp.getheaders(), resp, conn)


def with_heartbeat(items: Iterator[bytes], interval: float) -> Iterator[bytes | None]:
    """Yield items from a blocking iterator; yield None every `interval` seconds of silence.

    Lets the gateway send SSE pings to Claude Code while a slow provider is thinking, so
    Claude Code's 300-second idle watchdog doesn't abort the stream.
    """
    q: queue.Queue = queue.Queue(maxsize=256)
    done = object()

    def pump() -> None:
        try:
            for item in items:
                q.put(item)
        except Exception as exc:  # surfaced to the consumer
            q.put(exc)
        finally:
            q.put(done)

    threading.Thread(target=pump, daemon=True).start()
    while True:
        try:
            item = q.get(timeout=interval)
        except queue.Empty:
            yield None
            continue
        if item is done:
            return
        if isinstance(item, Exception):
            raise NetworkError(str(item))
        yield item

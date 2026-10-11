"""LLM client for Ollama-native or OpenAI-compatible endpoints."""

import json
import logging
from collections.abc import AsyncIterator

import httpx

from app.config import get_settings

log = logging.getLogger(__name__)


class LLMError(RuntimeError):
    pass


class ThinkFilter:
    """Strips <think>...</think> blocks from a token stream, even when tags are split across chunks."""

    OPEN = "<think>"
    CLOSE = "</think>"

    def __init__(self) -> None:
        self.buf = ""
        self.in_think = False

    @staticmethod
    def _partial(buf: str, tag: str) -> int:
        for n in range(min(len(tag) - 1, len(buf)), 0, -1):
            if buf.endswith(tag[:n]):
                return n
        return 0

    def feed(self, chunk: str) -> str:
        self.buf += chunk
        out: list[str] = []
        while True:
            if self.in_think:
                i = self.buf.find(self.CLOSE)
                if i == -1:
                    keep = len(self.CLOSE) - 1
                    if len(self.buf) > keep:
                        self.buf = self.buf[-keep:]
                    break
                self.buf = self.buf[i + len(self.CLOSE):]
                self.in_think = False
            else:
                i = self.buf.find(self.OPEN)
                if i == -1:
                    hold = self._partial(self.buf, self.OPEN)
                    out.append(self.buf[: len(self.buf) - hold])
                    self.buf = self.buf[len(self.buf) - hold:]
                    break
                out.append(self.buf[:i])
                self.buf = self.buf[i + len(self.OPEN):]
                self.in_think = True
        return "".join(out)

    def flush(self) -> str:
        rest = "" if self.in_think else self.buf
        self.buf = ""
        return rest


class LLMClient:
    def __init__(self) -> None:
        self.s = get_settings()
        self.base = self.s.llm_base_url.rstrip("/")
        headers = {"Content-Type": "application/json"}
        if self.s.llm_api_key:
            headers["Authorization"] = f"Bearer {self.s.llm_api_key}"
        self.headers = headers
        self.timeout = httpx.Timeout(self.s.llm_timeout_s, connect=10.0)

    # -- request building -------------------------------------------------
    def _request(self, messages: list[dict[str, str]], stream: bool, max_tokens: int | None) -> tuple[str, dict]:
        s = self.s
        if s.llm_provider == "ollama":
            options: dict = {"temperature": s.llm_temperature, "num_ctx": s.llm_num_ctx}
            if max_tokens:
                options["num_predict"] = max_tokens
            body = {"model": s.llm_model, "messages": messages, "stream": stream, "think": s.llm_think, "options": options}
            return f"{self.base}/api/chat", body
        body = {"model": s.llm_model, "messages": messages, "stream": stream, "temperature": s.llm_temperature}
        if max_tokens:
            body["max_tokens"] = max_tokens
        return f"{self.base}/chat/completions", body

    # -- streaming --------------------------------------------------------
    async def stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        url, body = self._request(messages, True, None)
        think = ThinkFilter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, json=body, headers=self.headers) as resp:
                    if resp.status_code >= 400:
                        detail = (await resp.aread()).decode("utf-8", "replace")[:300]
                        raise LLMError(f"LLM returned HTTP {resp.status_code}: {detail}")
                    async for line in resp.aiter_lines():
                        piece = self._parse_line(line)
                        if piece:
                            visible = think.feed(piece)
                            if visible:
                                yield visible
            tail = think.flush()
            if tail:
                yield tail
        except httpx.HTTPError as exc:
            raise LLMError(f"LLM endpoint unreachable ({type(exc).__name__}): {exc}") from exc

    def _parse_line(self, line: str) -> str:
        line = line.strip()
        if not line:
            return ""
        if self.s.llm_provider == "ollama":
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                return ""
            if data.get("error"):
                raise LLMError(str(data["error"]))
            return (data.get("message") or {}).get("content", "") or ""
        if not line.startswith("data:"):
            return ""
        payload = line[5:].strip()
        if payload == "[DONE]":
            return ""
        try:
            data = json.loads(payload)
            return (data["choices"][0].get("delta") or {}).get("content") or ""
        except (json.JSONDecodeError, KeyError, IndexError):
            return ""

    # -- one-shot ---------------------------------------------------------
    async def complete(self, messages: list[dict[str, str]], max_tokens: int | None = None) -> str:
        url, body = self._request(messages, False, max_tokens)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=body, headers=self.headers)
        except httpx.HTTPError as exc:
            raise LLMError(f"LLM endpoint unreachable ({type(exc).__name__}): {exc}") from exc
        if resp.status_code >= 400:
            raise LLMError(f"LLM returned HTTP {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        text = (data.get("message") or {}).get("content", "") if self.s.llm_provider == "ollama" else data["choices"][0]["message"]["content"]
        f = ThinkFilter()
        return (f.feed(text) + f.flush()).strip()

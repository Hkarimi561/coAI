"""LLM client for Ollama-native or OpenAI-compatible endpoints (LM Studio, vLLM, llama.cpp, ...).

Streaming yields (channel, text) pairs where channel is "think" (model reasoning) or "answer".
"""

import json
import logging
from collections.abc import AsyncIterator

import httpx

from app.config import get_settings

log = logging.getLogger(__name__)

Chunk = tuple[str, str]


class LLMError(RuntimeError):
    pass


class ThinkSplitter:
    """Splits a token stream into reasoning and answer parts based on <think>...</think> tags,
    even when a tag is split across chunks."""

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

    def feed(self, chunk: str) -> list[Chunk]:
        self.buf += chunk
        out: list[Chunk] = []
        while True:
            tag = self.CLOSE if self.in_think else self.OPEN
            channel = "think" if self.in_think else "answer"
            i = self.buf.find(tag)
            if i == -1:
                hold = self._partial(self.buf, tag)
                text = self.buf[: len(self.buf) - hold]
                if text:
                    out.append((channel, text))
                self.buf = self.buf[len(self.buf) - hold:]
                return out
            if i:
                out.append((channel, self.buf[:i]))
            self.buf = self.buf[i + len(tag):]
            self.in_think = not self.in_think

    def flush(self) -> list[Chunk]:
        rest, self.buf = self.buf, ""
        return [("think" if self.in_think else "answer", rest)] if rest else []


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
    async def stream(self, messages: list[dict[str, str]]) -> AsyncIterator[Chunk]:
        url, body = self._request(messages, True, None)
        splitter = ThinkSplitter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, json=body, headers=self.headers) as resp:
                    if resp.status_code >= 400:
                        detail = (await resp.aread()).decode("utf-8", "replace")[:300]
                        raise LLMError(f"LLM returned HTTP {resp.status_code}: {detail}")
                    async for line in resp.aiter_lines():
                        reasoning, content = self._parse_line(line)
                        if reasoning:  # structured reasoning field (Ollama `thinking`, LM Studio `reasoning_content`)
                            yield "think", reasoning
                        if content:
                            for part in splitter.feed(content):
                                yield part
            for part in splitter.flush():
                yield part
        except httpx.HTTPError as exc:
            raise LLMError(f"LLM endpoint unreachable ({type(exc).__name__}): {exc}") from exc

    def _parse_line(self, line: str) -> tuple[str, str]:
        """Returns (reasoning_text, answer_text) contained in one streamed line."""
        line = line.strip()
        if not line:
            return "", ""
        if self.s.llm_provider == "ollama":
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                return "", ""
            if data.get("error"):
                raise LLMError(str(data["error"]))
            msg = data.get("message") or {}
            return msg.get("thinking") or "", msg.get("content") or ""
        if not line.startswith("data:"):
            return "", ""
        payload = line[5:].strip()
        if payload == "[DONE]":
            return "", ""
        try:
            delta = json.loads(payload)["choices"][0].get("delta") or {}
        except (json.JSONDecodeError, KeyError, IndexError):
            return "", ""
        return delta.get("reasoning_content") or delta.get("reasoning") or "", delta.get("content") or ""

    async def health(self) -> tuple[bool, str]:
        """Cheap reachability + model-availability check (does not generate text)."""
        ollama = self.s.llm_provider == "ollama"
        url = f"{self.base}/api/tags" if ollama else f"{self.base}/models"
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(url, headers=self.headers)
        except httpx.HTTPError as exc:
            return False, f"Cannot reach {self.base} ({type(exc).__name__}). Is the LLM server running and listening on 0.0.0.0?"
        if resp.status_code >= 400:
            return False, f"{url} returned HTTP {resp.status_code}"
        try:
            data = resp.json()
            names = [m.get("name", "") for m in data.get("models", [])] if ollama else [m.get("id", "") for m in data.get("data", [])]
        except ValueError:
            return False, "Unexpected response from the LLM server"
        model = self.s.llm_model
        if names and model not in names and f"{model}:latest" not in names:
            return False, f"Server is reachable but model '{model}' is not installed. Available: {', '.join(names[:8])}"
        return True, f"{model} @ {self.base}"

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
        splitter = ThinkSplitter()
        parts = splitter.feed(text or "") + splitter.flush()
        return "".join(t for ch, t in parts if ch == "answer").strip()

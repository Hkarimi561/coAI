"""Embedding providers: local sentence-transformers, Ollama, or any OpenAI-compatible endpoint."""

import asyncio
import logging
from typing import Literal

import httpx

from app.config import get_settings

log = logging.getLogger(__name__)
Kind = Literal["query", "passage"]


class EmbeddingError(RuntimeError):
    pass


class Embedder:
    def __init__(self) -> None:
        self.s = get_settings()
        self._model = None
        self._load_lock = asyncio.Lock()
        self._dim: int | None = None
        self._uses_e5_prefix = "e5" in self.s.embedding_model.lower()

    def _prefixed(self, texts: list[str], kind: Kind) -> list[str]:
        if not self._uses_e5_prefix:
            return texts
        prefix = "query: " if kind == "query" else "passage: "
        return [prefix + t for t in texts]

    async def embed(self, texts: list[str], kind: Kind = "passage") -> list[list[float]]:
        if not texts:
            return []
        texts = self._prefixed(texts, kind)
        provider = self.s.embedding_provider
        if provider == "local":
            return await self._embed_local(texts)
        if provider == "ollama":
            return await self._embed_ollama(texts)
        if provider == "openai":
            return await self._embed_openai(texts)
        raise EmbeddingError(f"Unknown EMBEDDING_PROVIDER '{provider}'")

    async def dimension(self) -> int:
        if self._dim is None:
            vec = await self.embed(["dimension probe"], "query")
            self._dim = len(vec[0])
        return self._dim

    # -- local ------------------------------------------------------------
    async def _embed_local(self, texts: list[str]) -> list[list[float]]:
        async with self._load_lock:
            if self._model is None:
                try:
                    from sentence_transformers import SentenceTransformer
                except ImportError as exc:  # pragma: no cover
                    raise EmbeddingError(
                        "sentence-transformers is not installed. Build the backend image with INSTALL_LOCAL_EMBEDDINGS=true "
                        "or set EMBEDDING_PROVIDER=ollama|openai."
                    ) from exc
                log.info("Loading embedding model %s", self.s.embedding_model)
                self._model = await asyncio.to_thread(SentenceTransformer, self.s.embedding_model)
        model = self._model

        def _run() -> list[list[float]]:
            return model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False).tolist()

        return await asyncio.to_thread(_run)

    # -- remote -----------------------------------------------------------
    def _base(self) -> str:
        base = self.s.embedding_base_url or self.s.llm_base_url
        return base.rstrip("/")

    def _headers(self) -> dict[str, str]:
        key = self.s.embedding_api_key or self.s.llm_api_key
        h = {"Content-Type": "application/json"}
        if key:
            h["Authorization"] = f"Bearer {key}"
        return h

    async def _embed_ollama(self, texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient(timeout=120) as client:
            try:
                resp = await client.post(
                    f"{self._base()}/api/embed", json={"model": self.s.embedding_model, "input": texts}, headers=self._headers()
                )
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise EmbeddingError(f"Ollama embeddings failed: {exc}") from exc
        return _normalize(resp.json()["embeddings"])

    async def _embed_openai(self, texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient(timeout=120) as client:
            try:
                resp = await client.post(
                    f"{self._base()}/embeddings", json={"model": self.s.embedding_model, "input": texts}, headers=self._headers()
                )
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise EmbeddingError(f"OpenAI-compatible embeddings failed: {exc}") from exc
        data = sorted(resp.json()["data"], key=lambda d: d["index"])
        return _normalize([d["embedding"] for d in data])


def _normalize(vectors: list[list[float]]) -> list[list[float]]:
    out = []
    for v in vectors:
        norm = sum(x * x for x in v) ** 0.5 or 1.0
        out.append([x / norm for x in v])
    return out

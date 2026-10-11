"""Qdrant wrapper. A single collection holds three kinds of points (payload.kind):
  doc      - chunks of approved Markdown documentation
  solution - user-confirmed solutions (candidates for promotion)
  web      - cached web research entries
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from qdrant_client import AsyncQdrantClient, models

from app.config import get_settings
from app.services.embeddings import Embedder

log = logging.getLogger(__name__)


@dataclass
class Hit:
    id: str
    score: float
    payload: dict[str, Any]


class VectorStore:
    def __init__(self, embedder: Embedder) -> None:
        s = get_settings()
        self.client = AsyncQdrantClient(url=s.qdrant_url, api_key=s.qdrant_api_key)
        self.collection = s.qdrant_collection
        self.embedder = embedder
        self._ready = False
        self._lock = asyncio.Lock()

    async def ensure(self) -> None:
        if self._ready:
            return
        async with self._lock:
            if self._ready:
                return
            dim = await self.embedder.dimension()
            if not await self.client.collection_exists(self.collection):
                await self.client.create_collection(
                    collection_name=self.collection,
                    vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
                )
                log.info("Created Qdrant collection %s (dim=%s)", self.collection, dim)
            else:
                info = await self.client.get_collection(self.collection)
                vectors = info.config.params.vectors
                size = getattr(vectors, "size", None)
                if size is not None and size != dim:
                    raise RuntimeError(
                        f"Qdrant collection '{self.collection}' has dimension {size} but the embedding model produces {dim}. "
                        "Use another QDRANT_COLLECTION or delete the old one, then re-index."
                    )
            for field in ("kind", "path", "ref"):
                try:
                    await self.client.create_payload_index(self.collection, field, models.PayloadSchemaType.KEYWORD)
                except Exception:  # index already exists
                    pass
            self._ready = True

    async def upsert(self, points: list[models.PointStruct]) -> None:
        if not points:
            return
        await self.ensure()
        await self.client.upsert(self.collection, points=points, wait=True)

    async def delete_where(self, **match: str) -> None:
        await self.ensure()
        flt = models.Filter(must=[models.FieldCondition(key=k, match=models.MatchValue(value=v)) for k, v in match.items()])
        await self.client.delete(self.collection, points_selector=models.FilterSelector(filter=flt), wait=True)

    async def search(
        self, vector: list[float], kinds: list[str], limit: int = 5, exclude_refs: list[str] | None = None
    ) -> list[Hit]:
        await self.ensure()
        must = [models.FieldCondition(key="kind", match=models.MatchAny(any=kinds))]
        must_not = [models.FieldCondition(key="ref", match=models.MatchAny(any=exclude_refs))] if exclude_refs else []
        res = await self.client.query_points(
            self.collection,
            query=vector,
            limit=limit,
            query_filter=models.Filter(must=must, must_not=must_not or None),
            with_payload=True,
        )
        return [Hit(id=str(p.id), score=float(p.score), payload=p.payload or {}) for p in res.points]

    async def health(self) -> bool:
        try:
            await self.client.get_collections()
            return True
        except Exception:
            return False

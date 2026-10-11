"""Managed docs store + incremental Markdown indexing into Qdrant."""

import asyncio
import hashlib
import logging
import os
import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from qdrant_client import models
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import SessionLocal
from app.models import Document
from app.redaction import redact
from app.redis_client import get_redis
from app.services.chunker import chunk_markdown, parse_document
from app.services.container import get_embedder, get_vectorstore

log = logging.getLogger(__name__)
_NS = uuid.UUID("6f1c3b1e-5a7b-4d62-9f0e-3a1c9d2b7e11")
_LOCK_KEY = "lock:ingest"


class DocsError(ValueError):
    pass


@dataclass
class SyncReport:
    indexed: list[str] = field(default_factory=list)
    skipped: int = 0
    removed: list[str] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)


def docs_root() -> Path:
    root = Path(get_settings().docs_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def safe_rel_path(rel: str) -> str:
    """Validate a user-supplied relative path and return it normalised (posix)."""
    rel = rel.replace("\\", "/").strip().lstrip("/")
    if not rel or ".." in Path(rel).parts or not rel.lower().endswith(".md"):
        raise DocsError("Path must be a relative .md path without '..'")
    if not re.fullmatch(r"[\w\-./ ]+", rel, flags=re.UNICODE):
        raise DocsError("Path contains unsupported characters")
    full = (docs_root() / rel).resolve()
    if docs_root() not in full.parents:
        raise DocsError("Path escapes the docs directory")
    return full.relative_to(docs_root()).as_posix()


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
    s = re.sub(r"[\s_]+", "-", s)
    return s[:80].strip("-") or "document"


def _point_id(path: str, idx: int) -> str:
    return str(uuid.uuid5(_NS, f"{path}#{idx}"))


async def index_content(session: AsyncSession, rel_path: str, raw: str, source: str = "imported", force: bool = False) -> Document:
    """Chunk, embed and upsert one document; update its Document row. Raises on embedding/vector errors."""
    content_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    doc = (await session.execute(select(Document).where(Document.path == rel_path))).scalar_one_or_none()
    if doc and doc.content_hash == content_hash and doc.status == "indexed" and not force:
        return doc

    parsed = parse_document(raw, fallback_title=Path(rel_path).stem)
    chunks = chunk_markdown(parsed.body, parsed.title, get_settings().chunk_max_chars)
    now = datetime.now(UTC)
    embedder, store = get_embedder(), get_vectorstore()

    try:
        points: list[models.PointStruct] = []
        if chunks:
            texts = [f"{c.heading}\n{c.text}" for c in chunks]
            vectors: list[list[float]] = []
            for i in range(0, len(texts), 32):
                vectors.extend(await embedder.embed(texts[i:i + 32], "passage"))
            for c, vec in zip(chunks, vectors, strict=True):
                points.append(
                    models.PointStruct(
                        id=_point_id(rel_path, c.index),
                        vector=vec,
                        payload={
                            "kind": "doc",
                            "ref": f"doc:{rel_path}#{c.index}",
                            "path": rel_path,
                            "filename": Path(rel_path).name,
                            "doc_title": parsed.title,
                            "heading": c.heading,
                            "chunk_index": c.index,
                            "hash": content_hash,
                            "indexed_at": now.isoformat(),
                            "text": c.text,
                        },
                    )
                )
        await store.ensure()
        await store.delete_where(kind="doc", path=rel_path)  # drop stale chunks of a previous version
        await store.upsert(points)
    except Exception as exc:
        if doc is None:
            doc = Document(path=rel_path, title=parsed.title, source=source, content_hash=content_hash)
            session.add(doc)
        doc.status, doc.error = "error", str(exc)[:1000]
        await session.commit()
        raise

    if doc is None:
        doc = Document(path=rel_path, source=source)
        session.add(doc)
    doc.title = parsed.title[:255]
    doc.content_hash = content_hash
    doc.chunk_count = len(chunks)
    doc.size_bytes = len(raw.encode("utf-8"))
    doc.status, doc.error, doc.indexed_at = "indexed", None, now
    if source != "imported" or doc.source is None:
        doc.source = source
    await session.commit()
    return doc


async def save_document(session: AsyncSession, rel_path: str, content: str, source: str, overwrite: bool = True) -> Document:
    rel = safe_rel_path(rel_path)
    full = docs_root() / rel
    if full.exists() and not overwrite:
        raise DocsError(f"'{rel}' already exists")
    full.parent.mkdir(parents=True, exist_ok=True)
    tmp = full.with_suffix(".md.tmp")
    tmp.write_text(content, encoding="utf-8", newline="\n")
    os.replace(tmp, full)
    return await index_content(session, rel, content, source=source, force=True)


async def remove_document(session: AsyncSession, doc: Document) -> None:
    store = get_vectorstore()
    await store.delete_where(kind="doc", path=doc.path)
    full = docs_root() / doc.path
    if full.exists():
        full.unlink()
    await session.delete(doc)
    await session.commit()


async def sync_directory(force: bool = False) -> SyncReport:
    """Index new/modified Markdown files, drop deleted ones. Guarded by a Redis lock."""
    redis = get_redis()
    token = uuid.uuid4().hex
    if not await redis.set(_LOCK_KEY, token, nx=True, ex=900):
        raise DocsError("Another indexing run is in progress")
    report = SyncReport()
    try:
        root = docs_root()
        files = sorted(p for p in root.rglob("*.md") if p.is_file())
        seen: set[str] = set()
        async with SessionLocal() as session:
            for path in files:
                rel = path.relative_to(root).as_posix()
                seen.add(rel)
                try:
                    raw = await asyncio.to_thread(path.read_text, encoding="utf-8")
                    existing = (await session.execute(select(Document).where(Document.path == rel))).scalar_one_or_none()
                    before = existing.content_hash if existing else None
                    source = "promoted" if rel.startswith("promoted/") else ("upload" if rel.startswith("uploads/") else "imported")
                    doc = await index_content(session, rel, raw, source=source, force=force)
                    if before != doc.content_hash or force or (existing and existing.status != "indexed"):
                        report.indexed.append(rel)
                    else:
                        report.skipped += 1
                except Exception as exc:
                    await session.rollback()
                    log.exception("Indexing failed for %s", rel)
                    report.errors.append({"path": rel, "error": redact(str(exc))[:300]})
            for doc in (await session.execute(select(Document))).scalars().all():
                if doc.path not in seen:
                    await get_vectorstore().delete_where(kind="doc", path=doc.path)
                    await session.delete(doc)
                    report.removed.append(doc.path)
            await session.commit()
    finally:
        if await redis.get(_LOCK_KEY) == token:
            await redis.delete(_LOCK_KEY)
    return report

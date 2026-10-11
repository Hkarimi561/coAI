"""Lazily-created singletons shared across the app."""

from functools import lru_cache

from app.services.embeddings import Embedder
from app.services.llm import LLMClient
from app.services.vectorstore import VectorStore


@lru_cache
def get_embedder() -> Embedder:
    return Embedder()


@lru_cache
def get_vectorstore() -> VectorStore:
    return VectorStore(get_embedder())


@lru_cache
def get_llm() -> LLMClient:
    return LLMClient()

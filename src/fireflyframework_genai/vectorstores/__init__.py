"""Pluggable vector storage and retrieval backends."""

from fireflyframework_genai.vectorstores.base import BaseVectorStore, VectorStoreProtocol
from fireflyframework_genai.vectorstores.memory_store import InMemoryVectorStore
from fireflyframework_genai.vectorstores.registry import VectorStoreRegistry
from fireflyframework_genai.vectorstores.types import SearchFilter, SearchResult, VectorDocument

__all__ = [
    "BaseVectorStore",
    "InMemoryVectorStore",
    "SearchFilter",
    "SearchResult",
    "VectorDocument",
    "VectorStoreProtocol",
    "VectorStoreRegistry",
]

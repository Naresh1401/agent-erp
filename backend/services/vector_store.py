"""Qdrant vector store service for semantic search over ERP documents."""

from __future__ import annotations

import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class VectorStoreService:
    def __init__(self) -> None:
        self.client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        self.collection = settings.qdrant_collection
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection not in collections:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )
            logger.info(f"Created Qdrant collection: {self.collection}")

    def upsert(self, doc_id: str, embedding: list[float], payload: dict[str, Any]) -> None:
        self.client.upsert(
            collection_name=self.collection,
            points=[PointStruct(id=doc_id, vector=embedding, payload=payload)],
        )

    def search(self, query_embedding: list[float], limit: int = 10) -> list[dict[str, Any]]:
        results = self.client.search(
            collection_name=self.collection,
            query_vector=query_embedding,
            limit=limit,
        )
        return [
            {"id": str(r.id), "score": r.score, "payload": r.payload}
            for r in results
        ]

    def delete(self, doc_id: str) -> None:
        self.client.delete(
            collection_name=self.collection,
            points_selector=[doc_id],
        )


def get_vector_store() -> VectorStoreService:
    return VectorStoreService()

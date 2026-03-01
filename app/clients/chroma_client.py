from __future__ import annotations

import asyncio
from typing import Any

import chromadb

from app.models.schemas import RetrieveResult


class ChromaClientError(Exception):
    pass


class ChromaClientWrapper:
    def __init__(self, base_url: str, collection_name: str, timeout: float, threshold: float) -> None:
        self._base_url = base_url
        self._collection_name = collection_name
        self._timeout = timeout
        self._threshold = threshold
        self._client = chromadb.HttpClient(host=self._extract_host(base_url), port=self._extract_port(base_url))

    @staticmethod
    def _extract_host(url: str) -> str:
        cleaned = url.replace("http://", "").replace("https://", "")
        return cleaned.split(":")[0]

    @staticmethod
    def _extract_port(url: str) -> int:
        cleaned = url.replace("http://", "").replace("https://", "")
        parts = cleaned.split(":")
        if len(parts) > 1:
            return int(parts[1])
        return 8000

    async def retrieve(self, query: str, top_k: int) -> RetrieveResult:
        try:
            collection = await asyncio.to_thread(self._client.get_collection, self._collection_name)
            raw: dict[str, Any] = await asyncio.to_thread(
                collection.query,
                query_texts=[query],
                n_results=top_k,
                include=["documents", "distances"],
            )
        except Exception as error:
            raise ChromaClientError(str(error)) from error

        docs = raw.get("documents", [[]])[0] or []
        distances = raw.get("distances", [[]])[0] or []

        filtered_docs: list[str] = []
        filtered_scores: list[float] = []

        for doc, dist in zip(docs, distances):
            score = max(0.0, min(1.0, 1.0 - float(dist)))
            if score >= self._threshold:
                filtered_docs.append(doc)
                filtered_scores.append(score)

        return RetrieveResult(documents=filtered_docs, scores=filtered_scores)

    async def health_check(self) -> bool:
        try:
            collections = await asyncio.to_thread(self._client.list_collections)
            names = {c.name for c in collections}
            return self._collection_name in names
        except Exception:
            return False

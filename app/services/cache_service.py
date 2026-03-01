from __future__ import annotations

import hashlib
import json
from typing import Any

import redis.asyncio as redis

from app.models.schemas import CacheStatsResponse, RetrieveResult, WorkflowResponse
from app.services.semantic_cache import cosine_similarity, text_to_embedding


class CacheService:
    def __init__(self, redis_url: str, ttl_seconds: int, semantic_threshold: float) -> None:
        self._redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        self._ttl = ttl_seconds
        self._semantic_threshold = semantic_threshold

    @staticmethod
    def _hash_key(raw: str) -> str:
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _exact_key(self, question: str, level: str) -> str:
        return f"cache:exact:{self._hash_key(f'{question}|{level}') }"

    def _retrieval_key(self, question: str, top_k: int) -> str:
        return f"cache:retrieval:{self._hash_key(f'{question}|{top_k}') }"

    def _semantic_key(self, item_id: str) -> str:
        return f"cache:semantic:item:{item_id}"

    async def get_exact(self, question: str, level: str) -> WorkflowResponse | None:
        payload = await self._redis.get(self._exact_key(question, level))
        if not payload:
            return None
        return WorkflowResponse.model_validate_json(payload)

    async def set_exact(self, question: str, level: str, response: WorkflowResponse) -> None:
        await self._redis.set(
            self._exact_key(question, level),
            response.model_dump_json(),
            ex=self._ttl,
        )

    async def get_retrieval(self, question: str, top_k: int) -> RetrieveResult | None:
        payload = await self._redis.get(self._retrieval_key(question, top_k))
        if not payload:
            return None
        data = json.loads(payload)
        return RetrieveResult(**data)

    async def set_retrieval(self, question: str, top_k: int, result: RetrieveResult) -> None:
        await self._redis.set(
            self._retrieval_key(question, top_k),
            json.dumps(result.model_dump(), ensure_ascii=False),
            ex=self._ttl,
        )

    async def find_semantic(self, question: str, level: str) -> WorkflowResponse | None:
        query_emb = text_to_embedding(question)
        keys = await self._redis.keys("cache:semantic:item:*")

        best_item: dict[str, Any] | None = None
        best_score = 0.0

        for key in keys:
            raw = await self._redis.get(key)
            if not raw:
                continue
            item = json.loads(raw)
            if item.get("level") != level:
                continue
            cached_emb = item.get("embedding")
            if not isinstance(cached_emb, list):
                continue
            score = cosine_similarity(query_emb, [float(v) for v in cached_emb])
            if score > best_score:
                best_score = score
                best_item = item

        if not best_item or best_score < self._semantic_threshold:
            return None

        response = WorkflowResponse(**best_item["response"])
        return response

    async def set_semantic(self, question: str, level: str, response: WorkflowResponse) -> None:
        item_id = self._hash_key(f"{question}|{level}|{response.answer[:80]}")
        payload = {
            "question": question,
            "level": level,
            "embedding": text_to_embedding(question),
            "response": response.model_dump(),
        }
        await self._redis.set(self._semantic_key(item_id), json.dumps(payload, ensure_ascii=False), ex=self._ttl)

    async def clear(self) -> int:
        keys = await self._redis.keys("cache:*")
        if not keys:
            return 0
        return int(await self._redis.delete(*keys))

    async def stats(self) -> CacheStatsResponse:
        exact = len(await self._redis.keys("cache:exact:*") or [])
        semantic = len(await self._redis.keys("cache:semantic:item:*") or [])
        retrieval = len(await self._redis.keys("cache:retrieval:*") or [])
        return CacheStatsResponse(exact_entries=exact, semantic_entries=semantic, retrieval_entries=retrieval)

    async def health_check(self) -> bool:
        try:
            pong = await self._redis.ping()
            return bool(pong)
        except Exception:
            return False

    async def aclose(self) -> None:
        await self._redis.aclose()

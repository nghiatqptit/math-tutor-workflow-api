from __future__ import annotations

from app.clients.chroma_client import ChromaClientWrapper
from app.clients.ollama_client import OllamaClientWrapper
from app.services.cache_service import CacheService


class HealthService:
    def __init__(
        self,
        chroma_client: ChromaClientWrapper,
        math_client: OllamaClientWrapper,
        viet_client: OllamaClientWrapper,
        cache_service: CacheService,
    ) -> None:
        self._chroma = chroma_client
        self._math = math_client
        self._viet = viet_client
        self._cache = cache_service

    async def live(self) -> dict:
        return {"status": "ok"}

    async def ready(self) -> tuple[bool, dict]:
        chroma_ok, math_ok, viet_ok, redis_ok = await self._run_checks()
        details = {
            "chromadb": "ok" if chroma_ok else "down",
            "ollama_math": "ok" if math_ok else "down",
            "ollama_viet": "ok" if viet_ok else "down",
            "redis": "ok" if redis_ok else "down",
        }
        return all([chroma_ok, math_ok, viet_ok, redis_ok]), details

    async def _run_checks(self) -> tuple[bool, bool, bool, bool]:
        chroma_ok = await self._chroma.health_check()
        math_ok = await self._math.health_check()
        viet_ok = await self._viet.health_check()
        redis_ok = await self._cache.health_check()
        return chroma_ok, math_ok, viet_ok, redis_ok

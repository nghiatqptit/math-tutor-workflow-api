from __future__ import annotations

from functools import lru_cache

from app.clients.chroma_client import ChromaClientWrapper
from app.clients.ollama_client import OllamaClientWrapper
from app.config.settings import get_settings
from app.services.cache_service import CacheService
from app.services.correction_loop import CorrectionLoopService
from app.services.sandbox_executor import SandboxExecutor
from app.services.verifier import VerifierService
from app.services.workflow_service import WorkflowService


@lru_cache(maxsize=1)
def get_chroma_client() -> ChromaClientWrapper:
    settings = get_settings()
    return ChromaClientWrapper(
        base_url=settings.chromadb_url,
        collection_name=settings.chroma_collection,
        timeout=settings.request_timeout,
        threshold=settings.similarity_threshold,
    )


@lru_cache(maxsize=1)
def get_math_client() -> OllamaClientWrapper:
    settings = get_settings()
    return OllamaClientWrapper(
        base_url=settings.ollama_math_url,
        model=settings.model_math,
        timeout=settings.request_timeout,
        retry_attempts=settings.retry_attempts,
        breaker_threshold=settings.breaker_threshold,
        breaker_reset_seconds=settings.breaker_reset_seconds,
    )


@lru_cache(maxsize=1)
def get_viet_client() -> OllamaClientWrapper:
    settings = get_settings()
    return OllamaClientWrapper(
        base_url=settings.ollama_viet_url,
        model=settings.model_viet,
        timeout=settings.request_timeout,
        retry_attempts=settings.retry_attempts,
        breaker_threshold=settings.breaker_threshold,
        breaker_reset_seconds=settings.breaker_reset_seconds,
    )


@lru_cache(maxsize=1)
def get_cache_service() -> CacheService:
    settings = get_settings()
    return CacheService(
        redis_url=settings.redis_url,
        ttl_seconds=settings.cache_ttl,
        semantic_threshold=settings.semantic_threshold,
    )


@lru_cache(maxsize=1)
def get_sandbox_executor() -> SandboxExecutor:
    settings = get_settings()
    return SandboxExecutor(
        timeout_seconds=settings.sandbox_timeout,
        memory_mb=settings.sandbox_memory_mb,
        code_size_limit=settings.code_size_limit,
    )


@lru_cache(maxsize=1)
def get_verifier() -> VerifierService:
    return VerifierService()


@lru_cache(maxsize=1)
def get_correction_loop() -> CorrectionLoopService:
    return CorrectionLoopService(math_client=get_math_client())


@lru_cache(maxsize=1)
def get_workflow_service() -> WorkflowService:
    settings = get_settings()
    return WorkflowService(
        settings=settings,
        chroma_client=get_chroma_client(),
        math_client=get_math_client(),
        viet_client=get_viet_client(),
        cache_service=get_cache_service(),
        sandbox_executor=get_sandbox_executor(),
        verifier=get_verifier(),
        correction_loop=get_correction_loop(),
    )

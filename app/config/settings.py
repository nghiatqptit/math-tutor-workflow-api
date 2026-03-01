from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "math-tutor-workflow-api")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")

    request_timeout: float = float(os.getenv("REQUEST_TIMEOUT", "25"))
    top_k: int = int(os.getenv("TOP_K", "3"))
    similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.35"))

    ollama_math_url: str = os.getenv("OLLAMA_MATH_URL", "http://ollama-gpu:11434")
    ollama_viet_url: str = os.getenv("OLLAMA_VIET_URL", "http://ollama-viet:11434")
    chromadb_url: str = os.getenv("CHROMADB_URL", "http://chromadb:8000")
    chroma_collection: str = os.getenv("CHROMA_COLLECTION", "math_tutor_knowledge")

    model_math: str = os.getenv("MODEL_MATH", "qwen2.5-coder:7b-instruct")
    model_viet: str = os.getenv("MODEL_VIET", "sailor2:1b-iq4_nl")

    retry_attempts: int = int(os.getenv("RETRY_ATTEMPTS", "3"))
    breaker_threshold: int = int(os.getenv("BREAKER_THRESHOLD", "5"))
    breaker_reset_seconds: int = int(os.getenv("BREAKER_RESET_SECONDS", "30"))
    context_char_limit: int = int(os.getenv("CONTEXT_CHAR_LIMIT", "2200"))

    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    cache_ttl: int = int(os.getenv("CACHE_TTL", "1800"))
    semantic_threshold: float = float(os.getenv("SEMANTIC_THRESHOLD", "0.92"))

    sandbox_timeout: float = float(os.getenv("SANDBOX_TIMEOUT", "2"))
    sandbox_memory_mb: int = int(os.getenv("SANDBOX_MEMORY_MB", "128"))
    code_size_limit: int = int(os.getenv("CODE_SIZE_LIMIT", "6000"))
    max_reasoning_tokens_cap: int = int(os.getenv("MAX_REASONING_TOKENS_CAP", "1200"))

    enable_self_correction: bool = os.getenv("ENABLE_SELF_CORRECTION", "true").lower() == "true"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def max_tokens_for_level(level: str) -> int:
    normalized = level.strip().lower()
    if normalized == "thcs":
        return 512
    if normalized == "thpt":
        return 768
    if normalized in {"đại học", "dai hoc", "university"}:
        return 1024
    return 768

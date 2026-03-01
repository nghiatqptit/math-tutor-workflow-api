from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Level(str, Enum):
    THCS = "THCS"
    THPT = "THPT"
    DAI_HOC = "Đại học"


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=5000)
    level: Level = Field(default=Level.THPT)
    stream: bool = Field(default=False)
    top_k: int | None = Field(default=None, ge=1, le=10)


class RagOnlyResponse(BaseModel):
    context: list[str]
    scores: list[float]


class WorkflowResponse(BaseModel):
    answer: str
    latex: str | None = None
    code: str | None = None
    confidence: float = Field(..., ge=0, le=1)
    cache_hit: bool = False
    cache_layer: str | None = None
    verified: bool = False
    correction_attempted: bool = False
    trace_id: str | None = None
    latency_ms: int
    retrieval_time_ms: int
    reasoning_time_ms: int
    verification_time_ms: int = 0
    formatting_time_ms: int


class HealthResponse(BaseModel):
    status: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    detail: str


class ModelTextResponse(BaseModel):
    text: str
    latency_ms: int


class RetrieveResult(BaseModel):
    documents: list[str]
    scores: list[float]


class ReasoningResult(BaseModel):
    reasoning_steps: str
    final_answer: str
    latex: str | None = None
    python_code: str | None = None
    confidence: float = 0.5

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, value: float) -> float:
        return max(0.0, min(1.0, value))


class SandboxResult(BaseModel):
    execution_success: bool
    evaluated_result: str | None = None
    error: str | None = None


class VerificationResult(BaseModel):
    verified: bool
    reason: str
    normalized_llm_answer: str | None = None
    normalized_exec_answer: str | None = None


class VerifyOnlyResponse(BaseModel):
    verification: VerificationResult
    sandbox: SandboxResult
    latency_ms: int


class CacheStatsResponse(BaseModel):
    exact_entries: int
    semantic_entries: int
    retrieval_entries: int

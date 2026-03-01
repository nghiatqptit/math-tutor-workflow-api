from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import AsyncIterator

from app.clients.chroma_client import ChromaClientWrapper
from app.clients.ollama_client import OllamaClientWrapper, extract_json_object
from app.config.metrics import (
    AVG_REASONING_TIME,
    AVG_VERIFICATION_TIME,
    CACHE_HITS,
    CACHE_LOOKUPS,
    CORRECTION_SUCCESS,
    CORRECTION_TOTAL,
    EXTERNAL_ERRORS,
    STAGE_LATENCY,
    VERIFICATION_FAILURES,
    VERIFICATION_TOTAL,
)
from app.config.settings import Settings, max_tokens_for_level
from app.models.schemas import (
    CacheStatsResponse,
    ChatRequest,
    ReasoningResult,
    RetrieveResult,
    SandboxResult,
    VerificationResult,
    VerifyOnlyResponse,
    WorkflowResponse,
)
from app.services.cache_service import CacheService
from app.services.correction_loop import CorrectionLoopService
from app.services.prompt_builder import build_format_messages, build_math_messages, merge_template
from app.services.sandbox_executor import SandboxExecutor
from app.services.sanitizer import enforce_code_limit, sanitize_latex, sanitize_question
from app.services.verifier import VerifierService

logger = logging.getLogger(__name__)


class WorkflowService:
    def __init__(
        self,
        settings: Settings,
        chroma_client: ChromaClientWrapper,
        math_client: OllamaClientWrapper,
        viet_client: OllamaClientWrapper,
        cache_service: CacheService,
        sandbox_executor: SandboxExecutor,
        verifier: VerifierService,
        correction_loop: CorrectionLoopService,
    ) -> None:
        self._settings = settings
        self._chroma = chroma_client
        self._math = math_client
        self._viet = viet_client
        self._cache = cache_service
        self._sandbox = sandbox_executor
        self._verifier = verifier
        self._correction = correction_loop

    def _parse_reasoning_output(self, text: str) -> ReasoningResult:
        parsed = extract_json_object(text) or {}
        reasoning_steps = str(parsed.get("reasoning_steps") or text or "Không đủ dữ liệu để giải chính xác.")
        final_answer = str(parsed.get("final_answer") or "Chưa xác định")
        latex = sanitize_latex(parsed.get("latex")) if parsed.get("latex") else None
        python_code = parsed.get("python_code") if isinstance(parsed.get("python_code"), str) else None
        confidence = 0.55
        if isinstance(parsed.get("confidence_score"), (float, int)):
            confidence = float(parsed["confidence_score"])

        python_code = enforce_code_limit(python_code, self._settings.code_size_limit)
        return ReasoningResult(
            reasoning_steps=reasoning_steps,
            final_answer=final_answer,
            latex=latex,
            python_code=python_code,
            confidence=confidence,
        )

    async def retrieve_context(self, question: str, top_k: int) -> tuple[RetrieveResult, int]:
        started = time.perf_counter()
        CACHE_LOOKUPS.labels(layer="retrieval").inc()
        cached = await self._cache.get_retrieval(question, top_k)
        if cached:
            CACHE_HITS.labels(layer="retrieval").inc()
            elapsed = int((time.perf_counter() - started) * 1000)
            STAGE_LATENCY.labels(stage="retrieval").observe(elapsed / 1000)
            return cached, elapsed

        try:
            result = await self._chroma.retrieve(question, top_k)
            await self._cache.set_retrieval(question, top_k, result)
        except Exception:
            EXTERNAL_ERRORS.labels(dependency="chromadb").inc()
            logger.exception("chromadb_retrieval_failed")
            result = RetrieveResult(documents=[], scores=[])
        elapsed = int((time.perf_counter() - started) * 1000)
        STAGE_LATENCY.labels(stage="retrieval").observe(elapsed / 1000)
        return result, elapsed

    async def _run_reasoning(self, question: str, level: str, context: list[str]) -> tuple[ReasoningResult, int]:
        started = time.perf_counter()
        messages = build_math_messages(
            question=question,
            level=level,
            context=context,
            context_char_limit=self._settings.context_char_limit,
        )

        try:
            text, _ = await self._math.chat_text(
                messages=messages,
                temperature=0.1,
                max_tokens=min(max_tokens_for_level(level), self._settings.max_reasoning_tokens_cap),
            )
        except Exception:
            EXTERNAL_ERRORS.labels(dependency="ollama_math").inc()
            logger.exception("math_reasoning_failed")
            text = ""

        reasoning_result = self._parse_reasoning_output(text)
        if len(reasoning_result.reasoning_steps) < 80:
            reasoning_result.confidence = min(reasoning_result.confidence, 0.45)

        elapsed = int((time.perf_counter() - started) * 1000)
        STAGE_LATENCY.labels(stage="reasoning").observe(elapsed / 1000)
        AVG_REASONING_TIME.observe(elapsed / 1000)

        return reasoning_result, elapsed

    async def _run_format_scaffold(self, question: str, level: str) -> tuple[str, int]:
        started = time.perf_counter()
        messages = build_format_messages(question=question, level=level)

        try:
            text, _ = await self._viet.chat_text(
                messages=messages,
                temperature=0.2,
                max_tokens=380,
            )
        except Exception:
            EXTERNAL_ERRORS.labels(dependency="ollama_viet").inc()
            logger.exception("viet_format_failed")
            text = "Ý tưởng:\nTiếp cận bài toán theo dữ kiện đã cho.\n\nCác bước giải:\n{{REASONING_CORE}}\n\nKết luận:\nRút gọn kết quả cuối cùng."

        elapsed = int((time.perf_counter() - started) * 1000)
        STAGE_LATENCY.labels(stage="formatting").observe(elapsed / 1000)
        return text, elapsed

    async def math_only(self, question: str, level: str) -> tuple[ReasoningResult, int]:
        sanitized_question = sanitize_question(question)
        return await self._run_reasoning(sanitized_question, level, context=[])

    async def format_only(self, question: str, level: str) -> tuple[str, int]:
        sanitized_question = sanitize_question(question)
        return await self._run_format_scaffold(sanitized_question, level)

    async def verify_reasoning(self, reasoning: ReasoningResult) -> tuple[VerificationResult, SandboxResult, int]:
        started = time.perf_counter()
        VERIFICATION_TOTAL.inc()
        sandbox = await self._sandbox.execute(reasoning.python_code)
        verification = self._verifier.verify(reasoning.final_answer, sandbox)
        elapsed = int((time.perf_counter() - started) * 1000)
        STAGE_LATENCY.labels(stage="verification").observe(elapsed / 1000)
        AVG_VERIFICATION_TIME.observe(elapsed / 1000)
        if not verification.verified:
            VERIFICATION_FAILURES.inc()
        return verification, sandbox, elapsed

    async def verify_only(self, request: ChatRequest) -> VerifyOnlyResponse:
        start = time.perf_counter()
        reasoning, _ = await self.math_only(request.question, request.level.value)
        verification, sandbox, _ = await self.verify_reasoning(reasoning)
        return VerifyOnlyResponse(
            verification=verification,
            sandbox=sandbox,
            latency_ms=int((time.perf_counter() - start) * 1000),
        )

    async def cache_clear(self) -> int:
        return await self._cache.clear()

    async def cache_stats(self) -> CacheStatsResponse:
        return await self._cache.stats()

    async def orchestrate(self, request: ChatRequest, trace_id: str | None = None) -> WorkflowResponse:
        overall = time.perf_counter()
        question = sanitize_question(request.question)
        top_k = request.top_k or self._settings.top_k
        logger.info("orchestrate_started", extra={"request_id": trace_id})

        CACHE_LOOKUPS.labels(layer="exact").inc()
        exact = await self._cache.get_exact(question, request.level.value)
        if exact:
            CACHE_HITS.labels(layer="exact").inc()
            exact.cache_hit = True
            exact.cache_layer = "exact"
            exact.trace_id = trace_id
            exact.latency_ms = int((time.perf_counter() - overall) * 1000)
            return exact

        CACHE_LOOKUPS.labels(layer="semantic").inc()
        semantic = await self._cache.find_semantic(question, request.level.value)
        if semantic:
            CACHE_HITS.labels(layer="semantic").inc()
            semantic.cache_hit = True
            semantic.cache_layer = "semantic"
            semantic.trace_id = trace_id
            semantic.latency_ms = int((time.perf_counter() - overall) * 1000)
            return semantic

        retrieval_result, retrieval_ms = await self.retrieve_context(question, top_k)
        logger.info("retrieval_completed", extra={"request_id": trace_id})

        reasoning_task = asyncio.create_task(
            self._run_reasoning(question=question, level=request.level.value, context=retrieval_result.documents)
        )
        format_task = asyncio.create_task(self._run_format_scaffold(question=question, level=request.level.value))

        (reasoning_result, reasoning_ms), (template, formatting_ms) = await asyncio.gather(reasoning_task, format_task)

        verification, sandbox, verification_ms = await self.verify_reasoning(reasoning_result)
        logger.info("verification_completed", extra={"request_id": trace_id})
        correction_attempted = False

        if not verification.verified and self._settings.enable_self_correction:
            correction_attempted = True
            CORRECTION_TOTAL.inc()
            corrected = await self._correction.run_once(
                question=question,
                level=request.level.value,
                previous=reasoning_result,
                sympy_result=sandbox.evaluated_result or sandbox.error or "N/A",
            )
            corrected_verification, corrected_sandbox, corrected_ms = await self.verify_reasoning(corrected)
            verification_ms += corrected_ms
            if corrected_verification.verified:
                CORRECTION_SUCCESS.inc()
                reasoning_result = corrected
                verification = corrected_verification
                sandbox = corrected_sandbox

        verified_line = (
            f"Kết quả symbolic đã xác minh: {sandbox.evaluated_result}"
            if verification.verified and sandbox.evaluated_result
            else "Kết quả symbolic chưa xác minh được hoàn toàn."
        )

        reasoning_block = f"{reasoning_result.reasoning_steps}\n\nĐáp án cuối: {reasoning_result.final_answer}\n{verified_line}"
        answer = merge_template(
            template=template,
            reasoning=reasoning_block,
            latex=reasoning_result.latex,
            code=reasoning_result.python_code,
        )

        confidence = reasoning_result.confidence
        if retrieval_result.scores:
            confidence = min(1.0, (confidence + (sum(retrieval_result.scores) / len(retrieval_result.scores))) / 2)
        if not verification.verified:
            confidence = min(confidence, 0.38)

        if confidence < 0.45:
            answer = (
                "Mình chưa đủ tự tin để trả lời chính xác. "
                "Bạn có thể bổ sung điều kiện bài toán (hệ số, miền giá trị, hoặc mục tiêu cụ thể) để mình giải chi tiết hơn không?"
            )

        total_ms = int((time.perf_counter() - overall) * 1000)

        response = WorkflowResponse(
            answer=answer,
            latex=reasoning_result.latex,
            code=reasoning_result.python_code,
            confidence=round(confidence, 3),
            cache_hit=False,
            cache_layer=None,
            verified=verification.verified,
            correction_attempted=correction_attempted,
            trace_id=trace_id,
            latency_ms=total_ms,
            retrieval_time_ms=retrieval_ms,
            reasoning_time_ms=reasoning_ms,
            verification_time_ms=verification_ms,
            formatting_time_ms=formatting_ms,
        )

        await self._cache.set_exact(question, request.level.value, response)
        await self._cache.set_semantic(question, request.level.value, response)
        logger.info("orchestrate_completed", extra={"request_id": trace_id})
        return response

    async def orchestrate_stream(self, request: ChatRequest) -> AsyncIterator[bytes]:
        overall = time.perf_counter()
        question = sanitize_question(request.question)
        top_k = request.top_k or self._settings.top_k

        retrieval_result, retrieval_ms = await self.retrieve_context(question, top_k)
        template_task = asyncio.create_task(self._run_format_scaffold(question=question, level=request.level.value))

        messages = build_math_messages(
            question=question,
            level=request.level.value,
            context=retrieval_result.documents,
            context_char_limit=self._settings.context_char_limit,
        )
        tokens: list[str] = []

        yield (json.dumps({"event": "stage", "data": "retrieval_done", "retrieval_ms": retrieval_ms}) + "\n").encode("utf-8")

        reasoning_started = time.perf_counter()
        try:
            async for token in self._math.chat_stream(
                messages=messages,
                temperature=0.1,
                max_tokens=min(max_tokens_for_level(request.level.value), self._settings.max_reasoning_tokens_cap),
            ):
                tokens.append(token)
                yield (json.dumps({"event": "reasoning_token", "data": token}) + "\n").encode("utf-8")
        except Exception:
            EXTERNAL_ERRORS.labels(dependency="ollama_math").inc()
            logger.exception("math_stream_failed")
            fallback = "Xin lỗi, luồng suy luận bị gián đoạn."
            tokens = [fallback]
            yield (json.dumps({"event": "reasoning_token", "data": fallback}) + "\n").encode("utf-8")

        reasoning_ms = int((time.perf_counter() - reasoning_started) * 1000)
        STAGE_LATENCY.labels(stage="reasoning").observe(reasoning_ms / 1000)

        template, formatting_ms = await template_task

        raw_reasoning = "".join(tokens).strip()
        reasoning_result = self._parse_reasoning_output(raw_reasoning)
        verification, sandbox, verification_ms = await self.verify_reasoning(reasoning_result)

        reasoning_block = (
            f"{reasoning_result.reasoning_steps}\n\nĐáp án cuối: {reasoning_result.final_answer}\n"
            f"Kết quả symbolic: {sandbox.evaluated_result or sandbox.error or 'N/A'}"
        )

        answer = merge_template(
            template=template,
            reasoning=reasoning_block,
            latex=reasoning_result.latex,
            code=reasoning_result.python_code,
        )
        confidence = reasoning_result.confidence
        if retrieval_result.scores:
            confidence = min(1.0, (confidence + (sum(retrieval_result.scores) / len(retrieval_result.scores))) / 2)
        if not verification.verified:
            confidence = min(confidence, 0.38)

        total_ms = int((time.perf_counter() - overall) * 1000)

        final_payload = {
            "answer": answer,
            "latex": reasoning_result.latex,
            "code": reasoning_result.python_code,
            "confidence": round(max(0.0, min(confidence, 1.0)), 3),
            "verified": verification.verified,
            "cache_hit": False,
            "cache_layer": None,
            "latency_ms": total_ms,
            "retrieval_time_ms": retrieval_ms,
            "reasoning_time_ms": reasoning_ms,
            "verification_time_ms": verification_ms,
            "formatting_time_ms": formatting_ms,
        }
        yield (json.dumps({"event": "final", "data": final_payload}, ensure_ascii=False) + "\n").encode("utf-8")

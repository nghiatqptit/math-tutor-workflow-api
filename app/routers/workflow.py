from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.dependencies import get_workflow_service
from app.models.schemas import CacheStatsResponse, ChatRequest, ModelTextResponse, RagOnlyResponse, VerifyOnlyResponse, WorkflowResponse
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/api/v1", tags=["workflow"])


@router.post("/workflow/chat", response_model=WorkflowResponse)
async def workflow_chat(
    http_request: Request,
    request: ChatRequest,
    service: WorkflowService = Depends(get_workflow_service),
):
    if request.stream:
        return StreamingResponse(
            service.orchestrate_stream(request),
            media_type="application/x-ndjson",
        )
    trace_id = getattr(http_request.state, "request_id", None)
    return await service.orchestrate(request, trace_id=trace_id)


@router.post("/rag-only", response_model=RagOnlyResponse)
async def rag_only(
    request: ChatRequest,
    service: WorkflowService = Depends(get_workflow_service),
):
    result, _ = await service.retrieve_context(request.question, request.top_k or 3)
    return RagOnlyResponse(context=result.documents, scores=result.scores)


@router.post("/math-only", response_model=ModelTextResponse)
async def math_only(
    request: ChatRequest,
    service: WorkflowService = Depends(get_workflow_service),
):
    result, latency = await service.math_only(request.question, request.level.value)
    return ModelTextResponse(
        text=json.dumps(
            {
                "reasoning_steps": result.reasoning_steps,
                "final_answer": result.final_answer,
                "latex": result.latex,
                "python_code": result.python_code,
                "confidence": result.confidence,
            },
            ensure_ascii=False,
        ),
        latency_ms=latency,
    )


@router.post("/format-only", response_model=ModelTextResponse)
async def format_only(
    request: ChatRequest,
    service: WorkflowService = Depends(get_workflow_service),
):
    scaffold, latency = await service.format_only(request.question, request.level.value)
    return ModelTextResponse(text=scaffold, latency_ms=latency)


@router.post("/verify-only", response_model=VerifyOnlyResponse)
async def verify_only(
    request: ChatRequest,
    service: WorkflowService = Depends(get_workflow_service),
):
    return await service.verify_only(request)


@router.post("/cache/clear")
async def cache_clear(
    service: WorkflowService = Depends(get_workflow_service),
):
    cleared = await service.cache_clear()
    return {"cleared_keys": cleared}


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def cache_stats(
    service: WorkflowService = Depends(get_workflow_service),
):
    return await service.cache_stats()

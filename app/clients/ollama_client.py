from __future__ import annotations

import json
import re
import time
from typing import Any, AsyncIterator

import httpx
from ollama import AsyncClient
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.clients.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError


class OllamaClientError(Exception):
    pass


class OllamaClientWrapper:
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: float,
        retry_attempts: int,
        breaker_threshold: int,
        breaker_reset_seconds: int,
    ) -> None:
        self._model = model
        self._timeout = timeout
        self._retry_attempts = retry_attempts
        self._client = AsyncClient(host=base_url, timeout=timeout)
        self._http = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        )
        self._breaker = CircuitBreaker(
            threshold=breaker_threshold,
            reset_seconds=breaker_reset_seconds,
        )

    @property
    def model(self) -> str:
        return self._model

    async def _chat_once(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> Any:
        await self._breaker.before_call()
        try:
            response = await self._client.chat(
                model=self._model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                stream=stream,
            )
            await self._breaker.on_success()
            return response
        except (httpx.HTTPError, TimeoutError, CircuitBreakerOpenError) as error:
            await self._breaker.on_failure()
            raise OllamaClientError(str(error)) from error

    def _retry_decorator(self):
        return retry(
            reraise=True,
            stop=stop_after_attempt(self._retry_attempts),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
            retry=retry_if_exception_type(OllamaClientError),
        )

    async def chat_text(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> tuple[str, int]:
        start = time.perf_counter()

        @self._retry_decorator()
        async def _execute() -> Any:
            return await self._chat_once(messages, temperature, max_tokens, stream=False)

        response = await _execute()
        text = response.get("message", {}).get("content", "").strip()
        latency_ms = int((time.perf_counter() - start) * 1000)
        return text, latency_ms

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> AsyncIterator[str]:
        @self._retry_decorator()
        async def _execute() -> Any:
            return await self._chat_once(messages, temperature, max_tokens, stream=True)

        stream = await _execute()
        async for chunk in stream:
            token = chunk.get("message", {}).get("content", "")
            if token:
                yield token

    async def health_check(self) -> bool:
        try:
            await self._breaker.before_call()
            resp = await self._http.get("/api/tags")
            resp.raise_for_status()
            body = resp.json()
            models = {m.get("model") for m in body.get("models", [])}
            ok = self._model in models
            if ok:
                await self._breaker.on_success()
            else:
                await self._breaker.on_failure()
            return ok
        except Exception:
            await self._breaker.on_failure()
            return False

    async def aclose(self) -> None:
        await self._http.aclose()


def extract_json_object(text: str) -> dict[str, Any] | None:
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?", "", candidate).strip()
        candidate = re.sub(r"```$", "", candidate).strip()

    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        return None
    return None

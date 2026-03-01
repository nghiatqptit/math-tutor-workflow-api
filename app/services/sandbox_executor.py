from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from app.models.schemas import SandboxResult


class SandboxExecutor:
    def __init__(self, timeout_seconds: float, memory_mb: int, code_size_limit: int) -> None:
        self._timeout = timeout_seconds
        self._memory_mb = memory_mb
        self._code_size_limit = code_size_limit
        self._worker = Path(__file__).with_name("sandbox_worker.py")

    async def execute(self, code: str | None) -> SandboxResult:
        if not code:
            return SandboxResult(execution_success=False, evaluated_result=None, error="No code provided")

        if len(code) > self._code_size_limit:
            return SandboxResult(execution_success=False, evaluated_result=None, error="Code exceeds allowed size")

        payload = json.dumps({"code": code, "memory_mb": self._memory_mb}, ensure_ascii=False).encode("utf-8")

        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-I",
            "-S",
            str(self._worker),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(input=payload), timeout=self._timeout)
        except TimeoutError:
            process.kill()
            await process.wait()
            return SandboxResult(execution_success=False, evaluated_result=None, error="Sandbox timeout")

        if process.returncode != 0:
            return SandboxResult(
                execution_success=False,
                evaluated_result=None,
                error=stderr.decode("utf-8", errors="ignore").strip() or "Sandbox execution error",
            )

        try:
            parsed = json.loads(stdout.decode("utf-8", errors="ignore") or "{}")
        except json.JSONDecodeError:
            return SandboxResult(execution_success=False, evaluated_result=None, error="Invalid sandbox output")

        return SandboxResult(**parsed)

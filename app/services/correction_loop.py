from __future__ import annotations

from app.clients.ollama_client import OllamaClientWrapper, extract_json_object
from app.config.settings import max_tokens_for_level
from app.models.schemas import ReasoningResult


class CorrectionLoopService:
    def __init__(self, math_client: OllamaClientWrapper) -> None:
        self._math = math_client

    async def run_once(
        self,
        question: str,
        level: str,
        previous: ReasoningResult,
        sympy_result: str,
    ) -> ReasoningResult:
        messages = [
            {
                "role": "system",
                "content": (
                    "Bạn là máy sửa lỗi toán học. "
                    "Đối chiếu lời giải trước đó với kết quả symbolic để hòa giải khác biệt. "
                    "Trả về JSON hợp lệ với keys: reasoning_steps, final_answer, python_code, confidence_score."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n"
                    f"Level: {level}\n"
                    f"Previous reasoning: {previous.reasoning_steps}\n"
                    f"Previous final answer: {previous.final_answer}\n"
                    f"Symbolic output: {sympy_result}\n"
                    "Yêu cầu: sửa lời giải sao cho final_answer nhất quán với symbolic output."
                ),
            },
        ]

        text, _ = await self._math.chat_text(
            messages=messages,
            temperature=0.05,
            max_tokens=max_tokens_for_level(level),
        )

        parsed = extract_json_object(text) or {}
        return ReasoningResult(
            reasoning_steps=str(parsed.get("reasoning_steps") or previous.reasoning_steps),
            final_answer=str(parsed.get("final_answer") or previous.final_answer),
            python_code=parsed.get("python_code") if isinstance(parsed.get("python_code"), str) else previous.python_code,
            latex=parsed.get("latex") if isinstance(parsed.get("latex"), str) else previous.latex,
            confidence=float(parsed.get("confidence_score", previous.confidence))
            if isinstance(parsed.get("confidence_score", (float, int)))
            else previous.confidence,
        )

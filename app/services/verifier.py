from __future__ import annotations

import re

from sympy import SympifyError, nsimplify, simplify, sympify

from app.models.schemas import SandboxResult, VerificationResult


class VerifierService:
    def verify(self, llm_answer: str | None, sandbox_result: SandboxResult) -> VerificationResult:
        if not llm_answer:
            return VerificationResult(verified=False, reason="Missing LLM final answer")

        if not sandbox_result.execution_success:
            return VerificationResult(verified=False, reason=f"Sandbox failed: {sandbox_result.error}")

        llm_normalized = self._normalize(llm_answer)
        exec_normalized = self._normalize(sandbox_result.evaluated_result or "")

        if not llm_normalized or not exec_normalized:
            return VerificationResult(
                verified=False,
                reason="Insufficient outputs for deterministic comparison",
                normalized_llm_answer=llm_normalized,
                normalized_exec_answer=exec_normalized,
            )

        if self._equivalent(llm_normalized, exec_normalized):
            return VerificationResult(
                verified=True,
                reason="LLM answer matches symbolic evaluation",
                normalized_llm_answer=llm_normalized,
                normalized_exec_answer=exec_normalized,
            )

        return VerificationResult(
            verified=False,
            reason="Mismatch between LLM answer and symbolic evaluation",
            normalized_llm_answer=llm_normalized,
            normalized_exec_answer=exec_normalized,
        )

    @staticmethod
    def _normalize(text: str) -> str:
        cleaned = text.strip()
        cleaned = re.sub(r"\$+", "", cleaned)
        cleaned = re.sub(r"\s+", "", cleaned)
        return cleaned

    @staticmethod
    def _equivalent(left: str, right: str) -> bool:
        if left == right:
            return True

        try:
            l_expr = sympify(nsimplify(left))
            r_expr = sympify(nsimplify(right))
            return simplify(l_expr - r_expr) == 0
        except (SympifyError, TypeError, ValueError):
            return False

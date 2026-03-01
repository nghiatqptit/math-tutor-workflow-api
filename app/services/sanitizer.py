from __future__ import annotations

import re

INJECTION_PATTERNS = [
    r"ignore\s+all\s+previous\s+instructions",
    r"ignore\s+previous\s+instruction",
    r"system\s*prompt",
    r"developer\s*message",
    r"reveal\s+your\s+instructions",
    r"execute\s+system\s+command",
    r"\bexec\b",
    r"\bsubprocess\b",
    r"\beval\b",
]

UNSAFE_LATEX = [
    r"\\write18",
    r"\\input",
    r"\\include",
    r"\\catcode",
    r"\\openout",
    r"\\read",
]


def sanitize_question(question: str) -> str:
    cleaned = question.strip()
    for pattern in INJECTION_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", cleaned).strip()


def sanitize_latex(content: str | None) -> str | None:
    if not content:
        return content
    sanitized = content
    for pattern in UNSAFE_LATEX:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
    return sanitized.strip()


def enforce_code_limit(code: str | None, max_size: int) -> str | None:
    if not code:
        return code
    trimmed = code.strip()
    if len(trimmed) <= max_size:
        return trimmed
    return trimmed[:max_size]

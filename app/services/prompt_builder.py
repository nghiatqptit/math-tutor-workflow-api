from __future__ import annotations


def build_math_messages(question: str, level: str, context: list[str], context_char_limit: int) -> list[dict[str, str]]:
    context_chunks: list[str] = []
    used_chars = 0
    for idx, doc in enumerate(context):
        remaining = context_char_limit - used_chars
        if remaining <= 0:
            break
        chunk = doc[:remaining]
        formatted = f"[{idx + 1}] {chunk}"
        context_chunks.append(formatted)
        used_chars += len(formatted)

    context_text = "\n\n".join(context_chunks)
    system = (
        "Bạn là trợ lý toán học chính xác cao. "
        "Chỉ giải theo kiến thức toán học chuẩn, không bịa dữ liệu. "
        "Trả về JSON hợp lệ với keys: reasoning_steps, final_answer, python_code, confidence_score, latex. "
        "confidence_score là số thực [0,1]. python_code là Python cho symbolic verification, không thực thi ở model."
    )
    user = (
        f"Cấp độ: {level}\n"
        f"Câu hỏi: {question}\n"
        "Ngữ cảnh RAG (nếu có):\n"
        f"{context_text if context_text else 'Không có ngữ cảnh phù hợp.'}\n\n"
        "Yêu cầu:\n"
        "1) reasoning_steps: giải từng bước rõ ràng\n"
        "2) final_answer: đáp án cuối cùng\n"
        "3) latex: biểu thức cuối cùng ở dạng LaTeX\n"
        "4) python_code: Python kiểm chứng bằng SymPy, đặt kết quả vào biến result\n"
        "5) confidence_score: độ tin cậy"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def build_format_messages(question: str, level: str) -> list[dict[str, str]]:
    system = (
        "Bạn là trợ lý diễn giải tiếng Việt cho học sinh. "
        "Hãy tạo khung trình bày súc tích, dễ hiểu, có token {{REASONING_CORE}} để chèn lời giải chi tiết."
    )
    user = (
        f"Câu hỏi: {question}\n"
        f"Cấp độ: {level}\n"
        "Trả về khung tiếng Việt với bố cục:\n"
        "- Ý tưởng\n"
        "- Các bước giải\n"
        "- Kết luận\n"
        "Trong phần Các bước giải phải chứa đúng token {{REASONING_CORE}}."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def merge_template(template: str, reasoning: str, latex: str | None, code: str | None) -> str:
    merged = template.strip()
    if "{{REASONING_CORE}}" in merged:
        merged = merged.replace("{{REASONING_CORE}}", reasoning.strip())
    else:
        merged = f"{merged}\n\nCác bước giải:\n{reasoning.strip()}"

    if latex:
        merged += f"\n\nBiểu thức LaTeX:\n$$\n{latex.strip()}\n$$"

    if code:
        merged += f"\n\nMã Python tham khảo (không thực thi):\n```python\n{code.strip()}\n```"

    return merged

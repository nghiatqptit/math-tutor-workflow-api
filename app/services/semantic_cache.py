from __future__ import annotations

import math
import re
from collections import defaultdict

VECTOR_SIZE = 64


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[\w\d]+", text.lower())


def text_to_embedding(text: str) -> list[float]:
    bins: dict[int, float] = defaultdict(float)
    for token in _tokenize(text):
        slot = hash(token) % VECTOR_SIZE
        bins[slot] += 1.0

    vector = [bins[idx] for idx in range(VECTOR_SIZE)]
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return [0.0] * VECTOR_SIZE
    return [value / norm for value in vector]


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    return max(0.0, min(1.0, sum(a * b for a, b in zip(vec_a, vec_b))))

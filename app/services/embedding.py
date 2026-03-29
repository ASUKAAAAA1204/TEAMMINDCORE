from __future__ import annotations

import hashlib
import math
import re


WORD_PATTERN = re.compile(r"[A-Za-z0-9_]+")
CJK_PATTERN = re.compile(r"[\u4e00-\u9fff]")


class DeterministicEmbeddingService:
    def __init__(self, dimensions: int = 24) -> None:
        self.dimensions = dimensions

    def embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = self._tokenize(text)
        if not tokens:
            return vector
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=self.dimensions).digest()
            for index, byte in enumerate(digest):
                vector[index] += byte / 255.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def cosine_similarity(self, left: list[float], right: list[float]) -> float:
        if not left or not right:
            return 0.0
        return sum(a * b for a, b in zip(left, right))

    def keyword_overlap(self, query: str, text: str) -> float:
        query_tokens = set(self._tokenize(query))
        text_tokens = set(self._tokenize(text))
        if not query_tokens or not text_tokens:
            return 0.0
        common = len(query_tokens & text_tokens)
        return common / len(query_tokens)

    def _tokenize(self, text: str) -> list[str]:
        normalized = text.lower()
        word_tokens = WORD_PATTERN.findall(normalized)
        cjk_tokens = CJK_PATTERN.findall(normalized)
        if word_tokens or cjk_tokens:
            return [*word_tokens, *cjk_tokens]
        return [token for token in normalized.split() if token]


"""Fuzzy match of v0.1 free-text action prose to v1 action catalog ids."""

from __future__ import annotations

import re
from typing import Any, Optional


_STOPWORDS = {
    "a", "an", "the", "of", "to", "in", "on", "for", "with", "without",
    "and", "or", "by", "from", "into", "out", "as", "at", "is", "are", "be",
    "this", "that", "these", "those", "its", "their", "our", "any", "all",
    "no", "not", "may", "must", "should", "would", "can", "do", "does",
    "did", "will", "shall", "if", "when", "while", "than", "then", "so",
    "via", "per", "make", "made", "making",
}


def _normalize_token(token: str) -> str:
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def _tokenize(text: str) -> set[str]:
    return {
        _normalize_token(token)
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if token and token not in _STOPWORDS
    }


def fuzzy_action_match(prose: str, catalog: list[dict[str, Any]]) -> tuple[Optional[str], float]:
    """Return (action-id, score) for the best catalog match.

    Score is Jaccard similarity over token sets of (label + definition) versus
    (prose). Returns (None, score) if no catalog entry exceeds 0.18.
    """
    prose_tokens = _tokenize(prose)
    if not prose_tokens:
        return None, 0.0
    best_id: Optional[str] = None
    best_score = 0.0
    for entry in catalog:
        haystack = " ".join([
            entry.get("label", ""),
            entry.get("definition", ""),
            entry.get("id", "").replace("-", " "),
        ])
        catalog_tokens = _tokenize(haystack)
        if not catalog_tokens:
            continue
        intersection = prose_tokens & catalog_tokens
        union = prose_tokens | catalog_tokens
        score = len(intersection) / len(union)
        recall = len(intersection) / len(prose_tokens)
        score = 0.6 * score + 0.4 * recall
        if score > best_score:
            best_score = score
            best_id = entry.get("id")
    if best_score < 0.18:
        return None, best_score
    return best_id, best_score

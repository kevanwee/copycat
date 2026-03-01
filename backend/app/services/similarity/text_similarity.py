from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

from app.services.extraction.text import normalize_text, tokenize

ENTITY_PATTERN = re.compile(r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|[A-Z]{2,}|\d{4})\b")


@dataclass(slots=True)
class TextSimilarityResult:
    headline_score: float
    component_scores: dict[str, float]
    matched_passages: list[dict[str, Any]]
    normalized_original_length: int
    normalized_alleged_length: int


def _ngrams(tokens: list[str], n: int) -> set[tuple[str, ...]]:
    if len(tokens) < n:
        return set()
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def five_gram_jaccard(tokens_a: list[str], tokens_b: list[str]) -> float:
    a = _ngrams(tokens_a, 5)
    b = _ngrams(tokens_b, 5)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def lcs_ratio(tokens_a: list[str], tokens_b: list[str]) -> float:
    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0

    prev = [0] * (len(tokens_b) + 1)
    curr = [0] * (len(tokens_b) + 1)

    for i in range(1, len(tokens_a) + 1):
        for j in range(1, len(tokens_b) + 1):
            if tokens_a[i - 1] == tokens_b[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev, curr = curr, [0] * (len(tokens_b) + 1)

    lcs_len = prev[-1]
    return lcs_len / max(len(tokens_a), len(tokens_b))


def _feature_tokens(tokens: list[str]) -> list[str]:
    unigrams = tokens
    bigrams = [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens) - 1)] if len(tokens) > 1 else []
    return unigrams + bigrams


def _tfidf_vector(features: list[str], idf: dict[str, float]) -> dict[str, float]:
    if not features:
        return {}
    counts: dict[str, int] = {}
    for token in features:
        counts[token] = counts.get(token, 0) + 1

    total = len(features)
    vector: dict[str, float] = {}
    for token, count in counts.items():
        tf = count / total
        vector[token] = tf * idf[token]
    return vector


def tfidf_cosine_similarity(norm_a: str, norm_b: str) -> float:
    if not norm_a and not norm_b:
        return 1.0
    if not norm_a or not norm_b:
        return 0.0

    tokens_a = _feature_tokens(tokenize(norm_a))
    tokens_b = _feature_tokens(tokenize(norm_b))

    docs = [tokens_a, tokens_b]
    df: dict[str, int] = {}
    for doc in docs:
        for term in set(doc):
            df[term] = df.get(term, 0) + 1

    n_docs = len(docs)
    idf = {term: math.log((n_docs + 1) / (freq + 1)) + 1.0 for term, freq in df.items()}

    vec_a = _tfidf_vector(tokens_a, idf)
    vec_b = _tfidf_vector(tokens_b, idf)

    if not vec_a or not vec_b:
        return 0.0

    common = set(vec_a) & set(vec_b)
    dot = sum(vec_a[t] * vec_b[t] for t in common)
    norm_a_v = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b_v = math.sqrt(sum(v * v for v in vec_b.values()))
    if norm_a_v == 0.0 or norm_b_v == 0.0:
        return 0.0

    cosine = dot / (norm_a_v * norm_b_v)
    return max(0.0, min(1.0, cosine))


def named_entity_overlap(raw_a: str, raw_b: str) -> float:
    ents_a = {m.group(0).strip() for m in ENTITY_PATTERN.finditer(raw_a)}
    ents_b = {m.group(0).strip() for m in ENTITY_PATTERN.finditer(raw_b)}

    if not ents_a and not ents_b:
        return 1.0
    if not ents_a or not ents_b:
        return 0.0

    return len(ents_a & ents_b) / len(ents_a | ents_b)


def matched_passages(tokens_a: list[str], tokens_b: list[str], window: int = 12) -> list[dict[str, Any]]:
    if len(tokens_a) < window or len(tokens_b) < window:
        return []

    lookup: dict[tuple[str, ...], list[int]] = {}
    for i in range(len(tokens_a) - window + 1):
        key = tuple(tokens_a[i : i + window])
        lookup.setdefault(key, []).append(i)

    matches: list[dict[str, Any]] = []
    for j in range(len(tokens_b) - window + 1):
        key = tuple(tokens_b[j : j + window])
        original_positions = lookup.get(key)
        if not original_positions:
            continue
        for i in original_positions:
            snippet = " ".join(key)
            matches.append(
                {
                    "original_token_start": i,
                    "alleged_token_start": j,
                    "length_tokens": window,
                    "snippet": snippet,
                },
            )

    matches.sort(key=lambda x: (x["original_token_start"], x["alleged_token_start"], x["snippet"]))

    dedup: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    for item in matches:
        key = (item["original_token_start"], item["alleged_token_start"])
        if key in seen:
            continue
        seen.add(key)
        dedup.append(item)
        if len(dedup) >= 50:
            break

    return dedup


def compute_text_similarity(raw_original: str, raw_alleged: str) -> TextSimilarityResult:
    norm_a = normalize_text(raw_original)
    norm_b = normalize_text(raw_alleged)

    tokens_a = tokenize(norm_a)
    tokens_b = tokenize(norm_b)

    m1 = five_gram_jaccard(tokens_a, tokens_b)
    m2 = lcs_ratio(tokens_a, tokens_b)
    m3 = tfidf_cosine_similarity(norm_a, norm_b)
    m4 = named_entity_overlap(raw_original, raw_alleged)

    score = (0.35 * m1) + (0.25 * m2) + (0.30 * m3) + (0.10 * m4)
    score = max(0.0, min(1.0, float(score)))

    matches = matched_passages(tokens_a, tokens_b)

    return TextSimilarityResult(
        headline_score=score,
        component_scores={
            "M1_5gram_jaccard": round(m1, 6),
            "M2_lcs_ratio": round(m2, 6),
            "M3_tfidf_cosine": round(m3, 6),
            "M4_named_entity_overlap": round(m4, 6),
        },
        matched_passages=matches,
        normalized_original_length=len(tokens_a),
        normalized_alleged_length=len(tokens_b),
    )
"""Bounded deterministic text metrics and normalized-token evidence."""

import math
import re
from collections import Counter
from dataclasses import dataclass
from app.core.config import get_settings
from app.services.extraction.text import normalize_text, tokenize

ENTITY_PATTERN = re.compile(r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|[A-Z]{2,}|\d{4})\b")


@dataclass(slots=True)
class TextSimilarityResult:
    headline_score: float
    component_scores: dict
    matched_passages: list
    normalized_original_length: int
    normalized_alleged_length: int
    coverage: dict


def five_gram_jaccard(a, b):
    if not a or not b:
        return 0.0
    n = min(5, len(a), len(b))
    x = {tuple(a[i : i + n]) for i in range(len(a) - n + 1)}
    y = {tuple(b[i : i + n]) for i in range(len(b) - n + 1)}
    return len(x & y) / len(x | y)


def lcs_ratio(a, b):
    """Exact LCS via bit-vector dynamic programming; no quadratic Python loop."""
    if not a or not b:
        return 0.0
    if len(b) > len(a):
        a, b = b, a
    masks = {}
    for i, token in enumerate(b):
        masks[token] = masks.get(token, 0) | (1 << i)
    state = 0
    for token in a:
        x = masks.get(token, 0) | state
        state = x & ~(x - ((state << 1) | 1))
    return state.bit_count() / max(len(a), len(b))


def tfidf_cosine_similarity(norm_a, norm_b):
    docs = []
    for norm in (norm_a, norm_b):
        tokens = tokenize(norm)
        docs.append(Counter(tokens + [a + "_" + b for a, b in zip(tokens, tokens[1:])]))
    a, b = docs
    if not a or not b:
        return 0.0
    terms = sorted(a.keys() | b.keys())
    idf = {t: math.log(3 / (1 + int(t in a) + int(t in b))) + 1 for t in terms}
    dot = math.fsum(a[t] * b[t] * idf[t] ** 2 for t in terms)
    na = math.sqrt(math.fsum((a[t] * idf[t]) ** 2 for t in terms))
    nb = math.sqrt(math.fsum((b[t] * idf[t]) ** 2 for t in terms))
    return min(1.0, max(0.0, dot / (na * nb)))


def named_entity_overlap(raw_a, raw_b):
    a = set(ENTITY_PATTERN.findall(raw_a))
    b = set(ENTITY_PATTERN.findall(raw_b))
    return len(a & b) / len(a | b) if a or b else None


def matched_passages(a, b, window=5):
    if not a or not b:
        return []
    n = min(window, len(a), len(b))
    lookup = {}
    for i in range(len(a) - n + 1):
        positions = lookup.setdefault(tuple(a[i : i + n]), [])
        if len(positions) < 8:
            positions.append(i)
    matches, j = [], 0
    while j <= len(b) - n and len(matches) < 50:
        candidates = lookup.get(tuple(b[j : j + n]), [])
        best = None
        for i in candidates:
            length = n
            while (
                i + length < len(a)
                and j + length < len(b)
                and a[i + length] == b[j + length]
            ):
                length += 1
            if best is None or length > best[1]:
                best = (i, length)
        if best:
            i, length = best
            matches.append(
                dict(
                    original_token_start=i,
                    alleged_token_start=j,
                    length_tokens=length,
                    snippet=" ".join(a[i : i + min(length, 200)]),
                    snippet_truncated=length > 200,
                )
            )
            j += length
        else:
            j += 1
    return matches


def _coverage(matches, key, length):
    intervals = sorted((m[key], m[key] + m["length_tokens"]) for m in matches)
    covered, end = 0, 0
    for start, stop in intervals:
        covered += max(0, stop - max(start, end))
        end = max(end, stop)
    return round(covered / length, 6)


def compute_text_similarity(raw_original, raw_alleged):
    na, nb = normalize_text(raw_original), normalize_text(raw_alleged)
    a, b = tokenize(na), tokenize(nb)
    if not a or not b:
        raise ValueError(
            "No readable words in one or both files. Scanned PDFs need a text layer; OCR is not performed."
        )
    if max(len(a), len(b)) > get_settings().max_text_tokens:
        raise ValueError(
            f"Text exceeds {get_settings().max_text_tokens:,} tokens per file. Compare a smaller identified work or excerpt."
        )
    m1, m2, m3 = (
        five_gram_jaccard(a, b),
        lcs_ratio(a, b),
        tfidf_cosine_similarity(na, nb),
    )
    m4 = named_entity_overlap(raw_original, raw_alleged)
    score = (0.35 * m1 + 0.25 * m2 + 0.30 * m3 + 0.10 * (m4 or 0)) / (
        1 if m4 is not None else 0.90
    )
    matches = matched_passages(a, b)
    return TextSimilarityResult(
        round(min(1, max(0, score)), 6),
        {
            "M1_ngram_jaccard": round(m1, 6),
            "M2_lcs_ratio": round(m2, 6),
            "M3_tfidf_cosine": round(m3, 6),
            "M4_entity_overlap": round(m4, 6) if m4 is not None else None,
        },
        matches,
        len(a),
        len(b),
        dict(
            original=_coverage(matches, "original_token_start", len(a)),
            alleged=_coverage(matches, "alleged_token_start", len(b)),
            note="Lower-bound coverage of displayed exact normalized-token matches; up to 50 blocks and 8 candidate starts per phrase. Not legal substantiality.",
            ngram_size=min(5, len(a), len(b)),
            entity_metric_available=m4 is not None,
        ),
    )

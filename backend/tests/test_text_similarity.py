from __future__ import annotations

from app.services.similarity.text_similarity import compute_text_similarity



def test_text_similarity_deterministic() -> None:
    original = "The quick brown fox jumps over the lazy dog in Singapore."
    alleged = "The quick brown fox jumps over the lazy dog in Singapore."

    result1 = compute_text_similarity(original, alleged)
    result2 = compute_text_similarity(original, alleged)

    assert result1.headline_score == result2.headline_score
    assert result1.component_scores == result2.component_scores
    assert result1.headline_score > 0.99



def test_text_similarity_low_overlap() -> None:
    original = "alpha beta gamma delta epsilon"
    alleged = "carrot potato lettuce onion"

    result = compute_text_similarity(original, alleged)
    assert result.headline_score < 0.3
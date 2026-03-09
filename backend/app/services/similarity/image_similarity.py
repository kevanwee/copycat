from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ImageSimilarityResult:
    headline_score: float
    component_scores: dict[str, float]
    evidence: dict[str, Any]


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def _phash_similarity(path_a: str, path_b: str) -> float:
    """Perceptual hash Hamming similarity (I1). Range [0, 1]."""
    try:
        import imagehash
        from PIL import Image
    except ImportError:
        return 0.0

    hash_a = imagehash.phash(Image.open(path_a))
    hash_b = imagehash.phash(Image.open(path_b))
    distance = hash_a - hash_b          # Hamming distance (0 = identical)
    max_bits = hash_a.hash.size         # typically 64
    return max(0.0, 1.0 - distance / max_bits)


def _color_histogram_similarity(path_a: str, path_b: str) -> float:
    """Per-channel RGB histogram correlation (I2). Range [0, 1]."""
    try:
        import cv2
        import numpy as np
    except ImportError:
        return 0.0

    img_a = cv2.imread(path_a)
    img_b = cv2.imread(path_b)
    if img_a is None or img_b is None:
        return 0.0

    scores: list[float] = []
    for ch in range(3):
        hist_a = cv2.calcHist([img_a], [ch], None, [256], [0, 256])
        hist_b = cv2.calcHist([img_b], [ch], None, [256], [0, 256])
        cv2.normalize(hist_a, hist_a, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        cv2.normalize(hist_b, hist_b, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        corr = cv2.compareHist(hist_a, hist_b, cv2.HISTCMP_CORREL)
        scores.append(max(0.0, float(corr)))

    return sum(scores) / len(scores)


def _ssim_similarity(path_a: str, path_b: str, target_size: tuple[int, int] = (512, 512)) -> float:
    """Structural Similarity Index (I3). Range [0, 1]."""
    try:
        import cv2
        from skimage.metrics import structural_similarity as ssim
    except ImportError:
        return 0.0

    img_a = cv2.imread(path_a)
    img_b = cv2.imread(path_b)
    if img_a is None or img_b is None:
        return 0.0

    img_a = cv2.resize(img_a, target_size)
    img_b = cv2.resize(img_b, target_size)

    gray_a = cv2.cvtColor(img_a, cv2.COLOR_BGR2GRAY)
    gray_b = cv2.cvtColor(img_b, cv2.COLOR_BGR2GRAY)

    score, _ = ssim(gray_a, gray_b, full=True)
    return max(0.0, min(1.0, float(score)))


def _orb_match_ratio(path_a: str, path_b: str, max_distance: int = 64) -> float:
    """ORB keypoint match ratio (I4). Range [0, 1]."""
    try:
        import cv2
    except ImportError:
        return 0.0

    img_a = cv2.imread(path_a, cv2.IMREAD_GRAYSCALE)
    img_b = cv2.imread(path_b, cv2.IMREAD_GRAYSCALE)
    if img_a is None or img_b is None:
        return 0.0

    orb = cv2.ORB_create(nfeatures=1000)
    kp_a, des_a = orb.detectAndCompute(img_a, None)
    kp_b, des_b = orb.detectAndCompute(img_b, None)

    if des_a is None or des_b is None or len(kp_a) == 0 or len(kp_b) == 0:
        return 0.0

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = matcher.match(des_a, des_b)
    good = [m for m in matches if m.distance < max_distance]

    total_possible = min(len(kp_a), len(kp_b))
    if total_possible == 0:
        return 0.0

    return min(1.0, len(good) / total_possible)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_image_similarity(path_a: str, path_b: str) -> ImageSimilarityResult:
    """
    Compute image similarity using four complementary metrics.

    Weights:
        I1 pHash Hamming           35 %  — overall perceptual structure
        I2 Color Histogram Correl  20 %  — colour palette similarity
        I3 SSIM                    30 %  — structural / luminance match
        I4 ORB Feature Match Ratio 15 %  — local feature correspondence

    Formula:
        score = 0.35·I1 + 0.20·I2 + 0.30·I3 + 0.15·I4
    """
    i1 = _phash_similarity(path_a, path_b)
    i2 = _color_histogram_similarity(path_a, path_b)
    i3 = _ssim_similarity(path_a, path_b)
    i4 = _orb_match_ratio(path_a, path_b)

    score = 0.35 * i1 + 0.20 * i2 + 0.30 * i3 + 0.15 * i4
    score = max(0.0, min(1.0, float(score)))

    return ImageSimilarityResult(
        headline_score=score,
        component_scores={
            "I1_phash_similarity": round(i1, 6),
            "I2_color_histogram": round(i2, 6),
            "I3_ssim": round(i3, 6),
            "I4_orb_feature_match": round(i4, 6),
        },
        evidence={
            "paths": {"original": path_a, "alleged": path_b},
        },
    )

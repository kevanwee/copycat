from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.extraction.video import FrameSample
from app.services.similarity.text_similarity import compute_text_similarity


@dataclass(slots=True)
class VideoSimilarityResult:
    headline_score: float
    component_scores: dict[str, float]
    timeline_matches: list[dict[str, Any]]
    transcript_excerpt_matches: list[dict[str, Any]]


def _hamming_similarity(hash_a: str, hash_b: str) -> float:
    int_a = int(hash_a, 16)
    int_b = int(hash_b, 16)
    xor = int_a ^ int_b
    distance = xor.bit_count()
    max_bits = len(hash_a) * 4
    return 1.0 - (distance / max_bits)


def _monotonic_align(frames_a: list[FrameSample], frames_b: list[FrameSample]) -> list[tuple[FrameSample, FrameSample, float]]:
    if not frames_a or not frames_b:
        return []

    i = 0
    j = 0
    aligned: list[tuple[FrameSample, FrameSample, float]] = []

    lookahead = 8
    min_similarity = 0.55

    while i < len(frames_a) and j < len(frames_b):
        best = None
        best_j = -1
        for k in range(j, min(len(frames_b), j + lookahead + 1)):
            sim = _hamming_similarity(frames_a[i].phash, frames_b[k].phash)
            if best is None or sim > best:
                best = sim
                best_j = k

        if best is not None and best >= min_similarity:
            aligned.append((frames_a[i], frames_b[best_j], best))
            j = best_j + 1
            i += 1
        else:
            i += 1

    return aligned


def _compute_ssim_and_psnr(aligned: list[tuple[FrameSample, FrameSample, float]]) -> tuple[float, float]:
    try:
        import cv2
        from skimage.metrics import structural_similarity as ssim
    except Exception:
        return 0.0, 0.0

    if not aligned:
        return 0.0, 0.0

    ssim_values: list[float] = []
    psnr_values: list[float] = []

    for frame_a, frame_b, _ in aligned:
        img_a = cv2.imread(frame_a.path)
        img_b = cv2.imread(frame_b.path)
        if img_a is None or img_b is None:
            continue

        gray_a = cv2.cvtColor(img_a, cv2.COLOR_BGR2GRAY)
        gray_b = cv2.cvtColor(img_b, cv2.COLOR_BGR2GRAY)

        if gray_a.shape != gray_b.shape:
            gray_b = cv2.resize(gray_b, (gray_a.shape[1], gray_a.shape[0]))

        ssim_values.append(float(ssim(gray_a, gray_b)))
        psnr_values.append(float(cv2.PSNR(img_a, img_b)))

    if not ssim_values:
        return 0.0, 0.0

    avg_ssim = sum(ssim_values) / len(ssim_values)
    avg_psnr = sum(psnr_values) / len(psnr_values)
    normalized_psnr = max(0.0, min(1.0, avg_psnr / 50.0))
    return avg_ssim, normalized_psnr


def _timeline_payload(aligned: list[tuple[FrameSample, FrameSample, float]]) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for frame_a, frame_b, sim in aligned[:200]:
        payload.append(
            {
                "original_timestamp_sec": round(frame_a.timestamp_sec, 3),
                "alleged_timestamp_sec": round(frame_b.timestamp_sec, 3),
                "hash_similarity": round(sim, 6),
                "original_frame_path": frame_a.path,
                "alleged_frame_path": frame_b.path,
            },
        )
    return payload


def compute_video_similarity(
    original_frames: list[FrameSample],
    alleged_frames: list[FrameSample],
    original_transcript: str,
    alleged_transcript: str,
) -> VideoSimilarityResult:
    aligned = _monotonic_align(original_frames, alleged_frames)

    if aligned:
        avg_hash_similarity = sum(item[2] for item in aligned) / len(aligned)
    else:
        avg_hash_similarity = 0.0

    coverage = len(aligned) / max(len(original_frames), len(alleged_frames), 1)
    v1 = avg_hash_similarity * coverage

    v2, v3 = _compute_ssim_and_psnr(aligned)

    transcript_result = compute_text_similarity(original_transcript or "", alleged_transcript or "")
    v4 = transcript_result.headline_score if (original_transcript or alleged_transcript) else 0.0

    video_score = (0.50 * v1) + (0.20 * v2) + (0.30 * v4)
    video_score = max(0.0, min(1.0, float(video_score)))

    return VideoSimilarityResult(
        headline_score=video_score,
        component_scores={
            "V1_frame_phash_alignment": round(v1, 6),
            "V2_ssim": round(v2, 6),
            "V3_psnr_supporting": round(v3, 6),
            "V4_transcript_similarity": round(v4, 6),
        },
        timeline_matches=_timeline_payload(aligned),
        transcript_excerpt_matches=transcript_result.matched_passages[:50],
    )
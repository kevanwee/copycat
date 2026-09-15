from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings


@dataclass(slots=True)
class FrameSample:
    index: int
    timestamp_sec: float
    path: str
    phash: str


@dataclass(slots=True)
class VideoExtractionResult:
    source_path: str
    normalized_path: str
    duration_sec: float
    frames: list[FrameSample]
    transcript: str


settings = get_settings()


def probe_duration_seconds(path: str | Path) -> float:
    cmd = [
        settings.ffprobe_bin,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)
    payload = json.loads(result.stdout)
    duration = payload.get("format", {}).get("duration")
    return float(duration) if duration is not None else 0.0


def normalize_video(input_path: str | Path, output_path: str | Path) -> None:
    vf = "fps=2,scale=640:360:force_original_aspect_ratio=decrease,pad=640:360:(ow-iw)/2:(oh-ih)/2"
    cmd = [
        settings.ffmpeg_bin,
        "-y",
        "-i",
        str(input_path),
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-an",
        "-threads",
        "1",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=300)


def extract_frames_with_hashes(
    video_path: str | Path, out_dir: str | Path
) -> list[FrameSample]:
    try:
        import cv2
        import imagehash
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Video frame dependencies are unavailable") from exc

    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    capture = cv2.VideoCapture(str(video_path))
    fps = capture.get(cv2.CAP_PROP_FPS) or 2.0
    frames: list[FrameSample] = []
    idx = 0

    while True:
        ok, frame = capture.read()
        if not ok:
            break
        timestamp_sec = idx / fps if fps > 0 else float(idx) / 2.0
        frame_path = output_dir / f"frame_{idx:06d}.jpg"
        cv2.imwrite(str(frame_path), frame)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        phash = str(imagehash.phash(pil_img))

        frames.append(
            FrameSample(
                index=idx,
                timestamp_sec=float(timestamp_sec),
                path=str(frame_path),
                phash=phash,
            ),
        )
        idx += 1

    capture.release()
    return frames


def extract_video(path: str | Path, working_dir: str | Path) -> VideoExtractionResult:
    src = Path(path)
    work = Path(working_dir)
    work.mkdir(parents=True, exist_ok=True)

    normalized = work / f"normalized_{src.stem}.mp4"
    normalize_video(src, normalized)

    duration = probe_duration_seconds(normalized)
    frames_dir = work / "frames"
    frames = extract_frames_with_hashes(normalized, frames_dir)
    if not frames:
        raise ValueError("No decodable video frames were found.")
    # Model-based transcription is excluded from the deterministic visual workflow.
    transcript = ""

    return VideoExtractionResult(
        source_path=str(src),
        normalized_path=str(normalized),
        duration_sec=duration,
        frames=frames,
        transcript=transcript,
    )

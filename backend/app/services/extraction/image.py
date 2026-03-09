from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ImageExtractionResult:
    source_path: str
    normalized_path: str
    width: int
    height: int
    format: str
    mode: str


_NORMALIZE_SIZE = (1024, 1024)


def extract_image(path: str | Path, working_dir: str | Path | None = None) -> ImageExtractionResult:
    """Open an image, convert to RGB, save a normalised copy for comparison."""
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is required for image extraction. Install requirements-video.txt.") from exc

    source = Path(path)
    img = Image.open(source)
    fmt = img.format or source.suffix.lstrip(".").upper() or "UNKNOWN"
    orig_w, orig_h = img.size

    rgb = img.convert("RGB")
    rgb.thumbnail(_NORMALIZE_SIZE, Image.LANCZOS)

    if working_dir is not None:
        out_dir = Path(working_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        normalized_path = out_dir / f"{source.stem}_normalized.png"
    else:
        normalized_path = source.parent / f"{source.stem}_normalized.png"

    rgb.save(str(normalized_path), format="PNG")

    return ImageExtractionResult(
        source_path=str(source),
        normalized_path=str(normalized_path),
        width=orig_w,
        height=orig_h,
        format=fmt,
        mode=img.mode,
    )

import importlib.util
import shutil
from app.core.config import get_settings


def capabilities():
    s = get_settings()
    images = all(importlib.util.find_spec(n) is not None for n in ("PIL", "imagehash", "cv2", "skimage", "numpy"))
    video = images and bool(shutil.which(s.ffmpeg_bin)) and bool(shutil.which(s.ffprobe_bin))
    return {"media": {
        "text": {"available": True, "max_mb": s.max_text_mb, "extensions": [".txt", ".pdf", ".docx"], "note": "Readable UTF-8 text, text PDF or DOCX. No OCR. Up to 20,000 tokens per file."},
        "image": {"available": images, "max_mb": s.max_image_mb, "extensions": [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"], "note": "Still images only. Visual metrics require the image dependencies."},
        "video": {"available": video, "max_mb": s.max_video_mb, "extensions": [".mp4", ".mov", ".mkv", ".avi"], "note": f"Visual comparison only; audio is not assessed. Maximum {s.max_video_seconds} seconds. Requires FFmpeg and image dependencies."}},
        "retention_hours": s.retention_hours}

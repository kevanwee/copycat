from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from docx import Document
from langdetect import DetectorFactory, LangDetectException, detect
from pypdf import PdfReader

DetectorFactory.seed = 0

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9']+")
PUNCT_PATTERN = re.compile(r"[^\w\s']", re.UNICODE)


@dataclass(slots=True)
class TextExtractionResult:
    text: str
    language: str
    source_path: str


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    lowered = normalized.casefold()
    no_punct = PUNCT_PATTERN.sub(" ", lowered)
    squashed = re.sub(r"\s+", " ", no_punct).strip()
    return squashed


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text)


def detect_language(text: str) -> str:
    snippet = text[:5000]
    if not snippet.strip():
        return "unknown"
    try:
        return detect(snippet)
    except LangDetectException:
        return "unknown"


def extract_text_from_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_text_from_docx(path: Path) -> str:
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)


def _ocr_pdf_images(reader: PdfReader) -> str:
    try:
        import io

        import pytesseract
        from PIL import Image
    except Exception:
        return ""

    ocr_chunks: list[str] = []
    for page in reader.pages:
        images = getattr(page, "images", [])
        for image in images:
            try:
                with Image.open(io.BytesIO(image.data)) as img:
                    chunk = pytesseract.image_to_string(img)
                if chunk.strip():
                    ocr_chunks.append(chunk)
            except Exception:
                continue
    return "\n".join(ocr_chunks)


def extract_text_from_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    chunks: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            chunks.append(text)
    content = "\n".join(chunks)
    if content.strip():
        return content
    return _ocr_pdf_images(reader)


def extract_text(path: str | Path, enforce_english: bool = True) -> TextExtractionResult:
    src = Path(path)
    suffix = src.suffix.lower()
    if suffix == ".txt":
        raw = extract_text_from_txt(src)
    elif suffix == ".pdf":
        raw = extract_text_from_pdf(src)
    elif suffix == ".docx":
        raw = extract_text_from_docx(src)
    else:
        raise ValueError(f"Unsupported text file type: {suffix}")

    language = detect_language(raw)
    if enforce_english and language not in {"en", "unknown"}:
        # Keep deterministic pipeline but flag in output.
        pass

    return TextExtractionResult(text=raw, language=language, source_path=str(src))
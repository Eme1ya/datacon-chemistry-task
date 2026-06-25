"""PDF text and metadata utilities."""

from __future__ import annotations

import re
from pathlib import Path

import fitz


def get_pdf_metadata(pdf_path: Path) -> dict[str, str]:
    doc = fitz.open(pdf_path)
    meta = doc.metadata or {}
    doc.close()
    doi = ""
    title = meta.get("title", "")
    for candidate in (title, meta.get("subject", "")):
        m = re.search(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", candidate or "", re.I)
        if m:
            doi = m.group(0)
            break
    return {
        "doi": doi,
        "title": title,
    }


def extract_page_text(pdf_path: Path, page_index: int) -> str:
    doc = fitz.open(pdf_path)
    text = doc[page_index].get_text()
    doc.close()
    return text


def extract_all_text(pdf_path: Path) -> str:
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text


def cluster_words_by_line(pdf_path: Path, page_index: int, y_tolerance: float = 3.0) -> list[str]:
    doc = fitz.open(pdf_path)
    words = doc[page_index].get_text("words")
    doc.close()
    if not words:
        return []
    rows: dict[float, list[tuple[float, str]]] = {}
    for x0, y0, _x1, _y1, text, *_rest in words:
        y_key = round(y0 / y_tolerance) * y_tolerance
        rows.setdefault(y_key, []).append((x0, text))
    lines = []
    for y in sorted(rows.keys()):
        parts = [t for _x, t in sorted(rows[y], key=lambda item: item[0])]
        lines.append(" ".join(parts))
    return lines


def find_pdf_by_pattern(root: Path, pattern: str) -> Path:
    matches = [p for p in root.glob("*.pdf") if pattern.lower() in p.name.lower()]
    if not matches:
        raise FileNotFoundError(f"No PDF matching pattern: {pattern}")
    return matches[0]

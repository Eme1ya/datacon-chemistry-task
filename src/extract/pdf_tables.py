"""pdfplumber table extraction helpers."""

from __future__ import annotations

import re
from pathlib import Path

import pdfplumber


def extract_tables(pdf_path: Path) -> list[dict]:
    results = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            tables = page.extract_tables() or []
            for table_idx, table in enumerate(tables):
                results.append(
                    {
                        "page": page_idx + 1,
                        "table_index": table_idx + 1,
                        "rows": table,
                    }
                )
    return results


def flatten_table_cell(cell: str | None) -> str:
    if cell is None:
        return ""
    return re.sub(r"\s+", " ", str(cell).replace("\n", " ")).strip()


def table_to_text_rows(table: list[list]) -> list[str]:
    lines = []
    for row in table:
        cells = [flatten_table_cell(c) for c in row if flatten_table_cell(c)]
        if cells:
            lines.append(" | ".join(cells))
    return lines


def parse_multiline_data_block(text: str) -> list[str]:
    """Split merged table cells into logical rows."""
    text = text.replace("\n", " ")
    # compound rows often start with digit+optional letter
    parts = re.split(r"(?=(?:\b\d+[a-z]?(?:\([^)]*\))?\b))", text)
    return [p.strip() for p in parts if p.strip()]

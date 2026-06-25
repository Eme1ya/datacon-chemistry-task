"""Naltrexamine derivatives ACS paper parser."""

from __future__ import annotations

import re
from pathlib import Path

from src.extract.pdf_text import extract_all_text, find_pdf_by_pattern, get_pdf_metadata
from src.records import make_record

CONTROL_NAMES = {
    "NTX": "naltrexone",
    "β-FNA": "beta-FNA",
    "CTAP": "CTAP",
}

COMPOUND_LINE = re.compile(
    r"^(NTX|CTAP|.*FNA|\d{1,2}(?:\s*\([A-Z]+\))?)$"
)
VALUE_LINE = re.compile(r"^[\d.]+ \(\s*[\d.]+\)")


def _is_compound_line(line: str) -> bool:
    line = line.strip()
    if not COMPOUND_LINE.match(line):
        return False
    if "FNA" in line or line in {"NTX", "CTAP"}:
        return True
    m = re.match(r"^(\d{1,2})", line)
    if m:
        return 1 <= int(m.group(1)) <= 16
    return False


def _parse_table2_lines(lines: list[str]) -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not _is_compound_line(line):
            i += 1
            continue
        comp = line
        comp_id = re.sub(r"\s*\([A-Z]+\)", "", comp).strip()
        comp_name = ""
        if "FNA" in comp:
            comp_id = "beta-FNA"
            comp_name = "beta-FNA"
        elif "(NAP)" in comp:
            comp_id = "6"
            comp_name = "NAP"
        elif "(NAQ)" in comp:
            comp_id = "9"
            comp_name = "NAQ"
        elif comp_id in CONTROL_NAMES:
            comp_name = CONTROL_NAMES[comp_id]

        values: list[str] = []
        j = i + 1
        while j < len(lines) and len(values) < 3:
            vline = lines[j].strip()
            if _is_compound_line(vline):
                break
            m = VALUE_LINE.match(vline)
            if m:
                num = re.match(r"^([\d.]+)", vline)
                if num:
                    values.append(num.group(1))
            j += 1

        if len(values) == 3:
            rows.append((comp_id, comp_name, values[0], values[1], values[2]))
            i = j
        else:
            i += 1
    return rows


def extract_naltrexamine(root: Path) -> list[dict]:
    pdf = find_pdf_by_pattern(root, "naltrexamine")
    text = extract_all_text(pdf)
    meta = get_pdf_metadata(pdf)
    records: list[dict] = []

    start = text.find("Table 2.")
    end = text.find("Table 3.", start) if start >= 0 else -1
    block = text[start:end] if start >= 0 else text
    lines = block.splitlines()

    for comp_id, comp_name, mor, dor, kor in _parse_table2_lines(lines):
        base = {
            "source_pdf": pdf.name,
            "source_doi": meta["doi"],
            "source_page": "6",
            "source_table": "Table 2",
            "extraction_method": "pymupdf_text",
            "validation_status": "valid",
        }
        for target, val in [("MOR", mor), ("DOR", dor), ("KOR", kor)]:
            records.append(
                make_record(
                    **base,
                    compound_id=comp_id,
                    compound_name=comp_name,
                    endpoint_raw="Ki(nM)",
                    value_raw=val,
                    unit_raw="nM",
                    target_raw=target,
                    assay_type_raw="binding",
                )
            )
    return records

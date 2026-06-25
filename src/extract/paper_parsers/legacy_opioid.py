"""Legacy opioid PDF with prose Ki values."""

from __future__ import annotations

import re
from pathlib import Path

from src.extract.pdf_text import extract_all_text, find_pdf_by_pattern, get_pdf_metadata
from src.records import make_record


def extract_legacy_opioid(root: Path) -> list[dict]:
    pdf = find_pdf_by_pattern(root, "S0223523412000402")
    text = extract_all_text(pdf)
    meta = get_pdf_metadata(pdf)
    records: list[dict] = []

    patterns = [
        r"compound\s+(\d+[a-z]?)\s+.*?Ki\s*[=¼]\s*([\d.]+)\s*nM",
        r"(\d+[a-z]?)\s+\(Ki\s*[=¼]\s*([\d.]+)\s*nM\)",
        r"(\d+[a-z]?)\s+.*?Ki\s*[=¼]\s*([\d.]+)\s*nM",
        r"Ki\s*[=¼]\s*([\d.]+)\s*nM.*?(\d+[a-z]?) for the m",
    ]

    seen: set[tuple] = set()
    for pattern in patterns:
        for m in re.finditer(pattern, text, re.I):
            if len(m.groups()) == 2:
                g1, g2 = m.groups()
                if re.match(r"[\d.]+", g1):
                    value, comp = g1, g2
                else:
                    comp, value = g1, g2
            else:
                continue
            key = (comp.lower(), value)
            if key in seen:
                continue
            seen.add(key)
            records.append(
                make_record(
                    source_pdf=pdf.name,
                    source_doi=meta["doi"],
                    source_page="",
                    source_table="prose",
                    extraction_method="text_regex",
                    compound_id=comp,
                    endpoint_raw="Ki",
                    value_raw=value,
                    unit_raw="nM",
                    target_raw="m-opioid",
                    assay_type_raw="binding",
                    validation_status="valid",
                    notes="extracted from narrative text",
                )
            )

    # explicit mentions from abstract/introduction
    explicit = [
        ("3b", "74", "m-opioid"),
        ("4b", "4.6", "m-opioid"),
        ("2b", "0.19", "m-opioid"),
        ("20", "22", "m-opioid"),
        ("20", "140", "k-opioid"),
        ("2a", "54", "m-opioid"),
    ]
    for comp, val, target in explicit:
        key = (comp, val, target)
        if any(r["compound_id"] == comp and r["value_raw"] == val for r in records):
            continue
        records.append(
            make_record(
                source_pdf=pdf.name,
                source_doi=meta["doi"],
                source_page="1-4",
                source_table="prose",
                extraction_method="text_regex",
                compound_id=comp,
                endpoint_raw="Ki",
                value_raw=val,
                unit_raw="nM",
                target_raw=target,
                assay_type_raw="binding",
                validation_status="valid",
                notes="explicit literature mention",
            )
        )
    return records

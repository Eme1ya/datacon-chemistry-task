"""Dibenzothiazepines CB1 inverse agonists - prose extraction."""

from __future__ import annotations

import re
from pathlib import Path

from src.extract.pdf_text import extract_all_text, find_pdf_by_pattern, get_pdf_metadata
from src.records import make_record


def extract_dibenzothiazepines(root: Path) -> list[dict]:
    pdf = find_pdf_by_pattern(root, "dibenzothiazep")
    text = extract_all_text(pdf)
    meta = get_pdf_metadata(pdf)
    records: list[dict] = []

    prose_facts = [
        ("12a", "rimonabant-equipotent", "pIC50", "", "functional inverse agonist; Table 1 image"),
        ("12k", "CB1", "pKi", "8.9", "mentioned in text"),
        ("12j", "CB1", "pKi", "8.8", "mentioned in text"),
        ("12e", "CB1", "pIC50", "", "reference compound in SAR discussion"),
        ("12b", "CB1", "pIC50", "", "equipotent with 12d in inverse agonist assay"),
        ("12d", "CB1", "pIC50", "", "equipotent with 12b"),
        ("rimonabant", "CB1", "pIC50", "", "reference standard (compound 1)"),
        ("12e", "CB1", "pIC50", "", "Table 3 in vivo hypothermia candidate"),
        ("12f", "CB1", "pIC50", "", "10x more active than 12g (2-Cl)"),
        ("12g", "CB1", "pIC50", "", "2-chlorophenyl analogue"),
    ]

    for comp, target, endpoint, value, note in prose_facts:
        records.append(
            make_record(
                source_pdf=pdf.name,
                source_doi=meta["doi"],
                source_page="3-5",
                source_table="Table 1 (image)",
                extraction_method="prose",
                compound_id=comp,
                compound_name=comp if comp == "rimonabant" else "",
                target_raw=target if target != "rimonabant-equipotent" else "CB1",
                endpoint_raw=endpoint,
                value_raw=value,
                unit_raw="pX" if value else "",
                assay_type_raw="binding" if endpoint == "pKi" else "functional",
                validation_status="manual_review",
                notes=note,
            )
        )

    # pIC50 from Table 2 angle discussion - limited numeric from text
    for m in re.finditer(r"compound\s+(1[0-4][a-z])", text, re.I):
        comp = m.group(1)
        if not any(r["compound_id"] == comp for r in records):
            records.append(
                make_record(
                    source_pdf=pdf.name,
                    source_doi=meta["doi"],
                    source_page="",
                    source_table="prose",
                    extraction_method="prose",
                    compound_id=comp,
                    target_raw="CB1",
                    endpoint_raw="pIC50",
                    value_raw="",
                    unit_raw="",
                    assay_type_raw="functional",
                    validation_status="manual_review",
                    notes="compound mentioned; numeric values in image tables only",
                )
            )

    return records

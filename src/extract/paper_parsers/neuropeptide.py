"""Neuropeptide S receptor antagonists parser."""

from __future__ import annotations

import re
from pathlib import Path

from src.extract.pdf_text import cluster_words_by_line, find_pdf_by_pattern, get_pdf_metadata
from src.records import make_record


def extract_neuropeptide(root: Path) -> list[dict]:
    pdf = find_pdf_by_pattern(root, "neuropeptide")
    meta = get_pdf_metadata(pdf)
    records: list[dict] = []

    # Table 2 - selectivity profile (page 3, index 2)
    lines = cluster_words_by_line(pdf, 2)
    for line in lines:
        m = re.match(
            r"CHO.*?recombinant\s+(\S+)\s+(.+?)\s+([\d.]+)\s+(\d+)\s*\(?([\d.-]+)?\)?\s+([\d.]+)\s+(\d+)",
            line,
        )
        if not m:
            continue
        receptor_code, agonist, pec50_ctrl, emax_ctrl, _cl, pec50_test, emax_test = m.groups()
        base = {
            "source_pdf": pdf.name,
            "source_doi": meta["doi"],
            "source_page": "3",
            "source_table": "Table 2",
            "extraction_method": "coordinate_cluster",
            "compound_id": "[tBu-D-Gly5]NPS",
            "compound_name": "[tBu-D-Gly5]NPS",
            "cell_line": "CHO recombinant",
            "conditions": f"agonist={agonist}",
            "validation_status": "valid",
        }
        for suffix, endpoint, val, emax in [
            ("control", "pEC50", pec50_ctrl, emax_ctrl),
            ("test", "pEC50", pec50_test, emax_test),
        ]:
            records.append(
                make_record(
                    **base,
                    target_raw=receptor_code,
                    endpoint_raw=endpoint,
                    value_raw=val,
                    unit_raw="pX",
                    assay_type_raw=f"functional {suffix}",
                    notes=f"Emax={emax}%",
                )
            )

    # Table 1 - image; extract from prose
    prose_entries = [
        ("[tBu-D-Gly5]NPS", "NPSR", "pKB", "7.06", "antagonist vs 30 nM NPS"),
        ("[tBu-D-Gly5]NPS", "NPSR", "pKB", "6.78", "Schild analysis"),
        ("[D-Thr5]NPS", "NPSR", "pKB", "", "partial agonist R=0.08"),
        ("[D-allo-Thr5]NPS", "NPSR", "pKB", "", "antagonist R=0"),
        ("[D-Val5]NPS", "NPSR", "pKB", "", "reference peptide"),
        ("NPS", "NPSR", "pEC50", "8.32", "agonist reference"),
    ]
    for comp, target, endpoint, value, note in prose_entries:
        records.append(
            make_record(
                source_pdf=pdf.name,
                source_doi=meta["doi"],
                source_page="2-3",
                source_table="Table 1 (image)",
                extraction_method="prose",
                compound_id=comp,
                compound_name=comp,
                target_raw=target,
                endpoint_raw=endpoint,
                value_raw=value,
                unit_raw="pX" if value else "",
                assay_type_raw="functional",
                validation_status="manual_review",
                notes=f"Table 1 is image-only; {note}",
            )
        )

    return records

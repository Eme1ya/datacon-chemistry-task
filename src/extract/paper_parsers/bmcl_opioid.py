"""BMCL and related opioid PDF parsers."""

from __future__ import annotations

import re
from pathlib import Path

from src.extract.pdf_tables import extract_tables, flatten_table_cell
from src.extract.pdf_text import find_pdf_by_pattern, get_pdf_metadata
from src.records import make_record


def _base(source_pdf: Path, page: int, table: str, method: str) -> dict:
    meta = get_pdf_metadata(source_pdf)
    return {
        "source_pdf": source_pdf.name,
        "source_doi": meta["doi"],
        "source_page": page,
        "source_table": table,
        "extraction_method": method,
        "validation_status": "valid",
    }


def _add_measurement(
    records: list[dict],
    base: dict,
    compound_id: str,
    endpoint: str,
    target: str,
    value: str,
    unit: str = "nM",
    sem: str = "",
    qualifier: str = "",
    assay: str = "binding",
) -> None:
    records.append(
        make_record(
            **base,
            compound_id=compound_id,
            endpoint_raw=endpoint,
            value_raw=value,
            unit_raw=unit,
            sem_raw=sem,
            qualifier=qualifier,
            target_raw=target,
            assay_type_raw=assay,
        )
    )


def parse_08008214(root: Path) -> list[dict]:
    pdf = find_pdf_by_pattern(root, "S0960894X08008214")
    records: list[dict] = []
    tables = extract_tables(pdf)
    for tbl in tables:
        merged = " ".join(flatten_table_cell(c) for row in tbl["rows"] for c in row)
        if "Selectivity" not in merged and "Ki" not in merged:
            continue
        # 15a(levorphanol) 0.21±0.017 4.2±0.45 2.3±0.26
        for m in re.finditer(
            r"(\d+[a-z](?:\([^)]+\))?|[A-Z]+-\d+)\s+"
            r"([\d.]+)(?:[±+\-]\s*([\d.]+))?\s+"
            r"([\d.]+)(?:[±+\-]\s*([\d.]+))?\s+"
            r"([\d.]+)(?:[±+\-]\s*([\d.]+))?",
            merged,
        ):
            comp, ki_l, sem_l, ki_d, sem_d, ki_k, sem_k = m.groups()
            base = _base(pdf, tbl["page"], "Table 1", "pdfplumber_table")
            _add_measurement(records, base, comp, "Ki", "l", ki_l, sem=sem_l or "")
            _add_measurement(records, base, comp, "Ki", "d", ki_d, sem=sem_d or "")
            _add_measurement(records, base, comp, "Ki", "j", ki_k, sem=sem_k or "")
    return records


def _parse_compound_ki_rows(text: str, min_id: int, max_id: int) -> list[tuple[str, str, str]]:
    """Parse rows like '14 H 4 52' or '41 CONH2 F 3 85'."""
    rows: list[tuple[str, str, str]] = []
    for m in re.finditer(
        r"\b(\d{1,2})\s+"
        r"([A-Za-z0-9,\-]+(?:\s+[A-Za-z0-9,\-]+)?)\s+"
        r"(>?\d+(?:\.\d+)?|nd)\s+"
        r"(\d+(?:\.\d+)?|nd)?",
        text,
    ):
        comp_id, subst, nop_val, mop_val = m.groups()
        cid = int(comp_id)
        if cid < min_id or cid > max_id:
            continue
        label = f"{comp_id} ({subst.strip()})"
        rows.append((label, nop_val, mop_val or ""))
    return rows


def parse_09003679(root: Path) -> list[dict]:
    pdf = find_pdf_by_pattern(root, "S0960894X09003679")
    records: list[dict] = []
    tables = extract_tables(pdf)

    ranges = [(14, 25, 1), (41, 47, 2), (26, 32, 3), (33, 40, 4), (47, 50, 5)]

    for tbl in tables:
        merged = " ".join(flatten_table_cell(c) for row in tbl["rows"] for c in row)
        compact = merged.replace(" ", "")
        if "NOPKi" not in compact and "NOP Ki" not in merged:
            if "GTPcS" in merged and "EC50" in merged:
                for m in re.finditer(r"\b(1[5-7]|3[5-7]|4[1-6])\s+([\d.]+)\s+[\d()]+\s+([\d.]+)", merged):
                    comp, nop_ec50, mop_ec50 = m.groups()
                    base = _base(pdf, tbl["page"], "Table EC50", "pdfplumber_table")
                    _add_measurement(
                        records, base, comp, "IC50", "NOP", nop_ec50, assay="functional GTPgammaS"
                    )
                    _add_measurement(
                        records, base, comp, "IC50", "MOP", mop_ec50, assay="functional GTPgammaS"
                    )
            continue

        for min_id, max_id, table_num in ranges:
            parsed = _parse_compound_ki_rows(merged, min_id, max_id)
            if not parsed:
                continue
            for label, nop_val, mop_val in parsed:
                base = _base(pdf, tbl["page"], f"Table {table_num}", "pdfplumber_table")
                q = ">" if str(nop_val).startswith(">") else ""
                val = str(nop_val).lstrip(">")
                if val != "nd":
                    _add_measurement(records, base, label, "Ki", "NOP", val, qualifier=q)
                if mop_val and mop_val != "nd":
                    _add_measurement(records, base, label, "Ki", "MOP", mop_val)
    return records


def parse_09006222(root: Path) -> list[dict]:
    pdf = find_pdf_by_pattern(root, "S0960894X09006222")
    records: list[dict] = []
    tables = extract_tables(pdf)
    for tbl in tables:
        merged = " ".join(flatten_table_cell(c) for row in tbl["rows"] for c in row)
        if "Ki(nM)" not in merged:
            continue
        for m in re.finditer(
            r"\b(\d{1,2})\s+([\d.]+|c)\s+([\d.]+|c)\s+([\d.]+|c)\s+([\d.]+|c)?\s+([\d.]+|c)?\s+([\d.]+|c)?\s+([\d.]+|c)?",
            merged,
        ):
            comp, ki_j, ki_l, ki_d, ic50_j, ic50_l, ic50_d, _ = m.groups()
            if int(comp) > 22:
                continue
            base = _base(pdf, tbl["page"], "Table 1", "pdfplumber_table")
            if ki_j != "c":
                _add_measurement(records, base, comp, "Ki", "j", ki_j)
            if ki_l != "c":
                _add_measurement(records, base, comp, "Ki", "l", ki_l)
            if ki_d and ki_d != "c":
                _add_measurement(records, base, comp, "Ki", "d", ki_d)
            if ic50_j and ic50_j != "c":
                _add_measurement(
                    records, base, comp, "IC50", "j", ic50_j, assay="functional antagonism"
                )
            if ic50_l and ic50_l != "c":
                _add_measurement(
                    records, base, comp, "IC50", "l", ic50_l, assay="functional antagonism"
                )
    return records


def parse_09006258(root: Path) -> list[dict]:
    pdf = find_pdf_by_pattern(root, "S0960894X09006258")
    records: list[dict] = []
    tables = extract_tables(pdf)
    for tbl in tables:
        merged = " ".join(flatten_table_cell(c) for row in tbl["rows"] for c in row)
        if "ORL1" not in merged:
            continue
        # Simple rows: "13 28 23" or "19 H 4.0 4.7 16000"
        for m in re.finditer(
            r"\b(\d{1,2})\s+(?:[^\d]{0,20}\s+)?"
            r"([\d.]+|>1000)\s+"
            r"([\d.]+|>1000)?\s*"
            r"([\d.]+|>1000)?",
            merged,
        ):
            comp, v1, v2, v3 = m.groups()
            if int(comp) > 31:
                continue
            base = _base(pdf, tbl["page"], f"Table (p{tbl['page']})", "pdfplumber_table")
            if "Antagonism" in merged and "hERG" in merged:
                targets = [("ORL1", v1, "binding"), ("ORL1", v2, "functional antagonism"), ("hERG", v3, "binding")]
            elif "hERG" in merged:
                targets = [("ORL1", v1, "binding"), ("hERG", v2, "binding")]
            else:
                targets = [("ORL1", v1, "binding")]
            for target, val, assay in targets:
                if not val:
                    continue
                q = ">" if str(val).startswith(">") else ""
                val_clean = str(val).replace(">1000", "1000").lstrip(">")
                _add_measurement(
                    records,
                    base,
                    comp,
                    "IC50",
                    target,
                    val_clean,
                    qualifier=q,
                    assay=assay,
                )
    return records


def extract_all_bmcl(root: Path) -> list[dict]:
    records: list[dict] = []
    parsers = [parse_08008214, parse_09003679, parse_09006222, parse_09006258]
    for parser in parsers:
        try:
            records.extend(parser(root))
        except FileNotFoundError:
            continue
    return records

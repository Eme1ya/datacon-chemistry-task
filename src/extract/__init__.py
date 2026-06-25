"""Dispatch extraction from all PDF sources."""

from __future__ import annotations

from pathlib import Path

from src.extract.paper_parsers.bmcl_opioid import extract_all_bmcl
from src.extract.paper_parsers.dibenzothiazepines import extract_dibenzothiazepines
from src.extract.paper_parsers.legacy_opioid import extract_legacy_opioid
from src.extract.paper_parsers.naltrexamine import extract_naltrexamine
from src.extract.paper_parsers.neuropeptide import extract_neuropeptide


def extract_all_records(root: Path) -> list[dict]:
    records: list[dict] = []
    records.extend(extract_all_bmcl(root))
    records.extend(extract_legacy_opioid(root))
    records.extend(extract_naltrexamine(root))
    records.extend(extract_neuropeptide(root))
    records.extend(extract_dibenzothiazepines(root))
    return records

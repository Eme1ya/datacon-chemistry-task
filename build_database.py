#!/usr/bin/env python3
"""Build chemical bioactivity database from PDF sources."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.export import export_csv, export_qc_report
from src.extract import extract_all_records
from src.resolve.pubchem import resolve_records
from src.standardize import standardize_records
from src.validate.qc import run_qc_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Build bioactivity database from PDFs")
    parser.add_argument(
        "--no-pubchem",
        action="store_true",
        help="Skip PubChem API calls (use cache only)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data" / "chemical_database.csv",
        help="Output CSV path",
    )
    args = parser.parse_args()

    print("Extracting records from PDFs...")
    records = extract_all_records(ROOT)
    print(f"  Raw records extracted: {len(records)}")

    print("Standardizing units, targets, and assay types...")
    records = standardize_records(records)

    print("Resolving structures via PubChem...")
    records = resolve_records(records, use_network=not args.no_pubchem)

    print("Running QC pipeline...")
    records, dup_removed, qc = run_qc_pipeline(records)
    print(f"  Final records: {len(records)} (merged {dup_removed} duplicates)")

    export_csv(records, args.output)
    qc_path = args.output.parent / "qc_report.csv"
    export_qc_report(qc, qc_path)

    print(f"Database written to: {args.output}")
    print(f"QC report written to: {qc_path}")


if __name__ == "__main__":
    main()

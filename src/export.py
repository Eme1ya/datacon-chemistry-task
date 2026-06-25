"""Export database and QC report to CSV."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.records import RECORD_COLUMNS


def export_csv(records: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(records)
    for col in RECORD_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[RECORD_COLUMNS]
    df.to_csv(output_path, index=False, encoding="utf-8-sig")


def export_qc_report(qc_rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(qc_rows).to_csv(output_path, index=False, encoding="utf-8-sig")

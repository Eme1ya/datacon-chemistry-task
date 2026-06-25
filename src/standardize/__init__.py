"""Apply standardization to raw records."""

from __future__ import annotations

from typing import Any

from src.standardize.categories import standardize_assay_type
from src.standardize.targets import standardize_target
from src.standardize.units import standardize_measurement


def standardize_record(record: dict[str, Any]) -> dict[str, Any]:
    std = standardize_measurement(
        record.get("endpoint_raw", ""),
        record.get("value_raw", ""),
        record.get("unit_raw", ""),
        record.get("qualifier", ""),
    )
    record.update(std)
    record["target_std"] = standardize_target(record.get("target_raw", ""))
    record["assay_type_std"] = standardize_assay_type(
        record.get("assay_type_raw", ""),
        record.get("endpoint_raw", ""),
    )
    return record


def standardize_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [standardize_record(r) for r in records]

"""Quality control, deduplication, and conflict detection."""

from __future__ import annotations

import hashlib
from typing import Any

from src.records import RECORD_COLUMNS


def _fingerprint(record: dict[str, Any]) -> str:
    parts = [
        record.get("source_pdf", ""),
        record.get("compound_id", ""),
        record.get("compound_name", ""),
        record.get("target_raw", ""),
        record.get("endpoint_raw", ""),
        str(record.get("value_raw", "")),
        record.get("unit_raw", ""),
        record.get("assay_type_raw", ""),
    ]
    return hashlib.md5("|".join(parts).encode()).hexdigest()


def _entity_key(record: dict[str, Any]) -> tuple:
    return (
        record.get("source_pdf", ""),
        record.get("compound_id", ""),
        record.get("target_std", ""),
        record.get("endpoint_std", ""),
    )


def validate_record(record: dict[str, Any]) -> dict[str, Any]:
    status = record.get("validation_status") or "valid"
    notes = record.get("notes", "")

    if record.get("extraction_method") == "prose":
        status = "manual_review"
    if not record.get("value_raw") and not record.get("qualifier"):
        status = "suspicious"
        notes = (notes + "; missing value").strip("; ")
    if record.get("value_std") == "" and record.get("value_raw") and record.get("qualifier") not in {
        "nd",
        "na",
        "c",
        "e",
    }:
        status = "suspicious"
        notes = (notes + "; unit conversion failed").strip("; ")

    record["validation_status"] = status
    record["notes"] = notes
    return record


def deduplicate_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    seen: dict[str, dict] = {}
    removed = 0
    for record in records:
        fp = _fingerprint(record)
        if fp in seen:
            removed += 1
            existing = seen[fp]
            existing["notes"] = (existing.get("notes", "") + "; duplicate_merged").strip("; ")
            existing["duplicate_level"] = "1_exact"
            continue
        record["duplicate_level"] = ""
        seen[fp] = record
    return list(seen.values()), removed


def assign_conflict_groups(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple, list[dict]] = {}
    for record in records:
        if not record.get("value_std") and not record.get("value_raw"):
            continue
        key = _entity_key(record)
        groups.setdefault(key, []).append(record)

    conflict_id = 0
    for key, group in groups.items():
        if len(group) < 2:
            continue
        values = []
        for r in group:
            v = r.get("value_std")
            if v != "" and v is not None:
                try:
                    values.append(float(v))
                except (TypeError, ValueError):
                    pass
        if len(values) < 2:
            continue
        vmin, vmax = min(values), max(values)
        # Only flag true conflicts: same assay context, different values
        assays = {r.get("assay_type_std", "") for r in group}
        if len(assays) > 1:
            continue
        if vmax > 0 and vmin > 0 and vmax / vmin > 2.0:
            conflict_id += 1
            gid = f"conflict_{conflict_id:04d}"
            for r in group:
                r["conflict_group_id"] = gid
                if r.get("validation_status") == "valid":
                    r["validation_status"] = "suspicious"
                r["notes"] = (r.get("notes", "") + "; value conflict in group").strip("; ")
    return records


def build_qc_report(
    raw_count: int,
    records: list[dict[str, Any]],
    duplicates_removed: int,
) -> list[dict[str, str]]:
    issues: dict[str, int] = {}
    for r in records:
        if r.get("validation_status") == "suspicious":
            issues["suspicious"] = issues.get("suspicious", 0) + 1
        if r.get("validation_status") == "manual_review":
            issues["manual_review"] = issues.get("manual_review", 0) + 1
        if r.get("structure_resolution") == "unresolved":
            issues["unresolved_structure"] = issues.get("unresolved_structure", 0) + 1
        if "image" in r.get("source_table", "").lower():
            issues["image_table"] = issues.get("image_table", 0) + 1
        if not r.get("unit_raw") and r.get("value_raw"):
            issues["missing_unit"] = issues.get("missing_unit", 0) + 1

    conflicts = sum(1 for r in records if r.get("conflict_group_id"))

    summary = [
        {"metric": "raw_records", "value": str(raw_count)},
        {"metric": "final_records", "value": str(len(records))},
        {"metric": "duplicates_merged", "value": str(duplicates_removed)},
        {"metric": "conflict_groups", "value": str(conflicts)},
        {"metric": "manual_review", "value": str(issues.get("manual_review", 0))},
        {"metric": "suspicious", "value": str(issues.get("suspicious", 0))},
    ]
    for issue, count in sorted(issues.items()):
        summary.append({"metric": f"issue_{issue}", "value": str(count)})
    return summary


def run_qc_pipeline(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int, list[dict]]:
    raw_count = len(records)
    records = [validate_record(r) for r in records]
    records, dup_removed = deduplicate_records(records)
    records = assign_conflict_groups(records)
    qc = build_qc_report(raw_count, records, dup_removed)
    return records, dup_removed, qc

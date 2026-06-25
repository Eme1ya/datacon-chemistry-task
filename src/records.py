"""Shared record schema and helpers."""

from __future__ import annotations

import uuid
from copy import deepcopy
from typing import Any

RECORD_COLUMNS = [
    "record_id",
    "source_pdf",
    "source_doi",
    "source_page",
    "source_table",
    "extraction_method",
    "compound_id",
    "compound_name",
    "smiles_raw",
    "inchikey",
    "pubchem_cid",
    "structure_resolution",
    "endpoint_raw",
    "value_raw",
    "unit_raw",
    "sem_raw",
    "qualifier",
    "endpoint_std",
    "value_std",
    "unit_std",
    "conversion_note",
    "target_raw",
    "target_std",
    "assay_type_raw",
    "assay_type_std",
    "organism",
    "cell_line",
    "conditions",
    "validation_status",
    "duplicate_level",
    "conflict_group_id",
    "notes",
]


def make_record(**kwargs: Any) -> dict[str, Any]:
    record = {col: "" for col in RECORD_COLUMNS}
    record["record_id"] = kwargs.pop("record_id", str(uuid.uuid4()))
    record.update(kwargs)
    return record


def clone_record(record: dict[str, Any], **updates: Any) -> dict[str, Any]:
    new_record = deepcopy(record)
    new_record["record_id"] = str(uuid.uuid4())
    new_record.update(updates)
    return new_record

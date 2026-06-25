"""Assay type categorization."""

from __future__ import annotations

import re

ASSAY_PATTERNS = [
    (re.compile(r"binding|affinity|displacement|radioligand", re.I), "binding"),
    (re.compile(r"gtp|functional|antagonis|agonis|stimul|efficacy|emax|gtpγs|gtpcs", re.I), "functional"),
    (re.compile(r"selectiv|ratio", re.I), "selectivity"),
    (re.compile(r"hypotherm|anorexia|in vivo|behavior", re.I), "in_vivo"),
    (re.compile(r"microsomal|metab", re.I), "adme"),
]


def standardize_assay_type(assay_type_raw: str, endpoint_raw: str = "") -> str:
    text = f"{assay_type_raw} {endpoint_raw}".strip()
    if not text:
        return "binding"
    for pattern, label in ASSAY_PATTERNS:
        if pattern.search(text):
            return label
    return "binding"

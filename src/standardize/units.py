"""Unit and endpoint standardization."""

from __future__ import annotations

import math
import re
from typing import Any

CONCENTRATION_TO_NM = {
    "pm": 0.001,
    "nm": 1.0,
    "um": 1000.0,
    "µm": 1000.0,
    "μm": 1000.0,
    "mm": 1_000_000.0,
    "m": 1_000_000_000.0,
}

LOG_ENDPOINTS = {"pki", "pic50", "pec50", "pkb", "plogd", "plogp"}

ENDPOINT_ALIASES = {
    "ki": "Ki",
    "ic50": "IC50",
    "ec50": "EC50",
    "kd": "Kd",
    "pki": "pKi",
    "pic50": "pIC50",
    "pec50": "pEC50",
    "pkb": "pKB",
    "ad50": "AD50",
    "emax": "Emax",
    "gtpcs": "GTPgammaS",
}


def normalize_unit(unit: str) -> str:
    if not unit:
        return ""
    u = unit.strip().lower()
    u = u.replace("µ", "u").replace("μ", "u")
    u = re.sub(r"\s+", "", u)
    return u


def normalize_endpoint(endpoint: str) -> str:
    if not endpoint:
        return ""
    key = re.sub(r"[^a-z0-9]", "", endpoint.lower())
    return ENDPOINT_ALIASES.get(key, endpoint.strip())


def parse_value_token(token: str) -> tuple[str, str | float, str]:
    """Return qualifier, numeric value (or empty), remainder."""
    if not token or not str(token).strip():
        return "", "", ""
    text = str(token).strip()
    text = text.replace("¼", "").replace("=", " ").replace("−", "-")
    qualifier = ""
    if text.lower() in {"nd", "na", "n/a", "c", "e", "—", "-"}:
        return text.lower(), "", ""
    if text.startswith((">", "<", "≥", "≤")):
        qualifier = text[0]
        text = text[1:].strip()
    match = re.search(r"([\d.]+(?:e[+-]?\d+)?)", text.replace(",", ""))
    if not match:
        return qualifier, "", text
    try:
        value = float(match.group(1))
    except ValueError:
        return qualifier, "", text
    return qualifier, value, text


def standardize_measurement(
    endpoint_raw: str,
    value_raw: str | float,
    unit_raw: str,
    qualifier: str = "",
) -> dict[str, Any]:
    endpoint_std = normalize_endpoint(endpoint_raw)
    q, value, _ = parse_value_token(str(value_raw))
    if not qualifier:
        qualifier = q

    unit_norm = normalize_unit(unit_raw)
    result = {
        "endpoint_std": endpoint_std,
        "value_std": "",
        "unit_std": "",
        "conversion_note": "",
        "qualifier": qualifier,
    }

    if qualifier in {"nd", "na", "n/a", "c", "e"}:
        result["unit_std"] = unit_norm or unit_raw
        return result

    if value == "" or value is None:
        return result

    ep_key = re.sub(r"[^a-z0-9]", "", endpoint_std.lower())
    if ep_key in LOG_ENDPOINTS:
        result["value_std"] = value
        result["unit_std"] = "pX"
        result["conversion_note"] = "log scale preserved"
        return result

    if ep_key == "emax":
        result["value_std"] = value
        result["unit_std"] = "%"
        return result

    if unit_norm in CONCENTRATION_TO_NM:
        nm_value = value * CONCENTRATION_TO_NM[unit_norm]
        result["value_std"] = nm_value
        result["unit_std"] = "nM"
        if unit_norm == "nm":
            result["conversion_note"] = "already canonical"
        else:
            result["conversion_note"] = f"{unit_raw} × {CONCENTRATION_TO_NM[unit_norm]}"
        return result

    # unit embedded in endpoint name, e.g. Ki(nM)
    embedded = re.search(r"\((nm|um|µm|pm|mm)\)", endpoint_raw, re.I)
    if embedded and not unit_norm:
        unit_norm = normalize_unit(embedded.group(1))
        if unit_norm in CONCENTRATION_TO_NM:
            nm_value = value * CONCENTRATION_TO_NM[unit_norm]
            result["value_std"] = nm_value
            result["unit_std"] = "nM"
            result["conversion_note"] = f"unit from endpoint: {embedded.group(1)}"
            return result

    result["value_std"] = value
    result["unit_std"] = unit_raw or ""
    return result

"""Target name standardization."""

from __future__ import annotations

import json
import re
from pathlib import Path

_MAPPING: dict[str, str] | None = None


def _load_mapping() -> dict[str, str]:
    global _MAPPING
    if _MAPPING is None:
        path = Path(__file__).resolve().parents[2] / "config" / "target_mapping.json"
        with open(path, encoding="utf-8") as f:
            _MAPPING = {k.lower(): v for k, v in json.load(f).items()}
    return _MAPPING


def normalize_target_raw(text: str) -> str:
    if not text:
        return ""
    t = text.strip()
    t = t.replace("μ", "µ")
    return t


def standardize_target(target_raw: str) -> str:
    if not target_raw:
        return ""
    mapping = _load_mapping()
    raw = normalize_target_raw(target_raw)
    key = raw.lower()
    if key in mapping:
        return mapping[key]

    # strip receptor suffixes
    for suffix in (" receptor", " binding", "binding", "receptor"):
        if key.endswith(suffix):
            sub = key[: -len(suffix)].strip()
            if sub in mapping:
                return mapping[sub]

    # radioligand patterns
    ligand = re.search(r"\[3h\](\w+)", key, re.I)
    if ligand and ligand.group(1).upper() in mapping:
        return mapping[ligand.group(1).upper()]

    # Greek letter only
    if len(key) == 1 and key in mapping:
        return mapping[key]

    return raw.upper() if raw.isascii() and len(raw) <= 6 else raw

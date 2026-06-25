"""PubChem structure resolution with local cache."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

CACHE_PATH = Path(__file__).resolve().parents[2] / "data" / "pubchem_cache.json"
PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

NAME_ALIASES = {
    "NTX": "naltrexone",
    "naltrexone": "naltrexone",
    "rimonabant": "rimonabant",
    "CTAP": "CTAP",
    "DAMGO": "DAMGO",
    "levorphanol": "levorphanol",
    "butorphanol": "butorphanol",
    "naltrexamine": "naltrexamine",
}


def _load_cache() -> dict[str, Any]:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict[str, Any]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def _is_peptide(name: str) -> bool:
    return bool(re.search(r"\[.*\]|NPS|peptide", name, re.I))


def _http_get_json(url: str) -> dict[str, Any] | None:
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return None


def resolve_name(name: str, cache: dict[str, Any] | None = None) -> dict[str, str]:
    if not name:
        return {"structure_resolution": "unresolved", "pubchem_cid": "", "smiles_raw": "", "inchikey": ""}

    if _is_peptide(name):
        return {
            "structure_resolution": "peptide_sequence_only",
            "pubchem_cid": "",
            "smiles_raw": "",
            "inchikey": "",
        }

    lookup = NAME_ALIASES.get(name, name)
    if cache is None:
        cache = _load_cache()
    if lookup in cache:
        return cache[lookup]

    result = {
        "structure_resolution": "unresolved",
        "pubchem_cid": "",
        "smiles_raw": "",
        "inchikey": "",
    }
    encoded = urllib.parse.quote(lookup)
    url = f"{PUBCHEM_BASE}/compound/name/{encoded}/property/CanonicalSMILES,InChIKey/JSON"
    data = _http_get_json(url)
    if data:
        try:
            props = data["PropertyTable"]["Properties"][0]
            cid = str(props.get("CID", ""))
            result = {
                "structure_resolution": "pubchem_name",
                "pubchem_cid": cid,
                "smiles_raw": props.get("CanonicalSMILES", props.get("ConnectivitySMILES", "")),
                "inchikey": props.get("InChIKey", ""),
            }
        except (KeyError, IndexError):
            result["structure_resolution"] = "pubchem_error"
    else:
        result["structure_resolution"] = "pubchem_error"

    time.sleep(0.25)
    cache[lookup] = result
    _save_cache(cache)
    return result


def resolve_records(records: list[dict[str, Any]], use_network: bool = True) -> list[dict[str, Any]]:
    cache = _load_cache()
    for record in records:
        name = record.get("compound_name") or ""
        comp_id = record.get("compound_id") or ""
        lookup = name
        if not lookup and comp_id in NAME_ALIASES:
            lookup = NAME_ALIASES[comp_id]
        if not lookup:
            record.setdefault("structure_resolution", "unresolved")
            continue
        if not use_network:
            cached = cache.get(NAME_ALIASES.get(lookup, lookup), {})
            record.update(
                {
                    "structure_resolution": cached.get("structure_resolution", "unresolved"),
                    "pubchem_cid": cached.get("pubchem_cid", ""),
                    "smiles_raw": cached.get("smiles_raw", ""),
                    "inchikey": cached.get("inchikey", ""),
                }
            )
            continue
        resolved = resolve_name(lookup, cache)
        record.update(resolved)
    return records

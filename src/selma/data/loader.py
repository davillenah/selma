"""file: src/selma/data/loader.py

Loaders for bundled standard tables used by SELMA.

This module loads immutable technical data distributed inside the Python
package, validates the minimum expected structure, and returns a normalized
dictionary ready to be consumed by the engine.

Supported bundled resources
---------------------------
- wires.json
- factors.json
- constants.json

Current packaged standards
--------------------------
- aea90364

Design principles
-----------------
- Fail fast on missing or invalid packaged resources
- Keep validation structural and lightweight
- Avoid filesystem assumptions outside the installed package
- Be ready for future standards bundled under ``selma.data.<standard>``
"""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

__all__ = [
    "debug_print_loaded_tables",
    "load_json_resource",
    "load_standard_tables",
    "validate_constants_structure",
    "validate_factors_structure",
    "validate_wires_structure",
]

JsonDict = dict[str, Any]

_RESOURCE_FILENAMES: dict[str, str] = {
    "wires": "wires.json",
    "factors": "factors.json",
    "constants": "constants.json",
}


def load_json_resource(package: str, filename: str) -> JsonDict:
    resource = files(package).joinpath(filename)

    if not resource.is_file():
        raise FileNotFoundError(f"JSON resource not found: {package}:{filename}")

    raw_content = resource.read_text(encoding="utf-8")

    if not raw_content.strip():
        raise ValueError(f"Empty JSON resource: {package}:{filename}")

    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON format in resource: {package}:{filename}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object in resource: {package}:{filename}")

    return data


def _require_keys(obj: JsonDict, keys: set[str], context: str) -> None:
    missing = sorted(key for key in keys if key not in obj)
    if missing:
        raise ValueError(f"Missing keys in {context}: {', '.join(missing)}")


def validate_wires_structure(wires: JsonDict) -> None:
    _require_keys(wires, {"base_conditions", "materials"}, "wires root")

    if not isinstance(wires["materials"], dict):
        raise ValueError("wires.materials must be a dictionary")


def validate_factors_structure(factors: JsonDict) -> None:
    _require_keys(
        factors,
        {
            "grouped_general",
            "grouping_air",
            "soil_resistivity",
            "temperature_air",
            "temperature_soil",
        },
        "factors root",
    )


def validate_constants_structure(constants: JsonDict) -> None:
    _require_keys(constants, {"k_values"}, "constants root")

    if not isinstance(constants["k_values"], dict):
        raise ValueError("constants.k_values must be a dictionary")


def load_standard_tables(standard: str) -> JsonDict:
    if not isinstance(standard, str) or not standard.strip():
        raise ValueError("standard must be a non-empty string")

    standard_name = standard.strip().lower()
    package_name = f"selma.data.standards.{standard_name}"

    wires = load_json_resource(package_name, _RESOURCE_FILENAMES["wires"])
    factors = load_json_resource(package_name, _RESOURCE_FILENAMES["factors"])
    constants = load_json_resource(package_name, _RESOURCE_FILENAMES["constants"])

    validate_wires_structure(wires)
    validate_factors_structure(factors)
    validate_constants_structure(constants)

    return {
        "standard": standard_name,
        "resources": {
            "package": package_name,
            "wires": _RESOURCE_FILENAMES["wires"],
            "factors": _RESOURCE_FILENAMES["factors"],
            "constants": _RESOURCE_FILENAMES["constants"],
        },
        "wires": wires,
        "factors": factors,
        "constants": constants,
    }


def debug_print_loaded_tables(tables: JsonDict) -> None:
    standard = tables.get("standard", "-")
    print(f"\nStandard: {standard}")
    print("Loaded tables:")

    for name in ("wires", "factors", "constants"):
        keys = list(tables.get(name, {}).keys())
        print(f" - {name}: keys = {keys}")

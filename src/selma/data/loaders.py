"""
file: src/selma/data/loaders.py

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
    """
    Load a JSON resource bundled inside a package.

    Parameters
    ----------
    package:
        Fully qualified package name containing the JSON resource.
    filename:
        Resource filename to read.

    Returns
    -------
    dict[str, Any]
        Parsed JSON object.

    Raises
    ------
    FileNotFoundError
        If the resource does not exist in the package.
    ValueError
        If the resource is empty, invalid JSON, or its root is not an object.
    """
    resource = files(package).joinpath(filename)

    if not resource.is_file():
        msg = f"JSON resource not found: {package}:{filename}"
        raise FileNotFoundError(msg)

    try:
        raw_content = resource.read_text(encoding="utf-8")
    except FileNotFoundError:
        msg = f"JSON resource not found: {package}:{filename}"
        raise FileNotFoundError(msg) from None

    if not raw_content.strip():
        msg = f"Empty JSON resource: {package}:{filename}"
        raise ValueError(msg)

    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        msg = f"Invalid JSON format in resource: {package}:{filename}"
        raise ValueError(msg) from exc

    if not isinstance(data, dict):
        msg = f"JSON root must be an object in resource: {package}:{filename}"
        raise ValueError(msg)

    return data


def _require_keys(obj: JsonDict, keys: set[str], context: str) -> None:
    """
    Ensure that all required keys exist in a dictionary.

    Parameters
    ----------
    obj:
        Dictionary to validate.
    keys:
        Required keys.
    context:
        Human-readable validation context.
    """
    missing = sorted(key for key in keys if key not in obj)
    if missing:
        missing_list = ", ".join(missing)
        msg = f"Missing keys in {context}: {missing_list}"
        raise ValueError(msg)


def validate_wires_structure(wires: JsonDict) -> None:
    """
    Validate the minimum structure of the ampacity tables bundle.

    Parameters
    ----------
    wires:
        Parsed wires table object.
    """
    _require_keys(wires, {"base_conditions", "materials"}, "wires root")

    if not isinstance(wires["materials"], dict):
        msg = "wires.materials must be a dictionary"
        raise ValueError(msg)


def validate_factors_structure(factors: JsonDict) -> None:
    """
    Validate the minimum structure of the correction factors bundle.

    Parameters
    ----------
    factors:
        Parsed factors table object.
    """
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
    """
    Validate the minimum structure of the constants bundle.

    Parameters
    ----------
    constants:
        Parsed constants table object.
    """
    _require_keys(constants, {"k_values"}, "constants root")

    if not isinstance(constants["k_values"], dict):
        msg = "constants.k_values must be a dictionary"
        raise ValueError(msg)


def load_standard_tables(standard: str) -> JsonDict:
    """
    Load and validate all packaged technical tables for a given standard.

    Parameters
    ----------
    standard:
        Standard identifier, for example ``"aea90364"``.

    Returns
    -------
    dict[str, Any]
        Dictionary with the following keys:

        - ``standard``
        - ``resources``
        - ``wires``
        - ``factors``
        - ``constants``

    Raises
    ------
    ValueError
        If the standard identifier is invalid or if table structures are invalid.
    FileNotFoundError
        If one or more packaged resources are missing.
    """
    if not isinstance(standard, str) or not standard.strip():
        msg = "standard must be a non-empty string"
        raise ValueError(msg)

    standard_name = standard.strip().lower()
    package_name = f"selma.data.{standard_name}"

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
    """
    Print a compact summary of the loaded tables bundle.

    Parameters
    ----------
    tables:
        Tables bundle returned by ``load_standard_tables``.
    """
    standard = tables.get("standard", "-")
    print(f"\nStandard: {standard}")
    print("Loaded tables:")
    for name in ("wires", "factors", "constants"):
        keys = list(tables.get(name, {}).keys())
        print(f" - {name}: keys = {keys}")
"""file: src/selma/tables/lookup.py

Generic lookup utilities for SELMA tables.
"""

from __future__ import annotations

from typing import Any

# ✅ FIX IMPORT
from .constants import FLEXIBLE_CABLE_AMPACITY_FACTOR

# ============================================================
# CONSTANTS
# ============================================================

EMPTY_LOOKUP_TABLE_MSG = "Lookup table is empty"
EMPTY_GROUPED_LOOKUP_TABLE_MSG = "Grouped lookup table is empty"


# ============================================================
# GENERIC LOOKUPS
# ============================================================


def conservative_lookup(table: dict[str, Any], value: float) -> float:
    """Perform a conservative lookup independent of numeric key formatting."""
    table_float = {float(key): raw_value for key, raw_value in table.items()}
    keys = sorted(table_float)

    if not keys:
        raise ValueError(EMPTY_LOOKUP_TABLE_MSG)

    for key in keys:
        if value <= key:
            return float(table_float[key])

    return float(table_float[keys[-1]])


def conservative_lookup_nested(
    table: dict[str, Any],
    count: int,
    phase_type: str,
) -> float:
    """Perform a conservative lookup for nested numeric-keyed tables."""
    table_float = {float(key): raw_value for key, raw_value in table.items()}
    keys = sorted(table_float)

    if not keys:
        raise ValueError(EMPTY_GROUPED_LOOKUP_TABLE_MSG)

    for key in keys:
        if count <= key:
            return float(table_float[key][phase_type])

    return float(table_float[keys[-1]][phase_type])


def apply_ampacity_table_factor(iz_table_a: float) -> float:
    """Apply the ampacity correction required for flexible cables."""
    return iz_table_a * FLEXIBLE_CABLE_AMPACITY_FACTOR

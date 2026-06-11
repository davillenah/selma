"""
file: src/selma/tables/ampacity.py

Ampacity table lookup utilities.
"""

from __future__ import annotations

from typing import Any

# ✅ FIX IMPORT
from ..models.schemas import AmpacityRequest


# ============================================================
# TABLE LOOKUPS
# ============================================================

def find_ampacity_rows(
    wires_tables: dict[str, Any],
    req: AmpacityRequest,
) -> list[dict[str, Any]]:
    """Return ampacity rows for a material, insulation and method family."""

    materials = wires_tables.get("materials", {})
    mat_block = materials.get(req.material)

    if mat_block is None:
        raise KeyError(f"Missing material '{req.material}' in ampacity tables")

    ins_block = mat_block.get(req.insulation)
    if ins_block is None:
        raise KeyError(
            f"Missing insulation '{req.insulation}' for material '{req.material}'"
        )

    rows = ins_block.get(req.method_family)
    if rows is None:
        raise KeyError(
            f"Missing method family '{req.method_family}' for "
            f"{req.material}/{req.insulation}"
        )

    return rows


def extract_sections(rows: list[dict[str, Any]]) -> list[float]:
    """Extract sorted section values from ampacity rows."""
    return sorted(float(row["section_mm2"]) for row in rows)


def ampacity_at(
    rows: list[dict[str, Any]],
    section_mm2: float,
    column: str,
) -> float | None:
    """
    Return ampacity for a given section and method column.
    """

    for row in rows:
        if float(row["section_mm2"]) == float(section_mm2):
            if column not in row:
                raise KeyError(
                    f"Missing ampacity column '{column}' for section {section_mm2}"
                )

            value = row[column]
            return None if value is None else float(value)

    raise KeyError(f"Section {section_mm2} mm² not found in ampacity table")
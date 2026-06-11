"""
file: src/selma/selection/sections.py

Section selection logic for SELMA.
"""

from __future__ import annotations

from typing import Any

from ..models.schemas import (
    AmpacitySelectionInput,
    VoltageDropSelectionInput,
)
from ..tables.ampacity import ampacity_at
from ..voltage_drop.router import voltage_drop_pct
from ..protection.protection import select_protection_for_ampacity

JsonDict = dict[str, Any]


# ============================================================
# AMPACITY + PROTECTION
# ============================================================

def select_section_by_ampacity_and_protection(
    selection_input: AmpacitySelectionInput,
) -> tuple[float, float, float, float, Any]:
    """
    Select section based on ampacity and protection coordination.
    """

    for section in selection_input.sections:

        # mínimo reglamentario
        if section < selection_input.min_section_mm2:
            continue

        # Iz tabla
        iz_table = ampacity_at(
            selection_input.rows,
            section,
            selection_input.method_column,
        )

        if iz_table is None:
            continue

        iz_base = float(iz_table)

        # Iz corregida total
        iz_corr_total = (
            iz_base
            * selection_input.installation_factor
            * selection_input.parallels
            * selection_input.symmetry_factor
        )

        # condición térmica primaria
        if iz_corr_total < selection_input.ib_design:
            continue

        # ✅ SELECCIÓN REAL DE PROTECCIÓN (FIX CRÍTICO)
        protection = select_protection_for_ampacity(
            selection_input.ib_design,
            iz_corr_total,
        )

        # si no puedo coordinar protección → descarto sección
        if protection is None:
            continue

        return (
            float(section),
            float(iz_table),
            float(iz_base),
            float(iz_corr_total),
            protection,
        )

    return (None, None, None, None, None)


# ============================================================
# VOLTAGE DROP
# ============================================================

def select_section_by_voltage_drop(
    selection_input: VoltageDropSelectionInput,
) -> tuple[float, float]:
    """
    Select section based on voltage drop criteria.
    """

    # intento de menor sección que cumple
    for section in selection_input.sections:

        if section < selection_input.min_section_mm2:
            continue

        vdrop_pct = voltage_drop_pct(
            selection_input.electrical,
            selection_input.installation,
            selection_input.cable,
            selection_input.ib,
            selection_input.cos_phi,
            section,
        )

        if vdrop_pct <= selection_input.max_vdrop_pct:
            return float(section), float(vdrop_pct)

    # fallback: mayor sección disponible
    max_section = max(selection_input.sections)

    vdrop_pct = voltage_drop_pct(
        selection_input.electrical,
        selection_input.installation,
        selection_input.cable,
        selection_input.ib,
        selection_input.cos_phi,
        max_section,
    )

    return float(max_section), float(vdrop_pct)
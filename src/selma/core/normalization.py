"""
file: src/selma/core/normalization.py

Normalization utilities for electrical calculation inputs.
"""

from __future__ import annotations

from typing import Any

# ✅ FIX: imports corregidos al paquete selma
from ..models.schemas import MethodSelection
from ..core.load import is_single_motor_circuit
from ..sources.constants import (
    PE_PHASE_LIMIT_MM2,
    PE_FIXED_SECTION_MM2,
    PE_UPPER_LIMIT_MM2,
    MOTOR_SINGLE_FEEDER_FACTOR,
    LOW_VDROP_PURPOSES,
    LOW_VDROP_LIMIT_PCT,
    DEFAULT_VDROP_LIMIT_PCT,
)


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _get_purpose_type(purpose: Any) -> str:
    """Extract purpose type from legacy or structured format."""

    # New format
    if isinstance(purpose, dict):
        return str(purpose.get("type", "")).strip().lower()

    # Legacy format
    return str(purpose).strip().lower()


# ============================================================
# NORMALIZATION HELPERS
# ============================================================

def parse_installation_method(method_full: str) -> MethodSelection:
    if "-" not in method_full:
        raise ValueError(f"Invalid installation method format: '{method_full}'")

    family, column = method_full.split("-", 1)

    if not family or not column:
        raise ValueError(f"Invalid installation method format: '{method_full}'")

    return MethodSelection(family=family, column=column)


def format_section_string(section_mm2: float) -> str:
    if float(section_mm2).is_integer():
        return str(int(section_mm2))
    return str(section_mm2)


# ============================================================
# AEA RULES
# ============================================================

def get_minimum_phase_section_mm2(purpose: Any) -> float:
    """Return minimum conductor section based on circuit type (AEA)."""

    p_type = _get_purpose_type(purpose)

    if p_type == "lighting":
        return 1.5

    return 2.5


def get_max_voltage_drop_pct(purpose: Any) -> float:
    """Return maximum permissible voltage drop (AEA)."""

    p_type = _get_purpose_type(purpose)

    if p_type in LOW_VDROP_PURPOSES:
        return LOW_VDROP_LIMIT_PCT

    return DEFAULT_VDROP_LIMIT_PCT


# ============================================================
# PE SIZING
# ============================================================

def compute_pe_section_mm2(phase_section_mm2: float) -> float:
    """Compute PE section according to AEA rules."""

    if phase_section_mm2 <= PE_PHASE_LIMIT_MM2:
        return phase_section_mm2

    if phase_section_mm2 <= PE_UPPER_LIMIT_MM2:
        return PE_FIXED_SECTION_MM2

    return phase_section_mm2 / 2.0


# ============================================================
# DESIGN CURRENT
# ============================================================

def compute_design_current(
    circuit: dict[str, Any],
    ib: float,
    ampacity_margin: float,
) -> tuple[float, dict[str, Any]]:
    """Compute design current including AEA motor factors."""

    motor_factor = (
        MOTOR_SINGLE_FEEDER_FACTOR
        if is_single_motor_circuit(circuit)
        else 1.0
    )

    ib_regulatory = ib * motor_factor
    ib_design = ib_regulatory * ampacity_margin

    return ib_design, {
        "motor_single_feeder_factor": motor_factor,
        "Ib_regulatory": ib_regulatory,
        "Ib_design": ib_design,
    }
"""
file: src/selma/voltage_drop/gdc.py

Simplified voltage-drop calculation using the GDC method.

This module implements a configurable AEA-style gradient method:

    ΔU = (GDC · I · L) / S

Where:
- GDC = voltage-drop gradient constant [V·mm² / (A·m)]
- I   = current (A)
- L   = length (m)
- S   = conductor section (mm²)

Notes:
- Parallel conductors increase effective section.
- GDC can be overridden per circuit via the "cable" block.
- Defaults are temporary and should be replaced by table-driven values.
"""

from __future__ import annotations

from typing import Any


# ------------------------------------------------------------
# Temporary defaults (to be replaced by table-based values)
# ------------------------------------------------------------
GDC_DEFAULTS = {
    ("CU", "1PH"): 0.040,
    ("CU", "3PH"): 0.035,
    ("AL", "1PH"): 0.063,
    ("AL", "3PH"): 0.055,
}


def _normalize_phase(phase_type: str) -> str:
    """Normalize phase type to internal key."""
    return "3PH" if str(phase_type).strip().upper() == "3PH" else "1PH"


# ============================================================
# GDC RESOLUTION
# ============================================================

def resolve_gdc_value(
    cable: dict[str, Any],
    installation: dict[str, Any],
    phase_type: str,
) -> float:
    """Resolve GDC value.

    Resolution order:
    1. cable["gdc_value"]
    2. installation["gdc_value"] (legacy support)
    3. default constants
    """

    # -------------------------
    # 1. Explicit value (preferred)
    # -------------------------
    gdc_input = cable.get("gdc_value") if cable else None
    if gdc_input is not None and float(gdc_input) > 0.0:
        return float(gdc_input)

    # -------------------------
    # 2. Legacy support
    # -------------------------
    gdc_input = installation.get("gdc_value") if installation else None
    if gdc_input is not None and float(gdc_input) > 0.0:
        return float(gdc_input)

    # -------------------------
    # 3. Defaults
    # -------------------------
    material = str(installation["material"]).strip().upper()
    phase_key = _normalize_phase(phase_type)

    try:
        return float(GDC_DEFAULTS[(material, phase_key)])
    except KeyError as exc:
        msg = f"Unsupported GDC default for material={material}, phase={phase_key}"
        raise KeyError(msg) from exc


# ============================================================
# VOLTAGE DROP
# ============================================================

def voltage_drop_pct_gdc(
    electrical: dict[str, Any],
    installation: dict[str, Any],
    cable: dict[str, Any],
    current_a: float,
    section_mm2: float,
) -> float:
    """Calculate voltage drop percentage using GDC method."""

    length_m = float(electrical["length_m"])
    voltage_v = float(electrical["voltage_v"])
    phase_type = str(electrical["phase_type"]).strip().upper()
    parallels = int(electrical.get("parallels", 1))

    if section_mm2 <= 0.0:
        return 0.0  # defensive

    effective_section = float(section_mm2) * max(1, parallels)

    if effective_section <= 0.0:
        return 0.0  # defensive

    gdc_value = resolve_gdc_value(cable, installation, phase_type)

    # ΔU (volts)
    delta_u_v = (gdc_value * current_a * length_m) / effective_section

    # Percentage
    if voltage_v <= 0.0:
        return 0.0

    return (delta_u_v / voltage_v) * 100.0
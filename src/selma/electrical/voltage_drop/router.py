"""file: src/selma/voltage_drop/router.py

Voltage-drop method router.
"""

from __future__ import annotations

from typing import Any

# ✅ FIX IMPORTS
from ..voltage_drop.gdc import voltage_drop_pct_gdc
from ..voltage_drop.impedance import (
    voltage_drop_pct as voltage_drop_pct_impedance,
)

# ============================================================
# METHOD RESOLUTION
# ============================================================


def resolve_voltage_drop_method(cable: dict[str, Any]) -> str:
    method_raw = cable.get("voltage_drop_method", "GDC")
    method = str(method_raw).strip().upper()

    valid_methods = {"GDC", "IMPEDANCE"}

    if method not in valid_methods:
        raise ValueError(
            f"Unsupported voltage_drop_method '{method_raw}'. Use 'GDC' or 'IMPEDANCE'.",
        )

    return method


# ============================================================
# ROUTER
# ============================================================


def voltage_drop_pct(
    electrical: dict[str, Any],
    installation: dict[str, Any],
    cable: dict[str, Any],
    current_a: float,
    cos_phi: float,
    section_mm2: float,
) -> float:

    method = resolve_voltage_drop_method(cable)

    # --------------------------------------------------------
    # GDC method
    # --------------------------------------------------------
    if method == "GDC":
        return voltage_drop_pct_gdc(
            electrical=electrical,
            installation=installation,
            cable=cable,
            current_a=current_a,
            section_mm2=section_mm2,
        )

    # --------------------------------------------------------
    # IMPEDANCE method
    # --------------------------------------------------------
    return voltage_drop_pct_impedance(
        electrical=electrical,
        installation=installation,
        current_a=current_a,
        cos_phi=cos_phi,
        section_mm2=section_mm2,
    )

"""
file: src/selma/voltage_drop/impedance.py

Voltage drop calculation using full impedance model (R + X).
"""

from __future__ import annotations

from typing import Any
from math import sqrt

# ✅ FIX IMPORT
from ..sources.constants import (
    RHO_OHM_MM2_PER_M_20C,
    X_OHM_PER_M_DEFAULT,
)


# ============================================================
# VOLTAGE DROP
# ============================================================

def voltage_drop_pct(
    electrical: dict[str, Any],
    installation: dict[str, Any],
    current_a: float,
    cos_phi: float,
    section_mm2: float,
) -> float:
    """Calculate voltage drop percentage using full impedance model (R + X)."""

    # -------------------------
    # Inputs
    # -------------------------
    length_m = float(electrical["length_m"])
    voltage_v = float(electrical["voltage_v"])
    phase = str(electrical["phase_type"]).upper()
    parallels = int(electrical.get("parallels", 1))

    material = str(installation["material"]).upper()

    # -------------------------
    # Resistivity
    # -------------------------
    rho = RHO_OHM_MM2_PER_M_20C[material]

    # -------------------------
    # Effective section
    # -------------------------
    s_eff = float(section_mm2) * parallels

    if s_eff <= 0:
        return 0.0

    # -------------------------
    # Resistance
    # -------------------------
    r_ohm_per_m = rho / s_eff

    # -------------------------
    # Reactance
    # -------------------------
    x_input = electrical.get("reactance_ohm_per_m", None)

    if x_input is None or float(x_input) <= 0.0:
        x_input = installation.get("reactance_ohm_per_m", None)

    if x_input is not None and float(x_input) > 0.0:
        x_ohm_per_m = float(x_input)
    else:
        x_ohm_per_m = X_OHM_PER_M_DEFAULT.get(material, 0.00008)

    # -------------------------
    # Power factor decomposition
    # -------------------------
    cos_phi = max(0.0, min(1.0, float(cos_phi)))
    sin_phi = sqrt(max(0.0, 1.0 - cos_phi**2))

    # -------------------------
    # Equivalent impedance
    # -------------------------
    z_eq = (r_ohm_per_m * cos_phi) + (x_ohm_per_m * sin_phi)

    # -------------------------
    # System factor
    # -------------------------
    if phase == "3PH":
        k = sqrt(3.0)
    else:
        k = 2.0

    # -------------------------
    # Voltage drop
    # -------------------------
    dv = k * current_a * z_eq * length_m

    if voltage_v <= 0:
        return 0.0

    return (dv / voltage_v) * 100.0
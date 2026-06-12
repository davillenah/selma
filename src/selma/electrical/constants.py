"""file: engine/sources/constants.py

Centralized constants for the wire sizing engine.

This module defines all engineering constants, default values and
normalized parameters used across the engine.

Design principles
-----------------
- Single source of truth for engineering constants
- No business logic
- Explicit naming for readability
- Easy extensibility for future standards (IEC, NEC, etc.)
- Fully lint-compliant and type-safe where applicable

Scope
-----
Includes:
- Protection ratings
- Electrical material properties
- Installation/environment factors
- Short-circuit design constants
- Voltage drop limits
"""

from __future__ import annotations

# ============================================================
# PROTECTION DEVICES (COMMERCIAL SERIES)
# ============================================================

DEFAULT_PROTECTION_RATINGS_A: list[int] = [
    1,
    2,
    3,
    4,
    6,
    10,
    13,
    16,
    20,
    25,
    32,
    40,
    50,
    63,
    80,
    100,
    125,
    160,
    200,
    225,
    250,
    315,
    400,
    500,
    630,
    700,
    800,
    1000,
    1250,
    1600,
    2000,
    2500,
    3200,
    4000,
    5000,
    6300,
]

MCB_MAX_CURRENT_A: int = 63


# ============================================================
# ELECTRICAL PROPERTIES (AT 20°C)
# ============================================================

RHO_OHM_MM2_PER_M_20C: dict[str, float] = {
    "Cu": 0.017241,
    "Al": 0.028264,
}

X_OHM_PER_M_DEFAULT: dict[str, float] = {
    "Cu": 0.00008,
    "Al": 0.00008,
}


# ============================================================
# SOIL
# ============================================================

SOIL_THERMAL_RESISTIVITY_BY_TYPE: dict[str, float] = {
    "default": 1.0,
    "sand_dry": 2.5,
    "sand_wet": 0.9,
    "clay_dry": 1.3,
    "clay_wet": 0.7,
    "organic": 1.4,
    "peat_wet": 1.1,
    "gravel_dry": 2.2,
    "stabilized_backfill": 0.7,
}


# ============================================================
# PE
# ============================================================

PE_PHASE_LIMIT_MM2: float = 16.0
PE_FIXED_SECTION_MM2: float = 16.0
PE_UPPER_LIMIT_MM2: float = 35.0


# ============================================================
# SHORT CIRCUIT
# ============================================================

K_VALUES_BY_MATERIAL_AND_INSULATION: dict[str, dict[str, float]] = {
    "Cu": {
        "PVC": 115.0,
        "XLPE": 143.0,
    },
    "Al": {
        "PVC": 76.0,
        "XLPE": 94.0,
    },
}

SHORT_CIRCUIT_VOLTAGE_FACTOR: float = 1.05


# ============================================================
# AMPACITY
# ============================================================

FLEXIBLE_CABLE_AMPACITY_FACTOR: float = 0.95

MOTOR_SINGLE_FEEDER_FACTOR: float = 1.25


# ============================================================
# 🔥 VOLTAGE DROP (FIX REAL)
# ============================================================

# BEFORE ❌:
# LOW_VDROP_PURPOSES = {"lighting", "control", "signal"}

# ✅ AFTER (CORRECTO AEA):
LOW_VDROP_PURPOSES: set[str] = {
    "lighting",
    "outlet",
    "control",
    "signal",
}

LOW_VDROP_LIMIT_PCT: float = 3.0
DEFAULT_VDROP_LIMIT_PCT: float = 5.0


# ============================================================
# ERRORS
# ============================================================

EMPTY_LOOKUP_TABLE_MSG: str = "Empty lookup table"

EMPTY_GROUPED_LOOKUP_TABLE_MSG: str = "Empty grouped lookup table"

NO_VALID_SHORT_CIRCUIT_SECTION_MSG: str = (
    "No valid numeric sections available for short-circuit verification"
)

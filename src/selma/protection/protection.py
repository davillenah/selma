"""
file: src/selma/protection/protection.py

Protección eléctrica – selección y coordinación AEA.
"""

from __future__ import annotations

from typing import Any

# ✅ FIX IMPORTS (ANTES: engine...)
from ..models.schemas import ProtectionSelection
from ..sources.constants import (
    DEFAULT_PROTECTION_RATINGS_A,
    MCB_MAX_CURRENT_A,
)


# ============================================================
# HELPERS
# ============================================================

def _normalize_purpose(purpose: Any) -> tuple[str, str | None]:
    if isinstance(purpose, dict):
        p_type = str(purpose.get("type", "")).lower()
        p_sub = purpose.get("subtype")
        return p_type, (str(p_sub).lower() if p_sub else None)

    return str(purpose).lower(), None


# ============================================================
# DEVICE
# ============================================================

def classify_protection_device(in_a: int) -> tuple[str, str, str]:
    if in_a <= MCB_MAX_CURRENT_A:
        return "MCB", "IEC 60898-1", "C"
    return "MCCB", "IEC 60947-2", "TM"


def compute_i2_from_in(in_a: int) -> float:
    return 1.45 * in_a


# ============================================================
# GENERIC AMPACITY SELECTION
# ============================================================

def candidate_protection_devices(ib_design: float):
    candidates = []

    for rating in DEFAULT_PROTECTION_RATINGS_A:
        if rating < ib_design:
            continue

        device_type, standard, curve = classify_protection_device(rating)
        i2 = compute_i2_from_in(rating)

        candidates.append(
            ProtectionSelection(
                in_a=rating,
                i2_a=i2,
                device_type=device_type,
                standard=standard,
                curve=curve,
            )
        )

    return candidates


def select_protection_for_ampacity(
    ib_design: float,
    iz_corrected_total: float,
):
    for c in candidate_protection_devices(ib_design):

        if c.in_a > iz_corrected_total:
            continue

        if c.in_a < ib_design:
            continue

        if c.i2_a > (1.45 * iz_corrected_total):
            continue

        return c

    return None


# ============================================================
# AEA DEFAULTS
# ============================================================

def _select_aea_nominal_rating_and_curve(
    p_type: str,
    p_sub: str | None,
):
    if p_type == "lighting":
        return 10, "B"

    if p_type == "outlet":
        if p_sub == "tue":
            return 20, "C"
        return 16, "C"

    if p_type == "power":
        return 16, "C"

    if p_type == "motor":
        return 20, "C"

    if p_type == "board":
        return 20, "C"

    if p_type == "control":
        return 10, "C"

    if p_type == "signal":
        return 6, "C"

    return 16, "C"


# ============================================================
# ✅ AEA SELECTION
# ============================================================

def select_protection_aea(
    circuit: dict[str, Any],
    ib_design: float,
    iz_corrected_total: float,
):
    p_type, p_sub = _normalize_purpose(circuit.get("purpose"))

    rating, curve = _select_aea_nominal_rating_and_curve(p_type, p_sub)

    device_type, standard, _ = classify_protection_device(rating)
    i2 = compute_i2_from_in(rating)

    # 🔥 CRÍTICO: evitar In > Iz
    if rating > iz_corrected_total:
        return select_protection_for_ampacity(
            ib_design,
            iz_corrected_total,
        )

    # coordinación
    in_ok = ib_design <= rating
    i2_ok = i2 <= (1.45 * iz_corrected_total)

    if not (in_ok and i2_ok):
        return select_protection_for_ampacity(
            ib_design,
            iz_corrected_total,
        )

    return ProtectionSelection(
        in_a=rating,
        i2_a=i2,
        device_type=device_type,
        standard=standard,
        curve=curve,
    )
"""file: src/selma/core/load.py

AGREGAR COMENTARIO
"""

from math import sqrt
from typing import Any

# ============================================================
# LOAD / CURRENT RESOLUTION
# ============================================================


def load_to_kva_and_ib(
    electrical: dict[str, Any],
    cos_phi: float,
) -> tuple[float, float, dict[str, Any]]:
    """Resolve electrical load into apparent power and project current.

    Accepted units
    --------------
    A, W, kW, MW, VA, kVA, MVA, HP

    Returns
    -------
    tuple[float, float, dict[str, Any]]
        Apparent power in kVA, project current in A, and a trace fragment.

    """
    phase = electrical["phase_type"]
    voltage_v = float(electrical["voltage_v"])
    load = electrical["load"]

    value = float(load["value"])
    unit = str(load["unit"]).strip()

    if unit == "A":
        ib = value
        s_kva = sqrt(3.0) * voltage_v * ib / 1000.0 if phase == "3PH" else voltage_v * ib / 1000.0
        return (
            s_kva,
            ib,
            {
                "load_value": value,
                "load_unit": unit,
                "interpreted_as": "current",
            },
        )

    if unit == "VA":
        s_kva = value / 1000.0
    elif unit == "kVA":
        s_kva = value
    elif unit == "MVA":
        s_kva = value * 1000.0
    elif unit == "W":
        s_kva = (value / 1000.0) / cos_phi
    elif unit == "kW":
        s_kva = value / cos_phi
    elif unit == "MW":
        s_kva = (value * 1000.0) / cos_phi
    elif unit == "HP":
        s_kva = ((value * 746.0) / 1000.0) / cos_phi
    else:
        msg = f"Unsupported load unit '{unit}'"
        raise ValueError(msg)

    ib = s_kva * 1000.0 / (sqrt(3.0) * voltage_v) if phase == "3PH" else s_kva * 1000.0 / voltage_v

    return (
        s_kva,
        ib,
        {
            "load_value": value,
            "load_unit": unit,
            "interpreted_as": "power",
        },
    )


def power_to_kva_and_ib(
    electrical: dict[str, Any],
    cos_phi: float,
) -> tuple[float, float, dict[str, Any]]:
    """Backward-compatible alias for legacy helpers and tests."""
    return load_to_kva_and_ib(electrical, cos_phi)


def is_single_motor_circuit(circuit: dict[str, Any]) -> bool:
    """Return whether the circuit is a single-motor feeder."""
    return str(circuit.get("purpose", "")).strip().lower() == "motor"

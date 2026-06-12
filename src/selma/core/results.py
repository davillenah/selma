"""file: src/selma/core/results.py

Result builders and formatting helpers for the wire sizing engine.

This module is responsible for:

- Building standardized output dictionaries (OK / FAILED)
- Providing consistent formatting for:
    * Cable description (phase + PE conductor)
    * Protection devices (MCB / MCCB)

Design principles
-----------------
- Stateless helpers
- Deterministic formatting
- No business logic (only presentation layer)

AEA alignment
-------------
- Cable always includes PE conductor
- Section formatting follows engineering convention (2x4mm², not 2 x 4 mm²)
- Protection format follows: "MCB - 2x16A - Curva C"
"""

from typing import Any

# ============================================================
# INTERNAL HELPERS
# ============================================================


def _fmt_mm2(value: float) -> str:
    """Format section value without trailing decimals."""
    if float(value).is_integer():
        return str(int(value))
    return str(value)


def _pe_section_mm2(phase_section_mm2: float) -> float:
    """Determine PE section according to AEA simplified rule."""
    if phase_section_mm2 <= 16:
        return phase_section_mm2
    if phase_section_mm2 <= 35:
        return 16
    return phase_section_mm2 / 2


# ============================================================
# FORMATTERS
# ============================================================


def format_cable(
    circuit: dict[str, Any],
    section_mm2: float,
) -> tuple[str, float]:
    """Build cable description including PE conductor."""
    installation = circuit.get("installation", {})
    electrical = circuit.get("electrical", {})

    insulation = str(installation.get("insulation", ""))
    material = str(installation.get("material", ""))
    phase_type = str(electrical.get("phase_type", "1PH")).upper()

    s = _fmt_mm2(section_mm2)
    pe_section = _pe_section_mm2(section_mm2)
    pe = _fmt_mm2(pe_section)

    if phase_type == "3PH":
        cable_str = f"{insulation} 3x{s}mm² + PE{pe}mm² {material}"
    else:
        cable_str = f"{insulation} 2x{s}mm² + PE{pe}mm² {material}"

    return cable_str, pe_section


def format_protection(
    protection: Any,
    circuit: dict[str, Any],
) -> str:
    """Format protection output string."""
    if protection is None:
        return "N/A"

    electrical = circuit.get("electrical", {})
    phase_type = str(electrical.get("phase_type", "1PH")).upper()

    poles = 2 if phase_type == "1PH" else 3

    return f"{protection.device_type} - {poles}x{protection.in_a}A - Curva {protection.curve}"


# ============================================================
# RESULT HELPERS
# ============================================================


def ok_result(
    base: dict[str, Any],
    trace: dict[str, Any],
    checks: dict[str, bool],
    warning: str | None = None,
    warning_code: str | None = None,
) -> dict[str, Any]:
    """Build a successful engine result dictionary."""
    result = dict(base)
    result["status"] = "OK"
    result["checks"] = checks
    result["trace"] = trace

    if warning:
        result["warning"] = warning
        result["warning_code"] = warning_code or "WARNING"

    return result


def failed_result(
    base: dict[str, Any],
    trace: dict[str, Any],
    error: str,
    error_code: str,
) -> dict[str, Any]:
    """Build a failed engine result dictionary."""
    result = dict(base)
    result["status"] = "FAILED"
    result["checks"] = {
        "ampacity": False,
        "protection_coordination": False,
        "voltage_drop": False,
        "short_circuit": False,
        "minimum_section": False,
    }
    result["trace"] = trace
    result["error"] = error
    result["error_code"] = error_code
    return result


def base_output_fields(
    circuit: dict[str, Any],
    electrical: dict[str, Any],
) -> dict[str, Any]:
    """Build the base output structure shared by all results."""
    return {
        "tag": circuit.get("tag", "?"),
        "origin": circuit.get("origin", "-"),
        "destination": circuit.get("destination", "-"),
        "purpose": circuit.get("purpose", "-"),
        "length_m": float(electrical.get("length_m", 0.0)),
        "current_a": 0.0,
        "cable_section": "N/A",
        "pe_section_mm2": 0.0,
        "protection": "N/A",
        "protection_type": "-",
        "protection_standard": "-",
        "protection_curve": "-",
        "voltage_drop_pct": 0.0,
    }

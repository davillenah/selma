"""
file: src/selma/factors/calculator.py

Factor calculation utilities for SELMA.
"""

from __future__ import annotations

from typing import Any

# ✅ IMPORTS CORREGIDOS (ANTES: engine...)
from ..core.normalization import parse_installation_method
from ..tables.lookup import conservative_lookup, conservative_lookup_nested
from ..sources.constants import SOIL_THERMAL_RESISTIVITY_BY_TYPE


# ============================================================
# FACTOR RESOLUTION
# ============================================================

def get_installation_temperature_c(installation: dict[str, Any]) -> float:
    """Return the installation temperature."""
    if "installation_temp_c" in installation:
        return float(installation["installation_temp_c"])
    if "temperature_c" in installation:
        return float(installation["temperature_c"])
    if "ambient_temp_c" in installation:
        return float(installation["ambient_temp_c"])

    raise KeyError("Missing installation temperature. Use 'installation_temp_c'.")


def get_soil_thermal_resistivity(installation: dict[str, Any]) -> float:
    """Resolve soil thermal resistivity."""
    soil_type = str(installation.get("soil_type", "default")).strip().lower()

    if soil_type not in SOIL_THERMAL_RESISTIVITY_BY_TYPE:
        raise KeyError(f"Unsupported soil_type '{installation.get('soil_type')}'")

    return float(SOIL_THERMAL_RESISTIVITY_BY_TYPE[soil_type])


def get_temperature_factor(
    _wires: dict[str, Any],
    factors: dict[str, Any],
    installation: dict[str, Any],
) -> tuple[float, dict[str, Any]]:
    insulation = installation["insulation"]
    method = parse_installation_method(installation["installation_method"])
    temperature_c = get_installation_temperature_c(installation)

    if method.family in {"D1", "D2"}:
        factor = conservative_lookup(
            factors["temperature_soil"][insulation],
            temperature_c,
        )
        return factor, {
            "temperature_factor_source": "temperature_soil",
            "temperature_c": temperature_c,
            "temperature_context": "soil",
        }

    factor = conservative_lookup(
        factors["temperature_air"][insulation],
        temperature_c,
    )
    return factor, {
        "temperature_factor_source": "temperature_air",
        "temperature_c": temperature_c,
        "temperature_context": "air",
    }


def get_grouping_factor(
    factors: dict[str, Any],
    installation: dict[str, Any],
    phase_type: str,
) -> tuple[float, dict[str, Any]]:
    count = int(installation["grouped_circuits"])
    method = parse_installation_method(installation["installation_method"])

    if method.family in {"B1", "B2", "D1", "D2"}:
        factor = conservative_lookup_nested(
            factors["grouped_general"],
            count,
            phase_type,
        )
        return factor, {
            "grouping_factor_source": "grouped_general",
            "grouped_circuits": count,
        }

    if method.family == "C":
        factor = conservative_lookup(
            factors["grouping_air"]["solid_tray"],
            count,
        )
        return factor, {
            "grouping_factor_source": "grouping_air.solid_tray",
            "grouped_circuits": count,
        }

    if method.family in {"E", "F"}:
        factor = conservative_lookup(
            factors["grouping_air"]["perforated_tray"],
            count,
        )
        return factor, {
            "grouping_factor_source": "grouping_air.perforated_tray",
            "grouped_circuits": count,
        }

    if method.family == "G":
        factor = conservative_lookup(
            factors["grouping_air"]["ladder_tray"],
            count,
        )
        return factor, {
            "grouping_factor_source": "grouping_air.ladder_tray",
            "grouped_circuits": count,
            "note": "Mapped conservatively",
        }

    return 1.0, {
        "grouping_factor_source": "default",
        "grouped_circuits": count,
    }


def get_soil_resistivity_factor(
    _wires: dict[str, Any],
    factors: dict[str, Any],
    installation: dict[str, Any],
) -> tuple[float, dict[str, Any]]:
    method = parse_installation_method(installation["installation_method"])

    if method.family not in {"D1", "D2"}:
        return 1.0, {"soil_resistivity_factor_source": "not_applicable"}

    soil_res = get_soil_thermal_resistivity(installation)

    key = "ducts" if method.family == "D1" else "direct_buried"
    table = factors["soil_resistivity"][key]

    factor = conservative_lookup(table, soil_res)
    return factor, {
        "soil_resistivity_factor_source": f"soil_resistivity.{key}",
        "soil_thermal_resistivity": soil_res,
        "soil_type": installation.get("soil_type", "default"),
    }


def get_burial_depth_factor(
    factors: dict[str, Any],
    installation: dict[str, Any],
) -> tuple[float, dict[str, Any]]:
    method = parse_installation_method(installation["installation_method"])

    if method.family not in {"D1", "D2"}:
        return 1.0, {"burial_depth_factor_source": "not_applicable"}

    depth_m = float(installation["wire_burial_depth_m"])
    tables = factors.get("burial_depth", {})

    key = "ducts" if method.family == "D1" else "direct_buried"
    table = tables.get(key)

    if table:
        factor = conservative_lookup(table, depth_m)
        return factor, {
            "burial_depth_factor_source": f"burial_depth.{key}",
            "wire_burial_depth_m": depth_m,
        }

    return 1.0, {
        "burial_depth_factor_source": "default",
        "wire_burial_depth_m": depth_m,
    }


def get_parallel_symmetry_factor(
    factors: dict[str, Any],
    electrical: dict[str, Any],
    installation: dict[str, Any],
) -> tuple[float, dict[str, Any]]:
    parallels = int(electrical.get("parallels", 1))

    if parallels <= 1:
        return 1.0, {"parallel_symmetry_source": "not_applicable"}

    return float(factors["parallel_symmetry"]["non_ideal"]), {
        "parallel_symmetry_source": "parallel_symmetry.non_ideal",
        "parallels": parallels,
    }


def compute_total_factors(
    wires: dict[str, Any],
    factors: dict[str, Any],
    electrical: dict[str, Any],
    installation: dict[str, Any],
) -> tuple[float, float, dict[str, Any]]:
    trace: dict[str, Any] = {}

    f_temp, t = get_temperature_factor(wires, factors, installation)
    f_group, g = get_grouping_factor(factors, installation, electrical["phase_type"])
    f_soil, s = get_soil_resistivity_factor(wires, factors, installation)
    f_depth, d = get_burial_depth_factor(factors, installation)
    f_sym, p = get_parallel_symmetry_factor(factors, electrical, installation)

    trace.update(t)
    trace.update(g)
    trace.update(s)
    trace.update(d)
    trace.update(p)

    installation_factor = f_temp * f_group * f_soil * f_depth

    trace.update(
        {
            "f_temp": f_temp,
            "f_group": f_group,
            "f_soil": f_soil,
            "f_depth": f_depth,
            "f_parallel": f_sym,
        },
    )

    return installation_factor, f_sym, trace
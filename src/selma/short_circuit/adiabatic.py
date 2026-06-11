"""
file: src/selma/short_circuit/adiabatic.py

Short-circuit sizing helpers for the wire sizing engine.

This module implements the thermal short-circuit verification logic for
conductors according to the adiabatic criterion:

    S >= I * sqrt(t) / k
"""

from __future__ import annotations

from math import sqrt
from typing import Any

from ..models.schemas import ShortCircuitSelectionInput
from ..sources.constants import RHO_OHM_MM2_PER_M_20C, X_OHM_PER_M_DEFAULT
from ..tables.ampacity import ampacity_at


# ============================================================
# CORE HELPERS
# ============================================================

def short_circuit_min_section_mm2(
    constants: dict[str, Any],
    installation: dict[str, Any],
    short_circuit: dict[str, Any],
    parallels: int,
) -> tuple[float, dict[str, Any]]:
    """Calculate minimum thermal withstand section for short circuit."""
    material = installation["material"]
    insulation = installation["insulation"]
    k = float(constants["k_values"][material][insulation])

    icc_ka = float(short_circuit["Icc_kA"])
    time_s = float(short_circuit["time_s"])

    icc_a = icc_ka * 1000.0
    icc_per_conductor = icc_a / max(1, int(parallels))

    s_required = (icc_per_conductor * sqrt(time_s)) / k

    return s_required, {
        "short_circuit_mode": "manual",
        "short_circuit_k": k,
        "short_circuit_Icc_kA": icc_ka,
        "short_circuit_time_s": time_s,
        "short_circuit_Icc_per_conductor_A": icc_per_conductor,
        "short_circuit_required_section_mm2": s_required,
        "short_circuit_equal_distribution_assumed": True,
    }


def resolve_short_circuit_mode(short_circuit: dict[str, Any]) -> str:
    """Resolve the short-circuit operating mode."""
    mode = str(short_circuit.get("mode", "manual")).strip().lower()
    valid_modes = {"manual", "board_icc", "skip"}

    if mode not in valid_modes:
        msg = (
            f"Unsupported short_circuit mode '{short_circuit.get('mode')}'. "
            "Use 'manual', 'board_icc' or 'skip'."
        )
        raise ValueError(msg)

    return mode


def calculate_required_section_mm2(
    constants: dict[str, Any],
    installation: dict[str, Any],
    fault_current_ka: float,
    time_s: float,
    parallels: int,
) -> tuple[float, dict[str, Any]]:
    """Calculate required conductor section from a given fault current."""
    material = installation["material"]
    insulation = installation["insulation"]
    k = float(constants["k_values"][material][insulation])

    icc_a = float(fault_current_ka) * 1000.0
    icc_per_conductor = icc_a / max(1, int(parallels))
    s_required = (icc_per_conductor * sqrt(float(time_s))) / k

    return s_required, {
        "short_circuit_k": k,
        "short_circuit_Icc_kA": float(fault_current_ka),
        "short_circuit_time_s": float(time_s),
        "short_circuit_Icc_per_conductor_A": icc_per_conductor,
        "short_circuit_required_section_mm2": s_required,
        "short_circuit_equal_distribution_assumed": True,
    }


def calculate_end_of_circuit_fault_current_ka(
    electrical: dict[str, Any],
    installation: dict[str, Any],
    cable: dict[str, Any],
    board_icc_ka: float,
    section_mm2: float,
) -> float:
    """Estimate short-circuit current at the end of the circuit."""
    voltage_v = float(electrical["voltage_v"])
    phase_type = str(electrical["phase_type"]).strip().upper()
    length_m = float(electrical["length_m"])
    parallels = int(electrical.get("parallels", 1))

    material = str(installation["material"]).strip()
    rho = float(RHO_OHM_MM2_PER_M_20C[material])

    effective_section = float(section_mm2) * max(1, parallels)
    r_ohm_per_m = rho / effective_section

    x_input = float(cable.get("reactance_ohm_per_m", 0.0) or 0.0)
    if x_input > 0.0:
        x_ohm_per_m = x_input
    else:
        x_ohm_per_m = float(X_OHM_PER_M_DEFAULT.get(material, 0.00008))

    r_cable = r_ohm_per_m * length_m
    x_cable = x_ohm_per_m * length_m
    z_cable = sqrt((r_cable**2) + (x_cable**2))

    board_icc_a = float(board_icc_ka) * 1000.0
    if board_icc_a <= 0.0:
        msg = "Icc_kA must be greater than zero when short_circuit.mode='board_icc'"
        raise ValueError(msg)

    factor = sqrt(3.0) if phase_type == "3PH" else 2.0
    z_source = voltage_v / (factor * board_icc_a)
    z_total = z_source + z_cable

    end_icc_a = voltage_v / (factor * z_total)
    return end_icc_a / 1000.0


# ============================================================
# MODE-AWARE SHORT-CIRCUIT SELECTION
# ============================================================

def select_section_by_short_circuit_mode(
    selection_input: ShortCircuitSelectionInput,
) -> tuple[float, float, dict[str, Any]]:
    """Select the governing short-circuit section according to the active mode."""
    mode = resolve_short_circuit_mode(selection_input.short_circuit)

    if mode == "skip":
        selected_section = _select_minimum_valid_section(
            rows=selection_input.rows,
            method_column=selection_input.method_column,
            sections=selection_input.sections,
            min_section_mm2=selection_input.min_section_mm2,
        )
        return 0.0, selected_section, {
            "short_circuit_mode": "skip",
            "short_circuit_skipped": True,
            "short_circuit_required_section_mm2": 0.0,
        }

    if mode == "manual":
        required_section, trace = short_circuit_min_section_mm2(
            constants=selection_input.constants,
            installation=selection_input.installation,
            short_circuit=selection_input.short_circuit,
            parallels=selection_input.parallels,
        )
        selected_section = _select_standard_section_for_requirement(
            rows=selection_input.rows,
            method_column=selection_input.method_column,
            sections=selection_input.sections,
            min_section_mm2=selection_input.min_section_mm2,
            required_section_mm2=required_section,
        )
        return required_section, selected_section, trace

    board_icc_ka = float(selection_input.short_circuit["Icc_kA"])
    time_s = float(selection_input.short_circuit["time_s"])

    valid_sections = [
        section
        for section in selection_input.sections
        if section >= selection_input.min_section_mm2
        and ampacity_at(
            selection_input.rows,
            section,
            selection_input.method_column,
        )
        is not None
    ]
    if not valid_sections:
        msg = "No valid sections available for board_icc short-circuit evaluation"
        raise ValueError(msg)

    last_trace: dict[str, Any] = {}
    for section in valid_sections:
        end_icc_ka = calculate_end_of_circuit_fault_current_ka(
            electrical=selection_input.electrical,
            installation=selection_input.installation,
            cable=selection_input.cable,
            board_icc_ka=board_icc_ka,
            section_mm2=section,
        )
        required_section, trace = calculate_required_section_mm2(
            constants=selection_input.constants,
            installation=selection_input.installation,
            fault_current_ka=end_icc_ka,
            time_s=time_s,
            parallels=selection_input.parallels,
        )
        last_trace = {
            "short_circuit_mode": "board_icc",
            "short_circuit_board_Icc_kA": board_icc_ka,
            "short_circuit_end_Icc_kA": end_icc_ka,
            **trace,
        }

        if section >= required_section:
            return required_section, section, last_trace

    return last_trace["short_circuit_required_section_mm2"], valid_sections[-1], {
        **last_trace,
        "short_circuit_warning": (
            "No standard section fully satisfies board_icc adiabatic verification; "
            "returning highest available valid section."
        ),
    }


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _select_minimum_valid_section(
    rows: list[dict[str, Any]],
    method_column: str,
    sections: list[float],
    min_section_mm2: float,
) -> float:
    """Return the smallest valid standard section."""
    for section in sections:
        if section < min_section_mm2:
            continue
        if ampacity_at(rows, section, method_column) is not None:
            return section

    raise ValueError("No valid standard sections available")


def _select_standard_section_for_requirement(
    rows: list[dict[str, Any]],
    method_column: str,
    sections: list[float],
    min_section_mm2: float,
    required_section_mm2: float,
) -> float:
    """Return the smallest standard section satisfying a required minimum."""
    for section in sections:
        if section < min_section_mm2 or section < required_section_mm2:
            continue
        if ampacity_at(rows, section, method_column) is not None:
            return section

    valid_sections = [
        section
        for section in sections
        if section >= min_section_mm2
        and ampacity_at(rows, section, method_column) is not None
    ]
    if not valid_sections:
        msg = "No valid standard sections available for short-circuit requirement"
        raise ValueError(msg)

    return valid_sections[-1]
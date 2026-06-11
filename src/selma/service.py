"""
file: src/selma/service.py

Application service layer for SELMA.

This module exposes the public engine class used to size low-voltage power
circuits according to the selected standard tables.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Mapping

from .core.load import load_to_kva_and_ib
from .core.normalization import (
    compute_design_current,
    get_max_voltage_drop_pct,
    get_minimum_phase_section_mm2,
    parse_installation_method,
)
from .core.results import (
    base_output_fields,
    failed_result,
    format_cable,
    format_protection,
    ok_result,
)
from .data.loaders import load_standard_tables
from .exporters import (
    export_detailed_report,
    export_executive_report,
    export_visual_report,
    render_detailed_report,
    render_executive_report,
    render_visual_report,
)
from .factors.calculator import compute_total_factors
from .infrastructure.logging import get_logger
from .models.schemas import (
    AmpacityRequest,
    AmpacitySelectionInput,
    ShortCircuitSelectionInput,
    VoltageDropSelectionInput,
)
from .protection.protection import select_protection_aea
from .selection.sections import (
    select_section_by_ampacity_and_protection,
    select_section_by_voltage_drop,
)
from .short_circuit.adiabatic import select_section_by_short_circuit_mode
from .sources.constants import FLEXIBLE_CABLE_AMPACITY_FACTOR
from .tables.ampacity import ampacity_at, extract_sections, find_ampacity_rows
from .tables.lookup import apply_ampacity_table_factor
from .validation.validators import validate_inputs
from .voltage_drop.router import voltage_drop_pct

__all__ = ["SelmaEngine", "size_power_circuit", "__version__"]

__version__ = "3.0.0"

JsonDict = dict[str, Any]
DEFAULT_PURPOSE: JsonDict = {"type": "power", "subtype": None}
DEFAULT_CRITERIA: JsonDict = {
    "cos_phi": 0.9,
    "ampacity_margin": 1.0,
}


def _merge_criteria(criteria: Mapping[str, Any] | None) -> JsonDict:
    """Return validated engine criteria with defaults applied."""
    merged = dict(DEFAULT_CRITERIA)

    if criteria:
        merged.update(criteria)

    if "cos_phi" not in merged:
        raise ValueError("criteria must define 'cos_phi'")

    if "ampacity_margin" not in merged:
        raise ValueError("criteria must define 'ampacity_margin'")

    merged["cos_phi"] = float(merged["cos_phi"])
    merged["ampacity_margin"] = float(merged["ampacity_margin"])

    return merged


def _build_failure(
    *,
    circuit: JsonDict,
    electrical: JsonDict,
    trace: JsonDict,
    error: str,
    error_code: str,
) -> JsonDict:
    """Build a standard failed result."""
    return failed_result(
        base_output_fields(circuit, electrical),
        trace,
        error,
        error_code,
    )


def _build_trace_context(
    *,
    purpose: JsonDict,
    electrical: JsonDict,
    installation: JsonDict,
    cable: JsonDict,
    method_family: str,
    method_column: str,
    cos_phi: float,
    ampacity_margin: float,
    s_kva: float,
    ib: float,
    ib_design: float,
) -> JsonDict:
    """Build the shared trace context for a successful calculation."""
    return {
        "purpose": purpose,
        "phase_type": electrical["phase_type"],
        "voltage_v": electrical["voltage_v"],
        "length_m": electrical["length_m"],
        "parallels": int(electrical["parallels"]),
        "cos_phi_used": cos_phi,
        "ampacity_margin": ampacity_margin,
        "material": installation["material"],
        "insulation": installation["insulation"],
        "installation_method_full": installation["installation_method"],
        "installation_method_family": method_family,
        "installation_method_column": method_column,
        "temperature_c": installation["installation_temp_c"],
        "voltage_drop_method": cable.get("voltage_drop_method", "GDC"),
        "load_value": electrical["load"]["value"],
        "load_unit": electrical["load"]["unit"],
        "S_kVA": s_kva,
        "Ib": ib,
        "Ib_design": ib_design,
    }


def _build_checks(
    *,
    ib_design: float,
    final_protection: Any,
    final_iz_corr: float | None,
    final_vdrop_pct: float,
    max_vdrop_pct: float,
    final_section: float,
    min_section_mm2: float,
    sc_required_mm2: float,
) -> dict[str, bool]:
    """Compute the final engineering checks reported in the result."""
    ampacity_ok = final_iz_corr is not None and ib_design <= final_iz_corr

    protection_ok = (
        final_protection is not None
        and final_iz_corr is not None
        and ib_design <= float(final_protection.in_a) <= final_iz_corr
        and float(final_protection.i2_a) <= (1.45 * final_iz_corr)
    )

    voltage_drop_ok = final_vdrop_pct <= max_vdrop_pct
    short_circuit_ok = final_section >= max(min_section_mm2, sc_required_mm2)
    minimum_section_ok = final_section >= min_section_mm2

    return {
        "ampacity": ampacity_ok,
        "protection_coordination": protection_ok,
        "voltage_drop": voltage_drop_ok,
        "short_circuit": short_circuit_ok,
        "minimum_section": minimum_section_ok,
    }


def size_power_circuit(
    *,
    circuit: JsonDict,
    tables: JsonDict,
    criteria: Mapping[str, Any],
    standard: str,
    logger: logging.Logger,
) -> JsonDict:
    """
    Size a single low-voltage power circuit.

    Returns a standardized SELMA result dictionary.
    """
    logger.debug("size_power_circuit() called for tag=%s", circuit.get("tag", "?"))

    wires = tables["wires"]
    factors = tables["factors"]
    constants = tables["constants"]

    electrical = circuit["electrical"]
    installation = circuit["installation"]
    short_circuit = circuit["short_circuit"]
    cable = circuit["cable"]

    purpose = circuit.get("purpose", DEFAULT_PURPOSE)
    base = base_output_fields(circuit, electrical)
    trace: JsonDict = {
        "engine_version": __version__,
        "standard": standard,
    }

    try:
        cos_phi = float(criteria["cos_phi"])
        ampacity_margin = float(criteria["ampacity_margin"])
        phase = electrical["phase_type"]
        parallels = int(electrical["parallels"])

        method = parse_installation_method(installation["installation_method"])

        s_kva, ib, load_trace = load_to_kva_and_ib(electrical, cos_phi)
        if ib <= 0:
            return failed_result(base, trace, "Invalid load", "INVALID_LOAD")

        ib_design, design_trace = compute_design_current(
            circuit=circuit,
            ib=ib,
            ampacity_margin=ampacity_margin,
        )

        trace.update(load_trace)
        trace.update(design_trace)
        trace.update(
            _build_trace_context(
                purpose=purpose,
                electrical=electrical,
                installation=installation,
                cable=cable,
                method_family=method.family,
                method_column=method.column,
                cos_phi=cos_phi,
                ampacity_margin=ampacity_margin,
                s_kva=s_kva,
                ib=ib,
                ib_design=ib_design,
            ),
        )

        installation_factor, symmetry_factor, factor_trace = compute_total_factors(
            wires=wires,
            factors=factors,
            electrical=electrical,
            installation=installation,
        )
        trace.update(factor_trace)
        trace.update(
            {
                "phase_type": phase,
                "f_parallel": symmetry_factor,
                "flexible_cable_ampacity_factor": FLEXIBLE_CABLE_AMPACITY_FACTOR,
            },
        )

        request = AmpacityRequest(
            material=installation["material"],
            insulation=installation["insulation"],
            method_family=method.family,
            method_column=method.column,
        )

        rows = find_ampacity_rows(wires, request)
        if not rows:
            return _build_failure(
                circuit=circuit,
                electrical=electrical,
                trace=trace,
                error="No ampacity rows found for the selected configuration",
                error_code="NO_AMPACITY_ROWS",
            )

        sections = extract_sections(rows)
        if not sections:
            return _build_failure(
                circuit=circuit,
                electrical=electrical,
                trace=trace,
                error="No standard sections found for the selected configuration",
                error_code="NO_STANDARD_SECTIONS",
            )

        min_section_mm2 = get_minimum_phase_section_mm2(purpose)

        ampacity_input = AmpacitySelectionInput(
            rows=rows,
            method_column=method.column,
            sections=sections,
            installation_factor=installation_factor,
            parallels=parallels,
            symmetry_factor=symmetry_factor,
            ib_design=ib_design,
            min_section_mm2=min_section_mm2,
        )

        (
            selected_by_ampacity,
            iz_table,
            iz_base,
            iz_corr_total,
            protection_ampacity,
        ) = select_section_by_ampacity_and_protection(ampacity_input)

        if (
            selected_by_ampacity is None
            or iz_table is None
            or iz_base is None
            or iz_corr_total is None
            or protection_ampacity is None
        ):
            return _build_failure(
                circuit=circuit,
                electrical=electrical,
                trace=trace,
                error="Unable to select a section by ampacity and protection",
                error_code="AMPACITY_SELECTION_FAILED",
            )

        trace.update(
            {
                "selected_by_ampacity_mm2": selected_by_ampacity,
                "selected_Iz_table_a": iz_table,
                "selected_Iz_base_a": iz_base,
                "selected_Iz_corrected_total_a": iz_corr_total,
                "selected_protection_in_a": protection_ampacity.in_a,
                "selected_protection_i2_a": protection_ampacity.i2_a,
            },
        )

        max_vdrop_pct = get_max_voltage_drop_pct(purpose)

        vdrop_input = VoltageDropSelectionInput(
            sections=sections,
            selected_by_ampacity_mm2=selected_by_ampacity,
            min_section_mm2=min_section_mm2,
            max_vdrop_pct=max_vdrop_pct,
            electrical=electrical,
            installation=installation,
            cable=cable,
            ib=ib,
            cos_phi=cos_phi,
        )

        selected_by_vdrop, selected_vdrop_pct = select_section_by_voltage_drop(vdrop_input)

        trace.update(
            {
                "selected_by_vdrop_mm2": selected_by_vdrop,
                "selected_vdrop_pct": selected_vdrop_pct,
                "max_voltage_drop_pct": max_vdrop_pct,
            },
        )

        sc_required, selected_by_sc, sc_trace = select_section_by_short_circuit_mode(
            ShortCircuitSelectionInput(
                rows=rows,
                method_column=method.column,
                sections=sections,
                min_section_mm2=min_section_mm2,
                constants=constants,
                electrical=electrical,
                installation=installation,
                cable=cable,
                short_circuit=short_circuit,
                parallels=parallels,
            ),
        )

        trace.update(sc_trace)
        trace.update(
            {
                "selected_by_short_circuit_mm2": selected_by_sc,
                "short_circuit_required_section_mm2": sc_required,
                "short_circuit_Icc_kA": short_circuit.get("Icc_kA"),
                "short_circuit_time_s": short_circuit.get("time_s"),
            },
        )

        final_section = max(
            float(min_section_mm2),
            float(selected_by_ampacity),
            float(selected_by_vdrop),
            float(selected_by_sc),
        )

        final_iz_table = ampacity_at(rows, final_section, method.column)
        if final_iz_table is None:
            return _build_failure(
                circuit=circuit,
                electrical=electrical,
                trace=trace,
                error="Final section is not available in the ampacity table",
                error_code="FINAL_SECTION_NOT_IN_TABLE",
            )

        final_iz_base = apply_ampacity_table_factor(final_iz_table)
        final_iz_corr = final_iz_base * installation_factor * parallels * symmetry_factor

        final_protection = select_protection_aea(
            circuit,
            ib_design,
            final_iz_corr,
        )
        if final_protection is None:
            return _build_failure(
                circuit=circuit,
                electrical=electrical,
                trace=trace,
                error="Unable to select final protective device",
                error_code="FINAL_PROTECTION_SELECTION_FAILED",
            )

        cable_str, pe_mm2 = format_cable(circuit, final_section)
        final_vdrop = voltage_drop_pct(
            electrical,
            installation,
            cable,
            ib,
            cos_phi,
            final_section,
        )

        trace.update(
            {
                "final_section_mm2": final_section,
                "final_pe_section_mm2": pe_mm2,
                "final_Iz_table_a": final_iz_table,
                "final_Iz_base_a": final_iz_base,
                "final_Iz_corrected_total_a": final_iz_corr,
                "final_voltage_drop_pct": final_vdrop,
                "final_protection_in_a": final_protection.in_a,
                "final_protection_i2_a": final_protection.i2_a,
            },
        )

        base.update(
            {
                "current_a": float(ib),
                "cable_section": cable_str,
                "pe_section_mm2": pe_mm2,
                "protection": format_protection(final_protection, circuit),
                "protection_curve": final_protection.curve,
                "voltage_drop_pct": float(final_vdrop),
            },
        )

        checks = _build_checks(
            ib_design=ib_design,
            final_protection=final_protection,
            final_iz_corr=final_iz_corr,
            final_vdrop_pct=final_vdrop,
            max_vdrop_pct=max_vdrop_pct,
            final_section=final_section,
            min_section_mm2=min_section_mm2,
            sc_required_mm2=sc_required,
        )

        if all(checks.values()):
            return ok_result(base, trace, checks)

        return ok_result(
            base,
            trace,
            checks,
            warning="One or more engineering checks require review",
            warning_code="CHECKS_REVIEW",
        )

    except Exception as exc:
        logger.exception("Engine failure for tag=%s: %s", circuit.get("tag", "?"), exc)
        return failed_result(
            base,
            trace,
            f"Unexpected engine failure: {exc}",
            "ENGINE_EXCEPTION",
        )


class SelmaEngine:
    """
    Public SELMA application service.

    This class encapsulates the selected standard tables, engine criteria,
    and the orchestration logic required to size one or multiple circuits.
    """

    def __init__(
        self,
        *,
        standard: str = "aea90364",
        criteria: Mapping[str, Any] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the SELMA engine with the selected standard and criteria."""
        self.standard = standard.strip().lower()
        self.criteria = _merge_criteria(criteria)
        self.logger = logger or get_logger("selma.engine")
        self.tables = load_standard_tables(self.standard)

    def size_circuit(self, circuit: JsonDict) -> JsonDict:
        """Size a single circuit using the engine configuration."""
        validate_inputs(self.standard, [circuit])
        return size_power_circuit(
            circuit=circuit,
            tables=self.tables,
            criteria=self.criteria,
            standard=self.standard,
            logger=self.logger,
        )

    def size_project(self, circuits: list[JsonDict]) -> list[JsonDict]:
        """Size all circuits in a project run."""
        validate_inputs(self.standard, circuits)
        return [self.size_circuit(circuit) for circuit in circuits]

    def render_detailed_report(self, results: list[JsonDict]) -> str:
        """Render the detailed technical report."""
        return render_detailed_report(results)

    def render_executive_report(self, results: list[JsonDict]) -> str:
        """Render the executive technical report."""
        return render_executive_report(results)

    def render_visual_report(self, results: list[JsonDict]) -> str:
        """Render the visual engineering trace."""
        return render_visual_report(results)

    def export_detailed_report(
        self,
        results: list[JsonDict],
        output_dir: str | Path,
    ) -> Path:
        """Export the detailed technical report."""
        return export_detailed_report(results, output_dir)

    def export_executive_report(
        self,
        results: list[JsonDict],
        output_dir: str | Path,
    ) -> Path:
        """Export the executive technical report."""
        return export_executive_report(results, output_dir)

    def export_visual_report(
        self,
        results: list[JsonDict],
        output_dir: str | Path,
    ) -> Path:
        """Export the visual engineering trace."""
        return export_visual_report(results, output_dir)

    def export_reports(
        self,
        results: list[JsonDict],
        output_dir: str | Path,
    ) -> dict[str, Path]:
        """Export all reports."""
        return {
            "detailed": self.export_detailed_report(results, output_dir),
            "executive": self.export_executive_report(results, output_dir),
            "visual": self.export_visual_report(results, output_dir),
        }
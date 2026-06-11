"""
file: src/selma/exporters/visual.py

Visual engineering trace exporter.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import (
    add_bullet,
    add_failed_debug_section,
    build_ampacity_formula,
    build_conductor_material_label,
    build_differential_obligation_text,
    build_final_current_capacity,
    build_governing_criteria,
    build_installation_factor_expression,
    build_load_declared_label,
    build_method_description,
    build_motor_or_margin_note,
    build_operating_current_formula,
    build_phase_network_label,
    build_protection_curve_label,
    build_short_circuit_condition,
    build_total_factor_expression,
    build_voltage_drop_method_label,
    format_optional_factor,
    format_purpose_label,
    format_trace_float,
    format_trace_int,
    get_breaking_capacity_ka,
    get_min_section_text,
    get_vdrop_limit_text,
    safe_str,
    write_text_file,
)

JsonDict = dict[str, Any]


def render_visual_report(results: list[JsonDict]) -> str:
    """Generate the professional calculation log in markdown."""
    lines: list[str] = ["# Bitácora de Cálculo", ""]

    for result in results:
        tag = result.get("tag", "-")
        trace = result.get("trace", {})
        purpose_raw = result.get("purpose", "-")

        lines.append("---")
        lines.append(f"# Bitácora de Cálculo Optimizada: Circuito {tag}")
        lines.append("")

        if result.get("status") == "FAILED":
            lines.extend(add_failed_debug_section(result))
            continue

        lines.append("### 1. Definición del Circuito y Carga")
        add_bullet(
            lines,
            "Propósito",
            f"{format_purpose_label(purpose_raw)} "
            f"(Sección mínima {get_min_section_text(purpose_raw)})",
        )
        add_bullet(
            lines,
            "Tensión de Red ($U_n$)",
            build_phase_network_label(trace),
        )
        add_bullet(
            lines,
            "Carga Declarada ($S$)",
            build_load_declared_label(trace),
        )
        add_bullet(
            lines,
            "Corriente de Proyecto ($I_B$)",
            build_operating_current_formula(trace),
        )
        add_bullet(
            lines,
            "Longitud del tramo ($L$)",
            (
                f"{format_trace_float(trace.get('length_m'), 2)} m"
                if trace.get("length_m") is not None
                else "-"
            ),
        )
        extra_ib = build_motor_or_margin_note(trace)
        if extra_ib != "-":
            lines.append(f"*   **Ajustes sobre corriente:** {extra_ib}")
        lines.append("")

        lines.append("### 2. Capacidad de Conducción Térmica ($I_z$)")
        add_bullet(
            lines,
            "Método de Instalación",
            build_method_description(trace),
        )
        add_bullet(
            lines,
            "Conductores",
            build_conductor_material_label(trace),
        )
        add_bullet(
            lines,
            "Sección Inicial Candidata ($S_{térmica}$)",
            (
                f"{format_trace_float(trace.get('selected_by_ampacity_mm2'), 1)} mm²"
                if trace.get("selected_by_ampacity_mm2") is not None
                else "-"
            ),
        )
        add_bullet(
            lines,
            "$I_z$ de tabla",
            (
                f"{format_trace_float(trace.get('selected_Iz_table_a'), 3)} A"
                if trace.get("selected_Iz_table_a") is not None
                else "-"
            ),
        )
        lines.append("")
        lines.append("#### Factores de Corrección Aplicados:")
        add_bullet(
            lines,
            "Por Temperatura ($f_t$)",
            format_optional_factor(trace.get("f_temp"), 3),
        )
        add_bullet(
            lines,
            "Por Agrupamiento ($f_g$)",
            format_optional_factor(trace.get("f_group"), 3),
        )
        add_bullet(
            lines,
            "Por Flexibilidad ($f_{flex}$)",
            format_optional_factor(trace.get("flexible_cable_ampacity_factor"), 2),
        )
        add_bullet(
            lines,
            "Por Suelo ($f_s$)",
            format_optional_factor(trace.get("f_soil"), 3),
        )
        add_bullet(
            lines,
            "Por Profundidad ($f_p$)",
            format_optional_factor(trace.get("f_depth"), 3),
        )
        add_bullet(
            lines,
            "Por Simetría ($f_{sim}$)",
            format_optional_factor(trace.get("f_parallel"), 3),
        )
        add_bullet(
            lines,
            "Factor de Instalación / Otros ($f_{inst}$)",
            build_installation_factor_expression(trace),
        )
        add_bullet(
            lines,
            "Factor Total Aplicado ($f_{total}$)",
            build_total_factor_expression(trace),
        )
        add_bullet(
            lines,
            "Corriente Admisible Corregida ($I_z'$)",
            build_ampacity_formula(
                trace.get("selected_Iz_table_a"),
                trace,
                trace.get("selected_Iz_corrected_total_a"),
            ),
        )

        ib_design = trace.get("Ib_design")
        iz_corr = trace.get("selected_Iz_corrected_total_a")
        if ib_design is not None and iz_corr is not None:
            lines.append("")
            lines.append(
                f"> **Condición Térmica:** $I_B \\le I_z'$  "
                f"(debe cumplirse **{format_trace_float(ib_design, 2)} A ≤ "
                f"{format_trace_float(iz_corr, 2)} A**)."
            )
        lines.append("")

        lines.append("### 3. Selección y Coordinación de la Protección")
        add_bullet(
            lines,
            "Corriente Nominal ($I_n$)",
            build_protection_curve_label(result, trace),
        )
        final_in = trace.get("final_protection_in_a")

        selected_i2 = None
        if final_in is not None:
            try:
                selected_i2 = 1.45 * float(final_in)
            except (TypeError, ValueError):
                selected_i2 = None

        add_bullet(
            lines,
            "Corriente de Operación Convencional ($I_2$)",
            (
                f"$I_2 = 1,45 × I_n = "
                f"\\mathbf{{{format_trace_float(selected_i2, 2)} A}}$"
                if selected_i2 is not None
                else "-"
            ),
        )

        if ib_design is not None and final_in is not None and iz_corr is not None:
            lines.append("")
            lines.append("> **Condiciones de Coordinación:**")
            lines.append(
                f"> 1. $I_B \\le I_n \\le I_z'$  "
                f"(**{format_trace_float(ib_design, 2)} A ≤ "
                f"{format_trace_float(final_in, 0)} A ≤ "
                f"{format_trace_float(iz_corr, 2)} A**)."
            )
            i2_display = selected_i2 if selected_i2 is not None else None
            if i2_display is not None:
                lines.append(
                    f"> 2. $I_2 \\le 1,45 \\times I_z'$  "
                    f"(**{format_trace_float(i2_display, 2)} A ≤ "
                    f"{format_trace_float(1.45 * float(iz_corr), 2)} A**)."
                )
        lines.append("")

        lines.append("### 4. Verificación por Caída de Tensión ($\\Delta U$)")
        add_bullet(
            lines,
            "Método",
            build_voltage_drop_method_label(trace),
        )

        vdrop_pct = trace.get("final_voltage_drop_pct", trace.get("selected_vdrop_pct"))
        voltage_v = trace.get("voltage_v")
        if vdrop_pct is not None and voltage_v is not None:
            try:
                dv_volts = (float(vdrop_pct) / 100.0) * float(voltage_v)
                add_bullet(
                    lines,
                    "$\\Delta U$ calculada",
                    f"$\\Delta U = \\mathbf{{{format_trace_float(dv_volts, 3)} V}}$",
                )
            except (TypeError, ValueError):
                pass

        add_bullet(
            lines,
            "Sección por caída de tensión",
            (
                f"{format_trace_float(trace.get('selected_by_vdrop_mm2'), 1)} mm²"
                if trace.get("selected_by_vdrop_mm2") is not None
                else "-"
            ),
        )
        add_bullet(
            lines,
            "Porcentaje final",
            (
                f"$\\Delta U = \\mathbf{{{format_trace_float(vdrop_pct, 3)} \\%}}$"
                if vdrop_pct is not None
                else "-"
            ),
        )
        add_bullet(
            lines,
            "Límite admisible",
            get_vdrop_limit_text(purpose_raw, trace),
        )
        lines.append("")
        lines.append("*Si no verifica, se debe aumentar la sección y recalcular este paso.*")
        lines.append("")

        lines.append("### 5. Verificación al Cortocircuito (Solicitación Térmica)")
        add_bullet(
            lines,
            "Corriente de Cortocircuito Máxima ($I_{cc}$)",
            (
                f"{format_trace_float(trace.get('short_circuit_Icc_kA'), 1)} kA"
                if trace.get("short_circuit_Icc_kA") is not None
                else "-"
            ),
        )
        add_bullet(
            lines,
            "Tiempo de Despeje ($t$)",
            (
                f"{format_trace_float(trace.get('short_circuit_time_s'), 3)} s"
                if trace.get("short_circuit_time_s") is not None
                else "-"
            ),
        )
        add_bullet(
            lines,
            "Factor de Material ($k$)",
            format_trace_float(trace.get("short_circuit_k"), 0),
        )
        condition = build_short_circuit_condition(trace)
        if condition != "-":
            lines.append("")
            lines.append(f"> **Condición de Energía Pasante:** {condition}")
        lines.append("")

        lines.append("### 10. Resumen de Resultados Finales")
        lines.append("| Parámetro | Valor Final |")
        lines.append("| :--- | :--- |")
        lines.append(
            f"| **Sección del Conductor** | "
            f"**{format_trace_float(trace.get('final_section_mm2'), 1)} mm²** |"
        )
        lines.append(
            f"| **Protección (Calibre / Curva)** | "
            f"**{format_trace_int(trace.get('final_protection_in_a'))} A / "
            f"{safe_str(result.get('protection_curve', '-'))}** |"
        )
        lines.append(
            f"| **Poder de Corte ($P_{{dCcc}}$)** | "
            f"**{get_breaking_capacity_ka(result)} kA** |"
        )
        lines.append(
            f"| **Caída de Tensión Final** | "
            f"**{format_trace_float(trace.get('final_voltage_drop_pct'), 4)} %** |"
        )
        lines.append(
            f"| **$I_z'$ (Capacidad Real)** | "
            f"**{build_final_current_capacity(trace)} A** |"
        )
        lines.append(
            f"| **Protección Diferencial** | "
            f"**{build_differential_obligation_text()}** |"
        )

        governing = build_governing_criteria(trace)
        if governing != "-":
            lines.append(f"| **Criterio Gobernante** | **{governing}** |")

        if result.get("warning"):
            lines.append(
                f"| **Advertencia** | **{safe_str(result.get('warning'))}** |"
            )

        lines.append("")
        lines.append("")

    return "\n".join(lines)


def export_visual_report(results: list[JsonDict], output_dir: str | Path) -> Path:
    """Render and export the visual report."""
    content = render_visual_report(results)
    return write_text_file(output_dir, "bitacora_calculo.md", content)
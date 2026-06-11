"""
file: src/selma/exporters/markdown.py

Wire sizing markdown export module.

Generate AEA-compliant documentation by loading the official template,
injecting calculated results, and exporting final markdown outputs.

Design principles
-----------------
- Separation of concerns (template, logic, formatting)
- AEA-compliant output
- Clean, explicit and maintainable implementation
- Human-readable engineering trace for audit and review

Notes
-----
- The bitácora is only as complete as the engine trace allows.
- Missing values are displayed as "-" explicitly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
TEMPLATE_PATH = BASE_DIR / "templates" / "DV-E-LV-MC-Wires.md"


# ============================================================
# FILE IO
# ============================================================


def read_template() -> str:
    """Load the AEA memory template from disk."""
    if not TEMPLATE_PATH.exists():
        msg = f"Template not found: {TEMPLATE_PATH}"
        raise FileNotFoundError(msg)

    with TEMPLATE_PATH.open(encoding="utf-8") as file:
        return file.read()


def write_file(filename: str, content: str) -> None:
    """Write a UTF-8 text file into the outputs directory."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename

    with path.open("w", encoding="utf-8") as file:
        file.write(content)


# ============================================================
# GENERIC FORMAT HELPERS
# ============================================================


def format_float(value: float, decimals: int = 1) -> str:
    """Format a floating-point value using fixed decimals."""
    return f"{value:.{decimals}f}"


def format_trace_float(
    value: Any,
    decimals: int = 3,
    fallback: str = "-",
) -> str:
    """Safely format a numeric trace value."""
    if value is None:
        return fallback
    try:
        return format_float(float(value), decimals)
    except (TypeError, ValueError):
        return fallback


def format_trace_int(
    value: Any,
    fallback: str = "-",
) -> str:
    """Safely format an integer-like value."""
    if value is None:
        return fallback
    try:
        return str(int(round(float(value))))
    except (TypeError, ValueError):
        return fallback


def format_optional_factor(value: Any, decimals: int = 3) -> str:
    """Format an optional correction factor using '-' when absent."""
    return format_trace_float(value, decimals=decimals, fallback="-")


def safe_str(value: Any, fallback: str = "-") -> str:
    """Return a safe string representation."""
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def extract_section_mm2(cable_str: str) -> str:
    """Extract the numeric phase section from the cable description.

    Examples
    --------
    - "PVC 2x4mm² + PE4mm² Cu" -> "4"
    - "PVC 3x10mm² + PE10mm² Cu" -> "10"
    """
    text = str(cable_str)
    if "x" not in text or "mm²" not in text:
        return "-"
    try:
        after_x = text.split("x", maxsplit=1)[1]
        return after_x.split("mm²", maxsplit=1)[0].strip()
    except (IndexError, AttributeError):
        return "-"


def build_system_string(phase: str, parallels: int) -> str:
    """Build the system description used by the summary table."""
    phase_norm = str(phase).strip().upper()
    if phase_norm == "3PH":
        return f"Trif. / {parallels}"
    return f"Monof. / {parallels}"


def build_conductor_description(trace: dict[str, Any]) -> str:
    """Build the conductor type, material and insulation description."""
    material = trace.get("material", "Cu")
    insulation = trace.get("insulation", "PVC")
    return f"Multipolar / {material} / {insulation}"


def format_protection_summary(result: dict[str, Any]) -> str:
    """Format protection descriptor for the summary results table."""
    protection = safe_str(result.get("protection", "-"))
    curve = safe_str(result.get("protection_curve", "-"))
    return f"{protection} / {curve}"


def get_breaking_capacity_ka(result: dict[str, Any]) -> str:
    """Return the breaking capacity in kA from trace when available."""
    trace = result.get("trace", {})
    icc = trace.get("short_circuit_Icc_kA")

    if icc is not None:
        return format_float(float(icc), 1)

    # fallback shown explicitly
    return "-"


def build_warning_suffix(result: dict[str, Any]) -> str:
    """Return an inline warning marker for summary rows when relevant."""
    if result.get("warning"):
        return " ⚠"
    return ""


def build_load_input_string(trace: dict[str, Any]) -> str:
    """Build the declared load string preserving original unit when available."""
    load_value = trace.get("load_value")
    load_unit = trace.get("load_unit")

    if load_value is None or load_unit is None:
        return "-"

    value = float(load_value)
    if value.is_integer():
        value_str = str(int(value))
    else:
        value_str = format_float(value, 3)

    return f"{value_str} {load_unit}"


def build_temperature_context_label(trace: dict[str, Any]) -> str:
    """Return a user-facing label for the temperature interpretation."""
    context = str(trace.get("temperature_context", "")).strip().lower()
    if context == "soil":
        return "suelo"
    if context == "air":
        return "ambiente"
    return "-"


def build_temperature_label(trace: dict[str, Any]) -> str:
    """Build the temperature label including the installation context."""
    context = build_temperature_context_label(trace)
    if context == "-":
        return "Temperatura utilizada"
    return f"Temperatura utilizada para el {context}"


def build_governing_criteria(trace: dict[str, Any]) -> str:
    """Return the governing criterion (single, not combined)."""

    final_section = trace.get("final_section_mm2")

    priority = [
        ("selected_by_short_circuit_mm2", "cortocircuito"),
        ("selected_by_vdrop_mm2", "caída de tensión"),
        ("selected_by_ampacity_mm2", "ampacidad y protección"),
    ]

    for key, label in priority:
        try:
            if abs(float(trace.get(key)) - float(final_section)) < 1e-6:
                return label
        except (TypeError, ValueError):
            continue

    return "-"


def build_installation_factor_expression(trace: dict[str, Any]) -> str:
    """Build the installation derating expression shown in the calculation log."""
    flexible = float(trace.get("flexible_cable_ampacity_factor", 1.0))
    f_temp = float(trace.get("f_temp", 1.0))
    f_group = float(trace.get("f_group", 1.0))
    f_soil = float(trace.get("f_soil", 1.0))
    f_depth = float(trace.get("f_depth", 1.0))
    f_sym = float(trace.get("f_parallel", 1.0))

    parts = [
        format_float(flexible, 2),
        format_float(f_temp, 3),
        format_float(f_group, 3),
        format_float(f_soil, 3),
        format_float(f_depth, 3),
        format_float(f_sym, 3),
    ]
    total = flexible * f_temp * f_group * f_soil * f_depth * f_sym

    return f"({'×'.join(parts)}) = {format_float(total, 3)}"


def build_total_factor_expression(trace: dict[str, Any]) -> str:
    """Build the full correction-factor expression including parallels."""
    f_inst = (
        float(trace.get("flexible_cable_ampacity_factor", 1.0))
        * float(trace.get("f_temp", 1.0))
        * float(trace.get("f_group", 1.0))
        * float(trace.get("f_soil", 1.0))
        * float(trace.get("f_depth", 1.0))
        * float(trace.get("f_parallel", 1.0))
    )
    n_parallel = int(trace.get("parallels", 1))
    f_total = f_inst * n_parallel

    return f"{format_float(f_inst, 3)} × {n_parallel} = {format_float(f_total, 3)}"


def build_ampacity_formula(
    iz_table: Any,
    trace: dict[str, Any],
    corrected_value: Any,
) -> str:
    """Build the corrected ampacity expression with all applied factors."""
    if iz_table is None or corrected_value is None:
        return "-"

    factors_str = "×".join(
        [
            format_trace_float(
                trace.get("flexible_cable_ampacity_factor"),
                2,
                fallback="1.00",
            ),
            format_trace_float(trace.get("f_temp"), 3, fallback="1.000"),
            format_trace_float(trace.get("f_group"), 3, fallback="1.000"),
            format_trace_float(trace.get("f_soil"), 3, fallback="1.000"),
            format_trace_float(trace.get("f_depth"), 3, fallback="1.000"),
            format_trace_float(trace.get("f_parallel"), 3, fallback="1.000"),
        ],
    )
    n_parallel = int(trace.get("parallels", 1))

    return (
        f"{format_trace_float(iz_table, 3)} A × {factors_str} × {n_parallel} = "
        f"{format_trace_float(corrected_value, 3)} A"
    )


def round_pe_section(pe_section_mm2: Any) -> str:
    """Round the PE section to the next standard commercial section."""
    if pe_section_mm2 is None:
        return "-"

    standard_sections = [
        1.5,
        2.5,
        4,
        6,
        10,
        16,
        25,
        35,
        50,
        70,
        95,
        120,
        150,
        185,
        240,
        300,
        400,
        500,
        630,
    ]
    pe_value = float(pe_section_mm2)

    for section in standard_sections:
        if pe_value <= section:
            if float(section).is_integer():
                return f"{int(section)} mm²"
            return f"{format_float(section, 1)} mm²"

    return f"{format_float(standard_sections[-1], 1)} mm²"


def add_bullet(lines: list[str], label: str, value: str) -> None:
    """Append a markdown bullet line only when the value is meaningful."""
    if value == "-":
        return
    lines.append(f"*   **{label}:** {value}")


def add_failed_debug_section(result: dict[str, Any]) -> list[str]:
    """Build the debug trace section for a failed circuit result."""
    return [
        "### Estado",
        f"*   **Resultado:** ❌ Error en el cálculo.",
        f"*   **Detalle:** {safe_str(result.get('error', 'Sin detalle'))}",
        "",
    ]


def build_ampacity_selection_string(trace: dict[str, Any]) -> str:
    """Build the section string selected from ampacity criteria."""
    selected = trace.get("selected_by_ampacity_mm2")
    if selected is None:
        return "-"
    return f"{format_trace_float(selected, 1)} mm²"


def build_corrected_section_check_string(trace: dict[str, Any]) -> str:
    """Build the corrected ampacity coordination line."""
    selected = trace.get("selected_by_ampacity_mm2")
    if selected is None:
        return "-"
    return f"{format_trace_float(selected, 1)} mm²"


def build_raw_table_section_check_string(trace: dict[str, Any]) -> str:
    """Build the raw-table preliminary ampacity coordination line."""
    selected = trace.get("selected_by_raw_table_mm2")
    if selected is None:
        return "-"
    return f"{format_trace_float(selected, 1)} mm²"


# ============================================================
# PURPOSE / DOMAIN PRESENTATION HELPERS
# ============================================================


def normalize_purpose(purpose: Any) -> tuple[str, str | None]:
    """Normalize purpose into (type, subtype) for presentation."""
    if isinstance(purpose, dict):
        p_type = str(purpose.get("type", "")).strip().lower()
        subtype_raw = purpose.get("subtype")
        p_subtype = (
            str(subtype_raw).strip().lower()
            if subtype_raw is not None
            else None
        )
        return p_type, p_subtype

    return str(purpose).strip().lower(), None


def format_purpose_label(purpose: Any) -> str:
    """Return a readable purpose label for the log."""
    p_type, p_subtype = normalize_purpose(purpose)

    if p_type == "lighting":
        if p_subtype == "iug":
            return "Iluminación de Uso General (IUG)"
        if p_subtype == "iue":
            return "Iluminación de Uso Especial (IUE)"
        return "Iluminación"

    if p_type == "outlet":
        if p_subtype == "tug":
            return "Tomacorrientes de Uso General (TUG)"
        if p_subtype == "tue":
            return "Tomacorrientes de Uso Especial (TUE)"
        return "Tomacorrientes"

    if p_type == "board":
        return "Alimentación de Tablero"

    if p_type == "power":
        if p_subtype == "acu":
            return "Alimentación de Carga Única (ACU)"
        if p_subtype == "equipment":
            return "Alimentación de Equipo"
        return "Potencia General"

    if p_type == "motor":
        if p_subtype == "direct":
            return "Motor (Servicio Directo)"
        if p_subtype == "heavy":
            return "Motor (Arranque Pesado)"
        return "Motor"

    if p_type == "control":
        return "Control"

    if p_type == "signal":
        return "Señal"

    return safe_str(purpose, "-")


def get_min_section_text(purpose: Any) -> str:
    """Return the minimum regulatory section text according to purpose."""
    p_type, _ = normalize_purpose(purpose)

    if p_type == "lighting":
        return "1,5 mm²"

    if p_type in {"outlet", "power", "motor"}:
        return "2,5 mm²"

    return "-"


def get_vdrop_limit_text(purpose: Any, trace: dict[str, Any]) -> str:
    """Return the admissible voltage-drop limit in a user-facing way."""
    p_type, p_subtype = normalize_purpose(purpose)
    explicit_limit = trace.get("max_voltage_drop_pct")
    limit_str = (
        f"{format_trace_float(explicit_limit, 2)}%"
        if explicit_limit is not None
        else "-"
    )

    if p_type == "board":
        return f"{limit_str} (alimentación de tablero)"
    if p_type == "lighting":
        return f"{limit_str} (iluminación)"
    if p_type == "outlet":
        return f"{limit_str} (tomacorrientes)"
    if p_type == "motor":
        if p_subtype == "heavy":
            return f"{limit_str} (motor)"
        return f"{limit_str} (motor)"
    if p_type == "power":
        return f"{limit_str} (uso general)"
    return limit_str


def build_phase_network_label(trace: dict[str, Any]) -> str:
    """Return a readable network label."""
    phase = str(trace.get("phase_type", "")).strip().upper()
    voltage = trace.get("voltage_v", None)

    voltage_text = (
        f"{format_trace_int(voltage)} V"
        if voltage is not None
        else "- V"
    )

    if phase == "3PH":
        return f"{voltage_text} (Trifásico)"

    return f"{voltage_text} (Monofásico)"


def build_load_declared_label(trace: dict[str, Any]) -> str:
    """Return a readable declared load string (FIXED units)."""
    s_kva = trace.get("S_kVA")

    if s_kva is None:
        return "-"

    kva = float(s_kva)
    va = int(kva * 1000)

    return f"{format_float(kva, 1)} kVA ({va} VA)"


def build_operating_current_formula(trace: dict[str, Any]) -> str:
    """Return a readable operating-current expression when possible."""
    s_kva = trace.get("S_kVA")
    voltage = trace.get("voltage_v")
    phase = str(trace.get("phase_type", "")).strip().upper()
    ib = trace.get("Ib")

    if ib is None:
        return "-"

    if s_kva is None or voltage is None:
        return f"{format_trace_float(ib, 2)} A"

    s_va = float(s_kva) * 1000.0
    voltage_f = float(voltage)

    if phase == "3PH":
        return (
            f"$I_B = S / (\\sqrt{{3}} \\times U_n) = "
            f"{format_float(s_va, 0)} VA / (1,732 × {format_float(voltage_f, 0)} V) = "
            f"\\mathbf{{{format_trace_float(ib, 2)} A}}$"
        )

    return (
        f"$I_B = S / U_n = "
        f"{format_float(s_va, 0)} VA / {format_float(voltage_f, 0)} V = "
        f"\\mathbf{{{format_trace_float(ib, 2)} A}}$"
    )


def build_motor_or_margin_note(trace: dict[str, Any]) -> str:
    """Return additional note about regulatory or margin factors."""
    ib = trace.get("Ib")
    ib_reg = trace.get("Ib_regulatory")
    ib_design = trace.get("Ib_design")
    motor_factor = trace.get("motor_single_feeder_factor")
    margin = trace.get("ampacity_margin")

    parts: list[str] = []

    if ib is not None and ib_reg is not None:
        try:
            if float(ib_reg) != float(ib):
                parts.append(
                    f"Factor reglamentario aplicado: {format_trace_float(motor_factor, 2)} → "
                    f"$I_{{B,reg}} = \\mathbf{{{format_trace_float(ib_reg, 2)} A}}$"
                )
        except (TypeError, ValueError):
            pass

    if margin is not None and ib_design is not None:
        try:
            if float(margin) != 1.0:
                parts.append(
                    f"Margen de diseño: {format_trace_float(margin, 2)} → "
                    f"$I_{{B,d}} = \\mathbf{{{format_trace_float(ib_design, 2)} A}}$"
                )
            else:
                parts.append(
                    f"Corriente de proyecto corregida: "
                    f"$I_{{B,d}} = \\mathbf{{{format_trace_float(ib_design, 2)} A}}$"
                )
        except (TypeError, ValueError):
            pass

    if not parts:
        return "-"

    return " | ".join(parts)


def build_method_description(trace: dict[str, Any]) -> str:
    """Return a user-facing installation-method description."""
    full = safe_str(trace.get("installation_method_full", "-"))
    family = safe_str(trace.get("installation_method_family", "-"))
    column = safe_str(trace.get("installation_method_column", "-"))

    if full != "-":
        return f"{full} (familia {family}, columna {column})"

    return "-"


def build_conductor_material_label(trace: dict[str, Any]) -> str:
    """Return conductor material/insulation/parallels."""
    material = safe_str(trace.get("material", "-"))
    insulation = safe_str(trace.get("insulation", "-"))
    parallels = format_trace_int(trace.get("parallels", 1), fallback="1")

    return f"{material} / {insulation}, n={parallels}"


def build_voltage_drop_method_label(trace: dict[str, Any]) -> str:
    """Return voltage-drop method label."""
    method = safe_str(trace.get("voltage_drop_method", "-")).upper()
    if method == "GDC":
        return "Gradiente de Caída (GDC)"
    if method == "IMPEDANCE":
        return "Impedancia (R + X)"
    return method


def build_protection_curve_label(result: dict[str, Any], trace: dict[str, Any]) -> str:
    """Build a readable protection rating/curve label."""
    current = trace.get("final_protection_in_a", trace.get("selected_protection_in_a"))
    curve = result.get("protection_curve", trace.get("final_protection_curve", "-"))
    return f"{format_trace_int(current)} A (Curva {safe_str(curve, '-')})"


def build_short_circuit_condition(trace: dict[str, Any]) -> str:
    """Build short-circuit condition correctly."""
    mode = str(trace.get("short_circuit_mode", "")).lower()

    if mode == "skip":
        return "No gobernante (modo skip)"

    required = trace.get("short_circuit_required_section_mm2")
    final_section = trace.get("final_section_mm2")

    if required is None or required == 0:
        return "No gobernante (sin exigencia térmica)"

    return (
        f"$S \\ge (I_{{cc}} \\times \\sqrt{{t}}) / k$  →  "
        f"requerido: **{format_trace_float(required, 3)} mm²**, "
        f"adoptado: **{format_trace_float(final_section, 1)} mm²**"
    )


def build_final_current_capacity(trace: dict[str, Any]) -> str:
    """Return corrected final ampacity."""
    return format_trace_float(trace.get("final_Iz_corrected_total_a"), 3)


def build_differential_obligation_text() -> str:
    """Return the regulatory differential note."""
    return "≤ 30 mA (Obligatoria en circuitos terminales según AEA)"


# ============================================================
# TABLE BUILDER
# ============================================================


def build_results_table(results: list[dict[str, Any]]) -> str:
    """Generate the AEA-compliant summary results table."""
    headers = [
        "Circuito",
        "Destino",
        "Sistema / Ternas",
        "Conductor (Tipo/Mat./Aisl.)",
        "I_B [A]",
        "Sección [mm²]",
        "Prot. (I_n/C)",
        "P_dc [kA]",
        "ΔV [%]",
        "S_PE [mm²]",
    ]

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for result in results:
        if result.get("status") == "FAILED":
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(result.get("tag", "-")),
                        str(result.get("destination", "-")),
                        "-",
                        "ERROR",
                        "-",
                        "-",
                        "-",
                        "-",
                        "-",
                        "-",
                    ],
                )
                + " |",
            )
            continue

        trace = result.get("trace", {})
        phase = trace.get("phase_type", "3PH")
        parallels = int(trace.get("parallels", 1))

        row = [
            f"**{result.get('tag', '-')}**{build_warning_suffix(result)}",
            f"{result.get('origin', '-')} → {result.get('destination', '-')}",
            build_system_string(phase, parallels),
            build_conductor_description(trace),
            format_float(float(result.get("current_a", 0.0))),
            extract_section_mm2(str(result.get("cable_section", ""))),
            format_protection_summary(result),
            get_breaking_capacity_ka(result),
            format_trace_float(float(result.get("voltage_drop_pct", 0.0))),
            format_float(float(result.get("pe_section_mm2", 0.0)), 0),
        ]

        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


# ============================================================
# DOCUMENT GENERATION
# ============================================================


def generate_memory_document(results: list[dict[str, Any]]) -> str:
    """Inject the results table into the official memory template."""
    template = read_template()
    table = build_results_table(results)

    if "{{RESULTS_TABLE}}" not in template:
        msg = "Template missing placeholder '{{RESULTS_TABLE}}'"
        raise ValueError(msg)

    return template.replace("{{RESULTS_TABLE}}", table)


# ============================================================
# PLIEGO
# ============================================================


def build_pliego(results: list[dict[str, Any]]) -> str:
    """Generate the simplified specification table."""
    headers = ["Circuito", "Destino", "Sección", "Protección"]

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for result in results:
        section = (
            "ERROR"
            if result.get("status") == "FAILED"
            else result.get("cable_section", "-")
        )

        row = [
            str(result.get("tag", "-")),
            str(result.get("destination", "-")),
            str(section),
            str(result.get("protection", "-")),
        ]

        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


# ============================================================
# DEBUG / BITÁCORA PROFESIONAL
# ============================================================


def build_debug_trace(results: list[dict[str, Any]]) -> str:
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

        # ----------------------------------------------------
        # 1. Definición del circuito y carga
        # ----------------------------------------------------
        lines.append("### 1. Definición del Circuito y Carga")
        add_bullet(
            lines,
            "Propósito",
            f"{format_purpose_label(purpose_raw)} (Sección mínima {get_min_section_text(purpose_raw)})",
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

        # ----------------------------------------------------
        # 2. Capacidad de conducción térmica
        # ----------------------------------------------------
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
            lines.append(
                ""
            )
            lines.append(
                f"> **Condición Térmica:** "
                f"$I_B \\le I_z'$  "
                f"(debe cumplirse **{format_trace_float(ib_design, 2)} A ≤ {format_trace_float(iz_corr, 2)} A**)."
            )
        lines.append("")

        # ----------------------------------------------------
        # 3. Protección
        # ----------------------------------------------------
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

        # ----------------------------------------------------
        # 4. Caída de tensión
        # ----------------------------------------------------
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
                    (
                        f"$\\Delta U = \\mathbf{{{format_float(dv_volts, 3)} V}}$"
                    ),
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

        # ----------------------------------------------------
        # 5. Cortocircuito
        # ----------------------------------------------------
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

        # ----------------------------------------------------
        # 6. Resumen final
        # ----------------------------------------------------
        lines.append("### 10. Resumen de Resultados Finales")
        lines.append("| Parámetro | Valor Final |")
        lines.append("| :--- | :--- |")
        lines.append(
            f"| **Sección del Conductor** | **{format_trace_float(trace.get('final_section_mm2'), 1)} mm²** |"
        )
        lines.append(
            f"| **Protección (Calibre / Curva)** | **{format_trace_int(trace.get('final_protection_in_a'))} A / {safe_str(result.get('protection_curve', '-'))}** |"
        )
        lines.append(
            f"| **Poder de Corte ($P_{{dCcc}}$)** | **{get_breaking_capacity_ka(result)} kA** |"
        )
        lines.append(
            f"| **Caída de Tensión Final** | **{format_trace_float(trace.get('final_voltage_drop_pct'), 4)} %** |"
        )
        lines.append(
            f"| **$I_z'$ (Capacidad Real)** | **{build_final_current_capacity(trace)} A** |"
        )
        lines.append(
            f"| **Protección Diferencial** | **{build_differential_obligation_text()}** |"
        )

        governing = build_governing_criteria(trace)
        if governing != "-":
            lines.append(
                f"| **Criterio Gobernante** | **{governing}** |"
            )

        if result.get("warning"):
            lines.append(
                f"| **Advertencia** | **{safe_str(result.get('warning'))}** |"
            )

        lines.append("")
        lines.append("")

    return "\n".join(lines)


# ============================================================
# EXPORT ENTRYPOINT
# ============================================================


def export_markdown_outputs(
    results: list[dict[str, Any]],
    project_meta: dict[str, Any],
    standard: str,
) -> None:
    """Export all markdown deliverables to the outputs directory."""
    memoria = generate_memory_document(results)
    pliego = build_pliego(results)
    debug = build_debug_trace(results)

    write_file("DV-E-LV-MC-Wires.md", memoria)
    write_file("pliego.md", pliego)
    write_file("bitacora_calculo.md", debug)

    _ = project_meta
    _ = standard
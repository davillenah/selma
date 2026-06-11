"""
file: src/selma/exporters/common.py

Shared helpers for SELMA markdown exporters.
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]


def read_template() -> str:
    """Load the bundled markdown template."""
    template = files("selma.templates").joinpath("DV-E-LV-MC-Wires.md")

    if not template.is_file():
        msg = "Template not found inside package: selma.templates/DV-E-LV-MC-Wires.md"
        raise FileNotFoundError(msg)

    return template.read_text(encoding="utf-8")


def write_text_file(output_dir: str | Path, filename: str, content: str) -> Path:
    """Write UTF-8 text content to a target directory."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    file_path = output_path / filename
    file_path.write_text(content, encoding="utf-8")
    return file_path


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
    """Extract the numeric phase section from the cable description."""
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


def build_conductor_description(trace: JsonDict) -> str:
    """Build the conductor type, material and insulation description."""
    material = trace.get("material", "Cu")
    insulation = trace.get("insulation", "PVC")
    return f"Multipolar / {material} / {insulation}"


def format_protection_summary(result: JsonDict) -> str:
    """Format protection descriptor for the summary results table."""
    protection = safe_str(result.get("protection", "-"))
    curve = safe_str(result.get("protection_curve", "-"))
    return f"{protection} / {curve}"


def get_breaking_capacity_ka(result: JsonDict) -> str:
    """Return the breaking capacity in kA from trace when available."""
    trace = result.get("trace", {})
    icc = trace.get("short_circuit_Icc_kA")

    if icc is not None:
        return format_float(float(icc), 1)

    return "-"


def build_warning_suffix(result: JsonDict) -> str:
    """Return an inline warning marker for summary rows when relevant."""
    if result.get("warning"):
        return " ⚠"
    return ""


def build_load_input_string(trace: JsonDict) -> str:
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


def build_temperature_context_label(trace: JsonDict) -> str:
    """Return a user-facing label for the temperature interpretation."""
    context = str(trace.get("temperature_context", "")).strip().lower()
    if context == "soil":
        return "suelo"
    if context == "air":
        return "ambiente"
    return "-"


def build_temperature_label(trace: JsonDict) -> str:
    """Build the temperature label including the installation context."""
    context = build_temperature_context_label(trace)
    if context == "-":
        return "Temperatura utilizada"
    return f"Temperatura utilizada para el {context}"


def build_governing_criteria(trace: JsonDict) -> str:
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


def build_installation_factor_expression(trace: JsonDict) -> str:
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


def build_total_factor_expression(trace: JsonDict) -> str:
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
    trace: JsonDict,
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


def add_failed_debug_section(result: JsonDict) -> list[str]:
    """Build the debug trace section for a failed circuit result."""
    return [
        "### Estado",
        "*   **Resultado:** ❌ Error en el cálculo.",
        f"*   **Detalle:** {safe_str(result.get('error', 'Sin detalle'))}",
        "",
    ]


def build_ampacity_selection_string(trace: JsonDict) -> str:
    """Build the section string selected from ampacity criteria."""
    selected = trace.get("selected_by_ampacity_mm2")
    if selected is None:
        return "-"
    return f"{format_trace_float(selected, 1)} mm²"


def build_corrected_section_check_string(trace: JsonDict) -> str:
    """Build the corrected ampacity coordination line."""
    selected = trace.get("selected_by_ampacity_mm2")
    if selected is None:
        return "-"
    return f"{format_trace_float(selected, 1)} mm²"


def build_raw_table_section_check_string(trace: JsonDict) -> str:
    """Build the raw-table preliminary ampacity coordination line."""
    selected = trace.get("selected_by_raw_table_mm2")
    if selected is None:
        return "-"
    return f"{format_trace_float(selected, 1)} mm²"


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


def get_vdrop_limit_text(purpose: Any, trace: JsonDict) -> str:
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


def build_phase_network_label(trace: JsonDict) -> str:
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


def build_load_declared_label(trace: JsonDict) -> str:
    """Return a readable declared load string."""
    s_kva = trace.get("S_kVA")

    if s_kva is None:
        return "-"

    kva = float(s_kva)
    va = int(kva * 1000)

    return f"{format_float(kva, 1)} kVA ({va} VA)"


def build_operating_current_formula(trace: JsonDict) -> str:
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


def build_motor_or_margin_note(trace: JsonDict) -> str:
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
                    "Factor reglamentario aplicado: "
                    f"{format_trace_float(motor_factor, 2)} → "
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
                    "Corriente de proyecto corregida: "
                    f"$I_{{B,d}} = \\mathbf{{{format_trace_float(ib_design, 2)} A}}$"
                )
        except (TypeError, ValueError):
            pass

    if not parts:
        return "-"

    return " | ".join(parts)


def build_method_description(trace: JsonDict) -> str:
    """Return a user-facing installation-method description."""
    full = safe_str(trace.get("installation_method_full", "-"))
    family = safe_str(trace.get("installation_method_family", "-"))
    column = safe_str(trace.get("installation_method_column", "-"))

    if full != "-":
        return f"{full} (familia {family}, columna {column})"

    return "-"


def build_conductor_material_label(trace: JsonDict) -> str:
    """Return conductor material/insulation/parallels."""
    material = safe_str(trace.get("material", "-"))
    insulation = safe_str(trace.get("insulation", "-"))
    parallels = format_trace_int(trace.get("parallels", 1), fallback="1")

    return f"{material} / {insulation}, n={parallels}"


def build_voltage_drop_method_label(trace: JsonDict) -> str:
    """Return voltage-drop method label."""
    method = safe_str(trace.get("voltage_drop_method", "-")).upper()
    if method == "GDC":
        return "Gradiente de Caída (GDC)"
    if method == "IMPEDANCE":
        return "Impedancia (R + X)"
    return method


def build_protection_curve_label(result: JsonDict, trace: JsonDict) -> str:
    """Build a readable protection rating/curve label."""
    current = trace.get("final_protection_in_a", trace.get("selected_protection_in_a"))
    curve = result.get("protection_curve", trace.get("final_protection_curve", "-"))
    return f"{format_trace_int(current)} A (Curva {safe_str(curve, '-')})"


def build_short_circuit_condition(trace: JsonDict) -> str:
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


def build_final_current_capacity(trace: JsonDict) -> str:
    """Return corrected final ampacity."""
    return format_trace_float(trace.get("final_Iz_corrected_total_a"), 3)


def build_differential_obligation_text() -> str:
    """Return the regulatory differential note."""
    return "≤ 30 mA (Obligatoria en circuitos terminales según AEA)"

# ============================================================
# MISSING HELPERS FOR VISUAL REPORT
# ============================================================

def build_ampacity_formula(
    iz_table: Any,
    trace: JsonDict,
    corrected_value: Any,
) -> str:
    if iz_table is None or corrected_value is None:
        return "-"

    factors_str = "×".join(
        [
            format_trace_float(trace.get("flexible_cable_ampacity_factor"), 2, "1.00"),
            format_trace_float(trace.get("f_temp"), 3, "1.000"),
            format_trace_float(trace.get("f_group"), 3, "1.000"),
            format_trace_float(trace.get("f_soil"), 3, "1.000"),
            format_trace_float(trace.get("f_depth"), 3, "1.000"),
            format_trace_float(trace.get("f_parallel"), 3, "1.000"),
        ],
    )

    n_parallel = int(trace.get("parallels", 1))

    return (
        f"{format_trace_float(iz_table, 3)} A × {factors_str} × {n_parallel} = "
        f"{format_trace_float(corrected_value, 3)} A"
    )


def build_final_current_capacity(trace: JsonDict) -> str:
    return format_trace_float(trace.get("final_Iz_corrected_total_a"), 3)


def build_differential_obligation_text() -> str:
    return "≤ 30 mA (Obligatoria en circuitos terminales según AEA)"
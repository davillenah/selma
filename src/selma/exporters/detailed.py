"""file: src/selma/exporters/detailed.py

Detailed technical report exporter.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .utils import (
    build_conductor_description,
    build_system_string,
    build_warning_suffix,
    extract_section_mm2,
    format_float,
    format_protection_summary,
    format_trace_float,
    get_breaking_capacity_ka,
    read_template,
    write_text_file,
)

JsonDict = dict[str, Any]


def build_detailed_results_table(results: list[JsonDict]) -> str:
    """Generate the AEA-compliant detailed summary results table."""
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


def render_detailed_report(results: list[JsonDict]) -> str:
    """Inject the detailed results table into the official memory template."""
    template = read_template()
    table = build_detailed_results_table(results)

    if "{{RESULTS_TABLE}}" not in template:
        msg = "Template missing placeholder '{{RESULTS_TABLE}}'"
        raise ValueError(msg)

    return template.replace("{{RESULTS_TABLE}}", table)


def export_detailed_report(results: list[JsonDict], output_dir: str | Path) -> Path:
    """Render and export the detailed report."""
    content = render_detailed_report(results)
    return write_text_file(output_dir, "EE-MC-WireSizing.md", content)

"""file: src/selma/exporters/executive.py

Executive report exporter.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .utils import write_text_file

JsonDict = dict[str, Any]


def render_executive_report(results: list[JsonDict]) -> str:
    """Generate the simplified executive specification table."""
    headers = ["Circuito", "Destino", "Sección", "Protección"]

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for result in results:
        section = "ERROR" if result.get("status") == "FAILED" else result.get("cable_section", "-")

        row = [
            str(result.get("tag", "-")),
            str(result.get("destination", "-")),
            str(section),
            str(result.get("protection", "-")),
        ]

        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def export_executive_report(results: list[JsonDict], output_dir: str | Path) -> Path:
    """Render and export the executive report."""
    content = render_executive_report(results)
    return write_text_file(output_dir, "results.md", content)

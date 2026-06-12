import re
from copy import deepcopy

import pytest

from selma import SelmaEngine


def build_engine():
    return SelmaEngine(
        standard="aea90364",
        criteria={
            "cos_phi": 0.90,
            "ampacity_margin": 1.00,
        },
    )


def build_common_installation():
    return {
        "installation_method": "B2-2x",
        "material": "Cu",
        "insulation": "PVC",
        "installation_temp_c": 40.0,
        "grouped_circuits": 1,
        "soil_type": "default",
        "wire_burial_depth_m": 0.0,
    }


def build_common_short_circuit():
    return {
        "mode": "skip",
        "Icc_kA": 4.5,
        "time_s": 0.5,
    }


def build_common_cable():
    return {
        "voltage_drop_method": "GDC",
        "reactance_ohm_per_m": 0.0,
        "mode": "auto",
        "section_mm2": None,
    }


def build_circuits():
    circuits = [
        {
            "tag": "C-01",
            "origin": "TPBT",
            "destination": "IUG en Planta Baja",
            "purpose": {"type": "lighting", "subtype": "iug"},
            "electrical": {
                "phase_type": "1PH",
                "voltage_v": 220,
                "parallels": 1,
                "length_m": (
                    15.03
                    + 3.82
                    + 1.67
                    + 1.71
                    + 0.2
                    + 0.78
                    + 0.25
                    + 0.19
                    + 0.52
                    + 0.19
                    + 3.04
                    + 0.84
                    + 0.46
                    + 3.88
                    + 0.84
                    + 0.52
                    + 1.51
                    + 0.78
                    + 0.31
                    + 0.6
                    + 1.21
                    + 7.68
                    + 1.59
                    + 0.67
                    + 4.69
                    + 1.69
                    + 0.87
                ),
                "load": {"value": 2.2, "unit": "kVA"},
            },
            "installation": build_common_installation(),
            "short_circuit": build_common_short_circuit(),
            "cable": build_common_cable(),
        },
        {
            "tag": "C-02",
            "origin": "TPBT",
            "destination": "IUG en Planta Alta",
            "purpose": {"type": "lighting", "subtype": "iug"},
            "electrical": {
                "phase_type": "1PH",
                "voltage_v": 220,
                "parallels": 1,
                "length_m": (
                    7.61
                    + 7.57
                    + 5.32
                    + 2.69
                    + 2.69
                    + 6.58
                    + 3.44
                    + 3.44
                    + 2.39
                    + 1.76
                    + 1.59
                    + 1.26
                    + 5.08
                ),
                "load": {"value": 2.2, "unit": "kVA"},
            },
            "installation": build_common_installation(),
            "short_circuit": build_common_short_circuit(),
            "cable": build_common_cable(),
        },
        {
            "tag": "C-03",
            "origin": "TPBT",
            "destination": "TUG en Planta Baja",
            "purpose": {"type": "outlet", "subtype": "tug"},
            "electrical": {
                "phase_type": "1PH",
                "voltage_v": 220,
                "parallels": 1,
                "length_m": 50.0,
                "load": {"value": 2.2, "unit": "kVA"},
            },
            "installation": build_common_installation(),
            "short_circuit": build_common_short_circuit(),
            "cable": build_common_cable(),
        },
        {
            "tag": "C-04",
            "origin": "TPBT",
            "destination": "TUG en Planta Alta",
            "purpose": {"type": "outlet", "subtype": "tug"},
            "electrical": {
                "phase_type": "1PH",
                "voltage_v": 220,
                "parallels": 1,
                "length_m": 50.0,
                "load": {"value": 2.2, "unit": "kVA"},
            },
            "installation": build_common_installation(),
            "short_circuit": build_common_short_circuit(),
            "cable": build_common_cable(),
        },
        {
            "tag": "C-05",
            "origin": "TPBT",
            "destination": "TUE en Planta Baja",
            "purpose": {"type": "outlet", "subtype": "tue"},
            "electrical": {
                "phase_type": "1PH",
                "voltage_v": 220,
                "parallels": 1,
                "length_m": 50.0,
                "load": {"value": 3.3, "unit": "kVA"},
            },
            "installation": build_common_installation(),
            "short_circuit": build_common_short_circuit(),
            "cable": build_common_cable(),
        },
        {
            "tag": "C-06",
            "origin": "TPBT",
            "destination": "TUE en Planta Alta",
            "purpose": {"type": "outlet", "subtype": "tue"},
            "electrical": {
                "phase_type": "1PH",
                "voltage_v": 220,
                "parallels": 1,
                "length_m": 50.0,
                "load": {"value": 3.3, "unit": "kVA"},
            },
            "installation": build_common_installation(),
            "short_circuit": build_common_short_circuit(),
            "cable": build_common_cable(),
        },
    ]

    for i in range(7, 11):
        circuits.append(
            {
                "tag": f"C-{i:02d}",
                "origin": "TPBT",
                "destination": "ACU para Aires Acondicionados",
                "purpose": {"type": "motor", "subtype": "direct"},
                "electrical": {
                    "phase_type": "1PH",
                    "voltage_v": 220,
                    "parallels": 1,
                    "length_m": (3.83 + 7 + 14.16 + 1),
                    "load": {"value": 14, "unit": "A"},
                },
                "installation": build_common_installation(),
                "short_circuit": build_common_short_circuit(),
                "cable": build_common_cable(),
            },
        )

    return circuits


def parse_cable_section_and_pe(cable_section: str) -> tuple[float, float]:
    match = re.search(r"[23]x([0-9]+(?:\.[0-9]+)?)mm² \+ PE([0-9]+(?:\.[0-9]+)?)mm²", cable_section)
    if match is None:
        raise AssertionError(f"Formato de cable inválido: {cable_section}")
    return float(match.group(1)), float(match.group(2))


def min_section_for_purpose(purpose: dict) -> float:
    if purpose["type"] == "lighting":
        return 1.5
    return 2.5


def expected_pe(phase_section: float) -> float:
    if phase_section <= 16:
        return phase_section
    if phase_section <= 35:
        return 16.0
    return phase_section / 2.0


@pytest.fixture(scope="module")
def engine():
    return build_engine()


@pytest.fixture(scope="module")
def circuits():
    return build_circuits()


@pytest.mark.parametrize("circuit", build_circuits(), ids=lambda c: c["tag"])
def test_single_circuit_regulatory_constraints(engine, circuit):
    result = engine.size_project([deepcopy(circuit)])[0]

    assert result["status"] == "OK"
    assert all(result["checks"].values())

    trace = result["trace"]
    phase_section, pe_section = parse_cable_section_and_pe(result["cable_section"])

    assert result["current_a"] > 0.0
    assert phase_section >= min_section_for_purpose(circuit["purpose"])
    assert phase_section == pytest.approx(float(trace["final_section_mm2"]))
    assert pe_section == pytest.approx(float(result["pe_section_mm2"]))
    assert pe_section == pytest.approx(expected_pe(phase_section))

    assert float(trace["final_Iz_corrected_total_a"]) >= float(trace["Ib_design"])
    assert float(trace["final_protection_in_a"]) >= float(trace["Ib_design"])
    assert float(trace["final_protection_in_a"]) <= float(trace["final_Iz_corrected_total_a"])
    assert float(trace["final_protection_i2_a"]) <= 1.45 * float(
        trace["final_Iz_corrected_total_a"],
    )

    assert float(trace["final_voltage_drop_pct"]) <= float(trace["max_voltage_drop_pct"])
    assert float(result["voltage_drop_pct"]) == pytest.approx(
        float(trace["final_voltage_drop_pct"]),
    )

    assert phase_section >= float(trace["selected_by_ampacity_mm2"])
    assert phase_section >= float(trace["selected_by_vdrop_mm2"])
    assert phase_section >= float(trace["selected_by_short_circuit_mm2"])

    assert result["protection"] != "N/A"
    assert result["cable_section"] != "N/A"


def test_project_batch_regulatory_constraints(engine, circuits):
    results = engine.size_project(deepcopy(circuits))

    assert len(results) == 10
    assert all(r["status"] == "OK" for r in results)
    assert all(all(r["checks"].values()) for r in results)

    for result in results:
        trace = result["trace"]
        phase_section, pe_section = parse_cable_section_and_pe(result["cable_section"])

        assert result["current_a"] > 0.0
        assert result["protection"] != "N/A"
        assert result["cable_section"] != "N/A"

        assert phase_section == pytest.approx(float(trace["final_section_mm2"]))
        assert pe_section == pytest.approx(float(result["pe_section_mm2"]))
        assert pe_section == pytest.approx(expected_pe(phase_section))

        assert float(trace["final_voltage_drop_pct"]) <= float(trace["max_voltage_drop_pct"])
        assert float(trace["final_Iz_corrected_total_a"]) >= float(trace["Ib_design"])
        assert float(trace["final_protection_in_a"]) <= float(trace["final_Iz_corrected_total_a"])


def test_engine_is_deterministic(engine, circuits):
    results_a = engine.size_project(deepcopy(circuits))
    results_b = engine.size_project(deepcopy(circuits))

    projection_a = [
        (
            r["tag"],
            r["status"],
            r["cable_section"],
            r["protection"],
            round(float(r["voltage_drop_pct"]), 6),
            round(float(r["trace"]["final_section_mm2"]), 6),
            round(float(r["trace"]["final_Iz_corrected_total_a"]), 6),
            int(r["trace"]["final_protection_in_a"]),
        )
        for r in results_a
    ]

    projection_b = [
        (
            r["tag"],
            r["status"],
            r["cable_section"],
            r["protection"],
            round(float(r["voltage_drop_pct"]), 6),
            round(float(r["trace"]["final_section_mm2"]), 6),
            round(float(r["trace"]["final_Iz_corrected_total_a"]), 6),
            int(r["trace"]["final_protection_in_a"]),
        )
        for r in results_b
    ]

    assert projection_a == projection_b


def test_reports_render_all_tags(engine, circuits):
    results = engine.size_project(deepcopy(circuits))

    detailed = engine.render_detailed_report(results)
    executive = engine.render_executive_report(results)
    visual = engine.render_visual_report(results)

    for circuit in circuits:
        tag = circuit["tag"]
        assert tag in detailed
        assert tag in executive
        assert tag in visual


def test_export_reports(engine, circuits, tmp_path):
    results = engine.size_project(deepcopy(circuits))
    exported = engine.export_reports(results, tmp_path)

    assert exported["detailed"].exists()
    assert exported["executive"].exists()
    assert exported["visual"].exists()

    detailed_text = exported["detailed"].read_text(encoding="utf-8")
    executive_text = exported["executive"].read_text(encoding="utf-8")
    visual_text = exported["visual"].read_text(encoding="utf-8")

    assert "C-01" in detailed_text
    assert "C-10" in detailed_text
    assert "C-01" in executive_text
    assert "C-10" in executive_text
    assert "C-01" in visual_text
    assert "C-10" in visual_text

from selma import SelmaEngine

engine = SelmaEngine(
    standard="aea90364",
    criteria={"cos_phi": 0.9, "ampacity_margin": 1.0},
)

circuits = [
    {
        "tag": "C-01",
        "origin": "TAB",
        "destination": "Iluminación Piso 1",
        "purpose": {"type": "lighting", "subtype": "iug"},
        "electrical": {
            "phase_type": "1PH",
            "voltage_v": 220,
            "parallels": 1,
            "length_m": 40,
            "load": {"value": 2.0, "unit": "kVA"},
        },
        "installation": {
            "installation_method": "B2-2x",
            "material": "Cu",
            "insulation": "PVC",
            "installation_temp_c": 35,
            "grouped_circuits": 2,
            "soil_type": "default",
            "wire_burial_depth_m": 0.0,
        },
        "short_circuit": {"mode": "skip", "Icc_kA": 4, "time_s": 0.3},
        "cable": {"voltage_drop_method": "GDC", "reactance_ohm_per_m": 0.0, "mode": "auto", "section_mm2": None},
    },
    {
        "tag": "C-02",
        "origin": "TAB",
        "destination": "Tomas",
        "purpose": {"type": "outlet", "subtype": "tug"},
        "electrical": {
            "phase_type": "1PH",
            "voltage_v": 220,
            "parallels": 1,
            "length_m": 50,
            "load": {"value": 2.5, "unit": "kVA"},
        },
        "installation": {
            "installation_method": "B2-2x",
            "material": "Cu",
            "insulation": "PVC",
            "installation_temp_c": 35,
            "grouped_circuits": 2,
            "soil_type": "default",
            "wire_burial_depth_m": 0.0,
        },
        "short_circuit": {"mode": "skip", "Icc_kA": 4, "time_s": 0.3},
        "cable": {"voltage_drop_method": "IMPEDANCE", "reactance_ohm_per_m": 0.08, "mode": "auto", "section_mm2": None},
    },
]

results = engine.size_project(circuits)

print("\nRESULTS")
for r in results:
    print(r["tag"], r["cable_section"], r["protection"], r["voltage_drop_pct"])

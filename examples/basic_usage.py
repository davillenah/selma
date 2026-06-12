from selma import SelmaEngine

engine = SelmaEngine(
    standard="aea90364",
    criteria={"cos_phi": 0.9, "ampacity_margin": 1.0},
)

circuits = [
    {
        "tag": "C-01",
        "origin": "TAB",
        "destination": "Iluminación",
        "purpose": {"type": "lighting", "subtype": "iug"},
        "electrical": {
            "phase_type": "1PH",
            "voltage_v": 220,
            "parallels": 1,
            "length_m": 25.0,
            "load": {"value": 1.5, "unit": "kVA"},
        },
        "installation": {
            "installation_method": "B2-2x",
            "material": "Cu",
            "insulation": "PVC",
            "installation_temp_c": 30,
            "grouped_circuits": 1,
            "soil_type": "default",
            "wire_burial_depth_m": 0.0,
        },
        "short_circuit": {"mode": "skip", "Icc_kA": 3, "time_s": 0.2},
        "cable": {
            "voltage_drop_method": "GDC",
            "reactance_ohm_per_m": 0.0,
            "mode": "auto",
            "section_mm2": None,
        },
    },
]

results = engine.size_project(circuits)

print("\nRESULTS")
for r in results:
    print(r["tag"], r["cable_section"], r["protection"], r["voltage_drop_pct"])

from copy import deepcopy

from selma import SelmaEngine

engine = SelmaEngine(
    standard="aea90364",
    criteria={"cos_phi": 0.9, "ampacity_margin": 1.1},
)

base_motor = {
    "origin": "TAB",
    "destination": "Equipos HVAC",
    "purpose": {"type": "motor", "subtype": "direct"},
    "electrical": {
        "phase_type": "3PH",
        "voltage_v": 380,
        "parallels": 1,
        "length_m": 60,
        "load": {"value": 10, "unit": "kVA"},
    },
    "installation": {
        "installation_method": "C-3x",
        "material": "Cu",
        "insulation": "XLPE",
        "installation_temp_c": 40,
        "grouped_circuits": 3,
        "soil_type": "default",
        "wire_burial_depth_m": 0.0,
    },
    "short_circuit": {"mode": "board_icc", "Icc_kA": 6, "time_s": 0.4},
    "cable": {
        "voltage_drop_method": "IMPEDANCE",
        "reactance_ohm_per_m": 0.08,
        "mode": "auto",
        "section_mm2": None,
    },
}

circuits = []

for i in range(1, 6):
    c = deepcopy(base_motor)
    c["tag"] = f"M-{i:02d}"
    c["electrical"]["load"]["value"] = 8 + i
    circuits.append(c)

results = engine.size_project(circuits)

print("\nRESULTS")
for r in results:
    print(
        r["tag"],
        r["cable_section"],
        r["protection"],
        round(r["voltage_drop_pct"], 2),
    )

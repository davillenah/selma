"""file: src/selma/validation/input.py

Enhanced validation with purpose {type, subtype} support.

Backward compatible with legacy string purpose.
"""

# ===============================
# ALLOWED VALUES
# ===============================

ALLOWED_PURPOSE_TYPES = {
    "board",
    "power",
    "lighting",
    "control",
    "signal",
    "motor",
    "outlet",
}

ALLOWED_SUBTYPES = {
    "board": {"main", "distribution", "submain"},
    "lighting": {"iug", "iue"},
    "outlet": {"tug", "tue"},
    "power": {"general", "acu", "equipment"},
    "motor": {"direct", "heavy"},
    "control": {"plc", "relay"},
    "signal": {"analog", "digital", "communication"},
}

ALLOWED_PHASE_TYPES = {"1PH", "3PH"}
ALLOWED_MATERIALS = {"Cu", "Al"}
ALLOWED_INSULATION = {"PVC", "XLPE"}

ALLOWED_LOAD_UNITS = {
    "A",
    "W",
    "kW",
    "MW",
    "VA",
    "kVA",
    "MVA",
    "HP",
}

ALLOWED_SOIL_TYPES = {
    "default",
    "sand_dry",
    "sand_wet",
    "clay_dry",
    "clay_wet",
    "organic",
    "peat_wet",
    "gravel_dry",
    "stabilized_backfill",
}

VALID_METHODS = {
    "B1-2x",
    "B1-3x",
    "B2-2x",
    "B2-3x",
    "C-2x",
    "C-3x",
    "E-2x",
    "E-3x",
    "F-2x",
    "F-3xT",
    "F-3xP",
    "G-3xH",
    "G-3xV",
    "D1-2x",
    "D1-3x",
    "D2-1x",
    "D2-2xA",
    "D2-2xB",
    "D2-3xA",
    "D2-3xB",
}

# ===============================
# REQUIRED KEYS
# ===============================

REQUIRED_CIRCUIT_KEYS = {
    "tag",
    "origin",
    "destination",
    "purpose",
    "electrical",
    "short_circuit",
    "installation",
    "cable",
}

# ===============================
# UTILS
# ===============================


def _require_keys(obj: dict, keys: set, where: str) -> None:
    missing = [k for k in keys if k not in obj]
    if missing:
        raise ValueError(f"Missing keys in {where}: {', '.join(missing)}")


def _is_positive_number(value) -> bool:
    return isinstance(value, (int, float)) and value > 0


def _normalize_purpose(circuit: dict, tag: str) -> dict:
    """Normalize purpose into {type, subtype} format.

    Supports:
    - string input → legacy
    - dict input → new model
    """
    raw = circuit.get("purpose")

    # -------------------------
    # Legacy string
    # -------------------------
    if isinstance(raw, str):
        p_type = raw.strip().lower()

        if p_type not in ALLOWED_PURPOSE_TYPES:
            raise ValueError(f"{tag}: invalid purpose '{raw}'")

        purpose = {"type": p_type, "subtype": None}

    # -------------------------
    # New structured purpose
    # -------------------------
    elif isinstance(raw, dict):
        if "type" not in raw:
            raise ValueError(f"{tag}: purpose requires 'type'")

        p_type = str(raw["type"]).strip().lower()

        if p_type not in ALLOWED_PURPOSE_TYPES:
            raise ValueError(f"{tag}: invalid purpose.type '{p_type}'")

        subtype = raw.get("subtype")

        if subtype is not None:
            subtype = str(subtype).strip().lower()

            valid_subtypes = ALLOWED_SUBTYPES.get(p_type)

            if valid_subtypes and subtype not in valid_subtypes:
                raise ValueError(f"{tag}: invalid subtype '{subtype}' for type '{p_type}'")

        purpose = {"type": p_type, "subtype": subtype}

    else:
        raise ValueError(f"{tag}: invalid purpose format")

    # ✅ overwrite normalized purpose
    circuit["purpose"] = purpose

    return purpose


# ===============================
# VALIDATION CORE
# ===============================


def validate_circuit(circuit: dict) -> None:
    tag = circuit.get("tag", "?")

    _require_keys(circuit, REQUIRED_CIRCUIT_KEYS, f"circuit '{tag}'")

    # ✅ PURPOSE NORMALIZATION (NEW CENTRAL POINT)
    _purpose = _normalize_purpose(circuit, tag)

    # ---- rest of your validation stays identical ----
    # 👇 no tocamos el resto (esto evita romper cosas)

    e = circuit["electrical"]
    inst = circuit["installation"]
    cable = circuit["cable"]
    sc = circuit["short_circuit"]
    load = e["load"]
    method = inst["installation_method"]

    if e["phase_type"] not in ALLOWED_PHASE_TYPES:
        raise ValueError(f"{tag}: invalid phase_type '{e['phase_type']}'")

    if not _is_positive_number(e["voltage_v"]):
        raise ValueError(f"{tag}: voltage_v must be > 0")

    if not _is_positive_number(e["length_m"]):
        raise ValueError(f"{tag}: length_m must be > 0")

    if not isinstance(e["parallels"], int) or e["parallels"] < 1:
        raise ValueError(f"{tag}: parallels must be >= 1")

    _require_keys(load, {"value", "unit"}, f"{tag}.electrical.load")

    if load["unit"] not in ALLOWED_LOAD_UNITS:
        raise ValueError(f"{tag}: invalid load unit '{load['unit']}'")

    if not _is_positive_number(load["value"]):
        raise ValueError(f"{tag}: load value must be > 0")

    if inst["material"] not in ALLOWED_MATERIALS:
        raise ValueError(f"{tag}: invalid material '{inst['material']}'")

    if inst["insulation"] not in ALLOWED_INSULATION:
        raise ValueError(f"{tag}: invalid insulation '{inst['insulation']}'")

    if method not in VALID_METHODS:
        raise ValueError(f"{tag}: invalid installation_method '{method}'")

    if not _is_positive_number(inst["installation_temp_c"]):
        raise ValueError(f"{tag}: installation_temp_c must be > 0")

    if not isinstance(inst["grouped_circuits"], int) or inst["grouped_circuits"] < 1:
        raise ValueError(f"{tag}: grouped_circuits must be >= 1")

    if not _is_positive_number(sc["Icc_kA"]):
        raise ValueError(f"{tag}: short_circuit.Icc_kA must be > 0")

    if not _is_positive_number(sc["time_s"]):
        raise ValueError(f"{tag}: short_circuit.time_s must be > 0")

    if cable["mode"] not in {"auto", "fixed"}:
        raise ValueError(f"{tag}: cable.mode must be 'auto' or 'fixed'")

    if cable["mode"] == "fixed" and not _is_positive_number(cable["section_mm2"]):
        raise ValueError(f"{tag}: cable.section_mm2 must be > 0")


# ===============================
# ENTRY POINT
# ===============================


def validate_inputs(standard: str, circuits: list[dict]) -> None:
    if not isinstance(standard, str) or not standard.strip():
        raise ValueError("STANDARD must be a non-empty string")

    if not circuits:
        raise ValueError("No circuits defined")

    for c in circuits:
        validate_circuit(c)

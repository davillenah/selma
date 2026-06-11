"""
file: src/selma/models/schemas.py

Shared data models for the wire sizing engine.

This module centralizes the immutable input bundles and simple value objects
used across the engine. The goal is to provide a stable contract between
the orchestration layer and the specialized modules (tables, factors,
protection, voltage drop, short circuit, etc.).

Design principles
-----------------
- Immutable models via dataclasses with ``frozen=True``
- Small, explicit, highly cohesive value objects
- No business logic inside models
- Clear type annotations for maintainability and static analysis
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ============================================================
# DATA CLASSES
# ============================================================


@dataclass(frozen=True)
class MethodSelection:
    """Represent a parsed AEA installation method.

    Example
    -------
    ``D2-3xA`` -> ``family="D2"``, ``column="3xA"``
    """

    family: str
    column: str


@dataclass(frozen=True)
class AmpacityRequest:
    """Describe the ampacity table query required by the engine."""

    material: str
    insulation: str
    method_family: str
    method_column: str


@dataclass(frozen=True)
class ProtectionSelection:
    """Represent the selected overcurrent protective device.

    Attributes
    ----------
    in_a:
        Nominal current of the protective device.
    i2_a:
        Conventional operating current used for overload verification.
    device_type:
        Simplified family identifier (MCB or MCCB).
    standard:
        Reference product standard used as documentation value.
    curve:
        Simplified curve or trip type descriptor.
    """

    in_a: int
    i2_a: float
    device_type: str
    standard: str
    curve: str


@dataclass(frozen=True)
class AmpacitySelectionInput:
    """Bundle inputs for ampacity and protection-based section selection."""

    rows: list[dict[str, Any]]
    method_column: str
    sections: list[float]
    installation_factor: float
    parallels: int
    symmetry_factor: float
    ib_design: float
    min_section_mm2: float


@dataclass(frozen=True)
class VoltageDropSelectionInput:
    """Bundle inputs for voltage-drop-based section selection."""

    sections: list[float]
    selected_by_ampacity_mm2: float
    min_section_mm2: float
    max_vdrop_pct: float
    electrical: dict[str, Any]
    installation: dict[str, Any]
    cable: dict[str, Any]
    ib: float
    cos_phi: float


@dataclass(frozen=True)
class ShortCircuitSelectionInput:
    """Bundle inputs for short-circuit-based section selection.

    This model allows the short-circuit engine to work in multiple modes
    without coupling the orchestration layer to the internal implementation.

    Supported modes
    ---------------
    The ``short_circuit`` dictionary is expected to include:

    - ``mode = "manual"``
        Uses the explicit ``Icc_kA`` and ``time_s`` provided in the circuit.
    - ``mode = "board_icc"``
        Uses ``board_Icc_kA`` and attenuates the fault current through the
        circuit cable impedance for each candidate section.
    - ``mode = "skip"``
        Ignores short-circuit sizing as a governing criterion.

    Notes
    -----
    This dataclass does not validate the input structure itself. That remains
    the responsibility of the validators and the engine.
    """

    rows: list[dict[str, Any]]
    method_column: str
    sections: list[float]
    min_section_mm2: float
    constants: dict[str, Any]
    electrical: dict[str, Any]
    installation: dict[str, Any]
    cable: dict[str, Any]
    short_circuit: dict[str, Any]
    parallels: int
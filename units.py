"""
Unit conversion helpers for engineering calculators.

Internal base units used by the calculator:
- length: mm
- area: mm²
- volume: mm³
- second moment of area / inertia: mm⁴
- force: N
- stress/modulus: MPa = N/mm²
- mass: kg
"""

from __future__ import annotations

from typing import Mapping


LENGTH_TO_MM: dict[str, float] = {
    "mm": 1.0,
    "cm": 10.0,
    "m": 1000.0,
    "in": 25.4,
    "ft": 304.8,
    "yd": 914.4,
}

AREA_TO_MM2 = {
    "mm²": 1.0,
    "cm²": 100.0,
    "m²": 1e6,
    "in²": 25.4**2,
    "ft²": 304.8**2,
}

VOLUME_TO_MM3: dict[str, float] = {
    "mm³": 1.0,
    "cm³": 1000.0,
    "m³": 1e9,
    "in³": 25.4**3,
    "ft³": 304.8**3,
}

INERTIA_TO_MM4: dict[str, float] = {
    "mm⁴": 1.0,
    "cm⁴": 10_000.0,
    "m⁴": 1e12,
    "in⁴": 25.4**4,
    "ft⁴": 304.8**4,
}

FORCE_TO_N: dict[str, float] = {
    "N": 1.0,
    "kN": 1000.0,
    "lbf": 4.4482216152605,
    "kip": 4448.2216152605,
}

STRESS_TO_MPA: dict[str, float] = {
    "MPa": 1.0,
    "Pa": 1e-6,
    "kPa": 1e-3,
    "GPa": 1000.0,
    "psi": 0.006894757293168,
    "ksi": 6.894757293168,
}

MASS_TO_KG: dict[str, float] = {
    "kg": 1.0,
    "t": 1000.0,
    "tonne": 1000.0,
    "tons": 1000.0,
    "lbm": 0.45359237,
    "slug": 14.59390294,
}


UNIT_GROUPS: dict[str, dict[str, float]] = {
    "length": LENGTH_TO_MM,
    "area": AREA_TO_MM2,
    "volume": VOLUME_TO_MM3,
    "inertia": INERTIA_TO_MM4,
    "force": FORCE_TO_N,
    "stress": STRESS_TO_MPA,
    "modulus": STRESS_TO_MPA,
    "mass": MASS_TO_KG,
}


BASE_UNITS: dict[str, str] = {
    "length": "mm",
    "area": "mm²",
    "volume": "mm³",
    "inertia": "mm⁴",
    "force": "N",
    "stress": "MPa",
    "modulus": "MPa",
    "mass": "kg",
}


def _validate_unit(unit: str, factors: Mapping[str, float]) -> None:
    if unit not in factors:
        allowed = ", ".join(factors.keys())
        raise ValueError(f"Unsupported unit '{unit}'. Allowed units: {allowed}")


def to_base(value: float, unit: str, factors: Mapping[str, float]) -> float:
    """Convert value from selected unit to the group's internal base unit."""
    _validate_unit(unit, factors)
    return value * factors[unit]


def from_base(value: float, unit: str, factors: Mapping[str, float]) -> float:
    """Convert value from the group's internal base unit to selected unit."""
    _validate_unit(unit, factors)
    return value / factors[unit]


def convert(value: float, from_unit: str, to_unit: str, factors: Mapping[str, float]) -> float:
    """Convert value between two units from the same unit group."""
    base_value = to_base(value, from_unit, factors)
    return from_base(base_value, to_unit, factors)


# Convenience functions used by the Streamlit app.
def length_to_mm(value: float, unit: str) -> float:
    return to_base(value, unit, LENGTH_TO_MM)


def mm_to_length(value: float, unit: str) -> float:
    return from_base(value, unit, LENGTH_TO_MM)


def area_to_mm2(value: float, unit: str) -> float:
    return to_base(value, unit, AREA_TO_MM2)


def mm2_to_area(value: float, unit: str) -> float:
    return from_base(value, unit, AREA_TO_MM2)


def inertia_to_mm4(value: float, unit: str) -> float:
    return to_base(value, unit, INERTIA_TO_MM4)


def mm4_to_inertia(value: float, unit: str) -> float:
    return from_base(value, unit, INERTIA_TO_MM4)


def force_to_n(value: float, unit: str) -> float:
    return to_base(value, unit, FORCE_TO_N)


def n_to_force(value: float, unit: str) -> float:
    return from_base(value, unit, FORCE_TO_N)


def stress_to_mpa(value: float, unit: str) -> float:
    return to_base(value, unit, STRESS_TO_MPA)


def mpa_to_stress(value: float, unit: str) -> float:
    return from_base(value, unit, STRESS_TO_MPA)


def modulus_to_mpa(value: float, unit: str) -> float:
    return stress_to_mpa(value, unit)


def mpa_to_modulus(value: float, unit: str) -> float:
    return mpa_to_stress(value, unit)


def mass_to_kg(value: float, unit: str) -> float:
    return to_base(value, unit, MASS_TO_KG)


def kg_to_mass(value: float, unit: str) -> float:
    return from_base(value, unit, MASS_TO_KG)


def unit_options(group: str) -> list[str]:
    """Return available units for a unit group, useful for Streamlit selectboxes."""
    if group not in UNIT_GROUPS:
        allowed = ", ".join(UNIT_GROUPS.keys())
        raise ValueError(f"Unsupported unit group '{group}'. Allowed groups: {allowed}")
    return list(UNIT_GROUPS[group].keys())

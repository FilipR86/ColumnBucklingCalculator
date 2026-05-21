"""
Buckling calculation logic for the column buckling calculator.

Internal units expected:
- E: MPa = N/mm²
- yield strength: MPa = N/mm²
- length/effective length: mm
- area: mm²
- second moment of area: mm⁴
- force: N

This module contains no Streamlit code. It can be reused by app.py and later by report.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt


@dataclass(frozen=True)
class BucklingResult:
    radius_of_gyration_mm: float
    slenderness_ratio: float
    limiting_slenderness_ratio: float
    relative_slenderness: float
    reduction_factor_chi: float
    critical_stress_mpa: float
    critical_force_n: float
    utilization_percent: float


@dataclass(frozen=True)
class DesignCheckSummary:
    status: str
    message: str


def assert_positive(name: str, value: float) -> None:
    if value is None or value <= 0:
        raise ValueError(f"{name} must be greater than 0.")


def reduction_factor(lambda_k: float, alpha_c: float = 0.49) -> float:
    """DIN 18800-style buckling reduction factor.

    lambda_k is the relative slenderness ratio.
    alpha_c is the imperfection factor for the selected buckling curve.
    """
    assert_positive("Relative slenderness λk", lambda_k)
    assert_positive("Imperfection factor αc", alpha_c)

    kfac = 0.5 * (1 + alpha_c * (lambda_k - 0.2) + lambda_k**2)

    if lambda_k <= 0.2:
        return 1.0

    if lambda_k <= 3.0:
        return 1 / (kfac + sqrt(kfac**2 - lambda_k**2))

    return 1 / (lambda_k * (lambda_k + alpha_c))


def calculate_buckling(
    *,
    elastic_modulus_mpa: float,
    yield_strength_mpa: float,
    effective_length_mm: float,
    area_mm2: float,
    inertia_mm4: float,
    compression_force_n: float,
    alpha_c: float = 0.49,
    design_factor: float = 0.90,
) -> BucklingResult:
    """Calculate column buckling values.

    Returns all core result values in internal units.
    """
    assert_positive("Elastic modulus E", elastic_modulus_mpa)
    assert_positive("Yield strength YS", yield_strength_mpa)
    assert_positive("Effective length Leff", effective_length_mm)
    assert_positive("Cross-sectional area A", area_mm2)
    assert_positive("Second moment of area I", inertia_mm4)
    assert_positive("Compression force Fcompr", compression_force_n)
    assert_positive("Design factor", design_factor)

    radius_of_gyration_mm = sqrt(inertia_mm4 / area_mm2)
    slenderness_ratio = effective_length_mm / radius_of_gyration_mm
    limiting_slenderness_ratio = sqrt(pi**2 * elastic_modulus_mpa / yield_strength_mpa)
    relative_slenderness = slenderness_ratio / limiting_slenderness_ratio
    chi = reduction_factor(relative_slenderness, alpha_c)
    critical_stress_mpa = chi * design_factor * yield_strength_mpa
    critical_force_n = critical_stress_mpa * area_mm2
    utilization_percent = compression_force_n / critical_force_n * 100

    return BucklingResult(
        radius_of_gyration_mm=radius_of_gyration_mm,
        slenderness_ratio=slenderness_ratio,
        limiting_slenderness_ratio=limiting_slenderness_ratio,
        relative_slenderness=relative_slenderness,
        reduction_factor_chi=chi,
        critical_stress_mpa=critical_stress_mpa,
        critical_force_n=critical_force_n,
        utilization_percent=utilization_percent,
    )


def critical_stress_for_slenderness(
    *,
    slenderness_ratio: float,
    limiting_slenderness_ratio: float,
    yield_strength_mpa: float,
    alpha_c: float = 0.49,
    design_factor: float = 0.90,
) -> float:
    """Return critical stress in MPa for a given slenderness ratio λ."""
    assert_positive("Slenderness ratio λ", slenderness_ratio)
    assert_positive("Limiting slenderness ratio λeH", limiting_slenderness_ratio)
    assert_positive("Yield strength YS", yield_strength_mpa)

    lambda_k = slenderness_ratio / limiting_slenderness_ratio
    return reduction_factor(lambda_k, alpha_c) * design_factor * yield_strength_mpa


def design_check_summary(
    *,
    utilization_percent: float,
    slenderness_ratio: float,
    slenderness_limit: float = 90.0,
    bending_moment_expected: bool = False,
) -> DesignCheckSummary:
    """Return unified design-check status and message.

    status values:
    - success
    - warning
    - error
    """
    force_ok = utilization_percent <= 100
    slenderness_warning = slenderness_ratio > slenderness_limit

    if force_ok and not slenderness_warning:
        return DesignCheckSummary(
            status="success",
            message=(
                "Design check summary: The selected column is adequate for the entered axial "
                "compression force, and the slenderness ratio is below the caution limit of 90."
            ),
        )

    if force_ok and slenderness_warning:
        if bending_moment_expected:
            return DesignCheckSummary(
                status="warning",
                message=(
                    "Design check summary: The selected column has enough axial buckling resistance "
                    "for the entered compression force, but the slenderness ratio is above 90. "
                    "It may still be acceptable, but higher safety is recommended. Since bending "
                    "moment is expected, a combined compression + bending check should be performed."
                ),
            )

        return DesignCheckSummary(
            status="warning",
            message=(
                "Design check summary: The selected column has enough axial buckling resistance "
                "for the entered compression force, but the slenderness ratio is above 90. "
                "It may still be acceptable, but higher safety is recommended."
            ),
        )

    if not force_ok and slenderness_warning:
        return DesignCheckSummary(
            status="error",
            message=(
                "Design check summary: The selected column is NOT adequate. The utilization is "
                "above 100%, and the slenderness ratio is also above 90."
            ),
        )

    return DesignCheckSummary(
        status="error",
        message=(
            "Design check summary: The selected column is NOT adequate. The utilization is above 100%."
        ),
    )

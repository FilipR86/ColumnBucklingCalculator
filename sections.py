"""
Section profile utilities for the column buckling calculator.

This module keeps section data handling separate from app.py.
It uses Flanged_steel_sections.py as the profile database.

Internal units returned:
- Area A: mm²
- Second moment of area I: mm⁴
- Dimensions: mm
"""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

import Flanged_steel_sections as fss


FLANGED_PROFILE_LIBRARY: dict[str, dict] = {
    "HEA": fss.HEA,
    "HEB": fss.HEB,
    "HEM": fss.HEM,
    "IPE": fss.IPE,
    "UB - Universal Beam": fss.UB,
    "UC - Universal Column": fss.UC,
}


FLANGED_DIMENSION_KEYS = {
    "h": "Depth h [mm]",
    "b": "Width b [mm]",
    "tw": "Web thickness tw [mm]",
    "tf": "Flange thickness tf [mm]",
    "area": "Area [mm2]",
    "iy": "Second moment of area Iy [×10^6 mm4]",
    "iz": "Second moment of area Iz [×10^6 mm4]",
    "wy": "Elastic section modulus Wel,y [×10^3 mm3]",
    "wz": "Elastic section modulus Wel,z [×10^3 mm3]",
}


def get_flanged_profile_names(profile_type: str) -> list[str]:
    """Return available profile names for HEA, HEB, HEM, IPE, UB, or UC."""
    if profile_type not in FLANGED_PROFILE_LIBRARY:
        raise ValueError(f"Unsupported flanged profile type: {profile_type}")

    return list(FLANGED_PROFILE_LIBRARY[profile_type].keys())


def get_flanged_profile_data(profile_type: str, profile_name: str) -> dict:
    """Return raw profile data from Flanged_steel_sections.py."""
    if profile_type not in FLANGED_PROFILE_LIBRARY:
        raise ValueError(f"Unsupported flanged profile type: {profile_type}")

    profile_dict = FLANGED_PROFILE_LIBRARY[profile_type]

    if profile_name not in profile_dict:
        raise ValueError(f"Profile '{profile_name}' not found in {profile_type} library.")

    return profile_dict[profile_name]


def get_flanged_dimensions(profile_data: dict) -> dict[str, float]:
    """Extract main geometric dimensions from raw flanged profile data."""
    return {
        "h_mm": float(profile_data[FLANGED_DIMENSION_KEYS["h"]]),
        "b_mm": float(profile_data[FLANGED_DIMENSION_KEYS["b"]]),
        "tw_mm": float(profile_data[FLANGED_DIMENSION_KEYS["tw"]]),
        "tf_mm": float(profile_data[FLANGED_DIMENSION_KEYS["tf"]]),
    }


def get_flanged_properties(profile_data: dict) -> dict[str, float]:
    """Extract section properties from raw flanged profile data."""
    return {
        "area_mm2": float(profile_data[FLANGED_DIMENSION_KEYS["area"]]),
        "iy_mm4": float(profile_data[FLANGED_DIMENSION_KEYS["iy"]]) * 1e6,
        "iz_mm4": float(profile_data[FLANGED_DIMENSION_KEYS["iz"]]) * 1e6,
        "wy_mm3": float(profile_data.get(FLANGED_DIMENSION_KEYS["wy"], 0.0)) * 1e3,
        "wz_mm3": float(profile_data.get(FLANGED_DIMENSION_KEYS["wz"], 0.0)) * 1e3,
    }


def draw_flanged_section(profile_data: dict, profile_name: str = ""):
    """
    Draw a simplified flanged I/H cross-section.

    Root radii are intentionally ignored for the first version.
    The sketch is proportional to h, b, tw, and tf from the profile database.
    """
    dims = get_flanged_dimensions(profile_data)

    h = dims["h_mm"]
    b = dims["b_mm"]
    tw = dims["tw_mm"]
    tf = dims["tf_mm"]

    if h <= 0 or b <= 0 or tw <= 0 or tf <= 0:
        raise ValueError("Profile dimensions must be positive.")

    if 2 * tf >= h:
        raise ValueError("Invalid profile dimensions: 2 × tf must be smaller than h.")

    fig, ax = plt.subplots(figsize=(4.5, 5.0))

    # Coordinate system centered at section centroid.
    x_left_flange = -b / 2
    x_left_web = -tw / 2
    y_bottom = -h / 2
    y_top_flange_bottom = h / 2 - tf
    y_web_bottom = -h / 2 + tf

    # Bottom flange
    ax.add_patch(
        Rectangle(
            (x_left_flange, y_bottom),
            b,
            tf,
            fill=False,
            linewidth=2,
        )
    )

    # Web
    ax.add_patch(
        Rectangle(
            (x_left_web, y_web_bottom),
            tw,
            h - 2 * tf,
            fill=False,
            linewidth=2,
        )
    )

    # Top flange
    ax.add_patch(
        Rectangle(
            (x_left_flange, y_top_flange_bottom),
            b,
            tf,
            fill=False,
            linewidth=2,
        )
    )

    # Centroid axes
    ax.axhline(0, linewidth=0.8, linestyle="--")
    ax.axvline(0, linewidth=0.8, linestyle="--")

    # Axis labels
    label_margin = 0.2 * max(b, h)

    # Horizontal centroid axis
    ax.text(
        -b / 2 - label_margin,
        0,
        "Y-Y",
        ha="right",
        va="center",
        fontsize=10,
        fontweight="bold",
    )
    ax.text(
        b / 2 + label_margin,
        0,
        "Y-Y",
        ha="left",
        va="center",
        fontsize=10,
        fontweight="bold",
    )

    # Vertical centroid axis
    ax.text(
        0,
        h / 2 + label_margin,
        "Z-Z",
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold",
    )
    ax.text(
        0,
        -h / 2 - label_margin,
        "Z-Z",
        ha="center",
        va="top",
        fontsize=10,
        fontweight="bold",
    )

    # Dimension annotations
    ax.annotate(
        f"h = {h:g} mm",
        xy=(b / 2, 0),
        xytext=(b / 2 + 0.32 * max(b, h), 0),
        va="center",
        arrowprops=dict(arrowstyle="<->", linewidth=1),
    )

    ax.annotate(
        f"b = {b:g} mm",
        xy=(0, h / 2),
        xytext=(0, h / 2 + 0.10 * max(b, h)),
        ha="center",
        arrowprops=dict(arrowstyle="<->", linewidth=1),
    )

    ax.text(
        0,
        -h / 2 - 0.12 * max(b, h),
        f"tw = {tw:g} mm    tf = {tf:g} mm",
        ha="center",
        va="top",
    )

    title = f"{profile_name} simplified cross-section" if profile_name else "Simplified flanged cross-section"
    ax.set_title(title)
    ax.set_aspect("equal", adjustable="box")

    margin = 0.45 * max(b, h)
    ax.set_xlim(-b / 2 - margin, b / 2 + margin)
    ax.set_ylim(-h / 2 - margin, h / 2 + margin)
    ax.axis("off")

    fig.tight_layout()
    return fig


def selected_axis_properties(properties: dict[str, float], axis: str) -> tuple[float, float]:
    """
    Return area and selected second moment of area.

    axis:
    - "Y-Y" uses Iy
    - "Z-Z" uses Iz
    """
    area_mm2 = properties["area_mm2"]

    if axis == "Y-Y":
        return area_mm2, properties["iy_mm4"]

    if axis == "Z-Z":
        return area_mm2, properties["iz_mm4"]

    raise ValueError("Axis must be 'Y-Y' or 'Z-Z'.")


# -----------------------------------------------------------------------------
# Parametric section property functions
# -----------------------------------------------------------------------------


def chs_properties(outer_diameter_mm: float, wall_thickness_mm: float) -> dict[str, float]:
    """Circular hollow section / pipe properties."""
    if outer_diameter_mm <= 0 or wall_thickness_mm <= 0:
        raise ValueError("Outer diameter and wall thickness must be positive.")

    if 2 * wall_thickness_mm >= outer_diameter_mm:
        raise ValueError("Wall thickness must be smaller than half the outer diameter.")

    d = outer_diameter_mm
    di = outer_diameter_mm - 2 * wall_thickness_mm

    area_mm2 = 3.141592653589793 / 4 * (d**2 - di**2)
    inertia_mm4 = 3.141592653589793 / 64 * (d**4 - di**4)

    return {
        "area_mm2": area_mm2,
        "iy_mm4": inertia_mm4,
        "iz_mm4": inertia_mm4,
    }


def rhs_properties(width_mm: float, height_mm: float, wall_thickness_mm: float) -> dict[str, float]:
    """Rectangular or square hollow section properties."""
    if width_mm <= 0 or height_mm <= 0 or wall_thickness_mm <= 0:
        raise ValueError("Width, height, and wall thickness must be positive.")

    if 2 * wall_thickness_mm >= min(width_mm, height_mm):
        raise ValueError("Wall thickness must be smaller than half of width and height.")

    b = width_mm
    h = height_mm
    t = wall_thickness_mm
    bi = b - 2 * t
    hi = h - 2 * t

    area_mm2 = b * h - bi * hi
    iy_mm4 = (b * h**3 - bi * hi**3) / 12
    iz_mm4 = (b**3 * h - bi**3 * hi) / 12

    return {
        "area_mm2": area_mm2,
        "iy_mm4": iy_mm4,
        "iz_mm4": iz_mm4,
    }


def flat_bar_properties(width_mm: float, height_mm: float) -> dict[str, float]:
    """Flat rectangular bar / plate properties."""
    if width_mm <= 0 or height_mm <= 0:
        raise ValueError("Width and height must be positive.")

    b = width_mm
    h = height_mm

    area_mm2 = b * h
    iy_mm4 = b * h**3 / 12
    iz_mm4 = b**3 * h / 12

    return {
        "area_mm2": area_mm2,
        "iy_mm4": iy_mm4,
        "iz_mm4": iz_mm4,
    }


def round_bar_properties(diameter_mm: float) -> dict[str, float]:
    """Solid circular bar properties."""
    if diameter_mm <= 0:
        raise ValueError("Diameter must be positive.")

    d = diameter_mm
    area_mm2 = 3.141592653589793 * d**2 / 4
    inertia_mm4 = 3.141592653589793 * d**4 / 64

    return {
        "area_mm2": area_mm2,
        "iy_mm4": inertia_mm4,
        "iz_mm4": inertia_mm4,
    }


# -----------------------------------------------------------------------------
# Parametric section sketch functions
# -----------------------------------------------------------------------------


def _add_centroid_axes(ax, width: float, height: float) -> None:
    """Add Y-Y and Z-Z centroid axes to a section sketch."""
    max_dim = max(width, height)
    label_margin = 0.20 * max_dim

    ax.axhline(0, linewidth=0.8, linestyle="--")
    ax.axvline(0, linewidth=0.8, linestyle="--")

    ax.text(-width / 2 - label_margin, 0, "Y-Y", ha="right", va="center", fontsize=10, fontweight="bold")
    ax.text(width / 2 + label_margin, 0, "Y-Y", ha="left", va="center", fontsize=10, fontweight="bold")
    ax.text(0, height / 2 + label_margin, "Z-Z", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.text(0, -height / 2 - label_margin, "Z-Z", ha="center", va="top", fontsize=10, fontweight="bold")


def _finish_section_plot(fig, ax, width: float, height: float, title: str) -> None:
    """Common plot formatting for section sketches."""
    max_dim = max(width, height)
    margin = 0.40 * max_dim

    ax.set_title(title)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-width / 2 - margin, width / 2 + margin)
    ax.set_ylim(-height / 2 - margin, height / 2 + margin)
    ax.axis("off")
    fig.tight_layout()


def draw_chs_section(outer_diameter_mm: float, wall_thickness_mm: float):
    """Draw circular hollow section / pipe sketch."""
    if outer_diameter_mm <= 0 or wall_thickness_mm <= 0:
        raise ValueError("Outer diameter and wall thickness must be positive.")

    if 2 * wall_thickness_mm >= outer_diameter_mm:
        raise ValueError("Wall thickness must be smaller than half the outer diameter.")

    d = outer_diameter_mm
    di = outer_diameter_mm - 2 * wall_thickness_mm

    fig, ax = plt.subplots(figsize=(4.5, 4.5))

    outer = plt.Circle((0, 0), d / 2, fill=False, linewidth=2)
    inner = plt.Circle((0, 0), di / 2, fill=False, linewidth=2)
    ax.add_patch(outer)
    ax.add_patch(inner)

    _add_centroid_axes(ax, d, d)

    ax.text(0, -d / 2 - 0.12 * d, f"OD = {d:g} mm    t = {wall_thickness_mm:g} mm", ha="center", va="top")

    _finish_section_plot(fig, ax, d, d, "Circular hollow section")
    return fig


def draw_round_bar_section(diameter_mm: float):
    """Draw solid round bar sketch."""
    if diameter_mm <= 0:
        raise ValueError("Diameter must be positive.")

    d = diameter_mm

    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    ax.add_patch(plt.Circle((0, 0), d / 2, fill=False, linewidth=2))

    _add_centroid_axes(ax, d, d)

    ax.text(0, -d / 2 - 0.12 * d, f"d = {d:g} mm", ha="center", va="top")

    _finish_section_plot(fig, ax, d, d, "Round bar")
    return fig


def draw_rhs_section(width_mm: float, height_mm: float, wall_thickness_mm: float):
    """Draw RHS/SHS sketch."""
    if width_mm <= 0 or height_mm <= 0 or wall_thickness_mm <= 0:
        raise ValueError("Width, height, and wall thickness must be positive.")

    if 2 * wall_thickness_mm >= min(width_mm, height_mm):
        raise ValueError("Wall thickness must be smaller than half of width and height.")

    b = width_mm
    h = height_mm
    t = wall_thickness_mm
    bi = b - 2 * t
    hi = h - 2 * t

    fig, ax = plt.subplots(figsize=(4.5, 5.0))

    ax.add_patch(Rectangle((-b / 2, -h / 2), b, h, fill=False, linewidth=2))
    ax.add_patch(Rectangle((-bi / 2, -hi / 2), bi, hi, fill=False, linewidth=2))

    _add_centroid_axes(ax, b, h)

    ax.text(0, -h / 2 - 0.12 * max(b, h), f"b = {b:g} mm    h = {h:g} mm    t = {t:g} mm", ha="center", va="top")

    title = "Square hollow section" if abs(b - h) < 1e-9 else "Rectangular hollow section"
    _finish_section_plot(fig, ax, b, h, title)
    return fig


def draw_flat_bar_section(width_mm: float, height_mm: float):
    """Draw flat bar / plate sketch."""
    if width_mm <= 0 or height_mm <= 0:
        raise ValueError("Width and height must be positive.")

    b = width_mm
    h = height_mm

    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    ax.add_patch(Rectangle((-b / 2, -h / 2), b, h, fill=False, linewidth=2))

    _add_centroid_axes(ax, b, h)

    ax.text(0, -h / 2 - 0.12 * max(b, h), f"b = {b:g} mm    h = {h:g} mm", ha="center", va="top")

    _finish_section_plot(fig, ax, b, h, "Flat bar / plate")
    return fig


def draw_custom_section_placeholder():
    """Placeholder sketch for custom A + I input."""
    fig, ax = plt.subplots(figsize=(4.5, 3.5))

    ax.text(
        0.5,
        0.58,
        "Custom section",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        transform=ax.transAxes,
    )
    ax.text(
        0.5,
        0.42,
        "Sketch unavailable for A + I input",
        ha="center",
        va="center",
        fontsize=10,
        transform=ax.transAxes,
    )

    ax.axis("off")
    fig.tight_layout()
    return fig

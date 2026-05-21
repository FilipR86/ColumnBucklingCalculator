import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from buckling import (
    calculate_buckling,
    critical_stress_for_slenderness,
    design_check_summary,
)

from report import create_pdf_report

from units import (
    unit_options,
    length_to_mm,
    stress_to_mpa,
    modulus_to_mpa,
    force_to_n,
    mm_to_length,
    mm2_to_area,
    mm4_to_inertia,
    area_to_mm2,
    inertia_to_mm4,
    mpa_to_stress,
    n_to_force,
)
from sections import (
    FLANGED_PROFILE_LIBRARY,
    get_flanged_profile_names,
    get_flanged_profile_data,
    get_flanged_properties,
    draw_flanged_section,
    selected_axis_properties,
    chs_properties,
    rhs_properties,
    flat_bar_properties,
    round_bar_properties,
    draw_chs_section,
    draw_rhs_section,
    draw_flat_bar_section,
    draw_round_bar_section,
    draw_custom_section_placeholder,
)


st.set_page_config(
    page_title="Column Buckling Calculator",
    page_icon="🏗️",
    layout="wide",
)


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------


def section_title(title: str) -> None:
    st.markdown(
        f"<p style='font-size:26px; text-decoration: underline;'>{title}</p>",
        unsafe_allow_html=True,
    )


def display_section_properties(
    A: float,
    Iy: float,
    Iz: float,
    selected_I: float,
    axis: str,
    key_prefix: str,
) -> None:
    """Display section properties with user-selected output units.

    Internal values are expected in:
    - A: mm²
    - Iy, Iz, selected_I: mm⁴
    """
    unit_col1, unit_col2 = st.columns(2)

    with unit_col1:
        area_output_unit = st.selectbox(
            "Area output unit",
            unit_options("area"),
            index=0,
            key=f"{key_prefix}_area_output_unit",
        )

    with unit_col2:
        inertia_output_unit = st.selectbox(
            "Inertia output unit",
            unit_options("inertia"),
            index=0,
            key=f"{key_prefix}_inertia_output_unit",
        )

    st.write(f"Area A = **{mm2_to_area(A, area_output_unit):.3f} {area_output_unit}**")
    st.write(f"Iy = **{mm4_to_inertia(Iy, inertia_output_unit):.3f} {inertia_output_unit}**")
    st.write(f"Iz = **{mm4_to_inertia(Iz, inertia_output_unit):.3f} {inertia_output_unit}**")
    st.write(
        f"Selected I for {axis} buckling = "
        f"**{mm4_to_inertia(selected_I, inertia_output_unit):.3f} {inertia_output_unit}**"
    )


def display_custom_section_properties(A: float, I: float, key_prefix: str) -> None:
    """Display custom section A and I with user-selected output units."""
    unit_col1, unit_col2 = st.columns(2)

    with unit_col1:
        area_output_unit = st.selectbox(
            "Area output unit",
            unit_options("area"),
            index=0,
            key=f"{key_prefix}_area_output_unit",
        )

    with unit_col2:
        inertia_output_unit = st.selectbox(
            "Inertia output unit",
            unit_options("inertia"),
            index=0,
            key=f"{key_prefix}_inertia_output_unit",
        )

    st.write(f"Area A = **{mm2_to_area(A, area_output_unit):.3f} {area_output_unit}**")
    st.write(f"Selected I = **{mm4_to_inertia(I, inertia_output_unit):.3f} {inertia_output_unit}**")


def select_axis_and_get_I(properties: dict[str, float], key_prefix: str) -> tuple[str, float, float]:
    axis = st.radio(
        "Select buckling axis",
        options=["Z-Z", "Y-Y"],
        index=0,
        horizontal=True,
        key=f"{key_prefix}_axis",
    )

    A, I = selected_axis_properties(properties, axis)
    return axis, A, I


def get_summary_units(profile_type: str) -> tuple[str, str]:
    """Return area/inertia display units currently selected for the active profile."""
    if profile_type == "Custom section":
        return (
            st.session_state.get("custom_area_output_unit", "mm²"),
            st.session_state.get("custom_inertia_output_unit", "mm⁴"),
        )
    if profile_type in FLANGED_PROFILE_LIBRARY:
        return (
            st.session_state.get("flanged_area_output_unit", "mm²"),
            st.session_state.get("flanged_inertia_output_unit", "mm⁴"),
        )
    if profile_type == "CHS - Circular hollow section / pipe":
        return (
            st.session_state.get("chs_area_output_unit", "mm²"),
            st.session_state.get("chs_inertia_output_unit", "mm⁴"),
        )
    if profile_type == "SHS/RHS - Square/rectangular hollow section":
        return (
            st.session_state.get("rhs_area_output_unit", "mm²"),
            st.session_state.get("rhs_inertia_output_unit", "mm⁴"),
        )
    if profile_type == "Flat bar / plate":
        return (
            st.session_state.get("flat_area_output_unit", "mm²"),
            st.session_state.get("flat_inertia_output_unit", "mm⁴"),
        )
    if profile_type == "Round bar":
        return (
            st.session_state.get("round_area_output_unit", "mm²"),
            st.session_state.get("round_inertia_output_unit", "mm⁴"),
        )
    return "mm²", "mm⁴"


def show_design_check_message(status: str, message: str) -> None:
    if status == "success":
        st.success(message)
    elif status == "warning":
        st.warning(message)
    else:
        st.error(message)


# -----------------------------------------------------------------------------
# Main app
# -----------------------------------------------------------------------------

st.title("Column Buckling Calculator")
st.write("#### Column buckling calculation according to DIN 18800 guideline")

section_title("Input")

# Elasticity modulus input
Ecol1, Ecol2 = st.columns([2, 1])
with Ecol1:
    E_in = st.number_input("Elasticity modulus (E)", value=200000.0, min_value=0.0, format="%.2f")
with Ecol2:
    E_unit = st.selectbox("Unit", unit_options("modulus"), index=0, key="E_unit")
E = modulus_to_mpa(E_in, E_unit)

# Yield strength input
YScol1, YScol2 = st.columns([2, 1])
with YScol1:
    YS_in = st.number_input("Material yield strength (YS)", value=350.0, min_value=0.0, format="%.2f")
with YScol2:
    YS_unit = st.selectbox("Unit", unit_options("stress"), index=0, key="YS_unit")
YS = stress_to_mpa(YS_in, YS_unit)

# Column length input
Lcol1, Lcol2 = st.columns([2, 1])
with Lcol1:
    L_in = st.number_input("Column length (L)", value=1000.0, min_value=0.0, format="%.2f")
with Lcol2:
    L_unit = st.selectbox("Unit", unit_options("length"), index=0, key="L_unit")
L = length_to_mm(L_in, L_unit)

# Maximum compression force input
Fcol1, Fcol2 = st.columns([2, 1])
with Fcol1:
    Fcompr_in = st.number_input("Maximum compression force (Fcompr)", value=100.0, min_value=0.0, format="%.2f")
with Fcol2:
    Fcompr_unit = st.selectbox("Unit", unit_options("force"), index=1, key="Fcompr_unit")
Fcompr = force_to_n(Fcompr_in, Fcompr_unit)

# Bending moment warning
bending_expected = st.radio(
    "Is bending moment expected to occur?",
    options=["No", "Yes"],
    index=0,
    horizontal=True,
    key="bending_expected",
)
has_bending_moment = bending_expected == "Yes"

if has_bending_moment:
    st.warning(
        "This calculator currently covers axial compression buckling only. "
        "If bending moment is expected, a combined compression + bending check is required."
    )

if E <= 0 or YS <= 0 or L <= 0 or Fcompr <= 0:
    st.error("E, YS, L, and Fcompr must all be greater than 0.")
    st.stop()

st.divider()

# -----------------------------------------------------------------------------
# Buckling shape / effective length factor
# -----------------------------------------------------------------------------
section_title("Buckling shape")

k_factors = {
    "Mode 1": 0.70,
    "Mode 2": 0.85,
    "Mode 3": 1.00,
    "Mode 4": 1.20,
    "Mode 5": 2.20,
    "Mode 6": 2.20,
    "Custom k": None,
}

st.write("Select a buckling shape or enter your own effective length factor.")

try:
    st.image("modes.png", caption="Buckling modes", use_container_width=True)
except Exception:
    st.info("Add `modes.png` to the project folder to show buckling mode diagrams.")

if "selected_buckling_mode" not in st.session_state:
    st.session_state.selected_buckling_mode = "Mode 3"

button_cols = st.columns(7)
for index, mode_name in enumerate(k_factors.keys()):
    with button_cols[index]:
        if st.button(mode_name, use_container_width=True):
            st.session_state.selected_buckling_mode = mode_name

selected_buckling_mode = st.session_state.selected_buckling_mode

if selected_buckling_mode == "Custom k":
    k = st.number_input(
        "Custom effective length factor k",
        value=1.00,
        min_value=0.01,
        step=0.05,
        format="%.3f",
        key="custom_k_factor",
    )
else:
    k = k_factors[selected_buckling_mode]

Leff = k * L

st.write(f"Selected buckling shape: **{selected_buckling_mode}**")
st.write(f"Effective length factor k = **{k:.3f}**")
st.write(f"Effective length Leff = **{mm_to_length(Leff, L_unit):.3f} {L_unit}**")

st.divider()

# -----------------------------------------------------------------------------
# Profile selection
# -----------------------------------------------------------------------------
section_title("Profile selection")

standard_profiles = list(FLANGED_PROFILE_LIBRARY.keys())
parametric_profiles = [
    "CHS - Circular hollow section / pipe",
    "SHS/RHS - Square/rectangular hollow section",
    "Flat bar / plate",
    "Round bar",
    "Custom section",
]

profile_type = st.selectbox(
    "Select profile type",
    options=standard_profiles + parametric_profiles,
    index=0,
    key="profile_type",
)

profile_col1, profile_col2 = st.columns([1, 1])

# Standard flanged profiles
if profile_type in FLANGED_PROFILE_LIBRARY:
    with profile_col1:
        profile_name = st.selectbox(
            "Select profile size",
            options=get_flanged_profile_names(profile_type),
            index=0,
            key="profile_name",
        )

        profile_data = get_flanged_profile_data(profile_type, profile_name)
        profile_properties = get_flanged_properties(profile_data)
        axis, A, I = select_axis_and_get_I(profile_properties, "flanged")

        display_section_properties(
            A=A,
            Iy=profile_properties["iy_mm4"],
            Iz=profile_properties["iz_mm4"],
            selected_I=I,
            axis=axis,
            key_prefix="flanged",
        )

    with profile_col2:
        fig = draw_flanged_section(profile_data, profile_name)
        st.pyplot(fig)

# CHS / pipe
elif profile_type == "CHS - Circular hollow section / pipe":
    with profile_col1:
        ODcol1, ODcol2 = st.columns([2, 1])
        with ODcol1:
            OD_in = st.number_input("Outer diameter OD", value=200.0, min_value=0.0, format="%.2f")
        with ODcol2:
            OD_unit = st.selectbox("Unit", unit_options("length"), index=0, key="OD_unit")

        WTcol1, WTcol2 = st.columns([2, 1])
        with WTcol1:
            WT_in = st.number_input("Wall thickness t", value=10.0, min_value=0.0, format="%.2f")
        with WTcol2:
            WT_unit = st.selectbox("Unit", unit_options("length"), index=0, key="WT_unit")

        OD = length_to_mm(OD_in, OD_unit)
        WT = length_to_mm(WT_in, WT_unit)

        try:
            profile_properties = chs_properties(OD, WT)
        except ValueError as error:
            st.error(str(error))
            st.stop()

        axis, A, I = select_axis_and_get_I(profile_properties, "chs")
        display_section_properties(A, profile_properties["iy_mm4"], profile_properties["iz_mm4"], I, axis, "chs")

    with profile_col2:
        fig = draw_chs_section(OD, WT)
        st.pyplot(fig)

# SHS / RHS
elif profile_type == "SHS/RHS - Square/rectangular hollow section":
    with profile_col1:
        b_col1, b_col2 = st.columns([2, 1])
        with b_col1:
            b_in = st.number_input("Outer width b", value=100.0, min_value=0.0, format="%.2f")
        with b_col2:
            b_unit = st.selectbox("Unit", unit_options("length"), index=0, key="rhs_b_unit")

        h_col1, h_col2 = st.columns([2, 1])
        with h_col1:
            h_in = st.number_input("Outer height h", value=100.0, min_value=0.0, format="%.2f")
        with h_col2:
            h_unit = st.selectbox("Unit", unit_options("length"), index=0, key="rhs_h_unit")

        t_col1, t_col2 = st.columns([2, 1])
        with t_col1:
            t_in = st.number_input("Wall thickness t", value=5.0, min_value=0.0, format="%.2f")
        with t_col2:
            t_unit = st.selectbox("Unit", unit_options("length"), index=0, key="rhs_t_unit")

        b = length_to_mm(b_in, b_unit)
        h = length_to_mm(h_in, h_unit)
        t = length_to_mm(t_in, t_unit)

        try:
            profile_properties = rhs_properties(b, h, t)
        except ValueError as error:
            st.error(str(error))
            st.stop()

        axis, A, I = select_axis_and_get_I(profile_properties, "rhs")
        display_section_properties(A, profile_properties["iy_mm4"], profile_properties["iz_mm4"], I, axis, "rhs")

    with profile_col2:
        fig = draw_rhs_section(b, h, t)
        st.pyplot(fig)

# Flat bar / plate
elif profile_type == "Flat bar / plate":
    with profile_col1:
        b_col1, b_col2 = st.columns([2, 1])
        with b_col1:
            b_in = st.number_input("Width b", value=100.0, min_value=0.0, format="%.2f")
        with b_col2:
            b_unit = st.selectbox("Unit", unit_options("length"), index=0, key="flat_b_unit")

        h_col1, h_col2 = st.columns([2, 1])
        with h_col1:
            h_in = st.number_input("Height h", value=10.0, min_value=0.0, format="%.2f")
        with h_col2:
            h_unit = st.selectbox("Unit", unit_options("length"), index=0, key="flat_h_unit")

        b = length_to_mm(b_in, b_unit)
        h = length_to_mm(h_in, h_unit)

        try:
            profile_properties = flat_bar_properties(b, h)
        except ValueError as error:
            st.error(str(error))
            st.stop()

        axis, A, I = select_axis_and_get_I(profile_properties, "flat")
        display_section_properties(A, profile_properties["iy_mm4"], profile_properties["iz_mm4"], I, axis, "flat")

    with profile_col2:
        fig = draw_flat_bar_section(b, h)
        st.pyplot(fig)

# Round bar
elif profile_type == "Round bar":
    with profile_col1:
        d_col1, d_col2 = st.columns([2, 1])
        with d_col1:
            d_in = st.number_input("Diameter d", value=50.0, min_value=0.0, format="%.2f")
        with d_col2:
            d_unit = st.selectbox("Unit", unit_options("length"), index=0, key="round_d_unit")

        d = length_to_mm(d_in, d_unit)

        try:
            profile_properties = round_bar_properties(d)
        except ValueError as error:
            st.error(str(error))
            st.stop()

        axis, A, I = select_axis_and_get_I(profile_properties, "round")
        display_section_properties(A, profile_properties["iy_mm4"], profile_properties["iz_mm4"], I, axis, "round")

    with profile_col2:
        fig = draw_round_bar_section(d)
        st.pyplot(fig)

# Custom section
elif profile_type == "Custom section":
    with profile_col1:
        Acol1, Acol2 = st.columns([2, 1])
        with Acol1:
            A_in = st.number_input("Cross-sectional area A", value=1000.0, min_value=0.0, format="%.3f")
        with Acol2:
            A_unit = st.selectbox("Unit", unit_options("area"), index=0, key="custom_A_unit")

        Icol1, Icol2 = st.columns([2, 1])
        with Icol1:
            I_in = st.number_input("Second moment of area I", value=1_000_000.0, min_value=0.0, format="%.3f")
        with Icol2:
            I_unit = st.selectbox("Unit", unit_options("inertia"), index=0, key="custom_I_unit")

        A = area_to_mm2(A_in, A_unit)
        I = inertia_to_mm4(I_in, I_unit)

        if A <= 0 or I <= 0:
            st.error("A and I must be greater than 0.")
            st.stop()

        axis = "Custom"
        display_custom_section_properties(A, I, "custom")

    with profile_col2:
        fig = draw_custom_section_placeholder()
        st.pyplot(fig)

# -----------------------------------------------------------------------------
# Buckling curve / imperfection factor
# -----------------------------------------------------------------------------
alpha_curve_options = {
    "Curve a - αc = 0.21": 0.21,
    "Curve b - αc = 0.34": 0.34,
    "Curve c - αc = 0.49": 0.49,
    "Curve d - αc = 0.76": 0.76,
}

default_alpha_index = 2  # Curve c - general default

selected_alpha_curve = st.selectbox(
    "Imperfection factor αc",
    options=list(alpha_curve_options.keys()),
    index=default_alpha_index,
    key="selected_alpha_curve",
)

alphac = alpha_curve_options[selected_alpha_curve]

st.caption(
    "αc adjusts the buckling reduction curve and represents initial imperfections. "
    "Select curve a, b, c, or d according to the applicable standard table for the chosen profile, axis, and fabrication method."
)

st.divider()

# -----------------------------------------------------------------------------
# Input summary
# -----------------------------------------------------------------------------
with st.expander("Input summary", expanded=True):
    area_summary_unit, inertia_summary_unit = get_summary_units(profile_type)

    summary_rows = [
        ("Elasticity modulus E", f"{E_in:.3f} {E_unit}"),
        ("Yield strength YS", f"{YS_in:.3f} {YS_unit}"),
        ("Column length L", f"{L_in:.3f} {L_unit}"),
        ("Maximum compression force Fcompr", f"{Fcompr_in:.3f} {Fcompr_unit}"),
        ("Buckling shape", selected_buckling_mode),
        ("Effective length factor k", f"{k:.3f}"),
        ("Effective length Leff", f"{mm_to_length(Leff, L_unit):.3f} {L_unit}"),
        ("Profile type", profile_type),
        ("Buckling axis", axis),
        ("Cross-sectional area A", f"{mm2_to_area(A, area_summary_unit):.3f} {area_summary_unit}"),
        ("Selected second moment of area I", f"{mm4_to_inertia(I, inertia_summary_unit):.3f} {inertia_summary_unit}"),
        ("Buckling curve factor αc", f"{alphac:.2f}"),
    ]

    for label, value in summary_rows:
        col_label, col_value = st.columns([2, 1])
        with col_label:
            st.write(label)
        with col_value:
            st.write(f"**{value}**")

st.divider()

# -----------------------------------------------------------------------------
# Results
# -----------------------------------------------------------------------------
section_title("Results")

try:
    result = calculate_buckling(
        elastic_modulus_mpa=E,
        yield_strength_mpa=YS,
        effective_length_mm=Leff,
        area_mm2=A,
        inertia_mm4=I,
        compression_force_n=Fcompr,
        alpha_c=alphac,
    )
except ValueError as error:
    st.error(str(error))
    st.stop()

result_unit_col1, result_unit_col2, result_unit_col3 = st.columns(3)

with result_unit_col1:
    result_stress_unit = st.selectbox(
        "Result stress unit",
        unit_options("stress"),
        index=unit_options("stress").index(YS_unit) if YS_unit in unit_options("stress") else 0,
        key="result_stress_unit",
    )

with result_unit_col2:
    result_force_unit = st.selectbox(
        "Result force unit",
        unit_options("force"),
        index=unit_options("force").index(Fcompr_unit) if Fcompr_unit in unit_options("force") else 1,
        key="result_force_unit",
    )

with result_unit_col3:
    result_length_unit = st.selectbox(
        "Result length unit",
        unit_options("length"),
        index=unit_options("length").index(L_unit) if L_unit in unit_options("length") else 0,
        key="result_length_unit",
    )

main_result_rows = [
    (
        "Critical stress sigma_k",
        f"{mpa_to_stress(result.critical_stress_mpa, result_stress_unit):.3f} {result_stress_unit}",
    ),
    (
        "Critical buckling force Fcr",
        f"{n_to_force(result.critical_force_n, result_force_unit):.3f} {result_force_unit}",
    ),
    ("Utilization", f"{result.utilization_percent:.2f}%"),
]

main_result_col1, main_result_col2, main_result_col3 = st.columns(3)

with main_result_col1:
    st.metric(
        "Critical stress σk",
        f"{mpa_to_stress(result.critical_stress_mpa, result_stress_unit):.3f} {result_stress_unit}",
    )

with main_result_col2:
    st.metric(
        "Critical buckling force Fcr",
        f"{n_to_force(result.critical_force_n, result_force_unit):.3f} {result_force_unit}",
    )

with main_result_col3:
    st.metric("Utilization", f"{result.utilization_percent:.2f}%")

with st.expander("Detailed buckling values"):
    detail_rows = [
        ("Radius of gyration i", f"{mm_to_length(result.radius_of_gyration_mm, result_length_unit):.3f} {result_length_unit}"),
        ("Slenderness ratio λ", f"{result.slenderness_ratio:.3f}"),
        ("Yield point limiting slenderness ratio λeH", f"{result.limiting_slenderness_ratio:.3f}"),
        ("Relative slenderness λk", f"{result.relative_slenderness:.3f}"),
        ("Buckling curve factor αc", f"{alphac:.2f}"),
        ("Reduction factor χ", f"{result.reduction_factor_chi:.3f}"),
        ("Applied compression force Fcompr", f"{n_to_force(Fcompr, result_force_unit):.3f} {result_force_unit}"),
    ]

    for label, value in detail_rows:
        col_label, col_value = st.columns([2, 1])
        with col_label:
            st.write(label)
        with col_value:
            st.write(f"**{value}**")

# -----------------------------------------------------------------------------
# Buckling curve diagram
# -----------------------------------------------------------------------------
st.subheader("Buckling curve")

lambda_limit = 90.0
lambda_values = np.linspace(1.0, max(180.0, result.slenderness_ratio * 1.20), 400)

stress_values_mpa = np.array([
    critical_stress_for_slenderness(
        slenderness_ratio=float(lam),
        limiting_slenderness_ratio=result.limiting_slenderness_ratio,
        yield_strength_mpa=YS,
        alpha_c=alphac,
    )
    for lam in lambda_values
])

stress_values_display = np.array([
    mpa_to_stress(float(y), result_stress_unit) for y in stress_values_mpa
])
critical_stress_display = mpa_to_stress(result.critical_stress_mpa, result_stress_unit)

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(lambda_values, stress_values_display, label="Critical compression stress curve")

xmax = lambda_values.max()
if xmax > lambda_limit:
    ax.axvspan(lambda_limit, xmax, alpha=0.40, color="orange", label="Caution region (λ > 90)")

ax.scatter(result.slenderness_ratio, critical_stress_display, color="red", zorder=5, label="Current critical point")
ax.axvline(result.slenderness_ratio, color="red", linestyle="--", linewidth=1)
ax.axhline(critical_stress_display, color="red", linestyle="--", linewidth=1)

ax.set_title("Slenderness ratio vs critical compression stress")
ax.set_xlabel("Slenderness ratio λ")
ax.set_ylabel(f"Critical compression stress σk [{result_stress_unit}]")
ax.grid(True)
ax.legend()
st.pyplot(fig)

summary = design_check_summary(
    utilization_percent=result.utilization_percent,
    slenderness_ratio=result.slenderness_ratio,
    slenderness_limit=lambda_limit,
    bending_moment_expected=has_bending_moment,
)
show_design_check_message(summary.status, summary.message)

pdf_bytes = create_pdf_report(
    input_summary_rows=summary_rows,
    main_result_rows=main_result_rows,
    detail_rows=detail_rows,
    design_check_message=summary.message,
    buckling_curve_fig=fig,
)

st.download_button(
    label="Download PDF report",
    data=pdf_bytes,
    file_name="column_buckling_report.pdf",
    mime="application/pdf",
    use_container_width=True,
)

st.divider()

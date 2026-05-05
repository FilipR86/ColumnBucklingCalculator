# Buckling calculator DIN 18800 Teil 2 Seite 9

import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import math
import Flanged_steel_sections as fss

st.title("Column Buckling Calculator")
st.write("""
#### Column buckling calculation according to DIN 18800 guidelines
         """)         

st.markdown(
    "<p style='font-size:26px; text-decoration: underline;'>Input</p>",
    unsafe_allow_html=True
)

# --- Inputs ---
# Elasticity modulus input
Ecol1, Ecol2 = st.columns([2, 1])
with Ecol1:
    E_in = st.number_input("Elasticity modulus (E)", value=200000.0, format="%.2f")
with Ecol2:
    E_unit = st.selectbox("Unit", ["MPa", "psi", "psf"], key="E_unit")

if E_unit == "MPa":
    E = E_in
if E_unit == "psi":
    E = E_in * 0.0068947573
if E_unit == "psf":
    E = E_in * 0.000047880259

# Yield strength input
YScol1, YScol2 = st.columns([2, 1])
with YScol1:
    YS_in = st.number_input("Material Yield strength (YS)", value=350.0, format="%.2f")
with YScol2:
    YS_unit = st.selectbox("Unit", ["MPa", "psi", "psf"], key="YS_unit")

if YS_unit == "MPa":
    YS = YS_in
if YS_unit == "psi":
    YS = YS_in * 0.0068947573
if YS_unit == "psf":
    YS = YS_in * 0.000047880259

# Beam length input
Lcol1, Lcol2 = st.columns([2, 1])
with Lcol1:
    L_in = st.number_input("Beam length (L)", value=1000.0, format="%.2f")
with Lcol2:
    L_unit = st.selectbox("Unit", ["mm", "m", "cm", "inches", "feet"], key="L_unit")

if L_unit == "mm":
    L = L_in
if L_unit == "m":
    L = L_in * 1000
if L_unit == "cm":
    L = L_in * 10
if L_unit == "inches":
    L = L_in * 25.4
if L_unit == "feet":
    L = L_in * 304.8


st.divider()

# Buckling shape selection
Bshape1, Bshape2 = st.columns([1,1])
with Bshape1:
    shape = st.selectbox("Select buckling shape (1 to 6)", options=[1, 2, 3, 4, 5, 6])
with Bshape2:
    k_override = st.number_input("Override Effective length factor k (optional)", value=0.0, min_value=0.0)

st.image("modes.png", caption="Buckling modes", use_container_width=True)


# --- Determine k factor ---
k_factors = {1: 0.7, 2: 0.85, 3: 1, 4: 1.2, 5: 2.2, 6: 2.2}
k = k_factors.get(shape, 1)
if k_override != 0:
    k = k_override
st.write(f"Selectedd Effective length factor (k) is: {k:.2f}")

st.divider()


# --- Section properties ---
st.markdown(
    "<p style='font-size:26px; text-decoration: underline;'>Column profile selection</p>",
    unsafe_allow_html=True
)
Crossection = st.selectbox("Select a beam profile type", options=["HEA", "HEB", "HEM", "IPE", "UB - Universal Beam", "UC - Universal Column", 
                                                         "CHC - Circular Hollow Section - pipe/tube", 
                                                         "SHS/RHS - Square/Rectangular hollow section", 
                                                         "Flat bar/plate", "Round bar", "Custom section"], index=0, key="profile")


def load_flanged_profile(profile_dict, profile_name):

    d1, d2 = st.columns([2,2])
    with d1:
        name = st.selectbox("Select size", options=list(profile_dict.keys()), index=0, key="sub_profile")
    with d2:
        st.image("Flanged_profile.png", caption="Flanged profile", width=250)
    
    data = profile_dict[name]

    A = data["Area [mm2]"]
    Iy = data["Second moment of area Iy [×10^6 mm4]"] * 1e6
    Iz = data["Second moment of area Iz [×10^6 mm4]"] * 1e6
    Wy = data["Elastic section modulus Wel,y [×10^3 mm3]"] * 1e3
    Wz = data["Elastic section modulus Wel,z [×10^3 mm3]"] * 1e3

    st.write(
    f"Area A = {A:.6f} mm² / "
    f"{A*0.01:.6f} cm² / "
    f"{A*1e-6:.6f} m² / "
    f"{A*(1/25.4)**2:.6f} in² / "
    f"{A*(1/304.8)**2:.6f} ft²")
    
    st.write(
    f"Second moment of area Iy = {Iy} mm⁴ / "
    f"{Iy * 1e-4:.3f} cm⁴ / "
    f"{Iy * 1e-12:.9f} m⁴ / "
    f"{Iy * (1/25.4)**4:.4f} in⁴ / "
    f"{Iy * (1/304.8)**4:.8f} ft⁴")

    st.write(
    f"Second moment of area Iz = {Iz} mm⁴ / "
    f"{Iz * 1e-4:.3f} cm⁴ / "
    f"{Iz * 1e-12:.9f} m⁴ / "
    f"{Iz * (1/25.4)**4:.4f} in⁴ / "
    f"{Iz * (1/304.8)**4:.8f} ft⁴")

    st.write(
    f"Second moment of area Wel,y = {Wy} mm³ / "
    f"{Wy * 1e-3:.3f} cm³ / "
    f"{Wy * 1e-9:.8f} m³ / "
    f"{Wy * (1/25.4)**3:.4f} in³ / "
    f"{Wy * (1/304.8)**3:.8f} ft³ ")

    st.write(
    f"Second moment of area Wel,z = {Wz} mm³ / "
    f"{Wz * 1e-3:.3f} cm³ / "
    f"{Wz * 1e-9:.8f} m³ / "
    f"{Wz * (1/25.4)**3:.4f} in³ / "
    f"{Wz * (1/304.8)**3:.8f} ft³ ")

    axis = st.radio("Choose axis", ["Z-Z","Y-Y"])
    I = Iy if axis == "Y-Y" else Iz
    W = Wy if axis == "Y-Y" else Wz

    return A, I, W

if Crossection == "HEA":
    A, I, W = load_flanged_profile(fss.HEA, "HEA")
if Crossection == "HEB":
    A, I, W = load_flanged_profile(fss.HEB, "HEB")
if Crossection == "HEM":
    A, I, W = load_flanged_profile(fss.HEM, "HEM")
if Crossection == "IPE":
    A, I, W = load_flanged_profile(fss.IPE, "IPE")
if Crossection == "UB - Universal Beam":
    A, I, W = load_flanged_profile(fss.UB, "UB")
if Crossection == "UC - Universal Column":
    A, I, W = load_flanged_profile(fss.UC, "UC")

# ---- Unit conversion logic ----
FORCE_TO_N = {"N": 1.0, "kN": 1_000.0, "lbf": 4.4482216152605}
LENGTH_TO_MM = {"mm": 1.0, "cm": 10.0, "m": 1_000.0, "inch": 25.4, "ft": 304.8}
STRESS_TO_MPA = {"MPa": 1.0, "GPa": 1_000.0, "psi": 0.006894757293168, "kips": 6.894757293168}
MODULUS_TO_MPA = STRESS_TO_MPA.copy()

N_TO_FORCE = {k: 1.0/v for k, v in FORCE_TO_N.items()}
MM_TO_LENGTH = {k: 1.0/v for k, v in LENGTH_TO_MM.items()}
MPA_TO_STRESS = {k: 1.0/v for k, v in STRESS_TO_MPA.items()}

def to_internal(value, unit, m): return value * m[unit]
def from_internal(value, unit, m): return value * m[unit]

def force_to_N(v, u): return to_internal(v, u, FORCE_TO_N)
def length_to_mm(v, u): return to_internal(v, u, LENGTH_TO_MM)
def stress_to_MPa(v, u): return to_internal(v, u, STRESS_TO_MPA)
def modulus_to_MPa(v, u): return to_internal(v, u, MODULUS_TO_MPA)

def N_to_force(v, u): return from_internal(v, u, N_TO_FORCE)
def mm_to_length(v, u): return from_internal(v, u, MM_TO_LENGTH)
def MPa_to_stress(v, u): return from_internal(v, u, MPA_TO_STRESS)

def assert_positive(name: str, v: float):
    if v is None or math.isnan(v) or v <= 0:
        raise ValueError(f"{name} must be positive; got {v}")

if Crossection == "CHC - Circular Hollow Section - pipe/tube":
    c13, c14 = st.columns(2)
    with c13:
        OD_val = st.number_input("Outer diameter OD", value=200.0, min_value=0.0, step=5.0, format="%.2f")
    with c14:
        OD_unit = st.selectbox("Unit", options=["mm", "cm", "m", "inch", "ft"], index=0, key="OD")
    c15, c16 = st.columns(2)
    with c15:
        WT_val = st.number_input("Wall thickness WT", value=10.0, min_value=0.0, step=5.0, format="%.2f")
    with c16:
        WT_unit = st.selectbox("Unit", options=["mm", "cm", "m", "inch", "ft"], index=0, key="WT")
    
    OD_mm = length_to_mm(OD_val, OD_unit)
    WT_mm = length_to_mm(WT_val, WT_unit)              

    A = (OD_mm**2-(OD_mm-2*WT_mm)**2)*np.pi*0.25
    st.write(f"Area A = {A} mm²")
    I = np.pi*(OD_mm**4-(OD_mm-2*WT_mm)**4)/64
    st.write(f"Second moment of area I = {I/10**6} × 10⁶ mm⁴")
    W = np.pi*((OD_mm/2)**4-(OD_mm/2-WT_mm)**4)/(4*(OD_mm/2))
    st.write(f"Second moment of area Wel = {W/10**3} × 10$^3$ mm⁴") 



if Crossection == "Flat bar/plate":
    b = st.number_input("Plate breath (b) in mm", value=100.0, format="%.2f")
    h = st.number_input("Plate height (h) in mm", value=10.0, format="%.2f")
    A = b * h
    st.write(f"Profile area A is: {A:.3f} mm2")
    Iy_mm4 = b * h**3 / 12
    st.write(f"Second moment of area Iy is: {Iy_mm4:.3f} mm4")
    Iz_mm4 = b**3 * h / 12
    st.write(f"Second moment of area Iz is: {Iz_mm4:.3f} mm4")
    I = min(Iy_mm4, Iz_mm4) 
    if b <= 0 or h <= 0:
        st.error("b or h must be greater than 0.")
        st.stop()

if Crossection == "Round bar":
    d = st.number_input("Rod diameter (d) in mm", value=50.0)
    A = 0.25 * np.pi * d**2
    I = np.pi * d**4 / 64
    st.write(f"Profile area A is: {A:.3f} mm2")
    st.write(f"Second moment of area I is: {I:.3f} mm4")
    if d <= 0:
        st.error("d must be greater than 0.")
        st.stop()

if Crossection == "SHS/RHS - Square/Rectangular hollow section":
    b = st.number_input("Outer width (b) in mm", value=100.0, format="%.2f")
    h = st.number_input("Outer height (h) in mm", value=100.0, format="%.2f")
    t = st.number_input("Wall thickness (t) in mm", value=5.0, format="%.2f")

    if b <= 0 or h <= 0 or t <= 0:
        st.error("b, h and t must be greater than 0.")
        st.stop()

    if 2 * t >= min(b, h):
        st.error("Wall thickness t is too large (must be less than half of b and h).")
        st.stop()

    bi = b - 2 * t
    hi = h - 2 * t

    A = b * h - bi * hi
    st.write(f"Profile area A is: {A:.3f} mm2")

    Iy_mm4 = (b * h**3 - bi * hi**3) / 12
    st.write(f"Second moment of area Iy is: {Iy_mm4:.3f} mm4")

    Iz_mm4 = (b**3 * h - bi**3 * hi) / 12
    st.write(f"Second moment of area Iz is: {Iz_mm4:.3f} mm4")

    I = min(Iy_mm4, Iz_mm4)

if Crossection == "Custom section":
    A = st.number_input("Cross-sectional area A (mm2)", value=1000.0, format="%.3f")
    I = st.number_input("Second moment of area I (mm4)", value=1e6, format="%.3f")

    if A <= 0 or I <= 0:
        st.error("A and I must be greater than 0.")
        st.stop()

    st.write(f"Profile area A is: {A:.3f} mm2")
    st.write(f"Second moment of area I is: {I:.3f} mm4")

if E <= 0 or YS <= 0 or L <= 0:
    st.error("Value must be greater than 0.")
    st.stop()


# --- Buckling analysis ---
imin = math.sqrt(I / A) # Radius of gravity
L0 = L * k
lam = L0 / imin
lameH = math.sqrt(np.pi**2 * E / YS) # Yield point limiting slenderness ratio
lamk = lam / lameH
alfac = 0.49

# --- Relative slenderness function ---
def reducing_factor(lamk):
    kfac = 0.5 * (1 + alfac * (lamk - 0.2) + lamk**2)
    if lamk <= 0.2:
        K = 1
    elif lamk <= 3:
        K = 1 / (kfac + math.sqrt(kfac**2 - lamk**2))
    else:
        K = 1 / (lamk * (lamk + alfac))
    return K

K = reducing_factor(lamk)
sigmak = K * 0.9 * YS
Fcr = sigmak * A

st.divider()

# --- Output results ---
st.markdown(
    "<p style='font-size:26px; text-decoration: underline;'>Results</p>",
    unsafe_allow_html=True
)
st.write(f"Radius of gravity: {imin:.2f} mm")
st.write(f"Slenderness Ratio λ: {lam:.3f}")
st.write(f"Yield point limiting slenderness ratio λeH: {lameH:.3f}")
st.write(f"Relative Slenderness Ratio λk: {lamk:.3f}")
st.write(f"Ϗ: {K:.3f}")
st.write(f"Critical compression stress (σk): {sigmak:.2f} MPa")
st.write(f"Critical Buckling Force (Fcr): {Fcr:.2f} N")

# --- Plot σk vs λk ---
x_vals = np.arange(0, 6.1, 0.1)

if YS_unit == "MPa":
    y_vals = [float(reducing_factor(x)) * 0.9 * YS for x in x_vals]
if YS_unit == "psi":
    y_vals = [float(reducing_factor(x)) * 0.9 * YS / 0.0068947573 for x in x_vals]
if YS_unit == "psf":
    y_vals = [float(reducing_factor(x)) * 0.9 * YS / 0.000047880259 for x in x_vals]

point_x = lamk
point_y = sigmak


fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(x_vals, y_vals, label='σk vs λk', color='blue')
ax.scatter(point_x, point_y, color='red', label='Critical point')
ax.set_title("Reduced Design Stress vs Relative Slenderness Ratio")
ax.set_xlabel("λk (Relative Slenderness Ratio)")
ax.set_ylabel(f"σk ({YS_unit})")
ax.grid(True)
ax.legend()
st.pyplot(fig)


# Dodat C, L, T, hollow square, kvadrat profile
import streamlit as st
import pandas as pd
import pydeck as pdk
import numpy as np
import matplotlib.pyplot as plt
from utils.io import load_data

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
st.title("📊 Dashboard — Price Gap & Risk Score (District 1 & 5)")

df, summary_by_district, top_streets = load_data()

# Column names (English with spaces)
LAT = "Latitude"
LON = "Longitude"
GAP = "Price Gap Corrected" if "Price Gap Corrected" in df.columns else "Price Gap (MarketRef / GovPrice)"
RISK = "Risk Score"
DISTRICT = "District"
WARD = "Ward"
STREET = "Street"

# Keep only rows with coordinates for maps
dff = df.copy()
dff[LAT] = pd.to_numeric(dff.get(LAT), errors="coerce")
dff[LON] = pd.to_numeric(dff.get(LON), errors="coerce")
dff = dff.dropna(subset=[LAT, LON]).copy()

# Sidebar controls
c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
with c1:
    district_filter = st.selectbox("District filter", ["All", "1", "5"], index=0)
with c2:
    signal = st.selectbox("Color/weight signal (for interpretation)", ["Risk Score", "Price Gap"], index=0)
with c3:
    layer_type = st.selectbox("Map layer", ["Scatter (points)", "Heatmap", "Hexagon (3D bins)"], index=0)
with c4:
    radius = st.slider("Radius (meters)", min_value=50, max_value=800, value=120, step=10)

if district_filter != "All":
    dff = dff[dff[DISTRICT].astype(str).str.contains(district_filter)].copy()

# Prepare map data
if signal == "Risk Score":
    weight_col = RISK
else:
    weight_col = GAP

dff[weight_col] = pd.to_numeric(dff.get(weight_col), errors="coerce")
# Clip for stability (avoid extreme dominance)
w = dff[weight_col].copy()
if signal == "Price Gap":
    w = w.clip(lower=0, upper=w.quantile(0.99))
else:
    w = w.clip(lower=0, upper=1)
dff["_weight"] = w.fillna(0)

# Optional: jitter to prevent exact overlap when using scatter
jitter = st.checkbox("Add tiny jitter to separate overlapping points (recommended for screenshots)", value=True)
if jitter:
    rng = np.random.default_rng(42)
    dff["_lat_j"] = dff[LAT] + rng.normal(0, 0.00015, size=len(dff))  # ~15m
    dff["_lon_j"] = dff[LON] + rng.normal(0, 0.00015, size=len(dff))
    lat_col, lon_col = "_lat_j", "_lon_j"
else:
    lat_col, lon_col = LAT, LON

# View state centered on HCMC
view_state = pdk.ViewState(
    latitude=float(dff[lat_col].median()),
    longitude=float(dff[lon_col].median()),
    zoom=12.5,
    pitch=40 if layer_type == "Hexagon (3D bins)" else 0,
)

# Build layers
layers = []
if layer_type == "Scatter (points)":
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=dff,
            get_position=f"[{lon_col}, {lat_col}]",
            get_radius=radius,
            radius_units="meters",
            get_fill_color="[255, 80, 80, 140]",
            pickable=True,
        )
    )
elif layer_type == "Heatmap":
    layers.append(
        pdk.Layer(
            "HeatmapLayer",
            data=dff,
            get_position=f"[{lon_col}, {lat_col}]",
            get_weight="_weight",
            radius_pixels=radius,   # here pixels, so we map meter slider roughly
            opacity=0.75,
        )
    )
else:  # Hexagon
    layers.append(
        pdk.Layer(
            "HexagonLayer",
            data=dff,
            get_position=f"[{lon_col}, {lat_col}]",
            radius=radius,          # meters
            elevation_scale=25,
            elevation_range=[0, 4000],
            extruded=True,
            pickable=True,
            get_weight="_weight",
        )
    )

tooltip = {
    "html": "<b>{District}</b> — {Ward}<br/>{Street}<br/>"
            + ("Risk Score" if signal=="Risk Score" else "Price Gap")
            + ": <b>{_weight}</b>",
    "style": {"backgroundColor": "black", "color": "white"},
}

st.pydeck_chart(
    pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        initial_view_state=view_state,
        layers=layers,
        tooltip=tooltip,
    ),
    use_container_width=True,
)

st.caption("Tip: If you only see a couple of blobs, reduce the radius or switch to Scatter/Hexagon.")

st.divider()
st.subheader("Ranking table (Top 30 streets)")

# Street aggregation for table
agg = dff.groupby([DISTRICT, WARD, STREET], as_index=False).agg(
    **{
        "Listings (count)": (weight_col, "size"),
        "Median Price Gap": (GAP, "median"),
        "Mean Risk Score": (RISK, "mean"),
    }
).sort_values("Median Price Gap" if signal=="Price Gap" else "Mean Risk Score", ascending=False).head(30)

st.dataframe(agg, use_container_width=True, hide_index=True)

st.subheader("Distributions")
colA, colB = st.columns(2)
with colA:
    st.markdown("**Price Gap histogram**")
    plt.figure()
    pd.to_numeric(dff[GAP], errors="coerce").dropna().plot(kind="hist", bins=30)
    plt.xlabel("Price Gap")
    plt.ylabel("Count")
    st.pyplot(plt.gcf())
    plt.close()

with colB:
    st.markdown("**Risk Score histogram**")
    plt.figure()
    pd.to_numeric(dff[RISK], errors="coerce").dropna().plot(kind="hist", bins=30)
    plt.xlabel("Risk Score")
    plt.ylabel("Count")
    st.pyplot(plt.gcf())
    plt.close()

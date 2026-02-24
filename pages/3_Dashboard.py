import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pydeck as pdk
import numpy as np
from utils.io import load_data

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
st.title("📊 Dashboard — Price Gap & Risk Score (District 1 & 5)")

df, _, _ = load_data()

LAT, LON = "Latitude", "Longitude"
DISTRICT, WARD, STREET = "District", "Ward", "Street"
GAP = "Price Gap Corrected" if "Price Gap Corrected" in df.columns else "Price Gap (MarketRef / GovPrice)"
RISK = "Risk Score"

# filters
c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    district_filter = st.selectbox("District filter", ["All", "1", "5"], index=0)
with c2:
    signal = st.selectbox("Signal", ["Risk Score", "Price Gap"], index=0)
with c3:
    layer_type = st.selectbox("Map layer", ["Scatter", "Heatmap", "Hexagon"], index=0)

dff = df.copy()
if district_filter != "All":
    dff = dff[dff[DISTRICT].astype(str).str.contains(district_filter)].copy()

# numeric + coords
dff[LAT] = pd.to_numeric(dff.get(LAT), errors="coerce")
dff[LON] = pd.to_numeric(dff.get(LON), errors="coerce")
dff = dff.dropna(subset=[LAT, LON]).copy()

if dff.empty:
    st.error("No rows with Latitude/Longitude after filtering. Please check your data file.")
    st.stop()

weight_col = RISK if signal == "Risk Score" else GAP
dff[weight_col] = pd.to_numeric(dff.get(weight_col), errors="coerce").fillna(0)

# jitter option (avoid overlap)
jitter = st.checkbox("Add tiny jitter (recommended)", value=True)
if jitter:
    rng = np.random.default_rng(42)
    dff["_lat"] = dff[LAT] + rng.normal(0, 0.00015, size=len(dff))
    dff["_lon"] = dff[LON] + rng.normal(0, 0.00015, size=len(dff))
    lat_col, lon_col = "_lat", "_lon"
else:
    lat_col, lon_col = LAT, LON

radius = st.slider("Radius", 50, 800, 120, 10)

view_state = pdk.ViewState(
    latitude=float(dff[lat_col].median()),
    longitude=float(dff[lon_col].median()),
    zoom=12.5,
    pitch=40 if layer_type == "Hexagon" else 0,
)

layers = []
if layer_type == "Scatter":
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
            get_weight=weight_col,
            radius_pixels=radius,
            opacity=0.75,
        )
    )
else:
    layers.append(
        pdk.Layer(
            "HexagonLayer",
            data=dff,
            get_position=f"[{lon_col}, {lat_col}]",
            radius=radius,
            elevation_scale=25,
            elevation_range=[0, 4000],
            extruded=True,
            pickable=True,
            get_weight=weight_col,
        )
    )

tooltip = {"html": "<b>{District}</b> — {Ward}<br/>{Street}<br/>", "style": {"backgroundColor": "black", "color": "white"}}

st.pydeck_chart(
    pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        initial_view_state=view_state,
        layers=layers,
        tooltip=tooltip,
    ),
    use_container_width=True,
)

st.divider()
st.subheader("Distributions")

colA, colB = st.columns(2)
with colA:
    plt.figure()
    pd.to_numeric(dff[GAP], errors="coerce").dropna().plot(kind="hist", bins=30)
    plt.xlabel("Price Gap")
    plt.ylabel("Count")
    st.pyplot(plt.gcf())
    plt.close()

with colB:
    plt.figure()
    pd.to_numeric(dff[RISK], errors="coerce").dropna().plot(kind="hist", bins=30)
    plt.xlabel("Risk Score")
    plt.ylabel("Count")
    st.pyplot(plt.gcf())
    plt.close()

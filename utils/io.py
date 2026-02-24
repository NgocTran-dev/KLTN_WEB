import streamlit as st
import pandas as pd
from utils.io import load_data
from utils.tax import registration_fee_land, non_agri_land_tax_simple, pit_transfer_tax

st.set_page_config(page_title="Tax & Fees", page_icon="🧾", layout="wide")
st.title("🧾 Tax & Fee Estimates (illustrative) — based on Gov Price 2026")

df, _, _ = load_data()

c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    district = st.selectbox("District", ["1", "5"], index=0)
sub = df[df["District"].astype(str).str.contains(district)].copy()

wards = sorted([w for w in sub["Ward"].dropna().unique().tolist()])
with c2:
    ward = st.selectbox("Ward", wards)
sub = sub[sub["Ward"] == ward].copy()

streets = sorted([r for r in sub["Street"].dropna().unique().tolist()])
with c3:
    street = st.selectbox("Street", streets)
sub = sub[sub["Street"] == street].copy()

gov_col = "Government Unit Price 2026 (million VND/m²)"
gov = pd.to_numeric(sub[gov_col], errors="coerce").median()

st.markdown("### Inputs")
colA, colB, colC = st.columns(3)
with colA:
    area = st.number_input("Land area (m²)", min_value=1.0, value=80.0, step=1.0)
with colB:
    transfer_price = st.number_input("Transfer price (billion VND) — for PIT", min_value=0.0, value=0.0, step=0.1)
with colC:
    st.write("Gov Price 2026 (median):", f"{gov:.2f} mil VND/m²" if pd.notna(gov) else "N/A")

st.markdown("### Results (illustrative)")
if pd.notna(gov):
    reg_fee = registration_fee_land(area, gov)
    na_tax = non_agri_land_tax_simple(area, gov)
    pit = pit_transfer_tax(transfer_price) if transfer_price > 0 else None

    k1, k2, k3 = st.columns(3)
    k1.metric("Registration fee (land) ~ 0.5%", f"{reg_fee:,.2f} mil VND")
    k2.metric("Non-agri land tax (simple, 0.03%*)", f"{na_tax:,.2f} mil VND/year")
    k3.metric("PIT transfer tax (2%)", f"{pit:,.2f} mil VND" if pit is not None else "Not provided")
    st.caption("*Real calculation depends on local thresholds, progressive rates, exemptions. This is for quick reference only.")
else:
    st.warning("No Gov Price found for the selected ward/street (mapping missing). Please choose another street or review unmatched list.")

with st.expander("Legal disclaimer", expanded=True):
    st.markdown("""- Estimates are **for reference only** (academic demo).
    - Real results may differ due to exemptions, thresholds, asset-specific legal documents, and the tax authority's rules.
    """)

import streamlit as st
import pandas as pd
from utils.io import load_data
from utils.scoring import normalize_gap, risk_score, risk_level

st.set_page_config(page_title="Price Lookup", page_icon="🔎", layout="wide")
st.title("🔎 Price Lookup — Gov Price 2026, Market Reference, Price Gap, Risk Score")

df, _, _ = load_data()

# Filters
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


    # If corrected columns exist (recommended)
    gov_corr_col = "Gov Price 2026 Corrected (million VND/m²)" if "Gov Price 2026 Corrected (million VND/m²)" in sub.columns else None
    gap_corr_col = "Price Gap Corrected" if "Price Gap Corrected" in sub.columns else None

    # Aggregate key metrics
gov_col = "Government Unit Price 2026 (million VND/m²)"
mref_col = "Market Reference Unit Price (median, million VND/m²)"
fake_col = "Fake Probability (data quality)"

gov = pd.to_numeric(sub[gov_corr_col], errors="coerce").median() if gov_corr_col else pd.to_numeric(sub[gov_col], errors="coerce").median()
mref = pd.to_numeric(sub[mref_col], errors="coerce").median()
gap = (mref / gov) if (pd.notna(mref) and pd.notna(gov) and gov != 0) else None
    if gap_corr_col:
        gap2 = pd.to_numeric(sub[gap_corr_col], errors="coerce").median()
    else:
        gap2 = None

# Risk
w_fake = st.slider("Weight on Fake Probability (w)", 0.0, 1.0, 0.5, 0.05)
fake_prob = pd.to_numeric(sub[fake_col], errors="coerce").median()
s_gap = normalize_gap(gap) if gap is not None else None
risk = risk_score(fake_prob, s_gap, w_fake=w_fake) if s_gap is not None else None
rlevel = risk_level(risk)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Gov Price 2026 (median)", f"{gov:.2f} mil VND/m²" if pd.notna(gov) else "N/A")
k2.metric("Market Reference (median)", f"{mref:.2f} mil VND/m²" if pd.notna(mref) else "N/A")
k3.metric("Price Gap", f"{gap2:.2f}× (corrected)" if gap2 is not None else (f"{gap:.2f}×" if gap is not None else "N/A"))
k4.metric("Risk Score", f"{risk:.2f} ({rlevel})" if risk is not None else "N/A")

st.caption("Price Gap = Market Reference / Government Price. Risk Score combines data quality signal and Price Gap (normalized).")

    # Explain rare case: MarketRef below GovPrice
    if gap2 is not None and gap2 < 1:
        st.warning("MarketRef is below GovPrice (Price Gap < 1). This may indicate (a) mapping/position mismatch, or (b) listing characteristics not comparable to land price. Please review Match Type / listing details.")


st.markdown("### Reference listings")
show_cols = [c for c in [
    "Source","URL","Price (million VND)","Area (m²)","Unit Price (million VND/m²)",
    "House Type","Road/Alley Width (m)","Floors",
    gov_col, mref_col, "Price Gap (MarketRef / GovPrice)",
    fake_col, "Normalized Gap Score", "Risk Score", "Risk Level", "Listing Text"
] if c in sub.columns]
st.dataframe(sub[show_cols].sort_values("Unit Price (million VND/m²)", ascending=False), use_container_width=True, hide_index=True)

with st.expander("Legal disclaimer", expanded=False):
    st.markdown("""- This is an **academic demo**.
    - Listings are **asking prices**, not confirmed transaction prices.
    - Government prices depend on mapping (ward/street) and official rules.
    """)

import pandas as pd
import streamlit as st
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "RegTech_Data_Q1_Q5_2026.xlsx"

@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_excel(DATA_PATH, sheet_name="Listings Enriched")
    summary_by_district = pd.read_excel(DATA_PATH, sheet_name="Summary by District")
    top_streets = pd.read_excel(DATA_PATH, sheet_name="Top Streets")
    return df, summary_by_district, top_streets

import streamlit as st
import pandas as pd
import altair as alt
import io
import os

st.set_page_config(page_title="Consultant Billing Dashboard", layout="wide")
st.title("📊 Consultant Billing Dashboard")

@st.cache_data
def load_data(uploaded_file):
    df = pd.read_excel(uploaded_file, sheet_name=0)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Month'] = df['Date'].dt.strftime('%b')
    df['Year'] = df['Date'].dt.year
    return df

# Load file
uploaded_file = st.file_uploader("Upload the latest billing Excel file", type=["xlsx"])

if uploaded_file:
    df_all = load_data(uploaded_file)
else:
    default_file = "billing_data.xlsx"
    if os.path.exists(default_file):
        st.info("No file uploaded. Showing default dataset.")
        df_all = load_data(default_file)
    else:
        st.error("⚠️ Default file not found. Please upload the billing Excel file to continue.")
        st.stop()

# Example: Just show key metrics
st.subheader("📈 Key Metrics")
st.write(f"Number of rows loaded: {df_all.shape[0]}")
st.write(f"Date range: {df_all['Date'].min().date()} to {df_all['Date'].max().date()}")

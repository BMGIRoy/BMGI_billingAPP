
import streamlit as st
import pandas as pd
import altair as alt
import io
import os

st.set_page_config(page_title="Consultant Billing Dashboard", layout="wide")
st.title("📊 Consultant Billing Dashboard")

@st.cache_data
def load_data(file):
    df = pd.read_excel(file)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Month'] = df['Date'].dt.strftime('%b')
    df['Year'] = df['Date'].dt.year
    df['Month_Year_Fiscal'] = df['Date'].dt.to_period('M').dt.to_timestamp()
    return df

# File Upload or Fallback to Default
uploaded_file = st.file_uploader("Upload the latest billing Excel file", type=["xlsx"])
if uploaded_file is not None:
    df = load_data(uploaded_file)
    st.success("✅ Uploaded file used.")
else:
    default_path = "Book2.xlsx"
    if os.path.exists(default_path):
        df = load_data(default_path)
        st.info("ℹ️ Using default Book2.xlsx file.")
    else:
        st.error("❌ No uploaded file and Book2.xlsx not found.")
        st.stop()

# Key Metrics
st.subheader("📊 Key Metrics")
st.write(f"Number of rows loaded: {df.shape[0]}")
st.write(f"Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")

# Monthly Net Billing Trend
st.subheader("📅 Monthly Net Billing Trend")
monthly_trend = df.groupby("Month_Year_Fiscal")["Net Amount"].sum().reset_index()
monthly_trend = monthly_trend.sort_values("Month_Year_Fiscal")
chart = alt.Chart(monthly_trend).mark_line(point=True).encode(
    x=alt.X("Month_Year_Fiscal:T", title="Month-Year"),
    y=alt.Y("Net Amount:Q", title="Net Amount"),
    tooltip=["Month_Year_Fiscal", "Net Amount"]
).properties(width=1000)
st.altair_chart(chart, use_container_width=True)

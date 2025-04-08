
import streamlit as st
import pandas as pd
import altair as alt
import io
import os

st.set_page_config(page_title="Consultant Billing Dashboard", layout="wide")
st.title("📊 Consultant Billing Dashboard")

DEFAULT_FILE = "Book2.xlsx"

@st.cache_data
def load_data(path_or_file):
    df = pd.read_excel(path_or_file, sheet_name=0)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Month'] = df['Date'].dt.strftime('%b')
    df['Year'] = df['Date'].dt.year
    df['FiscalMonth'] = df['Date'].dt.month % 12 + 3
    df['FiscalMonth'] = df['FiscalMonth'].apply(lambda x: x if x <= 12 else x - 12)
    df['FiscalYear'] = df['Date'].dt.year.where(df['Date'].dt.month >= 4, df['Date'].dt.year - 1)
    df['Month_Year_Fiscal'] = pd.to_datetime(df['FiscalYear'].astype(str) + '-' + df['FiscalMonth'].astype(str) + '-01')
    df['Month_Year_Fiscal'] = df['Month_Year_Fiscal'].dt.strftime('%b %Y')
    return df

uploaded_file = st.file_uploader("Upload the latest billing Excel file", type=["xlsx"])

# Load from upload or fallback to default file
if uploaded_file:
    df_all = load_data(uploaded_file)
elif os.path.exists(DEFAULT_FILE):
    st.caption("Using default file from repo: Book2.xlsx")
    df_all = load_data(DEFAULT_FILE)
else:
    st.warning("Upload the Excel sheet to begin or ensure Book2.xlsx exists in the repo.")
    st.stop()

st.sidebar.header("🗂️ Column Mapping")

column_map = {}
expected_columns = {
    "Billed Amount": "Billed Amount",
    "Net Amount": "Net Amount",
    "Actual Days": "Actual Days",
    "Target Days": "Target Days",
    "Consultant": "Consultant",
    "Client": "Client",
    "Date": "Date",
    "Business Head": "Business Head"
}

for key in expected_columns:
    selected = st.sidebar.selectbox(f"Map '{key}' to:", df_all.columns.tolist(), index=df_all.columns.get_loc(expected_columns[key]) if expected_columns[key] in df_all.columns else 0)
    column_map[key] = selected

df_all.rename(columns=column_map, inplace=True)

st.sidebar.header("🔍 Filters")
consultants = st.sidebar.multiselect("Consultant", df_all[column_map['Consultant']].dropna().unique().tolist(), default=None)
clients = st.sidebar.multiselect("Client", df_all[column_map['Client']].dropna().unique().tolist(), default=None)
months = st.sidebar.multiselect("Month", df_all['Month'].dropna().unique().tolist(), default=None)
years = st.sidebar.multiselect("Year", df_all['Year'].dropna().unique().tolist(), default=None)
teams = st.sidebar.multiselect("Business Head", df_all[column_map['Business Head']].dropna().unique().tolist(), default=None)

df_filtered = df_all.copy()
if consultants:
    df_filtered = df_filtered[df_filtered[column_map['Consultant']].isin(consultants)]
if clients:
    df_filtered = df_filtered[df_filtered[column_map['Client']].isin(clients)]
if months:
    df_filtered = df_filtered[df_filtered['Month'].isin(months)]
if years:
    df_filtered = df_filtered[df_filtered['Year'].isin(years)]
if teams:
    df_filtered = df_filtered[df_filtered[column_map['Business Head']].isin(teams)]

# Key Metrics
st.subheader("📈 Key Metrics")
col1, col2 = st.columns(2)
col1.metric("Number of rows loaded", len(df_filtered))
if not df_filtered.empty:
    col2.metric("Date range", f"{df_filtered['Date'].min().date()} to {df_filtered['Date'].max().date()}")

# Charts
def chart_section(title, x, y, color, tooltip, data):
    st.subheader(title)
    chart = alt.Chart(data).mark_line(point=True).encode(
        x=alt.X(x, type="ordinal", sort=list(data[x].unique())),
        y=alt.Y(y, type="quantitative"),
        color=color,
        tooltip=tooltip
    ).properties(width=800)
    st.altair_chart(chart, use_container_width=True)

# Monthly Net Billing Trend
monthly_trend = df_filtered.groupby(['Month_Year_Fiscal', 'Year'])[column_map["Net Amount"]].sum().reset_index()
monthly_trend.sort_values("Month_Year_Fiscal", inplace=True)
chart_section("📅 Monthly Net Billing Trend", "Month_Year_Fiscal", column_map["Net Amount"], "Year:N", ['Month_Year_Fiscal', column_map["Net Amount"]], monthly_trend)

# Client Chart
st.subheader("👨‍💼 Net Billing by Client")
client_group = df_filtered.groupby(column_map["Client"])[column_map["Net Amount"]].sum().reset_index()
client_chart = alt.Chart(client_group).mark_bar().encode(
    x=column_map["Net Amount"],
    y=alt.Y(column_map["Client"], sort='-x'),
    tooltip=[column_map["Client"], column_map["Net Amount"]],
    color=alt.value("#1f77b4")
).properties(width=800)
st.altair_chart(client_chart, use_container_width=True)

# Consultant Chart
st.subheader("🧑‍⚕️ Billing by Consultant")
consultant_group = df_filtered.groupby(column_map["Consultant"])[column_map["Billed Amount"]].sum().reset_index()
consultant_chart = alt.Chart(consultant_group).mark_bar().encode(
    x=column_map["Consultant"],
    y=column_map["Billed Amount"],
    tooltip=[column_map["Consultant"], column_map["Billed Amount"]],
    color=alt.value("#2ca02c")
).properties(width=800)
st.altair_chart(consultant_chart, use_container_width=True)

# Team-wise Summary
st.subheader("👥 Team-wise Summary (Business Head)")
team_summary = df_filtered.groupby(column_map["Business Head"])[[column_map["Billed Amount"], column_map["Net Amount"]]].sum().reset_index()
st.dataframe(team_summary)

# Team-wise Chart
team_chart = alt.Chart(team_summary).mark_bar().encode(
    x=column_map["Net Amount"],
    y=alt.Y(column_map["Business Head"], sort='-x'),
    tooltip=[column_map["Business Head"], column_map["Net Amount"]],
    color=alt.value("#ff7f0e")
).properties(width=800)
st.altair_chart(team_chart, use_container_width=True)

# Month-wise Summary
st.subheader("📆 Month-wise Summary")
month_summary = df_filtered.groupby(['Year', 'Month'])[[column_map["Billed Amount"], column_map["Net Amount"]]].sum().reset_index()
st.dataframe(month_summary)

month_chart = alt.Chart(month_summary).mark_line(point=True).encode(
    x='Month:N',
    y=column_map["Net Amount"],
    color='Year:N',
    tooltip=['Month', column_map["Net Amount"]]
).properties(width=800)
st.altair_chart(month_chart, use_container_width=True)

# Download filtered data
st.sidebar.download_button(
    label="⬇️ Download Filtered Data",
    data=df_filtered.to_csv(index=False).encode('utf-8'),
    file_name="filtered_billing_data.csv",
    mime="text/csv"
)

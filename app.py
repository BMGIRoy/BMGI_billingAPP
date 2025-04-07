
import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Consultant Billing Dashboard", layout="wide")
st.title("📊 Consultant Billing Dashboard")

@st.cache_data
def load_data(uploaded_file):
    df = pd.read_excel(uploaded_file, sheet_name=0)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Month'] = df['Date'].dt.strftime('%b')
    df['Year'] = df['Date'].dt.year
    return df

uploaded_file = st.file_uploader("Upload the latest billing Excel file", type=["xlsx"])
if uploaded_file:
    df_all = load_data(uploaded_file)

    st.sidebar.markdown("ℹ️ [About this app](https://github.com/yourusername/yourrepo)")
    st.sidebar.header("🔍 Filters")

    consultant_options = df_all['Consultant'].dropna().unique().tolist()
    consultants = st.sidebar.multiselect("Consultant", consultant_options, default=consultant_options)

    client_options = df_all['Client'].dropna().unique().tolist()
    clients = st.sidebar.multiselect("Client", client_options, default=client_options)

    month_options = df_all['Month'].dropna().unique().tolist()
    months = st.sidebar.multiselect("Month", month_options, default=month_options)

    year_options = df_all['Year'].dropna().unique().tolist()
    years = st.sidebar.multiselect("Year", year_options, default=year_options)

    team_options = df_all['Business Head'].dropna().unique().tolist()
    teams = st.sidebar.multiselect("Business Head", team_options, default=team_options)

    df_filtered = df_all[
        df_all['Consultant'].isin(consultants) &
        df_all['Client'].isin(clients) &
        df_all['Month'].isin(months) &
        df_all['Year'].isin(years) &
        df_all['Business Head'].isin(teams)
    ]

    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Billed", f"₹{df_filtered['Billed Amount'].sum():,.0f}")
    col2.metric("Total Net Amount", f"₹{df_filtered['Net Amount'].sum():,.0f}")
    col3.metric("Actual Days", f"{df_filtered['Actual Days'].sum():.1f}")
    col4.metric("Target Days", f"{df_filtered['Target Days'].sum():.1f}")

    st.subheader("📊 Billing by Consultant")
    consultant_chart = alt.Chart(df_filtered).mark_bar().encode(
        x='Consultant',
        y='Billed Amount',
        color='Consultant',
        tooltip=['Consultant', 'Billed Amount']
    ).properties(width=800)
    st.altair_chart(consultant_chart, use_container_width=True)

    st.subheader("📆 Monthly Net Billing Trend")
    monthly_trend = df_filtered.groupby(['Year', 'Month'])['Net Amount'].sum().reset_index()
    monthly_trend['MonthYear'] = monthly_trend['Month'] + ' ' + monthly_trend['Year'].astype(str)
    line_chart = alt.Chart(monthly_trend).mark_line(point=True).encode(
        x='MonthYear:N',
        y='Net Amount:Q',
        tooltip=['MonthYear', 'Net Amount']
    ).properties(width=800)
    st.altair_chart(line_chart, use_container_width=True)

    st.subheader("🧑‍💼 Net Billing by Client")
    client_chart = alt.Chart(df_filtered).mark_bar().encode(
        x='Net Amount',
        y=alt.Y('Client', sort='-x'),
        color='Client',
        tooltip=['Client', 'Net Amount']
    ).properties(width=800)
    st.altair_chart(client_chart, use_container_width=True)

    st.subheader("👥 Team-Level Billing by Business Head")
    team_chart = alt.Chart(df_filtered).mark_bar().encode(
        x='Business Head',
        y='Net Amount',
        color='Business Head',
        tooltip=['Business Head', 'Net Amount']
    ).properties(width=800)
    st.altair_chart(team_chart, use_container_width=True)

    st.subheader("🗂️ Detailed Data Table")
    st.dataframe(df_filtered.reset_index(drop=True))

else:
    st.info("Upload the Excel sheet to begin.")

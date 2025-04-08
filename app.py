
import streamlit as st
import pandas as pd
import altair as alt
import io

st.set_page_config(page_title="Consultant Billing Dashboard", layout="wide")
st.title("📊 Consultant Billing Dashboard")

@st.cache_data
def load_data(uploaded_file):
    df = pd.read_excel(uploaded_file, sheet_name=0)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Month'] = df['Date'].dt.strftime('%b')
    df['Year'] = df['Date'].dt.year
    df['MonthNum'] = df['Date'].dt.month
    return df

uploaded_file = st.file_uploader("Upload the latest billing Excel file", type=["xlsx"])
if uploaded_file:
    df_all = load_data(uploaded_file)

    st.sidebar.markdown("ℹ️ [About this app](https://github.com/yourusername/yourrepo)")
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
        selected = st.sidebar.selectbox(
            f"Map '{key}' to:",
            df_all.columns.tolist(),
            index=df_all.columns.get_loc(expected_columns[key]) if expected_columns[key] in df_all.columns else 0
        )
        column_map[key] = selected

    df_all.rename(columns=column_map, inplace=True)

    st.sidebar.header("🔍 Filters")

    consultants = st.sidebar.multiselect("Consultant", df_all[column_map['Consultant']].dropna().unique(), default=df_all[column_map['Consultant']].dropna().unique())
    clients = st.sidebar.multiselect("Client", df_all[column_map['Client']].dropna().unique(), default=df_all[column_map['Client']].dropna().unique())
    months = st.sidebar.multiselect("Month", df_all['Month'].dropna().unique(), default=df_all['Month'].dropna().unique())
    years = st.sidebar.multiselect("Year", df_all['Year'].dropna().unique(), default=df_all['Year'].dropna().unique())
    teams = st.sidebar.multiselect("Business Head", df_all[column_map['Business Head']].dropna().unique(), default=df_all[column_map['Business Head']].dropna().unique())

    df_filtered = df_all[
        df_all[column_map['Consultant']].isin(consultants) &
        df_all[column_map['Client']].isin(clients) &
        df_all['Month'].isin(months) &
        df_all['Year'].isin(years) &
        df_all[column_map['Business Head']].isin(teams)
    ]

    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Billed", f"₹{df_filtered[column_map['Billed Amount']].sum():,.0f}")
    col2.metric("Total Net Amount", f"₹{df_filtered[column_map['Net Amount']].sum():,.0f}")
    col3.metric("Actual Days", f"{df_filtered[column_map['Actual Days']].sum():.1f}")
    col4.metric("Target Days", f"{df_filtered[column_map['Target Days']].sum():.1f}")

    st.subheader("🧑‍💼 Billing by Consultant")
    if df_filtered[column_map['Consultant']].nunique() > 0:
        consultant_chart = alt.Chart(df_filtered).mark_bar().encode(
            x=column_map['Consultant'],
            y=column_map['Billed Amount'],
            color=column_map['Consultant'],
            tooltip=[column_map['Consultant'], column_map['Billed Amount']]
        ).properties(width=800)
        st.altair_chart(consultant_chart, use_container_width=True)

    st.subheader("🏢 Net Billing by Client")
    client_data = df_filtered[[column_map['Client'], column_map['Net Amount']]].copy()
    client_grouped = client_data.groupby(column_map['Client'])[column_map['Net Amount']].sum().reset_index()
    if not client_grouped.empty:
        client_chart = alt.Chart(client_grouped).mark_bar().encode(
            x=column_map['Net Amount'],
            y=alt.Y(column_map['Client'], sort='-x'),
            color=alt.value("#1f77b4"),
            tooltip=[column_map['Client'], column_map['Net Amount']]
        ).properties(width=800)
        st.altair_chart(client_chart, use_container_width=True)

    st.subheader("👥 Team-Level Billing by Business Head")
    if df_filtered[column_map['Business Head']].nunique() > 0:
        team_chart = alt.Chart(df_filtered).mark_bar().encode(
            x=column_map['Business Head'],
            y=column_map['Net Amount'],
            color=column_map['Business Head'],
            tooltip=[column_map['Business Head'], column_map['Net Amount']]
        ).properties(width=800)
        st.altair_chart(team_chart, use_container_width=True)

    st.subheader("📆 Monthly Net Billing Trend")
    trend_df = df_filtered.copy()
    trend_df['Month_Year'] = pd.to_datetime(trend_df[column_map['Date']]).dt.to_period('M').astype(str)
    trend_df['Fiscal_Month'] = pd.to_datetime(trend_df[column_map['Date']]) + pd.offsets.MonthBegin(-3)
    trend_df['Month_Year_Fiscal'] = trend_df['Fiscal_Month'].dt.strftime('%b %Y')
    trend_summary = trend_df.groupby('Month_Year_Fiscal')[column_map['Net Amount']].sum().reset_index()
    trend_summary['MonthOrder'] = pd.to_datetime(trend_summary['Month_Year_Fiscal'], format='%b %Y')
    trend_summary = trend_summary.sort_values('MonthOrder')
    trend_chart = alt.Chart(trend_summary).mark_line(point=True).encode(
        x=alt.X('Month_Year_Fiscal:N', sort=trend_summary['Month_Year_Fiscal'].tolist()),
        y=alt.Y(column_map['Net Amount'], title='Net Amount'),
        tooltip=['Month_Year_Fiscal', column_map['Net Amount']]
    ).properties(width=800)
    st.altair_chart(trend_chart, use_container_width=True)

    st.subheader("📅 Month-wise Summary")
    df_filtered["Month"] = pd.to_datetime(df_filtered[column_map["Date"]]).dt.strftime("%b")
    df_filtered["Year"] = pd.to_datetime(df_filtered[column_map["Date"]]).dt.year
    df_filtered["Month_Num"] = pd.to_datetime(df_filtered[column_map["Date"]]).dt.month
    month_summary = df_filtered.groupby(["Year", "Month", "Month_Num"])[[column_map["Billed Amount"], column_map["Net Amount"]]].sum().reset_index()
    month_summary = month_summary.sort_values(["Year", "Month_Num"])
    st.dataframe(month_summary)

    st.subheader("👥 Team-wise Summary")
    team_summary = df_filtered.groupby(column_map["Business Head"])[[column_map["Billed Amount"], column_map["Net Amount"]]].sum().reset_index()
    st.dataframe(team_summary)

    st.subheader("🗂️ Full Filtered Data")
    st.dataframe(df_filtered.reset_index(drop=True))

    st.sidebar.markdown("### 📤 Export Data")
    export_df = df_filtered.copy()
    excel_data = io.BytesIO()
    with pd.ExcelWriter(excel_data, engine="xlsxwriter") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Filtered Data")
    st.sidebar.download_button(
        label="Download Filtered Data as Excel",
        data=excel_data.getvalue(),
        file_name="filtered_billing_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Upload the Excel sheet to begin.")

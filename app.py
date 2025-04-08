# Consultant Billing Dashboard with full charts + tables + fiscal sort
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
    return df

# Fiscal month order mapping
fiscal_order = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
fiscal_map = {month: i for i, month in enumerate(fiscal_order)}

uploaded_file = st.file_uploader("Upload the latest billing Excel file", type=["xlsx"])
if uploaded_file:
    df_all = load_data(uploaded_file)
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
        selected = st.sidebar.selectbox(f"Map '{key}' to:", df_all.columns.tolist(),
            index=df_all.columns.get_loc(expected_columns[key]) if expected_columns[key] in df_all.columns else 0)
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

    # Metrics
    st.subheader(":bar_chart: Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Billed", f"₹{df_filtered[column_map['Billed Amount']].sum():,.0f}")
    col2.metric("Total Net Amount", f"₹{df_filtered[column_map['Net Amount']].sum():,.0f}")
    col3.metric("Actual Days", f"{df_filtered[column_map['Actual Days']].sum():.1f}")
    col4.metric("Target Days", f"{df_filtered[column_map['Target Days']].sum():.1f}")

    # Monthly Billing Trend
    st.subheader(":calendar: Monthly Net Billing Trend")
    trend = df_filtered.groupby(['Year', 'Month'])[column_map['Net Amount']].sum().reset_index()
    trend['Month_Num'] = trend['Month'].map(fiscal_map)
    trend = trend.sort_values(['Year', 'Month_Num'])
    trend['Month_Year_Fiscal'] = trend['Month'] + ' ' + trend['Year'].astype(str)

    chart = alt.Chart(trend).mark_line(point=True).encode(
        x=alt.X('Month_Year_Fiscal:N', sort=list(trend['Month_Year_Fiscal'].unique())),
        y=alt.Y(column_map['Net Amount'], title='Net Amount'),
        tooltip=['Month_Year_Fiscal', column_map['Net Amount']]
    ).properties(width=800)
    st.altair_chart(chart, use_container_width=True)

    # Net Billing by Client
    st.subheader(":man_office_worker: Net Billing by Client")
    client_grouped = df_filtered.groupby(column_map['Client'])[column_map['Net Amount']].sum().reset_index()
    chart = alt.Chart(client_grouped).mark_bar().encode(
        x=column_map['Net Amount'], y=alt.Y(column_map['Client'], sort='-x'), color=alt.value('#1f77b4'),
        tooltip=[column_map['Client'], column_map['Net Amount']]
    ).properties(width=800)
    st.altair_chart(chart, use_container_width=True)

    # Billing by Consultant
    st.subheader(":busts_in_silhouette: Billing by Consultant")
    chart = alt.Chart(df_filtered).mark_bar().encode(
        x=column_map['Consultant'], y=column_map['Billed Amount'], color=column_map['Consultant'],
        tooltip=[column_map['Consultant'], column_map['Billed Amount']]
    ).properties(width=800)
    st.altair_chart(chart, use_container_width=True)

    # Team-Level Billing
    st.subheader(":office: Team-Level Billing by Business Head")
    team_chart = alt.Chart(df_filtered).mark_bar().encode(
        x=column_map['Business Head'], y=column_map['Net Amount'], color=column_map['Business Head'],
        tooltip=[column_map['Business Head'], column_map['Net Amount']]
    ).properties(width=800)
    st.altair_chart(team_chart, use_container_width=True)

    # Detailed Table
    st.subheader(":card_index_dividers: Detailed Data Table")
    st.dataframe(df_filtered.reset_index(drop=True))

    # Month-wise Summary Table + Chart
    st.subheader(":calendar: Month-wise Summary")
    df_filtered['Month_Num'] = df_filtered['Month'].map(fiscal_map)
    month_summary = df_filtered.groupby(['Year', 'Month', 'Month_Num'])[[column_map['Billed Amount'], column_map['Net Amount']]].sum().reset_index()
    month_summary = month_summary.sort_values(['Year', 'Month_Num'])
    st.dataframe(month_summary)

    chart = alt.Chart(month_summary).mark_line(point=True).encode(
        x=alt.X('Month', sort=fiscal_order),
        y=column_map['Net Amount'], color='Year:N',
        tooltip=['Month', 'Year', column_map['Net Amount']]
    ).properties(width=800)
    st.altair_chart(chart, use_container_width=True)

    # Team-wise Summary Table + Chart
    st.subheader(":busts_in_silhouette: Team-wise Summary")
    team_summary = df_filtered.groupby(column_map['Business Head'])[[column_map['Billed Amount'], column_map['Net Amount']]].sum().reset_index()
    st.dataframe(team_summary)

    chart = alt.Chart(team_summary).mark_bar().encode(
        x=column_map['Net Amount'], y=alt.Y(column_map['Business Head'], sort='-x'),
        color=alt.value('#4c78a8'), tooltip=[column_map['Business Head'], column_map['Net Amount']]
    ).properties(width=800)
    st.altair_chart(chart, use_container_width=True)

    # Export
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

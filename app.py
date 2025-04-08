
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
        selected = st.sidebar.selectbox(f"Map '{key}' to:", df_all.columns.tolist(), index=df_all.columns.get_loc(expected_columns[key]) if expected_columns[key] in df_all.columns else 0)
        column_map[key] = selected

    df_all.rename(columns=column_map, inplace=True)

    st.sidebar.header("🔍 Filters")

    consultant_options = df_all[column_map['Consultant']].dropna().unique().tolist()
    consultants = st.sidebar.multiselect("Consultant", consultant_options, default=consultant_options)

    client_options = df_all[column_map['Client']].dropna().unique().tolist()
    clients = st.sidebar.multiselect("Client", client_options, default=client_options)

    month_options = df_all['Month'].dropna().unique().tolist()
    months = st.sidebar.multiselect("Month", month_options, default=month_options)

    year_options = df_all['Year'].dropna().unique().tolist()
    years = st.sidebar.multiselect("Year", year_options, default=year_options)

    team_options = df_all[column_map['Business Head']].dropna().unique().tolist()
    teams = st.sidebar.multiselect("Business Head", team_options, default=team_options)

    required_mapped_cols = ['Billed Amount', 'Net Amount', 'Actual Days', 'Target Days']
    missing_mappings = [key for key in required_mapped_cols if key not in column_map or column_map[key] not in df_all.columns]

    if missing_mappings:
        st.error(f"⚠️ Please make sure these columns are mapped correctly: {', '.join(missing_mappings)}")
        st.stop()

    df_filtered = df_all[
        df_all[column_map['Consultant']].isin(consultants) &
        df_all[column_map['Client']].isin(clients) &
        df_all['Month'].isin(months) &
        df_all['Year'].isin(years) &
        df_all[column_map['Business Head']].isin(teams)
    ]

    # Metrics
    billed_total = df_filtered[column_map['Billed Amount']].sum()
    net_total = df_filtered[column_map['Net Amount']].sum()
    actual_total = df_filtered[column_map['Actual Days']].sum()
    target_total = df_filtered[column_map['Target Days']].sum()

    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Billed", f"₹{billed_total:,.0f}")
    col2.metric("Total Net Amount", f"₹{net_total:,.0f}")
    col3.metric("Actual Days", f"{actual_total:.1f}")
    col4.metric("Target Days", f"{target_total:.1f}")

    # Monthly Trend (Fiscal Year)
    st.subheader("📆 Monthly Net Billing Trend")
    monthly_trend = df_filtered.copy()
    monthly_trend['MonthNum'] = pd.to_datetime(monthly_trend[column_map["Date"]]).dt.month
    monthly_trend['FiscalYear'] = pd.to_datetime(monthly_trend[column_map["Date"]]).apply(lambda d: d.year if d.month >= 4 else d.year - 1)
    monthly_trend['Month'] = pd.to_datetime(monthly_trend[column_map["Date"]]).dt.strftime('%b')

    order = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
    monthly_summary = monthly_trend.groupby(['FiscalYear', 'Month', 'MonthNum'])[column_map["Net Amount"]].sum().reset_index()
    monthly_summary['Month'] = pd.Categorical(monthly_summary['Month'], categories=order, ordered=True)
    monthly_summary = monthly_summary.sort_values(by=['FiscalYear', 'Month'])

    line_chart = alt.Chart(monthly_summary).mark_line(point=True).encode(
        x=alt.X('Month:N', sort=order),
        y=alt.Y(column_map["Net Amount"], title="Net Amount"),
        color='FiscalYear:N',
        tooltip=['FiscalYear', 'Month', column_map["Net Amount"]]
    ).properties(width=900)
    st.altair_chart(line_chart, use_container_width=True)

    # Export section
    st.subheader("🗂️ Detailed Data Table")
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

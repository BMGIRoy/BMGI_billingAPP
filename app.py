
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
    df['Month_Num'] = df['Date'].dt.month
    return df

month_order = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']

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

    consultants = st.sidebar.multiselect("Consultant", df_all[column_map['Consultant']].dropna().unique(), default=df_all[column_map['Consultant']].dropna().unique())
    clients = st.sidebar.multiselect("Client", df_all[column_map['Client']].dropna().unique(), default=df_all[column_map['Client']].dropna().unique())
    months = st.sidebar.multiselect("Month", month_order, default=month_order)
    years = st.sidebar.multiselect("Year", df_all['Year'].dropna().unique(), default=df_all['Year'].dropna().unique())
    teams = st.sidebar.multiselect("Business Head", df_all[column_map['Business Head']].dropna().unique(), default=df_all[column_map['Business Head']].dropna().unique())

    df_filtered = df_all[
        df_all[column_map['Consultant']].isin(consultants) &
        df_all[column_map['Client']].isin(clients) &
        df_all['Month'].isin(months) &
        df_all['Year'].isin(years) &
        df_all[column_map['Business Head']].isin(teams)
    ]

    # Summary and trend
    st.subheader("📅 Month-wise Summary")
    df_filtered['Month'] = pd.Categorical(df_filtered['Month'], categories=month_order, ordered=True)
    month_summary = df_filtered.groupby(['Year', 'Month'])[[column_map['Billed Amount'], column_map['Net Amount']]].sum().reset_index().sort_values(by=['Year', 'Month'])
    st.dataframe(month_summary)

    chart = alt.Chart(month_summary).mark_line(point=True).encode(
        x=alt.X('Month:N', sort=month_order),
        y=alt.Y(column_map['Net Amount'], title='Net Amount'),
        color='Year:N',
        tooltip=['Year', 'Month', column_map['Net Amount']]
    ).properties(width=800)
    st.altair_chart(chart, use_container_width=True)

    # Export option
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        month_summary.to_excel(writer, index=False)
    st.download_button(
        label="Download Month-wise Summary",
        data=excel_buffer.getvalue(),
        file_name="month_wise_summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Upload the Excel sheet to begin.")

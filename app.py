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

uploaded_file = st.file_uploader("Upload the latest billing Excel file", type=["xlsx"])
if uploaded_file:
    df_all = load_data(uploaded_file)
    st.sidebar.markdown("ℹ️ [About this app](https://github.com/yourusername/yourrepo)")
    st.sidebar.header("📂️ Column Mapping")

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
    months = st.sidebar.multiselect("Month", df_all['Month'].dropna().unique(), default=df_all['Month'].dropna().unique())
    years = st.sidebar.multiselect("Year", df_all['Year'].dropna().unique(), default=df_all['Year'].dropna().unique())
    teams = st.sidebar.multiselect("Business Head", df_all[column_map['Business Head']].dropna().unique(), default=df_all[column_map['Business Head']].dropna().unique())

    required_cols = ['Billed Amount', 'Net Amount', 'Actual Days', 'Target Days']
    missing = [col for col in required_cols if col not in column_map or column_map[col] not in df_all.columns]

    if missing:
        st.error(f"⚠️ Please map the following correctly: {', '.join(missing)}")
        st.stop()

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

    st.subheader("📊 Billing by Consultant")
    if df_filtered[column_map['Consultant']].nunique() > 0:
        st.altair_chart(
            alt.Chart(df_filtered).mark_bar().encode(
                x=column_map['Consultant'],
                y=column_map['Billed Amount'],
                color=column_map['Consultant'],
                tooltip=[column_map['Consultant'], column_map['Billed Amount']]
            ).properties(width=800),
            use_container_width=True
        )

    st.subheader("📆 Monthly Net Billing Trend")
    monthly_trend = df_filtered.groupby(['Year', 'Month'])[column_map['Net Amount']].sum().reset_index()
    if not monthly_trend.empty:
        monthly_trend['MonthYear'] = monthly_trend['Month'] + ' ' + monthly_trend['Year'].astype(str)
        st.altair_chart(
            alt.Chart(monthly_trend).mark_line(point=True).encode(
                x=alt.X('MonthYear:N', sort=None),
                y=alt.Y(column_map['Net Amount'], title="Net Amount"),
                tooltip=['MonthYear', column_map['Net Amount']]
            ).properties(width=800),
            use_container_width=True
        )

    st.subheader("🧑‍💼 Net Billing by Client")
    client_summary = df_filtered.groupby(column_map['Client'])[column_map['Net Amount']].sum().reset_index()
    if not client_summary.empty:
        st.altair_chart(
            alt.Chart(client_summary).mark_bar().encode(
                x=column_map['Net Amount'],
                y=alt.Y(column_map['Client'], sort='-x'),
                tooltip=[column_map['Client'], column_map['Net Amount']]
            ).properties(width=800),
            use_container_width=True
        )

    st.subheader("👥 Team-wise Net Billing Summary")
    team_summary = df_filtered.groupby(column_map['Business Head'])[[column_map['Billed Amount'], column_map['Net Amount']]].sum().reset_index()
    if not team_summary.empty:
        st.altair_chart(
            alt.Chart(team_summary).mark_bar().encode(
                x=column_map['Net Amount'],
                y=alt.Y(column_map['Business Head'], sort='-x'),
                tooltip=[column_map['Business Head'], column_map['Net Amount']]
            ).properties(width=800),
            use_container_width=True
        )
        st.dataframe(team_summary)

    st.subheader("📅 Month-wise Summary")
    month_summary = df_filtered.groupby(['Year', 'Month'])[[column_map['Billed Amount'], column_map['Net Amount']]].sum().reset_index()
    if not month_summary.empty:
        st.altair_chart(
            alt.Chart(month_summary).mark_line(point=True).encode(
                x=alt.X('Month', sort=None),
                y=column_map['Net Amount'],
                color='Year:N',
                tooltip=['Year', 'Month', column_map['Net Amount']]
            ).properties(width=800),
            use_container_width=True
        )
        st.dataframe(month_summary)

    st.subheader("📋 Full Data Table")
    st.dataframe(df_filtered.reset_index(drop=True))


import streamlit as st
import pandas as pd

# Upload file
st.title("⚡ Energy Price Estimator with Markup")
uploaded_file = st.file_uploader("Upload your energy price Excel file", type=["xlsx"])
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    # Parse datetime if not already parsed
    if not pd.api.types.is_datetime64_any_dtype(df['Date/Time CET/CEST']):
        df['Date/Time CET/CEST'] = pd.to_datetime(df['Date/Time CET/CEST'])

    # Add derived columns
    df['Hour'] = df['Date/Time CET/CESTe'].dt.hour
    df['Month'] = df['Date/Time CET/CEST'].dt.month
    df['Weekday'] = df['Date/Time CET/CEST'].dt.weekday
    df['Week_Number'] = df['Date/Time CET/CEST'].dt.isocalendar().week

    # Define seasons
    def get_season(month):
        if month in [12, 1, 2]:
            return 'Winter'
        elif month in [3, 4, 5]:
            return 'Spring'
        elif month in [6, 7, 8]:
            return 'Summer'
        else:
            return 'Autumn'
    
    df['Season'] = df['Month'].apply(get_season)

    st.sidebar.header("🔍 Filters")

    # Filters
    hour_range = st.sidebar.slider("Hour Range", 0, 23, (0, 23))
    months = st.sidebar.multiselect("Month(s)", options=list(range(1,13)), default=[1])
    weekdays = st.sidebar.multiselect("Weekday(s)", options=list(range(7)), format_func=lambda x: ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][x], default=[0])
    weeks = st.sidebar.multiselect("Week Number(s)", options=list(range(1, 54)), default=[1])
    seasons = st.sidebar.multiselect("Season(s)", options=df['Season'].unique(), default=['Winter'])

    # Filter data
    filtered_df = df[
        (df['Hour'] >= hour_range[0]) & (df['Hour'] <= hour_range[1]) &
        (df['Month'].isin(months)) &
        (df['Weekday'].isin(weekdays)) &
        (df['Week_Number'].isin(weeks)) &
        (df['Season'].isin(seasons))
    ]

    if filtered_df.empty:
        st.warning("No data found for the selected filters.")
    else:
        avg_price = filtered_df['Energy Price [EUR/MWh]'].mean()
        markup_price = avg_price * 1.20

        st.subheader("📊 Results")
        st.write(f"**Average Price**: {avg_price:.2f} EUR/MWh")
        st.write(f"**Price with 20% Markup**: {markup_price:.2f} EUR/MWh")
        st.line_chart(filtered_df.set_index('DateTime')['Energy Price [EUR/MWh]'])

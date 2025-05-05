import streamlit as st
import pandas as pd

# Streamlit file upload
uploaded_file = st.file_uploader("Upload your energy data file", type=['xlsx'])
if uploaded_file is not None:
    # Load the dataset
    df = pd.read_excel(uploaded_file)

    # Convert 'Date/Time CET/CEST' column to datetime type
    df['Date/Time CET/CEST'] = pd.to_datetime(df['Date/Time CET/CEST'])

    # Add time-related columns
    df['Year'] = df['Date/Time CET/CEST'].dt.year
    df['Month'] = df['Date/Time CET/CEST'].dt.month
    df['Day'] = df['Date/Time CET/CEST'].dt.day
    df['Weekday'] = df['Date/Time CET/CEST'].dt.weekday  # 0=Monday
    df['Hour'] = df['Date/Time CET/CEST'].dt.hour
    df['Week'] = df['Date/Time CET/CEST'].dt.isocalendar().week
    df['Weekday_Name'] = df['Weekday'].map({
        0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
        4: 'Friday', 5: 'Saturday', 6: 'Sunday'
    })

    # Define Weekday/Weekend and Day/Night
    df['Weekday/Weekend'] = df['Weekday'].apply(lambda x: 'Weekday' if x < 5 else 'Weekend')
    df['Day/Night'] = df['Hour'].apply(lambda x: 'Day' if 8 <= x < 20 else 'Night')

    # Define season
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

    # Exclude war-related high price period
    df_clean = df[~((df['Year'] == 2022) & (df['Month'].between(3, 9)))]

    # UI
    st.title("🔌 Energy Price Explorer")

    st.sidebar.header("📊 Filter Options")
    hour_range = st.sidebar.slider("Select Hour Range", 0, 23, (0, 23))
    months = st.sidebar.multiselect("Select Month(s)", list(range(1, 13)), default=list(range(1, 13)))
    weekdays = st.sidebar.multiselect("Select Weekday(s) (0=Mon)", list(range(0, 7)), default=list(range(0, 7)))
    weeks = st.sidebar.multiselect("Select Week Number(s)", sorted(df_clean['Week'].unique()), default=sorted(df_clean['Week'].unique()))
    seasons = st.sidebar.multiselect("Select Season(s)", ['Winter', 'Spring', 'Summer', 'Autumn'], default=['Winter', 'Spring', 'Summer', 'Autumn'])

    # Apply filters
    filtered = df_clean[
        (df_clean['Hour'] >= hour_range[0]) & (df_clean['Hour'] <= hour_range[1]) &
        (df_clean['Month'].isin(months)) &
        (df_clean['Weekday'].isin(weekdays)) &
        (df_clean['Week'].isin(weeks)) &
        (df_clean['Season'].isin(seasons))
    ]

    # Debug: Show filtered data size
    st.write(f"Filtered data contains {filtered.shape[0]} rows")

    # Result section
    st.subheader("📈 Average Energy Price for Selected Filters")

    if filtered.empty:
        st.warning("No data available for selected filters.")
    else:
        # Compute overall average
        avg_price = filtered['Energy Price [EUR/MWh]'].mean()
        st.metric(label="Average Price [EUR/MWh]", value=f"{avg_price:.2f}")

        # Optional: Show per-year average
        yearly_avg = filtered.groupby('Year')['Energy Price [EUR/MWh]'].mean()
        st.write("Average Price per Year:")
        st.dataframe(yearly_avg.reset_index().rename(columns={"Energy Price [EUR/MWh]": "Average Price (EUR/MWh)"}))

        # Optional: Show line chart
        st.line_chart(filtered.set_index('Date/Time CET/CEST')['Energy Price [EUR/MWh]'])

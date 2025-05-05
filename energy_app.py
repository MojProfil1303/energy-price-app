import streamlit as st
import pandas as pd

# Streamlit file upload
uploaded_file = st.file_uploader("Upload your energy data file", type=['xlsx'])

if uploaded_file is not None:
    # Load the dataset
    df = pd.read_excel(uploaded_file)

    # Ensure correct datetime parsing
    df['Date/Time CET/CEST'] = pd.to_datetime(df['Date/Time CET/CEST'])

    # Add time-related columns
    df['Year'] = df['Date/Time CET/CEST'].dt.year
    df['Month'] = df['Date/Time CET/CEST'].dt.month
    df['Day'] = df['Date/Time CET/CEST'].dt.day
    df['Hour'] = df['Date/Time CET/CEST'].dt.hour
    df['Weekday'] = df['Date/Time CET/CEST'].dt.weekday  # 0=Monday
    df['Week'] = df['Date/Time CET/CEST'].dt.isocalendar().week.astype(int)

    # Weekday Name
    df['Weekday_Name'] = df['Weekday'].map({
        0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
        4: 'Friday', 5: 'Saturday', 6: 'Sunday'
    })

    # Weekday/Weekend
    df['Weekday/Weekend'] = df['Weekday'].apply(lambda x: 'Weekday' if x < 5 else 'Weekend')

    # Day/Night
    df['Day/Night'] = df['Hour'].apply(lambda x: 'Day' if 8 <= x < 20 else 'Night')

    # Seasons
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

    # Exclude 2022 March–Sept (war-related spike)
    df_clean = df[~((df['Year'] == 2022) & (df['Month'].between(3, 9)))]

    # Streamlit UI
    st.title("🔌 Energy Price Explorer")

    st.sidebar.header("📊 Filter Options")

    # Use dynamic options from the data
    hour_range = st.sidebar.slider("Select Hour Range", 0, 23, (0, 23))
    months = st.sidebar.multiselect("Select Month(s)", sorted(df_clean['Month'].unique()), default=sorted(df_clean['Month'].unique()))
    weekdays = st.sidebar.multiselect("Select Weekday(s)", sorted(df_clean['Weekday'].unique()), default=sorted(df_clean['Weekday'].unique()))
    weeks = st.sidebar.multiselect("Select Week Number(s)", sorted(df_clean['Week'].unique()), default=sorted(df_clean['Week'].unique()))
    seasons = st.sidebar.multiselect("Select Season(s)", sorted(df_clean['Season'].unique()), default=sorted(df_clean['Season'].unique()))

    # Apply filters
    filtered = df_clean[
        (df_clean['Hour'] >= hour_range[0]) & (df_clean['Hour'] <= hour_range[1]) &
        (df_clean['Month'].isin(months)) &
        (df_clean['Weekday'].isin(weekdays)) &
        (df_clean['Week'].isin(weeks)) &
        (df_clean['Season'].isin(seasons))
    ]

    # Debug: Show filtered data size
    st.write(f"📌 Filtered data contains `{filtered.shape[0]}` rows")

    # Result section
    st.subheader("📈 Average Energy Price for Selected Filters")

    if filtered.empty:
        st.warning("⚠️ No data available for selected filters.")
    else:
        # Compute overall average
        avg_price = filtered['Energy Price [EUR/MWh]'].mean()
        st.metric(label="Average Price [EUR/MWh]", value=f"{avg_price:.2f}")

        # Per-year average
        yearly_avg = filtered.groupby('Year')['Energy Price [EUR/MWh]'].mean()
        st.write("📅 Average Price per Year:")
        st.dataframe(yearly_avg.reset_index().rename(columns={"Energy Price [EUR/MWh]": "Average Price (EUR/MWh)"}))

        # Line chart
        st.line_chart(filtered.set_index('Date/Time CET/CEST')['Energy Price [EUR/MWh]'])

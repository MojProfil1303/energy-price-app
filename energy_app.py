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
    df['Weekday/Weekend'] = df['Weekday'].apply(lambda x: 'Weekday' if x < 5 else 'Weekend')
    df['Day/Night'] = df['Hour'].apply(lambda x: 'Day' if 8 <= x < 20 else 'Night')

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

    # Recreate necessary columns for filtered dataframe
    df_clean['Weekday_Name'] = df_clean['Weekday'].map({
        0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
        4: 'Friday', 5: 'Saturday', 6: 'Sunday'
    })

    # Precomputed averages (from Colab-style logic)
    hourly_avg = df_clean.groupby('Hour')['Energy Price [EUR/MWh]'].mean()
    daily_avg = df_clean.groupby(df_clean['Date/Time CET/CEST'].dt.date)['Energy Price [EUR/MWh]'].mean()
    weekly_avg = df_clean.groupby('Week')['Energy Price [EUR/MWh]'].mean()
    monthly_avg = df_clean.groupby('Month')['Energy Price [EUR/MWh]'].mean()
    seasonal_avg = df_clean.groupby('Season')['Energy Price [EUR/MWh]'].mean()
    yearly_avg = df_clean.groupby('Year')['Energy Price [EUR/MWh]'].mean()
    weekday_avg = df_clean.groupby('Weekday_Name')['Energy Price [EUR/MWh]'].mean()

    # UI
    st.title("🔌 Energy Price Explorer")

    st.sidebar.header("📊 Filter Options")
    hour_range = st.sidebar.slider("Select Hour Range", 0, 23, (0, 23))
    months = st.sidebar.multiselect("Select Month(s)", list(range(1, 13)), default=list(range(1, 13)))
    weekdays = st.sidebar.multiselect("Select Weekday(s) (0=Mon)", list(range(0, 7)), default=list(range(0, 7)))
    weeks = st.sidebar.multiselect("Select Week Number(s)", sorted(df_clean['Week'].unique()), default=sorted(df_clean['Week'].unique()))
    seasons = st.sidebar.multiselect("Select Season(s)", ['Winter', 'Spring', 'Summer', 'Autumn'], default=['Winter', 'Spring', 'Summer', 'Autumn'])

    # Filter using cleaned data
    filtered = df_clean[
        (df_clean['Hour'] >= hour_range[0]) & (df_clean['Hour'] <= hour_range[1]) &
        (df_clean['Month'].isin(months)) &
        (df_clean['Weekday'].isin(weekdays)) &
        (df_clean['Week'].isin(weeks)) &
        (df_clean['Season'].isin(seasons))
    ]

    # Result section
    st.subheader("📈 Average Energy Price for Selected Filters")

    if filtered.empty:
        st.warning("No data available for selected filters.")
    else:
        # Use precomputed average if only 1 value selected in each filter
        if hour_range[0] == hour_range[1] and \
           len(months) == 1 and \
           len(weekdays) == 1 and \
           len(weeks) == 1 and \
           len(seasons) == 1:
            selected_hour = hour_range[0]
            selected_month = months[0]
            selected_week = weeks[0]
            selected_weekday = weekdays[0]
            selected_season = seasons[0]

            # Get weekday name
            weekday_name = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
                            4: 'Friday', 5: 'Saturday', 6: 'Sunday'}[selected_weekday]

            # Safely fetch each average (guard against missing keys)
            avg_hour = hourly_avg.get(selected_hour, None)
            avg_month = monthly_avg.get(selected_month, None)
            avg_week = weekly_avg.get(selected_week, None)
            avg_season = seasonal_avg.get(selected_season, None)
            avg_weekday = weekday_avg.get(weekday_name, None)

            # Show results
            if avg_hour: st.metric("Hourly Average", f"{avg_hour:.2f} EUR/MWh")
            if avg_month: st.metric("Monthly Average", f"{avg_month:.2f} EUR/MWh")
            if avg_week: st.metric("Weekly Average", f"{avg_week:.2f} EUR/MWh")
            if avg_season: st.metric("Seasonal Average", f"{avg_season:.2f} EUR/MWh")
            if avg_weekday: st.metric("Weekday Average", f"{avg_weekday:.2f} EUR/MWh")

        else:
            # General fallback for multiple selections
            avg_price = filtered['Energy Price [EUR/MWh]'].mean()
            st.metric(label="Average Price [EUR/MWh]", value=f"{avg_price:.2f}")

        # Line chart for filtered data
        st.line_chart(filtered.set_index('Date/Time CET/CEST')['Energy Price [EUR/MWh]'])

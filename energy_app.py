import streamlit as st
import pandas as pd

# Streamlit file upload
uploaded_file = st.file_uploader("Upload your energy data file", type=['xlsx'])
if uploaded_file is not None:
    # Load the dataset
    df = pd.read_excel(uploaded_file)

    # Convert 'Date/Time CET/CEST' column to datetime type
    df['Date/Time CET/CEST'] = pd.to_datetime(df['Date/Time CET/CEST'])

    st.write(df.head())  # Show first few rows to confirm structure

    # Add necessary columns for easy filtering
    # Extract year, month, day, weekday, hour, week, and day part (day/night)
    df['Year'] = df['Date/Time CET/CEST'].dt.year
    df['Month'] = df['Date/Time CET/CEST'].dt.month
    df['Day'] = df['Date/Time CET/CEST'].dt.day
    df['Weekday'] = df['Date/Time CET/CEST'].dt.weekday  # Monday=0, Sunday=6
    df['Hour'] = df['Date/Time CET/CEST'].dt.hour
    df['Week'] = df['Date/Time CET/CEST'].dt.isocalendar().week

    # Create a new column to identify whether the day is a weekday or weekend
    df['Weekday/Weekend'] = df['Date/Time CET/CEST'].dt.dayofweek

    # 0-4 = Weekdays (Monday to Friday), 5-6 = Weekend (Saturday and Sunday)
    df['Weekday/Weekend'] = df['Weekday/Weekend'].apply(lambda x: 'Weekday' if x < 5 else 'Weekend')

    # Determine day or night based on the hour
    df['Day/Night'] = df['Hour'].apply(lambda x: 'Day' if 8 <= x < 20 else 'Night')

    # Function to map months to seasons
    def get_season(month):
       if month in [12, 1, 2]:
          return 'Winter'
       elif month in [3, 4, 5]:
          return 'Spring'
       elif month in [6, 7, 8]:
          return 'Summer'
       else:
          return 'Autumn'

    # Apply the function to your data
    df['Season'] = df['Month'].apply(get_season)

    # Filter high prices
    high_price_threshold = df['Energy Price [EUR/MWh]'].quantile(0.75)
    high_prices = df[df['Energy Price [EUR/MWh]'] >= high_price_threshold]
    # Exclude the year 2022
    high_prices_not_2022 = high_prices[high_prices['Date/Time CET/CEST'].dt.year != 2022]
    # Exclude March to September 2022 (war-driven high price months)
    df_clean = df[~((df['Year'] == 2022) & (df['Month'].between(3,9)))]

    # Calculate Averages
    hourly_avg = df_clean.groupby('Hour')['Energy Price [EUR/MWh]'].mean()
    daily_avg = df_clean.groupby(df['Date/Time CET/CEST'].dt.date)['Energy Price [EUR/MWh]'].mean()
    weekly_avg = df_clean.groupby('Week')['Energy Price [EUR/MWh]'].mean()
    monthly_avg = df_clean.groupby('Month')['Energy Price [EUR/MWh]'].mean()
    seasonal_avg = df_clean.groupby('Season')['Energy Price [EUR/MWh]'].mean()
    yearly_avg = df_clean.groupby('Year')['Energy Price [EUR/MWh]'].mean()

    # Define peak and off-peak hour ranges
    peak_hours = list(range(8, 21))  # 8 AM to 8 PM
    off_peak_hours = list(range(0, 8)) + list(range(20, 24))  # 00:00–08:00 and 20:00–00:00

    # Extract hour from 'Date/Time CET/CEST'
    df_clean['Hour'] = df_clean['Date/Time CET/CEST'].dt.hour

    # Filter data for peak hours and off-peak hours
    df_peak = df_clean[df_clean['Hour'].isin(peak_hours)]
    df_off_peak = df_clean[df_clean['Hour'].isin(off_peak_hours)]

    # Calculate average energy prices for peak and off-peak hours
    avg_peak_price = df_peak['Energy Price [EUR/MWh]'].mean()
    avg_off_peak_price = df_off_peak['Energy Price [EUR/MWh]'].mean()

    # Calculate average energy price for Weekdays and Weekends
    weekday_avg = df_clean[df_clean['Weekday/Weekend'] == 'Weekday']['Energy Price [EUR/MWh]'].mean()
    weekend_avg = df_clean[df_clean['Weekday/Weekend'] == 'Weekend']['Energy Price [EUR/MWh]'].mean()

    # Map the numeric weekday (0-6) to day names
    weekday_names = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
                 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
    df_clean['Weekday_Name'] = df_clean['Weekday'].map(weekday_names)

    # Group by weekday name and calculate the average
    average_price_by_weekday = df_clean.groupby('Weekday_Name')['Energy Price [EUR/MWh]'].mean()

    # Order the result: Monday -> Sunday
    ordered_weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    average_price_by_weekday = average_price_by_weekday.reindex(ordered_weekdays)

    # Calculate average energy price for Day and Night
    day_night_avg = df_clean.groupby('Day/Night')['Energy Price [EUR/MWh]'].mean()

    # Apply 20% markup
    peak_price_with_markup = avg_peak_price * 1.20
    off_peak_price_with_markup = avg_off_peak_price * 1.20

    # Round to 2 decimal places
    peak_price_with_markup = round(peak_price_with_markup, 2)
    off_peak_price_with_markup = round(off_peak_price_with_markup, 2)

    # Create Streamlit UI
    st.title(" Energy Price Explorer")

    # Sidebar filters for user input
    st.sidebar.header("Filter Options")

    hour_range = st.sidebar.slider("Select Hour Range", 0, 23, (0, 23))
    months = st.sidebar.multiselect("Select Month(s)", list(range(1, 13)), default=list(range(1, 13)))
    weekdays = st.sidebar.multiselect("Select Weekday(s) (0=Mon)", list(range(0, 7)), default=list(range(0, 7)))
    weeks = st.sidebar.multiselect("Select Week Number(s)", sorted(df['Week'].unique()), default=sorted(df['Week'].unique()))
    seasons = st.sidebar.multiselect("Select Season(s)", ['Winter', 'Spring', 'Summer', 'Autumn'], default=['Winter', 'Spring', 'Summer', 'Autumn'])

    # Apply the filters to the dataset
    filtered = df[
        (df['Hour'] >= hour_range[0]) & (df['Hour'] <= hour_range[1]) &
        (df['Month'].isin(months)) &
        (df['Weekday/Weekend'].isin(weekdays)) &
        (df['Week'].isin(weeks)) &
        (df['Season'].isin(seasons))
    ]

    # Display the result
    st.subheader("Average Energy Price for Selected Filters")
    if filtered.empty:
        st.warning("No data available for selected filters.")
    else:
        avg_price = filtered['Energy Price [EUR/MWh]'].mean()
        st.metric(label="Average Price [EUR/MWh]", value=f"{avg_price:.2f}")
        st.line_chart(filtered.set_index('Date/Time CET/CEST')['Energy Price [EUR/MWh]'])

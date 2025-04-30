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

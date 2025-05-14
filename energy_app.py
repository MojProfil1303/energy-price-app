import streamlit as st
import pandas as pd

st.set_page_config(page_title="Energy Price Explorer", layout="wide")

# Streamlit file upload
uploaded_file = st.file_uploader("Upload your energy data file", type=['xlsx'])
if uploaded_file is not None:
    st.write("DEBUG: File uploaded")
    # Load the dataset
    df = pd.read_excel(uploaded_file)
    st.write("DEBUG: DataFrame loaded", df.head())

    # Identify datetime column
    datetime_col = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
    st.write("DEBUG: Detected datetime column(s):", datetime_col)

    if datetime_col:
        df[datetime_col[0]] = pd.to_datetime(df[datetime_col[0]], format='%d.%m.%Y/%H:%M', errors='coerce')
        df = df.rename(columns={datetime_col[0]: 'Date/Time CET/CEST'})
    else:
        st.error("⚠️ No datetime column found. Please ensure your file has a date/time column.")
        st.stop()

    # Check if Energy Price column exists
    price_col = [col for col in df.columns if 'price' in col.lower()]
    st.write("DEBUG: Detected price column(s):", price_col)

    if not price_col:
        st.error("⚠️ No energy price column found. Please ensure your file includes a column with energy prices.")
        st.stop()

    df['Energy Price [EUR/MWh]'] = df[price_col[0]]
    df['Date/Time CET/CEST'] = pd.to_datetime(df['Date/Time CET/CEST'])

    # Add time-related columns
    df['Year'] = df['Date/Time CET/CEST'].dt.year
    df['Month'] = df['Date/Time CET/CEST'].dt.month
    df['Day'] = df['Date/Time CET/CEST'].dt.day
    df['Weekday'] = df['Date/Time CET/CEST'].dt.weekday
    df['Hour'] = df['Date/Time CET/CEST'].dt.hour
    df['Week'] = df['Date/Time CET/CEST'].dt.isocalendar().week
    df['Weekday_Name'] = df['Weekday'].map({
        0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
        4: 'Friday', 5: 'Saturday', 6: 'Sunday'
    })

    st.write("DEBUG: Sample with time columns", df.head())

    # Weekday/Weekend and Day/Night
    df['Weekday/Weekend'] = df['Weekday'].apply(lambda x: 'Weekday' if x < 5 else 'Weekend')
    df['Day/Night'] = df['Hour'].apply(lambda x: 'Day' if 8 <= x < 20 else 'Night')

    # Season classification
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

    st.write("DEBUG: After season classification", df[['Month', 'Season']].drop_duplicates())

    # Remove 2022 war-related spike
    df_clean = df[~((df['Year'] == 2022) & (df['Month'].between(3, 9)))].copy()
    st.write("DEBUG: Cleaned data shape", df_clean.shape)

    # UI
    st.title("Energy Price Explorer")

    st.sidebar.header("Filter Options")
    selected_hours = st.sidebar.multiselect("Select Hour(s)", list(range(24)))
    months = st.sidebar.multiselect("Select Month(s)", list(range(1, 13)))
    weekdays = st.sidebar.multiselect("Select Weekday(s) (0=Mon)", list(range(0, 7)))
    weeks = st.sidebar.multiselect("Select Week Number(s)", sorted(df_clean['Week'].unique()))
    seasons = st.sidebar.multiselect("Select Season(s)", ['Winter', 'Spring', 'Summer', 'Autumn'])
    markup_percent = st.sidebar.selectbox("Select Markup Percentage", [5, 10, 15, 20], index=3)

    st.write("DEBUG: Filters selected",
             {"Hours": selected_hours, "Months": months, "Weekdays": weekdays,
              "Weeks": weeks, "Seasons": seasons, "Markup": markup_percent})

    # Apply filters
    filtered = df_clean.copy()
    if selected_hours:
        filtered = filtered[filtered['Hour'].isin(selected_hours)]
    if months:
        filtered = filtered[filtered['Month'].isin(months)]
    if weekdays:
        filtered = filtered[filtered['Weekday'].isin(weekdays)]
    if weeks:
        filtered = filtered[filtered['Week'].isin(weeks)]
    if seasons:
        filtered = filtered[filtered['Season'].isin(seasons)]

    st.write("DEBUG: Filtered data shape", filtered.shape)

    # Show average price
    st.subheader("Average Energy Price for Selected Filters")
    if filtered.empty:
        st.warning("No data available for selected filters.")
    else:
        avg_price = filtered['Energy Price [EUR/MWh]'].mean()
        st.metric(label="Average Price [EUR/MWh]", value=f"{avg_price:.2f}")

        final_price = avg_price * (1 + markup_percent / 100)
        st.metric(label=f"Price with {markup_percent}% Markup", value=f"{final_price:.2f} EUR/MWh")

    # Bar Chart: Average price per hour based on filters (always show 0–23)
    st.subheader("Average Energy Price by Hour (Filtered Data)")
    hourly_avg_filtered = (filtered.groupby('Hour')['Energy Price [EUR/MWh]'].mean()
                           .reindex(range(24), fill_value=float('nan')).reset_index())
    st.write("DEBUG: Hourly average (filtered)", hourly_avg_filtered)
    st.bar_chart(hourly_avg_filtered.set_index('Hour'))
    st.write("Hourly Average Filtered:")
    st.dataframe(hourly_avg_filtered)
    st.write("Drop NaNs and set index:")
    st.dataframe(hourly_avg_filtered.dropna().set_index('Hour'))

    # Bar Chart for selected Weekdays
    if weekdays:
        st.subheader("Bar Chart per Selected Weekday(s)")
        filtered_weekdays = filtered[filtered['Weekday'].isin(weekdays)]
        weekday_avg = filtered_weekdays.groupby('Hour')['Energy Price [EUR/MWh]'].mean().reset_index()
        st.write("DEBUG: Weekday chart data", weekday_avg)
        st.bar_chart(weekday_avg.set_index('Hour'))

    # Bar Chart for selected Weeks
    if weeks:
        st.subheader("Bar Chart per Selected Week(s)")
        filtered_weeks = filtered[filtered['Week'].isin(weeks)]
        week_avg = filtered_weeks.groupby('Hour')['Energy Price [EUR/MWh]'].mean().reset_index()
        st.write("DEBUG: Week chart data", week_avg)
        st.bar_chart(week_avg.set_index('Hour'))

    # Bar Chart for selected Months
    if months:
        st.subheader("Bar Chart per Selected Month(s)")
        filtered_months = filtered[filtered['Month'].isin(months)]
        month_avg = filtered_months.groupby('Hour')['Energy Price [EUR/MWh]'].mean().reset_index()
        st.write("DEBUG: Month chart data", month_avg)
        st.bar_chart(month_avg.set_index('Hour'))

    # Bar Chart for selected Seasons
    if seasons:
        st.subheader("Bar Chart per Selected Season(s)")
        filtered_seasons = filtered[filtered['Season'].isin(seasons)]
        season_avg = filtered_seasons.groupby('Hour')['Energy Price [EUR/MWh]'].mean().reset_index()
        st.write("DEBUG: Season chart data", season_avg)
        st.bar_chart(season_avg.set_index('Hour'))

    # Show full dataset charts if no filters applied
    if not any([selected_hours, months, weekdays, weeks, seasons]):
        st.subheader("Bar Charts for the Full Dataset")

        full_hourly_avg = df_clean.groupby('Hour')['Energy Price [EUR/MWh]'].mean().reset_index()
        st.write("DEBUG: Full dataset hourly average", full_hourly_avg)
        st.write("**Average Price by Hour**")
        st.bar_chart(full_hourly_avg.set_index('Hour'))

        full_month_avg = df_clean.groupby('Month')['Energy Price [EUR/MWh]'].mean().reset_index()
        st.write("DEBUG: Full dataset monthly average", full_month_avg)
        st.write("**Average Price by Month**")
        st.bar_chart(full_month_avg.set_index('Month'))

        full_weekday_avg = df_clean.groupby('Weekday_Name')['Energy Price [EUR/MWh]'].mean().reset_index()
        full_weekday_avg = full_weekday_avg.sort_values('Energy Price [EUR/MWh]')
        st.write("DEBUG: Full dataset weekday average", full_weekday_avg)
        st.write("**Average Price by Weekday**")
        st.bar_chart(full_weekday_avg.set_index('Weekday_Name'))

        full_week_avg = df_clean.groupby('Week')['Energy Price [EUR/MWh]'].mean().reset_index()
        full_week_avg = full_week_avg.sort_values('Energy Price [EUR/MWh]')
        st.write("DEBUG: Full dataset weekly average", full_week_avg)
        st.write("**Average Price by Week Number**")
        st.bar_chart(full_week_avg.set_index('Week'))

        full_season_avg = df_clean.groupby('Season')['Energy Price [EUR/MWh]'].mean().reset_index()
        full_season_avg = full_season_avg.sort_values('Energy Price [EUR/MWh]')
        st.write("DEBUG: Full dataset season average", full_season_avg)
        st.write("**Average Price by Season**")
        st.bar_chart(full_season_avg.set_index('Season'))

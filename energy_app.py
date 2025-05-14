import streamlit as st
import pandas as pd

st.set_page_config(page_title="Energy Price Explorer", layout="wide")

# Streamlit file upload
uploaded_file = st.file_uploader("Upload your energy data file", type=['xlsx'])
if uploaded_file is not None:
    # Load the dataset
    df = pd.read_excel(uploaded_file)

    # Identify datetime column
    datetime_col = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
    if datetime_col:
        df[datetime_col[0]] = pd.to_datetime(df[datetime_col[0]], errors='coerce')  # more robust
        df = df.rename(columns={datetime_col[0]: 'Date/Time CET/CEST'})
    else:
        st.error("⚠️ No datetime column found. Please ensure your file has a date/time column.")
        st.stop()

    # Debug: Check datetime parsing
    st.write("Missing datetime values:", df['Date/Time CET/CEST'].isna().sum())

    # Check if Energy Price column exists
    price_col = [col for col in df.columns if 'price' in col.lower()]
    if not price_col:
        st.error("⚠️ No energy price column found. Please ensure your file includes a column with energy prices.")
        st.stop()

    price_col = price_col[0]  # use dynamically

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
    df_clean = df[~((df['Year'] == 2022) & (df['Month'].between(3, 9)))].copy()

    # UI
    st.title("Energy Price Explorer")

    st.sidebar.header("Filter Options")
    selected_hours = st.sidebar.multiselect("Select Hour(s)", list(range(24)))
    months = st.sidebar.multiselect("Select Month(s)", list(range(1, 13)))
    weekdays = st.sidebar.multiselect("Select Weekday(s) (0=Mon)", list(range(0, 7)))
    weeks = st.sidebar.multiselect("Select Week Number(s)", sorted(df_clean['Week'].unique()))
    seasons = st.sidebar.multiselect("Select Season(s)", ['Winter', 'Spring', 'Summer', 'Autumn'])

    # Markup Percentage Selector
    markup_percent = st.sidebar.selectbox("Select Markup Percentage", [5, 10, 15, 20], index=3)

    # Apply filters dynamically (only if the user selected values)
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

    # Debug: Show filter states and data shape
    st.write("📊 DEBUG INFO")
    st.write("Selected Hours:", selected_hours)
    st.write("Selected Months:", months)
    st.write("Selected Weekdays:", weekdays)
    st.write("Selected Weeks:", weeks)
    st.write("Selected Seasons:", seasons)
    st.write("Filtered Data Size:", filtered.shape)
    st.dataframe(filtered.head())  # show first few rows

    # Result section
    st.subheader("Average Energy Price for Selected Filters")

    if filtered.empty:
        st.warning("⚠️ No data available for selected filters.")
    else:
        avg_price = filtered[price_col].mean()
        st.metric(label="Average Price [EUR/MWh]", value=f"{avg_price:.2f}")

        final_price = avg_price * (1 + markup_percent / 100)
        st.metric(label=f"Price with {markup_percent}% Markup", value=f"{final_price:.2f} EUR/MWh")

        # Bar Chart for all 24 hours
        st.subheader("Bar Chart per Hour (with Selected Hours Highlighted)")
        hourly_avg = df_clean.groupby('Hour')[price_col].mean().reset_index()
        highlighted = hourly_avg[hourly_avg['Hour'].isin(selected_hours)] if selected_hours else pd.DataFrame()
        st.bar_chart(hourly_avg.rename(columns={price_col: 'Average Price'}).set_index('Hour'))

        if not highlighted.empty:
            st.markdown("### Highlighted Hours")
            st.bar_chart(highlighted.rename(columns={price_col: 'Average Price'}).set_index('Hour'))

        if weekdays:
            st.subheader("Bar Chart per Selected Weekday(s)")
            weekday_avg = filtered.groupby('Hour')[price_col].mean().reset_index()
            st.bar_chart(weekday_avg.rename(columns={price_col: 'Average Price'}).set_index('Hour'))

        if weeks:
            st.subheader("Bar Chart per Selected Week(s)")
            week_avg = filtered.groupby('Hour')[price_col].mean().reset_index()
            st.bar_chart(week_avg.rename(columns={price_col: 'Average Price'}).set_index('Hour'))

        if months:
            st.subheader("Bar Chart per Selected Month(s)")
            month_avg = filtered.groupby('Hour')[price_col].mean().reset_index()
            st.bar_chart(month_avg.rename(columns={price_col: 'Average Price'}).set_index('Hour'))

        if seasons:
            st.subheader("Bar Chart per Selected Season(s)")
            season_avg = filtered.groupby('Hour')[price_col].mean().reset_index()
            st.bar_chart(season_avg.rename(columns={price_col: 'Average Price'}).set_index('Hour'))

    # Show charts for the full dataset if no filters are applied
    if not selected_hours and not months and not weekdays and not weeks and not seasons:
        st.subheader("Bar Charts for the Full Dataset")

        full_hourly_avg = df_clean.groupby('Hour')[price_col].mean().reset_index()
        st.write("**Average Price by Hour**")
        st.bar_chart(full_hourly_avg.rename(columns={price_col: 'Average Price'}).set_index('Hour'))

        full_month_avg = df_clean.groupby('Month')[price_col].mean().reset_index()
        st.write("**Average Price by Month**")
        st.bar_chart(full_month_avg.rename(columns={price_col: 'Average Price'}).set_index('Month'))

        full_weekday_avg = df_clean.groupby('Weekday_Name')[price_col].mean().reset_index()
        full_weekday_avg = full_weekday_avg.sort_values(price_col)
        st.write("**Average Price by Weekday**")
        st.bar_chart(full_weekday_avg.rename(columns={price_col: 'Average Price'}).set_index('Weekday_Name'))

        full_week_avg = df_clean.groupby('Week')[price_col].mean().reset_index()
        full_week_avg = full_week_avg.sort_values(price_col)
        st.write("**Average Price by Week Number**")
        st.bar_chart(full_week_avg.rename(columns={price_col: 'Average Price'}).set_index('Week'))

        full_season_avg = df_clean.groupby('Season')[price_col].mean().reset_index()
        full_season_avg = full_season_avg.sort_values(price_col)
        st.write("**Average Price by Season**")
        st.bar_chart(full_season_avg.rename(columns={price_col: 'Average Price'}).set_index('Season'))

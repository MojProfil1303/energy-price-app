import streamlit as st
import pandas as pd

st.set_page_config(page_title="Energy Price Explorer", layout="wide")

# Streamlit file upload
uploaded_file = st.file_uploader("Upload your energy data file", type=['xlsx'])
if uploaded_file is not None:
    # Load the dataset
    df = pd.read_excel(uploaded_file)

    # ✅ DEBUG: Show raw uploaded data
    st.subheader("Uploaded Data Sample")
    st.dataframe(df.head())
    st.write("Shape of full dataset:", df.shape)

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
    df_clean = df[~((df['Year'] == 2022) & (df['Month'].between(3, 9)))].copy()

    # UI
    st.title("🔌 Energy Price Explorer")

    st.sidebar.header("📊 Filter Options")
    hour_range = st.sidebar.slider("Select Hour Range", 0, 23, (0, 23))
    months = st.sidebar.multiselect("Select Month(s)", list(range(1, 13)))
    weekdays = st.sidebar.multiselect("Select Weekday(s) (0=Mon)", list(range(0, 7)))
    weeks = st.sidebar.multiselect("Select Week Number(s)", sorted(df_clean['Week'].unique()))
    seasons = st.sidebar.multiselect("Select Season(s)", ['Winter', 'Spring', 'Summer', 'Autumn'])

    # Markup Percentage Selector
    markup_percent = st.sidebar.selectbox("Select Markup Percentage", [5, 10, 15, 20], index=3)

    # Apply filters dynamically (only if the user selected values)
    filtered = df_clean.copy()
    filtered = filtered[(filtered['Hour'] >= hour_range[0]) & (filtered['Hour'] <= hour_range[1])]
    if months:
        filtered = filtered[filtered['Month'].isin(months)]
    if weekdays:
        filtered = filtered[filtered['Weekday'].isin(weekdays)]
    if weeks:
        filtered = filtered[filtered['Week'].isin(weeks)]
    if seasons:
        filtered = filtered[filtered['Season'].isin(seasons)]

    # ✅ DEBUG: Show filtered data
    st.subheader("Filtered Data Preview")
    st.write("Filtered Rows:", filtered.shape[0])
    st.dataframe(filtered.head())

    # Result section
    st.subheader("📈 Average Energy Price for Selected Filters")

    if filtered.empty:
        st.warning("No data available for selected filters.")
    else:
        # Compute overall average
        avg_price = filtered['Energy Price [EUR/MWh]'].mean()
        st.metric(label="Average Price [EUR/MWh]", value=f"{avg_price:.2f}")

        # Calculate final price with markup
        final_price = avg_price * (1 + markup_percent / 100)

        # Price with markup
        st.metric(label=f"Price with {markup_percent}% Markup", value=f"{final_price:.2f} EUR/MWh")




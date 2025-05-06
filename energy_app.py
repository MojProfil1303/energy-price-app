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

    datetime_col = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
    if datetime_col:
        df[datetime_col[0]] = pd.to_datetime(df[datetime_col[0]], errors='coerce')
        df = df.rename(columns={datetime_col[0]: 'Date/Time CET/CEST'})
    else:
        st.error("⚠️ No datetime column found. Please ensure your file has a date/time column.")
        st.stop()

    # ✅ Check if Energy Price column exists
    price_col = [col for col in df.columns if 'price' in col.lower()]
    if not price_col:
        st.error("⚠️ No energy price column found. Please ensure your file includes a column with energy prices.")
        st.stop()

    # Strip whitespace in string columns
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    # Check for missing values in all columns
    missing_values = df.isnull().sum()

    # Display missing values summary
    st.write("Missing Values Summary:", missing_values)

    # Identify which columns have missing values
    missing_columns = missing_values[missing_values > 0].index.tolist()
    if missing_columns:
        st.write(f"The following columns have missing values: {', '.join(missing_columns)}")

    # Display row 288
    st.write("Row 288 with problematic date entry:")
    st.write(df.iloc[287])  # Row 288 corresponds to index 287

    # Check for non-date entries or special characters
    invalid_row = df.iloc[287]
    st.write("Checking for invalid characters in the date column:")
    st.write(invalid_row['Date/Time CET/CEST'])

    # Try to explicitly convert the date and catch errors
    try:
        test_date = pd.to_datetime(invalid_row['Date/Time CET/CEST'], errors='raise')
        st.write(f"Valid date: {test_date}")
    except Exception as e:
        st.write(f"Error in converting date: {e}")
    
    # Check the rows with missing values
    rows_with_missing_values = df[df.isnull().any(axis=1)]
    st.write("Rows with Missing Values:", rows_with_missing_values)

    # Further investigate the 'Date/Time CET/CEST' column for missing values
    if 'Date/Time CET/CEST' in df.columns:
        st.write(f"Missing values in 'Date/Time CET/CEST' column: {df['Date/Time CET/CEST'].isnull().sum()}")
        st.write("Unique values in 'Date/Time CET/CEST' column (before conversion to datetime):")
        st.write(df['Date/Time CET/CEST'].unique())

        # Try to convert 'Date/Time CET/CEST' to datetime and identify invalid entries
        df['Date/Time CET/CEST'] = pd.to_datetime(df['Date/Time CET/CEST'], errors='coerce')
        st.write("After conversion, the invalid date entries are:")
        invalid_dates = df[df['Date/Time CET/CEST'].isnull()]
        st.write(invalid_dates)

    # Check for other potential reasons for missing data
    st.write("Checking for rows where columns may have completely empty values (non-date columns)")
    empty_columns = df.columns[df.isnull().all()]
    if empty_columns.any():
        st.write(f"These columns are completely empty: {', '.join(empty_columns)}")
    else:
        st.write("No columns are completely empty.")

    # Check for duplicate rows that might have missing values as a result of merging or concatenating datasets
    st.write("Checking for duplicate rows:")
    duplicates = df[df.duplicated()]
    if not duplicates.empty:
        st.write("Found duplicate rows, which may cause missing values in some columns:")
        st.write(duplicates)
    else:
        st.write("No duplicate rows found.")

    # Provide information on the dataset after checking for missing values
    st.write("Shape of the dataset:", df.shape)
    
    # Check for missing values in the entire DataFrame
    missing_values = df.isnull().sum()

    # Display the missing values summary
    st.subheader("Missing Values Summary")
    st.write(missing_values)

    # Provide summary after cleaning
    st.write("Shape of cleaned dataset:", df_cleaned.shape)

    # Additional exploration
    st.write("Checking for specific columns' data types:")
    st.write(df.dtypes)

    st.write("Check for any values that are 'NaN' or 'None' in string columns:")
    string_columns = df.select_dtypes(include=['object']).columns
    for col in string_columns:
        if df[col].str.contains('nan', case=False).any():
            st.write(f"Column '{col}' has 'nan' values as strings!")

    # Check and show any rows that have special characters or unexpected formats
    special_characters = df[~df.applymap(lambda x: isinstance(x, str) or x.isalnum()).all(axis=1)]
    if not special_characters.empty:
        st.write("Rows with special characters or unexpected formats:")
        st.write(special_characters)
    
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




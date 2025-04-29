import streamlit as st
import pandas as pd

# Load and prepare the data 
df = pd.read_excel('your_uploaded_file.xlsx')

df['Date/Time CET/CEST'] = pd.to_datetime(df['Date/Time CET/CEST'])
df['Hour'] = df['Date/Time CET/CEST'].dt.hour
df['Month'] = df['Date/Time CET/CEST'].dt.month
df['Weekday'] = df['Date/Time CET/CEST'].dt.weekday
df['Week_Number'] = df['Date/Time CET/CEST'].dt.isocalendar().week
df['Season'] = df['Month'].apply(lambda x: 'Winter' if x in [12, 1, 2] else 'Spring' if x in [3, 4, 5] else 'Summer' if x in [6, 7, 8] else 'Autumn')

# Create Streamlit UI
st.title("🔌 Interactive Energy Price Explorer")

# Sidebar filters
st.sidebar.header("📊 Filter Options")

hour_range = st.sidebar.slider("Select Hour Range", 0, 23, (0, 23))
months = st.sidebar.multiselect("Select Month(s)", list(range(1, 13)), default=list(range(1, 13)))
weekdays = st.sidebar.multiselect("Select Weekday(s) (0=Mon)", list(range(0, 7)), default=list(range(0, 7)))
weeks = st.sidebar.multiselect("Select Week Number(s)", sorted(df['Week_Number'].unique()), default=sorted(df['Week_Number'].unique()))
seasons = st.sidebar.multiselect("Select Season(s)", ['Winter', 'Spring', 'Summer', 'Autumn'], default=['Winter', 'Spring', 'Summer', 'Autumn'])

# Filter the data
filtered = df[
    (df['Hour'] >= hour_range[0]) & (df['Hour'] <= hour_range[1]) &
    (df['Month'].isin(months)) &
    (df['Weekday'].isin(weekdays)) &
    (df['Week_Number'].isin(weeks)) &
    (df['Season'].isin(seasons))
]

# Show results
st.subheader("📈 Average Energy Price for Selected Filters")
if filtered.empty:
    st.warning("No data available for selected filters.")
else:
    avg_price = filtered['Energy Price [EUR/MWh]'].mean()
    st.metric(label="Average Price [EUR/MWh]", value=f"{avg_price:.2f}")
    st.line_chart(filtered.set_index('Date/Time CET/CEST')['Energy Price [EUR/MWh]'])

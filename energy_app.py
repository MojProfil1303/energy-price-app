import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Energy Price Explorer", layout="wide")

# File uploader
uploaded_file = st.file_uploader("Upload your energy data file", type=['xlsx'])
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    # Detect datetime column
    datetime_col = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
    if datetime_col:
        df[datetime_col[0]] = pd.to_datetime(df[datetime_col[0]], format='%d.%m.%Y/%H:%M', errors='coerce')
        df = df.rename(columns={datetime_col[0]: 'Date/Time CET/CEST'})
    else:
        st.error("⚠️ No datetime column found.")
        st.stop()

    # Detect price column
    price_col = [col for col in df.columns if 'price' in col.lower()]
    if not price_col:
        st.error("⚠️ No energy price column found.")
        st.stop()

    df['Date/Time CET/CEST'] = pd.to_datetime(df['Date/Time CET/CEST'])

    # Time features
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

    # Exclude war-period
    df_clean = df[~((df['Year'] == 2022) & (df['Month'].between(3, 9)))].copy()

    st.title("Energy Price Explorer")

    # Sidebar filters
    st.sidebar.header("Filter Options")
    selected_hours = st.sidebar.multiselect("Select Hour(s)", list(range(24)))
    months = st.sidebar.multiselect("Select Month(s)", list(range(1, 13)))
    weekdays = st.sidebar.multiselect("Select Weekday(s) (0=Mon)", list(range(0, 7)))
    weeks = st.sidebar.multiselect("Select Week Number(s)", sorted(df_clean['Week'].unique()))
    seasons = st.sidebar.multiselect("Select Season(s)", ['Winter', 'Spring', 'Summer', 'Autumn'])

    markup_percent = st.sidebar.selectbox("Select Markup Percentage", [5, 10, 15, 20], index=3)

    # Filtering
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

    # Results
    st.subheader("Average Energy Price for Selected Filters")

    if filtered.empty:
        st.warning("No data for selected filters.")
    else:
        avg_price = filtered['Energy Price [EUR/MWh]'].mean()
        st.metric("Average Price [EUR/MWh]", f"{avg_price:.2f}")

        final_price = avg_price * (1 + markup_percent / 100)
        st.metric(f"Price with {markup_percent}% Markup", f"{final_price:.2f} EUR/MWh")

        # Hourly average chart
        st.subheader("Bar Chart per Hour")
        hourly_avg = df_clean.groupby('Hour')['Energy Price [EUR/MWh]'].mean().reset_index()
        st.bar_chart(hourly_avg.rename(columns={'Energy Price [EUR/MWh]': 'Average Price'}).set_index('Hour'))

        # Grouped charts
        if selected_hours and weekdays and months:
            st.subheader("Grouped Bar Chart: Hour × Weekday × Month")
            month_names = {
                1: "January", 2: "February", 3: "March", 4: "April",
                5: "May", 6: "June", 7: "July", 8: "August",
                9: "September", 10: "October", 11: "November", 12: "December"
            }
            filtered['Month_Name'] = filtered['Month'].map(month_names)
            group_avg = filtered.groupby(['Month_Name', 'Weekday_Name', 'Hour'])['Energy Price [EUR/MWh]'].mean().reset_index()

            fig = px.bar(
                group_avg,
                x="Weekday_Name",
                y="Energy Price [EUR/MWh]",
                color="Hour",
                barmode="group",
                facet_col="Month_Name",
                category_orders={"Weekday_Name": ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']},
                title="Grouped Average Price by Weekday, Hour, and Month"
            )
            st.plotly_chart(fig, use_container_width=True)

        if selected_hours and seasons:
            st.subheader("Grouped Bar Chart: Hour × Season")
            season_avg = filtered.groupby(['Season', 'Hour'])['Energy Price [EUR/MWh]'].mean().reset_index()
            fig_season = px.bar(
                season_avg,
                x='Season',
                y='Energy Price [EUR/MWh]',
                color='Hour',
                barmode='group',
                title="Grouped Average Price by Season and Hour"
            )
            st.plotly_chart(fig_season, use_container_width=True)

        if selected_hours and weeks:
            st.subheader("Grouped Bar Chart: Hour × Week Number")
            week_avg = filtered.groupby(['Week', 'Hour'])['Energy Price [EUR/MWh]'].mean().reset_index()
            fig_week = px.bar(
                week_avg,
                x='Week',
                y='Energy Price [EUR/MWh]',
                color='Hour',
                barmode='group',
                title="Grouped Average Price by Week Number and Hour"
            )
            st.plotly_chart(fig_week, use_container_width=True)

    # Full dataset fallback charts
    if not selected_hours and not months and not weekdays and not weeks and not seasons:
        st.subheader("Full Dataset Charts")

        st.write("**Average Price by Hour**")
        hour_avg = df_clean.groupby('Hour')['Energy Price [EUR/MWh]'].mean().reset_index()
        st.bar_chart(hour_avg.rename(columns={'Energy Price [EUR/MWh]': 'Average Price'}).set_index('Hour'))

        st.write("**Average Price by Month**")
        month_avg = df_clean.groupby('Month')['Energy Price [EUR/MWh]'].mean().reset_index()
        st.bar_chart(month_avg.rename(columns={'Energy Price [EUR/MWh]': 'Average Price'}).set_index('Month'))

        st.write("**Average Price by Weekday**")
        weekday_avg = df_clean.groupby('Weekday_Name')['Energy Price [EUR/MWh]'].mean().reset_index()
        weekday_avg = weekday_avg.sort_values('Energy Price [EUR/MWh]')
        st.bar_chart(weekday_avg.rename(columns={'Energy Price [EUR/MWh]': 'Average Price'}).set_index('Weekday_Name'))

        st.write("**Average Price by Week Number**")
        week_avg = df_clean.groupby('Week')['Energy Price [EUR/MWh]'].mean().reset_index()
        st.bar_chart(week_avg.rename(columns={'Energy Price [EUR/MWh]': 'Average Price'}).set_index('Week'))

        st.write("**Average Price by Season**")
        season_avg = df_clean.groupby('Season')['Energy Price [EUR/MWh]'].mean().reset_index()
        st.bar_chart(season_avg.rename(columns={'Energy Price [EUR/MWh]': 'Average Price'}).set_index('Season'))

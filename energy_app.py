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

    # Mapping
    month_names = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April',
        5: 'May', 6: 'June', 7: 'July', 8: 'August',
        9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    weekday_names = {
        0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
        4: 'Friday', 5: 'Saturday', 6: 'Sunday'
    }

    df['Month_Name'] = df['Month'].map(month_names)
    df['Weekday_Name'] = df['Weekday'].map(weekday_names)

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
    month_name_to_num = {v: k for k, v in month_names.items()}
    selected_month_names = st.sidebar.multiselect("Select Month(s)", list(month_names.values()))
    months = [month_name_to_num[m] for m in selected_month_names] if selected_month_names else []

    weekday_name_to_num = {v: k for k, v in weekday_names.items()}
    selected_weekday_names = st.sidebar.multiselect("Select Weekday(s)", list(weekday_names.values()))
    weekdays = [weekday_name_to_num[d] for d in selected_weekday_names] if selected_weekday_names else []

    markup_percent = st.sidebar.number_input("Cost of Energy", min_value=0.0, step=0.5)

    # Filtering
    filtered = df_clean.copy()
    if selected_hours:
        filtered = filtered[filtered['Hour'].isin(selected_hours)]
    if months:
        filtered = filtered[filtered['Month'].isin(months)]
    if weekdays:
        filtered = filtered[filtered['Weekday'].isin(weekdays)]

    st.subheader("Average Energy Price for the Data")

    if filtered.empty:
        st.warning("No data for selected filters.")
    else:
        avg_price = filtered['Energy Price [EUR/MWh]'].mean()
        st.metric("Average Price [€/MWh]", f"{avg_price:.2f} €/MWh")

        final_price = avg_price * (1 + markup_percent / 100)
        st.metric("Total cost of energy", f"{final_price:.2f} €/MWh")

        if selected_hours and months and weekdays:
            st.subheader("Bar Chart: Hour × Month × Weekday")
            three_dim_avg = filtered.groupby(['Month_Name', 'Weekday_Name', 'Hour'])['Energy Price [EUR/MWh]'].mean().reset_index()
            fig_3d = px.bar(
                three_dim_avg,
                x='Month_Name',
                y='Energy Price [EUR/MWh]',
                color='Hour',
                facet_col='Weekday_Name',
                category_orders={"Weekday_Name": list(weekday_names.values())},
                title="Grouped Price by Month, Weekday, and Hour"
            )
            st.plotly_chart(fig_3d, use_container_width=True)

        elif selected_hours and months and not weekdays:
            st.subheader("Grouped Bar Chart: Hour × Month")
            month_avg = filtered.groupby(['Month_Name', 'Hour'])['Energy Price [EUR/MWh]'].mean().reset_index()
            fig_month = px.bar(
                month_avg,
                x='Month_Name',
                y='Energy Price [EUR/MWh]',
                color='Hour',
                barmode='group',
                title="Grouped Average Price by Month and Hour"
            )
            st.plotly_chart(fig_month, use_container_width=True)

        elif selected_hours and weekdays and not months:
            st.subheader("Grouped Bar Chart: Hour × Weekday")
            weekday_avg = filtered.groupby(['Weekday_Name', 'Hour'])['Energy Price [EUR/MWh]'].mean().reset_index()
            fig_weekday = px.bar(
                weekday_avg,
                x='Weekday_Name',
                y='Energy Price [EUR/MWh]',
                color='Hour',
                barmode='group',
                category_orders={"Weekday_Name": list(weekday_names.values())},
                title="Grouped Average Price by Weekday and Hour"
            )
            st.plotly_chart(fig_weekday, use_container_width=True)

        elif selected_hours and not months and not weekdays:
            hour_avg = filtered.groupby('Hour')['Energy Price [EUR/MWh]'].mean().reset_index()
            selected_avg = hour_avg['Energy Price [EUR/MWh]'].mean()

            def categorize(price):
                if price < selected_avg:
                    return '✅ Most Recommended'
                elif price <= selected_avg + 10:
                    return '⚠️ Moderate'
                else:
                    return '❌ Not Recommended'

            hour_avg['Recommendation'] = hour_avg['Energy Price [EUR/MWh]'].apply(categorize)

            fig = px.bar(
                hour_avg, 
                x='Hour',
                y='Energy Price [EUR/MWh]',
                color='Recommendation',
                title=f"Average Energy Price by Hour (Overall Avg: {selected_avg:.2f} EUR/MWh)",
                color_discrete_map={
                    '✅ Most Recommended': 'green',
                    '⚠️ Moderate': 'orange',
                    '❌ Not Recommended': 'red'
                },
                category_orders={
                    'Recommendation': ['✅ Most Recommended', '⚠️ Moderate', '❌ Not Recommended']
                }
            )

            st.plotly_chart(fig, use_container_width=True)

            st.markdown(f"**Most Recommended Hours:** {', '.join(map(str, hour_avg[hour_avg['Recommendation'] == '✅ Most Recommended']['Hour'].tolist()))}")
            st.markdown(f"**Moderate Hours:** {', '.join(map(str, hour_avg[hour_avg['Recommendation'] == '⚠️ Moderate']['Hour'].tolist()))}")
            st.markdown(f"**Not Recommended Hours:** {', '.join(map(str, hour_avg[hour_avg['Recommendation'] == '❌ Not Recommended']['Hour'].tolist()))}")

        elif months and not selected_hours and not weekdays:
            st.subheader("Average Price by Month")
            month_avg = filtered.groupby('Month_Name')['Energy Price [EUR/MWh]'].mean().reset_index()
            month_avg = month_avg.set_index('Month_Name').reindex(list(month_names.values()))
            st.bar_chart(month_avg.rename(columns={'Energy Price [EUR/MWh]': 'Average Price'}))

        elif weekdays and not selected_hours and not months:
            st.subheader("Average Price by Weekday")
            weekday_avg = filtered.groupby('Weekday_Name')['Energy Price [EUR/MWh]'].mean().reset_index()
            weekday_avg = weekday_avg.set_index('Weekday_Name').reindex(list(weekday_names.values()))
            st.bar_chart(weekday_avg.rename(columns={'Energy Price [EUR/MWh]': 'Average Price'}))

    # Fallback chart if no filters
    if not selected_hours and not months and not weekdays:
        hour_avg = df_clean.groupby('Hour')['Energy Price [EUR/MWh]'].mean().reset_index()
        overall_avg = hour_avg['Energy Price [EUR/MWh]'].mean()

        def categorize(price):
            if price < overall_avg:
                return '✅ Most Recommended'
            elif price <= overall_avg + 10:
                return '⚠️ Moderate'
            else:
                return '❌ Not Recommended'

        hour_avg['Recommendation'] = hour_avg['Energy Price [EUR/MWh]'].apply(categorize)

        fig = px.bar(
            hour_avg, 
            x='Hour',
            y='Energy Price [EUR/MWh]',
            color='Recommendation',
            title=f"Average Energy Price by Hour",
            color_discrete_map={
                '✅ Most Recommended': 'green',
                '⚠️ Moderate': 'orange',
                '❌ Not Recommended': 'red'
            },
            category_orders={
                'Recommendation': ['✅ Most Recommended', '⚠️ Moderate', '❌ Not Recommended']
            }
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("**Hourly Recommendation Summary Based on the Full Dataset:**")
        st.markdown(f"**Most Recommended (Lowest Avg Price):** {', '.join(str(h) for h in hour_avg[hour_avg['Recommendation'] == '✅ Most Recommended']['Hour'].tolist())}")
        st.markdown(f"**Moderate:** {', '.join(str(h) for h in hour_avg[hour_avg['Recommendation'] == '⚠️ Moderate']['Hour'].tolist())}")
        st.markdown(f"**Not Recommended (Highest Avg Price):** {', '.join(str(h) for h in hour_avg[hour_avg['Recommendation'] == '❌ Not Recommended']['Hour'].tolist())}")

        st.write("**Average Price by Month**")
        month_avg = df_clean.groupby('Month_Name')['Energy Price [EUR/MWh]'].mean().reset_index()
        month_avg = month_avg.set_index('Month_Name').reindex(list(month_names.values()))
        st.bar_chart(month_avg.rename(columns={'Energy Price [EUR/MWh]': 'Average Price'}))

        st.write("**Average Price by Weekday**")
        weekday_avg = df_clean.groupby('Weekday_Name')['Energy Price [EUR/MWh]'].mean().reset_index()
        weekday_avg = weekday_avg.set_index('Weekday_Name').reindex(list(weekday_names.values()))
        st.bar_chart(weekday_avg.rename(columns={'Energy Price [EUR/MWh]': 'Average Price'}))

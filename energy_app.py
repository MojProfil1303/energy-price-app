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
        st.error("\u26a0\ufe0f No datetime column found.")
        st.stop()

    # Detect price column
    price_col = [col for col in df.columns if 'price' in col.lower()]
    if not price_col:
        st.error("\u26a0\ufe0f No energy price column found.")
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

    markup_percent = st.sidebar.selectbox("Select Markup Percentage", [5, 10, 15, 20], index=3)

    # Filtering
    filtered = df_clean.copy()
    if selected_hours:
        filtered = filtered[filtered['Hour'].isin(selected_hours)]
    if months:
        filtered = filtered[filtered['Month'].isin(months)]
    if weekdays:
        filtered = filtered[filtered['Weekday'].isin(weekdays)]

    # Results
    st.subheader("Average Energy Price for Selected Filters")

    if filtered.empty:
        st.warning("No data for selected filters.")
    else:
        avg_price = filtered['Energy Price [EUR/MWh]'].mean()
        st.metric("Average Price [EUR/MWh]", f"{avg_price:.2f}")

        final_price = avg_price * (1 + markup_percent / 100)
        st.metric(f"Price with {markup_percent}% Markup", f"{final_price:.2f} EUR/MWh")

        # Chart logic
        if selected_hours and months and weekdays:
            st.subheader("3D Bar Chart: Hour × Month × Weekday")
            three_dim_avg = filtered.groupby(['Month', 'Weekday_Name', 'Hour'])['Energy Price [EUR/MWh]'].mean().reset_index()
            fig_3d = px.bar(
                three_dim_avg,
                x='Month',
                y='Energy Price [EUR/MWh]',
                color='Hour',
                facet_col='Weekday_Name',
                category_orders={"Weekday_Name": ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']},
                title="3D Grouped Price by Month, Weekday, and Hour"
            )
            st.plotly_chart(fig_3d, use_container_width=True)

        elif selected_hours and months and not weekdays:
            st.subheader("Grouped Bar Chart: Hour × Month")
            month_avg = filtered.groupby(['Month', 'Hour'])['Energy Price [EUR/MWh]'].mean().reset_index()
            fig_month = px.bar(
                month_avg,
                x='Month',
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
                category_orders={"Weekday_Name": ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']},
                title="Grouped Average Price by Weekday and Hour"
            )
            st.plotly_chart(fig_weekday, use_container_width=True)

        elif selected_hours and not months and not weekdays:
            st.write("**Average Price by Hour (with Recommendation Tags)**")
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
                title=f"Average Energy Price by Hour (Overall Avg: {overall_avg:.2f} EUR/MWh)",
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

        elif months and not selected_hours and not weekdays:
            st.subheader("Average Price by Month")
            month_avg = filtered.groupby('Month')['Energy Price [EUR/MWh]'].mean().reset_index()
            st.bar_chart(month_avg.rename(columns={'Energy Price [EUR/MWh]': 'Average Price'}).set_index('Month'))

        elif weekdays and not selected_hours and not months:
            st.subheader("Average Price by Weekday")
            weekday_avg = filtered.groupby('Weekday_Name')['Energy Price [EUR/MWh]'].mean().reset_index()
            weekday_avg = weekday_avg.sort_values('Energy Price [EUR/MWh]')
            st.bar_chart(weekday_avg.rename(columns={'Energy Price [EUR/MWh]': 'Average Price'}).set_index('Weekday_Name'))

    # Full dataset fallback charts
    if not selected_hours and not months and not weekdays:
        st.subheader("Full Dataset Charts")

        st.write("nesto")

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
            title=f"Average Energy Price by Hour (Overall Avg: {overall_avg:.2f} EUR/MWh)",
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

        # ➕ Add explanation text below
        recommended_hours = hour_avg[hour_avg['Recommendation'] == '✅ Most Recommended']['Hour'].tolist()
        st.markdown(
            f"💡 **Based on the full dataset, the most recommended hours with lowest average prices are:** "
            f"**{', '.join(str(h) for h in recommended_hours)}**"
        )

        st.write("**Average Price by Month**")
        month_avg = df_clean.groupby('Month')['Energy Price [EUR/MWh]'].mean().reset_index()
        st.bar_chart(month_avg.rename(columns={'Energy Price [EUR/MWh]': 'Average Price'}).set_index('Month'))

        st.write("**Average Price by Weekday**")
        weekday_avg = df_clean.groupby('Weekday_Name')['Energy Price [EUR/MWh]'].mean().reset_index()
        weekday_avg = weekday_avg.sort_values('Energy Price [EUR/MWh]')
        st.bar_chart(weekday_avg.rename(columns={'Energy Price [EUR/MWh]': 'Average Price'}).set_index('Weekday_Name'))

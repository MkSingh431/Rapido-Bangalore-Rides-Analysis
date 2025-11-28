import streamlit as st
import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from prophet import Prophet

def main():

    # for wider display
    st.set_page_config(
        page_title = "Rapido Rides Analysis",
        layout = 'wide'
    )
    # Load Data
    @st.cache_data
    def load_data():
        # df = pd.read_csv(os.path.join(os.getcwd(),'rides_data.csv')) 
        df = pd.read_csv('streamlit_dashboard/rides_data.csv') # For Github Deployment
        df['date'] = pd.to_datetime(df['date'])
        return df

    df = load_data()

    # df = df[df['ride_status'] == 'completed']

    # Sidebar Filters
    st.sidebar.header("Filter Data")
    st.sidebar.markdown("""
        **⚠️ Sidebar Instructions:**
        - Choose a filter option, then close the sidebar for a better view.
        - Click on **">"** (top left corner) to toggle the sidebar.
        """)
    
    ride_status_options = ['All Rides', 'Completed', 'Cancelled']
    ride_status_filter = st.sidebar.multiselect("Select Ride Status", ride_status_options, default = ['All Rides'])

    if not ride_status_filter:
        st.sidebar.warning("⚠️ Please select at least one ride status.")
        st.stop()

    if "All Rides" in ride_status_filter:
        filtered_status = df['ride_status'].notna()  # Show all rides
    elif "Completed" in ride_status_filter:
        filtered_status = df['ride_status'].isin(['completed'])
    else:
        filtered_status = df['ride_status'].isin(['cancelled'])

    # Add "All Services" option
    service_options = ['All Services'] + list(df['services'].dropna().unique())
    service_filter = st.sidebar.multiselect("Select Service Type", service_options, default=['All Services'])

    # Handle "All Services" selection correctly
    if "All Services" in service_filter:
        filtered_services = df['services'].dropna().unique()  # Select all service types
    else:
        filtered_services = service_filter  # Use selected services

    # Date range selection
    # date_range = st.sidebar.date_input("Select Date Range", [df['date'].min(), df['date'].max()])
    min_date = df['date'].min()
    max_date = df['date'].max()

    date_range = st.sidebar.date_input('Select Date Range', [min_date, max_date], min_value = min_date, max_value = max_date)

    # Convert selected date range to datetime
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])

    if start_date < min_date or end_date > max_date:
        st.sidebar.error(f"⚠️ Please select dates between {min_date.date()} and {max_date.date()} as per available data.")
        st.stop()

    payment_optios = ['All Payment Methods'] + list(df['payment_method'].dropna().unique())
    payment_filter = st.sidebar.multiselect("Select Payment Method", payment_optios, default = ['All Payment Methods'])

    if "All Payment Methods" in payment_filter:
        filtered_payments = df['payment_method'].unique()
    else:
        filtered_payments = payment_filter

    # Apply Filters
    filtered_df = df[
        ((filtered_status)) &
        (df['services'].isin(filtered_services)) & 
        (df['date'].between(start_date, end_date)) &
        (df['payment_method'].isin(filtered_payments))
    ]
    
    if filtered_df.empty:
        no_service_data = df[df['services'].isin(filtered_services)].empty
        no_date_data = df[df['date'].between(start_date, end_date)].empty
        no_payment_data = df[df['payment_method'].isin(filtered_payments)].empty

        if no_service_data and no_date_data and no_payment_data:
            st.warning("⚠️ No data available. Try adjusting multiple filters.")
        elif no_service_data:
            st.warning("⚠️ No data available for the selected Service Type.")
        elif no_date_data:
            st.warning("⚠️ No data available for the selected Date Range.")
        elif no_payment_data:
            st.warning("⚠️ No data available for the selected Payment Method.")

        st.stop()

    # Sidebar Developer Info
    st.sidebar.header("📌 About the Developer")
    st.sidebar.markdown("""
    👤 **Mallikarjuna Reddy Gurrala**  
    📍 Data Analyst | Business Analyst  

    📧 [Email](mailto:mallikarjunreddy448@gmail.com)  
    [![LinkedIn](https://img.shields.io/badge/-LinkedIn-blue?logo=linkedin)](https://www.linkedin.com/in/mallikarjuna-reddy-841190246/)  
    [![GitHub](https://img.shields.io/badge/-GitHub-gray?logo=github)](https://github.com/MallikarjunaReddy448/)  
    [![HackerRank](https://img.shields.io/badge/-HackerRank-brightgreen?logo=hackerrank)](https://www.hackerrank.com/mallikarjunred19)  
    [![Tableau](https://img.shields.io/badge/-Tableau-orange?logo=tableau)](https://public.tableau.com/app/profile/mallikarjuna.reddy.gurrala/vizzes)
    """, unsafe_allow_html=True)


    # Main Dashboard
    st.title("🚖 Rapido Ride Analytics Dashboard")

    # Key Metrics
    total_revenue = filtered_df['total_fare'].sum().round()
    if total_revenue >= 1_000_000:
        formated_revenue = f"{total_revenue / 1_000_000:.1f}M"
    elif total_revenue >= 1_000:
        formated_revenue = f"{total_revenue / 1_000:.1f}K"
    else:
        formated_revenue = total_revenue
    total_rides = len(filtered_df)

    avg_fare = round(filtered_df['total_fare'].mean(), 2) if round(filtered_df['total_fare'].mean(), 2)>0 else 0

    cancellation_rate = round((filtered_df['ride_status'] == 'cancelled').mean() * 100, 2)

    total_distance = round(filtered_df['distance'].sum()) 

    col1, col2, col3, col4, col7 = st.columns(5)
    col1.metric("Total Revenue", f"₹ {formated_revenue}")
    col2.metric("Total Rides", f"{total_rides:,}") 
    col3.metric("Avg Fare", f"₹ {avg_fare}")
    col4.metric("Cancellation Rate", f"{cancellation_rate}%")
    col7.metric("Total Distance Covered", f"{total_distance:,} Km")

    
    # Visualization: Rides Over Time
    daily_revenue = filtered_df.groupby('date').agg(
                                daily_total_revenue = ('total_fare','sum')).reset_index()
    
    daily_revenue['daily_total_revenue'] = daily_revenue['daily_total_revenue'].round(2)

    fig2 = px.line(daily_revenue, x='date', y= 'daily_total_revenue', title="📈 Daily Total Fare Trend", markers=True)

    fig2.update_traces(
    hovertemplate="<b>Date:</b> %{x}<br><b>Revenue:</b> ₹%{y:,.2f}<extra></extra>"
)

    fig2.update_layout(
        yaxis_title = "Daily Total Revenue"
    )

    st.plotly_chart(fig2)

    # Visualization: Rides per Service

    col5, col6 = st.columns(2)

    is_data_empty = daily_revenue.empty or (daily_revenue['daily_total_revenue'] <= 0).all()


    with col5:
        if is_data_empty:
            service_type_rides = filtered_df.groupby('services').agg(
                            Total_rides = ('ride_id', 'count')).reset_index()
            
            service_type_rides['Total_rides'] = service_type_rides['Total_rides'].round(0)
            service_type_rides = service_type_rides.sort_values(by = 'Total_rides', ascending = False)

            fig1 = px.bar(service_type_rides, x='services', y = "Total_rides", title="No of 🛵 Rides cancelled for Service Type", color='services')

            fig1.update_traces(
            hovertemplate="<b>Service Type:</b> %{x}<br><b>Total Rides:</b> %{y:.0f}<extra></extra>"
        )
            
            fig1.update_layout(
                xaxis_title = "Type of Ride Service",
                yaxis_title = "Total No. of Rides",
            )
            st.plotly_chart(fig1, use_container_width = True, use_container_height = True)
        else:
            service_type_rides = filtered_df.groupby('services').agg(
                            Total_rides = ('ride_id', 'count')).reset_index()
            
            service_type_rides['Total_rides'] = service_type_rides['Total_rides'].round(0)
            service_type_rides = service_type_rides.sort_values(by = 'Total_rides', ascending = False)

            fig1 = px.bar(service_type_rides, x='services', y = "Total_rides", title="🛵 Rides by Service Type", color='services')

            fig1.update_traces(
            hovertemplate="<b>Service Type:</b> %{x}<br><b>Total Rides:</b> %{y:.0f}<extra></extra>"
        )
            
            fig1.update_layout(
                xaxis_title = "Type of Ride Service",
                yaxis_title = "Total No. of Rides",
            )
            st.plotly_chart(fig1, use_container_width = True, use_container_height = True)

    # visualization: Total Revenue by Payement Methods

    with col6:
        if is_data_empty:
            st.warning("🚨 Not enough data to plot revenue by payment method. Please select a valid ride type with revenue data.")
        else:
            payment_revenue = filtered_df.groupby('payment_method').agg(
                        Total_revenue = ('total_fare', 'sum'),
                        Total_rides = ('ride_id', 'count')
            ).reset_index()

            payment_revenue['Total_revenue'] = payment_revenue['Total_revenue'].round(0)

            fig3 = px.pie(payment_revenue, names='payment_method', values = 'Total_revenue', title = "Total Revenue by Payement Methods",
                        color_discrete_sequence = px.colors.sequential.RdBu, hover_data = {'payment_method': True, 'Total_revenue': True, 'Total_rides': True} )
            
            fig3.update_traces(
            customdata=payment_revenue[['Total_rides']],  
            hovertemplate="<b>Payment Method:</b> %{label}<br>"
                        "<b>Total Revenue:</b> ₹ %{value:,.0f}<br>"
                        "<b>Total Rides:</b> %{customdata[0]:,.0f}<extra></extra>"  
        )   
            
            st.plotly_chart(fig3, use_container_width = True, use_container_height = True)

    # Visualization: Peak Hours Analysis (Busiest Time Slots for Rides)
    col8, col9 = st.columns(2)

    with col8:
        if is_data_empty:
            filtered_df['time'] = pd.to_datetime(filtered_df['time'], errors='coerce')
            
            filtered_df['hour'] = filtered_df['time'].dt.hour
            hourly_rides = filtered_df.groupby('hour').size().reset_index(name="Total Rides")

            fig4 = px.bar(hourly_rides, x = "hour", y = "Total Rides", title = "Total Rides Cancelled in Peak ⏰ Hours", color = "Total Rides",
                        color_continuous_scale ='blues')
            
            fig4.update_layout(
                    xaxis_title = "Hour of Day (24 hours format)",
                    yaxis_title = "No. of Total Rides"
            )

            st.plotly_chart(fig4, use_container_width = True)
        else:
            filtered_df['time'] = pd.to_datetime(filtered_df['time'], errors='coerce')
            
            filtered_df['hour'] = filtered_df['time'].dt.hour
            hourly_rides = filtered_df.groupby('hour').size().reset_index(name="Total Rides")

            fig4 = px.bar(hourly_rides, x = "hour", y = "Total Rides", title = "⏰ Peak Ride Hours", color = "Total Rides",
                        color_continuous_scale ='blues')
            
            fig4.update_layout(
                    xaxis_title = "Hour of Day (24 hours format)",
                    yaxis_title = "No. of Total Rides"
            )

            st.plotly_chart(fig4, use_container_width = True)

    # Visualization: Ride Distance Distribution (Short vs Long Rides)
    with col9:
        if is_data_empty:
            bins = [0,3,10,15,25,35]
            labels = ["0-3 km", "3-10 km", "10-15 km", "15-30 km", "30+ km"]
            filtered_df['distance_categories'] =pd.cut(filtered_df['distance'], bins = bins, labels= labels)
            
            distance_counts = filtered_df['distance_categories'].value_counts().reset_index()
            distance_counts.columns = ['distance_categories', 'count']
            distance_counts = distance_counts.sort_values(by='distance_categories', ascending=False)

            # Define a yellow gradient color palette (high to low intensity)
            yellow_gradient = ["#FFFFF0", "#FFFFE0", "#FFFACD", "#FFEC8B", "#FFD700"]  # Dark to light yellow

            # Plot
            fig5 = px.bar(
                distance_counts.sort_values('distance_categories'),  # Ensure correct order
                y='count', 
                x='distance_categories', 
                title="📏 Rides Cancelled per Distance Distribution",
                color='count', 
                color_continuous_scale=px.colors.sequential.Cividis
            )

            fig5.update_layout(xaxis_title = 'Distance Categories', yaxis_title= "Count of Cancelled Rides")

            # Show in Streamlit
            st.plotly_chart(fig5)
        else:
            bins = [0,3,10,15,25,35]
            labels = ["0-3 km", "3-10 km", "10-15 km", "15-30 km", "30+ km"]
            filtered_df['distance_categories'] =pd.cut(filtered_df['distance'], bins = bins, labels= labels)
            
            distance_counts = filtered_df['distance_categories'].value_counts().reset_index()
            distance_counts.columns = ['distance_categories', 'count']
            distance_counts = distance_counts.sort_values(by='distance_categories', ascending=False)

            # Define a yellow gradient color palette (high to low intensity)
            yellow_gradient = ["#FFFFF0", "#FFFFE0", "#FFFACD", "#FFEC8B", "#FFD700"]  # Dark to light yellow

            # Plot
            fig5 = px.bar(
                distance_counts.sort_values('distance_categories'),  # Ensure correct order
                y='count', 
                x='distance_categories', 
                title="📏 Ride Distance Distribution",
                color='count', 
                color_continuous_scale=px.colors.sequential.Cividis
            )

            fig5.update_layout(xaxis_title = 'Distance Categories', yaxis_title= "Count of Total Rides")

            # Show in Streamlit
            st.plotly_chart(fig5)

    col10, col11 = st.columns(2)

    # Visualization: Ride Duration vs. Distance vs. Service Type

    with col10:
        if is_data_empty:
            scatter_data = filtered_df.groupby('services', as_index=False).agg(
                            Average_distance = ('distance', 'mean'),
                            Average_duration = ('duration', 'mean'),
                            Total_rides = ('ride_id', 'count'),
            )

            fig6 = px.scatter(scatter_data, x = 'Average_distance', y = 'Average_duration', color= 'services', size = 'Total_rides',
                            title = "Cancelled Rides: Duration vs. Distance vs. Service Type vs. No of Rides",
                            hover_data = {"Average_distance": ':,.2f',
                                        "Average_duration": ':,.2f',
                                        "Total_rides": ':,',})
            
            fig6.update_layout(
                xaxis_title = "Average Ride Cancelled Distance (Km)",
                yaxis_title = "Average Ride Cancelled Duration (Hr)",
                
            )

            st.plotly_chart(fig6)
        else:
            scatter_data = filtered_df.groupby('services', as_index=False).agg(
                            Average_distance = ('distance', 'mean'),
                            Average_duration = ('duration', 'mean'),
                            Total_rides = ('ride_id', 'count'),
            )

            fig6 = px.scatter(scatter_data, x = 'Average_distance', y = 'Average_duration', color= 'services', size = 'Total_rides',
                            title = "Ride Duration vs. Distance vs. Service Type vs. No of Rides",
                            hover_data = {"Average_distance": ':,.2f',
                                        "Average_duration": ':,.2f',
                                        "Total_rides": ':,',})
            
            fig6.update_layout(
                xaxis_title = "Average Ride Distance (Km)",
                yaxis_title = "Average Ride Duration (Hr)",
                
            )

            st.plotly_chart(fig6)

    with col11:
        if is_data_empty:
            top_source_destination_pairs = filtered_df.groupby(['source', 'destination']).size().reset_index(name='count').sort_values(by='count', ascending=False).head(10)
            top_source_destination_pairs['route'] = top_source_destination_pairs['source']+ " → "+ top_source_destination_pairs['destination']

            fig7 = go.Figure(go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=top_source_destination_pairs['source'].tolist() + top_source_destination_pairs['destination'].tolist()
                ),
                link=dict(
                    source=top_source_destination_pairs['source'].astype('category').cat.codes.tolist(),
                    target=top_source_destination_pairs['destination'].astype('category').cat.codes.tolist(),
                    value=top_source_destination_pairs['count'].tolist()
                )
            ))

            fig7.update_layout(title_text="Top 10 Most Common Cancelled Ride Routes - Sankey Diagram")
            st.plotly_chart(fig7)
        else:
            top_source_destination_pairs = filtered_df.groupby(['source', 'destination']).size().reset_index(name='count').sort_values(by='count', ascending=False).head(10)
            top_source_destination_pairs['route'] = top_source_destination_pairs['source']+ " → "+ top_source_destination_pairs['destination']

            fig7 = go.Figure(go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label= [f"{s} →" for s in top_source_destination_pairs['source']] + top_source_destination_pairs['destination'].tolist()
                ),
                link=dict(
                source=top_source_destination_pairs['source'].astype('category').cat.codes.tolist(),
                target=top_source_destination_pairs['destination'].astype('category').cat.codes.tolist(),
                value=top_source_destination_pairs['count'].tolist()
            )
            ))

            fig7.update_layout(title_text="Top 10 Most Common Ride Routes - Sankey Diagram")
            st.plotly_chart(fig7)

    # Visualization: Forecasting Future Rides (Using Time-Series Model)
    # for cancelled rides
    model_choice = st.radio("Choose a Forecasting Model: ", ('Hol-winters', "Facebook-Prophet")) 

    
    if model_choice == 'Hol-winters':

        def holt_winters_forecast():
            if is_data_empty:
                st.warning("🚨 Expected Rides to be cancelled for next month")
                daily_rides = filtered_df.groupby('date').size().reset_index(name='total_rides') 
                forecast_color = 'red'
            else:
                forecast_color = 'green'
            daily_rides = filtered_df.groupby('date').size().reset_index(name='total_rides')
            forecast_period = 30
            future_dates = pd.date_range(start=daily_rides['date'].max(), periods=forecast_period+1, freq='D')[1:] 

            model = ExponentialSmoothing(daily_rides['total_rides'], trend= 'add', seasonal = 'add', seasonal_periods = 14).fit()
            historical_forecast = model.fittedvalues
            future_forecast = model.forecast(steps=forecast_period)

            future_rides_df = pd.DataFrame({'date': future_dates, 'forecast': future_forecast})
            future_rides_df['forecast'] = future_rides_df['forecast'].round(0)
            
            daily_rides['forecast'] = historical_forecast
            forecasted_data = pd.concat([daily_rides, future_rides_df], ignore_index=True)

            # Plot the results
            fig8 = go.Figure()

            # Actual ride data
            fig8.add_trace(go.Scatter(
                x=daily_rides['date'], y=daily_rides['total_rides'],
                mode='lines+markers', name='Actual Rides',
                line=dict(color='blue')
            ))

            # Forecasted rides with dynamic color
            fig8.add_trace(go.Scatter(
                x=forecasted_data['date'], y=forecasted_data['forecast'],
                mode='lines', name='Forecasted Rides',
                line=dict(color=forecast_color, dash=None)
            ))

            # Layout settings
            fig8.update_layout(
                title="🔮 Predicted Rides for Next Month",
                xaxis_title="Date",
                yaxis_title="Total Rides",
                template="plotly_white"
            )

            # Display the plot
            st.plotly_chart(fig8)

            # Visualization: Forecasting Future Revenue (Using Time-Series Model)
            if is_data_empty:
                st.warning("🚨 Not enough data to forecast revenue as cancelled rides selected. Please select a valid ride (All rides / Completed Rides) status to get revenue data insights.")
            else:
                forecast_color = 'green'
                future_dates_revenue = pd.date_range(start=daily_revenue['date'].max(), periods=forecast_period+1, freq='D')[1:]

                daily_revenue['daily_total_revenue'] = daily_revenue['daily_total_revenue'].round(0)

                revenue_model = ExponentialSmoothing(daily_revenue['daily_total_revenue'], trend = 'mul', seasonal = 'mul', seasonal_periods = 14).fit()
                dhistorical_forecast_rev = revenue_model.fittedvalues
                future_forecast_rev = revenue_model.forecast(steps=forecast_period)

                # Create DataFrame for future dates
                future_df_rev = pd.DataFrame({'date': future_dates_revenue, 'forecast': future_forecast_rev})

                # Merge historical data with future forecast
                daily_revenue['forecast'] = dhistorical_forecast_rev
                forecasted_revenue_data = pd.concat([daily_revenue, future_df_rev], ignore_index=True)

                forecasted_revenue_data['forecast'] = forecasted_revenue_data['forecast'].round(0)

                # Plot the results
                fig9 = go.Figure()

                # Actual revenue data
                fig9.add_trace(go.Scatter(
                    x=daily_revenue['date'], y=daily_revenue['daily_total_revenue'],
                    mode='lines+markers', name='Actual Revenue',
                    line=dict(color='blue')
                ))

                # Forecasted revenue with dynamic color
                fig9.add_trace(go.Scatter(
                    x=forecasted_revenue_data['date'], y=forecasted_revenue_data['forecast'],
                    mode='lines', name='Forecasted Revenue',
                    line=dict(color=forecast_color, dash=None)
                ))

                # Layout settings
                fig9.update_layout(
                    title="🔮 Predicted Revenue for Next Month",
                    xaxis_title="Date",
                    yaxis_title="Total Revenue",
                    template="plotly_white"
                )

                # Display the plot
                st.plotly_chart(fig9)

                
        holt_winters_forecast()

    elif  model_choice == 'Facebook-Prophet':
        def prophet_rides_forecast():
            if is_data_empty:
                daily_rides = filtered_df.groupby('date').size().reset_index(name='total_rides')
                st.warning("🚨 Expected Rides to be cancelled for next month")
                forecast_color = 'red'
            else:
                daily_rides = filtered_df.groupby('date').size().reset_index(name='total_rides')
                forecast_color = 'green'

            forecast_period = 30
            daily_rides.columns = ['ds', 'y']

            model = Prophet()
            model.fit(daily_rides)

            future = model.make_future_dataframe(periods=forecast_period)
            forecast = model.predict(future)

            # Create Plotly figure
            fig10 = go.Figure()

            # Actual rides data
            fig10.add_trace(go.Scatter(
                x=daily_rides['ds'], y=daily_rides['y'],
                mode='lines+markers', name='Actual Rides',
                line=dict(color='blue')
            ))

            # Forecasted rides
            fig10.add_trace(go.Scatter(
                x=forecast['ds'], y=forecast['yhat'],
                mode='lines', name='Forecasted Rides',
                line=dict(color=forecast_color, dash='dash')
            ))

            # Confidence interval
            fig10.add_trace(go.Scatter(
                x=forecast['ds'], y=forecast['yhat_upper'],
                mode='lines', name='Upper Bound',
                line=dict(color=f'rgba({255 if forecast_color=="red" else 0},128,0,0.3)')
            ))

            fig10.add_trace(go.Scatter(
                x=forecast['ds'], y=forecast['yhat_lower'],
                mode='lines', name='Lower Bound',
                fill='tonexty', line=dict(color=f'rgba({255 if forecast_color=="red" else 0},128,0,0.3)')
            ))

            # Layout settings
            fig10.update_layout(
                title="🔮 Predicted Rides for Next Month",
                xaxis_title="Date",
                yaxis_title="Total Rides",
                template="plotly_white"
            )

            # Display the plot
            st.plotly_chart(fig10)


        prophet_rides_forecast()

        def prophet_revenue_forecast():
            if is_data_empty:
                daily_revenue = filtered_df.groupby('date')['total_fare'].sum().reset_index(name='total_fare')
                st.warning("🚨 Not enough data to forecast revenue as cancelled rides selected. Please select a valid ride (All rides / Completed Rides) status to get revenue data insights.")
            else:
                daily_revenue = filtered_df.groupby('date')['total_fare'].sum().reset_index(name='total_fare')

                forecast_period = 30
                daily_revenue.columns = ['ds', 'y']

                model = Prophet()
                model.fit(daily_revenue)

                future = model.make_future_dataframe(periods=forecast_period)
                forecast = model.predict(future)

                # Create Plotly figure
                fig = go.Figure()

                # Actual revenue data
                fig.add_trace(go.Scatter(
                    x=daily_revenue['ds'], y=daily_revenue['y'],
                    mode='lines+markers', name='Actual Revenue',
                    line=dict(color='blue')
                ))

                # Forecasted revenue
                fig.add_trace(go.Scatter(
                    x=forecast['ds'], y=forecast['yhat'],
                    mode='lines', name='Forecasted Revenue',
                    line=dict(color='green', dash='dash')
                ))

                # Confidence interval
                fig.add_trace(go.Scatter(
                    x=forecast['ds'], y=forecast['yhat_upper'],
                    mode='lines', name='Upper Bound',
                    line=dict(color='green')
                ))

                fig.add_trace(go.Scatter(
                    x=forecast['ds'], y=forecast['yhat_lower'],
                    mode='lines', name='Lower Bound',
                    fill='tonexty', line=dict(color='green')
                ))

                # Layout settings
                fig.update_layout(
                    title="🔮 Predicted Revenue for Next Month",
                    xaxis_title="Date",
                    yaxis_title="Total Revenue",
                    template="plotly_white"
                )

                # Display the plot
                st.plotly_chart(fig)


        prophet_revenue_forecast()


    # Footer
    st.write("📊 **Developed by Mallikarjuna Reddy Gurrala** \n\n Check out the about page for more information and contact details for colloboration")
    
    

if __name__ == '__main__':
    main()

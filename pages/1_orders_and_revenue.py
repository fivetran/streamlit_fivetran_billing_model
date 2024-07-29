import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from functions.setup_page import page_creation

## Apply standard page settings.
st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title('Orders and Revenue')

## Define data and filters. The resulting data variable includes the data with all filters applied.
data = page_creation()

st.divider()

## Ensure all date columns are in datetime format
date_columns = ['created_at', 'customer_created_at', 'payment_at', 'subscription_period_started_at', 'subscription_period_ended_at']
for col in date_columns:
    if col in data.columns:
        data[col] = pd.to_datetime(data[col], errors='coerce')

st.divider()

st.dataframe(data.head(10)) ## This is here just as an example. This can be deleted during development and before release.

st.divider()

# KPI Metrics
with st.container():
    col1, col2, col3, col4 = st.columns(4)

    total_revenue = data['total_amount'].sum()
    number_of_orders = data['header_id'].nunique()
    number_of_customers = data['customer_id'].nunique()
    new_customers = data[data['customer_created_at'] == data['created_at']]['customer_id'].nunique()

    with col1:
        st.metric(label="**Total Revenue**", value=f"${total_revenue:,.2f}")

    with col2:
        st.metric(label="**Number of Orders**", value=number_of_orders)

    with col3:
        st.metric(label="**Number of Customers**", value=number_of_customers)

    with col4:
        st.metric(label="**New Customers**", value=new_customers)


# Time series charts
data['month'] = data['created_at'].dt.to_period('M').dt.to_timestamp()

with st.container():
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)

    with row1_col1:
        st.markdown("**Total Revenue Over Time**")
        revenue_over_time = data.groupby('month')['total_amount'].sum().reset_index()
        fig = px.line(revenue_over_time, x='month', y='total_amount')
        fig.update_yaxes(tickprefix='$', tickformat='~s', title_text='Revenue ($1000s)')
        fig.update_xaxes(title_text='Month')
        st.plotly_chart(fig, use_container_width=True)

    with row1_col2:
        st.markdown("**Total Orders Over Time**")
        orders_over_time = data.groupby('month')['header_id'].nunique().reset_index()
        fig = px.line(orders_over_time, x='month', y='header_id')
        fig.update_yaxes(title_text='Orders')
        fig.update_xaxes(title_text='Month')
        st.plotly_chart(fig, use_container_width=True)

    with row2_col1:
        st.markdown("**Percent of Successful Payments Over Time**")
        successful_payments = data[data['header_status'] == 'completed'].groupby('month')['payment_id'].nunique()
        total_payments = data.groupby('month')['payment_id'].nunique()
        percent_successful = (successful_payments / total_payments * 100).fillna(0).reset_index()
        fig = px.line(percent_successful, x='month', y='payment_id')
        fig.update_yaxes(range=[0, 100], title_text='Percentage (%)')
        fig.update_xaxes(title_text='Month')
        st.plotly_chart(fig, use_container_width=True)

    with row2_col2:
        st.markdown("**New Customers Over Time**")
        data['customer_created_month'] = data['customer_created_at'].dt.to_period('M').dt.to_timestamp()
        new_customers_over_time = data.groupby('customer_created_month')['customer_id'].nunique().reset_index()
        fig = px.line(new_customers_over_time, x='customer_created_month', y='customer_id')
        fig.update_yaxes(title_text='Customers')
        fig.update_xaxes(title_text='Month')
        st.plotly_chart(fig, use_container_width=True)

# Customer Table
st.markdown("**Customer Table**")
customer_table = data[['customer_id', 'customer_name', 'customer_email', 'customer_city', 'customer_country']].drop_duplicates().reset_index(drop=True)
st.dataframe(customer_table)

# Location Performance Chart
# Aggregate revenue by customer_country
location_performance = data.groupby('customer_country')['total_amount'].sum().reset_index()

# Sort by total_amount in descending order
location_performance = location_performance.sort_values(by='total_amount', ascending=False)

# Create the Plotly Express bar chart
fig = px.bar(
    location_performance,
    x='customer_country',
    y='total_amount',
    color='total_amount',
    title='Revenue by Country',
    labels={'customer_country': 'Country', 'total_amount': 'Total Revenue'},
    color_continuous_scale=px.colors.sequential.Blues
)

# Update the y-axis to show values in thousands
fig.update_yaxes(tickprefix='$', tickformat='~s', title_text='Total Revenue')

# Update the color bar to show values in thousands
fig.update_coloraxes(colorbar_tickprefix='$', colorbar_tickformat='~s')

# Display the chart
st.plotly_chart(fig, use_container_width=True)
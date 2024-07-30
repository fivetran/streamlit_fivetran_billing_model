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

## Ensure all date columns are in datetime format
date_columns = ['created_at', 'customer_created_at', 'payment_at', 'subscription_period_started_at', 'subscription_period_ended_at']
for col in date_columns:
    if col in data.columns:
        data[col] = pd.to_datetime(data[col], errors='coerce')

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


st.divider()

# Time series charts
data['month'] = data['created_at'].dt.to_period('M').dt.to_timestamp()

with st.container():
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)

    with row1_col1:
        st.markdown("**Total Revenue Over Time**")
        revenue_over_time = data.groupby('month')['total_amount'].sum().reset_index()
        fig = px.bar(revenue_over_time, x='month', y='total_amount')
        fig.update_yaxes(tickprefix='$', tickformat='~s', title_text='Revenue', range=[0, revenue_over_time['total_amount'].max() * 1.1])
        fig.update_xaxes(title_text='Month')
        st.plotly_chart(fig, use_container_width=True)

    with row1_col2:
        st.markdown("**Total Orders Over Time**")
        orders_over_time = data.groupby('month')['header_id'].nunique().reset_index()
        fig = px.bar(orders_over_time, x='month', y='header_id')
        fig.update_yaxes(title_text='Orders', range=[0, orders_over_time['header_id'].max() * 1.1])
        fig.update_xaxes(title_text='Month')
        st.plotly_chart(fig, use_container_width=True)

    with row2_col1:
        st.markdown("**Percent of Successful Payments Over Time**")
        successful_payments = data[data['header_status'] == 'completed'].groupby('month')['payment_id'].nunique()
        total_payments = data.groupby('month')['payment_id'].nunique()
        percent_successful = (successful_payments / total_payments * 100).fillna(0).reset_index()
        fig = px.bar(percent_successful, x='month', y='payment_id')
        fig.update_yaxes(range=[0, 100], title_text='Percentage (%)')
        fig.update_xaxes(title_text='Month')
        st.plotly_chart(fig, use_container_width=True)

    with row2_col2:
        st.markdown("**New Customers Over Time**")
        data['customer_created_month'] = data['customer_created_at'].dt.to_period('M').dt.to_timestamp()
        new_customers_over_time = data.groupby('customer_created_month')['customer_id'].nunique().reset_index()
        fig = px.bar(new_customers_over_time, x='customer_created_month', y='customer_id')
        fig.update_yaxes(title_text='Customers', range=[0, new_customers_over_time['customer_id'].max() * 1.1])
        fig.update_xaxes(title_text='Month')
        st.plotly_chart(fig, use_container_width=True)


# Location Performance Chart
# Aggregate revenue by customer_country
location_performance = data.groupby('customer_country')['total_amount'].sum().reset_index()

# Sort by total_amount in descending order
location_performance = location_performance.sort_values(by='total_amount', ascending=False)

# Create the Plotly Express choropleth map
fig = px.choropleth(
    location_performance,
    locations='customer_country',
    locationmode='country names',
    color='total_amount',
    color_continuous_scale=px.colors.sequential.Blues,
    title='Revenue by Country',
    labels={'customer_country': 'Country', 'total_amount': 'Total Revenue'},
    hover_name='customer_country',
    hover_data={'total_amount': True}
)

# Update the color bar to show values in thousands
fig.update_coloraxes(colorbar_tickprefix='$', colorbar_tickformat='~s')

# Update layout to make the map bigger
fig.update_layout(
    autosize=False,
    width=1200,  # Width in pixels
    height=900,  # Height in pixels
    title=dict(
        x=0.5,  # Center title horizontally
        xanchor='center'
    )
)

# Display the map
st.plotly_chart(fig, use_container_width=True)


# Customer Table

# Calculate Total Spend
total_spend = data.groupby('customer_id')['total_amount'].sum().reset_index()

# Calculate Total Orders
total_orders = data.groupby('customer_id')['header_id'].nunique().reset_index()
total_orders.rename(columns={'header_id': 'total_orders'}, inplace=True)

# Calculate Total Refunds
total_refunds = data.groupby('customer_id')['refund_amount'].sum().reset_index()

# Calculate Total Discounts
total_discounts = data.groupby('customer_id')['discount_amount'].sum().reset_index()

# Calculate Last Order Date
last_order_date = data.groupby('customer_id')['created_at'].max().reset_index()

# Calculate Created Date
created_date = data.groupby('customer_id')['customer_created_at'].min().reset_index()

# Merge all the calculated fields
customer_table = data[['customer_id', 'customer_name', 'customer_email', 'customer_city', 'customer_country']].drop_duplicates().reset_index(drop=True)
customer_table = customer_table.merge(total_spend, on='customer_id', how='left')
customer_table = customer_table.merge(total_orders, on='customer_id', how='left')
customer_table = customer_table.merge(total_refunds, on='customer_id', how='left')
customer_table = customer_table.merge(total_discounts, on='customer_id', how='left')
customer_table = customer_table.merge(last_order_date, on='customer_id', how='left')
customer_table = customer_table.merge(created_date, on='customer_id', how='left')

# Rename columns
customer_table.rename(columns={
    'customer_id': 'ID',
    'customer_name': 'Name',
    'customer_email': 'Email',
    'customer_city': 'City',
    'customer_country': 'Country',
    'total_amount': 'Total Spend',
    'refund_amount': 'Total Refunds',
    'discount_amount': 'Total Discounts',
    'created_at': 'Last Order Date',
    'customer_created_at': 'Created Date',
}, inplace=True)

# Format dollar columns
customer_table['Total Spend'] = customer_table['Total Spend'].apply(lambda x: f"${x:,.2f}")
customer_table['Total Refunds'] = customer_table['Total Refunds'].apply(lambda x: f"${x:,.2f}")
customer_table['Total Discounts'] = customer_table['Total Discounts'].apply(lambda x: f"${x:,.2f}")

# Format date columns
customer_table['Last Order Date'] = pd.to_datetime(customer_table['Last Order Date']).dt.strftime('%Y-%m-%d')
customer_table['Created Date'] = pd.to_datetime(customer_table['Created Date']).dt.strftime('%Y-%m-%d')

# Display the customer table
st.markdown("**Enhanced Customer Table**")
st.dataframe(customer_table)
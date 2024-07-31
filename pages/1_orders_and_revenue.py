import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from functions.setup_page import page_creation
from plotly.subplots import make_subplots

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

# Calculate KPIs
data['month'] = data['created_at'].dt.to_period('M').dt.to_timestamp()
data['quarter'] = data['created_at'].dt.to_period('Q').dt.to_timestamp()

current_quarter = data['quarter'].max()
previous_quarter = current_quarter - pd.offsets.QuarterBegin(n=1)
current_year = data['created_at'].dt.year.max()
previous_year = current_year - 1

total_revenue = data['total_amount'].sum()
number_of_orders = data['header_id'].nunique()
number_of_customers = data['customer_id'].nunique()
min_created_at = data['created_at'].min()
max_created_at = data['created_at'].max()
new_customers = data[(data['customer_created_at'] >= min_created_at) & (data['customer_created_at'] <= max_created_at)].shape[0]

total_revenue_qoq = data[data['quarter'] == current_quarter]['total_amount'].sum() - data[data['quarter'] == previous_quarter]['total_amount'].sum()
total_revenue_yoy = data[data['created_at'].dt.year == current_year]['total_amount'].sum() - data[data['created_at'].dt.year == previous_year]['total_amount'].sum()

number_of_orders_qoq = data[data['quarter'] == current_quarter]['header_id'].nunique() - data[data['quarter'] == previous_quarter]['header_id'].nunique()
number_of_orders_yoy = data[data['created_at'].dt.year == current_year]['header_id'].nunique() - data[data['created_at'].dt.year == previous_year]['header_id'].nunique()

number_of_customers_qoq = data[data['quarter'] == current_quarter]['customer_id'].nunique() - data[data['quarter'] == previous_quarter]['customer_id'].nunique()
number_of_customers_yoy = data[data['created_at'].dt.year == current_year]['customer_id'].nunique() - data[data['created_at'].dt.year == previous_year]['customer_id'].nunique()

new_customers_qoq = data[(data['customer_created_at'] >= current_quarter) & (data['customer_created_at'] < current_quarter + pd.offsets.QuarterEnd())].shape[0] - \
                    data[(data['customer_created_at'] >= previous_quarter) & (data['customer_created_at'] < previous_quarter + pd.offsets.QuarterEnd())].shape[0]
new_customers_yoy = data[(data['customer_created_at'].dt.year == current_year)].shape[0] - data[(data['customer_created_at'].dt.year == previous_year)].shape[0]

# KPI Metrics
with st.container():
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="**Total Revenue**", value=f"${total_revenue:,.2f}", delta=f"${total_revenue_qoq:,.2f} QoQ, ${total_revenue_yoy:,.2f} YoY")

    with col2:
        st.metric(label="**Number of Orders**", value=number_of_orders, delta=f"{number_of_orders_qoq} QoQ, {number_of_orders_yoy} YoY")

    with col3:
        st.metric(label="**Number of Customers in Period**", value=number_of_customers, delta=f"{number_of_customers_qoq} QoQ, {number_of_customers_yoy} YoY")

    with col4:
        st.metric(label="**New Customers**", value=new_customers, delta=f"{new_customers_qoq} QoQ, {new_customers_yoy} YoY")


# Time series charts
data['month'] = data['created_at'].dt.to_period('M').dt.to_timestamp()

with st.container():
    # Revenue and Orders chart (full width)
    st.markdown("**Total Revenue and Orders Over Time**")
    revenue_over_time = data.groupby('month')['total_amount'].sum().reset_index()
    orders_over_time = data.groupby('month')['header_id'].nunique().reset_index()
    combined_data = revenue_over_time.merge(orders_over_time, on='month')
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add revenue bars
    fig.add_trace(
        go.Bar(
            x=combined_data['month'],
            y=combined_data['total_amount'],
            name='Revenue',
            text=combined_data['total_amount'].apply(lambda x: f'${x:,.0f}'),
            textposition='outside',
            marker_color='#1f77b4'  # Blue color for revenue bars
        ),
        secondary_y=False,
    )
    
    # Add orders line
    fig.add_trace(
        go.Scatter(
            x=combined_data['month'],
            y=combined_data['header_id'],
            name='Orders',
            mode='lines+markers+text',
            text=combined_data['header_id'],
            textposition='top center',
            line=dict(color='#ff7f0e', width=3),  # Orange color for orders line
            marker=dict(size=8)
        ),
        secondary_y=True,
    )
    
    fig.update_layout(
        legend=dict(x=0.01, y=0.99, bgcolor='rgba(255, 255, 255, 0.5)'),
        barmode='group',
        height=500  # Increase height for better visibility
    )
    
    fig.update_xaxes(title_text="Month", tickformat='%b %Y')
    fig.update_yaxes(title_text="Revenue", secondary_y=False, tickprefix='$', tickformat='~s')
    fig.update_yaxes(title_text="Orders", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)

    # Product Revenue and New Customers charts 
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Product Revenue by Time Period**")
        product_revenue = data.groupby(['product_name', 'month'])['total_amount'].sum().reset_index()
        product_revenue['cumulative_revenue'] = product_revenue.groupby('product_name')['total_amount'].cumsum()
        cumulative_revenue_by_product = product_revenue.groupby('product_name')['cumulative_revenue'].max().reset_index()
        cumulative_revenue_by_product = cumulative_revenue_by_product.sort_values(by='cumulative_revenue', ascending=False)
        
        # Use a color sequence for differentiation
        color_sequence = px.colors.qualitative.Set3  # You can change this to another color sequence if desired
        
        fig = px.bar(cumulative_revenue_by_product, 
                     y='product_name', 
                     x='cumulative_revenue', 
                     orientation='h',
                     color='product_name',  # Color bars by product name
                     color_discrete_sequence=color_sequence)  # Use the color sequence
        
        fig.update_xaxes(tickprefix='$', tickformat='~s', title_text='Cumulative Revenue')
        fig.update_yaxes(title_text='Product')
        fig.update_traces(text=cumulative_revenue_by_product['cumulative_revenue'].apply(lambda x: f'${x:,.0f}'), textposition='outside')
        fig.update_layout(showlegend=False)  # Hide legend as it's redundant with y-axis labels
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**New Customers Over Time**")
        
        # Apply the same date filter as used in other charts
        filtered_data = data[(data['created_at'] >= min_created_at) & (data['created_at'] <= max_created_at)]
        
        filtered_data['customer_created_month'] = filtered_data['customer_created_at'].dt.to_period('M').dt.to_timestamp()
        new_customers_over_time = filtered_data.groupby('customer_created_month')['customer_id'].nunique().reset_index()
        
        fig = px.bar(new_customers_over_time, 
                    x='customer_created_month', 
                    y='customer_id',
                    color_discrete_sequence=['#2ca02c'])  # Green color for consistency
        
        fig.update_yaxes(title_text='New Customers', range=[0, new_customers_over_time['customer_id'].max() * 1.1])
        fig.update_xaxes(title_text='Month', tickformat='%b %Y')
        fig.update_traces(text=new_customers_over_time['customer_id'], textposition='outside')
        
        # Ensure x-axis range matches the filter
        fig.update_xaxes(range=[min_created_at, max_created_at])
        
        # Update layout for consistency
        fig.update_layout(
            height=400  # Adjust height to match other charts if needed
        )
        
        st.plotly_chart(fig, use_container_width=True)


# Location Performance Chart
# Aggregate revenue by customer_country
location_performance = data.groupby('customer_country')['total_amount'].sum().reset_index()

# Sort by total_amount in descending order
location_performance = location_performance.sort_values(by='total_amount', ascending=False)
# Format total_amount for better readability
location_performance['total_amount_formatted'] = location_performance['total_amount'].apply(lambda x: f"${x:,.0f}")
# Define a custom color scale that starts with darker shades of green
custom_color_scale = [
    (0.0, "rgb(198, 219, 239)"),
    (0.2, "rgb(158, 202, 225)"),
    (0.4, "rgb(107, 174, 214)"),
    (0.6, "rgb(66, 146, 198)"),
    (0.8, "rgb(33, 113, 181)"),
    (1.0, "rgb(8, 69, 148)")
]
# Create the Plotly Express choropleth map
fig = px.choropleth(
    location_performance,
    locations='customer_country',
    locationmode='country names',
    color='total_amount',
    color_continuous_scale=custom_color_scale,
    title='Revenue by Country',
    labels={'customer_country': 'Country', 'total_amount_formatted': 'Total Revenue'}
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
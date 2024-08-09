# orders_and_revenue

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

current_year = data['created_at'].dt.year.max()
previous_year = current_year - 1

total_revenue = data['total_amount'].sum()
number_of_orders = data['header_id'].nunique()
number_of_customers = data['customer_id'].nunique()
min_created_at = data['created_at'].min()
max_created_at = data['created_at'].max()
new_customers = data[(data['customer_created_at'] >= min_created_at) & (data['customer_created_at'] <= max_created_at)].shape[0]

# Helper function to calculate percentage change
def percentage_change(current, previous):
    return ((current - previous) / previous * 100) if previous != 0 else float('inf')

# Calculate percentage changes for YoY
total_revenue_yoy = percentage_change(
    data[data['created_at'].dt.year == current_year]['total_amount'].sum(),
    data[data['created_at'].dt.year == previous_year]['total_amount'].sum()
)

number_of_orders_yoy = percentage_change(
    data[data['created_at'].dt.year == current_year]['header_id'].nunique(),
    data[data['created_at'].dt.year == previous_year]['header_id'].nunique()
)

number_of_customers_yoy = percentage_change(
    data[data['created_at'].dt.year == current_year]['customer_id'].nunique(),
    data[data['created_at'].dt.year == previous_year]['customer_id'].nunique()
)

new_customers_yoy = percentage_change(
    data[data['customer_created_at'].dt.year == current_year].shape[0],
    data[data['customer_created_at'].dt.year == previous_year].shape[0]
)

# KPI Metrics
with st.container():
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="**Total Revenue**", value=f"${total_revenue:,.2f}", 
                  delta=f"{total_revenue_yoy:.1f}% YoY")

    with col2:
        st.metric(label="**Number of Orders**", value=number_of_orders, 
                  delta=f"{number_of_orders_yoy:.1f}% YoY")

    with col3:
        st.metric(label="**Number of Customers in Period**", value=number_of_customers, 
                  delta=f"{number_of_customers_yoy:.1f}% YoY")

    with col4:
        st.metric(label="**New Customers**", value=new_customers, 
                  delta=f"{new_customers_yoy:.1f}% YoY")
        

# Time series charts
data['month'] = data['created_at'].dt.to_period('M').dt.to_timestamp()

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

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
            marker_color='#1f77b4',  # Blue color for revenue bars
            textfont=dict(size=10)
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
            text=combined_data['header_id'].astype(str),
            textposition='top center',
            textfont=dict(size=10, color='#ff7f0e'),
            line=dict(color='#ff7f0e', width=3),  # Orange color for orders line
            marker=dict(size=8)
        ),
        secondary_y=True,
    )
    
    # Update layout
    fig.update_layout(
        legend=dict(x=0.01, y=0.99, bgcolor='rgba(255, 255, 255, 0.5)'),
        height=500,  # Increase height for better visibility
    )
    
    fig.update_xaxes(title_text="Month", tickformat='%b %Y')
    fig.update_yaxes(
        title_text="Revenue", 
        secondary_y=False, 
        tickprefix='$', 
        tickformat='~s',
        showgrid=False,  # Hide grid lines for Revenue axis
        showline=False   # Hide axis line for Revenue axis
    )
    fig.update_yaxes(
        title_text="Orders", 
        secondary_y=True,
        showgrid=False,  # Hide grid lines for Orders axis
        showline=False   # Hide axis line for Orders axis
    )
    
    # Adjust the y-axis range for Orders to reduce overlap
    max_revenue = combined_data['total_amount'].max()
    max_orders = combined_data['header_id'].max()
    revenue_order_ratio = max_revenue / max_orders
    
    fig.update_yaxes(
        range=[0, max_revenue * 1.2],  # Increase the range for Revenue axis
        secondary_y=False
    )
    fig.update_yaxes(
        range=[0, max_orders * (1 + (1 / revenue_order_ratio))],  # Adjust Orders axis proportionally
        secondary_y=True
    )
    
    # Ensure labels are above everything
    fig.update_traces(textfont_size=10)
    fig.update_traces(textposition='outside', selector=dict(type='bar'))
    fig.update_traces(textposition='top center', selector=dict(type='scatter'))
    
    st.plotly_chart(fig, use_container_width=True)

    # Product Revenue and New Customers charts 
    col1, col2 = st.columns(2)
    
with col1:
    st.markdown("**Product By Revenue**")
    product_revenue = data.groupby('product_name')['total_amount'].sum().reset_index()
    product_revenue = product_revenue.sort_values(by='total_amount', ascending=False)  # Changed to descending order

    # Create the figure manually with a blue gradient
    fig = go.Figure()

    # Create a blue color gradient
    n_products = len(product_revenue)
    blue_gradient = [f'rgb({int(33 + (i/n_products) * 165)}, {int(113 + (i/n_products) * 86)}, {int(181 + (i/n_products) * 74)})' for i in range(n_products)]

    fig.add_trace(go.Bar(
        y=product_revenue['product_name'],
        x=product_revenue['total_amount'],
        orientation='h',
        marker=dict(
            color=product_revenue['total_amount'],
            colorscale='Blues',
            reversescale=False,  # Changed to False to make darker blue correspond to higher revenue
        ),
        text=product_revenue['total_amount'].apply(lambda x: f"${x:,.0f}"),
        textposition='outside'
    ))

    fig.update_layout(
        xaxis_title="Total Revenue",
        yaxis_title="Product",
        yaxis=dict(autorange="reversed"),  # This will keep the order as is (highest revenue at top)
        xaxis=dict(tickprefix='$', tickformat='~s'),
        height=400,
        margin=dict(l=0, r=100, t=30, b=0),
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )

    # Adjust x-axis range to accommodate labels
    max_revenue = product_revenue['total_amount'].max()
    fig.update_xaxes(range=[0, max_revenue * 1.2])  # Extend x-axis by 20%

    st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("**New Customers Over Time**")
        
        # Apply the same date filter as used in other charts
        filtered_data = data[(data['customer_created_at'] >= min_created_at) & (data['customer_created_at'] <= max_created_at)]
        
        filtered_data['customer_created_month'] = filtered_data['customer_created_at'].dt.to_period('M').dt.to_timestamp()
        new_customers_over_time = filtered_data.groupby('customer_created_month')['customer_id'].nunique().reset_index()
        
        fig = px.bar(new_customers_over_time, 
                    x='customer_created_month', 
                    y='customer_id',
                    color_discrete_sequence=['#1f77b4'])  # Changed to blue
        
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


# Display the title above the filters
st.markdown("**Enhanced Customer Table**")

# Create two columns for the filter inputs
col1, col2 = st.columns([1, 1])

# Place the filters in these columns
with col1:
    name_filter = st.text_input("Filter by Customer Name", "")
with col2:
    email_filter = st.text_input("Filter by Customer Email", "")

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
filtered_customer_table = data[['customer_id', 'customer_name', 'customer_email', 'customer_city', 'customer_country']].drop_duplicates().reset_index(drop=True)
filtered_customer_table = filtered_customer_table.merge(total_spend, on='customer_id', how='left')
filtered_customer_table = filtered_customer_table.merge(total_orders, on='customer_id', how='left')
filtered_customer_table = filtered_customer_table.merge(total_refunds, on='customer_id', how='left')
filtered_customer_table = filtered_customer_table.merge(total_discounts, on='customer_id', how='left')
filtered_customer_table = filtered_customer_table.merge(last_order_date, on='customer_id', how='left')
filtered_customer_table = filtered_customer_table.merge(created_date, on='customer_id', how='left')

# Rename columns
filtered_customer_table.rename(columns={
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

# Apply filters to the customer table
filtered_customer_table = filtered_customer_table[
    (filtered_customer_table['Name'].str.contains(name_filter, case=False, na=False)) &
    (filtered_customer_table['Email'].str.contains(email_filter, case=False, na=False))
]

# Format dollar columns
filtered_customer_table['Total Spend'] = filtered_customer_table['Total Spend'].apply(lambda x: f"${x:,.2f}")
filtered_customer_table['Total Refunds'] = filtered_customer_table['Total Refunds'].apply(lambda x: f"${x:,.2f}")
filtered_customer_table['Total Discounts'] = filtered_customer_table['Total Discounts'].apply(lambda x: f"${x:,.2f}")

# Format date columns
filtered_customer_table['Last Order Date'] = pd.to_datetime(filtered_customer_table['Last Order Date']).dt.strftime('%Y-%m-%d')
filtered_customer_table['Created Date'] = pd.to_datetime(filtered_customer_table['Created Date']).dt.strftime('%Y-%m-%d')

# Display the customer table
st.dataframe(filtered_customer_table)
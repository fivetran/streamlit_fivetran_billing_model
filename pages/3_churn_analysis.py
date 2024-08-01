import streamlit as st
import plost
import pandas as pd
import numpy as np
from datetime import datetime
from functions.setup_page import page_creation
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

## Apply standard page settings.
st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title('Churn Analysis')

## Define data and filters. The resulting data variable includes the data with all filters applied.
data = page_creation()

st.divider()

# Data processing
data['created_at'] = pd.to_datetime(data['created_at'])
data['customer_created_at'] = pd.to_datetime(data['customer_created_at'])
data['subscription_period_started_at'] = pd.to_datetime(data['subscription_period_started_at'])
data['subscription_period_ended_at'] = pd.to_datetime(data['subscription_period_ended_at'])

# Calculate MRR (Monthly Recurring Revenue)
data['mrr'] = data['total_amount'] / ((data['subscription_period_ended_at'] - data['subscription_period_started_at']).dt.days / 30)


# QoQ and Yoy calculations

data['month'] = data['created_at'].dt.to_period('M').dt.to_timestamp()
data['quarter'] = data['created_at'].dt.to_period('Q').dt.to_timestamp()

current_year = data['created_at'].dt.year.max()
previous_year = current_year - 1
current_quarter = data['quarter'].max()
previous_quarter = data[data['quarter'] < current_quarter]['quarter'].max()
current_month = data['month'].max()
previous_month = data[data['month'] < current_month]['month'].max()

# Helper function to calculate percentage change
def percentage_change(current, previous):
    return ((current - previous) / previous * 100) if previous != 0 else float('inf')

# New MRR calculations
new_mrr = data[(data['created_at'] >= current_month) & (data['billing_type'] == 'recurring')]['mrr'].sum()
new_mrr_yoy = percentage_change(
    data[(data['created_at'].dt.year == current_year) & (data['billing_type'] == 'recurring')]['mrr'].sum(),
    data[(data['created_at'].dt.year == previous_year) & (data['billing_type'] == 'recurring')]['mrr'].sum()
)
new_mrr_qoq = percentage_change(
    data[(data['quarter'] == current_quarter) & (data['billing_type'] == 'recurring')]['mrr'].sum(),
    data[(data['quarter'] == previous_quarter) & (data['billing_type'] == 'recurring')]['mrr'].sum()
)

# Churned MRR calculations
churned_mrr = data[(data['subscription_status'] == 'inactive') & (data['subscription_period_ended_at'] >= current_month)]['mrr'].sum()
churned_mrr_yoy = percentage_change(
    data[(data['subscription_status'] == 'inactive') & (data['subscription_period_ended_at'].dt.year == current_year)]['mrr'].sum(),
    data[(data['subscription_status'] == 'inactive') & (data['subscription_period_ended_at'].dt.year == previous_year)]['mrr'].sum()
)
churned_mrr_qoq = percentage_change(
    data[(data['subscription_status'] == 'inactive') & (data['subscription_period_ended_at'].dt.to_period('Q') == current_quarter.to_period('Q'))]['mrr'].sum(),
    data[(data['subscription_status'] == 'inactive') & (data['subscription_period_ended_at'].dt.to_period('Q') == previous_quarter.to_period('Q'))]['mrr'].sum()
)

# Retention rate calculations
def calculate_retention_rate(period_start, period_end):
    customers_at_start = data[data['customer_created_at'] <= period_start]['customer_id'].nunique()
    customers_retained = data[(data['customer_created_at'] <= period_start) & (data['subscription_status'] == 'active') & (data['created_at'] <= period_end)]['customer_id'].nunique()
    return (customers_retained / customers_at_start) * 100 if customers_at_start > 0 else 0

retention_30_day = calculate_retention_rate(current_month - pd.DateOffset(days=30), current_month)
retention_30_day_yoy = percentage_change(
    calculate_retention_rate(current_month - pd.DateOffset(days=30), current_month),
    calculate_retention_rate(current_month - pd.DateOffset(years=1, days=30), current_month - pd.DateOffset(years=1))
)
retention_30_day_qoq = percentage_change(
    calculate_retention_rate(current_month - pd.DateOffset(days=30), current_month),
    calculate_retention_rate(current_month - pd.DateOffset(months=3, days=30), current_month - pd.DateOffset(months=3))
)

retention_90_day = calculate_retention_rate(current_month - pd.DateOffset(days=90), current_month)
retention_90_day_yoy = percentage_change(
    calculate_retention_rate(current_month - pd.DateOffset(days=90), current_month),
    calculate_retention_rate(current_month - pd.DateOffset(years=1, days=90), current_month - pd.DateOffset(years=1))
)
retention_90_day_qoq = percentage_change(
    calculate_retention_rate(current_month - pd.DateOffset(days=90), current_month),
    calculate_retention_rate(current_month - pd.DateOffset(months=3, days=90), current_month - pd.DateOffset(months=3))
)

retention_1_year = calculate_retention_rate(current_month - pd.DateOffset(years=1), current_month)
retention_1_year_yoy = percentage_change(
    calculate_retention_rate(current_month - pd.DateOffset(years=1), current_month),
    calculate_retention_rate(current_month - pd.DateOffset(years=2), current_month - pd.DateOffset(years=1))
)
retention_1_year_qoq = percentage_change(
    calculate_retention_rate(current_month - pd.DateOffset(years=1), current_month),
    calculate_retention_rate(current_month - pd.DateOffset(years=1, months=3), current_month - pd.DateOffset(months=3))
)

# KPI Metrics
with st.container():
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(label="**New MRR**", value=f"${new_mrr:,.0f}",
                  delta=f"{new_mrr_yoy:.1f}% YoY | {new_mrr_qoq:.1f}% QoQ")

    with col2:
        st.metric(label="**Churned MRR**", value=f"${churned_mrr:,.0f}",
                  delta=f"{churned_mrr_yoy:.1f}% YoY | {churned_mrr_qoq:.1f}% QoQ")

    with col3:
        st.metric(label="**30 Day Retention Rate**", value=f"{retention_30_day:.2f}%",
                  delta=f"{retention_30_day_yoy:.1f}% YoY | {retention_30_day_qoq:.1f}% QoQ")

    with col4:
        st.metric(label="**90 Day Retention Rate**", value=f"{retention_90_day:.2f}%",
                  delta=f"{retention_90_day_yoy:.1f}% YoY | {retention_90_day_qoq:.1f}% QoQ")

    with col5:
        st.metric(label="**1 Year Retention Rate**", value=f"{retention_1_year:.2f}%",
                  delta=f"{retention_1_year_yoy:.1f}% YoY | {retention_1_year_qoq:.1f}% QoQ")
# Combined Churn Rate Chart
st.markdown("**Churn Rate Over Time**")

# Filter data to include only records with a subscription_id
subscribed_data = data[data['subscription_id'].notna()]

# Calculate overall churn rate
churn_rate = subscribed_data.groupby(subscribed_data['created_at'].dt.to_period('M')).apply(
    lambda x: x[x['subscription_status'] == 'inactive']['customer_id'].nunique() / x['customer_id'].nunique()
).reset_index()
churn_rate.columns = ['Month', 'Overall Churn Rate']
churn_rate['Month'] = churn_rate['Month'].dt.to_timestamp()

# Calculate churn rate by plan
churn_rate_by_plan = subscribed_data.groupby(['subscription_plan', subscribed_data['created_at'].dt.to_period('M')]).apply(
    lambda x: x[x['subscription_status'] == 'inactive']['customer_id'].nunique() / x['customer_id'].nunique()
).reset_index()
churn_rate_by_plan.columns = ['Subscription Plan', 'Month', 'Churn Rate']
churn_rate_by_plan['Month'] = churn_rate_by_plan['Month'].dt.to_timestamp()

fig = go.Figure()

# Add overall churn rate with values
fig.add_trace(go.Scatter(
    x=churn_rate['Month'], 
    y=churn_rate['Overall Churn Rate'],
    mode='lines+markers+text',
    name='Overall Churn Rate',
    line=dict(width=6, color='black'),
    text=[f'{rate:.1%}' for rate in churn_rate['Overall Churn Rate']],
    textposition='top center'
))

# Add churn rate by plan with values
for plan in churn_rate_by_plan['Subscription Plan'].unique():
    plan_data = churn_rate_by_plan[churn_rate_by_plan['Subscription Plan'] == plan]
    fig.add_trace(go.Scatter(
        x=plan_data['Month'], 
        y=plan_data['Churn Rate'],
        mode='lines+markers+text',
        name=f'{plan} Churn Rate',
        text=[f'{rate:.1%}' for rate in plan_data['Churn Rate']],
        textposition='top center'
    ))

fig.update_layout(
    xaxis_title='Month',
    yaxis_title='Churn Rate',
    yaxis=dict(
            tickformat='.0%',
            range=[0, 1],  # This sets the y-axis range from 0 to 1 (0% to 100%)
            dtick=0.1  # This sets tick marks at every 10%
        ),
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
)

# Adjust layout to prevent overlap
fig.update_traces(textfont_size=10)
fig.update_layout(height=600)

st.plotly_chart(fig)

## New MRR by Product

# Filter for recurring billing type and group by month and product type
new_mrr_by_type = data[data['billing_type'] == 'recurring'].groupby([data['created_at'].dt.to_period('M'), 'product_type'])['mrr'].sum().reset_index()
new_mrr_by_type['created_at'] = new_mrr_by_type['created_at'].dt.to_timestamp()

# Create stacked bar chart
fig = px.bar(new_mrr_by_type, x='created_at', y='mrr', color='product_type', 
             title='New MRR by Product', labels={'created_at': 'Month', 'mrr': 'MRR', 'product_type': 'Product Type'}, 
             text_auto=True)

# Update layout with consistent font size
fig.update_layout(
    title_font_size=20,
    xaxis_title_font_size=14,
    yaxis_title_font_size=14,
    legend_title_font_size=14,
    legend_font_size=12,
    xaxis_tickfont_size=12,
    yaxis_tickfont_size=12,
    yaxis_title='MRR',
    yaxis_tickprefix='$',
    yaxis_tickformat=',.0f'
)

# Display chart
st.plotly_chart(fig)


## Cohort Analysis Chart
## Cohort Analysis Chart
st.markdown("**Cohort Analysis - Subscription Churn Count**")

# Filter data to include only records with a subscription_id and within the date range
start_date, end_date = st.session_state.get('date_range', (data['created_at'].min(), data['created_at'].max()))
subscribed_data = data[(data['subscription_id'].notna()) & 
                       (data['subscription_period_started_at'] >= start_date) & 
                       (data['subscription_period_started_at'] <= end_date)]

# Debug: Print the shape of subscribed_data
st.write(f"Number of subscribed records: {subscribed_data.shape[0]}")

# Prepare cohort data
cohort = subscribed_data.groupby('subscription_id').agg({
    'customer_created_at': 'first',
    'subscription_period_started_at': 'first',
    'subscription_status': 'last'
}).reset_index()

# Calculate months since customer creation
cohort['months_since_customer_creation'] = ((cohort['subscription_period_started_at'].dt.to_period('M') - 
                                             cohort['customer_created_at'].dt.to_period('M'))).apply(lambda x: max(0, x.n))

# Count churns
churn_matrix = cohort[cohort['subscription_status'] == 'inactive'].groupby([
    cohort['subscription_period_started_at'].dt.to_period('M'), 
    'months_since_customer_creation'
]).size().unstack(fill_value=0)

# Sort the columns and index
churn_matrix = churn_matrix.sort_index()
churn_matrix = churn_matrix.reindex(sorted(churn_matrix.columns), axis=1)

# Rename the index for clarity
churn_matrix.index = churn_matrix.index.strftime('%Y-%m')
churn_matrix.index.name = 'Subscription Start Month'

# Rename columns for clarity
churn_matrix.columns.name = 'Months Since Customer Creation'

# Display the churn matrix as a table
st.write("Churn Matrix:")
st.dataframe(churn_matrix.style.highlight_max(axis=None))

# Optionally, provide a CSV download link
csv = churn_matrix.to_csv().encode('utf-8')
st.download_button(
    label="Download Churn Matrix as CSV",
    data=csv,
    file_name="churn_matrix.csv",
    mime="text/csv",
)
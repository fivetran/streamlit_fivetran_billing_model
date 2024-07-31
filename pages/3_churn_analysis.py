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

# KPI Metrics
current_date = datetime.now()
last_month = current_date - pd.DateOffset(months=1)
last_3_months = current_date - pd.DateOffset(months=3)
last_year = current_date - pd.DateOffset(years=1)

new_mrr = data[(data['created_at'] >= last_month) & (data['billing_type'] == 'recurring')]['mrr'].sum()
churned_mrr = data[(data['subscription_status'] == 'inactive') & (data['subscription_period_ended_at'] >= last_month)]['mrr'].sum()

def calculate_retention_rate(period_start):
    customers_at_start = data[data['customer_created_at'] <= period_start]['customer_id'].nunique()
    customers_retained = data[(data['customer_created_at'] <= period_start) & (data['subscription_status'] == 'active')]['customer_id'].nunique()
    return (customers_retained / customers_at_start) * 100 if customers_at_start > 0 else 0

retention_30_day = calculate_retention_rate(last_month)
retention_90_day = calculate_retention_rate(last_3_months)
retention_1_year = calculate_retention_rate(last_year)

with st.container():
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(label="**New MRR**", value=f"${new_mrr:,.0f}")

    with col2:
        st.metric(label="**Churned MRR**", value=f"${churned_mrr:,.0f}")

    with col3:
        st.metric(label="**30 Day Retention Rate**", value=f"{retention_30_day:.2f}%")

    with col4:
        st.metric(label="**90 Day Retention Rate**", value=f"{retention_90_day:.2f}%")

    with col5:
        st.metric(label="**1 Year Retention Rate**", value=f"{retention_1_year:.2f}%")

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
st.markdown("**New MRR by Product**")
new_mrr_by_type = data[data['billing_type'] == 'recurring'].groupby([data['created_at'].dt.to_period('M'), 'product_type'])['mrr'].sum().reset_index()
new_mrr_by_type['created_at'] = new_mrr_by_type['created_at'].dt.to_timestamp()
fig = px.area(new_mrr_by_type, x='created_at', y='mrr', color='product_type')
fig.update_layout(yaxis_title='MRR', yaxis_tickprefix='$', yaxis_tickformat=',.0f')
st.plotly_chart(fig)

## Cohort Analysis Chart
st.markdown("**Cohort Analysis**")

# Filter data to include only records with a subscription_id
subscribed_data = data[data['subscription_id'].notna()]

# Debug: Print the shape of subscribed_data
st.write(f"Number of subscribed records: {subscribed_data.shape[0]}")

# Prepare cohort data
cohort = subscribed_data.groupby(['customer_id', pd.to_datetime(subscribed_data['customer_created_at']).dt.to_period('M')]).agg({
    'created_at': 'max',
    'subscription_status': 'last',
    'subscription_id': 'first'  # To ensure we're counting unique subscriptions
}).reset_index()

cohort['months_since_creation'] = ((cohort['created_at'].dt.to_period('M') - cohort['customer_created_at'])).apply(lambda x: x.n)

# Debug: Print the shape of cohort data
st.write(f"Shape of cohort data: {cohort.shape}")

# Calculate churn rate for each cohort and month
def calculate_churn_rate(group):
    total_subscriptions = group['subscription_id'].nunique()
    churned_subscriptions = group[group['subscription_status'] == 'inactive']['subscription_id'].nunique()
    return churned_subscriptions / total_subscriptions if total_subscriptions > 0 else 0

cohort_matrix = cohort.groupby(['customer_created_at', 'months_since_creation']).apply(calculate_churn_rate).unstack()

# Debug: Print the shape of cohort_matrix
st.write(f"Shape of cohort matrix: {cohort_matrix.shape}")

# Fill NaN values with 0
cohort_matrix = cohort_matrix.fillna(0)

# Debug: Print a sample of the cohort matrix
st.write("Sample of cohort matrix:")
st.write(cohort_matrix.head())

try:
    # Create the heatmap
    fig = px.imshow(cohort_matrix, 
                    labels=dict(x="Months Since Creation", y="Cohort", color="Churn Rate"),
                    x=cohort_matrix.columns,
                    y=cohort_matrix.index.strftime('%Y-%m'),
                    color_continuous_scale="RdYlGn_r",  # Red for high churn, Green for low churn
                    title="Cohort Analysis - Subscription Churn Rate")

    # Update layout
    fig.update_layout(
        xaxis_title="Months Since Creation",
        yaxis_title="Cohort",
        coloraxis_colorbar=dict(title="Churn Rate", tickformat=".0%")
    )

    # Add text annotations
    for y in range(len(cohort_matrix.index)):
        for x in range(len(cohort_matrix.columns)):
            value = cohort_matrix.iloc[y, x]
            if not np.isnan(value):
                fig.add_annotation(
                    x=x,
                    y=y,
                    text=f"{value:.1%}",
                    showarrow=False,
                    font=dict(color="black" if value < 0.5 else "white")
                )

    st.plotly_chart(fig)

except Exception as e:
    st.error(f"An error occurred while creating the cohort analysis chart: {str(e)}")
    
    # Fallback: Display the cohort matrix as a table
    st.write("Cohort Matrix (as table):")
    st.dataframe(cohort_matrix)


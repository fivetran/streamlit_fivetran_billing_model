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

# YoY calculations
data['month'] = data['created_at'].dt.to_period('M').dt.to_timestamp()
data['quarter'] = data['created_at'].dt.to_period('Q').dt.to_timestamp()

current_year = data['created_at'].dt.year.max()
previous_year = current_year - 1
current_month = data['month'].max()

def percentage_change(current, previous):
    if previous == 0:
        return "New" if current > 0 else 0
    return ((current - previous) / previous) * 100

# Helper function to format the YoY change
def format_yoy_change(change):
    if change == "New":
        return "New (prev. year was 0)"
    else:
        return f"{change:.1f}% YoY"
# MRR calculation
current_mrr = data[data['subscription_status'] == 'active']['mrr'].sum()
current_mrr_yoy = percentage_change(
    data[(data['created_at'].dt.year == current_year) & (data['subscription_status'] == 'active')]['mrr'].sum(),
    data[(data['created_at'].dt.year == previous_year) & (data['subscription_status'] == 'active')]['mrr'].sum()
)

# New MRR calculations
new_mrr = data[(data['created_at'] >= current_month) & (data['billing_type'] == 'recurring')]['mrr'].sum()
new_mrr_yoy = percentage_change(
    data[(data['created_at'].dt.year == current_year) & (data['billing_type'] == 'recurring')]['mrr'].sum(),
    data[(data['created_at'].dt.year == previous_year) & (data['billing_type'] == 'recurring')]['mrr'].sum()
)

# Churned MRR calculations
churned_mrr = data[(data['subscription_status'] == 'inactive') & (data['subscription_period_ended_at'] >= current_month)]['mrr'].sum()
churned_mrr_yoy = percentage_change(
    data[(data['subscription_status'] == 'inactive') & (data['subscription_period_ended_at'].dt.year == current_year)]['mrr'].sum(),
    data[(data['subscription_status'] == 'inactive') & (data['subscription_period_ended_at'].dt.year == previous_year)]['mrr'].sum()
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

retention_90_day = calculate_retention_rate(current_month - pd.DateOffset(days=90), current_month)
retention_90_day_yoy = percentage_change(
    calculate_retention_rate(current_month - pd.DateOffset(days=90), current_month),
    calculate_retention_rate(current_month - pd.DateOffset(years=1, days=90), current_month - pd.DateOffset(years=1))
)

retention_1_year = calculate_retention_rate(current_month - pd.DateOffset(years=1), current_month)
retention_1_year_yoy = percentage_change(
    calculate_retention_rate(current_month - pd.DateOffset(years=1), current_month),
    calculate_retention_rate(current_month - pd.DateOffset(years=2), current_month - pd.DateOffset(years=1))
)

# KPI Metrics
with st.container():
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric(label="**MRR**", value=f"${current_mrr:,.0f}",
                  delta=format_yoy_change(current_mrr_yoy))

    with col2:
        st.metric(label="**New MRR**", value=f"${new_mrr:,.0f}",
                  delta=format_yoy_change(new_mrr_yoy))

    with col3:
        st.metric(
            label="**Churned MRR**",
            value=f"${churned_mrr:,.0f}",
            delta=format_yoy_change(churned_mrr_yoy),
            delta_color="inverse"
        )
        if isinstance(churned_mrr_yoy, str) and churned_mrr_yoy == "New":
            st.caption("⚠️ New churn (prev. year was 0)")
        elif churned_mrr_yoy > 0:
            st.caption("⚠️ Increase in churn")
        elif churned_mrr_yoy < 0:
            st.caption("✅ Decrease in churn")
        else:
            st.caption("No change in churn")

    with col4:
        st.metric(label="**30 Day Retention Rate**", value=f"{retention_30_day:.2f}%",
                  delta=format_yoy_change(retention_30_day_yoy))

    with col5:
        st.metric(label="**90 Day Retention Rate**", value=f"{retention_90_day:.2f}%",
                  delta=format_yoy_change(retention_90_day_yoy))

    with col6:
        st.metric(label="**1 Year Retention Rate**", value=f"{retention_1_year:.2f}%",
                  delta=format_yoy_change(retention_1_year_yoy))

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


## New MRR by Product and Overall New MRR

st.markdown("**New MRR by Product and Overall New MRR**")

# Filter for recurring billing type and group by month and product type
new_mrr_by_type = data[data['billing_type'] == 'recurring'].groupby([data['created_at'].dt.to_period('M'), 'product_type'])['mrr'].sum().reset_index()
new_mrr_by_type['created_at'] = new_mrr_by_type['created_at'].dt.to_timestamp()

# Calculate overall new MRR by month
overall_new_mrr = new_mrr_by_type.groupby('created_at')['mrr'].sum().reset_index()

# Create figure
fig = go.Figure()

# Add stacked bar chart for new MRR by product
for product in new_mrr_by_type['product_type'].unique():
    product_data = new_mrr_by_type[new_mrr_by_type['product_type'] == product]
    fig.add_trace(
        go.Bar(
            x=product_data['created_at'], 
            y=product_data['mrr'], 
            name=product,
            text=product_data['mrr'].apply(lambda x: f'${x:,.0f}'),
            textposition='inside'
        )
    )

# Add line chart for overall new MRR
fig.add_trace(
    go.Scatter(
        x=overall_new_mrr['created_at'], 
        y=overall_new_mrr['mrr'], 
        name='Overall New MRR',
        line=dict(color='black', width=3),
        mode='lines+markers',
        text=overall_new_mrr['mrr'].apply(lambda x: f'${x:,.0f}'),
        textposition='top center'
    )
)

# Update layout
fig.update_layout(
    barmode='stack',
    xaxis_title='Month',
    yaxis_title='MRR',
    legend_title='Product Type',
    hovermode='x unified',
    xaxis_tickfont_size=12,
    yaxis_tickfont_size=12,
    legend_font_size=12,
    yaxis=dict(tickprefix='$', tickformat=',.0f')
)

# Display chart
st.plotly_chart(fig, use_container_width=True)




## Cohort Analysis Chart
st.markdown("**Cohort Analysis - Subscription Churn Rate**")

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

# Calculate total subscriptions
total_subs = cohort.groupby([
    cohort['subscription_period_started_at'].dt.to_period('M'), 
    'months_since_customer_creation'
]).size().unstack(fill_value=0)

# Calculate churned subscriptions
churned_subs = cohort[cohort['subscription_status'] == 'inactive'].groupby([
    cohort['subscription_period_started_at'].dt.to_period('M'), 
    'months_since_customer_creation'
]).size().unstack(fill_value=0)

# Ensure both dataframes have the same index and columns
common_index = total_subs.index.intersection(churned_subs.index)
common_columns = total_subs.columns.intersection(churned_subs.columns)

total_subs = total_subs.loc[common_index, common_columns]
churned_subs = churned_subs.loc[common_index, common_columns]


# Calculate churn rate
churn_rate = churned_subs / total_subs

# Replace NaN and inf with 0
churn_rate = churn_rate.fillna(0).replace([np.inf, -np.inf], 0)

# Sort the columns and index
churn_rate = churn_rate.sort_index()
churn_rate = churn_rate.reindex(sorted(churn_rate.columns), axis=1)

# Rename the index for clarity
churn_rate.index = churn_rate.index.strftime('%Y-%m')
churn_rate.index.name = 'Subscription Start Month'

# Remove any rows that are all zeros
churn_rate_cleaned = churn_rate.loc[(churn_rate != 0).any(axis=1)]

# Add "Months Since Customer Creation" as column header
churn_rate_cleaned.columns.name = "Months Since Customer Creation"

# Function to format cell content
def format_cell(val, churned, total):
    return f"{val:.0%}\n({churned}/{total})"

# Create a DataFrame with formatted cell contents
formatted_matrix = pd.DataFrame(index=churn_rate_cleaned.index, columns=churn_rate_cleaned.columns)
for idx in churn_rate_cleaned.index:
    for col in churn_rate_cleaned.columns:
        formatted_matrix.loc[idx, col] = format_cell(
            churn_rate_cleaned.loc[idx, col],
            churned_subs.loc[idx, col],
            total_subs.loc[idx, col]
        )

# Function to apply color gradient
def color_gradient(val):
    if isinstance(val, str):
        val = float(val.split('%')[0]) / 100
    color = "#306BEA"
    return f'background-color: rgba{tuple(int(color[i:i+2], 16) for i in (1, 3, 5)) + (val,)}'

# Apply formatting and styling
styled_churn_matrix = formatted_matrix.style.applymap(color_gradient)

# Increase cell size and center text
styled_churn_matrix = styled_churn_matrix.set_properties(**{
    'text-align': 'center',
    'height': '120px',
    'min-width': '150px',
    'font-size': '20px',
    'white-space': 'pre-wrap'
})

# Add styling for the index and column headers
styled_churn_matrix = styled_churn_matrix.set_table_styles([
    {'selector': 'th.col_heading', 'props': [('font-size', '16px'), ('text-align', 'center'), ('padding', '10px')]},
    {'selector': 'th.row_heading', 'props': [('font-size', '16px'), ('text-align', 'right'), ('padding', '10px')]},
    {'selector': 'th.col_heading.level0', 'props': [('font-size', '18px'), ('text-align', 'center'), ('padding', '15px')]},
])

# Display the churn matrix as a table
st.write("Churn Rate Matrix:")
st.dataframe(styled_churn_matrix, use_container_width=True, height=500)

# Optionally, provide a CSV download link for the full data
csv = churn_rate.to_csv().encode('utf-8')
st.download_button(
    label="Download Full Churn Rate Matrix as CSV",
    data=csv,
    file_name="full_churn_rate_matrix.csv",
    mime="text/csv",
)
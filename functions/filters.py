import streamlit as st
from datetime import datetime, timedelta
from functions.query import query_results
import pandas as pd

def date_filter():
    data = query_results()
    min_created_at = data['created_at'].min()
    max_created_at = data['created_at'].max()
    default_start_date = max_created_at - timedelta(days=365)

    if default_start_date < min_created_at:
        default_start_date = min_created_at
    if max_created_at > max_created_at:
        max_created_at = max_created_at

    if 'start_date' not in st.session_state:
        st.session_state.start_date = default_start_date
    if 'end_date' not in st.session_state:
        st.session_state.end_date = max_created_at

    start_date, end_date = st.date_input(
        "(Required) Select your date range",
        value=(st.session_state.start_date, st.session_state.end_date),
        min_value=min_created_at,
        max_value=max_created_at,
        format="MM/DD/YYYY"
    )

    st.session_state.start_date, st.session_state.end_date = start_date, end_date

    if not start_date:
        st.warning("Please select a start date.")
    elif not end_date:
        st.warning("Please select an end date.")
    elif start_date > end_date:
        st.warning("The start date cannot be after the end date. Please select a valid date range.")

    return data, (start_date, end_date)

def filter_data(start, end, data_ref):
    data_date_filtered = data_ref.query("`created_at` >= @start and `created_at` <= @end")

    return data_date_filtered

def create_filter(column_name, filter_type='selectbox', options=None, selected_options=None, min_value=None, max_value=None):
    if filter_type == 'multiselect':
        valid_selected_options = [opt for opt in selected_options if opt in options] if selected_options else []
        return st.multiselect(column_name, options, default=valid_selected_options)
    elif filter_type == 'date':
        return st.date_input(column_name, value=selected_options)
    return None

def calculate_tenure_range(tenure_in_months):
    ranges = [
        (0, 6, '0-6 months'),
        (7, 12, '7-12 months'),
        (13, 24, '1-2 years'),
        (25, 36, '2-3 years'),
        (37, 48, '3-4 years'),
        (49, 60, '4-5 years')
    ]
    
    for start, end, label in ranges:
        if start <= tenure_in_months <= end:
            return label
    
    return '5+ years'

def apply_filters(data, filter_values, columns):
    for display_name, column_name, filter_type in columns:
        if display_name in filter_values:
            selected_options = filter_values[display_name]
            if selected_options:
                data = data[data[column_name].isin(selected_options)]

    return data

def setting_filters(data):
    with st.container():
        date_filtered_data = data
        col1, col2, col3, col4 = st.columns(4)
        row1 = [col1, col2, col3, col4]
        col6, col7, col8, col9 = st.columns(4)
        row2 = [col6, col7, col8, col9]

        filter_values = {}

        current_date = pd.Timestamp(datetime.now())
        date_filtered_data['customer_created_date'] = pd.to_datetime(date_filtered_data['customer_created_at'])
        date_filtered_data['customer_tenure_months'] = ((current_date - date_filtered_data['customer_created_date']) / pd.Timedelta(days=30)).astype(int)
        date_filtered_data['customer_tenure_range'] = date_filtered_data['customer_tenure_months'].apply(calculate_tenure_range)

        def get_distinct_values(data, column_name):
            return sorted(set(data[column_name].dropna().astype(str)))

        if 'filter_values' not in st.session_state:
            st.session_state.filter_values = {}

        def update_filter(column_name, filter_type, options):
            if column_name not in st.session_state.filter_values:
                st.session_state.filter_values[column_name] = [] if filter_type == 'multiselect' else None
            selected_options = create_filter(column_name, filter_type, options, selected_options=st.session_state.filter_values[column_name])
            st.session_state.filter_values[column_name] = selected_options
            return selected_options

        columns = [
            ("Subscription Plan", 'subscription_plan', 'multiselect'),
            ("Customer Segment", 'customer_name', 'multiselect'),
            ("Purchase Location", 'customer_city', 'multiselect'),
            ("Payment Method", 'payment_method', 'multiselect'),
            ("Billing Source", 'billing_type', 'multiselect'),
            ("Customer Tenure", 'customer_tenure_range', 'multiselect'),
            ("Product Name", 'product_name', 'multiselect'),
            ("Subscription Status", 'subscription_status', 'multiselect')
        ]

        for i, (column_name, column_field, filter_type) in enumerate(columns):
            if i < 4:
                col = row1[i % 4]
            else:
                col = row2[(i - 4) % 4]
            with col:
                distinct_values = get_distinct_values(date_filtered_data, column_field)
                selected_options = update_filter(column_name, filter_type, distinct_values)
                filter_values[column_name] = selected_options
                date_filtered_data = apply_filters(date_filtered_data, filter_values, columns)

        filtered_data = date_filtered_data

    return filtered_data
import streamlit as st
import plost
import pandas as pd
import numpy as np
from datetime import datetime
from functions.filters import date_filter, filter_data, setting_filters
from functions.query import query_results

def page_creation():
    billing_data, d = date_filter()

    ## Only generate the tiles if date range is populated
    if d is not None and len(d) == 2:
        start_date, end_date = d
        if start_date is not None:
            data_date_filtered = filter_data(start=start_date, end=end_date, data_ref=billing_data)
            fully_filtered_data = setting_filters(data=data_date_filtered)

    return fully_filtered_data
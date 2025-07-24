"""
Frontend Micro-Architecture: Dashboard Tab

This module implements the UI for the main dashboard, providing an at-a-glance
overview of the user's financial status.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from core.processors.dashboard_processor import DashboardProcessor
from core.database.db_interface import DatabaseInterface

def render():
    """Renders the Dashboard tab with intelligent caching."""
    db_interface = DatabaseInterface()

    # --- Cold Start Check ---
    if db_interface.get_transactions_count() == 0:
        st.info("Welcome! Upload a statement to see your financial dashboard.")
        return

    # --- Intelligent Caching Logic ---
    latest_timestamp = db_interface.get_latest_transaction_timestamp()
    if ('dashboard_data' not in st.session_state or 
        st.session_state.get('last_transaction_timestamp') != latest_timestamp):
        
        with st.spinner("Analyzing your latest financial data..."):
            transactions_df = db_interface.get_transactions_table()
            processor = DashboardProcessor()
            st.session_state.dashboard_data = processor.process_dashboard_data(transactions_df)
            st.session_state.last_transaction_timestamp = latest_timestamp
    
    data = st.session_state.dashboard_data
    display_month = data.get("display_month", {})

    # --- Header and Info Alert ---
    st.header(f"Dashboard - {display_month.get('month_name', '' )}")
    if not display_month.get('is_current', True):
        st.info(f"Displaying data for {display_month.get('month_name', '')}, as it is the most recent month with transactions.")

    # --- Render Dashboard Components ---
    kpis = data.get("kpis", {})
    col1, col2, col3 = st.columns(3)
    col1.metric(f"Total Spend in {display_month.get('month_name', '')}", f"₹{kpis.get('total_spend', 0):,.2f}")
    col2.metric("Top Spending Category", str(kpis.get('top_category', 'N/A')))
    col3.metric(f"Largest Transaction in {display_month.get('month_name', '')}", f"₹{kpis.get('largest_transaction', 0):,.2f}")

    st.divider()

    col1, col2 = st.columns([2, 3])

    with col1:
        st.subheader("Expenses by Category")
        category_data = data.get("category_chart_data")
        if not category_data.empty:
            fig = px.pie(category_data, names='category', values='amount', hole=0.3)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write(f"No spending data for {display_month.get('month_name', '')}.")

    with col2:
        st.subheader("Spending Over Time")
        spending_data = data.get("spending_over_time_data")
        if not spending_data.empty:
            st.bar_chart(spending_data, x='month', y='amount', use_container_width=True)
        else:
            st.write("No spending data available.")

    st.divider()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("AI Insights")
        ai_insights = data.get("ai_insights", {})
        st.info(ai_insights.get("overview", ""))
        for insight in ai_insights.get("insights", []):
            st.markdown(f"- {insight}")

    with col2:
        st.subheader("Recent Transactions")
        recent_transactions = data.get("recent_transactions")
        st.dataframe(recent_transactions, use_container_width=True, hide_index=True)

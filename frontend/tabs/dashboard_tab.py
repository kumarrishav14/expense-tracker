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
    """Renders the Dashboard tab."""
    st.header("Dashboard")

    db_interface = DatabaseInterface()
    transactions_df = db_interface.get_transactions_table()

    if transactions_df.empty:
        st.info("Welcome! Upload a statement to see your financial dashboard.")
        return

    # --- Data Processing ---
    if 'dashboard_data' not in st.session_state or st.button("Refresh Data"):
        with st.spinner("Analyzing your financial data..."):
            processor = DashboardProcessor()
            st.session_state.dashboard_data = processor.process_dashboard_data(transactions_df)
    
    data = st.session_state.dashboard_data

    # --- Render Dashboard Components ---
    kpis = data.get("kpis", {})
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Spend (Current Month)", f"₹{kpis.get('total_spend', 0):,.2f}")
    col2.metric("Top Spending Category", str(kpis.get('top_category', 'N/A')))
    col3.metric("Largest Transaction (Current Month)", f"₹{kpis.get('largest_transaction', 0):,.2f}")

    st.divider()

    col1, col2 = st.columns([2, 3])

    with col1:
        st.subheader("Expenses by Category")
        category_data = data.get("category_chart_data")
        if not category_data.empty:
            fig = px.pie(category_data, names='category', values='amount', hole=0.3)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No spending data for this month.")

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

"""
Main Streamlit Application

This file serves as the entry point for the Streamlit frontend.
It sets up the main tabbed navigation and renders the content for each tab
by calling the respective modules.
"""
import sys
import os
import streamlit as st
from streamlit_option_menu import option_menu

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.tabs import dashboard_tab, statement_input_tab, settings_tab
from core.database.seeder import initialize_database

def main():
    """Main function to run the Streamlit application."""
    # Initialize the database with default categories if it's empty
    initialize_database()

    st.set_page_config(layout="wide")

    st.title("Expenses Tracking Tool")

    # --- State-aware Navigation using streamlit-option-menu ---
    selected_tab = option_menu(
        menu_title=None,  # required
        options=["Dashboard", "Statement Input", "Settings"],
        icons=['house', 'cloud-upload', 'gear'],  # optional
        key="main_menu", # Use key for built-in state management
        orientation="horizontal",
    )

    # --- Render Content based on Active Tab ---
    if selected_tab == "Dashboard":
        dashboard_tab.render()
    elif selected_tab == "Statement Input":
        statement_input_tab.render()
    elif selected_tab == "Settings":
        settings_tab.render()

if __name__ == "__main__":
    main()

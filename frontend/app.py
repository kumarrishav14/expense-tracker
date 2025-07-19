"""
Main Streamlit Application

This file serves as the entry point for the Streamlit frontend.
It sets up the main tabbed navigation and renders the content for each tab
by calling the respective modules.
"""
import sys
import os
import streamlit as st

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.tabs import statement_input_tab, settings_tab
from core.database.seeder import initialize_database

def main():
    """Main function to run the Streamlit application."""
    # Initialize the database with default categories if it's empty
    initialize_database()

    st.set_page_config(layout="wide")

    st.title("Expenses Tracking Tool")

    # --- Tab Navigation ---
    tab1, tab2 = st.tabs(["Statement Input", "Settings"])

    with tab1:
        statement_input_tab.render()

    with tab2:
        settings_tab.render()

if __name__ == "__main__":
    main()

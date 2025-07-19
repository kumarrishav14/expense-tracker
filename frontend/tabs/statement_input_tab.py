"""
Frontend Micro-Architecture: Statement Input Tab

This module implements the UI for the Statement Input tab, following the
streamlined "Process & Review -> Save" workflow.
"""

import streamlit as st
import pandas as pd
import io

from core.parsers.csv_parser import parse_csv_file
from core.parsers.pdf_parser import is_pdf_encrypted, parse_pdf
from core.processors import AIDataProcessor
from core.database.db_interface import DatabaseInterface

def render():
    """Renders the Statement Input tab."""
    st.header("Upload & Process New Statement")

    # --- State Initialization ---
    if 'processed_df' not in st.session_state:
        st.session_state.processed_df = None
    if 'upload_error' not in st.session_state:
        st.session_state.upload_error = None

    # --- File Uploader ---
    uploaded_file = st.file_uploader(
        "Choose a statement file (CSV or PDF)", 
        type=["csv", "pdf"]
    )

    password = None
    if uploaded_file:
        file_stream = io.BytesIO(uploaded_file.getvalue())
        file_type = uploaded_file.type

        # --- Password prompt for encrypted PDFs ---
        if file_type == "application/pdf" and is_pdf_encrypted(file_stream):
            password = st.text_input("PDF Password", type="password")

        # --- Process & Review Button ---
        if st.button("Process & Review"):
            progress_bar = st.progress(0.0, text="Starting processing...")

            def update_progress_in_ui(progress_value, message_text):
                progress_bar.progress(progress_value, text=message_text)

            try:
                # --- Backend Pipeline ---
                if file_type == "application/pdf":
                    raw_df = parse_pdf(file_stream, password=password)
                else: # CSV
                    raw_df = parse_csv_file(file_stream)
                
                processor = AIDataProcessor()
                processed_df = processor.process_raw_data(
                    raw_df, 
                    on_progress=update_progress_in_ui
                )
                
                st.session_state.processed_df = processed_df
                st.session_state.upload_error = None # Clear previous errors
                progress_bar.progress(1.0, text="Processing complete!")


            except ValueError as e:
                st.session_state.upload_error = str(e)
                st.session_state.processed_df = None # Clear previous results
                progress_bar.progress(1.0, text="An error occurred.")


    # --- Display Error ---
    if st.session_state.upload_error:
        st.error(st.session_state.upload_error)

    # --- Editable Data Preview ---
    if st.session_state.processed_df is not None:
        st.subheader("Review and Correct Categories")
        
        db_interface = DatabaseInterface()
        categories_df = db_interface.get_categories_table()
        # Get only main categories for the dropdown
        available_categories = categories_df[categories_df['parent_category'].isnull()]['name'].tolist()

        edited_df = st.data_editor(
            st.session_state.processed_df,
            column_config={
                "category": st.column_config.SelectboxColumn(
                    "Category",
                    options=available_categories,
                    required=True,
                )
            },
            use_container_width=True
        )

        # --- Confirm & Save Button ---
        if st.button("Confirm & Save"):
            try:
                db_interface.save_transactions_table(edited_df)
                st.success("Transactions saved successfully!")
                
                # Clear state for next upload
                st.session_state.processed_df = None
                st.session_state.upload_error = None
                st.rerun() # Rerun to clear the file uploader

            except Exception as e:
                st.error(f"An error occurred while saving: {e}")

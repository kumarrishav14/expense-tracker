"""
Frontend Micro-Architecture: Statement Input Tab

This module implements the UI for the Statement Input tab, which is the primary
entry point for uploading and processing new transaction files.
"""

import streamlit as st
import pandas as pd
import io

from core.parsers.csv_parser import parse_csv_file
from core.parsers.pdf_parser import is_pdf_encrypted, parse_pdf
from core.processors.data_processor import DataProcessor
from core.database.db_interface import DatabaseInterface

def render():
    """Renders the Statement Input tab."""
    st.header("Upload New Statement")

    # --- State Initialization ---
    if 'uploaded_file_stream' not in st.session_state:
        st.session_state.uploaded_file_stream = ""
    if 'pdf_requires_password' not in st.session_state:
        st.session_state.pdf_requires_password = False
    if 'pdf_password' not in st.session_state:
        st.session_state.pdf_password = ""
    if 'preview_df' not in st.session_state:
        st.session_state.preview_df = None
    if 'upload_error' not in st.session_state:
        st.session_state.upload_error = None

    # --- File Uploader ---
    uploaded_file = st.file_uploader(
        "Choose a file (CSV or PDF)", 
        type=["csv", "pdf"]
    )

    if uploaded_file is not None:
        st.session_state.uploaded_file_stream = io.BytesIO(uploaded_file.getvalue())
        file_type = uploaded_file.type

        try:
            if file_type == "application/pdf":
                if is_pdf_encrypted(st.session_state.uploaded_file_stream):
                    st.session_state.pdf_requires_password = True
                else:
                    st.session_state.preview_df = parse_pdf(st.session_state.uploaded_file_stream, password=None)
            elif file_type == "text/csv":
                st.session_state.preview_df = parse_csv_file(st.session_state.uploaded_file_stream)
        except ValueError as e:
            st.session_state.upload_error = str(e)

    # --- Password Input Form ---
    if st.session_state.pdf_requires_password:
        with st.form("password_form"):
            st.session_state.pdf_password = st.text_input("Enter PDF Password", type="password")
            submitted = st.form_submit_button("Parse PDF")
            if submitted:
                try:
                    st.session_state.preview_df = parse_pdf(
                        st.session_state.uploaded_file_stream, 
                        st.session_state.pdf_password
                    )
                    st.session_state.pdf_requires_password = False
                except ValueError as e:
                    st.session_state.upload_error = str(e)

    # --- Display Error ---
    if st.session_state.upload_error:
        st.error(st.session_state.upload_error)
        st.session_state.upload_error = None # Clear error after displaying

    # --- Data Preview and Confirmation ---
    if st.session_state.preview_df is not None:
        st.subheader("Data Preview")
        st.dataframe(st.session_state.preview_df)

        if st.button("Confirm & Save"):
            try:
                processor = DataProcessor()
                standardized_df = processor.process_raw_data(st.session_state.preview_df)
                
                db_interface = DatabaseInterface()
                db_interface.save_transactions_table(standardized_df)
                
                st.success("Transactions saved successfully!")
                # Clear state after successful import
                st.session_state.preview_df = None
                st.session_state.uploaded_file_stream = None

            except Exception as e:
                st.error(f"An error occurred during processing: {e}")

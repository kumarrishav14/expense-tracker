"""
Frontend Micro-Architecture: Statement Input Tab

This module implements the UI for the Statement Input tab, following the
user-driven workflow with proper state machine implementation.
"""

import streamlit as st
import pandas as pd
import io

from core.parsers.csv_parser import parse_csv_file
from core.parsers.pdf_parser import is_pdf_encrypted, parse_pdf
from core.processors import EnhancedAIDataProcessor
from core.database.db_interface import DatabaseInterface

# State constants
AWAITING_UPLOAD = "AWAITING_UPLOAD"
AWAITING_PASSWORD = "AWAITING_PASSWORD"
AWAITING_ACCOUNT_SELECTION = "AWAITING_ACCOUNT_SELECTION"
READY_FOR_PROCESSING = "READY_FOR_PROCESSING"

def render():
    """Renders the Statement Input tab with state machine workflow."""
    st.header("Upload & Process New Statement")

    # Initialize database interface
    db_interface = DatabaseInterface()

    # --- State Initialization ---
    if 'upload_flow_state' not in st.session_state:
        st.session_state.upload_flow_state = AWAITING_UPLOAD
    if 'uploaded_file_data' not in st.session_state:
        st.session_state.uploaded_file_data = None
    if 'selected_account_id' not in st.session_state:
        st.session_state.selected_account_id = None
    if 'processed_df' not in st.session_state:
        st.session_state.processed_df = None
    if 'upload_error' not in st.session_state:
        st.session_state.upload_error = None

    # --- State Machine Implementation ---
    if st.session_state.upload_flow_state == AWAITING_UPLOAD:
        _render_file_upload_state(db_interface)
    elif st.session_state.upload_flow_state == AWAITING_PASSWORD:
        _render_password_state(db_interface)
    elif st.session_state.upload_flow_state == AWAITING_ACCOUNT_SELECTION:
        _render_account_selection_state(db_interface)
    elif st.session_state.upload_flow_state == READY_FOR_PROCESSING:
        _render_processing_state(db_interface)

    # --- Display Global Error ---
    if st.session_state.upload_error:
        st.error(st.session_state.upload_error)

def _render_file_upload_state(db_interface):
    """Render the file upload state."""
    st.info("📁 Please upload a statement file to begin processing.")
    
    uploaded_file = st.file_uploader(
        "Choose a statement file (CSV or PDF)", 
        type=["csv", "pdf"],
        key="file_uploader"
    )

    if uploaded_file:
        file_stream = io.BytesIO(uploaded_file.getvalue())
        file_type = uploaded_file.type

        # Store file data in session state
        st.session_state.uploaded_file_data = {
            'file_stream': file_stream,
            'file_type': file_type,
            'file_name': uploaded_file.name
        }

        # Check if PDF is encrypted
        if file_type == "application/pdf" and is_pdf_encrypted(file_stream):
            st.session_state.upload_flow_state = AWAITING_PASSWORD
            st.rerun()
        else:
            st.session_state.upload_flow_state = AWAITING_ACCOUNT_SELECTION
            st.rerun()

def _render_password_state(db_interface):
    """Render the password input state for encrypted PDFs."""
    st.info("🔒 This PDF is password protected. Please enter the password to continue.")
    
    file_name = st.session_state.uploaded_file_data['file_name']
    st.write(f"**File:** {file_name}")

    password = st.text_input("PDF Password", type="password", key="pdf_password")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("Unlock PDF", type="primary"):
            if password:
                try:
                    # Test password by attempting to parse
                    file_stream = st.session_state.uploaded_file_data['file_stream']
                    file_stream.seek(0)  # Reset stream position
                    test_df = parse_pdf(file_stream, password=password)
                    
                    # Store password for later use
                    st.session_state.uploaded_file_data['password'] = password
                    st.session_state.upload_error = None
                    st.session_state.upload_flow_state = AWAITING_ACCOUNT_SELECTION
                    st.rerun()
                    
                except Exception as e:
                    st.session_state.upload_error = f"Failed to unlock PDF: {str(e)}"
            else:
                st.session_state.upload_error = "Please enter a password."
    
    with col2:
        if st.button("Cancel"):
            _reset_upload_state()
            st.rerun()

def _render_account_selection_state(db_interface):
    """Render the account selection state."""
    st.info("🏦 Please select the account for this statement.")
    
    file_name = st.session_state.uploaded_file_data['file_name']
    st.write(f"**File:** {file_name}")

    # Load active accounts
    try:
        accounts_df = db_interface.get_accounts_table(only_active=True)
        
        if accounts_df.empty:
            st.warning("No active accounts found. Please create an account first.")
            _render_new_account_form(db_interface, required=True)
        else:
            # Create account options
            account_options = ["--- Select Account ---"] + [
                f"{row['name']} ({row['account_type']})" 
                for _, row in accounts_df.iterrows()
            ] + ["--- Add New Account ---"]
            
            selected_option = st.selectbox(
                "Select Account",
                account_options,
                key="account_selector"
            )
            
            if selected_option == "--- Add New Account ---":
                _render_new_account_form(db_interface)
            elif selected_option != "--- Select Account ---":
                # Extract account ID from selection
                account_name = selected_option.split(" (")[0]
                selected_account = accounts_df[accounts_df['name'] == account_name].iloc[0]
                st.session_state.selected_account_id = selected_account['id']
                
                st.success(f"✅ Selected account: **{selected_account['name']}**")
                
                if st.button("Continue to Processing", type="primary"):
                    st.session_state.upload_flow_state = READY_FOR_PROCESSING
                    st.rerun()
            
            # Cancel button
            if st.button("Cancel"):
                _reset_upload_state()
                st.rerun()
                
    except Exception as e:
        st.session_state.upload_error = f"Failed to load accounts: {str(e)}"

def _render_new_account_form(db_interface, required=False):
    """Render the new account creation form."""
    if required:
        st.subheader("Create New Account")
    else:
        with st.expander("Create New Account", expanded=True):
            _render_account_form_fields(db_interface)
        return
    
    _render_account_form_fields(db_interface)

def _render_account_form_fields(db_interface):
    """Render the account form fields."""
    with st.form("new_account_form"):
        st.write("**Account Details**")
        
        account_name = st.text_input("Account Name*", placeholder="e.g., HDFC Regalia")
        account_type = st.selectbox(
            "Account Type*",
            ["", "Credit Card", "Bank Account", "Savings Account", "Current Account"],
            index=0
        )
        bank_name = st.text_input("Bank Name", placeholder="e.g., HDFC Bank")
        account_number_last4 = st.text_input(
            "Last 4 digits of Account Number", 
            placeholder="e.g., 1234",
            max_chars=4
        )
        
        submitted = st.form_submit_button("Create Account", type="primary")
        
        if submitted:
            if not account_name or not account_type:
                st.error("Account Name and Account Type are required.")
            else:
                try:
                    # Create account DataFrame
                    new_account_df = pd.DataFrame([{
                        'name': account_name,
                        'account_type': account_type,
                        'bank_name': bank_name if bank_name else None,
                        'account_number_last4': account_number_last4 if account_number_last4 else None,
                        'is_active': True
                    }])
                    
                    # Save account
                    result = db_interface.save_accounts_table(new_account_df)
                    
                    if result.success:
                        created_account = result.successful_items[0]
                        st.session_state.selected_account_id = created_account['id']
                        st.success(f"✅ Account '{account_name}' created successfully!")
                        st.session_state.upload_flow_state = READY_FOR_PROCESSING
                        st.rerun()
                    else:
                        st.error(f"Failed to create account: {result.error_message}")
                        
                except Exception as e:
                    st.error(f"Error creating account: {str(e)}")

def _render_processing_state(db_interface):
    """Render the processing state."""
    # Get account info
    try:
        accounts_df = db_interface.get_accounts_table()
        selected_account = accounts_df[accounts_df['id'] == st.session_state.selected_account_id].iloc[0]
        account_name = selected_account['name']
        
        st.success(f"🎯 File ready for account: **{account_name}**")
        
        file_name = st.session_state.uploaded_file_data['file_name']
        st.write(f"**File:** {file_name}")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("Process Statement", type="primary"):
                _process_statement(db_interface)
        
        with col2:
            if st.button("Start Over"):
                _reset_upload_state()
                st.rerun()
                
        # Show processed data if available
        if st.session_state.processed_df is not None:
            _render_data_review(db_interface)
            
    except Exception as e:
        st.session_state.upload_error = f"Error loading account information: {str(e)}"

def _process_statement(db_interface):
    """Process the uploaded statement."""
    try:
        with st.spinner("Processing file... Please wait."):
            progress_bar = st.progress(0.0, text="Starting processing...")

            def update_progress_in_ui(progress_value, message_text):
                progress_bar.progress(progress_value, text=message_text)

            # Parse file
            file_data = st.session_state.uploaded_file_data
            file_stream = file_data['file_stream']
            file_stream.seek(0)  # Reset stream position
            
            if file_data['file_type'] == "application/pdf":
                password = file_data.get('password')
                raw_df = parse_pdf(file_stream, password=password)
            else:  # CSV
                raw_df = parse_csv_file(file_stream)
            
            # Process data
            processor = EnhancedAIDataProcessor(debug=False)
            processed_df = processor.process_raw_data(
                raw_df, 
                on_progress=update_progress_in_ui
            )
            
            # Add account_id to processed data
            processed_df['account_id'] = st.session_state.selected_account_id
            
            st.session_state.processed_df = processed_df
            st.session_state.upload_error = None
            progress_bar.progress(1.0, text="Processing complete!")
            st.rerun()

    except Exception as e:
        st.session_state.upload_error = f"Processing failed: {str(e)}"
        progress_bar.progress(1.0, text="An error occurred.")

def _render_data_review(db_interface):
    """Render the data review and editing interface."""
    st.subheader("Review and Correct Categories")
    
    # Load categories for dropdown
    try:
        categories_df = db_interface.get_categories_table()
        # Get only main categories for the dropdown
        available_categories = categories_df[categories_df['parent_category'].isnull()]['name'].tolist()

        # Create editable dataframe (exclude account_id from display)
        display_df = st.session_state.processed_df.drop(columns=['account_id'])
        
        edited_df = st.data_editor(
            display_df,
            column_config={
                "category": st.column_config.SelectboxColumn(
                    "Category",
                    options=available_categories,
                    required=True,
                )
            },
            use_container_width=True,
            key="data_editor"
        )

        # Add account_id back to edited data
        edited_df['account_id'] = st.session_state.selected_account_id

        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("Confirm & Save", type="primary"):
                try:
                    result = db_interface.save_transactions_table(edited_df)
                    if result.success:
                        st.success(f"✅ {result.successful_count} transactions saved successfully!")
                        _reset_upload_state()
                        st.rerun()
                    else:
                        st.error(f"Failed to save transactions: {result.error_message}")
                except Exception as e:
                    st.error(f"Error saving transactions: {str(e)}")
        
        with col2:
            if st.button("Cancel"):
                st.session_state.processed_df = None
                st.rerun()
                
    except Exception as e:
        st.error(f"Error loading categories: {str(e)}")

def _reset_upload_state():
    """Reset the upload state to start over."""
    st.session_state.upload_flow_state = AWAITING_UPLOAD
    st.session_state.uploaded_file_data = None
    st.session_state.selected_account_id = None
    st.session_state.processed_df = None
    st.session_state.upload_error = None

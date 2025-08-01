
"""
Frontend Micro-Architecture: Accounts Tab (Simple - Master-Detail)

This module implements a simplified UI for the Accounts tab for A/B testing purposes.
It uses a master-detail layout with vanilla Streamlit components for a clean 
and straightforward user experience.
"""

import streamlit as st
import pandas as pd
from core.database.db_interface import DatabaseInterface

def _handle_account_selection():
    """Callback to update state when a new account is selected."""
    st.session_state.selected_account_id_simple = st.session_state.account_radio_selector
    st.session_state.action_simple = "view"

def render():
    """Renders the simplified Accounts tab with a master-detail layout."""
    st.title("Account Management (Simple)")

    db_interface = DatabaseInterface()

    # Initialize session state
    if 'selected_account_id_simple' not in st.session_state:
        st.session_state.selected_account_id_simple = None
    if 'action_simple' not in st.session_state:
        st.session_state.action_simple = "view"  # view, add, edit

    # Load accounts
    try:
        accounts_df = db_interface.get_accounts_table(only_active=False)
    except Exception as e:
        st.error(f"Error loading accounts: {e}")
        return

    # Master-detail layout
    master_col, detail_col = st.columns([1, 1.5])

    with master_col:
        _render_master_view(db_interface, accounts_df)

    with detail_col:
        _render_detail_view(db_interface, accounts_df)

def _render_master_view(db_interface, accounts_df):
    """Renders the master view with a list of accounts."""
    st.header("Your Accounts")

    if st.button("Add New Account", use_container_width=True):
        st.session_state.action_simple = "add"
        st.session_state.selected_account_id_simple = None
        st.rerun()

    if accounts_df.empty:
        st.info("No accounts found. Click 'Add New Account' to get started.")
        return

    # Use st.radio for selection, which is compatible with older Streamlit versions
    account_ids = accounts_df['id'].tolist()
    account_names = accounts_df['name'].tolist()
    
    # Set index for radio button based on current selection
    try:
        current_selection_index = account_ids.index(st.session_state.selected_account_id_simple)
    except (ValueError, TypeError):
        current_selection_index = 0 # Default to first item if nothing is selected

    st.radio(
        "Select an account:",
        options=account_ids,
        format_func=lambda account_id: account_names[account_ids.index(account_id)],
        key="account_radio_selector",
        on_change=_handle_account_selection,
        index=current_selection_index,
        label_visibility="collapsed"
    )


def _render_detail_view(db_interface, accounts_df):
    """Renders the detail view for the selected account or a form."""
    action = st.session_state.action_simple
    selected_account_id = st.session_state.selected_account_id_simple

    # If the radio button has a selection, ensure we are in view mode
    if st.session_state.account_radio_selector and action != 'edit':
         st.session_state.selected_account_id_simple = st.session_state.account_radio_selector
         selected_account_id = st.session_state.account_radio_selector
         action = 'view'

    if action == "add":
        _render_add_account_form(db_interface)
    elif action == "edit" and selected_account_id is not None:
        _render_edit_account_form(db_interface, accounts_df)
    elif action == "view" and selected_account_id is not None:
        _render_account_details(db_interface, accounts_df)
    else:
        st.info("Select an account to view its details or add a new one.")

def _render_account_details(db_interface, accounts_df):
    """Displays the details of the selected account."""
    account_id = st.session_state.selected_account_id_simple
    
    if account_id is None:
        st.info("Please select an account from the list.")
        return
        
    account_series = accounts_df[accounts_df['id'] == account_id]
    
    if account_series.empty:
        st.error("Selected account not found. It might have been deleted.")
        st.session_state.selected_account_id_simple = None # Reset selection
        st.rerun()
        return

    account = account_series.iloc[0]

    st.header(account['name'])
    
    st.markdown(f"**Account Type:** {account['account_type']}")
    st.markdown(f"**Bank Name:** {account['bank_name'] or 'N/A'}")
    st.markdown(f"**Last 4 Digits:** {account['account_number_last4'] or 'N/A'}")
    st.markdown(f"**Status:** {'Active' if account['is_active'] else 'Inactive'}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Edit", use_container_width=True):
            st.session_state.action_simple = "edit"
            st.rerun()
    
    with col2:
        if account['is_active']:
            if st.button("Close Account", use_container_width=True):
                _toggle_account_status(db_interface, account_id, False)
        else:
            if st.button("Reactivate Account", use_container_width=True):
                _toggle_account_status(db_interface, account_id, True)

    # Credit Card Statements Section (if applicable)
    if account['account_type'] == 'Credit Card':
        _render_credit_card_statements(db_interface, account['id'])


def _render_add_account_form(db_interface):
    """Renders the form to add a new account."""
    st.header("Add New Account")

    with st.form("add_account_form_simple"):
        name = st.text_input("Account Name *")
        account_type = st.selectbox("Account Type *", ["Credit Card", "Bank Account", "Savings Account", "Current Account", "Investment Account"])
        bank_name = st.text_input("Bank Name")
        account_number_last4 = st.text_input("Last 4 Digits of Account Number", max_chars=4)

        submitted = st.form_submit_button("Save")
        if submitted:
            if not name:
                st.error("Account Name is required.")
            else:
                new_account_df = pd.DataFrame([{'name': name, 'account_type': account_type, 'bank_name': bank_name, 'account_number_last4': account_number_last4, 'is_active': True}])
                result = db_interface.save_accounts_table(new_account_df)
                if result.success:
                    st.success("Account added successfully!")
                    st.session_state.action_simple = "view"
                    st.session_state.selected_account_id_simple = result.successful_items[0]['id']
                    st.rerun()
                else:
                    st.error(f"Failed to add account: {result.error_message}")

    if st.button("Cancel"):
        st.session_state.action_simple = "view"
        st.rerun()

def _render_edit_account_form(db_interface, accounts_df):
    """Renders the form to edit an existing account."""
    st.header("Edit Account")

    account_id = st.session_state.selected_account_id_simple
    account = accounts_df[accounts_df['id'] == account_id].iloc[0]

    with st.form("edit_account_form_simple"):
        name = st.text_input("Account Name *", value=account['name'])
        account_types = ["Credit Card", "Bank Account", "Savings Account", "Current Account", "Investment Account"]
        type_index = account_types.index(account['account_type']) if account['account_type'] in account_types else 0
        account_type = st.selectbox("Account Type *", account_types, index=type_index)
        bank_name = st.text_input("Bank Name", value=account['bank_name'])
        account_number_last4 = st.text_input("Last 4 Digits of Account Number", value=account['account_number_last4'], max_chars=4)

        submitted = st.form_submit_button("Update")
        if submitted:
            if not name:
                st.error("Account Name is required.")
            else:
                update_data = {'name': name, 'account_type': account_type, 'bank_name': bank_name, 'account_number_last4': account_number_last4}
                result = db_interface.update_account(account_id, update_data)
                if result.success:
                    st.success("Account updated successfully!")
                    st.session_state.action_simple = "view"
                    st.rerun()
                else:
                    st.error(f"Failed to update account: {result.error_message}")

    if st.button("Cancel"):
        st.session_state.action_simple = "view"
        st.rerun()

def _toggle_account_status(db_interface, account_id, is_active):
    """Toggles the active status of an account."""
    result = db_interface.update_account(account_id, {'is_active': is_active})
    if result.success:
        status = "reactivated" if is_active else "closed"
        st.success(f"Account successfully {status}.")
        st.rerun()
    else:
        st.error(f"Failed to update account status: {result.error_message}")

def _render_credit_card_statements(db_interface, account_id):
    """Render credit card statements section."""
    st.subheader("Credit Card Statements")

    try:
        statements_df = db_interface.get_card_statements_table()
        account_statements = statements_df[statements_df['account_id'] == account_id]

        if account_statements.empty:
            st.info("No statements uploaded for this account.")
            return

        st.dataframe(account_statements[['statement_date', 'total_due', 'status']])

    except Exception as e:
        st.error(f"Error loading statements: {str(e)}")

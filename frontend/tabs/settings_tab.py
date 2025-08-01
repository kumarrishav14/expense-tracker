"""
Frontend Micro-Architecture: Settings Tab

This module implements the UI for the Settings tab, allowing users to manage
all global application settings in a centralized manner.
"""

import streamlit as st
from core.config.settings_manager import settings_manager

def render():
    """Renders the Settings tab."""
    st.header("Application Settings")

    # Load current settings directly from the manager
    current_settings = settings_manager.get_app_settings()

    with st.form("app_settings_form"):
        st.subheader("Ollama AI Settings")
        st.write("Configure the connection to your local Ollama instance.")
        
        host = st.text_input(
            "Ollama Server URL", 
            value=current_settings.ollama.host
        )
        model = st.text_input(
            "Model Name", 
            value=current_settings.ollama.model
        )
        timeout = st.number_input(
            "Request Timeout (seconds)", 
            value=current_settings.ollama.timeout,
            min_value=1
        )

        st.divider()

        st.subheader("Custom Categorization Rules")
        st.write("Define custom rules to improve categorization accuracy.")
        categorization_rules = st.text_area(
            "Rules",
            value=current_settings.categorization_rules,
            height=200
        )

        submitted = st.form_submit_button("Save All Settings")
        if submitted:
            try:
                # Update Ollama settings
                settings_manager.update_ollama_settings(host=host, model=model, timeout=timeout)
                
                # Update categorization rules (even if disabled, to be future-proof)
                settings_manager.update_categorization_rules(categorization_rules)

                st.success("Settings saved successfully!")
            except Exception as e:
                st.error(f"Failed to save settings: {e}")
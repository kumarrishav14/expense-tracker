"""
Frontend Micro-Architecture: Settings Tab

This module implements the UI for the Settings tab, which allows users to
configure the Ollama AI integration.
"""

import streamlit as st
from ai.ollama.config import OllamaConfigManager, OllamaSettings

def render():
    """Renders the Settings tab."""
    st.header("Ollama AI Settings")

    config_manager = OllamaConfigManager()

    # --- Load current settings ---
    if 'ollama_settings' not in st.session_state:
        st.session_state.ollama_settings = config_manager.load_settings()

    # --- Settings Form ---
    with st.form("ollama_settings_form"):
        st.write("Configure the connection to your local Ollama instance.")
        
        base_url = st.text_input(
            "Ollama Server URL", 
            value=st.session_state.ollama_settings.base_url
        )
        model = st.text_input(
            "Model Name", 
            value=st.session_state.ollama_settings.model
        )
        timeout = st.number_input(
            "Request Timeout (seconds)", 
            value=st.session_state.ollama_settings.timeout,
            min_value=1
        )

        submitted = st.form_submit_button("Save Settings")
        if submitted:
            try:
                new_settings = OllamaSettings(base_url=base_url, model=model, timeout=timeout)
                config_manager.save_settings(new_settings)
                st.session_state.ollama_settings = new_settings
                st.success("Settings saved successfully!")
            except Exception as e:
                st.error(f"Failed to save settings: {e}")

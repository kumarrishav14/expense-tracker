# Architectural Review: State-Aware Navigation with Streamlit-Option-Menu

**Author:** AI Architect
**Date:** July 24, 2025
**Version:** 1.0

## 1. Overview

This document provides the final architectural solution for all frontend navigation and state persistence issues, including the two-click bug and state loss between tab switches. This plan supersedes all previous recommendations.

After a thorough review, the most effective and cleanest solution is to adopt the third-party component **`streamlit-option-menu`**. This component is specifically designed to provide a stateful, visually appealing navigation bar that solves our current issues with less complexity than a custom-built solution.

## 2. Rationale

-   **Stateful by Design:** The component has built-in support for `st.session_state`, which directly solves the problem of the UI resetting on script reruns.
-   **Superior UI/UX:** It provides a clean, tab-like horizontal menu with support for icons, offering a better user experience than native components like `st.pills` or `st.radio`.
-   **Simplified Code:** It reduces the complexity of our main application file, as the state management logic is more direct.
-   **Low Overhead:** The component is a single, well-maintained dependency that provides significant value.

## 3. Implementation Plan

### 3.1. Step 1: Add New Dependency

The developer must add `streamlit-option-menu` to the project's dependencies.

**File to Modify:** `pyproject.toml`

**Action:** Add the following line under the `[project.dependencies]` section:
```toml
"streamlit-option-menu"
```
After modifying the file, the developer must run `uv pip install -r requirements.txt` (or the equivalent `uv` command) to install the new package into the environment.

### 3.2. Step 2: Update the Main Application

The main application entry point must be updated to use the new navigation component.

**File to Modify:** `frontend/app.py`

**Logic:**
1.  Import the `option_menu` function.
2.  Use `st.session_state` to store the selected option's index, which is more robust than storing the label.
3.  Render the `option_menu` component, setting its `default_index` from the session state.
4.  Use the returned value from the component to conditionally render the content of the selected tab.

**Example Revised `main()` function:**

```python
# In frontend/app.py
import streamlit as st
from streamlit_option_menu import option_menu

# ... (other imports: sys, os, seeder, tabs)

def main():
    """Main function to run the Streamlit application."""
    initialize_database()
    st.set_page_config(layout="wide")
    st.title("Expenses Tracking Tool")

    # --- State-aware Navigation using streamlit-option-menu ---
    # Initialize state for the selected option's index
    if "selected_tab_index" not in st.session_state:
        st.session_state.selected_tab_index = 0 # Default to Dashboard

    # Render the option menu
    selected_tab = option_menu(
        menu_title=None,  # required
        options=["Dashboard", "Statement Input", "Settings"],
        icons=['house', 'cloud-upload', 'gear'],  # optional
        menu_icon="cast",  # optional
        default_index=st.session_state.selected_tab_index,
        orientation="horizontal",
    )

    # Update the session state with the index of the selected tab
    # This is crucial for preserving state across reruns
    tab_options = ["Dashboard", "Statement Input", "Settings"]
    st.session_state.selected_tab_index = tab_options.index(selected_tab)

    # --- Render Content based on Active Tab ---
    if selected_tab == "Dashboard":
        dashboard_tab.render()
    elif selected_tab == "Statement Input":
        statement_input_tab.render()
    elif selected_tab == "Settings":
        settings_tab.render()

if __name__ == "__main__":
    main()
```

This architecture is the most direct and robust solution. It solves all identified navigation issues while simultaneously improving the application's visual design and simplifying the code in `app.py`.

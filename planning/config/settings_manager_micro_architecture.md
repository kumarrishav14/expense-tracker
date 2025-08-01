# Settings Manager Micro-Architecture

**Component:** `core.config.settings_manager.SettingsManager`  
**Last Updated:** July 31, 2025  
**Status:** Finalized

---

## 1. **What & Why**

**Purpose:** This component provides a centralized, type-safe, and scalable mechanism for managing all application settings. It replaces the previous single-purpose `ollama_config.json` with a unified `settings.json` file.

**Key Decisions:**
- **Centralized `settings.json`**: A single file for all application settings simplifies configuration management and prevents the proliferation of config files.
- **Pydantic for Type Safety**: Using Pydantic models to define the settings schema ensures that all configuration data is validated on load and accessed in a type-safe manner, reducing runtime errors.
- **Manager as a Singleton**: The `SettingsManager` will be treated as a singleton instance throughout the application to ensure a single, consistent source of truth for all settings.

---

## 2. **Where It Fits**

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Settings Tab   │───▶│ SettingsManager  │◀───│    Processor     │
│       (UI)       │    │                  │    │   (Backend)      │
└──────────────────┘    └───────┬──────────┘    └──────────────────┘
                                │
                                ▼
                          settings.json
```

**Depends On:**
- **File System:** Reads from and writes to `settings.json`.
- **Pydantic:** For data validation and modeling.

**Used By:**
- **Frontend (Settings Tab):** To read current settings for display and to write updated settings.
- **Backend Components (e.g., Processors):** To fetch configuration like Ollama settings or categorization rules.
- **Application Startup:** To load the initial configuration.

---

## 3. **Internal Structure**

```
┌─────────────────────────────────────────┐
│           SettingsManager               │
├─────────────────────────────────────────┤
│  Public API Layer                      │
│  ┌────────────────┐ ┌────────────────┐ │
│  │ get_ollama()   │ │ update_rules() │ │
│  └────────────────┘ └────────────────┘ │
├─────────────────────────────────────────┤
│  Business Logic Layer                  │
│  ┌────────────────┐ ┌────────────────┐ │
│  │    load()      │ │     save()     │ │
│  └────────────────┘ └────────────────┘ │
├─────────────────────────────────────────┤
│  Data Layer                            │
│  ┌────────────────┐ ┌────────────────┐ │
│  │ Pydantic Models│ │ JSON I/O       │ │
│  └────────────────┘ └────────────────┘ │
└─────────────────────────────────────────┘
```

**Critical Path:**
1.  On application startup, an instance of `SettingsManager` is created.
2.  The `load()` method is called, which reads `settings.json`, validates its content against the Pydantic `AppSettings` model, and stores the result in memory.
3.  When a component needs a setting, it calls a specific getter (e.g., `get_ollama_config()`).
4.  When the user saves changes in the UI, the UI calls a specific update method (e.g., `update_categorization_rules()`), which modifies the in-memory Pydantic object and immediately calls `save()` to persist the changes to disk.

---

## 4. **Performance & Scalability**

| Operation | Complexity | Notes |
|-----------|------------|-------|
| `load()`  | O(1)       | Fast file I/O, performed once on startup. |
| `save()`  | O(1)       | Fast file I/O. Called infrequently on user action. |
| `get_*()` | O(1)       | Instantaneous memory access. |

**Limits:**
- **Memory:** Negligible. The settings object is very small.
- **CPU:** Negligible. Simple data access.
- **Scalability:** The architecture is highly scalable from a code maintenance perspective, as adding new settings only requires extending the Pydantic models.

---

## 5. Public API

The `SettingsManager` will expose a clear and concise API for other components to interact with. All methods that modify settings will automatically handle saving the changes to disk.

```python
class SettingsManager:
    # --- Lifecycle ---
    def __init__(self, settings_path: str = "settings.json") -> None:
        """Initializes the manager and loads the settings from disk."""
        pass

    def load(self) -> AppSettings:
        """Loads settings from the JSON file. Creates default if not found."""
        pass

    def save(self) -> None:
        """Persists the current in-memory settings back to the JSON file."""
        pass

    # --- Getters --- 
    def get_app_settings(self) -> AppSettings:
        """Returns the entire Pydantic settings object."""
        pass

    def get_ollama_settings(self) -> OllamaSettings:
        """Returns the Ollama-specific settings."""
        pass

    def get_categorization_rules(self) -> str:
        """Returns the user's custom categorization rules as a single string."""
        pass

    # --- Setters ---
    def update_ollama_settings(self, host: str, model: str, timeout: int) -> None:
        """Updates the Ollama settings and saves to disk."""
        pass

    def update_categorization_rules(self, new_rules_text: str) -> None:
        """Updates the categorization rules text and saves to disk."""
        pass
```

## 6. Implementation Notes

### Singleton Pattern

It is **critical** that the `SettingsManager` be implemented as a **Singleton**. There must only be one instance of this class for the entire application lifecycle. This ensures a single, consistent source of truth for all settings and prevents race conditions where different components could overwrite each other's changes.

The recommended approach is to instantiate the class once at the module level:

**In `core/config/settings_manager.py`:**
```python
class SettingsManager:
    # ... class implementation ...
    pass

# The single, shared instance to be imported by other modules
settings_manager = SettingsManager()
```

**Usage in other components:**
```python
from core.config.settings_manager import settings_manager

# Direct access to the shared instance
ollama_host = settings_manager.get_ollama_settings().host
```

## 7. Internal Testing

```python
def test_load_success():
    """Verify loading a valid settings.json file."""
    # Test with a well-formed JSON file
    pass

def test_load_file_not_found():
    """Verify graceful handling when settings.json is missing."""
    # Test that default settings are created
    pass

def test_load_corrupted_json():
    """Verify graceful handling of a malformed JSON file."""
    # Test that an error is raised or defaults are used
    pass

def test_update_and_save():
    """Verify that updating a setting correctly modifies the file on disk."""
    # Test a getter, then a setter, then reload to confirm persistence
    pass
```

"""
This module provides a centralized, type-safe manager for all application settings.
"""

import json
from pathlib import Path

from .models import AppSettings, OllamaSettings

class SettingsManager:
    """Manages the application settings, acting as a singleton."""

    def __init__(self, settings_path: str = "settings.json"):
        """Initializes the manager and loads settings from disk."""
        self.settings_path = Path(settings_path)
        self.settings: AppSettings  # Guaranteed to be loaded by self.load()
        self.load()

    def load(self) -> AppSettings:
        """Loads settings from the JSON file. Creates default if not found."""
        if not self.settings_path.exists():
            self.settings = AppSettings()
            self.save()
        else:
            try:
                with open(self.settings_path, 'r') as f:
                    data = json.load(f)
                self.settings = AppSettings(**data)
            except (json.JSONDecodeError, TypeError):
                # If the file is corrupted or invalid, create a default and overwrite
                self.settings = AppSettings()
                self.save()
        return self.settings

    def save(self) -> None:
        """Persists the current in-memory settings back to the JSON file."""
        with open(self.settings_path, 'w') as f:
            json.dump(self.settings.model_dump(), f, indent=4)

    def get_app_settings(self) -> AppSettings:
        """Returns the entire Pydantic settings object."""
        return self.settings

    def get_ollama_settings(self) -> OllamaSettings:
        """Returns the Ollama-specific settings."""
        return self.settings.ollama

    def get_categorization_rules(self) -> str:
        """Returns the user's custom categorization rules as a single string."""
        return self.settings.categorization_rules

    def update_ollama_settings(self, host: str, model: str, timeout: int) -> None:
        """Updates the Ollama settings and saves to disk."""
        self.settings.ollama.host = host
        self.settings.ollama.model = model
        self.settings.ollama.timeout = timeout
        self.save()

    def update_categorization_rules(self, new_rules_text: str) -> None:
        """Updates the categorization rules text and saves to disk."""
        self.settings.categorization_rules = new_rules_text
        self.save()

# The single, shared instance to be imported by other modules
settings_manager = SettingsManager()
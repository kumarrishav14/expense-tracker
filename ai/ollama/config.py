"""
Ollama Configuration Management

Simple configuration management for Ollama client settings.
Integrates with Streamlit app settings.
"""

import os
from typing import Optional
from dataclasses import dataclass, asdict
import json


@dataclass
class OllamaConfig:
    """Configuration for Ollama client."""
    base_url: str = "http://localhost:11434"
    model: str = "llama2"
    timeout: int = 30


@dataclass
class OllamaSettings:
    """Ollama settings that can be configured in Streamlit app."""
    base_url: str = "http://localhost:11434"
    model: str = "llama2"
    timeout: int = 30
    enabled: bool = True


class OllamaConfigManager:
    """Simple configuration manager for Ollama settings."""
    
    def __init__(self, config_file: str = "ollama_config.json"):
        """
        Initialize config manager.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self._settings: Optional[OllamaSettings] = None
    
    def load_settings(self) -> OllamaSettings:
        """
        Load settings from file or create a default config if it doesn't exist.
        
        Returns:
            OllamaSettings instance
        """
        if self._settings is not None:
            return self._settings
        
        if not os.path.exists(self.config_file):
            # Create default settings and save them
            default_settings = OllamaSettings()
            self.save_settings(default_settings)
            self._settings = default_settings
            return self._settings

        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                self._settings = OllamaSettings(**data)
                return self._settings
        except (Exception, json.JSONDecodeError):
            # If file is corrupted or invalid, create a default one
            default_settings = OllamaSettings()
            self.save_settings(default_settings)
            self._settings = default_settings
            return self._settings
    
    def save_settings(self, settings: OllamaSettings) -> None:
        """
        Save settings to file.
        
        Args:
            settings: OllamaSettings to save
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(asdict(settings), f, indent=2)
            self._settings = settings
        except Exception as e:
            raise Exception(f"Failed to save settings: {str(e)}")
    
    def update_setting(self, key: str, value: any) -> None:
        """
        Update a specific setting.
        
        Args:
            key: Setting key to update
            value: New value
        """
        settings = self.load_settings()
        if hasattr(settings, key):
            setattr(settings, key, value)
            self.save_settings(settings)
        else:
            raise ValueError(f"Unknown setting: {key}")
    
    def get_client_config(self) -> 'OllamaConfig':
        """
        Get OllamaConfig instance for client initialization.
        
        Returns:
            OllamaConfig instance
        """
        settings = self.load_settings()
        return OllamaConfig(
            base_url=settings.base_url,
            model=settings.model,
            timeout=settings.timeout
        )
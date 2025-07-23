"""
Ollama Client Factory

Simple factory for creating and managing Ollama client instances.
"""

from typing import Optional
from .client import OllamaClient
from .config import OllamaConfigManager, OllamaSettings


class OllamaFactory:
    """Factory for creating Ollama client instances."""
    
    _instance: Optional[OllamaClient] = None
    _config_manager: Optional[OllamaConfigManager] = None
    
    @classmethod
    def get_client(cls, force_reload: bool = False) -> OllamaClient:
        """
        Get Ollama client instance (singleton pattern for simplicity).
        
        Args:
            force_reload: Force reload of configuration
            
        Returns:
            OllamaClient instance
        """
        if cls._instance is None or force_reload:
            if cls._config_manager is None:
                cls._config_manager = OllamaConfigManager()
            
            config = cls._config_manager.get_client_config()
            cls._instance = OllamaClient(config)
        
        return cls._instance
    
    @classmethod
    def get_config_manager(cls) -> OllamaConfigManager:
        """
        Get configuration manager instance.
        
        Returns:
            OllamaConfigManager instance
        """
        if cls._config_manager is None:
            cls._config_manager = OllamaConfigManager()
        return cls._config_manager
    
    @classmethod
    def update_settings(cls, settings: OllamaSettings) -> None:
        """
        Update Ollama settings and reload client.
        
        Args:
            settings: New OllamaSettings
        """
        config_manager = cls.get_config_manager()
        config_manager.save_settings(settings)
        cls._instance = None  # Force reload on next get_client call
    
    @classmethod
    def is_available(cls) -> bool:
        """
        Check if Ollama is available and configured.
        
        Returns:
            True if Ollama is available, False otherwise
        """
        try:
            client = cls.get_client()
            return client.test_connection()
        except Exception:
            return False


# Convenience functions for easy access
def get_ollama_client(force_reload: bool = False) -> OllamaClient:
    """Get Ollama client instance."""
    return OllamaFactory.get_client(force_reload)


def is_ollama_available() -> bool:
    """Check if Ollama is available."""
    return OllamaFactory.is_available()


def categorize_expense(description: str, categories: list) -> str:
    """
    Categorize an expense using Ollama AI.
    
    Args:
        description: Transaction description
        categories: Available categories
        
    Returns:
        Suggested category
    """
    try:
        client = get_ollama_client()
        return client.categorize_transaction(description, categories)
    except Exception:
        # Fallback to first category if AI fails
        return categories[0] if categories else "Other"
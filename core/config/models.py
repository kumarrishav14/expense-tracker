"""
This module defines the Pydantic models for application settings.
"""

from pydantic import BaseModel, Field

class OllamaSettings(BaseModel):
    """Settings for the Ollama client."""
    host: str = Field(default="http://localhost:11434", description="The host of the Ollama API.")
    model: str = Field(default="mistral", description="The default model to use for generation.")
    timeout: int = Field(default=30, description="The timeout in seconds for API requests.")

class AppSettings(BaseModel):
    """The root model for all application settings."""
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    categorization_rules: str = Field(default="", description="User-defined rules for categorization.")

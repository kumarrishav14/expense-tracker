"""
Ollama Backend API Client

A simple client for interacting with Ollama server using requests.
Provides basic functionality for AI tasks in the expense tracking application.
"""

import json
import requests
from typing import Dict, List, Optional, Any
from .config import OllamaConfig


class OllamaConnectionError(Exception):
    """Custom exception for connection errors to the Ollama server."""
    pass


class OllamaTimeoutError(Exception):
    """Custom exception for timeout errors."""
    pass


class OllamaAPIError(Exception):
    """Custom exception for Ollama API errors."""
    pass


class OllamaClient:
    """Simple Ollama client using requests for API calls."""
    
    def __init__(self, config: OllamaConfig):
        """
        Initialize Ollama client with configuration.
        
        Args:
            config: OllamaConfig instance with server settings
        """
        self.config = config
        self.base_url = config.base_url.rstrip('/')
    
    def _execute_request(self, endpoint: str, method: str = "GET", 
                         data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute HTTP request and return parsed JSON response.
        
        Args:
            endpoint: API endpoint (e.g., "/api/tags")
            method: HTTP method (GET, POST)
            data: JSON data for POST requests
            
        Returns:
            Parsed JSON response
            
        Raises:
            OllamaConnectionError: If a connection error occurs.
            OllamaTimeoutError: If the request times out.
            OllamaAPIError: If the API returns an error.
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "POST":
                response = requests.post(url, json=data, timeout=self.config.timeout)
            else:
                response = requests.get(url, timeout=self.config.timeout)
            
            response.raise_for_status()
            
            if not response.text.strip():
                raise OllamaAPIError("Empty response from server")
                
            return response.json()
            
        except requests.exceptions.ConnectionError as e:
            raise OllamaConnectionError(f"Connection to {self.base_url} failed: {e}") from e
        except requests.exceptions.Timeout as e:
            raise OllamaTimeoutError(f"Request timed out after {self.config.timeout} seconds") from e
        except requests.exceptions.HTTPError as e:
            raise OllamaAPIError(f"HTTP error occurred: {e.response.status_code} - {e.response.text}") from e
        except json.JSONDecodeError as e:
            raise OllamaAPIError(f"Invalid JSON response: {e}") from e
    
    def test_connection(self) -> bool:
        """
        Test if Ollama server is accessible.
        
        Returns:
            True if server is accessible, False otherwise
        """
        try:
            response = self._execute_request("/api/tags")
            return "models" in response
        except (OllamaConnectionError, OllamaTimeoutError, OllamaAPIError):
            return False
    
    def list_models(self) -> List[str]:
        """
        Get list of available models on the server.
        
        Returns:
            List of model names
            
        Raises:
            OllamaAPIError: If unable to fetch models
        """
        try:
            response = self._execute_request("/api/tags")
            models = response.get("models", [])
            return [model.get("name", "") for model in models if model.get("name")]
        except (OllamaConnectionError, OllamaTimeoutError, OllamaAPIError) as e:
            raise OllamaAPIError(f"Failed to fetch models: {str(e)}") from e
    
    def check_model_exists(self, model_name: Optional[str] = None) -> bool:
        """
        Check if a specific model exists on the server.
        
        Args:
            model_name: Model name to check (uses config.model if None)
            
        Returns:
            True if model exists, False otherwise
        """
        try:
            model_to_check = model_name or self.config.model
            available_models = self.list_models()
            return model_to_check in available_models
        except OllamaAPIError:
            return False
    
    def generate_completion(self, prompt: str, model: Optional[str] = None, 
                          stream: bool = False) -> str:
        """
        Generate text completion using Ollama.
        
        Args:
            prompt: Input prompt for the model
            model: Model name (uses config.model if None)
            stream: Whether to stream response (not implemented for simplicity)
            
        Returns:
            Generated text response
            
        Raises:
            OllamaAPIError: If generation fails
        """
        model_name = model or self.config.model
        
        data = {
            "model": model_name,
            "prompt": prompt,
            "stream": False  # Keep it simple for now
        }
        
        try:
            response = self._execute_request("/api/generate", method="POST", data=data)
            return response.get("response", "")
        except (OllamaConnectionError, OllamaTimeoutError, OllamaAPIError) as e:
            raise OllamaAPIError(f"Failed to generate completion: {str(e)}") from e
    
    def categorize_transaction(self, transaction_description: str, 
                             available_categories: List[str]) -> str:
        """
        Categorize a transaction using AI.
        
        Args:
            transaction_description: Description of the transaction
            available_categories: List of available expense categories
            
        Returns:
            Suggested category name
            
        Raises:
            OllamaAPIError: If categorization fails
        """
        categories_str = ", ".join(available_categories)
        
        with open("prompts/expense_categorization.txt", "r") as f:
            prompt_template = f.read()
        
        prompt = prompt_template.format(
            transaction_description=transaction_description,
            categories_str=categories_str
        )
        
        try:
            response = self.generate_completion(prompt)
            # Clean up response and validate it's in available categories
            suggested_category = response.strip()
            
            if suggested_category in available_categories:
                return suggested_category
            
            # If exact match not found, try case-insensitive match
            for category in available_categories:
                if category.lower() == suggested_category.lower():
                    return category
            
            # If no match found, return first category as fallback
            return available_categories[0] if available_categories else "Other"
            
        except OllamaAPIError as e:
            # If AI categorization fails, return a default category
            return available_categories[0] if available_categories else "Other"
    
    def get_server_info(self) -> Dict[str, Any]:
        """
        Get server information and status.
        
        Returns:
            Dictionary with server info
        """
        try:
            models = self.list_models()
            return {
                "server_url": self.base_url,
                "is_connected": True,
                "available_models": models,
                "configured_model": self.config.model,
                "model_exists": self.check_model_exists()
            }
        except OllamaAPIError as e:
            return {
                "server_url": self.base_url,
                "is_connected": False,
                "error": str(e),
                "available_models": [],
                "configured_model": self.config.model,
                "model_exists": False
            }

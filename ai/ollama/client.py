"""
Ollama Backend API Client

A simple client for interacting with Ollama server using curl commands.
Provides basic functionality for AI tasks in the expense tracking application.
"""

import json
import subprocess
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class OllamaConfig:
    """Configuration for Ollama client."""
    base_url: str = "http://localhost:11434"
    model: str = "llama2"
    timeout: int = 30


class OllamaClient:
    """Simple Ollama client using curl for API calls."""
    
    def __init__(self, config: OllamaConfig):
        """
        Initialize Ollama client with configuration.
        
        Args:
            config: OllamaConfig instance with server settings
        """
        self.config = config
        self.base_url = config.base_url.rstrip('/')
    
    def _execute_curl(self, endpoint: str, method: str = "GET", 
                     data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute curl command and return parsed JSON response.
        
        Args:
            endpoint: API endpoint (e.g., "/api/tags")
            method: HTTP method (GET, POST)
            data: JSON data for POST requests
            
        Returns:
            Parsed JSON response
            
        Raises:
            Exception: If curl command fails or returns invalid JSON
        """
        url = f"{self.base_url}{endpoint}"
        cmd = ["curl", "-s", "--connect-timeout", str(self.config.timeout)]
        
        if method == "POST":
            cmd.extend(["-X", "POST", "-H", "Content-Type: application/json"])
            if data:
                cmd.extend(["-d", json.dumps(data)])
        
        cmd.append(url)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.config.timeout)
            
            if result.returncode != 0:
                raise Exception(f"Curl command failed: {result.stderr}")
            
            if not result.stdout.strip():
                raise Exception("Empty response from server")
                
            return json.loads(result.stdout)
            
        except subprocess.TimeoutExpired:
            raise Exception(f"Request timed out after {self.config.timeout} seconds")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {e}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def test_connection(self) -> bool:
        """
        Test if Ollama server is accessible.
        
        Returns:
            True if server is accessible, False otherwise
        """
        try:
            response = self._execute_curl("/api/tags")
            return "models" in response
        except Exception:
            return False
    
    def list_models(self) -> List[str]:
        """
        Get list of available models on the server.
        
        Returns:
            List of model names
            
        Raises:
            Exception: If unable to fetch models
        """
        try:
            response = self._execute_curl("/api/tags")
            models = response.get("models", [])
            return [model.get("name", "") for model in models if model.get("name")]
        except Exception as e:
            raise Exception(f"Failed to fetch models: {str(e)}")
    
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
        except Exception:
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
            Exception: If generation fails
        """
        model_name = model or self.config.model
        
        data = {
            "model": model_name,
            "prompt": prompt,
            "stream": False  # Keep it simple for now
        }
        
        try:
            response = self._execute_curl("/api/generate", method="POST", data=data)
            return response.get("response", "")
        except Exception as e:
            raise Exception(f"Failed to generate completion: {str(e)}")
    
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
            Exception: If categorization fails
        """
        categories_str = ", ".join(available_categories)
        
        prompt = f"""
You are an expense categorization assistant. Given a transaction description, 
choose the most appropriate category from the available options.

Transaction: {transaction_description}
Available categories: {categories_str}

Respond with only the category name, nothing else.
"""
        
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
            
        except Exception as e:
            raise Exception(f"Failed to categorize transaction: {str(e)}")
    
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
        except Exception as e:
            return {
                "server_url": self.base_url,
                "is_connected": False,
                "error": str(e),
                "available_models": [],
                "configured_model": self.config.model,
                "model_exists": False
            }
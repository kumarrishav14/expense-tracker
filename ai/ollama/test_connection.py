"""
Simple test script for Ollama backend API.

Run this script to test the Ollama connection and basic functionality.
"""

from .client import OllamaClient, OllamaConfig
from .config import OllamaConfigManager


def test_ollama_connection():
    """Test Ollama server connection and basic functionality."""
    print("Testing Ollama Backend API...")
    print("-" * 40)
    
    # Load configuration
    config_manager = OllamaConfigManager()
    config = config_manager.get_client_config()
    
    print(f"Server URL: {config.base_url}")
    print(f"Model: {config.model}")
    print(f"Timeout: {config.timeout}s")
    print()
    
    # Initialize client
    client = OllamaClient(config)
    
    # Test connection
    print("1. Testing server connection...")
    if client.test_connection():
        print("✅ Server is accessible")
    else:
        print("❌ Server is not accessible")
        return False
    
    # List available models
    print("\n2. Fetching available models...")
    try:
        models = client.list_models()
        if models:
            print(f"✅ Found {len(models)} models:")
            for model in models:
                print(f"   - {model}")
        else:
            print("⚠️  No models found")
    except Exception as e:
        print(f"❌ Failed to fetch models: {e}")
        return False
    
    # Check configured model
    print(f"\n3. Checking configured model '{config.model}'...")
    if client.check_model_exists():
        print("✅ Configured model is available")
    else:
        print("❌ Configured model is not available")
        print("Available models:", models)
        return False
    
    # Test simple completion
    print("\n4. Testing text generation...")
    try:
        prompt = "What is 2+2? Answer with just the number."
        response = client.generate_completion(prompt)
        print(f"✅ Generated response: '{response.strip()}'")
    except Exception as e:
        print(f"❌ Failed to generate text: {e}")
        return False
    
    # Test transaction categorization
    print("\n5. Testing transaction categorization...")
    try:
        categories = ["Food", "Transport", "Entertainment", "Shopping", "Other"]
        transaction = "McDonald's Restaurant Purchase"
        category = client.categorize_transaction(transaction, categories)
        print(f"✅ Transaction '{transaction}' categorized as: '{category}'")
    except Exception as e:
        print(f"❌ Failed to categorize transaction: {e}")
        return False
    
    # Get server info
    print("\n6. Getting server information...")
    info = client.get_server_info()
    print("✅ Server info:")
    for key, value in info.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 40)
    print("✅ All tests passed! Ollama backend is ready.")
    return True


if __name__ == "__main__":
    test_ollama_connection()
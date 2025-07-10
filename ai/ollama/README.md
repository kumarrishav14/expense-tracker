# Ollama Backend API

Simple Ollama integration for the expense tracking application.

## Overview

This module provides a lightweight interface to interact with Ollama server for AI-powered expense categorization and other AI tasks.

## Features

- **Simple Configuration**: Easy setup via config files or environment variables
- **Connection Testing**: Test server connectivity and model availability
- **Transaction Categorization**: AI-powered expense categorization
- **Error Handling**: Graceful fallbacks when AI is unavailable

## Quick Start

### 1. Basic Usage

```python
from ai.ollama import get_ollama_client, is_ollama_available

# Check if Ollama is available
if is_ollama_available():
    client = get_ollama_client()
    
    # Categorize a transaction
    categories = ["Food", "Transport", "Shopping", "Other"]
    category = client.categorize_transaction("McDonald's Purchase", categories)
    print(f"Suggested category: {category}")
```

### 2. Configuration

Create `ollama_config.json` in your app root:

```json
{
  "base_url": "http://localhost:11434",
  "model": "llama2",
  "timeout": 30,
  "enabled": true
}
```

Or use environment variables:
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `OLLAMA_TIMEOUT`
- `OLLAMA_ENABLED`

### 3. Testing Connection

```python
from ai.ollama.test_connection import test_ollama_connection

# Run comprehensive tests
test_ollama_connection()
```

## API Reference

### OllamaClient

Main client class for interacting with Ollama server.

**Methods:**
- `test_connection()` - Test server connectivity
- `list_models()` - Get available models
- `check_model_exists(model_name)` - Check if model exists
- `generate_completion(prompt)` - Generate text completion
- `categorize_transaction(description, categories)` - Categorize expense
- `get_server_info()` - Get server status and info

### OllamaFactory

Factory for managing client instances.

**Methods:**
- `get_client()` - Get client instance
- `is_available()` - Check availability
- `update_settings(settings)` - Update configuration

### Configuration

**OllamaSettings:**
- `base_url` - Ollama server URL (default: http://localhost:11434)
- `model` - Model name (default: llama2)
- `timeout` - Request timeout in seconds (default: 30)
- `enabled` - Enable/disable Ollama integration (default: true)

## Integration with Streamlit

This module is designed to integrate seamlessly with Streamlit settings:

```python
import streamlit as st
from ai.ollama import OllamaFactory, OllamaSettings

# In your Streamlit settings page
st.subheader("AI Settings")

base_url = st.text_input("Ollama Server URL", value="http://localhost:11434")
model = st.text_input("Model Name", value="llama2")
enabled = st.checkbox("Enable AI Categorization", value=True)

if st.button("Save AI Settings"):
    settings = OllamaSettings(
        base_url=base_url,
        model=model,
        enabled=enabled
    )
    OllamaFactory.update_settings(settings)
    st.success("Settings saved!")
```

## Error Handling

The module includes graceful error handling:
- Falls back to default categories when AI fails
- Provides clear error messages for debugging
- Includes connection timeouts and retries

## Requirements

- `curl` command available in system PATH
- Ollama server running and accessible
- Python 3.12+

## Notes

- Uses `curl` for HTTP requests (simple and reliable)
- Implements singleton pattern for client instances
- Designed for personal use (simple and straightforward)
- No external HTTP libraries required
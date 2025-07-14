
import pytest
from unittest.mock import MagicMock, patch
from ai.ollama.client import OllamaClient, OllamaConfig, OllamaConnectionError, OllamaAPIError, OllamaTimeoutError
import requests

@pytest.fixture
def mock_config():
    """Fixture for a standard OllamaConfig."""
    return OllamaConfig(base_url="http://mock-server:11434", model="test-model", timeout=5)

@pytest.fixture
def ollama_client(mock_config):
    """Fixture for an OllamaClient instance with the mock config."""
    return OllamaClient(mock_config)

# 1. Tests for _execute_request

def test_execute_request_get_success(mocker, ollama_client):
    """Test that _execute_request successfully handles a GET request."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "ok"}
    mocker.patch('requests.get', return_value=mock_response)
    
    response = ollama_client._execute_request("/api/test")
    
    requests.get.assert_called_once_with("http://mock-server:11434/api/test", timeout=5)
    assert response == {"status": "ok"}

def test_execute_request_post_success(mocker, ollama_client):
    """Test that _execute_request successfully handles a POST request."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "created"}
    mocker.patch('requests.post', return_value=mock_response)
    
    response = ollama_client._execute_request("/api/create", method="POST", data={"key": "value"})
    
    requests.post.assert_called_once_with("http://mock-server:11434/api/create", json={"key": "value"}, timeout=5)
    assert response == {"status": "created"}

def test_execute_request_raises_connection_error(mocker, ollama_client):
    """Test that OllamaConnectionError is raised on a connection failure."""
    mocker.patch('requests.get', side_effect=requests.exceptions.ConnectionError("Failed to connect"))
    
    with pytest.raises(OllamaConnectionError, match="Connection to http://mock-server:11434 failed"):
        ollama_client._execute_request("/api/test")

def test_execute_request_raises_timeout_error(mocker, ollama_client):
    """Test that OllamaTimeoutError is raised on a timeout."""
    mocker.patch('requests.get', side_effect=requests.exceptions.Timeout("Request timed out"))
    
    with pytest.raises(OllamaTimeoutError, match="Request timed out after 5 seconds"):
        ollama_client._execute_request("/api/test")

def test_execute_request_raises_api_error_on_http_error(mocker, ollama_client):
    """Test that OllamaAPIError is raised on an HTTP 4xx/5xx error."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
    mocker.patch('requests.get', return_value=mock_response)
    
    with pytest.raises(OllamaAPIError, match="HTTP error occurred: 404 - Not Found"):
        ollama_client._execute_request("/api/test")

# 2. Tests for test_connection

def test_test_connection_success(mocker, ollama_client):
    """Test test_connection returns True when the server is accessible and returns valid JSON."""
    mocker.patch.object(ollama_client, '_execute_request', return_value={"models": []})
    assert ollama_client.test_connection() is True

def test_test_connection_failure_on_connection_error(mocker, ollama_client):
    """Test test_connection returns False if an OllamaConnectionError is raised."""
    mocker.patch.object(ollama_client, '_execute_request', side_effect=OllamaConnectionError)
    assert ollama_client.test_connection() is False

def test_test_connection_failure_on_api_error(mocker, ollama_client):
    """Test test_connection returns False if an OllamaAPIError is raised."""
    mocker.patch.object(ollama_client, '_execute_request', side_effect=OllamaAPIError)
    assert ollama_client.test_connection() is False

# 3. Tests for list_models

def test_list_models_success(mocker, ollama_client):
    """Test list_models returns a list of model names from the API response."""
    mock_response = {"models": [{"name": "model-one:latest"}, {"name": "model-two:latest"}]}
    mocker.patch.object(ollama_client, '_execute_request', return_value=mock_response)
    
    models = ollama_client.list_models()
    
    assert models == ["model-one:latest", "model-two:latest"]

def test_list_models_raises_api_error(mocker, ollama_client):
    """Test list_models raises an OllamaAPIError if the underlying request fails."""
    mocker.patch.object(ollama_client, '_execute_request', side_effect=OllamaConnectionError("Connection failed"))
    
    with pytest.raises(OllamaAPIError, match="Failed to fetch models: Connection failed"):
        ollama_client.list_models()

# 4. Tests for check_model_exists

def test_check_model_exists_returns_true(mocker, ollama_client):
    """Test check_model_exists returns True when the configured model is in the list."""
    mocker.patch.object(ollama_client, 'list_models', return_value=["other-model", "test-model"])
    assert ollama_client.check_model_exists() is True

def test_check_model_exists_returns_false(mocker, ollama_client):
    """Test check_model_exists returns False when the configured model is not in the list."""
    mocker.patch.object(ollama_client, 'list_models', return_value=["other-model", "another-model"])
    assert ollama_client.check_model_exists() is False

def test_check_model_exists_with_specific_model_returns_true(mocker, ollama_client):
    """Test check_model_exists returns True for a specific model that exists."""
    mocker.patch.object(ollama_client, 'list_models', return_value=["specific-model", "test-model"])
    assert ollama_client.check_model_exists("specific-model") is True

def test_check_model_exists_returns_false_on_api_error(mocker, ollama_client):
    """Test check_model_exists returns False if list_models raises an API error."""
    mocker.patch.object(ollama_client, 'list_models', side_effect=OllamaAPIError)
    assert ollama_client.check_model_exists() is False

# 5. Tests for get_server_info

def test_get_server_info_success(mocker, ollama_client):
    """Test get_server_info returns a complete success dictionary when connected."""
    mocker.patch.object(ollama_client, 'list_models', return_value=["test-model"])
    mocker.patch.object(ollama_client, 'check_model_exists', return_value=True)
    
    info = ollama_client.get_server_info()
    
    assert info == {
        "server_url": "http://mock-server:11434",
        "is_connected": True,
        "available_models": ["test-model"],
        "configured_model": "test-model",
        "model_exists": True
    }

def test_get_server_info_failure(mocker, ollama_client):
    """Test get_server_info returns a failure dictionary when not connected."""
    mocker.patch.object(ollama_client, 'list_models', side_effect=OllamaAPIError("Connection failed"))
    
    info = ollama_client.get_server_info()
    
    assert info == {
        "server_url": "http://mock-server:11434",
        "is_connected": False,
        "error": "Connection failed",
        "available_models": [],
        "configured_model": "test-model",
        "model_exists": False
    }

# Ollama Module: Future Scaling for Multi-Model Support

**Author:** AI Architect
**Date:** July 10, 2025

## 1. Assessment of Multi-Model Capability

This document assesses the `ai.ollama` module's current capability to handle multiple Large Language Models (LLMs) for different use cases and outlines a potential path for future enhancements.

### Current State:
The current implementation has a **foundational but not yet optimized** capability to handle multiple models.

#### What Works Now:
The core `generate_completion` method in `OllamaClient` is designed to accept an optional `model` parameter:
```python
def generate_completion(self, prompt: str, model: Optional[str] = None, ...)
```
This is a crucial piece of foresight. It allows a developer to override the default model specified in the configuration for any individual API call. For example, one could use a powerful model for analysis and a faster, smaller model for simple categorization, just by passing the model name during the function call.

### Architectural Limitations for the Future:
While the immediate capability exists, the architecture is primarily designed around a single, default model. If using multiple models becomes a common pattern, the following limitations will become apparent:

1.  **Configuration:** The `OllamaSettings` and `ollama_config.json` are designed to hold only a single `model` name. There is no way to define and manage a mapping of use cases to specific models (e.g., `categorization_model: "llama3-8b"`, `summary_model: "mistral"`).
2.  **Hardcoded Model Names:** To use a different model, the developer must hardcode the model name (e.g., `"mistral"`) directly in the application logic. This mixes configuration with code, making it harder to manage and update model choices.

## 2. Recommended Future Evolution (No Action Needed Now)

When the need for first-class multi-model support arises, the architecture can be evolved. The path would look something like this:

### Step 1: Evolve the Configuration
Modify `OllamaSettings` in `config.py` to support a dictionary of models instead of a single string. This would allow for defining task-specific models in the configuration file.

**From:**
```python
# in OllamaSettings
model: str = "llama2"
```

**To:**
```python
# in OllamaSettings
from dataclasses import field
from typing import Dict

models: Dict[str, str] = field(default_factory=lambda: {
    "default": "llama2",
    "categorization": "llama2",
    "summarization": "mistral"
})
```

### Step 2: Refine the Client
The `OllamaClient` could be enhanced with methods that are aware of these use cases. A new method could be added to look up the correct model from the configuration based on a `task_name`.

**Example:**
```python
# New method in OllamaClient
def generate_for_task(self, task_name: str, prompt: str) -> str:
    """
    Generates a completion for a specific, pre-configured task.
    """
    # Look up the model from the config, with a fallback to default
    model_name = self.config.models.get(task_name, self.config.models.get("default"))
    
    if not model_name:
        raise ValueError(f"No model configured for task '{task_name}' or a default model.")

    # Call the existing method with the resolved model name
    return self.generate_completion(prompt, model=model_name)
```

## 3. Conclusion

**Yes, the backend is technically capable of handling multiple models today.** The design is flexible enough to allow it on a call-by-call basis.

However, to support this pattern elegantly and maintainably in the future, the configuration and client logic should be evolved to treat multiple models as a first-class concept. The current architecture is perfectly adequate for now, and the foresight to include the optional `model` parameter is a significant strength.

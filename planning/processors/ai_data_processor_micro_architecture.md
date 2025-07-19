# AI-Powered Data Processor Micro-Architecture

**Author:** AI Architect
**Date:** July 18, 2025
**Version:** 2.2

## 1. Component Overview

This document defines the micro-architecture for the `AIDataProcessor`. This component serves as an advanced, AI-driven alternative to the standard `RuleBasedDataProcessor`. It leverages a Large Language Model (LLM) via the `OllamaClient` to perform both the structuring and categorization of raw transaction data in a single, intelligent step.

Its primary goal is to handle a wide variety of inconsistent and unpredictable bank statement formats without requiring hard-coded rules.

**Version 2.2 Update:** This version refines the batch processing model to include a **configurable retry mechanism** to handle transient errors, ensuring a higher success rate for large files while maintaining architectural simplicity.

## 2. Architectural Pattern: Strategy, Decorator, and Callback

This processor follows three key patterns:

1.  **Strategy Pattern:** It adheres to the `AbstractDataProcessor` interface, making it interchangeable with any other processor.
2.  **Decorator Pattern:** Its `process_raw_data` method is wrapped by the `@enforce_output_schema` decorator, which **guarantees** that its final, aggregated output DataFrame conforms to the application-wide standard schema.
3.  **Callback Pattern:** The `process_raw_data` method accepts an optional `on_progress` callback function. This allows the processor to report its progress to the calling layer (e.g., the UI) without creating a tight coupling between the backend and the frontend.

## 3. Position in System Architecture

The processor's position remains the same. It takes raw data from parsers and produces a standardized DataFrame for the `DBInterface`.

```
┌─────────────────────────────────────────────────────────────────┐
│                    FILE PARSERS                                 │
└─────────────┬───────────────────────────────────────────────────┘
              │ Raw pandas DataFrame (any column names/structure)
┌─────────────▼───────────────────────────────────────────────────┐
│                  AI_DATA_PROCESSOR COMPONENT                    │
│  • **Splits data into batches**                                 │
│  • Loops through batches, calling LLM for each                  │
│  • **Invokes progress callback after each batch**               │
│  • Aggregates results into a final DataFrame                    │
└─────────────┬───────────────────────────────────────────────────┘
              │ Standardized DataFrame (guaranteed by decorator)
┌─────────────▼───────────────────────────────────────────────────┐
│                  DB_INTERFACE COMPONENT                         │
└─────────────────────────────────────────────────────────────────┘
```

## 4. Core Responsibilities

| Responsibility | Description |
|---|---|
| **Batch Processing** | **(New)** Splits large input DataFrames into smaller, manageable chunks to ensure reliable processing by the LLM. |
| **Retry Logic** | **(New)** For each chunk, retries the processing step up to a configurable number of times if an error occurs. |
| **Progress Reporting** | **(New)** Invokes an optional callback function to report the status (success or failure) of each batch. |
| **Category Transformation** | Transform the normalized `(name, parent_category)` DataFrame from the `DBInterface` into a hierarchical dictionary suitable for prompt engineering. |
| **Data Serialization** | Convert an input pandas DataFrame *chunk* into a simple text format (e.g., CSV) for the LLM. |
| **Prompt Engineering** | Dynamically construct a detailed prompt for each chunk. |
| **LLM Communication** | Use the `OllamaClient` to send the prompt to the LLM and receive the response for each chunk. |
| **Content Validation** | Use a Pydantic model to validate the content, structure, and data types of each individual record in the JSON response from the LLM. |
| **DataFrame Conversion** | Convert the list of validated Pydantic objects from a chunk's response into a pandas DataFrame. |

## 5. Component Logic and Sequence (Batch with Retries)

The internal logic is a nested loop: an outer loop for batches and an inner loop for retries.

```mermaid
sequenceDiagram
    participant Caller as Application Layer
    participant Decorator as @enforce_output_schema
    participant AIDP as AIDataProcessor

    Caller->>+Decorator: 1. process_raw_data(raw_df, on_progress=callback_func)
    Decorator->>+AIDP: 2. Calls the wrapped method

    AIDP->>AIDP: 3. Splits raw_df into chunks
    Note right of AIDP: Initializes successful_results = []

    loop For each chunk
        loop Up to MAX_RETRIES + 1 times
            Note right of AIDP: Attempting to process chunk...
            alt Processing is Successful
                AIDP->>AIDP: Add results to successful_results
                AIDP-->>Caller: on_progress(progress, "Success on batch X")
                break
            end
        end
        
        alt Chunk still failed after all retries
             Note right of AIDP: Log error and discard chunk data.
             AIDP-->>Caller: on_progress(progress, "Error on batch X after retries. Skipping.")
        end
    end

    AIDP->>AIDP: 10. Combines all successful results into a single DataFrame
    AIDP-->>-Decorator: 11. Returns final DataFrame

    Decorator->>Decorator: 12. Enforces final schema on the aggregated DataFrame
    Decorator-->>-Caller: 13. Returns final, guaranteed-schema DataFrame
```

### **Category Data Transformation (`_prepare_category_prompt_data`)**

This new private helper method is critical for creating an effective prompt.

-   **Input**: A pandas DataFrame from `db_interface.get_categories_table()` with columns `['name', 'parent_category']`.
-   **Logic**:
    1.  Initialize an empty dictionary, `hierarchy = {}`.
    2.  Iterate through the DataFrame to identify all unique parent categories and initialize them as keys with empty lists (e.g., `{'Food': [], 'Travel': []}`).
    3.  Iterate through the DataFrame again. For each row with a `parent_category`, append its `name` to the corresponding list in the dictionary.
-   **Output**: A dictionary structured for the LLM, like:
    ```json
    {
      "Food": ["Groceries", "Restaurant"],
      "Utilities": [],
      "Travel": ["Flights", "Hotels"]
    }
    ```

### **Developer Implementation Notes**

To allow for easy tuning without changing core logic, the following should be defined as configurable variables at the top of the `ai_data_processor.py` file:

*   **`BATCH_SIZE`**: The number of rows in each chunk. A default of `25` is recommended.
*   **`MAX_RETRIES`**: The number of extra attempts to make on a failed batch. A default of `1` is recommended.

## 6. Decoupling via the Callback Pattern

The user's concern about creating overdependence is valid. The callback pattern is the ideal solution because it **inverts control**.

*   **Without Callback (Tight Coupling):** The processor would need to know about the UI. It might have code like `from frontend import progress_bar` and `progress_bar.update(...)`. This is a major architectural violation.
*   **With Callback (Decoupled):** The processor knows nothing about the UI. It only knows about a generic function (`on_progress`) that it must call. The UI, which *does* know about its own progress bar, is responsible for creating a function that can update it and passing that function to the processor.

This maintains a strict separation of concerns. The backend processor is completely independent of any frontend implementation.

## 7. Two-Level Validation Details

### Level 1: Content Validation (Pydantic Model)

The `AIDataProcessor` **must** use a Pydantic model to validate the content of each record returned by the LLM. This ensures data integrity.

```python
# To be defined in core/processors/schema.py
from pydantic import BaseModel
from datetime import date

class StandardTransaction(BaseModel):
    description: str
    transaction_date: date
    amount: float
    category: str = "Other"
    sub_category: str = ""
```

### Level 2: Schema Enforcement (Decorator)

The `@enforce_output_schema` decorator provides a final, lightweight guarantee. It trusts that the processor has cleaned the data, and it simply enforces the final DataFrame structure (column names, order, dtypes) to ensure it matches the `DBInterface` contract.

## 8. Interface and Output Contract

The method signature is updated to include the optional callback, but the primary return type is unchanged.

```python
# In core/processors/abstract_processor.py
from typing import Callable, Optional
import pandas as pd

class AbstractDataProcessor(ABC):
    
    @abstractmethod
    @enforce_output_schema
    def process_raw_data(
        self, 
        df: pd.DataFrame, 
        on_progress: Optional[Callable[[float, str], None]] = None
    ) -> pd.DataFrame:
        """
        Processes a raw DataFrame and returns a standardized DataFrame.
        
        Args:
            df: A raw pandas DataFrame from a file parser.
            on_progress: An optional callback function to report progress.
                         It receives (progress: float, message: str).

        Returns:
            A standardized pandas DataFrame with a guaranteed schema.
        """
        pass
```

## 9. Error Handling

*   **Transient Errors:** Handled by the retry mechanism.
*   **Persistent Batch Errors:** If a batch fails after all retry attempts, the error is logged, the failure is reported via the `on_progress` callback, and the data for that batch is **discarded**. The processor then moves to the next batch.
*   **Schema Enforcement Failure:** This remains a critical error. If the final, aggregated DataFrame cannot be conformed to the schema by the decorator, it will raise a `SchemaValidationError`.
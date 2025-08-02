# ADR-001: Enhanced Processor Interface for Account and Statement Context

**Status:** Proposed  
**Date:** 2025-01-15  
**Deciders:** AI Architect  
**Technical Story:** Integration of Account Management and Credit Mapping features requires processors to handle account context and statement metadata.

## Context and Problem Statement

The current `AbstractDataProcessor` interface lacks account context and statement awareness required for new features. The interface must evolve to support account assignment, statement metadata, and transfer detection while maintaining **contract enforcement** across all processor implementations.

**Why Abstract Class:** Using `AbstractDataProcessor` ensures that any new processor developed for input processing (Rule-Based, AI-powered, or future implementations) **must** implement the same input/output contract. This architectural constraint prevents interface drift and guarantees consistent behavior across all processing strategies.

## Decision Drivers

- **Contract Enforcement:** All processors must handle identical data contracts
- **Feature Integration:** Account Management and Credit Mapping depend on processor-level context
- **Schema Compliance:** New database schema requires additional fields
- **Architectural Consistency:** Prevent interface fragmentation across processor implementations

## Decision

**Enhanced Abstract Interface** with mandatory account context:

```python
@abstractmethod
@enforce_output_schema
def process_raw_data(
    self, 
    df: pd.DataFrame, 
    account_id: int,
    statement_metadata: Optional[Dict] = None,
    on_progress: Optional[Callable[[float, str], None]] = None
) -> pd.DataFrame:
```

**Enhanced Output Schema:**
```python
# Current schema (from abstract_processor.py)
current_columns = [
    'description', 'amount', 'transaction_date', 'category', 'sub_category'
]

# Enhanced schema with new required columns
enhanced_columns = [
    'description',       # Transaction description
    'amount',           # Transaction amount  
    'transaction_date', # Transaction date
    'category',         # Category name
    'sub_category',     # Sub-category name 
    'account_id',       # NEW: Account ID (mandatory)
    'is_transfer'       # NEW: Transfer flag (default False)
]

# Optional columns for future features
optional_columns = [
    'statement_id',     # NEW: For credit card transactions
    'transfer_id'       # NEW: For linked transfers (initially None)
]
```

## Rationale

- **Contract Enforcement:** Abstract class forces all processors to implement identical interface
- **Account-Centric Processing:** Mandatory `account_id` ensures all transactions have account context
- **Feature Enablement:** Interface supports Account Management and Credit Mapping requirements
- **Consistency:** Single interface prevents processor implementations from diverging

## Consequences

### Positive:
- **Feature Enablement:** Enables Account Management and Credit Mapping features
- **Data Integrity:** Ensures all transactions have proper account context
- **Consistency:** Standardizes progress reporting across all processors
- **Future-Proofing:** Interface can accommodate additional context as needed

### Negative:
- **Breaking Change:** All existing processor implementations must be updated
- **Complexity:** Processors must handle additional responsibilities
- **Testing Impact:** All processor tests need updates for new interface

### Neutral:
- **Migration Required:** All three processors (Rule-Based, AI, Enhanced AI) need updates
- **Frontend Integration:** Upload workflow must provide account context to processors

## Architectural Impact

### Interface Evolution
The enhanced interface represents a **fundamental shift** from transaction-only processing to **context-aware processing**. This architectural change enables:

- **Account-Centric Data Model:** All transactions must be associated with accounts
- **Statement Lifecycle Integration:** Processors become aware of statement metadata and types
- **Transfer Detection Framework:** Processors gain responsibility for identifying potential transfers
- **Progress Transparency:** Standardized progress reporting across all processing strategies

### Separation of Concerns Validation
This change maintains proper architectural boundaries:

- **Processors (Business Logic Layer):** Responsible for data transformation, context assignment, and business rule application
- **Database Layer:** Remains focused on pure data persistence operations
- **Frontend Layer:** Provides context but delegates processing logic to appropriate layer

### System Integration Points
The enhanced interface creates new integration requirements:

- **Upload Workflow:** Must provide account context before processing
- **Account Management:** Must integrate with processor layer for smart onboarding
- **Credit Mapping:** Depends on processor-level transfer detection capabilities

## Compliance Notes

This ADR maintains architectural separation of concerns:
- **Processors:** Handle business logic for data transformation and context assignment
- **Database Layer:** Remains focused on pure data access operations
- **Frontend:** Provides context but doesn't handle data transformation logic

The enhanced interface keeps processors as the appropriate layer for account context assignment and transfer detection logic.
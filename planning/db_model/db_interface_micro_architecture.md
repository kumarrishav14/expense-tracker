# Database Interface Micro-Architecture

## **Component Overview**

The `db_interface` component serves as the **Simple Data Access Layer** in the personal expense tracking system. It provides clean, filtered access to raw data and handles data persistence, while leaving all business logic and data processing to individual components.

## **Position in System Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │  Dashboard  │ │  Analysis   │ │ AI Chatbot  │               │
│  │     Tab     │ │     Tab     │ │     Tab     │               │
│  │ ┌─────────┐ │ │ ┌─────────┐ │ │ ┌─────────┐ │               │
│  │ │Dashboard│ │ │ │Analysis │ │ │ │Chatbot  │ │               │
│  │ │Processor│ │ │ │Processor│ │ │ │Processor│ │               │
│  │ └─────────┘ │ │ └─────────┘ │ │ └─────────┘ │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
└─────────────┬───────────────┬───────────────┬─────────────────┘
              │               │               │
              └───────────────▼───────────────┘
┌─────────────────────────────────────────────────────────────────┐
│              DB_INTERFACE COMPONENT                             │
│              (Simple Data Access Layer)                        │
│  • Raw data access with basic filtering                        │
│  • Data persistence operations                                 │
│  • DataFrame ↔ Database translation                            │
└─────────────┬───────────────────────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────────────────────┐
│              DATABASE LAYER (SQLAlchemy + SQLite)               │
└─────────────────────────────────────────────────────────────────┘
```

## **Core Responsibilities Matrix**

| Responsibility Category | Specific Functions | Components Served |
|------------------------|-------------------|-------------------|
| **Raw Data Access** | Get transactions/categories with basic filters | All UI Components |
| **Data Persistence** | Save operations with transaction management | Data Pipeline, UI |
| **Data Translation** | DataFrame ↔ ORM conversion | All UI Components |
| **Basic Filtering** | Date range, category, amount filters | All UI Components |
| **Database Error Handling** | Database constraint and connection errors | All Components |
| **Category Management** | Hierarchy auto-creation | Statement Input, Settings |

## **What db_interface Does NOT Handle**

| Responsibility | Owner Component | Rationale |
|----------------|-----------------|-----------|
| **Business Logic Validation** | Data Processor | Domain-specific rules |
| **Data Quality Validation** | Data Processor | Completeness, accuracy checks |
| **Format Validation** | Data Processor | Date formats, number formats |
| **Duplicate Detection** | Data Processor | Business logic responsibility |
| **Data Analysis** | Dashboard/Analysis Processors | Component-specific calculations |
| **AI Insights** | AI Chatbot Component | Domain-specific processing |
| **Complex Aggregations** | UI Component Processors | Better performance and modularity |
| **Visualization Logic** | UI Components | Presentation layer responsibility |

## **DataFrame Contracts (Data API)**

### **Raw DataFrames Provided**

#### **1. Transactions DataFrame**
```python
transactions_df: pd.DataFrame
Columns:
├─ description: str (optional, transaction description)
├─ amount: float (required, transaction amount)
├─ transaction_date: datetime (required, when transaction occurred)
├─ category: str (optional, main category name)
└─ sub_category: str (optional, sub-category name)

Usage: Raw data for all UI components to process as needed
```

#### **2. Categories DataFrame**
```python
categories_df: pd.DataFrame
Columns:
├─ name: str (category name)
└─ parent_category: str (parent name, null for top-level)

Usage: Raw category hierarchy for components to analyze and display
```

**Note**: All analysis, aggregations, insights, and complex processing are handled by individual UI components, not by db_interface.

## **Component Internal Architecture**

### **Class Structure**

```python
class DatabaseInterface:
    """Simple data access layer providing raw data with basic filtering"""
    
    # Core Data Management
    def __init__(self, db_url: str)
    def get_session(self) -> Session
    
    # Raw Data Access Methods (Database → DataFrames)
    def get_transactions_table(
        self,
        date_range: Tuple[date, date] = None,
        categories: List[str] = None,
        amount_range: Tuple[float, float] = None,
        limit: int = None
    ) -> pd.DataFrame
    
    def get_categories_table(self) -> pd.DataFrame
    
    # Data Persistence Methods (DataFrames → Database)
    def save_transactions_table(self, df: pd.DataFrame) -> OperationResult
    def save_categories_table(self, df: pd.DataFrame) -> OperationResult
    
    # Batch operations with detailed error reporting
    def save_transactions_batch(self, df: pd.DataFrame) -> BatchOperationResult
    
    # Category Management
    def create_category_hierarchy(self, category: str, sub_category: str) -> bool
    def bulk_categorize_transactions(self, predictions_df: pd.DataFrame) -> OperationResult
    
    # Transaction Management
    def begin_transaction(self) -> TransactionContext
    def rollback_transaction(self, context: TransactionContext)
    def commit_transaction(self, context: TransactionContext)
```

### **Internal Data Flow**

```
Component Request → Apply Basic Filters → Database Query → ORM Objects → DataFrame Conversion → Return Raw DataFrame
                                                                                                    ↓
                                                                                        Component Processes Data
```

## **Caching Strategy**

### **Simplified Caching Architecture**

```python
Cache Strategy:
├─ Streamlit Session State:
│   ├─ Raw transactions DataFrame
│   └─ Categories DataFrame
├─ Database Connection Pooling:
│   └─ SQLAlchemy connection cache
└─ Component-Level Caching:
    └─ Each UI component caches its own processed data
```

### **Cache Invalidation Strategy**

```python
Cache Invalidation Rules:
├─ Data Modification Events:
│   ├─ Transaction save → Invalidate raw transactions cache
│   └─ Category changes → Invalidate categories cache
└─ Manual Invalidation:
    ├─ User refresh action
    └─ Component-specific cache clearing
```

## **Error Handling Architecture**

### **Error Classification & Response**

```python
Error Handling Matrix:
├─ DatabaseConnectionError:
│   ├─ Response: Retry with exponential backoff
│   ├─ Fallback: Use cached DataFrames
│   └─ User Message: "Connection issue, showing cached data"
├─ DatabaseConstraintError:
│   ├─ Foreign Key Violations: Category ID doesn't exist
│   ├─ Unique Constraint Violations: Duplicate primary keys
│   ├─ Check Constraint Violations: Invalid data ranges
│   ├─ Not Null Violations: Required database fields missing
│   ├─ Response: Return detailed constraint error (no retry)
│   ├─ Fallback: None (data must be fixed by Data Processor)
│   └─ User Message: Specific constraint violation details
├─ TransactionError:
│   ├─ Response: Full rollback, preserve original state
│   ├─ Fallback: Restore from cache
│   └─ User Message: "Operation failed, no changes made"
└─ CacheError:
    ├─ Response: Invalidate cache, reload from database
    ├─ Fallback: Direct database access
    └─ User Message: "Refreshing data..."
```

### **Simplified Operation Result Structure**

```python
@dataclass
class OperationResult:
    success: bool
    operation: str  # "save_transactions", "save_categories"
    affected_rows: int = 0
    error_message: Optional[str] = None
    error_type: Optional[str] = None  # "connection", "constraint", "transaction"
    
# For batch operations with detailed errors
@dataclass
class BatchOperationResult(OperationResult):
    failed_rows: List[int] = None  # Row indices that failed
    constraint_violations: List[str] = None  # Specific constraint details
```

### **Retry Strategy by Error Type**

```python
Retry Decision Matrix:
├─ Retryable Errors (Auto-retry with backoff):
│   ├─ DatabaseConnectionError: Connection timeout, database unavailable
│   ├─ TransactionError: Deadlock, temporary lock conflicts
│   └─ SessionError: Session management issues
├─ Non-Retryable Errors (Return immediately):
│   ├─ DatabaseConstraintError: Foreign key, unique, check constraints
│   ├─ DataStructureError: Missing columns, invalid DataFrame
│   └─ PermissionError: Database access denied
```

## **Transaction Management**

### **Atomic Operation Pattern**

```python
Transaction Scope Implementation:
├─ Begin Transaction Context
├─ Check Basic DataFrame Structure (columns present)
├─ Execute All Database Operations
├─ Handle Database Constraint Violations
├─ Commit Transaction
└─ Notify Dependent Components

Rollback Scenarios:
├─ Database constraint violation → Full rollback
├─ Connection failure → Full rollback
├─ Transaction conflict → Full rollback
└─ Component notification failure → Log warning, continue

Note: Data validation is handled by Data Processor before reaching db_interface
```

### **Batch Processing Strategy**

```python
Batch Operation Handling:
├─ Small Batches (< 100 rows):
│   ├─ Single transaction, all-or-nothing
│   ├─ Return simple OperationResult
│   └─ On constraint error: rollback, return detailed error
├─ Medium Batches (100-1000 rows):
│   ├─ Single transaction with detailed error tracking
│   ├─ Return BatchOperationResult with failed row indices
│   └─ On constraint error: rollback, return specific violations
└─ Large Batches (> 1000 rows):
    ├─ Chunked transactions (500 rows each)
    ├─ Continue processing remaining chunks on partial failure
    └─ Return BatchOperationResult with comprehensive error details

Constraint Error Handling:
├─ No Retry: Constraint violations require data fixes
├─ Detailed Reporting: Specific constraint and row information
├─ Rollback Strategy: Full rollback for single transaction
└─ User Action Required: Fix data in Data Processor and retry
```

## **Component Integration Patterns**

### **UI Component Integration**

```python
# Dashboard Tab Integration
raw_transactions = db_interface.get_transactions_table(
    date_range=(start_date, end_date)
)
# Dashboard processes its own data
monthly_summary = dashboard_processor.calculate_monthly_summary(raw_transactions)
spending_by_category = dashboard_processor.group_by_category(raw_transactions)

# Statement Input Integration (via Data Pipeline)
result = db_interface.save_transactions_table(processed_df)
if result.success:
    # Trigger UI refresh across all tabs
    st.rerun()

# Settings Tab Integration
categories_df = db_interface.get_categories_table()
# User modifies categories
result = db_interface.save_categories_table(modified_df)

# Analysis Tab Integration
raw_transactions = db_interface.get_transactions_table()
# Analysis Tab does its own complex processing
trend_analysis = analysis_processor.calculate_trends(raw_transactions)
custom_filters = analysis_processor.apply_user_filters(raw_transactions, filters)
```

### **AI Backend Integration**

```python
# AI Category Prediction
uncategorized_transactions = db_interface.get_transactions_table(
    categories=[]  # Filter for uncategorized transactions
)
# AI processes and returns predictions
predictions_df = ai_backend.predict_categories(uncategorized_transactions)
result = db_interface.bulk_categorize_transactions(predictions_df)

# AI Chatbot Integration
all_transactions = db_interface.get_transactions_table()
# AI Chatbot processes data and generates insights internally
chatbot_response = ai_chatbot.process_query(user_query, all_transactions)
```

### **Data Pipeline Integration**

```python
# File Processing Pipeline
parsed_data = file_parser.parse(uploaded_file)
validated_data = data_processor.validate_and_clean(parsed_data)
result = db_interface.save_transactions_table(validated_data)

# Error handling with detailed feedback
if not result.success:
    for error in result.error_details:
        st.error(f"Row {error.row_index}: {error.message}")
```

## **Performance Considerations (Personal Use)**

### **Simple Performance Guidelines**

```python
Basic Performance Approach:
├─ Load all data by default (personal datasets are small)
├─ Simple caching in Streamlit session state
├─ Basic database indexes on primary keys
└─ No complex optimization needed for personal use

Note: Advanced performance optimization moved to future phases
```

## **Simple Logging (Personal Use)**

### **Basic Logging Strategy**

```python
Essential Logging Only:
├─ ERROR: Failed operations, database errors
├─ WARNING: Retry attempts, constraint violations
└─ INFO: Successful batch operations

Note: Detailed monitoring and metrics moved to future phases
```

## **Testing Strategy**

### **Unit Testing**

```python
Test Categories:
├─ DataFrame Conversion Tests:
│   ├─ ORM → DataFrame transformation
│   ├─ DataFrame → ORM transformation
│   └─ Data type preservation
├─ Cache Management Tests:
│   ├─ Cache invalidation logic
│   ├─ Cache hit/miss scenarios
│   └─ Memory usage limits
├─ Error Handling Tests:
│   ├─ Database connection failures
│   ├─ Database constraint errors
│   └─ Transaction rollback scenarios
└─ Performance Tests:
    ├─ Large dataset handling
    ├─ Concurrent access patterns
    └─ Memory usage under load
```

### **Integration Testing**

```python
Integration Scenarios:
├─ UI Component Integration:
│   ├─ Multi-tab data consistency
│   ├─ Real-time data updates
│   └─ Error propagation to UI
├─ AI Backend Integration:
│   ├─ Prediction data flow
│   ├─ Insight generation pipeline
│   └─ Model failure handling
└─ Data Pipeline Integration:
    ├─ End-to-end file processing
    ├─ Batch operation handling
    └─ Error recovery scenarios
```

## **Future Enhancements (Personal Project)**

### **Phase 2 - Performance & Reliability**

```python
When Dataset Grows Large:
├─ Query optimization for large datasets
├─ DataFrame chunking for memory efficiency
├─ Advanced caching strategies
└─ Performance monitoring

When Features Expand:
├─ Additional file format support
├─ Data backup and restore
├─ Advanced error recovery
└─ Audit trail for modifications
```

### **Phase 3 - Advanced Features (Optional)**

```python
If Needed Later:
├─ Bank API integrations
├─ Cloud storage backup
├─ Data export/import improvements
└─ Advanced analytics features

Note: Multi-user support removed - this is a personal app
```

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-02  
**Component Phase**: Core Implementation  
**Dependencies**: system_architecture.md, db_interface_architecture.md
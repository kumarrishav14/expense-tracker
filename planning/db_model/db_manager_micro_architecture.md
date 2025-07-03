# Database Manager Micro-Architecture

## **Component Overview**

The `db_manager` component serves as the **Database Operations Layer** that handles session management and CRUD operations. It sits between `db_interface` and the SQLAlchemy models, providing atomic database operations with proper transaction management.

## **Position in System Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                    DB_INTERFACE COMPONENT                       │
│              (Simple Data Access Layer)                        │
└─────────────┬───────────────────────────────────────────────────┘
              │ Requires atomic operations with rollback support
┌─────────────▼───────────────────────────────────────────────────┐
│                  DB_MANAGER COMPONENT                           │
│              (Database Operations Layer)                       │
│  • Session Management                                          │
│  • CRUD Operations                                             │
│  • Transaction Control                                         │
│  • Error Handling                                              │
└─────────────┬───────────────────────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────────────────────┐
│              DATABASE LAYER (SQLAlchemy + SQLite)               │
│                        (model.py)                              │
└─────────────────────────────────────────────────────────────────┘
```

## **Current Implementation Analysis**

### **Strengths of Current Implementation**
```
✅ Good Practices:
├─ Streamlit-aware session management with @st.cache_resource
├─ Proper SQLAlchemy sessionmaker configuration
├─ Comprehensive CRUD operations for both entities
├─ Timezone-aware datetime handling
├─ Clean separation of concerns
└─ Proper session reuse across Streamlit reruns
```

### **Critical Issues for db_interface Integration**

```
❌ Rollback Support Problems:
├─ Individual operations auto-commit immediately
├─ No transaction context management
├─ No batch operation support
├─ No rollback mechanism for failed operations
├─ Session persists across operations (can cause issues)
└─ No error handling with transaction rollback
```

## **Required Enhancements for db_interface Support**

### **1. Transaction Context Management**

**Current Problem:**
```python
# Each operation commits immediately - no rollback possible
def create_transaction(self, ...):
    db = self.get_session()
    db.add(db_transaction)
    db.commit()  # ❌ Immediate commit - can't rollback
    return db_transaction
```

**Required Solution:**
```python
# Need transaction context for rollback support
@contextmanager
def transaction_scope(self):
    session = self._session_local()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

### **2. Batch Operations Support**

**Current Gap:**
- No batch insert/update operations
- No way to process multiple transactions atomically
- No partial failure handling

**Required Addition:**
```python
def create_transactions_batch(self, transactions_data: List[dict]) -> List[model.Transaction]:
    """Create multiple transactions in a single atomic operation"""
    
def update_transactions_batch(self, updates: List[dict]) -> List[model.Transaction]:
    """Update multiple transactions atomically"""
```

## **Enhanced db_manager Architecture**

### **Core Responsibilities**

| Responsibility | Current Status | Required Enhancement |
|----------------|----------------|---------------------|
| **Session Management** | ✅ Streamlit-aware | ✅ Add transaction contexts |
| **CRUD Operations** | ✅ Complete | ✅ Add batch operations |
| **Transaction Control** | ❌ Missing | ✅ Add rollback support |
| **Error Handling** | ❌ Basic | ✅ Add constraint error handling |
| **Connection Management** | ✅ Good | ✅ Maintain current approach |

### **Enhanced Class Structure**

```python
class Database:
    """Enhanced database operations with transaction support"""
    
    # Current - Session Management (Keep)
    def __init__(self, db_url: str = "sqlite:///expenses.db")
    def get_session(self) -> Session  # For simple operations
    
    # New - Transaction Management
    @contextmanager
    def transaction_scope(self) -> Session  # For atomic operations
    def begin_transaction(self) -> Session
    def commit_transaction(self, session: Session)
    def rollback_transaction(self, session: Session)
    
    # Current - Individual CRUD (Keep)
    def create_category(self, name: str, parent_id: Optional[int] = None) -> model.Category
    def create_transaction(self, amount: float, ...) -> model.Transaction
    # ... other individual CRUD methods
    
    # New - Batch Operations (Required for db_interface)
    def create_transactions_batch(
        self, 
        transactions_data: List[dict], 
        session: Optional[Session] = None
    ) -> List[model.Transaction]
    
    def create_categories_batch(
        self, 
        categories_data: List[dict], 
        session: Optional[Session] = None
    ) -> List[model.Category]
    
    # New - Query Operations with Session Control
    def get_transactions_filtered(
        self,
        date_range: Optional[Tuple[date, date]] = None,
        categories: Optional[List[str]] = None,
        amount_range: Optional[Tuple[float, float]] = None,
        session: Optional[Session] = None
    ) -> List[model.Transaction]
    
    # New - Error Handling
    def handle_constraint_error(self, error: Exception) -> dict
    def is_retryable_error(self, error: Exception) -> bool
```

## **Transaction Management Strategy**

### **Session Usage Patterns**

```python
Session Usage Strategy:
├─ Simple Operations (UI components):
│   └─ Use get_session() - Streamlit session state
├─ Atomic Operations (db_interface):
│   └─ Use transaction_scope() - New session with rollback
├─ Batch Operations (db_interface):
│   └─ Use explicit session parameter
└─ Query Operations:
    └─ Use session parameter or get_session()
```

### **Transaction Scope Implementation**

```python
Transaction Patterns:
├─ Single Operation:
│   ├─ Use existing get_session() for simple UI operations
│   └─ Auto-commit for immediate persistence
├─ Batch Operations:
│   ├─ Use transaction_scope() for atomic operations
│   ├─ All-or-nothing commitment
│   └─ Full rollback on any failure
└─ Mixed Operations:
    ├─ Pass session parameter between operations
    ├─ Manual commit/rollback control
    └─ Flexible transaction boundaries
```

## **Integration with db_interface**

### **db_interface Usage Patterns**

```python
# db_interface will use db_manager like this:

# For simple data retrieval
def get_transactions_table(self, **filters) -> pd.DataFrame:
    transactions = self.db_manager.get_transactions_filtered(**filters)
    return self._convert_to_dataframe(transactions)

# For atomic batch operations
def save_transactions_table(self, df: pd.DataFrame) -> OperationResult:
    try:
        with self.db_manager.transaction_scope() as session:
            transactions_data = self._convert_from_dataframe(df)
            created_transactions = self.db_manager.create_transactions_batch(
                transactions_data, session=session
            )
            # All operations succeed or all rollback
        return OperationResult(success=True, affected_rows=len(created_transactions))
    except Exception as e:
        return OperationResult(
            success=False, 
            error_message=str(e),
            error_type=self.db_manager.classify_error(e)
        )
```

### **Error Handling Integration**

```python
Error Flow:
├─ Database Constraint Violation:
│   ├─ SQLAlchemy raises IntegrityError
│   ├─ db_manager.transaction_scope() catches and rolls back
│   ├─ db_manager.handle_constraint_error() classifies error
│   └─ db_interface returns OperationResult with details
├─ Connection Error:
│   ├─ SQLAlchemy raises OperationalError
│   ├─ db_manager.is_retryable_error() returns True
│   └─ db_interface implements retry logic
└─ Data Type Error:
    ├─ SQLAlchemy raises DataError
    ├─ db_manager classifies as non-retryable
    └─ db_interface returns immediate error
```

## **Backward Compatibility**

### **Maintaining Current Functionality**

```python
Compatibility Strategy:
├─ Keep all existing methods unchanged
├─ Existing Streamlit UI components continue to work
├─ Add new methods for db_interface integration
├─ No breaking changes to current API
└─ Gradual migration path available
```

### **Migration Path**

```python
Phase 1: Add transaction support (immediate)
├─ Add transaction_scope() context manager
├─ Add batch operation methods
├─ Add error classification methods
└─ Keep existing methods unchanged

Phase 2: Enhance error handling (next)
├─ Improve constraint error details
├─ Add retry logic support
├─ Add operation result structures
└─ Maintain backward compatibility
```

## **Implementation Guidelines**

### **Session Management Rules**

```python
Session Usage Rules:
├─ UI Components: Use get_session() (Streamlit session state)
├─ db_interface: Use transaction_scope() (new session)
├─ Batch Operations: Always use transaction_scope()
├─ Query Operations: Use session parameter when available
└─ Error Handling: Always rollback on exceptions
```

### **Error Handling Requirements**

```python
Error Classification:
├─ Retryable Errors:
│   ├─ OperationalError (connection issues)
│   ├─ TimeoutError (database locks)
│   └─ TemporaryError (deadlocks)
├─ Non-Retryable Errors:
│   ├─ IntegrityError (constraint violations)
│   ├─ DataError (type mismatches)
│   └─ ProgrammingError (SQL syntax)
└─ Return structured error information for db_interface
```

## **Testing Strategy**

### **Unit Testing Requirements**

```python
Test Categories:
├─ Transaction Management:
│   ├─ Successful commit scenarios
│   ├─ Rollback on constraint violations
│   ├─ Rollback on connection failures
│   └─ Session cleanup verification
├─ Batch Operations:
│   ├─ Successful batch inserts
│   ├─ Partial failure rollback
│   ├─ Large batch handling
│   └─ Performance under load
├─ Error Handling:
│   ├─ Constraint violation classification
│   ├─ Connection error handling
│   ├─ Retry logic support
│   └─ Error message formatting
└─ Backward Compatibility:
    ├─ Existing method functionality
    ├─ Streamlit session state integration
    ├─ UI component compatibility
    └─ Migration path validation
```

## **Performance Considerations**

### **Session Management Performance**

```python
Performance Guidelines:
├─ Streamlit Session Reuse: Continue for UI operations
├─ Transaction Session Isolation: New sessions for atomic operations
├─ Connection Pooling: Leverage SQLAlchemy's built-in pooling
├─ Batch Size Limits: Handle large batches efficiently
└─ Memory Management: Proper session cleanup
```

## **Summary of Required Changes**

### **Critical Enhancements Needed**

```python
Priority 1 (Required for db_interface):
├─ Add transaction_scope() context manager
├─ Add batch operation methods
├─ Add error classification methods
└─ Add session parameter support

Priority 2 (Enhanced functionality):
├─ Improve error handling details
├─ Add retry logic support
├─ Add operation result structures
└─ Add performance optimizations
```

### **Implementation Impact**

```python
Impact Assessment:
├─ Breaking Changes: None (backward compatible)
├─ New Dependencies: None (use existing SQLAlchemy)
├─ Performance Impact: Minimal (better transaction control)
├─ Testing Required: Comprehensive (new transaction logic)
└─ Documentation: Update for new methods
```

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-02  
**Component Phase**: Enhancement Required  
**Dependencies**: system_architecture.md, db_interface_micro_architecture.md  
**Status**: Current implementation needs transaction management enhancements
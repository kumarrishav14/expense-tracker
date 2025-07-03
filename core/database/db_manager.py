"""
Database handler class for the expenses tracking tool.
This class encapsulates all CRUD operations and database session management,
and is optimized for use with Streamlit. Enhanced with transaction management
and batch operations for atomic database operations.
"""
import datetime
import pytz
from contextlib import contextmanager
from typing import List, Optional, Dict, Any

import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, TimeoutError

from . import model

# Set the timezone to Indian Standard Time
indian_timezone = pytz.timezone("Asia/Kolkata")


@st.cache_resource
def init_engine(db_url: str = "sqlite:///expenses.db"):
    """
    Initializes the database engine and creates tables if they don't exist.
    This function is cached to ensure the engine is created only once per
    Streamlit application lifecycle.

    Args:
        db_url (str): The database connection URL.

    Returns:
        The SQLAlchemy engine.
    """
    connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
    engine = create_engine(db_url, connect_args=connect_args)
    model.Base.metadata.create_all(engine)
    return engine


class Database:
    """
    Enhanced database operations handler with transaction management and batch processing.
    
    This class provides comprehensive database operations including:
    - Session management optimized for Streamlit applications
    - Atomic transaction support with automatic rollback
    - Batch operations for efficient multi-record processing
    - Error classification and retry logic support
    - Full CRUD operations for categories and transactions
    
    Session Management Strategy:
    - get_session(): Streamlit session state for UI components
    - transaction_scope(): New session for atomic operations with rollback
    
    Usage Examples:
        # Simple operations (UI components)
        db = Database()
        category = db.create_category("Food")
        
        # Atomic operations (batch processing)
        with db.transaction_scope() as session:
            categories = db.create_categories_batch(data, session=session)
            transactions = db.create_transactions_batch(data, session=session)
            # All operations commit together or rollback on error
        
        # Error handling
        try:
            result = db.create_transaction(...)
        except Exception as e:
            error_info = db.handle_constraint_error(e)
            if db.is_retryable_error(e):
                # Implement retry logic
                pass
    """

    def __init__(self, db_url: str = "sqlite:///expenses.db"):
        """
        Initializes the database connection and sets up a sessionmaker.

        Args:
            db_url (str): The database connection URL. Defaults to "sqlite:///expenses.db".
        """
        self.engine = init_engine(db_url)
        self._session_local = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_session(self) -> Session:
        """
        Provides a database session that is persisted across Streamlit reruns
        using st.session_state.
        """
        if "db_session" not in st.session_state:
            st.session_state.db_session = self._session_local()
        return st.session_state.db_session
    
    @contextmanager
    def transaction_scope(self) -> Session:
        """
        Provides a transactional scope around a series of operations.
        Uses the main application session with transaction control for data consistency.
        
        Usage:
            with db.transaction_scope() as session:
                # Perform multiple operations
                db.create_category("Food", session=session)
                db.create_transaction(100.0, datetime.now(), session=session)
                # All operations commit together or rollback on error
        
        Yields:
            Session: The main application session with transaction control.
        """
        session = self.get_session()
        
        # Begin a transaction if not already in one
        if not session.in_transaction():
            session.begin()
            print("DEBUG: Started new transaction")
        
        try:
            yield session
            session.commit()
            print("DEBUG: Transaction committed successfully")
        except Exception as e:
            session.rollback()
            print(f"DEBUG: Transaction rolled back due to error: {str(e)}")
            raise
    
    def handle_constraint_error(self, error: Exception) -> Dict[str, Any]:
        """
        Classify and handle constraint errors for structured error reporting.
        
        Args:
            error (Exception): The SQLAlchemy exception to classify.
            
        Returns:
            Dict[str, Any]: Structured error information.
        """
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "is_retryable": False,
            "suggested_action": "unknown"
        }
        
        if isinstance(error, IntegrityError):
            error_info.update({
                "error_category": "constraint_violation",
                "is_retryable": False,
                "suggested_action": "check_data_integrity"
            })
            if "UNIQUE constraint failed" in str(error):
                error_info["constraint_type"] = "unique_violation"
            elif "FOREIGN KEY constraint failed" in str(error):
                error_info["constraint_type"] = "foreign_key_violation"
        elif isinstance(error, DataError):
            error_info.update({
                "error_category": "data_type_error",
                "is_retryable": False,
                "suggested_action": "validate_data_types"
            })
        else:
            # Handle non-SQLAlchemy errors (ValueError, DateParseError, etc.)
            error_info.update({
                "error_category": "data_validation_error",
                "is_retryable": False,
                "suggested_action": "validate_input_data"
            })
        
        print(f"DEBUG: Classified error - {error_info['error_category']}: {error_info['error_message']}")
        return error_info
    
    def is_retryable_error(self, error: Exception) -> bool:
        """
        Determine if an error is retryable (connection/timeout issues).
        
        Args:
            error (Exception): The exception to check.
            
        Returns:
            bool: True if the error is retryable, False otherwise.
        """
        retryable_errors = (OperationalError, TimeoutError)
        is_retryable = isinstance(error, retryable_errors)
        
        # Additional check for specific connection-related messages
        if isinstance(error, OperationalError):
            error_msg = str(error).lower()
            connection_keywords = ["database is locked", "connection", "timeout", "deadlock"]
            is_retryable = any(keyword in error_msg for keyword in connection_keywords)
        
        print(f"DEBUG: Error retryable check - {type(error).__name__}: {is_retryable}")
        return is_retryable

    # --- Batch Operation Methods ---
    
    def create_transactions_batch(
        self, 
        transactions_data: List[Dict[str, Any]], 
        session: Optional[Session] = None
    ) -> List[model.Transaction]:
        """
        Create multiple transactions in a single atomic operation.
        
        Args:
            transactions_data (List[Dict[str, Any]]): List of transaction dictionaries.
                Each dict should contain: amount, transaction_date, description (optional), category_id (optional)
            session (Optional[Session]): Database session to use. If None, uses get_session().
            
        Returns:
            List[model.Transaction]: List of created transaction objects.
        """
        if not transactions_data:
            print("DEBUG: Empty transactions_data provided to batch create")
            return []
        
        db = session if session is not None else self.get_session()
        created_transactions = []
        
        print(f"DEBUG: Creating batch of {len(transactions_data)} transactions")
        
        try:
            for i, data in enumerate(transactions_data):
                db_transaction = model.Transaction(
                    amount=data['amount'],
                    transaction_date=data['transaction_date'],
                    description=data.get('description'),
                    category_id=data.get('category_id'),
                    created_at=datetime.datetime.now(indian_timezone),
                )
                db.add(db_transaction)
                created_transactions.append(db_transaction)
                print(f"DEBUG: Added transaction {i+1}/{len(transactions_data)} to batch")
            
            # Only commit if we're managing our own session
            if session is None:
                db.commit()
                print(f"DEBUG: Batch transaction commit successful - {len(created_transactions)} transactions created")
                
                # Refresh objects to get IDs
                for transaction in created_transactions:
                    db.refresh(transaction)
            else:
                # For session-managed transactions, flush to get IDs
                db.flush()
                for transaction in created_transactions:
                    db.refresh(transaction)
                print(f"DEBUG: Batch transaction flush successful - {len(created_transactions)} transactions prepared")
            
            return created_transactions
            
        except Exception as e:
            if session is None:
                db.rollback()
                print(f"ERROR: Batch transaction failed, rolled back: {str(e)}")
            raise
    
    def create_categories_batch(
        self, 
        categories_data: List[Dict[str, Any]], 
        session: Optional[Session] = None
    ) -> List[model.Category]:
        """
        Create multiple categories in a single atomic operation.
        
        Args:
            categories_data (List[Dict[str, Any]]): List of category dictionaries.
                Each dict should contain: name, parent_id (optional)
            session (Optional[Session]): Database session to use. If None, uses get_session().
            
        Returns:
            List[model.Category]: List of created category objects.
        """
        if not categories_data:
            print("DEBUG: Empty categories_data provided to batch create")
            return []
        
        db = session if session is not None else self.get_session()
        created_categories = []
        
        print(f"DEBUG: Creating batch of {len(categories_data)} categories")
        
        try:
            for i, data in enumerate(categories_data):
                db_category = model.Category(
                    name=data['name'],
                    parent_id=data.get('parent_id'),
                    created_at=datetime.datetime.now(indian_timezone)
                )
                db.add(db_category)
                created_categories.append(db_category)
                print(f"DEBUG: Added category {i+1}/{len(categories_data)} to batch: '{data['name']}'")
            
            # Only commit if we're managing our own session
            if session is None:
                db.commit()
                print(f"DEBUG: Batch category commit successful - {len(created_categories)} categories created")
                
                # Refresh objects to get IDs
                for category in created_categories:
                    db.refresh(category)
            else:
                # For session-managed transactions, flush to get IDs
                db.flush()
                for category in created_categories:
                    db.refresh(category)
                print(f"DEBUG: Batch category flush successful - {len(created_categories)} categories prepared")
            
            return created_categories
            
        except Exception as e:
            if session is None:
                db.rollback()
                print(f"ERROR: Batch category creation failed, rolled back: {str(e)}")
            raise

    # --- Category CRUD Methods ---

    def create_category(self, name: str, parent_id: Optional[int] = None, session: Optional[Session] = None) -> model.Category:
        """
        Creates a new category in the database.

        Args:
            name (str): The name for the new category.
            parent_id (Optional[int]): The ID of the parent category, if any.
            session (Optional[Session]): Database session to use. If None, uses get_session().

        Returns:
            model.Category: The newly created category object.
        """
        db = session if session is not None else self.get_session()
        db_category = model.Category(
            name=name,
            parent_id=parent_id,
            created_at=datetime.datetime.now(indian_timezone)
        )
        db.add(db_category)
        
        # Only commit if we're managing our own session
        if session is None:
            db.commit()
            db.refresh(db_category)
        else:
            # For session-managed transactions, flush to get the ID
            db.flush()
            db.refresh(db_category)
        
        return db_category

    def get_category(self, category_id: int, session: Optional[Session] = None) -> Optional[model.Category]:
        """
        Retrieves a single category by its ID.

        Args:
            category_id (int): The ID of the category to retrieve.
            session (Optional[Session]): Database session to use. If None, uses get_session().

        Returns:
            Optional[model.Category]: The category object if found, otherwise None.
        """
        db = session if session is not None else self.get_session()
        return db.query(model.Category).filter(model.Category.id == category_id).first()

    def get_all_categories(self, session: Optional[Session] = None) -> List[model.Category]:
        """
        Retrieves all categories from the database.

        Args:
            session (Optional[Session]): Database session to use. If None, uses get_session().

        Returns:
            List[model.Category]: A list of all category objects.
        """
        db = session if session is not None else self.get_session()
        return db.query(model.Category).all()

    def update_category(self, category_id: int, name: str, parent_id: Optional[int] = None, session: Optional[Session] = None) -> Optional[model.Category]:
        """
        Updates an existing category.

        Args:
            category_id (int): The ID of the category to update.
            name (str): The new name for the category.
            parent_id (Optional[int]): The new parent ID for the category.
            session (Optional[Session]): Database session to use. If None, uses get_session().

        Returns:
            Optional[model.Category]: The updated category object, or None if not found.
        """
        db = session if session is not None else self.get_session()
        db_category = db.query(model.Category).filter(model.Category.id == category_id).first()
        if db_category:
            db_category.name = name
            db_category.parent_id = parent_id
            db_category.updated_at = datetime.datetime.now(indian_timezone)
            
            # Only commit if we're managing our own session
            if session is None:
                db.commit()
                db.refresh(db_category)
        
        return db_category

    def delete_category(self, category_id: int, session: Optional[Session] = None) -> bool:
        """
        Deletes a category from the database.

        Args:
            category_id (int): The ID of the category to delete.
            session (Optional[Session]): Database session to use. If None, uses get_session().

        Returns:
            bool: True if the category was deleted, False otherwise.
        """
        db = session if session is not None else self.get_session()
        db_category = db.query(model.Category).filter(model.Category.id == category_id).first()
        if db_category:
            db.delete(db_category)
            
            # Only commit if we're managing our own session
            if session is None:
                db.commit()
            
            return True
        return False

    # --- Transaction CRUD Methods ---

    def create_transaction(
        self,
        amount: float,
        transaction_date: datetime.datetime,
        description: Optional[str] = None,
        category_id: Optional[int] = None,
        session: Optional[Session] = None,
    ) -> model.Transaction:
        """
        Creates a new transaction.

        Args:
            amount (float): The amount of the transaction.
            transaction_date (datetime.datetime): The date and time of the transaction.
            description (Optional[str]): A description for the transaction.
            category_id (Optional[int]): The ID of the category for this transaction.
            session (Optional[Session]): Database session to use. If None, uses get_session().

        Returns:
            model.Transaction: The newly created transaction object.
        """
        db = session if session is not None else self.get_session()
        db_transaction = model.Transaction(
            amount=amount,
            transaction_date=transaction_date,
            description=description,
            category_id=category_id,
            created_at=datetime.datetime.now(indian_timezone),
        )
        db.add(db_transaction)
        
        # Only commit if we're managing our own session
        if session is None:
            db.commit()
            db.refresh(db_transaction)
        else:
            # For session-managed transactions, flush to get the ID
            db.flush()
            db.refresh(db_transaction)
        
        return db_transaction

    def get_transaction(self, transaction_id: int, session: Optional[Session] = None) -> Optional[model.Transaction]:
        """
        Retrieves a single transaction by its ID.

        Args:
            transaction_id (int): The ID of the transaction to retrieve.
            session (Optional[Session]): Database session to use. If None, uses get_session().

        Returns:
            Optional[model.Transaction]: The transaction object if found, otherwise None.
        """
        db = session if session is not None else self.get_session()
        return db.query(model.Transaction).filter(model.Transaction.id == transaction_id).first()

    def get_all_transactions(self, session: Optional[Session] = None) -> List[model.Transaction]:
        """
        Retrieves all transactions from the database.

        Args:
            session (Optional[Session]): Database session to use. If None, uses get_session().

        Returns:
            List[model.Transaction]: A list of all transaction objects.
        """
        db = session if session is not None else self.get_session()
        return db.query(model.Transaction).all()

    def update_transaction(
        self,
        transaction_id: int,
        amount: float,
        transaction_date: datetime.datetime,
        description: Optional[str] = None,
        category_id: Optional[int] = None,
        session: Optional[Session] = None,
    ) -> Optional[model.Transaction]:
        """
        Updates an existing transaction.

        Args:
            transaction_id (int): The ID of the transaction to update.
            amount (float): The new amount for the transaction.
            transaction_date (datetime.datetime): The new date for the transaction.
            description (Optional[str]): The new description for the transaction.
            category_id (Optional[int]): The new category ID for the transaction.
            session (Optional[Session]): Database session to use. If None, uses get_session().

        Returns:
            Optional[model.Transaction]: The updated transaction object, or None if not found.
        """
        db = session if session is not None else self.get_session()
        db_transaction = db.query(model.Transaction).filter(model.Transaction.id == transaction_id).first()
        if db_transaction:
            db_transaction.amount = amount
            db_transaction.transaction_date = transaction_date
            db_transaction.description = description
            db_transaction.category_id = category_id
            db_transaction.updated_at = datetime.datetime.now(indian_timezone)
            
            # Only commit if we're managing our own session
            if session is None:
                db.commit()
                db.refresh(db_transaction)
        
        return db_transaction

    def delete_transaction(self, transaction_id: int, session: Optional[Session] = None) -> bool:
        """
        Deletes a transaction from the database.

        Args:
            transaction_id (int): The ID of the transaction to delete.
            session (Optional[Session]): Database session to use. If None, uses get_session().

        Returns:
            bool: True if the transaction was deleted, False otherwise.
        """
        db = session if session is not None else self.get_session()
        db_transaction = db.query(model.Transaction).filter(model.Transaction.id == transaction_id).first()
        if db_transaction:
            db.delete(db_transaction)
            
            # Only commit if we're managing our own session
            if session is None:
                db.commit()
            
            return True
        return False

    # --- Enhanced Query Methods ---
    
    def get_transactions_filtered(
        self,
        date_range: Optional[tuple] = None,
        categories: Optional[List[str]] = None,
        amount_range: Optional[tuple] = None,
        session: Optional[Session] = None
    ) -> List[model.Transaction]:
        """
        Retrieve transactions with filtering options.
        
        Args:
            date_range (Optional[tuple]): Tuple of (start_date, end_date) for filtering.
            categories (Optional[List[str]]): List of category names to filter by.
            amount_range (Optional[tuple]): Tuple of (min_amount, max_amount) for filtering.
            session (Optional[Session]): Database session to use. If None, uses get_session().
            
        Returns:
            List[model.Transaction]: List of filtered transaction objects.
        """
        db = session if session is not None else self.get_session()
        query = db.query(model.Transaction)
        
        # Apply date range filter
        if date_range:
            start_date, end_date = date_range
            if start_date:
                query = query.filter(model.Transaction.transaction_date >= start_date)
            if end_date:
                query = query.filter(model.Transaction.transaction_date <= end_date)
            print(f"DEBUG: Applied date filter: {start_date} to {end_date}")
        
        # Apply category filter
        if categories:
            # Join with Category table to filter by category names
            query = query.join(model.Category, model.Transaction.category_id == model.Category.id)
            query = query.filter(model.Category.name.in_(categories))
            print(f"DEBUG: Applied category filter: {categories}")
        
        # Apply amount range filter
        if amount_range:
            min_amount, max_amount = amount_range
            if min_amount is not None:
                query = query.filter(model.Transaction.amount >= min_amount)
            if max_amount is not None:
                query = query.filter(model.Transaction.amount <= max_amount)
            print(f"DEBUG: Applied amount filter: {min_amount} to {max_amount}")
        
        results = query.all()
        print(f"DEBUG: Filtered query returned {len(results)} transactions")
        return results
    
    def get_categories_by_parent(
        self, 
        parent_id: Optional[int] = None, 
        session: Optional[Session] = None
    ) -> List[model.Category]:
        """
        Retrieve categories by parent relationship.
        
        Args:
            parent_id (Optional[int]): Parent category ID. If None, returns root categories.
            session (Optional[Session]): Database session to use. If None, uses get_session().
            
        Returns:
            List[model.Category]: List of categories with the specified parent.
        """
        db = session if session is not None else self.get_session()
        
        if parent_id is None:
            # Return root categories (no parent)
            query = db.query(model.Category).filter(model.Category.parent_id.is_(None))
            print("DEBUG: Querying for root categories (no parent)")
        else:
            # Return categories with specified parent
            query = db.query(model.Category).filter(model.Category.parent_id == parent_id)
            print(f"DEBUG: Querying for categories with parent_id: {parent_id}")
        
        results = query.all()
        print(f"DEBUG: Parent category query returned {len(results)} categories")
        return results
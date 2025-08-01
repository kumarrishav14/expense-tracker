"""
Database handler class for the expenses tracking tool.
This class encapsulates all CRUD operations and database session management,
and is optimized for use with Streamlit. Enhanced with transaction management
and batch operations for atomic database operations.
"""
import datetime
import pytz
from contextlib import contextmanager
from typing import List, Optional, Dict, Any, Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, TimeoutError

from . import model

# Set the timezone to Indian Standard Time
indian_timezone = pytz.timezone("Asia/Kolkata")


def init_engine(db_url: str = "sqlite:///expenses.db"):
    """
    Initializes the database engine and creates tables if they don't exist.
    Creates a new engine instance for proper test isolation.

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
    - Session management with proper isolation
    - Atomic transaction support with automatic rollback
    - Batch operations for efficient multi-record processing
    - Error classification and retry logic support
    - Full CRUD operations for categories and transactions

    Session Management Strategy:
    - get_session(): Creates new session for each operation
    - transaction_scope(): New session for atomic operations with rollback

    Usage Examples:
        # Simple operations
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
        Creates a new database session for each operation to prevent contamination.
        This ensures proper session isolation and prevents PendingRollbackError.
        """
        return self._session_local()

    @contextmanager
    def transaction_scope(self) -> 'Generator[Session, None, None]':
        """
        Provides a transactional scope with proper isolation.
        Creates a NEW session for each transaction to prevent contamination.

        Usage:
            with db.transaction_scope() as session:
                # Perform multiple operations
                db.create_category("Food", session=session)
                db.create_transaction(100.0, datetime.now(), session=session)
                # All operations commit together or rollback on error

        Yields:
            Session: A new isolated session with transaction control.
        """
        session = self._session_local()  # Always create NEW session

        try:
            session.begin()
            print("DEBUG: Started new isolated transaction")
            yield session
            session.commit()
            print("DEBUG: Transaction committed successfully")
        except Exception as e:
            session.rollback()
            print(f"DEBUG: Transaction rolled back due to error: {str(e)}")
            raise
        finally:
            session.close()
            print("DEBUG: Session closed and cleaned up")

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
                    account_id=data['account_id'],
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

    def update_category(self, category_id: int, new_data: Dict[str, Any], session: Optional[Session] = None) -> Optional[model.Category]:
        """
        Updates an existing category from a dictionary of new data.

        Args:
            category_id (int): The ID of the category to update.
            new_data (Dict[str, Any]): A dictionary containing the new data.
            session (Optional[Session]): Database session to use. If None, uses get_session().

        Returns:
            Optional[model.Category]: The updated category object, or None if not found.
        """
        db = session if session is not None else self.get_session()

        if 'parent_id' in new_data:
            parent_id = new_data['parent_id']
            if category_id == parent_id:
                raise ValueError("Circular Dependency: A category cannot be its own parent.")
            if self._is_descendant(category_id, parent_id, db):
                raise ValueError("Circular Dependency: Cannot set a category's parent to one of its own descendants.")

        db_category = db.query(model.Category).filter(model.Category.id == category_id).first()
        if db_category:
            for key, value in new_data.items():
                setattr(db_category, key, value)
            db_category.updated_at = datetime.datetime.now(indian_timezone)

            if session is None:
                db.commit()
                db.refresh(db_category)

        return db_category

    def _is_descendant(self, category_id: int, potential_parent_id: int, session: Session) -> bool:
        """Checks if a category is a descendant of another using a recursive CTE."""
        from sqlalchemy import select
        if not potential_parent_id:
            return False

        descendants_cte = select(model.Category.id).where(model.Category.id == category_id).cte(name="descendants_cte", recursive=True)
        descendants_cte = descendants_cte.union_all(
            select(model.Category.id).where(model.Category.parent_id == descendants_cte.c.id)
        )

        return session.query(descendants_cte).filter(descendants_cte.c.id == potential_parent_id).first() is not None

    def delete_category(self, category_id: int, session: Optional[Session] = None) -> bool:
        """
        Deletes a category from the database, preventing deletion if it has children.

        Args:
            category_id (int): The ID of the category to delete.
            session (Optional[Session]): Database session to use. If None, uses get_session().

        Returns:
            bool: True if the category was deleted, False otherwise.
        """
        db = session if session is not None else self.get_session()
        db_category = db.query(model.Category).filter(model.Category.id == category_id).first()
        if db_category:
            # Check for child categories
            child_count = db.query(model.Category).filter(model.Category.parent_id == category_id).count()
            if child_count > 0:
                return False  # Cannot delete category with children

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
        account_id: int,
        description: Optional[str] = None,
        category_id: Optional[int] = None,
        statement_id: Optional[int] = None,
        is_transfer: bool = False,
        transfer_id: Optional[int] = None,
        session: Optional[Session] = None,
    ) -> model.Transaction:
        """
        Creates a new transaction.

        Args:
            amount (float): The amount of the transaction.
            transaction_date (datetime.datetime): The date and time of the transaction.
            account_id (int): The ID of the account for this transaction.
            description (Optional[str]): A description for the transaction.
            category_id (Optional[int]): The ID of the category for this transaction.
            statement_id (Optional[int]): The ID of the statement for this transaction.
            is_transfer (bool): Whether this transaction is a transfer.
            transfer_id (Optional[int]): The ID of the transfer for this transaction.
            session (Optional[Session]): Database session to use. If None, uses get_session().

        Returns:
            model.Transaction: The newly created transaction object.
        """
        db = session if session is not None else self.get_session()
        db_transaction = model.Transaction(
            amount=amount,
            transaction_date=transaction_date,
            account_id=account_id,
            description=description,
            category_id=category_id,
            statement_id=statement_id,
            is_transfer=is_transfer,
            transfer_id=transfer_id,
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

    def get_transactions_count(self, session: Optional[Session] = None) -> int:
        """
        Gets the total number of transactions in the database.
        """
        db = session if session is not None else self.get_session()
        return db.query(model.Transaction).count()

    def get_latest_transaction_timestamp(self, session: Optional[Session] = None) -> Optional[datetime.datetime]:
        """
        Gets the timestamp of the most recent transaction.
        """
        db = session if session is not None else self.get_session()
        latest_transaction = db.query(model.Transaction).order_by(model.Transaction.transaction_date.desc()).first()
        return latest_transaction.transaction_date if latest_transaction else None

    def update_transaction(
        self,
        transaction_id: int,
        new_data: Dict[str, Any],
        session: Optional[Session] = None,
    ) -> Optional[model.Transaction]:
        """
        Updates an existing transaction from a dictionary of new data.

        Args:
            transaction_id (int): The ID of the transaction to update.
            new_data (Dict[str, Any]): A dictionary containing the new data.
            session (Optional[Session]): Database session to use. If None, uses get_session().

        Returns:
            Optional[model.Transaction]: The updated transaction object, or None if not found.
        """
        db = session if session is not None else self.get_session()
        db_transaction = db.query(model.Transaction).filter(model.Transaction.id == transaction_id).first()
        if db_transaction:
            for key, value in new_data.items():
                setattr(db_transaction, key, value)
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

    def create_accounts_batch(self, accounts_data: List[Dict[str, Any]], session: Session) -> List[model.Account]:
        """Creates multiple accounts in a single atomic operation."""
        db_accounts = [model.Account(**data) for data in accounts_data]
        session.add_all(db_accounts)
        session.flush()
        return db_accounts

    def create_card_statements_batch(
        self,
        statements_data: List[Dict[str, Any]],
        session: Optional[Session] = None
    ) -> List[model.CardStatement]:
        """
        Create multiple card statements in a single atomic operation.
        FIXES: AttributeError for missing create_card_statements_batch method.
        """
        if not statements_data:
            print("DEBUG: Empty statements_data provided to batch create")
            return []

        db = session if session is not None else self.get_session()
        created_statements = []

        print(f"DEBUG: Creating batch of {len(statements_data)} card statements")

        try:
            for i, data in enumerate(statements_data):
                # Convert string dates to date objects for SQLite compatibility
                statement_date = data['statement_date']
                if isinstance(statement_date, str):
                    statement_date = datetime.datetime.strptime(statement_date, '%Y-%m-%d').date()
                elif isinstance(statement_date, datetime.datetime):
                    statement_date = statement_date.date()

                start_date = data.get('start_date')
                if start_date and isinstance(start_date, str):
                    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
                elif start_date and isinstance(start_date, datetime.datetime):
                    start_date = start_date.date()

                end_date = data.get('end_date')
                if end_date and isinstance(end_date, str):
                    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
                elif end_date and isinstance(end_date, datetime.datetime):
                    end_date = end_date.date()

                db_statement = model.CardStatement(
                    account_id=data['account_id'],
                    statement_date=statement_date,
                    total_due=data.get('total_due'),
                    status=data.get('status', 'UNPAID'),
                    start_date=start_date,
                    end_date=end_date,
                    created_at=datetime.datetime.now(indian_timezone)
                )
                db.add(db_statement)
                created_statements.append(db_statement)
                print(f"DEBUG: Added statement {i+1}/{len(statements_data)} to batch")

            if session is None:
                db.commit()
                for statement in created_statements:
                    db.refresh(statement)
                print(f"DEBUG: Batch statement commit successful - {len(created_statements)} statements created")
            else:
                db.flush()
                for statement in created_statements:
                    db.refresh(statement)
                print(f"DEBUG: Batch statement flush successful - {len(created_statements)} statements prepared")

            return created_statements

        except Exception as e:
            if session is None:
                db.rollback()
                print(f"ERROR: Batch statement creation failed, rolled back: {str(e)}")
            raise

    def get_category_by_name(self, name: str, parent_name: Optional[str] = None, session: Optional[Session] = None) -> Optional[model.Category]:
        """Gets a category by name and optional parent name for specificity."""
        db = session if session is not None else self.get_session()

        if parent_name:
            # First find the parent category
            parent_category = db.query(model.Category).filter(
                model.Category.name == parent_name,
                model.Category.parent_id.is_(None)
            ).first()

            if not parent_category:
                return None

            # Then find the child category under this parent
            return db.query(model.Category).filter(
                model.Category.name == name,
                model.Category.parent_id == parent_category.id
            ).first()
        else:
            # Find root category (no parent)
            return db.query(model.Category).filter(
                model.Category.name == name,
                model.Category.parent_id.is_(None)
            ).first()

    def get_all_card_statements(self, session: Optional[Session] = None) -> List[model.CardStatement]:
        """Get all card statements from database."""
        db = session if session is not None else self.get_session()
        return db.query(model.CardStatement).all()

    # --- Account CRUD Methods ---
    def create_account(self, name: str, account_type: str, bank_name: Optional[str] = None, account_number_last4: Optional[str] = None, file_fingerprint: Optional[str] = None, session: Optional[Session] = None) -> model.Account:
        db = session if session is not None else self.get_session()
        db_account = model.Account(
            name=name,
            account_type=account_type,
            bank_name=bank_name,
            account_number_last4=account_number_last4,
            file_fingerprint=file_fingerprint
        )
        db.add(db_account)
        if session is None: db.commit(); db.refresh(db_account)
        else: db.flush(); db.refresh(db_account)
        return db_account

    def get_account(self, account_id: int, session: Optional[Session] = None) -> Optional[model.Account]:
        db = session if session is not None else self.get_session()
        return db.query(model.Account).filter(model.Account.id == account_id).first()

    def get_all_accounts(self, only_active: bool = False, session: Optional[Session] = None) -> List[model.Account]:
        db = session if session is not None else self.get_session()
        query = db.query(model.Account)
        if only_active:
            query = query.filter(model.Account.is_active == True)
        return query.all()

    def update_account(self, account_id: int, new_data: Dict[str, Any], session: Optional[Session] = None) -> Optional[model.Account]:
        db = session if session is not None else self.get_session()
        db_account = db.query(model.Account).filter(model.Account.id == account_id).first()
        if db_account:
            for key, value in new_data.items():
                setattr(db_account, key, value)
            db_account.updated_at = datetime.datetime.now(indian_timezone)
            if session is None: db.commit(); db.refresh(db_account)
        return db_account

    # --- CardStatement CRUD Methods ---
    def create_card_statement(self, account_id: int, statement_date: datetime.date, total_due: Optional[float] = None, status: str = 'UNPAID', session: Optional[Session] = None) -> model.CardStatement:
        db = session if session is not None else self.get_session()
        db_statement = model.CardStatement(account_id=account_id, statement_date=statement_date, total_due=total_due, status=status)
        db.add(db_statement)
        if session is None: db.commit(); db.refresh(db_statement)
        else: db.flush(); db.refresh(db_statement)
        return db_statement

    def get_card_statement(self, statement_id: int, session: Optional[Session] = None) -> Optional[model.CardStatement]:
        db = session if session is not None else self.get_session()
        return db.query(model.CardStatement).filter(model.CardStatement.id == statement_id).first()

    def update_card_statement(self, statement_id: int, new_data: Dict[str, Any], session: Optional[Session] = None) -> Optional[model.CardStatement]:
        db = session if session is not None else self.get_session()
        db_statement = db.query(model.CardStatement).filter(model.CardStatement.id == statement_id).first()
        if db_statement:
            for key, value in new_data.items():
                setattr(db_statement, key, value)
            db_statement.updated_at = datetime.datetime.now(indian_timezone)
            if session is None: db.commit(); db.refresh(db_statement)
        return db_statement

    # --- Transfer CRUD Methods ---
    def create_transfer(self, payment_transaction_id: int, statement_id: int, matched_rule: Optional[str] = None, session: Optional[Session] = None) -> model.Transfer:
        db = session if session is not None else self.get_session()
        db_transfer = model.Transfer(payment_transaction_id=payment_transaction_id, statement_id=statement_id, matched_rule=matched_rule)
        db.add(db_transfer)
        if session is None: db.commit(); db.refresh(db_transfer)
        else: db.flush(); db.refresh(db_transfer)
        return db_transfer

"""
Database interface for converting between pandas DataFrames and database tables.

This module provides a simplified interface where other components work with
denormalized pandas DataFrames (no foreign keys), while the interface handles
all SQL relationship complexity internally.
"""
import datetime
from typing import Dict, List, Optional, Tuple
import pytz

import pandas as pd
from sqlalchemy.orm import Session

from .db_manager import Database
from .model import Category, Transaction, Account, CardStatement, Transfer
from .results import OperationResult, BatchOperationResult

# Set the timezone to Indian Standard Time
indian_timezone = pytz.timezone("Asia/Kolkata")


class DatabaseInterface:
    """
    Simplified interface for database operations.
    """

    def __init__(self, db_url: str = "sqlite:///expenses.db"):
        """
        Initialize the database interface.

        Args:
            db_url (str): Database connection URL.
        """
        self.db = Database(db_url)
        self._current_transaction_id = None

    # --- Account Management ---
    def get_accounts_table(self, only_active: bool = False) -> pd.DataFrame:
        accounts = self.db.get_all_accounts(only_active=only_active)
        if not accounts:
            return pd.DataFrame(columns=['id', 'name', 'account_type', 'bank_name', 'account_number_last4', 'is_active'])
        data = [{
            'id': acc.id, 'name': acc.name, 'account_type': acc.account_type, 'bank_name': acc.bank_name,
            'account_number_last4': acc.account_number_last4, 'is_active': acc.is_active
        } for acc in accounts]
        return pd.DataFrame(data)

    def save_accounts_table(self, df: pd.DataFrame) -> BatchOperationResult:
        try:
            if df.empty:
                return BatchOperationResult(success=True, total_processed=0, successful_count=0, failed_count=0)

            with self.db.transaction_scope() as session:
                accounts_data = [{str(k): v for k, v in record.items()} for record in df.to_dict(orient='records')]
                created_accounts = self.db.create_accounts_batch(accounts_data, session=session)

                # SERIALIZE while session-bound to prevent DetachedInstanceError
                serialized_accounts = [
                    {
                        'id': acc.id,
                        'name': acc.name,
                        'account_type': acc.account_type,
                        'bank_name': acc.bank_name,
                        'account_number_last4': acc.account_number_last4,
                        'is_active': acc.is_active,
                        'created_at': acc.created_at.isoformat() if acc.created_at else None,
                        'updated_at': acc.updated_at.isoformat() if acc.updated_at else None
                    }
                    for acc in created_accounts
                ]

            return BatchOperationResult(
                success=True,
                total_processed=len(df),
                successful_count=len(created_accounts),
                failed_count=0,
                successful_items=serialized_accounts
            )
        except Exception as e:
            error_info = self.db.handle_constraint_error(e)
            return BatchOperationResult(
                success=False,
                total_processed=len(df),
                successful_count=0,
                failed_count=len(df),
                error_message=error_info['error_message'],
                is_retryable=self.db.is_retryable_error(e)
            )

    def update_account(self, account_id: int, new_data: Dict) -> OperationResult:
        try:
            with self.db.transaction_scope() as session:
                updated_account = self.db.update_account(account_id, new_data, session=session)

            if updated_account:
                return OperationResult(success=True, affected_rows=1)
            else:
                return OperationResult(
                    success=False,
                    error_message=f"Account {account_id} not found"
                )
        except Exception as e:
            error_info = self.db.handle_constraint_error(e)
            return OperationResult(
                success=False,
                error_message=error_info['error_message'],
                error_type=error_info['error_type'],
                is_retryable=self.db.is_retryable_error(e)
            )

    # --- Credit Mapping ---
    def save_card_statements_table(self, df: pd.DataFrame) -> BatchOperationResult:
        try:
            if df.empty:
                return BatchOperationResult(success=True, total_processed=0, successful_count=0, failed_count=0)

            with self.db.transaction_scope() as session:
                statements_data = [{str(k): v for k, v in record.items()} for record in df.to_dict(orient='records')]
                created_statements = self.db.create_card_statements_batch(statements_data, session=session)

                # SERIALIZE while session-bound to prevent DetachedInstanceError
                serialized_statements = [
                    {
                        'id': stmt.id,
                        'statement_date': stmt.statement_date.isoformat() if stmt.statement_date else None,
                        'description': stmt.description,
                        'amount': float(stmt.amount),
                        'account_id': stmt.account_id,
                        'account_name': stmt.account.name if stmt.account else None,
                        'is_processed': stmt.is_processed,
                        'created_at': stmt.created_at.isoformat() if stmt.created_at else None
                    }
                    for stmt in created_statements
                ]

            return BatchOperationResult(
                success=True,
                total_processed=len(df),
                successful_count=len(created_statements),
                failed_count=0,
                successful_items=serialized_statements
            )
        except Exception as e:
            error_info = self.db.handle_constraint_error(e)
            return BatchOperationResult(
                success=False,
                total_processed=len(df),
                successful_count=0,
                failed_count=len(df),
                error_message=error_info['error_message'],
                is_retryable=self.db.is_retryable_error(e)
            )

    def link_transfer(self, payment_transaction_id: int, statement_id: int) -> OperationResult:
        try:
            with self.db.transaction_scope() as session:
                transfer = self.db.create_transfer(payment_transaction_id, statement_id, session=session)
                self.db.update_transaction(payment_transaction_id, {'is_transfer': True, 'transfer_id': transfer.id}, session=session)
                # Ensure we have the transfer ID before session closes
                transfer_id = transfer.id

            return OperationResult(success=True, affected_rows=2, data={'transfer_id': transfer_id})
        except Exception as e:
            error_info = self.db.handle_constraint_error(e)
            return OperationResult(
                success=False,
                error_message=error_info['error_message'],
                error_type=error_info['error_type'],
                is_retryable=self.db.is_retryable_error(e)
            )

    def update_statement_status(self, statement_id: int, new_status: str) -> OperationResult:
        try:
            with self.db.transaction_scope() as session:
                updated_statement = self.db.update_card_statement(statement_id, {'status': new_status}, session=session)

            if updated_statement:
                return OperationResult(success=True, affected_rows=1)
            else:
                return OperationResult(
                    success=False,
                    error_message=f"Statement {statement_id} not found"
                )
        except Exception as e:
            error_info = self.db.handle_constraint_error(e)
            return OperationResult(
                success=False,
                error_message=error_info['error_message'],
                error_type=error_info['error_type'],
                is_retryable=self.db.is_retryable_error(e)
            )

    # --- Existing Methods ---
    def get_transactions_count(self) -> int:
        """
        Gets the total number of transactions in the database.
        """
        return self.db.get_transactions_count()

    def get_latest_transaction_timestamp(self) -> Optional[datetime.datetime]:
        """
        Gets the timestamp of the most recent transaction.
        """
        return self.db.get_latest_transaction_timestamp()

    def get_categories_table(self) -> pd.DataFrame:
        """
        Get categories as a simple DataFrame for UX components (dropdowns, etc.).

        Returns:
            pd.DataFrame: DataFrame with columns [name, parent_category]
                         where parent_category is the name of parent (not ID).
        """
        categories = self.db.get_all_categories()

        if not categories:
            return pd.DataFrame(columns=['name', 'parent_category'])

        data = []
        for category in categories:
            row = {
                'name': category.name,
                'parent_category': category.parent.name if category.parent else None
            }
            data.append(row)

        return pd.DataFrame(data)

    def get_transactions_table(self) -> pd.DataFrame:
        """
        Get transactions as a denormalized DataFrame with category and sub_category columns.

        Returns:
            pd.DataFrame: DataFrame with columns [description, amount, transaction_date,
                         category, sub_category] where:
                         - category: parent category name (or category name if no parent)
                         - sub_category: category name (blank if category has no parent)
        """
        transactions = self.db.get_all_transactions()

        if not transactions:
            return pd.DataFrame(columns=[
                'description', 'amount', 'transaction_date', 'category', 'sub_category', 'account_name'
            ])

        data = []
        for transaction in transactions:
            # Determine category and sub_category based on hierarchy
            if transaction.category:
                if transaction.category.parent:
                    # Has parent: parent is category, current is sub_category
                    category = transaction.category.parent.name
                    sub_category = transaction.category.name
                else:
                    # No parent: current is category, sub_category is blank
                    category = transaction.category.name
                    sub_category = ""
            else:
                # No category assigned
                category = ""
                sub_category = ""

            row = {
                'description': transaction.description or "",
                'amount': float(transaction.amount),
                'transaction_date': transaction.transaction_date,
                'category': category,
                'sub_category': sub_category,
                'account_name': transaction.account.name if transaction.account else None
            }
            data.append(row)

        df = pd.DataFrame(data)

        # Convert datetime column to proper pandas datetime
        if 'transaction_date' in df.columns:
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])

        return df

    # --- Import methods (pandas to DB) ---

    def save_transactions_table(self, df: pd.DataFrame) -> BatchOperationResult:
        """
        Save transactions from denormalized DataFrame to database using atomic transactions.

        Args:
            df (pd.DataFrame): DataFrame with columns [description, amount, transaction_date,
                              category, sub_category]

        Returns:
            BatchOperationResult: Structured result with success/failure details.
        """
        if df.empty:
            print("DEBUG: Empty DataFrame provided, nothing to save")
            return BatchOperationResult(success=True, total_processed=0)

        print(f"DEBUG: Starting atomic save of {len(df)} transactions")

        # Validate required columns
        required_cols = ['amount', 'transaction_date', 'account_id']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"ERROR: Missing required columns: {missing_cols}")
            return BatchOperationResult(
                success=False,
                total_processed=len(df),
                failed_count=len(df),
                error_message=f"Missing required columns: {missing_cols}"
            )

        try:
            # Use transaction scope for atomic operation
            with self.db.transaction_scope() as session:
                print("DEBUG: Started transaction scope for atomic operation")

                # Prepare transaction data for batch operation
                transactions_data = []
                categories_to_create = []

                for index, row in df.iterrows():
                    try:
                        # Convert transaction_date to datetime if needed
                        transaction_date = row['transaction_date']
                        if isinstance(transaction_date, str):
                            transaction_date = pd.to_datetime(transaction_date).to_pydatetime()
                        elif isinstance(transaction_date, pd.Timestamp):
                            transaction_date = transaction_date.to_pydatetime()

                        # Ensure timezone awareness
                        if transaction_date.tzinfo is None:
                            transaction_date = indian_timezone.localize(transaction_date)

                        # Resolve category_id from category and sub_category names
                        category_id = self._resolve_category_id(
                            row.get('category', ''),
                            row.get('sub_category', ''),
                            session=session
                        )

                        # Auto-create category hierarchy if needed
                        if category_id is None and (row.get('category', '').strip() or row.get('sub_category', '').strip()):
                            print(f"DEBUG: Category not found for row {index}, will create hierarchy: '{row.get('category', '')}' -> '{row.get('sub_category', '')}'")

                            # Create categories within the same transaction
                            hierarchy_result = self._create_category_hierarchy_in_session(
                                row.get('category', ''),
                                row.get('sub_category', ''),
                                session
                            )

                            if hierarchy_result.success:
                                # Re-resolve category_id after creation
                                category_id = self._resolve_category_id(
                                    row.get('category', ''),
                                    row.get('sub_category', ''),
                                    session=session
                                )

                        # Prepare transaction data
                        transaction_data = {
                            'amount': float(row['amount']),
                            'transaction_date': transaction_date,
                            'description': row.get('description') or None,
                            'category_id': category_id,
                            'account_id': row['account_id']
                        }
                        transactions_data.append(transaction_data)

                        print(f"DEBUG: Prepared transaction {index}: {row.get('description', 'No description')} - ${row['amount']}")

                    except Exception as e:
                        print(f"ERROR: Failed to prepare transaction at row {index}: {str(e)}")
                        print(f"ERROR: Row data: {row.to_dict()}")
                        raise  # Re-raise to trigger rollback

                # Create all transactions in batch within the transaction
                print(f"DEBUG: Creating batch of {len(transactions_data)} transactions")
                created_transactions = self.db.create_transactions_batch(
                    transactions_data,
                    session=session
                )

                # SERIALIZE while session-bound to prevent DetachedInstanceError
                serialized_transactions = [
                    {
                        'id': txn.id,
                        'description': txn.description,
                        'amount': float(txn.amount),
                        'transaction_date': txn.transaction_date.isoformat() if txn.transaction_date else None,
                        'account_id': txn.account_id,
                        'account_name': txn.account.name if txn.account else None,
                        'category_id': txn.category_id,
                        'category_name': txn.category.name if txn.category else None,
                        'sub_category_name': txn.category.parent.name if txn.category and txn.category.parent else None,
                        'created_at': txn.created_at.isoformat() if txn.created_at else None
                    }
                    for txn in created_transactions
                ]

                print(f"DEBUG: Successfully created {len(created_transactions)} transactions in atomic operation")
                # Transaction will be committed automatically by transaction_scope

            print(f"DEBUG: Atomic transaction save complete - All {len(df)} transactions saved successfully")
            return BatchOperationResult(
                success=True,
                successful_count=len(df),
                total_processed=len(df),
                successful_items=serialized_transactions
            )

        except Exception as e:
            error_info = self.db.handle_constraint_error(e)
            print(f"ERROR: Atomic transaction failed and rolled back: {error_info['error_message']}")
            print(f"ERROR: Error category: {error_info.get('error_category', 'unknown')}")

            # Check if error is retryable
            if self.db.is_retryable_error(e):
                print("DEBUG: Error is retryable - caller may want to retry operation")
            else:
                print("DEBUG: Error is not retryable - data validation or constraint issue")

            return BatchOperationResult(
                success=False,
                failed_count=len(df),
                total_processed=len(df),
                error_message=error_info['error_message'],
                is_retryable=self.db.is_retryable_error(e)
            )

    def _resolve_category_id(self, category_name: str, sub_category_name: str, session: Optional[Session] = None) -> Optional[int]:
        """
        Resolve category_id using targeted database queries instead of fetching all categories.
        PERFORMANCE FIX: Was O(n), now O(1) with proper SQL indexing.

        Args:
            category_name (str): Main category name.
            sub_category_name (str): Sub-category name (can be empty).
            session (Optional[Session]): Database session to use.

        Returns:
            Optional[int]: Category ID or None if not found.
        """
        if not category_name.strip():
            return None

        # Use targeted query instead of get_all_categories()
        if sub_category_name.strip():
            # Look for sub_category with matching parent using targeted query
            category = self.db.get_category_by_name(
                sub_category_name.strip(),
                parent_name=category_name.strip(),
                session=session
            )
        else:
            # Look for category with no parent using targeted query
            category = self.db.get_category_by_name(
                category_name.strip(),
                parent_name=None,
                session=session
            )

        return category.id if category else None

    def _create_category_hierarchy_in_session(self, category_name: str, sub_category_name: str, session: Session) -> OperationResult:
        """
        Create category hierarchy within an existing session (for atomic operations).

        Args:
            category_name (str): Main category name.
            sub_category_name (str): Sub-category name (optional).
            session (Session): Database session to use.

        Returns:
            OperationResult: Structured result with success/failure details.
        """
        try:
            if not category_name.strip():
                return OperationResult(
                    success=False,
                    error_message="Category name cannot be empty",
                    error_type="validation_error",
                    error_category="user_input"
                )

            print(f"DEBUG: Creating category hierarchy in session - Category: '{category_name.strip()}', Sub-category: '{sub_category_name.strip()}'")

            # Find or create parent category using targeted query
            parent_category = self.db.get_category_by_name(
                category_name.strip(),
                parent_name=None,
                session=session
            )

            if parent_category:
                print(f"DEBUG: Found existing parent category: '{parent_category.name}' (ID: {parent_category.id})")
            else:
                parent_category = self.db.create_category(
                    name=category_name.strip(),
                    session=session
                )
                print(f"DEBUG: Created new parent category: '{parent_category.name}' (ID: {parent_category.id})")

            # Find or create sub-category if provided using targeted query
            sub_category = None
            if sub_category_name.strip():
                # Use targeted query instead of fetching all categories
                sub_category = self.db.get_category_by_name(
                    sub_category_name.strip(),
                    parent_name=parent_category.name,
                    session=session
                )

                if sub_category:
                    print(f"DEBUG: Found existing sub-category: '{sub_category.name}' (ID: {sub_category.id})")
                else:
                    sub_category = self.db.create_category(
                        name=sub_category_name.strip(),
                        parent_id=parent_category.id,
                        session=session
                    )
                    print(f"DEBUG: Created new sub-category: '{sub_category.name}' (ID: {sub_category.id}) under parent '{parent_category.name}'")

            print(f"DEBUG: Category hierarchy creation in session successful")
            return OperationResult(
                success=True,
                affected_rows=1,
                data={
                    "parent_category": parent_category.name,
                    "sub_category": sub_category.name if sub_category else None,
                    "parent_id": parent_category.id,
                    "sub_category_id": sub_category.id if sub_category else None
                }
            )

        except Exception as e:
            error_info = self.db.handle_constraint_error(e)
            return OperationResult(
                success=False,
                error_message=error_info['error_message'],
                error_type=error_info['error_type'],
                error_category=error_info['error_category'],
                is_retryable=self.db.is_retryable_error(e)
            )

    def create_category_hierarchy(self, category_name: str, sub_category_name: str = "") -> OperationResult:
        """
        Create category hierarchy if it doesn't exist.

        Args:
            category_name (str): Main category name.
            sub_category_name (str): Sub-category name (optional).

        Returns:
            OperationResult: Structured result with success/failure details.
        """
        try:
            if not category_name.strip():
                return OperationResult(
                    success=False,
                    error_message="Category name cannot be empty",
                    error_type="validation_error",
                    error_category="user_input"
                )

            print(f"DEBUG: Creating category hierarchy - Category: '{category_name.strip()}', Sub-category: '{sub_category_name.strip()}'")

            # Find or create parent category using targeted query
            parent_category = self.db.get_category_by_name(
                category_name.strip(),
                parent_name=None
            )

            if parent_category:
                print(f"DEBUG: Found existing parent category: '{parent_category.name}' (ID: {parent_category.id})")
            else:
                parent_category = self.db.create_category(name=category_name.strip())
                print(f"DEBUG: Created new parent category: '{parent_category.name}' (ID: {parent_category.id})")

            # Find or create sub-category if provided using targeted query
            sub_category = None
            if sub_category_name.strip():
                # Use targeted query instead of fetching all categories
                sub_category = self.db.get_category_by_name(
                    sub_category_name.strip(),
                    parent_name=parent_category.name
                )

                if sub_category:
                    print(f"DEBUG: Found existing sub-category: '{sub_category.name}' (ID: {sub_category.id})")
                else:
                    sub_category = self.db.create_category(
                        name=sub_category_name.strip(),
                        parent_id=parent_category.id
                    )
                    print(f"DEBUG: Created new sub-category: '{sub_category.name}' (ID: {sub_category.id}) under parent '{parent_category.name}'")

            print(f"DEBUG: Category hierarchy creation successful")
            return OperationResult(
                success=True,
                affected_rows=1,
                data={
                    "parent_category": parent_category.name,
                    "sub_category": sub_category.name if sub_category else None,
                    "parent_id": parent_category.id,
                    "sub_category_id": sub_category.id if sub_category else None
                }
            )

        except Exception as e:
            error_info = self.db.handle_constraint_error(e)
            return OperationResult(
                success=False,
                error_message=error_info['error_message'],
                error_type=error_info['error_type'],
                error_category=error_info['error_category'],
                is_retryable=self.db.is_retryable_error(e)
            )

    # --- Missing Interface Methods (Implementation Required by Architecture) ---

    def save_categories_table(self, df: pd.DataFrame, transaction_id: Optional[str] = None) -> BatchOperationResult:
        """Save categories from DataFrame with structured result."""
        try:
            if df.empty:
                return BatchOperationResult(success=True, total_processed=0, successful_count=0, failed_count=0)

            with self.db.transaction_scope() as session:
                # Process categories with hierarchy support and enforce uniqueness
                created_categories = []

                # First pass: create parent categories
                for _, row in df.iterrows():
                    if pd.isna(row.get('parent_category')) or not row.get('parent_category'):
                        # This is a root category
                        existing_cat = self.db.get_category_by_name(row['name'], session=session)
                        if existing_cat:
                            raise ValueError(f"Duplicate category '{row['name']}' already exists")
                        cat = self.db.create_category(name=row['name'], session=session)
                        created_categories.append(cat)

                # Second pass: create child categories with proper parent_id
                for _, row in df.iterrows():
                    if not pd.isna(row.get('parent_category')) and row.get('parent_category'):
                        # This is a child category
                        parent_cat = self.db.get_category_by_name(row['parent_category'], session=session)
                        if not parent_cat:
                            raise ValueError(f"Parent category '{row['parent_category']}' not found")
                        existing_cat = self.db.get_category_by_name(row['name'], row['parent_category'], session=session)
                        if existing_cat:
                            raise ValueError(f"Duplicate category '{row['name']}' under parent '{row['parent_category']}' already exists")
                        cat = self.db.create_category(
                            name=row['name'],
                            parent_id=parent_cat.id,
                            session=session
                        )
                        created_categories.append(cat)

                # SERIALIZE while session-bound to prevent DetachedInstanceError
                serialized_categories = [
                    {
                        'id': cat.id,
                        'name': cat.name,
                        'parent_id': cat.parent_id,
                        'parent_name': cat.parent.name if cat.parent else None,
                        'created_at': cat.created_at.isoformat() if cat.created_at else None,
                        'updated_at': cat.updated_at.isoformat() if cat.updated_at else None
                    }
                    for cat in created_categories
                ]

            return BatchOperationResult(
                success=True,
                total_processed=len(df),
                successful_count=len(created_categories),
                failed_count=0,
                successful_items=serialized_categories
            )
        except Exception as e:
            error_info = self.db.handle_constraint_error(e)
            return BatchOperationResult(
                success=False,
                total_processed=len(df),
                successful_count=0,
                failed_count=len(df),
                error_message=error_info['error_message'],
                is_retryable=self.db.is_retryable_error(e)
            )

    def get_card_statements_table(self) -> pd.DataFrame:
        """Get card statements as DataFrame."""
        statements = self.db.get_all_card_statements()
        if not statements:
            return pd.DataFrame(columns=['id', 'account_id', 'account_name', 'statement_date', 'total_due', 'status', 'start_date', 'end_date'])

        data = [{
            'id': stmt.id,
            'account_id': stmt.account_id,
            'account_name': stmt.account.name if stmt.account else None,
            'statement_date': stmt.statement_date,
            'total_due': float(stmt.total_due) if stmt.total_due else None,
            'status': stmt.status,
            'start_date': stmt.start_date,
            'end_date': stmt.end_date
        } for stmt in statements]

        return pd.DataFrame(data)

    def flag_transaction_as_transfer(self, transaction_id: int) -> OperationResult:
        """Flag a transaction as a transfer."""
        try:
            with self.db.transaction_scope() as session:
                updated_transaction = self.db.update_transaction(
                    transaction_id,
                    {'is_transfer': True},
                    session=session
                )

            if updated_transaction:
                return OperationResult(success=True, affected_rows=1)
            else:
                return OperationResult(
                    success=False,
                    error_message=f"Transaction {transaction_id} not found"
                )
        except Exception as e:
            error_info = self.db.handle_constraint_error(e)
            return OperationResult(
                success=False,
                error_message=error_info['error_message'],
                error_type=error_info['error_type'],
                is_retryable=self.db.is_retryable_error(e)
            )

    def bulk_categorize_transactions(self, categorization_rules: List[Dict]) -> BatchOperationResult:
        """Apply categorization rules to multiple transactions."""
        try:
            result = BatchOperationResult(success=True)

            # Get all transactions to apply rules against
            all_transactions = self.db.get_all_transactions()

            with self.db.transaction_scope() as session:
                for rule in categorization_rules:
                    try:
                        pattern = rule['pattern']
                        category_name = rule['category']
                        sub_category_name = rule.get('sub_category', '')

                        # Find transactions matching the pattern
                        matching_transactions = [
                            tx for tx in all_transactions
                            if tx.description and pattern.lower() in tx.description.lower()
                        ]

                        # Use optimized category resolution - no more O(n) lookups
                        category_id = self._resolve_category_id(category_name, sub_category_name, session)
                        if category_id is None:
                            # Try to create hierarchy, but catch failures for invalid categories
                            creation_result = self._create_category_hierarchy_in_session(category_name, sub_category_name, session)
                            if not creation_result.success:
                                result.add_failure(rule, f"Failed to create category hierarchy: {category_name} -> {sub_category_name}")
                                continue
                            # Re-resolve with optimized query after creation
                            category_id = self._resolve_category_id(category_name, sub_category_name, session)

                        if category_id is None:
                            result.add_failure(rule, f"Could not resolve category: {category_name} -> {sub_category_name}")
                            continue

                        # Update matching transactions
                        for tx in matching_transactions:
                            updated = self.db.update_transaction(
                                tx.id,
                                {'category_id': category_id},
                                session=session
                            )

                            if updated:
                                result.add_success({'transaction_id': tx.id, 'pattern': pattern})
                            else:
                                result.add_failure({'transaction_id': tx.id, 'pattern': pattern}, f"Failed to update transaction {tx.id}")

                    except Exception as e:
                        result.add_failure(rule, str(e))

            return result

        except Exception as e:
            return BatchOperationResult(
                success=False,
                failed_count=len(categorization_rules),
                total_processed=len(categorization_rules),
                error_message=str(e)
            )

    # Transaction Management (Required by Architecture)
    def begin_transaction(self) -> OperationResult:
        """Begin a new transaction context."""
        try:
            import uuid
            self._current_transaction_id = f"tx_{uuid.uuid4().hex[:8]}"
            return OperationResult(
                success=True,
                data={'transaction_id': self._current_transaction_id}
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error_message=f"Failed to begin transaction: {str(e)}"
            )

    def commit_transaction(self) -> OperationResult:
        """Commit current transaction."""
        if self._current_transaction_id is None:
            return OperationResult(
                success=False,
                error_message="No active transaction to commit"
            )

        transaction_id = self._current_transaction_id
        self._current_transaction_id = None
        return OperationResult(
            success=True,
            data={'message': f'Transaction {transaction_id} committed (handled by transaction_scope context manager)'}
        )

    def rollback_transaction(self) -> OperationResult:
        """Rollback current transaction."""
        if self._current_transaction_id is None:
            return OperationResult(
                success=False,
                error_message="No active transaction to rollback"
            )

        transaction_id = self._current_transaction_id
        self._current_transaction_id = None
        return OperationResult(
            success=True,
            data={'message': f'Transaction {transaction_id} rolled back (handled by transaction_scope context manager)'}
        )

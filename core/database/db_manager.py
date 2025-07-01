"""
Database handler class for the expenses tracking tool.
This class encapsulates all CRUD operations and database session management.
"""
import datetime
import pytz
from typing import List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from . import model

# Set the timezone to Indian Standard Time
indian_timezone = pytz.timezone("Asia/Kolkata")


class Database:
    """
    Handles all database operations, including session management and CRUD.
    """

    def __init__(self, db_url: str = "sqlite:///expenses.db"):
        """
        Initializes the database connection, creates tables if they don't exist,
        and sets up a sessionmaker.

        Args:
            db_url (str): The database connection URL. Defaults to "sqlite:///expenses.db".
        """
        # The connect_args is specific to SQLite and is required for multithreaded access.
        connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
        self.engine = create_engine(db_url, connect_args=connect_args)
        
        # Create all tables defined in the model package
        model.Base.metadata.create_all(self.engine)
        
        self._session_local = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def _get_db_session(self) -> Session:
        """
        Provides a new database session.
        """
        return self._session_local()

    # --- Category CRUD Methods ---

    def create_category(self, name: str, parent_id: Optional[int] = None) -> model.Category:
        """
        Creates a new category in the database.

        Args:
            name (str): The name for the new category.
            parent_id (Optional[int]): The ID of the parent category, if any.

        Returns:
            model.Category: The newly created category object.
        """
        db = self._get_db_session()
        try:
            db_category = model.Category(
                name=name, 
                parent_id=parent_id, 
                created_at=datetime.datetime.now(indian_timezone)
            )
            db.add(db_category)
            db.commit()
            db.refresh(db_category)
            return db_category
        finally:
            db.close()

    def get_category(self, category_id: int) -> Optional[model.Category]:
        """
        Retrieves a single category by its ID.

        Args:
            category_id (int): The ID of the category to retrieve.

        Returns:
            Optional[model.Category]: The category object if found, otherwise None.
        """
        db = self._get_db_session()
        try:
            return db.query(model.Category).filter(model.Category.id == category_id).first()
        finally:
            db.close()

    def get_all_categories(self) -> List[model.Category]:
        """
        Retrieves all categories from the database.

        Returns:
            List[model.Category]: A list of all category objects.
        """
        db = self._get_db_session()
        try:
            return db.query(model.Category).all()
        finally:
            db.close()

    def update_category(self, category_id: int, name: str, parent_id: Optional[int] = None) -> Optional[model.Category]:
        """
        Updates an existing category.

        Args:
            category_id (int): The ID of the category to update.
            name (str): The new name for the category.
            parent_id (Optional[int]): The new parent ID for the category.

        Returns:
            Optional[model.Category]: The updated category object, or None if not found.
        """
        db = self._get_db_session()
        try:
            db_category = db.query(model.Category).filter(model.Category.id == category_id).first()
            if db_category:
                db_category.name = name
                db_category.parent_id = parent_id
                db_category.updated_at = datetime.datetime.now(indian_timezone)
                db.commit()
                db.refresh(db_category)
            return db_category
        finally:
            db.close()

    def delete_category(self, category_id: int) -> bool:
        """
        Deletes a category from the database.

        Args:
            category_id (int): The ID of the category to delete.

        Returns:
            bool: True if the category was deleted, False otherwise.
        """
        db = self._get_db_session()
        try:
            db_category = db.query(model.Category).filter(model.Category.id == category_id).first()
            if db_category:
                db.delete(db_category)
                db.commit()
                return True
            return False
        finally:
            db.close()

    # --- Transaction CRUD Methods ---

    def create_transaction(
        self,
        amount: float,
        transaction_date: datetime.datetime,
        description: Optional[str] = None,
        category_id: Optional[int] = None,
    ) -> model.Transaction:
        """
        Creates a new transaction.

        Args:
            amount (float): The amount of the transaction.
            transaction_date (datetime.datetime): The date and time of the transaction.
            description (Optional[str]): A description for the transaction.
            category_id (Optional[int]): The ID of the category for this transaction.

        Returns:
            model.Transaction: The newly created transaction object.
        """
        db = self._get_db_session()
        try:
            db_transaction = model.Transaction(
                amount=amount,
                transaction_date=transaction_date,
                description=description,
                category_id=category_id,
                created_at=datetime.datetime.now(indian_timezone),
            )
            db.add(db_transaction)
            db.commit()
            db.refresh(db_transaction)
            return db_transaction
        finally:
            db.close()

    def get_transaction(self, transaction_id: int) -> Optional[model.Transaction]:
        """
        Retrieves a single transaction by its ID.

        Args:
            transaction_id (int): The ID of the transaction to retrieve.

        Returns:
            Optional[model.Transaction]: The transaction object if found, otherwise None.
        """
        db = self._get_db_session()
        try:
            return db.query(model.Transaction).filter(model.Transaction.id == transaction_id).first()
        finally:
            db.close()

    def get_all_transactions(self) -> List[model.Transaction]:
        """
        Retrieves all transactions from the database.

        Returns:
            List[model.Transaction]: A list of all transaction objects.
        """
        db = self._get_db_session()
        try:
            return db.query(model.Transaction).all()
        finally:
            db.close()

    def update_transaction(
        self,
        transaction_id: int,
        amount: float,
        transaction_date: datetime.datetime,
        description: Optional[str] = None,
        category_id: Optional[int] = None,
    ) -> Optional[model.Transaction]:
        """
        Updates an existing transaction.

        Args:
            transaction_id (int): The ID of the transaction to update.
            amount (float): The new amount for the transaction.
            transaction_date (datetime.datetime): The new date for the transaction.
            description (Optional[str]): The new description for the transaction.
            category_id (Optional[int]): The new category ID for the transaction.

        Returns:
            Optional[model.Transaction]: The updated transaction object, or None if not found.
        """
        db = self._get_db_session()
        try:
            db_transaction = db.query(model.Transaction).filter(model.Transaction.id == transaction_id).first()
            if db_transaction:
                db_transaction.amount = amount
                db_transaction.transaction_date = transaction_date
                db_transaction.description = description
                db_transaction.category_id = category_id
                db_transaction.updated_at = datetime.datetime.now(indian_timezone)
                db.commit()
                db.refresh(db_transaction)
            return db_transaction
        finally:
            db.close()

    def delete_transaction(self, transaction_id: int) -> bool:
        """
        Deletes a transaction from the database.

        Args:
            transaction_id (int): The ID of the transaction to delete.

        Returns:
            bool: True if the transaction was deleted, False otherwise.
        """
        db = self._get_db_session()
        try:
            db_transaction = db.query(model.Transaction).filter(model.Transaction.id == transaction_id).first()
            if db_transaction:
                db.delete(db_transaction)
                db.commit()
                return True
            return False
        finally:
            db.close()

"""
CRUD operations for the expenses tracking tool.
"""
from typing import List, Optional
import datetime
import pytz

from sqlalchemy.orm import Session

from . import model

# Set the timezone to Indian Standard Time
indian_timezone = pytz.timezone("Asia/Kolkata")


# Category CRUD
def create_category(db: Session, name: str, parent_id: Optional[int] = None) -> model.Category:
    """
    Creates a new category.

    Args:
        db (Session): Database session.
        name (str): Name of the category.
        parent_id (Optional[int]): ID of the parent category.

    Returns:
        model.Category: The created category.
    """
    db_category = model.Category(name=name, parent_id=parent_id, created_at=datetime.datetime.now(indian_timezone))
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def get_category(db: Session, category_id: int) -> Optional[model.Category]:
    """
    Gets a category by its ID.

    Args:
        db (Session): Database session.
        category_id (int): ID of the category.

    Returns:
        Optional[model.Category]: The category, or None if not found.
    """
    return db.query(model.Category).filter(model.Category.id == category_id).first()


def get_all_categories(db: Session) -> List[model.Category]:
    """
    Gets all categories.

    Args:
        db (Session): Database session.

    Returns:
        List[model.Category]: A list of all categories.
    """
    return db.query(model.Category).all()


def update_category(
    db: Session, category_id: int, name: str, parent_id: Optional[int] = None
) -> Optional[model.Category]:
    """
    Updates a category.

    Args:
        db (Session): Database session.
        category_id (int): ID of the category to update.
        name (str): New name of the category.
        parent_id (Optional[int]): New ID of the parent category.

    Returns:
        Optional[model.Category]: The updated category, or None if not found.
    """
    db_category = get_category(db, category_id)
    if db_category:
        db_category.name = name
        db_category.parent_id = parent_id
        db_category.updated_at = datetime.datetime.now(indian_timezone)
        db.commit()
        db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: int) -> bool:
    """
    Deletes a category.

    Args:
        db (Session): Database session.
        category_id (int): ID of the category to delete.

    Returns:
        bool: True if the category was deleted, False otherwise.
    """
    db_category = get_category(db, category_id)
    if db_category:
        db.delete(db_category)
        db.commit()
        return True
    return False


# Transaction CRUD
def create_transaction(
    db: Session,
    amount: float,
    transaction_date: datetime.datetime,
    description: Optional[str] = None,
    category_id: Optional[int] = None,
) -> model.Transaction:
    """
    Creates a new transaction.

    Args:
        db (Session): Database session.
        amount (float): Amount of the transaction.
        transaction_date (datetime.datetime): Date of the transaction.
        description (Optional[str]): Description of the transaction.
        category_id (Optional[int]): ID of the category.

    Returns:
        model.Transaction: The created transaction.
    """
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


def get_transaction(db: Session, transaction_id: int) -> Optional[model.Transaction]:
    """
    Gets a transaction by its ID.

    Args:
        db (Session): Database session.
        transaction_id (int): ID of the transaction.

    Returns:
        Optional[model.Transaction]: The transaction, or None if not found.
    """
    return db.query(model.Transaction).filter(model.Transaction.id == transaction_id).first()


def get_all_transactions(db: Session) -> List[model.Transaction]:
    """
    Gets all transactions.

    Args:
        db (Session): Database session.

    Returns:
        List[model.Transaction]: A list of all transactions.
    """
    return db.query(model.Transaction).all()


def update_transaction(
    db: Session,
    transaction_id: int,
    amount: float,
    transaction_date: datetime.datetime,
    description: Optional[str] = None,
    category_id: Optional[int] = None,
) -> Optional[model.Transaction]:
    """
    Updates a transaction.

    Args:
        db (Session): Database session.
        transaction_id (int): ID of the transaction to update.
        amount (float): New amount of the transaction.
        transaction_date (datetime.datetime): New date of the transaction.
        description (Optional[str]): New description of the transaction.
        category_id (Optional[int]): New ID of the category.

    Returns:
        Optional[model.Transaction]: The updated transaction, or None if not found.
    """
    db_transaction = get_transaction(db, transaction_id)
    if db_transaction:
        db_transaction.amount = amount
        db_transaction.transaction_date = transaction_date
        db_transaction.description = description
        db_transaction.category_id = category_id
        db_transaction.updated_at = datetime.datetime.now(indian_timezone)
        db.commit()
        db.refresh(db_transaction)
    return db_transaction


def delete_transaction(db: Session, transaction_id: int) -> bool:
    """
    Deletes a transaction.

    Args:
        db (Session): Database session.
        transaction_id (int): ID of the transaction to delete.

    Returns:
        bool: True if the transaction was deleted, False otherwise.
    """
    db_transaction = get_transaction(db, transaction_id)
    if db_transaction:
        db.delete(db_transaction)
        db.commit()
        return True
    return False
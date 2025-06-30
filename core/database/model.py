
"""
SQLAlchemy models for the expenses tracking tool.
"""
import datetime
from typing import List, Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship, declarative_base


Base = declarative_base()


class Category(Base):
    """
    Represents a category for transactions.

    Attributes:
        id (int): Primary key.
        name (str): Name of the category.
        parent_id (int): Foreign key to the parent category.
        created_at (datetime): Timestamp of creation.
        updated_at (datetime): Timestamp of last update.
        parent (Category): Parent category.
        transactions (List[Transaction]): List of transactions in this category.
    """

    __tablename__ = "categories"

    id: int = Column(Integer, primary_key=True)
    name: str = Column(String, nullable=False)
    parent_id: Optional[int] = Column(Integer, ForeignKey("categories.id"))
    created_at: datetime.datetime = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at: datetime.datetime = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    parent: Optional["Category"] = relationship("Category", remote_side=[id])
    transactions: List["Transaction"] = relationship("Transaction", back_populates="category")

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}')>"


class Transaction(Base):
    """
    Represents a financial transaction.

    Attributes:
        id (int): Primary key.
        description (str): Description of the transaction.
        amount (Numeric): Amount of the transaction.
        transaction_date (datetime): Date of the transaction.
        category_id (int): Foreign key to the category.
        embedding (str): Embedding of the transaction description for AI semantic search.
        created_at (datetime): Timestamp of creation.
        updated_at (datetime): Timestamp of last update.
        category (Category): Category of the transaction.
    """

    __tablename__ = "transactions"

    id: int = Column(Integer, primary_key=True)
    description: Optional[str] = Column(String)
    amount: float = Column(Numeric, nullable=False)
    transaction_date: datetime.datetime = Column(DateTime, nullable=False)
    category_id: Optional[int] = Column(Integer, ForeignKey("categories.id"))
    embedding: Optional[str] = Column(Text)  # Using Text to store vector as string for db compatibility
    created_at: datetime.datetime = Column(DateTime, default=datetime.datetime.now())
    updated_at: datetime.datetime = Column(
        DateTime, default=datetime.datetime.now(), onupdate=datetime.datetime.now()
    )

    category: Optional["Category"] = relationship("Category", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, description='{self.description}', amount={self.amount})>"

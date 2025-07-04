"""
SQLAlchemy models for the expenses tracking tool.
"""
import datetime
from typing import List, Optional
import pytz

from sqlalchemy import (
    Integer,
    String,
    Numeric,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship, declarative_base, Mapped, mapped_column


Base = declarative_base()
indian_timezone = pytz.timezone("Asia/Kolkata")


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

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.id"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now(indian_timezone))
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.now(indian_timezone), onupdate=datetime.datetime.now(indian_timezone)
    )

    parent: Mapped[Optional["Category"]] = relationship("Category", remote_side=[id])
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="category")

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

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(String)
    amount: Mapped[float] = mapped_column(Numeric, nullable=False)
    transaction_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.id"))
    embedding: Mapped[Optional[str]] = mapped_column(Text)  # Using Text to store vector as string for db compatibility
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now(indian_timezone))
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.now(indian_timezone), onupdate=datetime.datetime.now(indian_timezone)
    )

    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, description='{self.description}', amount={self.amount})>"
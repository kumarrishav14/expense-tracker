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
    Boolean,
    Date,
)
from sqlalchemy.orm import relationship, declarative_base, Mapped, mapped_column


Base = declarative_base()
indian_timezone = pytz.timezone("Asia/Kolkata")


class Account(Base):
    """
    Represents a user-defined financial account.

    Attributes:
        id (int): Primary key.
        name (str): User-defined name for the account (e.g., "HDFC Regalia").
        account_type (str): Type of account (e.g., 'Credit Card', 'Bank Account').
        bank_name (str): Name of the bank.
        account_number_last4 (str): Last four digits of the account number.
        is_active (bool): Flag for soft deletion.
        file_fingerprint (str): Unique hash of a CSV file's format.
        transactions (List[Transaction]): List of transactions in this account.
        statements (List[CardStatement]): List of statements for this account.
    """
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    account_type: Mapped[str] = mapped_column(String, nullable=False)
    bank_name: Mapped[Optional[str]] = mapped_column(String)
    account_number_last4: Mapped[Optional[str]] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    file_fingerprint: Mapped[Optional[str]] = mapped_column(String, unique=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now(indian_timezone))
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.now(indian_timezone), onupdate=datetime.datetime.now(indian_timezone)
    )

    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="account")
    statements: Mapped[List["CardStatement"]] = relationship("CardStatement", back_populates="account")

    def __repr__(self) -> str:
        return f"<Account(id={self.id}, name='{self.name}')>"


class CardStatement(Base):
    """
    Represents metadata for a credit card statement.

    Attributes:
        id (int): Primary key.
        account_id (int): Foreign key to the account.
        statement_date (date): The closing date of the statement.
        start_date (date): The start date of the statement period.
        end_date (date): The end date of the statement period.
        total_due (float): The total amount due on the statement.
        status (str): The payment status of the statement.
        account (Account): The account this statement belongs to.
        transactions (List[Transaction]): Transactions included in this statement.
        transfers (List[Transfer]): Payments made towards this statement.
    """
    __tablename__ = "card_statements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False)
    statement_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    start_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    end_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    total_due: Mapped[Optional[float]] = mapped_column(Numeric)
    status: Mapped[str] = mapped_column(String, default='UNPAID', nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now(indian_timezone))
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.now(indian_timezone), onupdate=datetime.datetime.now(indian_timezone)
    )

    account: Mapped["Account"] = relationship("Account", back_populates="statements")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="statement")
    transfers: Mapped[List["Transfer"]] = relationship("Transfer", back_populates="statement")

    def __repr__(self) -> str:
        return f"<CardStatement(id={self.id}, account_id={self.account_id}, date='{self.statement_date}')>"


class Transfer(Base):
    """
    Represents an auditable link for a credit card payment.

    Attributes:
        id (int): Primary key.
        payment_transaction_id (int): The transaction from a bank account paying the bill.
        statement_id (int): The credit card statement being paid.
        matched_rule (str): The rule used to match the payment.
        payment_transaction (Transaction): The payment transaction.
        statement (CardStatement): The statement being paid.
    """
    __tablename__ = "transfers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_transaction_id: Mapped[int] = mapped_column(Integer, ForeignKey("transactions.id"), nullable=False, unique=True)
    statement_id: Mapped[int] = mapped_column(Integer, ForeignKey("card_statements.id"), nullable=False)
    matched_rule: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now(indian_timezone))
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.now(indian_timezone), onupdate=datetime.datetime.now(indian_timezone)
    )

    payment_transaction: Mapped["Transaction"] = relationship("Transaction", foreign_keys=[payment_transaction_id])
    statement: Mapped["CardStatement"] = relationship("CardStatement", back_populates="transfers")

    def __repr__(self) -> str:
        return f"<Transfer(id={self.id}, payment_id={self.payment_transaction_id}, statement_id={self.statement_id})>"


class Category(Base):
    """
    Represents a category for transactions.
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
    """
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(String)
    amount: Mapped[float] = mapped_column(Numeric, nullable=False)
    transaction_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.id"))
    embedding: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now(indian_timezone))
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.now(indian_timezone), onupdate=datetime.datetime.now(indian_timezone)
    )

    # New fields for Account Management and Credit Mapping
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False)
    statement_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("card_statements.id"))
    is_transfer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    transfer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("transfers.id"))

    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="transactions")
    account: Mapped["Account"] = relationship("Account", back_populates="transactions")
    statement: Mapped[Optional["CardStatement"]] = relationship("CardStatement", back_populates="transactions")
    transfer: Mapped[Optional["Transfer"]] = relationship("Transfer", foreign_keys=[transfer_id])


    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, description='{self.description}', amount={self.amount})>"

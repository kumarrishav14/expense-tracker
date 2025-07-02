"""
Configurations and fixtures for database tests.
"""
import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from core.database.db_manager import Database
from core.database.model import Base

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_instance(monkeypatch):
    """
    Provides a clean, isolated database instance for each test function.
    - Creates a new in-memory SQLite database for each test.
    - Monkeypatches the Database.get_session method to provide an isolated session.
    - Yields a `Database` manager instance connected to this test database.
    - Ensures the database is properly torn down after each test.
    """
    # Each test gets its own in-memory database
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create a sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    # Create a Database instance
    db = Database(db_url=TEST_DATABASE_URL)

    # Monkeypatch the get_session method to return our test session
    monkeypatch.setattr(db, "get_session", lambda: session)
    
    try:
        yield db
    finally:
        # Close the session and drop all tables
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
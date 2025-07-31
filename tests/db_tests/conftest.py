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
import tempfile
import uuid

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "sanity: Critical database tests for quick validation after changes"
    )


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


@pytest.fixture(scope="function")
def persistent_db_instance():
    """
    Provides a persistent database instance for workflow tests that need
    data persistence across operations.

    This fixture creates a real SQLite file database that allows data
    to persist across different session contexts, solving the session
    isolation issues seen in workflow tests.

    Use this fixture for tests that:
    - Save data and then retrieve it to verify persistence
    - Perform multi-step operations that need to see each other's results
    - Test complex workflows involving multiple database operations

    Returns:
        tuple: (Database instance, db_url) for use in tests
    """
    # Create a temporary file for the test database
    temp_dir = tempfile.gettempdir()
    db_filename = f"test_db_{uuid.uuid4().hex}.sqlite"
    db_path = os.path.join(temp_dir, db_filename)
    db_url = f"sqlite:///{db_path}"

    try:
        # Create engine and database instance
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(engine)

        # Create Database instance - it will manage its own sessions
        db = Database(db_url=db_url)

        yield (db, db_url)

    finally:
        # Clean up: close any open connections and remove the file
        if hasattr(db, 'engine'):
            db.engine.dispose()
        engine.dispose()

        # Remove the temporary database file
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
        except OSError:
            pass  # File might already be deleted or locked

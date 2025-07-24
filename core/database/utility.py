"""
Admin related utility tasks for the database.

This script can be run from the command line to perform database management tasks.

Usage:
    python -m core.database.utility <command> [options]

Commands:
    visualise           Visualise a table or all tables.
    delete              Delete a table or all tables.

Examples:
    python -m core.database.utility visualise --table_name categories
    python -m core.database.utility visualise --all
    python -m core.database.utility delete --table_name categories
    python -m core.database.utility delete --all
"""
import argparse
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
import pandas as pd

from core.database.model import Base

DATABASE_URL = "sqlite:///expenses.db"

def visualise_table(session: Session, table_name: str):
    """
    Visualises a particular table as a simple read and print.

    Args:
        session (Session): Database session.
        table_name (str): Name of the table to visualise.
    """
    try:
        df = pd.read_sql_table(table_name, session.bind)
        print(f"Table: {table_name}")
        # Exclude 'created_at' and 'updated_at' columns if present
        exclude_cols = [col for col in ['created_at', 'updated_at'] if col in df.columns]
        print(df.drop(columns=exclude_cols))
    except Exception as e:
        print(f"Error visualising table {table_name}: {e}")


def visualise_all_tables(session: Session):
    """
    Visualises all tables of DB as a simple read and print.

    Args:
        session (Session): Database session.
    """
    inspector = inspect(session.bind)
    table_names = inspector.get_table_names()
    if not table_names:
        print("No tables found in the database.")
        return
    for table_name in table_names:
        visualise_table(session, table_name)
        print("\n")


def delete_table(session: Session, table_name: str):
    """
    Deletes a particular table from the DB.

    Args:
        session (Session): Database session.
        table_name (str): Name of the table to delete.
    """
    try:
        table = Base.metadata.tables[table_name]
        table.drop(session.bind)
        print(f"Table '{table_name}' deleted successfully.")
    except KeyError:
        print(f"Error: Table '{table_name}' not found.")
    except Exception as e:
        print(f"Error deleting table {table_name}: {e}")


def delete_all_tables(session: Session):
    """
    Deletes all tables from DB.

    Args:
        session (Session): Database session.
    """
    try:
        Base.metadata.drop_all(session.bind)
        print("All tables deleted successfully.")
    except Exception as e:
        print(f"Error deleting all tables: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Database admin utility.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands.")

    # Visualise command
    parser_visualise = subparsers.add_parser("visualise", help="Visualise a table or all tables.")
    visualise_group = parser_visualise.add_mutually_exclusive_group(required=True)
    visualise_group.add_argument("--table_name", type=str, help="Name of the table to visualise.")
    visualise_group.add_argument("--all", action="store_true", help="Visualise all tables.")

    # Delete command
    parser_delete = subparsers.add_parser("delete", help="Delete a table or all tables.")
    delete_group = parser_delete.add_mutually_exclusive_group(required=True)
    delete_group.add_argument("--table_name", type=str, help="Name of the table to delete.")
    delete_group.add_argument("--all", action="store_true", help="Delete all tables.")

    args = parser.parse_args()

    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = SessionLocal()

    try:
        if args.command == "visualise":
            if args.all:
                visualise_all_tables(db_session)
            else:
                visualise_table(db_session, args.table_name)
        elif args.command == "delete":
            if args.all:
                delete_all_tables(db_session)
            else:
                delete_table(db_session, args.table_name)
    finally:
        db_session.close()
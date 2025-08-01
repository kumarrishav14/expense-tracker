"""
Admin related utility tasks for the database.

This script can be run from the command line to perform database management tasks.
Enhanced to use the established Database class architecture for consistency and safety.

Usage:
    python -m core.database.utility <command> [options]

Commands:
    visualise           Visualise a table or all tables.
    delete              Delete a table or all tables.
    backup              Create a backup of the database.
    restore             Restore database from backup.

Examples:
    python -m core.database.utility visualise --table_name categories
    python -m core.database.utility visualise --all
    python -m core.database.utility delete --table_name categories --confirm
    python -m core.database.utility delete --all --confirm
    python -m core.database.utility backup --output backup.db
"""
import argparse
import shutil
import os
from datetime import datetime
from sqlalchemy import inspect
import pandas as pd

from core.database.db_manager import Database
from core.database.model import Base

def visualise_table(db: Database, table_name: str):
    """
    Visualises a particular table as a simple read and print.
    Enhanced with better formatting and error handling.

    Args:
        db (Database): Database instance.
        table_name (str): Name of the table to visualise.
    """
    try:
        with db.get_session() as session:
            with session.connection() as conn:
                df = pd.read_sql_table(table_name, conn)
            
            print(f"\n{'='*60}")
            print(f"TABLE: {table_name.upper()}")
            print(f"{'='*60}")
            print(f"Total rows: {len(df)}")
            
            if df.empty:
                print("No data found in this table.")
                return
            
            # Exclude timestamp columns for cleaner display
            exclude_cols = [col for col in ['created_at', 'updated_at'] if col in df.columns]
            display_df = df.drop(columns=exclude_cols) if exclude_cols else df
            
            # Limit display for large tables
            if len(display_df) > 50:
                print(f"Showing first 50 rows (total: {len(display_df)} rows)")
                print(display_df.head(50).to_string(index=False))
                print(f"\n... and {len(display_df) - 50} more rows")
            else:
                print(display_df.to_string(index=False))
                
    except Exception as e:
        error_info = db.handle_constraint_error(e)
        print(f"❌ Error visualising table '{table_name}': {error_info['error_message']}")
        print(f"   Error type: {error_info['error_type']}")


def visualise_all_tables(db: Database):
    """
    Visualises all tables of DB as a simple read and print.
    Enhanced with table statistics and better organization.

    Args:
        db (Database): Database instance.
    """
    try:
        with db.get_session() as session:
            inspector = inspect(db.engine)
            table_names = inspector.get_table_names()
            
            if not table_names:
                print("No tables found in the database.")
                return
            
            print(f"\n{'='*80}")
            print(f"DATABASE OVERVIEW - {len(table_names)} tables found")
            print(f"{'='*80}")
            
            # Show table summary first
            print("\nTable Summary:")
            print("-" * 40)
            for table_name in table_names:
                try:
                    with session.connection() as conn:
                        df = pd.read_sql_table(table_name, conn)
                    print(f"  {table_name:<20} : {len(df):>6} rows")
                except Exception as e:
                    print(f"  {table_name:<20} : Error reading")
            
            print("\nDetailed Table Contents:")
            print("-" * 40)
            
            for table_name in table_names:
                visualise_table(db, table_name)
                
    except Exception as e:
        print(f"❌ Error accessing database: {str(e)}")


def delete_table(db: Database, table_name: str, confirm: bool = False):
    """
    Deletes a particular table from the DB with safety checks.
    Enhanced with confirmation prompts and better error handling.

    Args:
        db (Database): Database instance.
        table_name (str): Name of the table to delete.
        confirm (bool): Whether to skip confirmation prompt.
    """
    try:
        # Safety check - show table info first
        with db.get_session() as session:
            inspector = inspect(db.engine)
            table_names = inspector.get_table_names()
            
            if table_name not in table_names:
                print(f"❌ Error: Table '{table_name}' not found.")
                print(f"Available tables: {', '.join(table_names)}")
                return
            
            # Show table contents before deletion
            with session.connection() as conn:
                df = pd.read_sql_table(table_name, conn)
            print(f"\n⚠️  About to delete table '{table_name}' with {len(df)} rows")
            
            if not confirm:
                response = input("Are you sure you want to delete this table? (yes/no): ")
                if response.lower() not in ['yes', 'y']:
                    print("❌ Operation cancelled.")
                    return
            
            # Perform deletion
            table = Base.metadata.tables[table_name]
            table.drop(session.bind)
            print(f"✅ Table '{table_name}' deleted successfully.")
            
    except KeyError:
        print(f"❌ Error: Table '{table_name}' not found in metadata.")
    except Exception as e:
        error_info = db.handle_constraint_error(e)
        print(f"❌ Error deleting table '{table_name}': {error_info['error_message']}")
        print(f"   Error type: {error_info['error_type']}")


def delete_all_tables(db: Database, confirm: bool = False):
    """
    Deletes all tables from DB with enhanced safety checks.
    Enhanced with confirmation prompts and backup suggestion.

    Args:
        db (Database): Database instance.
        confirm (bool): Whether to skip confirmation prompt.
    """
    try:
        with db.get_session() as session:
            inspector = inspect(db.engine)
            table_names = inspector.get_table_names()
            
            if not table_names:
                print("No tables found in the database.")
                return
            
            print(f"\n⚠️  DANGER: About to delete ALL {len(table_names)} tables:")
            for table_name in table_names:
                try:
                    with session.connection() as conn:
                        df = pd.read_sql_table(table_name, conn)
                    print(f"  - {table_name}: {len(df)} rows")
                except:
                    print(f"  - {table_name}: (unable to read)")
            
            print(f"\n💡 Consider creating a backup first:")
            print(f"   python -m core.database.utility backup --output backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            
            if not confirm:
                print(f"\n🚨 This action cannot be undone!")
                response = input("Type 'DELETE ALL TABLES' to confirm: ")
                if response != 'DELETE ALL TABLES':
                    print("❌ Operation cancelled.")
                    return
            
            # Perform deletion
            Base.metadata.drop_all(session.bind)
            print("✅ All tables deleted successfully.")
            
    except Exception as e:
        error_info = db.handle_constraint_error(e)
        print(f"❌ Error deleting all tables: {error_info['error_message']}")
        print(f"   Error type: {error_info['error_type']}")


def backup_database(db: Database, output_path: str):
    """
    Create a backup of the database file.
    
    Args:
        db (Database): Database instance.
        output_path (str): Path for the backup file.
    """
    try:
        # For SQLite, we can simply copy the file
        source_path = "expenses.db"  # Default database file
        
        if not os.path.exists(source_path):
            print(f"❌ Source database file '{source_path}' not found.")
            return
        
        # Ensure backup directory exists
        backup_dir = os.path.dirname(output_path)
        if backup_dir and not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Create backup
        shutil.copy2(source_path, output_path)
        
        # Verify backup
        backup_size = os.path.getsize(output_path)
        source_size = os.path.getsize(source_path)
        
        if backup_size == source_size:
            print(f"✅ Database backup created successfully:")
            print(f"   Source: {source_path} ({source_size:,} bytes)")
            print(f"   Backup: {output_path} ({backup_size:,} bytes)")
        else:
            print(f"⚠️  Backup created but size mismatch detected:")
            print(f"   Source: {source_size:,} bytes")
            print(f"   Backup: {backup_size:,} bytes")
            
    except Exception as e:
        print(f"❌ Error creating backup: {str(e)}")


def restore_database(db: Database, backup_path: str, confirm: bool = False):
    """
    Restore database from a backup file.
    
    Args:
        db (Database): Database instance.
        backup_path (str): Path to the backup file.
        confirm (bool): Whether to skip confirmation prompt.
    """
    try:
        target_path = "expenses.db"  # Default database file
        
        if not os.path.exists(backup_path):
            print(f"❌ Backup file '{backup_path}' not found.")
            return
        
        # Show current database info
        if os.path.exists(target_path):
            current_size = os.path.getsize(target_path)
            print(f"⚠️  Current database: {target_path} ({current_size:,} bytes)")
        else:
            print(f"ℹ️  No existing database found at {target_path}")
        
        backup_size = os.path.getsize(backup_path)
        print(f"📁 Backup file: {backup_path} ({backup_size:,} bytes)")
        
        if not confirm:
            print(f"\n🚨 This will overwrite the current database!")
            response = input("Are you sure you want to restore from backup? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("❌ Operation cancelled.")
                return
        
        # Create backup of current database before restore
        if os.path.exists(target_path):
            backup_current = f"expenses_backup_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(target_path, backup_current)
            print(f"💾 Current database backed up to: {backup_current}")
        
        # Restore from backup
        shutil.copy2(backup_path, target_path)
        
        # Verify restore
        restored_size = os.path.getsize(target_path)
        if restored_size == backup_size:
            print(f"✅ Database restored successfully from backup.")
        else:
            print(f"⚠️  Restore completed but size mismatch detected.")
            
    except Exception as e:
        print(f"❌ Error restoring database: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Enhanced database admin utility with safety features.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m core.database.utility visualise --all
  python -m core.database.utility visualise --table_name transactions
  python -m core.database.utility delete --table_name categories --confirm
  python -m core.database.utility backup --output backup.db
  python -m core.database.utility restore --backup backup.db
        """
    )
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
    parser_delete.add_argument("--confirm", action="store_true", help="Skip confirmation prompts.")

    # Backup command
    parser_backup = subparsers.add_parser("backup", help="Create a backup of the database.")
    parser_backup.add_argument("--output", type=str, required=True, help="Output path for backup file.")

    # Restore command
    parser_restore = subparsers.add_parser("restore", help="Restore database from backup.")
    parser_restore.add_argument("--backup", type=str, required=True, help="Path to backup file.")
    parser_restore.add_argument("--confirm", action="store_true", help="Skip confirmation prompts.")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        exit(1)

    # Initialize Database instance using established architecture
    try:
        db = Database()  # Uses default "sqlite:///expenses.db"
        print(f"🔗 Connected to database successfully")
        
        if args.command == "visualise":
            if args.all:
                visualise_all_tables(db)
            else:
                visualise_table(db, args.table_name)
                
        elif args.command == "delete":
            if args.all:
                delete_all_tables(db, confirm=args.confirm)
            else:
                delete_table(db, args.table_name, confirm=args.confirm)
                
        elif args.command == "backup":
            backup_database(db, args.output)
            
        elif args.command == "restore":
            restore_database(db, args.backup, confirm=args.confirm)
            
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        print(f"   Make sure the database is accessible and not in use by another process.")
        exit(1)
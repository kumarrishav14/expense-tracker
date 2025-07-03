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
from .model import Category, Transaction

# Set the timezone to Indian Standard Time
indian_timezone = pytz.timezone("Asia/Kolkata")


class DatabaseInterface:
    """
    Simplified interface for converting between pandas DataFrames and database tables.
    
    Other components work with denormalized DataFrames (no foreign keys), while this
    interface handles all SQL relationship complexity internally.
    """
    
    def __init__(self, db_url: str = "sqlite:///expenses.db"):
        """
        Initialize the database interface.
        
        Args:
            db_url (str): Database connection URL.
        """
        self.db = Database(db_url)
    
    # --- Export methods (DB to pandas) ---
    
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
                'description', 'amount', 'transaction_date', 'category', 'sub_category'
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
                'sub_category': sub_category
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Convert datetime column to proper pandas datetime
        if 'transaction_date' in df.columns:
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        
        return df
    
    # --- Import methods (pandas to DB) ---
    
    def save_transactions_table(self, df: pd.DataFrame) -> bool:
        """
        Save transactions from denormalized DataFrame to database.
        
        Args:
            df (pd.DataFrame): DataFrame with columns [description, amount, transaction_date, 
                              category, sub_category]
            
        Returns:
            bool: True if all transactions saved successfully, False otherwise.
        """
        if df.empty:
            print("DEBUG: Empty DataFrame provided, nothing to save")
            return True
        
        print(f"DEBUG: Starting to save {len(df)} transactions")
        
        # Validate required columns
        required_cols = ['amount', 'transaction_date']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"ERROR: Missing required columns: {missing_cols}")
            return False
        
        saved_count = 0
        failed_count = 0
        
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
                    row.get('sub_category', '')
                )
                
                if category_id is None and (row.get('category', '').strip() or row.get('sub_category', '').strip()):
                    print(f"DEBUG: Category not found for row {index}, creating hierarchy: '{row.get('category', '')}' -> '{row.get('sub_category', '')}'")
                    # Auto-create category hierarchy if names provided but not found
                    hierarchy_created = self.create_category_hierarchy(
                        row.get('category', ''), 
                        row.get('sub_category', '')
                    )
                    if hierarchy_created:
                        # Re-resolve category_id after creation
                        category_id = self._resolve_category_id(
                            row.get('category', ''), 
                            row.get('sub_category', '')
                        )
                
                # Create transaction
                transaction = self.db.create_transaction(
                    amount=float(row['amount']),
                    transaction_date=transaction_date,
                    description=row.get('description') or None,
                    category_id=category_id
                )
                
                saved_count += 1
                print(f"DEBUG: Saved transaction {index}: {row.get('description', 'No description')} - ${row['amount']}")
                
            except Exception as e:
                failed_count += 1
                print(f"ERROR: Failed to save transaction at row {index}: {str(e)}")
                print(f"ERROR: Row data: {row.to_dict()}")
        
        print(f"DEBUG: Transaction save complete - Saved: {saved_count}, Failed: {failed_count}")
        
        # Return True only if all transactions were saved successfully
        return failed_count == 0
    
    def _resolve_category_id(self, category_name: str, sub_category_name: str) -> Optional[int]:
        """
        Resolve category_id from category and sub_category names.
        
        Args:
            category_name (str): Main category name.
            sub_category_name (str): Sub-category name (can be empty).
            
        Returns:
            Optional[int]: Category ID or None if not found.
        """
        if not category_name.strip():
            return None
        
        categories = self.db.get_all_categories()
        
        if sub_category_name.strip():
            # Look for sub_category with matching parent
            for cat in categories:
                if (cat.name == sub_category_name.strip() and 
                    cat.parent and cat.parent.name == category_name.strip()):
                    return cat.id
        else:
            # Look for category with no parent
            for cat in categories:
                if cat.name == category_name.strip() and not cat.parent:
                    return cat.id
        
        return None
    
    def create_category_hierarchy(self, category_name: str, sub_category_name: str = "") -> bool:
        """
        Create category hierarchy if it doesn't exist.
        
        Args:
            category_name (str): Main category name.
            sub_category_name (str): Sub-category name (optional).
            
        Returns:
            bool: True if hierarchy created/exists successfully, False otherwise.
        """
        try:
            if not category_name.strip():
                print("ERROR: Category name cannot be empty")
                return False
            
            print(f"DEBUG: Creating category hierarchy - Category: '{category_name.strip()}', Sub-category: '{sub_category_name.strip()}'")
            
            # Find or create parent category
            parent_category = None
            categories = self.db.get_all_categories()
            
            for cat in categories:
                if cat.name == category_name.strip() and not cat.parent:
                    parent_category = cat
                    print(f"DEBUG: Found existing parent category: '{cat.name}' (ID: {cat.id})")
                    break
            
            if not parent_category:
                parent_category = self.db.create_category(name=category_name.strip())
                print(f"DEBUG: Created new parent category: '{parent_category.name}' (ID: {parent_category.id})")
            
            # Find or create sub-category if provided
            sub_category = None
            if sub_category_name.strip():
                # Refresh categories list after potential parent creation
                categories = self.db.get_all_categories()
                
                for cat in categories:
                    if (cat.name == sub_category_name.strip() and 
                        cat.parent and cat.parent.id == parent_category.id):
                        sub_category = cat
                        print(f"DEBUG: Found existing sub-category: '{cat.name}' (ID: {cat.id})")
                        break
                
                if not sub_category:
                    sub_category = self.db.create_category(
                        name=sub_category_name.strip(), 
                        parent_id=parent_category.id
                    )
                    print(f"DEBUG: Created new sub-category: '{sub_category.name}' (ID: {sub_category.id}) under parent '{parent_category.name}'")
            
            print(f"DEBUG: Category hierarchy creation successful")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to create category hierarchy - Category: '{category_name}', Sub-category: '{sub_category_name}': {str(e)}")
            return False
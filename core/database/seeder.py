"""
Database Seeding Utility

This module provides a utility to seed the database with initial data,
ensuring that the application has a default set of categories upon first launch.
Enhanced with batch operations and structured error handling.
"""

import json
import os
import pandas as pd
from typing import Dict, List, Any
from .db_interface import DatabaseInterface
from .results import OperationResult, BatchOperationResult

def initialize_database() -> OperationResult:
    """
    Initializes the database with default categories if it's empty.
    Enhanced with batch operations and structured error handling.

    This function is idempotent and safe to call on every application startup.
    It checks if the categories table is empty before attempting to seed the data.
    The default categories are loaded from 'default_categories.json'.
    
    Returns:
        OperationResult: Structured result with success/failure details.
    """
    try:
        db_interface = DatabaseInterface()

        # Idempotency Check: Only seed if the database is empty
        existing_categories = db_interface.get_categories_table()
        if not existing_categories.empty:
            print("✅ [INFO] Database already seeded. Skipping initialization.")
            return OperationResult(
                success=True,
                affected_rows=0,
                data={"message": "Database already seeded", "existing_categories": len(existing_categories)}
            )

        print("🌱 [INFO] Database is empty. Seeding with default categories...")

        # Load default categories from JSON
        categories_data = _load_default_categories()
        if not categories_data:
            return OperationResult(
                success=False,
                error_message="Failed to load default categories from JSON file",
                error_type="file_error"
            )

        # Convert to DataFrame for batch operation
        categories_df = _prepare_categories_dataframe(categories_data)
        
        print(f"📊 [INFO] Prepared {len(categories_df)} categories for seeding...")
        
        # Use batch operation for efficient seeding
        result = db_interface.save_categories_table(categories_df)
        
        if result.success:
            print(f"✅ [INFO] Database seeding complete! Created {result.successful_count} categories.")
            return OperationResult(
                success=True,
                affected_rows=result.successful_count,
                data={
                    "message": "Database seeding successful",
                    "categories_created": result.successful_count,
                    "categories_data": result.successful_items
                }
            )
        else:
            print(f"❌ [ERROR] Database seeding failed: {result.error_message}")
            return OperationResult(
                success=False,
                error_message=f"Batch seeding failed: {result.error_message}",
                error_type="database_error",
                is_retryable=result.is_retryable
            )

    except Exception as e:
        error_msg = f"Unexpected error during database seeding: {str(e)}"
        print(f"❌ [ERROR] {error_msg}")
        return OperationResult(
            success=False,
            error_message=error_msg,
            error_type="unexpected_error"
        )


def _load_default_categories() -> Dict[str, List[str]]:
    """
    Load default categories from JSON file with enhanced error handling.
    
    Returns:
        Dict[str, List[str]]: Dictionary of parent categories and their children.
    """
    try:
        # Construct the path to the JSON file relative to this script
        dir_path = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(dir_path, 'default_categories.json')

        if not os.path.exists(json_path):
            print(f"❌ [ERROR] Default categories file not found at {json_path}")
            return {}

        with open(json_path, 'r', encoding='utf-8') as f:
            default_categories = json.load(f)

        print(f"📁 [INFO] Loaded {len(default_categories)} parent categories from {json_path}")
        return default_categories

    except FileNotFoundError:
        print(f"❌ [ERROR] Could not find the default categories file at {json_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ [ERROR] Failed to decode JSON from {json_path}: {str(e)}")
        return {}
    except Exception as e:
        print(f"❌ [ERROR] Unexpected error loading categories: {str(e)}")
        return {}


def _prepare_categories_dataframe(categories_data: Dict[str, List[str]]) -> pd.DataFrame:
    """
    Convert categories dictionary to DataFrame for batch operation.
    Creates proper parent-child relationships for hierarchical categories.
    
    Args:
        categories_data (Dict[str, List[str]]): Dictionary of categories.
        
    Returns:
        pd.DataFrame: DataFrame with columns [name, parent_category].
    """
    categories_list = []
    
    # First pass: Create parent categories
    for parent_name, children in categories_data.items():
        categories_list.append({
            'name': parent_name,
            'parent_category': None  # Root category
        })
        print(f"📂 [INFO] Prepared parent category: {parent_name}")
    
    # Second pass: Create child categories
    for parent_name, children in categories_data.items():
        if children:  # Only if there are children
            for child_name in children:
                categories_list.append({
                    'name': child_name,
                    'parent_category': parent_name
                })
                print(f"📄 [INFO] Prepared child category: {child_name} under {parent_name}")
    
    df = pd.DataFrame(categories_list)
    print(f"📊 [INFO] Created DataFrame with {len(df)} total categories")
    return df


def seed_additional_categories(additional_categories: Dict[str, List[str]]) -> OperationResult:
    """
    Seed additional categories beyond the default set.
    Useful for custom category additions or updates.
    
    Args:
        additional_categories (Dict[str, List[str]]): Additional categories to seed.
        
    Returns:
        OperationResult: Structured result with success/failure details.
    """
    try:
        if not additional_categories:
            return OperationResult(
                success=True,
                affected_rows=0,
                data={"message": "No additional categories to seed"}
            )

        db_interface = DatabaseInterface()
        
        print(f"🌱 [INFO] Seeding {len(additional_categories)} additional category groups...")
        
        # Convert to DataFrame
        categories_df = _prepare_categories_dataframe(additional_categories)
        
        # Use batch operation
        result = db_interface.save_categories_table(categories_df)
        
        if result.success:
            print(f"✅ [INFO] Additional categories seeded successfully! Created {result.successful_count} categories.")
            return OperationResult(
                success=True,
                affected_rows=result.successful_count,
                data={
                    "message": "Additional categories seeded successfully",
                    "categories_created": result.successful_count
                }
            )
        else:
            print(f"❌ [ERROR] Additional category seeding failed: {result.error_message}")
            return OperationResult(
                success=False,
                error_message=f"Additional seeding failed: {result.error_message}",
                error_type="database_error",
                is_retryable=result.is_retryable
            )

    except Exception as e:
        error_msg = f"Unexpected error during additional category seeding: {str(e)}"
        print(f"❌ [ERROR] {error_msg}")
        return OperationResult(
            success=False,
            error_message=error_msg,
            error_type="unexpected_error"
        )


def verify_seeding() -> OperationResult:
    """
    Verify that database seeding was successful by checking category counts.
    
    Returns:
        OperationResult: Verification result with category statistics.
    """
    try:
        db_interface = DatabaseInterface()
        categories_df = db_interface.get_categories_table()
        
        if categories_df.empty:
            return OperationResult(
                success=False,
                error_message="No categories found in database",
                error_type="verification_failed"
            )
        
        # Count parent and child categories
        parent_count = len(categories_df[categories_df['parent_category'].isnull()])
        child_count = len(categories_df[categories_df['parent_category'].notnull()])
        total_count = len(categories_df)
        
        print(f"📊 [INFO] Verification complete:")
        print(f"   Total categories: {total_count}")
        print(f"   Parent categories: {parent_count}")
        print(f"   Child categories: {child_count}")
        
        return OperationResult(
            success=True,
            affected_rows=total_count,
            data={
                "total_categories": total_count,
                "parent_categories": parent_count,
                "child_categories": child_count,
                "categories": categories_df.to_dict('records')
            }
        )
        
    except Exception as e:
        error_msg = f"Error during seeding verification: {str(e)}"
        print(f"❌ [ERROR] {error_msg}")
        return OperationResult(
            success=False,
            error_message=error_msg,
            error_type="verification_error"
        )

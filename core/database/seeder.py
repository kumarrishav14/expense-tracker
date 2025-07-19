"""
Database Seeding Utility

This module provides a utility to seed the database with initial data,
ensuring that the application has a default set of categories upon first launch.
"""

import json
import os
from .db_interface import DatabaseInterface

def initialize_database():
    """
    Initializes the database with default categories if it's empty.

    This function is idempotent and safe to call on every application startup.
    It checks if the categories table is empty before attempting to seed the data.
    The default categories are loaded from 'default_categories.json'.
    """
    db_interface = DatabaseInterface()

    # Idempotency Check: Only seed if the database is empty
    if not db_interface.get_categories_table().empty:
        print("[INFO] Database already seeded. Skipping initialization.")
        return

    print("[INFO] Database is empty. Seeding with default categories...")

    # Construct the path to the JSON file relative to this script
    dir_path = os.path.dirname(os.path.realpath(__file__))
    json_path = os.path.join(dir_path, 'default_categories.json')

    try:
        with open(json_path, 'r') as f:
            default_categories = json.load(f)

        for parent, children in default_categories.items():
            if not children:
                # Create parent category with no children
                db_interface.create_category_hierarchy(parent, None)
            else:
                for child in children:
                    db_interface.create_category_hierarchy(parent, child)
        
        print("[INFO] Database seeding complete.")

    except FileNotFoundError:
        print(f"[ERROR] Could not find the default categories file at {json_path}.")
    except json.JSONDecodeError:
        print(f"[ERROR] Failed to decode the JSON from {json_path}.")
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred during database seeding: {e}")

"""
Database import script for normalizer output.

Phase 1: Converts normalized-ingredients.json to PostgreSQL.
Usage: python import_to_db.py <normalized_json_file>

This script:
1. Reads normalized-ingredients.json from normalizer
2. Extracts recipes and ingredients
3. Populates recipes, ingredients, recipe_ingredients tables
4. Reports import statistics

For development/testing:
- Uses SQLite if PostgreSQL connection fails
- Schema is created automatically
- Supports dry-run mode (validation only)
"""

import json
import sys
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import psycopg2 for PostgreSQL support
try:
    import psycopg2
    from psycopg2.extras import execute_values, RealDictCursor
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False
    logger.warning("psycopg2 not installed. Using SQLite for development.")


class DatabaseImporter:
    """Handles importing normalized ingredients to database (Phase 1)."""
    
    def __init__(self, db_path: Optional[str] = None, use_postgres: bool = False):
        """
        Initialize importer.
        
        Args:
            db_path: Path for SQLite DB (default: just_mealplanner.db)
            use_postgres: Force PostgreSQL even if psycopg2 not installed
        """
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), 'just_mealplanner.db')
        self.use_postgres = use_postgres and HAS_POSTGRES
        self.conn = None
        self.stats = {
            'recipes_imported': 0,
            'ingredients_matched': 0,
            'ingredients_unmatched': 0,
            'recipe_ingredients_imported': 0,
            'errors': []
        }
    
    def connect(self):
        """Establish database connection."""
        if self.use_postgres:
            try:
                self.conn = psycopg2.connect(
                    dbname="just_meal_planner",
                    user="postgres",
                    password=os.environ.get("DB_PASSWORD", "password"),
                    host="localhost",
                    port=5432
                )
                logger.info("✓ Connected to PostgreSQL")
            except Exception as e:
                logger.error(f"✗ PostgreSQL connection failed: {e}. Falling back to SQLite.")
                self.use_postgres = False
                self.connect_sqlite()
        else:
            self.connect_sqlite()
    
    def connect_sqlite(self):
        """Connect to SQLite database (development only)."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        logger.info(f"✓ Connected to SQLite: {self.db_path}")
    
    def create_schema(self):
        """Create Phase 1 tables if not exist."""
        if self.use_postgres:
            self._create_postgres_schema()
        else:
            self._create_sqlite_schema()
    
    def _create_sqlite_schema(self):
        """Create SQLite schema (simplified for development)."""
        cursor = self.conn.cursor()
        
        # Recipes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
                recipe_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                yield_servings INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source TEXT
            )
        """)
        
        # Ingredients table (minimal, can expand Phase 2+)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingredients (
                ingredient_id TEXT PRIMARY KEY,
                canonical_name TEXT NOT NULL,
                category TEXT,
                type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Recipe ingredients junction
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipe_ingredients (
                recipe_id TEXT NOT NULL,
                ingredient_id TEXT,
                display_text TEXT NOT NULL,
                parsed_amount_data TEXT,
                preparation TEXT,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id),
                FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id),
                PRIMARY KEY (recipe_id, sort_order)
            )
        """)
        
        self.conn.commit()
        logger.info("✓ SQLite schema created")
    
    def _create_postgres_schema(self):
        """Create PostgreSQL schema (from schema.sql phase 1)."""
        cursor = self.conn.cursor()
        
        # Similar structure but with PostgreSQL types
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
                recipe_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                yield_servings INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingredients (
                ingredient_id TEXT PRIMARY KEY,
                canonical_name TEXT NOT NULL,
                category TEXT,
                type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipe_ingredients (
                recipe_id TEXT NOT NULL,
                ingredient_id TEXT,
                display_text TEXT NOT NULL,
                parsed_amount_data JSONB,
                preparation TEXT,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id),
                FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id),
                PRIMARY KEY (recipe_id, sort_order)
            )
        """)
        
        self.conn.commit()
        logger.info("✓ PostgreSQL schema created")
    
    def import_data(self, json_file: str, dry_run: bool = False):
        """
        Import normalized ingredients JSON to database.
        
        Args:
            json_file: Path to normalized-ingredients.json from normalizer
            dry_run: If True, validate only (don't commit)
        """
        logger.info(f"Starting import from: {json_file}")
        
        # Load JSON
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.error(f"✗ File not found: {json_file}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"✗ Invalid JSON: {e}")
            return False
        
        cursor = self.conn.cursor()
        
        for recipe in data:
            recipe_id = recipe.get('recipe_id')
            title = recipe.get('recipe_title')
            
            if not recipe_id or not title:
                logger.warning(f"Skipping recipe with missing id/title: {recipe}")
                self.stats['errors'].append("Recipe missing id or title")
                continue
            
            # Insert recipe
            try:
                if self.use_postgres:
                    cursor.execute("""
                        INSERT INTO recipes (recipe_id, title, source)
                        VALUES (%s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (recipe_id, title, "webscraper"))
                else:
                    cursor.execute("""
                        INSERT OR IGNORE INTO recipes (recipe_id, title, source)
                        VALUES (?, ?, ?)
                    """, (recipe_id, title, "webscraper"))
                
                self.stats['recipes_imported'] += 1
            except Exception as e:
                logger.error(f"✗ Failed to insert recipe {recipe_id}: {e}")
                self.stats['errors'].append(f"Recipe insert error: {recipe_id}")
                continue
            
            # Insert ingredients and recipe_ingredients
            sort_order = 0
            for ingredient in recipe.get('ingredients', []):
                ingredient_id = ingredient.get('ingredient_id')
                display_text = ingredient.get('display_text', '')
                amount_data = ingredient.get('amount_data', {})
                preparation = ingredient.get('preparation')
                
                # Track unmatched ingredients
                if not ingredient_id:
                    self.stats['ingredients_unmatched'] += 1
                    logger.debug(f"⚠ Unmatched ingredient in {recipe_id}: {display_text}")
                    continue
                
                # Insert ingredient (if not exists)
                try:
                    canonical = ingredient.get('canonical_ingredient', {})
                    category = canonical.get('category', 'Unknown')
                    ing_type = canonical.get('source', 'unknown')
                    
                    if self.use_postgres:
                        cursor.execute("""
                            INSERT INTO ingredients (ingredient_id, canonical_name, category, type)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT DO NOTHING
                        """, (
                            ingredient_id,
                            canonical.get('canonical_name', ingredient_id),
                            category,
                            ing_type
                        ))
                    else:
                        cursor.execute("""
                            INSERT OR IGNORE INTO ingredients 
                            (ingredient_id, canonical_name, category, type)
                            VALUES (?, ?, ?, ?)
                        """, (
                            ingredient_id,
                            canonical.get('canonical_name', ingredient_id),
                            category,
                            ing_type
                        ))
                    
                    self.stats['ingredients_matched'] += 1
                except Exception as e:
                    logger.error(f"✗ Failed to insert ingredient {ingredient_id}: {e}")
                    self.stats['errors'].append(f"Ingredient insert error: {ingredient_id}")
                    continue
                
                # Insert recipe_ingredient
                try:
                    amount_data_str = json.dumps(amount_data)
                    
                    if self.use_postgres:
                        cursor.execute("""
                            INSERT INTO recipe_ingredients
                            (recipe_id, ingredient_id, display_text, parsed_amount_data, 
                             preparation, sort_order)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            recipe_id,
                            ingredient_id,
                            display_text,
                            amount_data_str,
                            preparation,
                            sort_order
                        ))
                    else:
                        cursor.execute("""
                            INSERT INTO recipe_ingredients
                            (recipe_id, ingredient_id, display_text, parsed_amount_data, 
                             preparation, sort_order)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            recipe_id,
                            ingredient_id,
                            display_text,
                            amount_data_str,
                            preparation,
                            sort_order
                        ))
                    
                    self.stats['recipe_ingredients_imported'] += 1
                    sort_order += 1
                except Exception as e:
                    logger.error(f"✗ Failed to insert recipe_ingredient: {e}")
                    self.stats['errors'].append(f"Recipe ingredient error: {recipe_id}/{ingredient_id}")
        
        # Commit or rollback based on dry_run
        if dry_run:
            self.conn.rollback()
            logger.info("⚠ DRY RUN: Changes rolled back (validation only)")
        else:
            self.conn.commit()
            logger.info("✓ Changes committed to database")
        
        return True
    
    def print_stats(self):
        """Print import statistics."""
        print("\n" + "="*60)
        print("IMPORT STATISTICS")
        print("="*60)
        print(f"Recipes imported:           {self.stats['recipes_imported']}")
        print(f"Ingredients matched:        {self.stats['ingredients_matched']}")
        print(f"Ingredients unmatched:      {self.stats['ingredients_unmatched']}")
        print(f"Recipe ingredients:         {self.stats['recipe_ingredients_imported']}")
        print(f"Errors:                     {len(self.stats['errors'])}")
        
        if self.stats['errors']:
            print("\nErrors encountered:")
            for error in self.stats['errors'][:10]:  # Show first 10
                print(f"  - {error}")
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more")
        
        print("="*60 + "\n")
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Import normalized ingredients to Phase 1 database"
    )
    parser.add_argument(
        "json_file",
        type=str,
        help="Path to normalized-ingredients.json from normalizer"
    )
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        help="Path to SQLite database (default: just_mealplanner.db)"
    )
    parser.add_argument(
        "--postgres",
        action="store_true",
        help="Use PostgreSQL (requires connection details in environment)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate without committing changes"
    )
    
    args = parser.parse_args()
    
    # Check file exists
    if not Path(args.json_file).exists():
        logger.error(f"✗ File not found: {args.json_file}")
        sys.exit(1)
    
    # Create importer
    importer = DatabaseImporter(
        db_path=args.db,
        use_postgres=args.postgres
    )
    
    try:
        # Connect to database
        importer.connect()
        
        # Create schema
        importer.create_schema()
        
        # Import data
        success = importer.import_data(args.json_file, dry_run=args.dry_run)
        
        if success:
            importer.print_stats()
            logger.info("✓ Import completed successfully")
            sys.exit(0)
        else:
            logger.error("✗ Import failed")
            sys.exit(1)
    
    finally:
        importer.close()


if __name__ == "__main__":
    main()

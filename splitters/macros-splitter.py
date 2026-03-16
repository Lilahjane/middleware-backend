"""
Phase 2.1: Macro Splitter

Extracts macro/nutrient data from recipes and creates a dedicated macros.json file.

Input: recipes-withID.json or normalized-ingredients.json
Output: macros.json with standardized structure

Filters for recipes that have nutrient/macro data and creates a clean,
consolidated macro file ready for Phase 2.2 normalization.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Configuration
INPUT_FILE = r"D:\just_mealplanner\source\recipes-withID.json"
OUTPUT_FILE = r"D:\just_mealplanner\source\macros.json"


def load_entire_json(path: str) -> Dict[str, Any]:
    """
    Load and parse JSON file.
    
    Args:
        path: File path
        
    Returns:
        Parsed JSON data
    """
    try:
        with open(path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading {path}: {e}")
        sys.exit(1)


def save_new_json(path: str, data_to_save: List[Dict]) -> None:
    """
    Save data to JSON file.
    
    Args:
        path: Output file path
        data_to_save: Data to serialize
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(data_to_save, file, indent=2)
        print(f"✓ Saved to {path}")
    except Exception as e:
        print(f"Error saving {path}: {e}")
        sys.exit(1)


def extract_macros(entire_json_dictionary: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract recipes that have nutrient/macro data.
    
    Filters for recipes with non-empty nutrients dict and creates
    a clean macro item with id, title, url, yield_servings, and macros.
    
    Args:
        entire_json_dictionary: Full recipe data structure
        
    Returns:
        List of macro items with nutrient data
    """
    all_recipes_list = entire_json_dictionary.get('results', [])
    valid_recipes_found = []
    
    recipes_processed = 0
    recipes_with_nutrients = 0
    recipes_without_nutrients = 0

    for single_recipe_object in all_recipes_list:
        recipes_processed += 1
        
        # Get the nutrients dict (default to empty dict if missing)
        nutrients = single_recipe_object.get('nutrients', {})
        
        # Logic: Only include recipes with nutrient data
        if nutrients and isinstance(nutrients, dict) and len(nutrients) > 0:
            # Create a clean macro item
            macro_item = {
                "id": single_recipe_object.get('id'),
                "title": single_recipe_object.get('title', ''),
                "url": single_recipe_object.get('url', ''),
                "yield_servings": single_recipe_object.get('yields', ''),
                "macros": nutrients
            }
            valid_recipes_found.append(macro_item)
            recipes_with_nutrients += 1
        else:
            recipes_without_nutrients += 1
    
    print(f"\nMacro Extraction Summary:")
    print(f"  Total recipes processed: {recipes_processed}")
    print(f"  Recipes with nutrient data: {recipes_with_nutrients}")
    print(f"  Recipes without nutrient data: {recipes_without_nutrients}")
    
    return valid_recipes_found


if __name__ == "__main__":
    print("="*70)
    print("PHASE 2.1: MACRO SPLITTER - Extracting nutrient data from recipes")
    print("="*70)
    
    # 1. Load the recipe file
    print(f"\nLoading recipes from: {INPUT_FILE}")
    raw_data = load_entire_json(INPUT_FILE)
    
    # 2. Extract only recipes with macro data
    print("Filtering recipes with nutrient data...")
    processed_data = extract_macros(raw_data)
    
    # 3. Save the cleaned macro file
    save_new_json(OUTPUT_FILE, processed_data)
    
    print(f"\n{'='*70}")
    print(f"✓ SUCCESS: Extracted {len(processed_data)} recipes with nutrient data")
    print(f"{'='*70}")
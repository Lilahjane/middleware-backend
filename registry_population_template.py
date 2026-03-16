"""
Phase 3.2: Registry Population Tool

Creates template entries for expanding the ingredient registry.

Generates entries with:
- ing_[category]_[type]_### format
- Aliases from unresolved ingredients
- Conversion data (where available)
- Semantic validation rules
- Metadata

Output: registry_templates.json (ready to merge with ingredient_registry.json)
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Optional


# ============================================================================
# INGREDIENT CATEGORIES & TEMPLATES
# ============================================================================

INGREDIENT_CATEGORIES = {
    "flour": {
        "category": "Grains & Flours",
        "type": "grain_product",
        "examples": ["all-purpose flour", "wheat flour", "whole wheat flour", "bread flour"],
        "conversions": {"cup": 125, "tablespoon": 8, "gram": 1},
        "density": 0.59  # g/ml
    },
    "sugar": {
        "category": "Sweeteners",
        "type": "sugar",
        "examples": ["granulated sugar", "white sugar", "caster sugar"],
        "conversions": {"cup": 200, "tablespoon": 12.5, "gram": 1},
        "density": 0.8
    },
    "butter": {
        "category": "Fats & Oils",
        "type": "dairy_fat",
        "examples": ["unsalted butter", "salted butter", "butter"],
        "conversions": {"cup": 227, "tablespoon": 14.2, "gram": 1},
        "density": 0.911
    },
    "egg": {
        "category": "Dairy & Eggs",
        "type": "egg",
        "examples": ["whole egg", "egg white", "egg yolk", "large egg"],
        "conversions": {"whole": 50, "white": 29, "yolk": 18, "gram": 1},
        "density": 1.0
    },
    "milk": {
        "category": "Dairy & Eggs",
        "type": "dairy_liquid",
        "examples": ["whole milk", "skim milk", "low-fat milk"],
        "conversions": {"cup": 240, "tablespoon": 15, "ml": 1},
        "density": 1.03
    },
    "salt": {
        "category": "Seasonings & Spices",
        "type": "mineral",
        "examples": ["table salt", "sea salt", "kosher salt"],
        "conversions": {"cup": 280, "tablespoon": 18, "teaspoon": 6, "gram": 1},
        "density": 1.17
    },
    "pepper": {
        "category": "Seasonings & Spices",
        "type": "spice",
        "examples": ["black pepper", "white pepper", "ground pepper"],
        "conversions": {"tablespoon": 6, "teaspoon": 2, "gram": 1},
        "density": 0.6
    },
    "oil": {
        "category": "Fats & Oils",
        "type": "vegetable_oil",
        "examples": ["olive oil", "vegetable oil", "canola oil"],
        "conversions": {"cup": 218, "tablespoon": 13.6, "ml": 1},
        "density": 0.918
    },
    "garlic": {
        "category": "Produce",
        "type": "bulb",
        "examples": ["garlic clove", "minced garlic", "garlic powder"],
        "conversions": {"clove": 3, "tablespoon": 15, "gram": 1},
        "density": 1.1
    },
    "onion": {
        "category": "Produce",
        "type": "vegetable",
        "examples": ["yellow onion", "white onion", "red onion"],
        "conversions": {"medium": 150, "tablespoon": 15, "gram": 1},
        "density": 1.1
    },
}

# ============================================================================
# UNRESOLVED INGREDIENTS MAPPING
# ============================================================================

UNRESOLVED_MAPPING = {
    # This would be populated from AUDIT_REPORT.json in production
    # For now, we use the top unresolved ingredients from normalized data
}


# ============================================================================
# REGISTRY ENTRY GENERATION
# ============================================================================

def generate_ingredient_id(category: str, ingredient_type: str, index: int) -> str:
    """
    Generate ingredient_id in format: ing_[category]_[type]_###
    
    Args:
        category: Category slug
        ingredient_type: Type slug
        index: Sequential index (001, 002, etc.)
        
    Returns:
        Formatted ingredient_id
    """
    category_slug = category.lower().replace(" ", "_").replace("&", "and")
    type_slug = ingredient_type.lower().replace(" ", "_")
    
    return f"ing_{category_slug}_{type_slug}_{index:03d}"


def create_registry_entry(
    ingredient_name: str,
    category: str,
    ingredient_type: str,
    aliases: List[str],
    index: int = 1,
    conversions: Optional[Dict] = None,
    density: Optional[float] = None,
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Create a complete ingredient registry entry.
    
    Args:
        ingredient_name: Canonical name
        category: Category name
        ingredient_type: Type/subtype
        aliases: List of alternative names
        index: Sequential index for ID
        conversions: Unit conversions dict
        density: g/ml density value
        metadata: Additional metadata
        
    Returns:
        Complete registry entry
    """
    ingredient_id = generate_ingredient_id(category, ingredient_type, index)
    
    entry = {
        "ingredient_id": ingredient_id,
        "canonical_name": ingredient_name,
        "category": category,
        "type": ingredient_type,
        "aliases": aliases,
        "fdc_reference": {
            "fdc_ids": [],
            "fdc_reason": "To be populated - check FDC database"
        },
        "conversions": conversions or {},
        "density_g_per_ml": density,
        "substitutions": [],
        "allergens": [],
        "metadata": metadata or {}
    }
    
    return entry


def generate_template_entries(audit_report_path: str = "AUDIT_REPORT.json") -> List[Dict]:
    """
    Generate template entries from audit report.
    
    Creates entries for top-priority unresolved ingredients.
    
    Args:
        audit_report_path: Path to audit report
        
    Returns:
        List of registry entry templates
    """
    entries = []
    
    # Try to load audit report for real data, fall back to templates
    try:
        with open(audit_report_path, 'r', encoding='utf-8') as f:
            audit = json.load(f)
            unresolved = audit.get("unresolved_ingredients", {})
    except FileNotFoundError:
        print(f"Note: {audit_report_path} not found, using template entries")
        unresolved = {}
    
    # Create entries for known ingredients from templates
    index_map = {}
    
    for ingredient_name, template_data in INGREDIENT_CATEGORIES.items():
        category = template_data["category"]
        ing_type = template_data["type"]
        
        if category not in index_map:
            index_map[category] = {}
        if ing_type not in index_map[category]:
            index_map[category][ing_type] = 1
        else:
            index_map[category][ing_type] += 1
        
        current_index = index_map[category][ing_type]
        
        entry = create_registry_entry(
            ingredient_name=ingredient_name.title(),
            category=category,
            ingredient_type=ing_type,
            aliases=template_data.get("examples", [ingredient_name.lower()]),
            index=current_index,
            conversions=template_data.get("conversions"),
            density=template_data.get("density"),
            metadata={"template_based": True}
        )
        
        entries.append(entry)
    
    # Create entries for unresolved ingredients from audit
    if unresolved:
        print(f"Creating entries from {len(unresolved)} unresolved ingredients...")
        
        for ingredient_str, data in list(unresolved.items())[:50]:  # Top 50
            # Guess category and type from ingredient string
            category = guess_category(ingredient_str)
            ing_type = guess_type(ingredient_str, category)
            
            if category not in index_map:
                index_map[category] = {}
            if ing_type not in index_map[category]:
                index_map[category][ing_type] = 1
            else:
                index_map[category][ing_type] += 1
            
            current_index = index_map[category][ing_type]
            
            entry = create_registry_entry(
                ingredient_name=ingredient_str.title(),
                category=category,
                ingredient_type=ing_type,
                aliases=[ingredient_str.lower()],
                index=current_index,
                metadata={
                    "from_audit": True,
                    "occurrences": data.get("occurrences", 1),
                    "sample_recipes": data.get("sample_recipes", [])
                }
            )
            
            entries.append(entry)
    
    return entries


def guess_category(ingredient_str: str) -> str:
    """Guess ingredient category from name."""
    lower = ingredient_str.lower()
    
    if any(word in lower for word in ['flour', 'rice', 'grain', 'bread', 'pasta']):
        return "Grains & Flours"
    elif any(word in lower for word in ['milk', 'cheese', 'yogurt', 'cream', 'egg']):
        return "Dairy & Eggs"
    elif any(word in lower for word in ['oil', 'butter', 'fat', 'shortening']):
        return "Fats & Oils"
    elif any(word in lower for word in ['salt', 'pepper', 'spice', 'herb', 'seasoning']):
        return "Seasonings & Spices"
    elif any(word in lower for word in ['sugar', 'honey', 'syrup', 'sweet']):
        return "Sweeteners"
    elif any(word in lower for word in ['meat', 'chicken', 'beef', 'pork', 'fish', 'ham']):
        return "Meat & Seafood"
    elif any(word in lower for word in ['vegetable', 'onion', 'garlic', 'tomato', 'lettuce', 'carrot']):
        return "Produce"
    else:
        return "Miscellaneous"


def guess_type(ingredient_str: str, category: str) -> str:
    """Guess ingredient type from name and category."""
    lower = ingredient_str.lower()
    
    if category == "Grains & Flours":
        if 'flour' in lower:
            return "grain_product"
        else:
            return "grain"
    elif category == "Dairy & Eggs":
        if 'milk' in lower:
            return "dairy_liquid"
        elif 'egg' in lower:
            return "egg"
        else:
            return "dairy_solid"
    elif category == "Meat & Seafood":
        if 'fish' in lower or 'seafood' in lower:
            return "seafood"
        else:
            return "meat"
    else:
        return "other"


# ============================================================================
# FILE I/O
# ============================================================================

def save_templates(entries: List[Dict], output_file: str = "registry_templates.json") -> None:
    """Save template entries to file."""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2)
    
    print(f"✓ Saved {len(entries)} template entries to {output_path}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("PHASE 3.2: REGISTRY POPULATION TOOL")
    print("="*70 + "\n")
    
    print("Generating template entries...")
    entries = generate_template_entries()
    
    print(f"\n{'='*70}")
    print(f"Generated {len(entries)} template entries")
    print(f"{'='*70}\n")
    
    # Display sample entries
    print("Sample entries (first 3):")
    for entry in entries[:3]:
        print(f"\n  ID: {entry['ingredient_id']}")
        print(f"  Name: {entry['canonical_name']}")
        print(f"  Category: {entry['category']}")
        print(f"  Type: {entry['type']}")
        print(f"  Aliases: {entry['aliases'][:2]}...")
        if entry['conversions']:
            print(f"  Conversions: {list(entry['conversions'].keys())}")
    
    # Save
    save_templates(entries)
    
    print("\nNext Steps:")
    print("1. Review registry_templates.json for accuracy")
    print("2. Add FDC IDs and missing conversions")
    print("3. Merge into normalizer/ingredient_registry.json")
    print("4. Re-run ingredient normalizer for full coverage")
    
    print(f"\n{'='*70}\n")

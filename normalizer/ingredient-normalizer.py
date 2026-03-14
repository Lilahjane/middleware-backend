import json
import logging
import sys
import re
import os
from fractions import Fraction
from ingredient_parser import parse_ingredient
from ingredient_parser.dataclasses import IngredientAmount, CompositeIngredientAmount
try:
    from googletrans import Translator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False

# --- LOGGING SETUP ---
logging.basicConfig(stream=sys.stdout)
# Only show foundation-foods logs, not all the preprocessing logs
logging.getLogger("ingredient-parser").setLevel(logging.WARNING)
logging.getLogger("ingredient-parser.foundation-foods").setLevel(logging.WARNING)

OUTPUT_FILE = r"D:\just_mealplanner\source\normalized-ingredients.json"
INPUT_FILE = r"D:\just_mealplanner\source\ingredients.json"

# --- CONFIGURATION ---
CONFIDENCE_THRESHOLD = 0.85  # Only accept foundation foods above this threshold
TRANSLATOR = Translator() if HAS_TRANSLATOR else None
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'es': 'Spanish', 
    'fr': 'French',
    'de': 'German',
    'it': 'Italian'
}

# Semantic validation: known ingredient name to INCOMPATIBLE categories
# These combinations should never happen and indicate parsing errors
INCOMPATIBLE_CATEGORIES = {
    'ham': {'Vegetables and Vegetable Products', 'Vegetables', 'Spices', 'Fruits and Fruit Juices'},
    'wine': {'Dairy and Egg Products', 'Vegetables and Vegetable Products', 'Vegetables', 'Fats and Oils'},
    'cheese': {'Vegetables and Vegetable Products', 'Vegetables', 'Spices', 'Beverages', 'Alcoholic Beverages'},
    'onion': {'Dairy and Egg Products', 'Fats and Oils', 'Spices'},
    'pepper': {'Dairy and Egg Products', 'Meat and Poultry', 'Cereals'},
    'salt': {'Vegetables and Vegetable Products', 'Meat and Poultry'},
    'flour': {'Dairy and Egg Products', 'Meat and Poultry', 'Vegetables and Vegetable Products'},
    'butter': {'Vegetables and Vegetable Products', 'Beverages', 'Spices'},
    'egg': {'Vegetables and Vegetable Products', 'Beverages', 'Fats and Oils'},
    'oil': {'Dairy and Egg Products', 'Meat and Poultry', 'Spices'},
}
# --- UTILITY FUNCTIONS ---
def safe_quantity_to_float(quantity):
    """
    Safely convert quantity to float, handling Fractions and string quantities.
    Extracts numeric part if string contains non-numeric characters.
    """
    try:
        # If it's already a number or Fraction, convert directly
        return float(quantity)
    except (ValueError, TypeError):
        # If it's a string with quotes or other chars, try to extract numeric part
        if isinstance(quantity, str):
            # Use regex to extract the first numeric value (including decimals/fractions)
            match = re.search(r'[\d.]+', quantity)
            if match:
                try:
                    return float(match.group())
                except ValueError:
                    return 0.0
            # If no numeric part found, return 0
            return 0.0
        return 0.0

# --- TRANSLATION MIDDLEWARE ---
def translate_to_english_if_needed(ingredient_text):
    """
    Detects if ingredient text is in a non-English language and translates to English.
    Returns both the original text and translated text.
    """
    if not HAS_TRANSLATOR:
        return ingredient_text, ingredient_text, 'en'
    
    try:
        detection = TRANSLATOR.detect(ingredient_text)
        detected_lang = detection.lang
        
        if detected_lang != 'en':
            translated = TRANSLATOR.translate(ingredient_text, src_lang=detected_lang, dest_lang='en')
            translated_text = translated['text']
            logging.getLogger(__name__).info(f"Translated ({detected_lang}→en): '{ingredient_text}' → '{translated_text}'")
            return ingredient_text, translated_text, detected_lang
        else:
            return ingredient_text, ingredient_text, 'en'
    except Exception as e:
        logging.getLogger(__name__).warning(f"Translation failed for '{ingredient_text}': {e}")
        return ingredient_text, ingredient_text, 'en'

def round_metric_value(metric_ml):
    """
    Rounds metric_ml to a reasonable precision (2 decimal places).
    Prevents extreme floating point precision issues.
    """
    if metric_ml is None or metric_ml == 0.0:
        return metric_ml
    try:
        return round(float(metric_ml), 2)
    except (ValueError, TypeError):
        return 0.0

def validate_category_match(ingredient_names, canonical_name, category):
    """
    Performs semantic validation: checks if the canonical category is INCOMPATIBLE
    with the ingredient names. This catches obvious parsing errors.
    
    Returns: (is_valid, warning_message)
      is_valid: False only if category is in the INCOMPATIBLE list for that ingredient
      warning_message: None if valid, or a string if there's a flagrant mismatch
    """
    if not ingredient_names or not category:
        return True, None
    
    # Extract first ingredient name and convert to lowercase
    primary_name = ingredient_names[0].lower() if ingredient_names else ""
    category_lower = category.lower()
    
    # Special case: if "wine", "vino", or "vin" appears in the ingredient or parsed name,
    # but the canonical name is "cheese" or "queso", reject it
    if any(wine_keyword in primary_name for wine_keyword in ['wine', 'vino', 'vin']):
        if any(cheese_keyword in canonical_name.lower() for cheese_keyword in ['cheese', 'queso', 'dairy']):
            warning = (
                f"SEMANTIC ERROR CAUGHT: Wine/vino ingredient should not map to "
                f"cheese/dairy product. Got '{canonical_name}' in category '{category}'"
            )
            return False, warning
    
    # Check if this is a flagrantly incompatible match
    for key_word, incompatible_cats in INCOMPATIBLE_CATEGORIES.items():
        if key_word in primary_name:
            # We have incompatibility rules for this ingredient type
            # Check if category matches any incompatible set (case-insensitive)
            for incompatible_cat in incompatible_cats:
                if incompatible_cat.lower() in category_lower or category_lower in incompatible_cat.lower():
                    warning = (
                        f"SEMANTIC ERROR CAUGHT: '{primary_name}' should NOT be '{incompatible_cat}' "
                        f"but parser returned '{category}'"
                    )
                    # Return False to reject this match
                    return False, warning
    
    return True, None

def find_ingredient_in_registry(fdc_id, ingredient_registry):
    """
    Lookup an FDC ID in the ingredient registry to find its ingredient_id.
    Registry structure: {"ingredients": [{...}, {...}]}
    Returns (ingredient_id, registry_entry) or (None, None) if not found.
    """
    for ing_entry in ingredient_registry.get('ingredients', []):
        fdc_ref = ing_entry.get('fdc_reference', {})
        # Handle both old format (string) and new format (dict)
        if isinstance(fdc_ref, dict):
            if fdc_ref.get('fdc_id') == fdc_id:
                return ing_entry.get('ingredient_id'), ing_entry
        elif fdc_ref == fdc_id:
            return ing_entry.get('ingredient_id'), ing_entry
    return None, None

def resolve_ingredient_id(parsed_names, foundation_food, ingredient_registry, ingredient_corrections):
    """
    Resolves an ingredient to an ingredient_id. Priority:
    1. Check ingredient_corrections.json for pattern matches
    2. Check FDC → ingredient_registry mapping (if high confidence + semantic validation)
    3. Return (ingredient_id, source, canonical_data) or (None, "unresolved", None)
    
    ingredient_id can be from correction, or looked up via FDC mapping.
    """
    if not foundation_food:
        return None, "unresolved", None
    
    ingredient_name = " ".join(parsed_names) if parsed_names else "unknown"
    
    # STEP 1: Check corrections first (highest priority)
    # Search for pattern matches in the ingredient name
    for correction_entry in ingredient_corrections.get('rejected_fdc_matches', []):
        pattern = correction_entry.get('parsed_ingredient_pattern', '').lower()
        if pattern and pattern in ingredient_name.lower():
            ingredient_id_to_use = correction_entry.get('ingredient_id_to_use')
            if ingredient_id_to_use:
                # Find this ingredient in registry
                for ing_entry in ingredient_registry.get('ingredients', []):
                    if ing_entry.get('ingredient_id') == ingredient_id_to_use:
                        logging.getLogger(__name__).info(
                            f"✓ CORRECTION APPLIED: '{ingredient_name}' → {ingredient_id_to_use} "
                            f"(FDC {correction_entry.get('fdc_id_that_failed')} rejected: {correction_entry.get('reason')})"
                        )
                        return ingredient_id_to_use, "ingredient_corrections_override", ing_entry
    
    # STEP 2: Try FDC → ingredient_registry lookup (confidence check required)
    if foundation_food.confidence >= CONFIDENCE_THRESHOLD:
        # Additional semantic validation for high-confidence matches
        is_semantically_valid, validation_warning = validate_category_match(
            parsed_names, 
            foundation_food.text, 
            foundation_food.category
        )
        
        if not is_semantically_valid:
            logging.getLogger(__name__).warning(f"Semantic error rejected: {validation_warning}")
            return None, "semantic_validation_rejected", None
        
        # Look up this FDC ID in our registry
        ingredient_id, registry_entry = find_ingredient_in_registry(foundation_food.fdc_id, ingredient_registry)
        if ingredient_id:
            logging.getLogger(__name__).info(
                f"✓ FDC MAPPED: '{ingredient_name}' → {ingredient_id} "
                f"(FDC {foundation_food.fdc_id}, confidence {foundation_food.confidence:.3f})"
            )
            return ingredient_id, "fdc_mapped", registry_entry
        else:
            # FDC match found but not in our registry yet
            # Return None but log for later population
            logging.getLogger(__name__).info(
                f"⚠ FDC NOT IN REGISTRY: '{ingredient_name}' (FDC {foundation_food.fdc_id}, "
                f"confidence {foundation_food.confidence:.3f}). Add to ingredient_registry.json"
            )
            return None, "fdc_not_in_registry", None
    else:
        logging.getLogger(__name__).warning(
            f"⚠ Low confidence rejected: '{foundation_food.text}' "
            f"(confidence: {foundation_food.confidence:.3f} < threshold: {CONFIDENCE_THRESHOLD})"
        )
        return None, "low_confidence_rejected", None


# --- PRE-PROCESSING LAYER ---
def custom_pre_processor(ingredient_list):
    """
    Filters out section headers and non-ingredient metadata
    found in the sources (e.g., 'FOR THE GARLIC BUTTER' or 'la veille').
    """
    cleaned_list = []
    headers_to_skip = ["FOR THE", "la veille", "Le lendemain", "Confection"]
    
    for line in ingredient_list:
        # Skip empty lines or lines that are clearly section headers
        if not line or any(header in line for header in headers_to_skip):
            continue
        cleaned_list.append(line.strip())
    return cleaned_list

# --- MAIN LOGIC ---
def process_recipes(input_file):
    # Load the source JSON mirroring ingredients_json
    with open(input_file, 'r', encoding='utf-8') as f:
        recipes = json.load(f)

    output_data = []
    
    # Load ingredient registry and corrections at startup
    try:
        with open(os.path.join(os.path.dirname(__file__), 'ingredient_registry.json'), 'r', encoding='utf-8') as f:
            ingredient_registry = json.load(f)
    except FileNotFoundError:
        logging.getLogger(__name__).warning("ingredient_registry.json not found. FDC ID used instead of ingredient_id.")
        ingredient_registry = {}
    
    try:
        with open(os.path.join(os.path.dirname(__file__), 'ingredient_corrections.json'), 'r', encoding='utf-8') as f:
            ingredient_corrections = json.load(f)
    except FileNotFoundError:
        logging.getLogger(__name__).warning("ingredient_corrections.json not found. No corrections will be applied.")
        ingredient_corrections = {}

    for recipe in recipes:
        recipe_entry = {
            "recipe_id": recipe.get("id"),
            "recipe_title": recipe.get("title"),
            "ingredients": []
        }

        # Step 1: Pre-process the list of strings
        cleaned_ingredients = custom_pre_processor(recipe.get("ingredients", []))

        for sentence in cleaned_ingredients:
            # Step 1.5: Apply translation middleware if needed
            original_text, translated_text, detected_lang = translate_to_english_if_needed(sentence)
            
            # Step 2: Use the tool to parse the translated string
            parsed = parse_ingredient(translated_text, foundation_foods=True, volumetric_units_system="us_customary")

            # --- DEBUG OUTPUT ---
            try:
                print(f"\n=== PARSING: {original_text} ===")
                if detected_lang != 'en':
                    print(f"[Translated from {detected_lang}] {translated_text}")
            except UnicodeEncodeError:
                print(f"\n=== PARSING: (Unicode characters present) ===")
            print(f"Type of parsed.foundation_foods: {type(parsed.foundation_foods)}")
            if parsed.foundation_foods:
                ff = parsed.foundation_foods[0]
                print(f"Foundation Food: {ff.text} (fdc_id: {ff.fdc_id}, confidence: {ff.confidence:.3f})")

            # Step 3: Extract Canonical Ingredient (ingredient_id with FDC as fallback)
            ingredient_id = None
            canonical_ingredient = None
            resolution_source = None
            
            if parsed.foundation_foods:
                foundation_food = parsed.foundation_foods[0]
                parsed_names = [n.text for n in parsed.name]
                
                # Use new resolution function (checks corrections, FDC mapping, semantic validation)
                ingredient_id, resolution_source, canonical_data = resolve_ingredient_id(
                    parsed_names,
                    foundation_food,
                    ingredient_registry,
                    ingredient_corrections
                )
                
                if ingredient_id and canonical_data:
                    # Successfully resolved to ingredient_id
                    canonical_ingredient = {
                        "ingredient_id": ingredient_id,
                        "canonical_name": canonical_data.get("canonical_name"),
                        "category": canonical_data.get("category"),
                        "source": resolution_source,
                        "fdc_reference": foundation_food.fdc_id if resolution_source == "fdc_mapped" else None
                    }
                else:
                    # Could not resolve, but include FDC info for debugging
                    canonical_ingredient = {
                        "ingredient_id": None,
                        "fdc_id_parsed": foundation_food.fdc_id,
                        "canonical_name": foundation_food.text,
                        "confidence": foundation_food.confidence,
                        "category": foundation_food.category,
                        "source": resolution_source,
                        "note": "Not yet added to ingredient_registry.json"
                    }

            # Step 4: Extract Preparation (separate from ingredient identity)
            preparation = parsed.preparation.text if parsed.preparation else None

            # Step 5: Process Amount Data (Composite, Simple, and Unquantified)
            amount_data = None
            if parsed.amount:
                amt = parsed.amount[0]  # Handle first amount (recipes typically have one)

                if isinstance(amt, CompositeIngredientAmount):
                    # Extract individual components from composite amount
                    components = []
                    for component in amt.amounts:
                        components.append({
                            "quantity": safe_quantity_to_float(component.quantity),
                            "unit": str(component.unit),
                            "quantity_fraction": str(component.quantity)
                        })

                    # FIXED: Split logic for volume vs count
                    try:
                        combined_qty = amt.combined()
                        metric_ml = round_metric_value(combined_qty.to("ml").magnitude)
                        aggregation_type = "volume"
                    except:
                        # Fallback: treat as count-based
                        metric_ml = 0.0
                        aggregation_type = "count"

                    amount_data = {
                        "type": "composite",
                        "aggregation_type": aggregation_type,
                        "components": components,
                        "join_text": getattr(amt, 'join', 'and'),
                        "metric_ml": metric_ml if aggregation_type == "volume" else 0.0,
                        "total_count": safe_quantity_to_float(amt.amounts[0].quantity) if aggregation_type == "count" else 0.0,
                        "is_approximate": getattr(amt, 'RANGE', False)
                    }
                else:  # Simple IngredientAmount
                    # FIXED: Split logic for volume vs count
                    try:
                        metric_ml = round_metric_value(amt.convert_to("ml").quantity)
                        aggregation_type = "volume"
                    except:
                        # Fallback: treat as count-based item (e.g., "2 eggs", "3 bay leaves")
                        metric_ml = 0.0
                        aggregation_type = "count"

                    amount_data = {
                        "type": "simple",
                        "aggregation_type": aggregation_type,
                        "components": [{
                            "quantity": safe_quantity_to_float(amt.quantity),
                            "unit": str(amt.unit),
                            "quantity_fraction": str(amt.quantity)
                        }],
                        "join_text": None,
                        "metric_ml": metric_ml if aggregation_type == "volume" else 0.0,
                        "total_count": safe_quantity_to_float(amt.quantity) if aggregation_type == "count" else 0.0,
                        "is_approximate": getattr(amt, 'RANGE', False)
                    }
            else:
                # FIXED: Handle unquantified amounts (e.g., "Oil for frying", "To taste")
                if parsed.purpose or parsed.comment:
                    amount_data = {
                        "type": "unquantified",
                        "aggregation_type": "unquantified",
                        "display": "To taste / As needed",
                        "metric_ml": 0.0,
                        "total_count": 0.0
                    }

            # Step 6: Create Recipe Ingredient Object (Database Schema)
            # FIXED: Use parsed.sentence for better display (preserves full context)
            recipe_ingredient = {
                "ingredient_id": ingredient_id,  # NEW: Primary key for our system
                "display_text": parsed.sentence,  # Full normalized sentence for cookbook view
                "raw_text": original_text,  # Original recipe text (may be in different language)
                "translated_text": translated_text if detected_lang != 'en' else None,
                "original_language": detected_lang if detected_lang != 'en' else None,
                "preparation": preparation,
                "canonical_ingredient": canonical_ingredient,
                "amount_data": amount_data,
                "standard_names": [n.text for n in parsed.name],
                "comment": parsed.comment.text if parsed.comment else None,
                "purpose": parsed.purpose.text if parsed.purpose else None,
                "size_modifier": parsed.size.text if parsed.size else None
            }

            recipe_entry["ingredients"].append(recipe_ingredient)

        output_data.append(recipe_entry)

    return output_data

if __name__ == "__main__":
    try:
        # Check for translation dependency
        if not HAS_TRANSLATOR:
            print("[WARNING] googletrans not installed. Multi-language support disabled.")
            print("[INFO] To enable: pip install googletrans-new")
        else:
            print("[OK] Translation support enabled")
        
        # Assumes your file is named 'ingredients.json'
        final_json = process_recipes(INPUT_FILE) 

        # Custom encoder to handle Fraction objects
        class FractionEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, Fraction):
                    return float(obj)
                return super().default(obj)

        # Write to output file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_json, f, indent=2, cls=FractionEncoder)

        print("[OK] Output saved to output.json")
    except FileNotFoundError:
        print("Error: Please create 'ingredients.json' in this directory.")

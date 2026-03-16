"""
Phase 2.2: Macro Normalizer

Implements the 6-stage macro normalization pipeline:
1. Field standardization: Map varied nutrient names to canonical fields
2. Value extraction & sanitization: Remove units, handle decimals
3. Serving size normalization: Estimate per-recipe from yield_servings
4. Validation: Check for impossible values
5. Confidence scoring: Flag incomplete macro data
6. Output canonical structure: per_recipe + per_serving variants

Input: macros.json (raw nutrient data from scrapers)
Output: normalized-macros.json (clean, structured, with confidence scores)
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict


# ============================================================================
# FIELD MAPPING: Map scraper field names → canonical names
# ============================================================================

FIELD_MAPPING = {
    # Energy/Calories
    "calories": "energy_kcal",
    "calorieContent": "energy_kcal",
    "Calories": "energy_kcal",
    "energy": "energy_kcal",
    
    # Protein
    "protein": "protein_g",
    "proteinContent": "protein_g",
    "Protein": "protein_g",
    
    # Carbohydrates
    "carbs": "carbs_g",
    "carbohydrates": "carbs_g",
    "carbohydrateContent": "carbs_g",
    "Carbohydrates": "carbs_g",
    
    # Fiber
    "fiber": "fiber_g",
    "fiberContent": "fiber_g",
    "Fiber": "fiber_g",
    
    # Total Fat
    "fat": "total_fat_g",
    "fatContent": "total_fat_g",
    "Fat": "total_fat_g",
    "totalFatContent": "total_fat_g",
    
    # Saturated Fat
    "saturated_fat": "saturated_fat_g",
    "saturatedFatContent": "saturated_fat_g",
    "Saturated Fat": "saturated_fat_g",
    
    # Trans Fat
    "trans_fat": "trans_fat_g",
    "transFatContent": "trans_fat_g",
    
    # Sodium
    "sodium": "sodium_mg",
    "sodiumContent": "sodium_mg",
    "Sodium": "sodium_mg",
    
    # Cholesterol
    "cholesterol": "cholesterol_mg",
    "cholesterolContent": "cholesterol_mg",
    "Cholesterol": "cholesterol_mg",
    
    # Sugar
    "sugar": "sugar_g",
    "sugarContent": "sugar_g",
    "Sugar": "sugar_g",
}

# Units to strip from values
UNIT_PATTERNS = re.compile(
    r'(calories?|kcal|g|gram|mg|milligram|ml|liter|l|oz|%|per serving|per recipe|serving)',
    re.IGNORECASE
)


# ============================================================================
# MACRO VALUE DATA CLASS
# ============================================================================

@dataclass
class MacroValue:
    """Represents a single macro nutrient with per-recipe and per-serving variants."""
    per_recipe: Optional[float] = None
    per_serving: Optional[float] = None
    unit_source: str = "unknown"
    confidence: str = "unknown"  # high, medium, low
    calculated: bool = False  # True if derived from other values
    validation_notes: str = ""


# ============================================================================
# STAGE 1: FIELD STANDARDIZATION
# ============================================================================

def standardize_field_name(raw_field: str) -> Optional[str]:
    """
    Map raw scraper field names to canonical field names.
    
    Args:
        raw_field: Field name from scraper
        
    Returns:
        Canonical field name or None if not recognized
    """
    return FIELD_MAPPING.get(raw_field)


def standardize_nutrients_dict(raw_nutrients: Dict[str, Any]) -> Dict[str, str]:
    """
    Convert raw nutrients dict with varied field names to canonical names.
    
    Args:
        raw_nutrients: Raw nutrient dict from scraper
        
    Returns:
        Dict with canonical field names and string values
    """
    standardized = {}
    
    for raw_field, raw_value in raw_nutrients.items():
        canonical_field = standardize_field_name(raw_field)
        
        if canonical_field and raw_value:
            standardized[canonical_field] = str(raw_value)
    
    return standardized


# ============================================================================
# STAGE 2: VALUE EXTRACTION & SANITIZATION
# ============================================================================

def extract_number(value_str: str) -> Optional[float]:
    """
    Extract numeric value from string with units.
    
    Handles:
    - "100g" → 100
    - "100,50" (European decimal) → 100.5
    - "100 g" → 100
    - "100-150" (range) → 125 (average)
    - "calories" → None
    
    Args:
        value_str: String value with possible units
        
    Returns:
        Extracted float or None if no number found
    """
    if not value_str or not isinstance(value_str, str):
        return None
    
    # Remove unit patterns
    cleaned = UNIT_PATTERNS.sub('', value_str).strip()
    
    # Handle European decimal (comma)
    cleaned = cleaned.replace(',', '.')
    
    # Handle ranges: "100-150" → average
    if '-' in cleaned:
        try:
            parts = [float(p.strip()) for p in cleaned.split('-') if p.strip()]
            if parts:
                return sum(parts) / len(parts)
        except ValueError:
            pass
    
    # Extract first number pattern
    match = re.search(r'(\d+\.?\d*)', cleaned)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    
    return None


def sanitize_macro_value(raw_value: str) -> Optional[float]:
    """
    Sanitize a macro value: extract number and round to 2 decimals.
    
    Args:
        raw_value: Raw value string (may include units)
        
    Returns:
        Sanitized float value or None
    """
    number = extract_number(raw_value)
    
    if number is None:
        return None
    
    # Round to 2 decimals
    return round(number, 2)


# ============================================================================
# STAGE 3: SERVING SIZE NORMALIZATION
# ============================================================================

def parse_yield_servings(yield_str: Optional[str]) -> Optional[int]:
    """
    Parse yield/servings string to extract serving count.
    
    Handles:
    - "4" → 4
    - "4 servings" → 4
    - "serves 4" → 4
    - "4-6" → 5 (average)
    
    Args:
        yield_str: Yield/servings string
        
    Returns:
        Serving count or None
    """
    if not yield_str or not isinstance(yield_str, str):
        return None
    
    yield_str = yield_str.lower().strip()
    
    # Extract number from "serves X" or "X servings"
    match = re.search(r'(\d+)\s*(?:serving|¬)', yield_str)
    if not match:
        match = re.search(r'(\d+)', yield_str)
    
    if match:
        try:
            number = int(match.group(1))
            if number > 0:
                return number
        except ValueError:
            pass
    
    return None


def normalize_per_serving_to_recipe(
    per_serving_value: float,
    serving_count: Optional[int]
) -> Optional[float]:
    """
    Convert per-serving value to per-recipe by multiplying by serving count.
    
    Args:
        per_serving_value: Value per serving
        serving_count: Number of servings
        
    Returns:
        Per-recipe value or None if serving_count unknown
    """
    if not serving_count or serving_count <= 0:
        return None
    
    return round(per_serving_value * serving_count, 2)


# ============================================================================
# STAGE 4: VALIDATION
# ============================================================================

def validate_macro_value(
    macro_field: str,
    value: float
) -> Tuple[bool, Optional[str]]:
    """
    Validate that a macro value is within reasonable ranges.
    
    Args:
        macro_field: Field name (e.g., 'energy_kcal')
        value: Value to validate
        
    Returns:
        Tuple: (is_valid, error_message)
    """
    # Negative values never valid
    if value < 0:
        return False, f"{macro_field} cannot be negative"
    
    # Field-specific ranges
    if macro_field == "energy_kcal":
        if value > 10000:
            return False, f"Energy {value} kcal seems impossibly high (>10000)"
    
    elif macro_field in ["protein_g", "carbs_g", "total_fat_g"]:
        if value > 2000:
            return False, f"{macro_field} value {value}g seems impossibly high"
    
    elif macro_field in ["fiber_g", "sugar_g"]:
        if value > 500:
            return False, f"{macro_field} value {value}g seems impossibly high"
    
    elif macro_field in ["sodium_mg"]:
        if value > 50000:
            return False, f"Sodium {value}mg seems impossibly high"
    
    elif macro_field in ["cholesterol_mg"]:
        if value > 1000:
            return False, f"Cholesterol {value}mg seems impossibly high"
    
    return True, None


def validate_macro_consistency(macros: Dict[str, float]) -> Tuple[bool, Optional[str]]:
    """
    Validate macro values against each other for consistency.
    
    Example: Protein + Carbs + Fat macros shouldn't exceed total energy
    
    Args:
        macros: Dict of macro values
        
    Returns:
        Tuple: (is_consistent, error_message)
    """
    # If we have energy and macronutrients, do a sanity check
    energy = macros.get("energy_kcal")
    protein = macros.get("protein_g")
    carbs = macros.get("carbs_g")
    fat = macros.get("total_fat_g")
    
    if energy and protein and carbs and fat:
        # Rough calculation: protein & carbs = 4 kcal/g, fat = 9 kcal/g
        calculated_kcal = (protein * 4) + (carbs * 4) + (fat * 9)
        
        # Allow 10% tolerance
        if calculated_kcal > energy * 1.1:
            return False, f"Macros ({calculated_kcal:.0f} kcal) exceed energy ({energy} kcal)"
    
    return True, None


# ============================================================================
# STAGE 5: CONFIDENCE SCORING
# ============================================================================

def score_confidence(macro_dict: Dict[str, float]) -> str:
    """
    Score confidence of macro data based on completeness.
    
    - high: All 8 major macros present
    - medium: 4-7 macros present
    - low: 1-3 macros present or with validation issues
    
    Args:
        macro_dict: Sanitized macro values
        
    Returns:
        Confidence level: "high", "medium", or "low"
    """
    major_macros = [
        "energy_kcal", "protein_g", "carbs_g", "total_fat_g",
        "fiber_g", "sodium_mg", "sugar_g", "cholesterol_mg"
    ]
    
    count = sum(1 for macro in major_macros if macro in macro_dict)
    
    if count >= 8:
        return "high"
    elif count >= 4:
        return "medium"
    else:
        return "low"


# ============================================================================
# STAGE 6: OUTPUT CONSTRUCTION
# ============================================================================

def build_macro_value(
    raw_value: Optional[str],
    serving_count: Optional[int],
    macro_field: str
) -> MacroValue:
    """
    Build a MacroValue object from raw value.
    
    Handles sanitization, validation, and per-serving/per-recipe conversion.
    
    Args:
        raw_value: Raw value string
        serving_count: Number of servings
        macro_field: Field name
        
    Returns:
        MacroValue with per_recipe and per_serving
    """
    # Sanitize value
    per_serving = sanitize_macro_value(raw_value)
    
    if per_serving is None:
        return MacroValue(
            per_recipe=None,
            per_serving=None,
            unit_source="missing",
            confidence="low",
            validation_notes="No numeric value found"
        )
    
    # Validate
    is_valid, error_msg = validate_macro_value(macro_field, per_serving)
    if not is_valid:
        return MacroValue(
            per_recipe=None,
            per_serving=None,
            unit_source="invalid",
            confidence="low",
            validation_notes=error_msg or ""
        )
    
    # Calculate per-recipe from per-serving
    per_recipe = None
    calculated = False
    
    if serving_count and serving_count > 0:
        per_recipe = normalize_per_serving_to_recipe(per_serving, serving_count)
        calculated = True
    
    return MacroValue(
        per_recipe=per_recipe,
        per_serving=per_serving,
        unit_source=f"extracted from scraped value",
        confidence="high" if per_serving and not error_msg else "medium",
        calculated=calculated
    )


# ============================================================================
# MAIN NORMALIZATION PIPELINE
# ============================================================================

def normalize_recipe_macros(
    recipe_id: str,
    title: str,
    raw_macros: Dict[str, str],
    yield_servings: Optional[str]
) -> Dict[str, Any]:
    """
    Run complete 6-stage macro normalization pipeline.
    
    Args:
        recipe_id: Recipe ID
        title: Recipe title
        raw_macros: Raw macro dict from scraper
        yield_servings: Yield servings string
        
    Returns:
        Normalized macro dict with confidence scores
    """
    # Stage 1: Standardize field names
    standardized = standardize_nutrients_dict(raw_macros)
    
    # Parse serving count
    serving_count = parse_yield_servings(yield_servings)
    
    # Stage 2-6: Process each macro field
    normalized_macros = {}
    
    for canonical_field, raw_value in standardized.items():
        macro_value = build_macro_value(raw_value, serving_count, canonical_field)
        normalized_macros[canonical_field] = asdict(macro_value)
    
    # Overall confidence
    macro_values = {k: v["per_recipe"] or 0 for k, v in normalized_macros.items()}
    overall_confidence = score_confidence({k: 1 for k in normalized_macros.keys()})
    
    # Consistency check
    is_consistent, consistency_note = validate_macro_consistency(macro_values)
    
    return {
        "recipe_id": recipe_id,
        "title": title,
        "yield_servings": serving_count,
        "macros": normalized_macros,
        "overall_confidence": overall_confidence,
        "consistency_valid": is_consistent,
        "consistency_note": consistency_note or "ok"
    }


# ============================================================================
# FILE I/O PIPELINE
# ============================================================================

def normalize_macros_file(input_file: str, output_file: str = None) -> None:
    """
    Load macros.json, normalize all recipes, save to normalized-macros.json.
    
    Args:
        input_file: Path to macros.json
        output_file: Path to save normalized-macros.json
    """
    # Load input
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"Error: {input_file} not found")
        sys.exit(1)
    
    print(f"Loading macros from: {input_path}")
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            macros_list = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)
    
    print(f"Normalizing {len(macros_list)} recipes...")
    
    # Normalize each recipe
    normalized = []
    high_confidence = 0
    medium_confidence = 0
    low_confidence = 0
    
    for macro_item in macros_list:
        normalized_item = normalize_recipe_macros(
            recipe_id=macro_item.get("id"),
            title=macro_item.get("title"),
            raw_macros=macro_item.get("macros", {}),
            yield_servings=macro_item.get("yield_servings")
        )
        
        normalized.append(normalized_item)
        
        conf = normalized_item["overall_confidence"]
        if conf == "high":
            high_confidence += 1
        elif conf == "medium":
            medium_confidence += 1
        else:
            low_confidence += 1
    
    # Save output
    if not output_file:
        output_file = str(input_path.parent / "normalized-macros.json")
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(normalized, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✓ Normalized {len(normalized)} recipes")
    print(f"  High confidence: {high_confidence}")
    print(f"  Medium confidence: {medium_confidence}")
    print(f"  Low confidence: {low_confidence}")
    print(f"{'='*70}")
    print(f"Saved to: {output_path}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("PHASE 2.2: MACRO NORMALIZER - Standardizing nutrient data")
    print("="*70 + "\n")
    
    normalize_macros_file(
        input_file="source/macros.json",
        output_file="source/normalized-macros.json"
    )
    
    print(f"\n{'='*70}")
    print("Phase 2.2 Complete: Normalized macros ready for database import")
    print(f"{'='*70}\n")

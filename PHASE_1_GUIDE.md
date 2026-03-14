# Just Meal Planner - Phase 1 Implementation

## Overview

Phase 1 establishes the foundation: **Parse recipes and normalize ingredients**. The workflow converts unstructured recipe text into a canonical ingredient registry using machine learning (ingredient-parser) and an internal ingredient_id system.

---

## Architecture: Three Key Systems

### 1. **Ingredient Parser (NLP)**  
- **Tool:** `ingredient_parser` (v2.5.0) with foundation_foods
- **Input:** Raw ingredient strings from web recipes
- **Output:** Parsed components (name, amount, preparation, FDC match)
- **File:** [normalizer/ingredient-normalizer.py](normalizer/ingredient-normalizer.py)

### 2. **Ingredient Registry (JSON)**
- **Purpose:** Single source of truth for 600-800 canonical ingredients  
- **Not database:** Git-controlled, migrated to DB in Phase 3
- **File:** [normalizer/ingredient_registry.json](normalizer/ingredient_registry.json)
- **Key feature:** Each item gets `ingredient_id` (e.g., `ing_ham_serrano_001`)

### 3. **Corrections Override System (JSON)**
- **Purpose:** Developer-controlled list of known bad FDC mappings
- **Trigger:** Catches high-confidence false positives like "jamón→pepper"
- **File:** [normalizer/ingredient_corrections.json](normalizer/ingredient_corrections.json)
- **12 seed entries:** Ready for expansion as parsing runs

---

## Workflow: From Recipe Text to Database

```
Recipe Website
    ↓
OG-scraper → ingredients.json (raw strings)
    ↓
ingredient-normalizer.py (NLP + registry + corrections)
    ├─ Load ingredient_corrections.json
    ├─ Load ingredient_registry.json
    ├─ Parse each ingredient with NLP
    ├─ Check corrections FIRST
    ├─ Check FDC confidence (threshold 0.85)
    ├─ Check semantic validation
    └─ Output: ingredient_id + metadata
    ↓
normalized-ingredients.json (structured)
    ↓
import_to_db.py (Phase 1 DB)
    ├─ recipes table (recipe_id, title)
    ├─ ingredients table (ingredient_id, canonical_name, category)
    └─ recipe_ingredients (FK to both)
    ↓
Database ready for Phase 2 (grocery lists)
```

---

## File Structure

```
d:\just_mealplanner\
│
├── normalizer/
│   ├── ingredient-normalizer.py       # Main parser (with registry integration)
│   ├── ingredient_registry.json       # 600+ canonical ingredients
│   ├── ingredient_corrections.json    # 12 known FDC failures
│   └── requirements.txt               # Dependencies
│
├── source/
│   ├── ingredients.json               # Input (raw from scraper)
│   ├── normalized-ingredients.json    # Output (structured with ingredient_id)
│   └── [other data files]
│
├── schema.sql                         # PostgreSQL DDL (all phases)
├── import_to_db.py                    # Phase 1 DB import script
├── IMPLEMENTATION_GUIDE.md            # Detailed workflows (this doc)
├── FINAL_SCHEMA.md                    # Database design rationale
└── docs/
    └── [future API documentation]
```

---

## Step 1: Parse Ingredients

### Input: [source/ingredients.json](source/ingredients.json)
```json
{
  "id": "rec_001",
  "title": "Croquetas de Jamón",
  "ingredients": [
    "1.5 cups of ground ham",
    "½ cup of ground jamón serrano",
    "1 tablespoon vino seco",
    ...
  ]
}
```

### Run Normalizer
```bash
cd normalizer
python ingredient-normalizer.py
```

### Output: [source/normalized-ingredients.json](source/normalized-ingredients.json)
```json
{
  "recipe_id": "rec_001",
  "recipe_title": "Croquetas de Jamón",
  "ingredients": [
    {
      "ingredient_id": "ing_ham_serrano_001",
      "display_text": "½ cup of ground jamón serrano",
      "canonical_ingredient": {
        "ingredient_id": "ing_ham_serrano_001",
        "canonical_name": "Ham, Jamón Serrano",
        "source": "ingredient_corrections_override"
      },
      "amount_data": {
        "aggregation_type": "volume",
        "metric_ml": 118.29,
        "total_count": 0.0
      }
    }
  ]
}
```

---

## Step 2: Understand ingredient_id Resolution

### Priority (in order):

#### 1️⃣ **Corrections Override** (Highest Priority)
Pattern matching in [ingredient_corrections.json](normalizer/ingredient_corrections.json):
```json
{
  "parsed_ingredient_pattern": "jamón serrano",
  "fdc_id_that_failed": 169395,
  "fdc_canonical_that_failed": "Peppers, serrano, raw",
  "ingredient_id_to_use": "ing_ham_serrano_001",
  "reason": "Parser confusion: jamón (ham) != serrano peppers"
}
```

When normalizer parses "jamón serrano":
- ✓ Finds correction entry
- ✓ Uses `ing_ham_serrano_001` directly
- ✓ Logs: "CORRECTION APPLIED"

#### 2️⃣ **FDC Mapping** (If In Registry)
If FDC ID 789828 (butter) is in [ingredient_registry.json](normalizer/ingredient_registry.json):
- ✓ Confidence passes (≥ 0.85)
- ✓ Semantic validation passes
- ✓ Maps to ingredient_id in registry
- ✓ Logs: "FDC MAPPED"

#### 3️⃣ **Unresolved** (No Match)
If ingredient not in corrections and FDC not in registry:
- ✗ ingredient_id = `None`
- ✗ Noted for manual mapping
- ✓ Logs: "FDC NOT IN REGISTRY"

---

## Step 3: Import to Database

### Create Database

**SQLite (Development - Recommended for Phase 1):**
```bash
cd d:\just_mealplanner
python import_to_db.py source/normalized-ingredients.json
```

**PostgreSQL (Production):**
```bash
# First create schema
psql -U postgres -d just_meal_planner < schema.sql

# Then import data
python import_to_db.py source/normalized-ingredients.json --postgres
```

### Verify Import

```sql
-- View recipes
SELECT COUNT(*) as total_recipes FROM recipes;

-- View ingredients with sources
SELECT ingredient_id, canonical_name, type FROM ingredients
WHERE type = 'ingredient_corrections_override'
LIMIT 5;

-- View correction-derived ingredients
SELECT 
  ri.display_text,
  ri.ingredient_id,
  i.canonical_name,
  ji.parsed_amount_data->>'metric_ml' as metric_ml
FROM recipe_ingredients ri
JOIN ingredients i ON ri.ingredient_id = i.ingredient_id
WHERE i.type = 'ingredient_corrections_override'
LIMIT 10;
```

---

## Key Features Implemented

### ✅ Confidence Threshold
- Rejects FDC matches below 0.85 confidence
- Prevents nutmeg butter (0.621) false positive

### ✅ Aggregation Type Split
- Volume items (ml): "2 cups", "1 tbsp"
- Count items (qty): "2 bay leaves", "3 eggs"
- Unquantified: "Oil for frying", "To taste"

### ✅ Semantic Validation
- Catches impossible combinations:
  - Wine → Dairy (false positive vino seco)
  - Ham → Vegetables (false positive jamón)
- Flags for developer review

### ✅ Float Precision Fix
- Rounds to 2 decimals
- Before: `354.88235474999993` ml
- After: `354.88` ml

### ✅ Ingredient Corrections
- 12 seed corrections documenting known issues
- Pattern-based matching ("jamón serrano", "vino seco")
- Extensible as parsing finds new issues

---

## Debugging Phase 1

### Check Normalizer Output
```python
import json
with open('source/normalized-ingredients.json') as f:
    data = json.load(f)
    recipe = data[0]
    for ing in recipe['ingredients'][:3]:
        print(f"{ing['display_text']}")
        print(f"  ingredient_id: {ing.get('ingredient_id')}")
        print(f"  source: {ing['canonical_ingredient'].get('source')}")
```

### Run with Debug Logging
```bash
cd normalizer
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
import ingredient-normalizer
# Will show detailed resolution paths
"
```

### Check Correction Application
```bash
grep -i "jamón\|vino\|correction" source/normalized-ingredients.json
# Should show ingredient_id populated for both
```

---

## Populating ingredient_registry.json

### Current Status
- **Seed ingredients:** 12 (template examples)
- **Needed:** ~600 total for comprehensive recipe coverage

### Population Strategy

1. **From existing recipes:**
   ```python
   import json
   with open('source/normalized-ingredients.json') as f:
       data = json.load(f)
   
   # Collect all FDC-matched ingredients
   fdc_matches = {}
   for recipe in data:
       for ing in recipe['ingredients']:
           if ing['ingredient_id'] is None:
               canonical = ing['canonical_ingredient']
               fdc_id = canonical.get('fdc_reference')
               if fdc_id:
                   fdc_matches[fdc_id] = canonical
   
   # Generate entries for each unique FDC match
   for fdc_id, data in fdc_matches.items():
       print(f"Add entry for: {data['canonical_name']} (FDC {fdc_id})")
   ```

2. **Format for each ingredient:**
   ```json
   {
     "ingredient_id": "ing_[type]_[subtype]_###",
     "canonical_name": "Official FDC name",
     "category": "FDC category",
     "type": "basic_type",
     "fdc_reference": {
       "fdc_id": 12345,
       "fdc_canonical_name": "Name from FDC",
       "is_correct_match": true
     },
     "aliases": ["common", "alternate", "names"],
     "substitutions": []
   }
   ```

3. **Naming convention:**
   - Format: `ing_[category]_[item]_###`
   - Examples:
     - `ing_ham_serrano_001`
     - `ing_onion_yellow_001`
     - `ing_wine_dry_white_001`
     - `ing_butter_unsalted_001`

---

## Next Steps: Phase 2 Preparation

Phase 2 (Grocery Lists) will need:

1. **Populated ingredients table:**
   - ingredient_id, canonical_name, category
   - Ready from this import ✓

2. **Amount aggregation logic:**
   - Uses `aggregation_type` field ✓
   - Volume: SUM metric_ml
   - Count: SUM total_count
   - Unquantified: Flag for user

3. **Units conversion table:**
   - Phase 2 feature
   - ingredient_conversions table
   - Support volume, count, weight units

---

## Troubleshooting

| Issue                                     | Cause                              | Solution                                          |
| ----------------------------------------- | ---------------------------------- | ------------------------------------------------- |
| `ingredient_id: null`                     | FDC match not in registry          | Add to ingredient_registry.json                   |
| `fdc_not_in_registry`                     | FDC ID found but no registry entry | Populate registry from FDC matches                |
| Low confidence filtered                   | Confidence < 0.85                  | If valid, lower threshold or add to corrections   |
| `ingredient_corrections_override` applied | Pattern matched                    | Review correction, adjust if needed               |
| Database insert fails                     | RecipeKey or FK constraint         | Ensure recipes inserted before recipe_ingredients |

---

## Summary

**Phase 1 creates:**
- ✅ Normalized ingredient data with `ingredient_id`
- ✅ Database tables (recipes, ingredients, recipe_ingredients)
- ✅ Seed ingredient registry (12 examples)
- ✅ Corrections system for known issues
- ✅ Ready for Phase 2 grocery list aggregation

**Files modified:**
- `normalizer/ingredient-normalizer.py` (registry integration)
- `normalizer/ingredient_registry.json` (seed template)
- `normalizer/ingredient_corrections.json` (seed corrections)

**Files created:**
- `import_to_db.py` (database import script)
- `schema.sql` (PostgreSQL DDL)
- `IMPLEMENTATION_GUIDE.md` (this guide)

---

## Quick Reference

```bash
# 1. Parse ingredients from source
cd normalizer && python ingredient-normalizer.py

# 2. Import to SQLite (development)
python import_to_db.py source/normalized-ingredients.json

# 3. Import to PostgreSQL (production)
python import_to_db.py source/normalized-ingredients.json --postgres

# 4. Verify database
sqlite3 just_mealplanner.db "SELECT COUNT(*) FROM recipes;"
```

---

**Ready for Phase 2: Grocery List Aggregation** 📋

Next: User selects recipes → system aggregates ingredients → generates shopping list

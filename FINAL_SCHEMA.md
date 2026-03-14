# JUST MEAL PLANNER - DATABASE SCHEMA
# Focused on Phase 1-2, with scaffolding for Phase 3 user features

# ============================================================================
# CORE RECIPE DATA - IMMEDIATE (Phase 1)
# ============================================================================

TABLE: recipes
├─ recipe_id (PK, UUID)
├─ title (STRING)
├─ source_url (STRING, nullable)
├─ yield_servings (INT, nullable)  # Can be NULL if scraper didn't capture
├─ cook_time_minutes (INT, nullable)
├─ prep_time_minutes (INT, nullable)
├─ created_at (TIMESTAMP)
└─ updated_at (TIMESTAMP)

INDEXES: recipe_id, title


TABLE: recipe_ingredients (CRITICAL FOR PHASE 2)
├─ recipe_ingredient_id (PK, UUID)
├─ recipe_id (FK → recipes.recipe_id)
├─ ingredient_id (FK → ingredients.ingredient_id)
├─ display_text (STRING)  # "1.5 cups finely diced"
├─ parsed_amount_data (JSON)
│  ├─ type: "simple" | "composite" | "unquantified"
│  ├─ aggregation_type: "volume" | "count" | "unquantified"
│  ├─ quantity: 1.5 (DECIMAL)
│  ├─ unit: "cup" (STRING)
│  ├─ metric_ml: 354.88 (DECIMAL, for volume items)
│  ├─ total_count: 0.0 (DECIMAL, for count items)
│  └─ is_approximate: false (BOOLEAN)
├─ parsed_preparation (STRING, nullable)  # "finely diced", "chopped"
├─ sort_order (INT)
├─ created_at (TIMESTAMP)
└─ updated_at (TIMESTAMP)

INDEXES: recipe_id, ingredient_id, (recipe_id, sort_order)


# ============================================================================
# GLOBAL INGREDIENT REGISTRY (JSON in Git - NOT DB for Phase 1-2)
# ============================================================================

FILE: normalizer/ingredient_registry.json
STRUCTURE:
{
  "ingredients": [
    {
      "ingredient_id": "ing_ham_serrano_001",
      "canonical_name": "Ham, Jamón Serrano",
      "category": "Cold Cuts & Cured Meats",
      "type": "cured_meat",
      
      "fdc_reference": {
        "fdc_id": null,
        "fdc_reason": "FDC ID 169395 is incorrect (maps to pepper)",
        "is_correct_match": false
      },
      
      "aliases": ["jamón", "jamon serrano", "spanish ham", "jamón serrano"],
      
      "substitutions": [
        {"ingredient_id": "ing_ham_prosciutto_001", "reason": "similar_cured_meat"},
        {"ingredient_id": "ing_ham_iberico_001", "reason": "similar_spanish_meat"}
      ],
      
      "metadata": {
        "region": "Spain",
        "preservation_method": "cured"
      }
    },
    
    {
      "ingredient_id": "ing_wine_dry_white_001",
      "canonical_name": "Wine, Dry White",
      "category": "Beverages",
      "type": "beverage",
      
      "fdc_reference": {
        "fdc_id": null,
        "fdc_reason": "FDC ID 746765 is incorrect (maps to queso seco/cheese)",
        "is_correct_match": false
      },
      
      "aliases": ["vino seco", "dry white wine", "white wine"],
      
      "substitutions": [
        {"ingredient_id": "ing_wine_dry_red_001", "reason": "flavor_substitute"},
        {"ingredient_id": "ing_stock_chicken_001", "reason": "cooking_substitute"}
      ],
      
      "metadata": {
        "style": "dry",
        "color": "white"
      }
    }
    
    // ... 795+ more ingredients
  ]
}

FILE: normalizer/ingredient_corrections.json  
STRUCTURE:
{
  "rejected_fdc_matches": [
    {
      "parsed_ingredient": "jamón serrano",
      "fdc_id_that_failed": 169395,
      "ingredient_id_to_use": "ing_ham_serrano_001",
      "reason": "FDC maps to pepper, should be ham"
    },
    {
      "parsed_ingredient": "vino seco",
      "fdc_id_that_failed": 746765,
      "ingredient_id_to_use": "ing_wine_dry_white_001",
      "reason": "FDC maps to cheese, should be wine"
    },
    // ... ~10-12 more known issues
  ]
}


# ============================================================================
# GLOBAL INGREDIENT REGISTRY (Seed Data Only)
# ============================================================================

TABLE: ingredients (Seeded from ingredient_registry.json in Phase 1)
├─ ingredient_id (PK, STRING)  # "ing_ham_serrano_001"
├─ canonical_name (STRING)
├─ category (STRING)
├─ type (STRING)
├─ aliases_json (JSON)  # Denormalized for fast lookup
├─ metadata_json (JSON)
└─ created_at (TIMESTAMP)

INDEXES: ingredient_id, type, category, (full-text search on canonical_name)

NOTE: In Phase 1-2, this is read-only, seeded from JSON.
In Phase 3, add update logic.


# ============================================================================
# MATH & LOGISTICS FOR PHASE 2
# ============================================================================

TABLE: ingredient_conversions (Reference data - Phase 2)
├─ conversion_id (PK, INT)
├─ ingredient_id (FK → ingredients.ingredient_id)
├─ from_unit (STRING)  # "cup"
├─ to_unit (STRING)  # "gram"
├─ conversion_factor (DECIMAL)  # 240
├─ notes (TEXT)
└─ created_at (TIMESTAMP)

INDEXES: ingredient_id, (from_unit, to_unit)

# Example:
# ing_flour_all_purpose_001: 1 cup = 125g
# ing_ham_serrano_001: 1 cup = 200g (estimated)


TABLE: grocery_lists (Phase 2)
├─ grocery_list_id (PK, UUID)
├─ user_id (FK → users.user_id, nullable for Phase 2)
├─ name (STRING)  # "Weekly shopping"
├─ created_from_recipes (ARRAY of recipe_ids)
├─ status (STRING)  # "draft", "ready", "completed"
├─ created_at (TIMESTAMP)
└─ updated_at (TIMESTAMP)

INDEXES: user_id, status, created_at


TABLE: grocery_list_items (Phase 2)
├─ item_id (PK, UUID)
├─ grocery_list_id (FK → grocery_lists.grocery_list_id)
├─ ingredient_id (FK → ingredients.ingredient_id)
├─ total_quantity (DECIMAL)  # Aggregated across recipes
├─ unit (STRING)  # Final unit for shopping
├─ metric_ml_equivalent (DECIMAL, nullable)  # For volume
├─ total_count_equivalent (DECIMAL, nullable)  # For counts
├─ aggregation_source (JSON)  # [{recipe_id, original_qty, unit}, ...]
├─ checked_off (BOOLEAN)
└─ notes (STRING, nullable)

INDEXES: grocery_list_id, ingredient_id


# ============================================================================
# USER FEATURES - SCAFFOLD FOR PHASE 3
# ============================================================================

TABLE: users (Phase 3)
├─ user_id (PK, UUID)
├─ email (STRING, UNIQUE)
├─ username (STRING, UNIQUE)
├─ password_hash (STRING)
├─ dietary_restrictions (JSON)  # ["gluten-free", "vegan", ...]
├─ allergies (JSON)  # ["peanuts", "shellfish", ...]
├─ created_at (TIMESTAMP)
└─ updated_at (TIMESTAMP)


TABLE: user_ingredient_preferences (Phase 3 - User customizations)
├─ preference_id (PK, UUID)
├─ user_id (FK → users.user_id)
├─ ingredient_id (FK → ingredients.ingredient_id)
├─ custom_aliases (ARRAY)  # ["my ham", "my jamón"]
├─ is_available (BOOLEAN)  # User can exclude from suggestions
├─ is_allergic (BOOLEAN)
├─ preferred_substitute_id (FK → ingredients.ingredient_id, nullable)
├─ custom_notes (TEXT)
└─ updated_at (TIMESTAMP)

INDEXES: user_id, ingredient_id


TABLE: user_ingredient_corrections (Phase 3 - Crowdsourced)
├─ correction_id (PK, UUID)
├─ user_id (FK → users.user_id)
├─ ingredient_id (FK → ingredients.ingredient_id)
├─ issue_type (STRING)  # "wrong_category", "missing_alias"
├─ description (TEXT)
├─ votes_agree (INT)
├─ status (STRING)  # "pending", "approved", "merged"
├─ created_at (TIMESTAMP)
└─ resolved_at (TIMESTAMP, nullable)

INDEXES: ingredient_id, status


TABLE: meal_plans (Phase 3)
├─ meal_plan_id (PK, UUID)
├─ user_id (FK → users.user_id)
├─ name (STRING)
├─ start_date (DATE)
├─ end_date (DATE)
├─ created_at (TIMESTAMP)
└─ updated_at (TIMESTAMP)

INDEXES: user_id, start_date


TABLE: meal_plan_recipes (Phase 3)
├─ item_id (PK, UUID)
├─ meal_plan_id (FK → meal_plans.meal_plan_id)
├─ recipe_id (FK → recipes.recipe_id)
├─ day_number (INT)  # 0-6 for week, or day offset
├─ meal_type (STRING)  # "breakfast", "lunch", "dinner"
├─ servings_to_make (INT, nullable)  # Override recipe yield
├─ created_at (TIMESTAMP)
└─ updated_at (TIMESTAMP)

INDEXES: meal_plan_id, day_number


# ============================================================================
# TOTAL TABLE COUNT BY PHASE
# ============================================================================

PHASE 1 (Parsing):
└─ recipes
└─ recipe_ingredients
└─ ingredients (seeded from JSON)
└─ Total: 3 tables

PHASE 2 (Grocery Lists):
├─ [From Phase 1: recipes, recipe_ingredients, ingredients]
└─ ingredient_conversions
└─ grocery_lists
└─ grocery_list_items
└─ Total: 6 tables

PHASE 3 (Multi-user):
├─ [From Phase 1-2: all above]
└─ users
└─ user_ingredient_preferences
└─ user_ingredient_corrections
└─ meal_plans
└─ meal_plan_recipes
└─ Total: 11 tables


# ============================================================================
# WHAT STAYS IN GIT (Not DB)
# ============================================================================

normalizer/ingredient_registry.json
├─ ~600-800 canonical ingredients
├─ Global reference, version-controlled
├─ Updated by devs, imported into DB at Phase 3
└─ Single source of truth for ingredient definitions

normalizer/ingredient_corrections.json
├─ ~10-12 known FDC mapping failures
├─ Developer overrides
├─ Used by normalizer at parse time
└─ Empty in Phase 3 (merged into ingredient_registry.json)


# ============================================================================
# KEY DATA FLOW FOR PHASE 1-2
# ============================================================================

PARSE TIME (normalizer/ingredient-normalizer.py):
1. Parse ingredient text with NLP
2. Get FDC match
3. Check ingredient_corrections.json for overrides
4. Return ingredient_id (from ingredient_registry.json)
5. Output to normalized-ingredients.json with ingredient_id

OUTPUT (normalized-ingredients.json):
{
  "recipe_id": "rec_001",
  "recipe_title": "Croquetas de Jamón",
  "ingredients": [
    {
      "display_text": "½ cup ground jamón serrano",
      "ingredient_id": "ing_ham_serrano_001",  ← Not FDC ID!
      "canonical_ingredient": {
        "canonical_name": "Ham, Jamón Serrano",
        "category": "Cold Cuts & Cured Meats",
        "source": "ingredient_registry_override"
      },
      "amount_data": {
        "type": "simple",
        "aggregation_type": "volume",
        "quantity": 0.5,
        "unit": "cup",
        "metric_ml": 118.29,
        "total_count": 0.0
      }
    }
  ]
}

DATABASE IMPORT (Phase 1):
1. Load normalized-ingredients.json
2. Insert into recipes table (recipe_id, title, yield_servings, etc.)
3. Insert into recipe_ingredients (recipe_id, ingredient_id, parsed_amount_data, etc.)
4. Ingredients table already seeded from ingredient_registry.json

PHASE 2 GROCERY AGGREGATION:
1. User selects recipes: [rec_001, rec_002, rec_003]
2. Query recipe_ingredients WHERE recipe_id IN (rec_001, rec_002, rec_003)
3. GROUP BY ingredient_id
4. For each ingredient:
   - IF aggregation_type == "volume": SUM metric_ml
   - IF aggregation_type == "count": SUM total_count
   - IF aggregation_type == "unquantified": FLAG for manual review
5. Insert into grocery_lists & grocery_list_items


# ============================================================================
# ADVANTAGES OF THIS APPROACH
# ============================================================================

✓ No FDC ID dependency
✓ Developer controls ingredient mappings via JSON
✓ Easy to add/correct ingredients
✓ 10-12 known bad mappings documented
✓ User preferences can override global registry (Phase 3)
✓ All Phase 2 math works (volume + count aggregation)
✓ Crowdsourcing path clear for Phase 3
✓ JSON in git = version controlled, reviewable changes
✓ Migrates to DB table naturally in Phase 3

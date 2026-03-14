# Database Schema for Just Meal Planner
# Organized by feature area and user-facing vs. internal

## PHASE 1: Recipe Parsing & Normalization (Current)
## PHASE 2: Grocery Lists & Recipe Scaling  
## PHASE 3: Full Stack with Multi-user

---

# ============================================================================
# CORE RECIPE DATA (User-Facing & Internal)
# ============================================================================

TABLE: recipes
├─ recipe_id (PK, UUID)
├─ title (STRING)
├─ source_url (STRING, nullable)
├─ yield_servings (INT)
├─ cook_time_minutes (INT, nullable)
├─ prep_time_minutes (INT, nullable)
├─ created_at (TIMESTAMP)
├─ updated_at (TIMESTAMP)
└─ metadata (JSON) # Tags, difficulty, cuisine, etc.
   
INDEXES: recipe_id, title

TABLE: recipe_ingredients (Join Table - Core to Phase 2!)
├─ recipe_ingredient_id (PK, UUID)
├─ recipe_id (FK → recipes.recipe_id)
├─ ingredient_id (FK → ingredients.ingredient_id)
├─ parsed_amount_data (JSON) # {"type": "simple", "quantity": 1.5, "unit": "cup", "metric_ml": 354.88, "aggregation_type": "volume"}
├─ parsed_preparation (STRING) # "finely diced", "chopped", etc.
├─ display_text (STRING) # "1.5 cups finely diced"
├─ sort_order (INT) # Ingredient order in recipe
├─ created_at (TIMESTAMP)
└─ updated_at (TIMESTAMP)

INDEXES: recipe_id, ingredient_id, (recipe_id, sort_order)

---

# ============================================================================
# INGREDIENT REGISTRY (Internal - NOT directly user-facing)
# ============================================================================

TABLE: ingredients (The 600-800 canonical ingredient list)
├─ ingredient_id (PK, STRING) # "ing_ham_serrano_001"
├─ canonical_name (STRING) # "Ham, Jamón Serrano"
├─ category (STRING) # "Cold Cuts & Cured Meats"
├─ type (STRING) # "cured_meat", "beverage", "vegetable", "spice", etc.
├─ description (TEXT, nullable)
├─ crowdsourced_name (STRING, nullable) # Community-suggested name
└─ metadata (JSON)
   ├─ region (STRING, nullable) # "Spain", "Italy"
   ├─ preservation_method (STRING, nullable)
   ├─ common_conversions (JSON) # {"1 cup": "~200g"}
   ├─ typical_quantity_unit (STRING) # For validation: "ml", "gram", "count"
   └─ verified_at (TIMESTAMP)

INDEXES: ingredient_id, type, category

TABLE: ingredient_aliases
├─ alias_id (PK, INT)
├─ ingredient_id (FK → ingredients.ingredient_id)
├─ alias_name (STRING) # "jamón", "jamon", "spanish ham"
├─ locale (STRING) # "en", "es", "fr" for language-specific aliases
├─ created_at (TIMESTAMP)
└─ source (STRING) # "parser_output", "crowdsourced", "manual"

INDEXES: ingredient_id, alias_name, (ingredient_id, locale)

TABLE: ingredient_substitutions (For Phase 2: Recipe Scaling & Suggestions)
├─ substitution_id (PK, INT)
├─ ingredient_id (FK → ingredients.ingredient_id)
├─ substitute_ingredient_id (FK → ingredients.ingredient_id)
├─ substitution_ratio (DECIMAL) # 1.0 = 1:1, 0.8 = 80%, NULL = no ratio
├─ reason (STRING) # "similar_cured_meat", "flavor_substitute", "dietary_alternative"
├─ confidence (DECIMAL 0-1) # How certain is this substitution?
└─ verified (BOOLEAN)

INDEXES: ingredient_id, substitute_ingredient_id

---

# ============================================================================
# INGREDIENT CORRECTIONS & QUALITY (Developer + Crowdsourced)
# ============================================================================

TABLE: ingredient_corrections (Developer Overrides - in code/JSON)
├─ correction_id (PK, INT)
├─ ingredient_id (FK → ingredients.ingredient_id)
├─ fdc_id_failed (INT, nullable) # "This FDC ID is wrong"
├─ fdc_failed_reason (TEXT) # "Maps to Pepper instead of Ham"
├─ source (STRING) # "manual_override", "semantic_validation_reject"
├─ developer (STRING) # Who made the correction
├─ notes (TEXT)
├─ created_at (TIMESTAMP)
└─ updated_at (TIMESTAMP)

INDEXES: ingredient_id, created_at

TABLE: ingredient_crowdsourced_corrections (Phase 3 - Public Crowdsourcing)
├─ crowdsource_id (PK, INT)
├─ ingredient_id (FK → ingredients.ingredient_id)
├─ user_id (FK → users.user_id, nullable for anonymous)
├─ issue_type (STRING) # "wrong_category", "missing_alias", "incorrect_substitution"
├─ description (TEXT)
├─ proposed_value (JSON, nullable) # What should it be?
├─ votes_agree (INT)
├─ votes_disagree (INT)
├─ status (STRING) # "pending", "approved", "rejected", "merged"
├─ created_at (TIMESTAMP)
└─ resolved_at (TIMESTAMP, nullable)

INDEXES: ingredient_id, status, votes_agree DESC

---

# ============================================================================
# FDC REFERENCE DATA (Optional - for nutritional lookup)
# ============================================================================

TABLE: ingredient_fdc_mapping
├─ mapping_id (PK, INT)
├─ ingredient_id (FK → ingredients.ingredient_id)
├─ fdc_id (INT, nullable) # FDC ID if we have one
├─ fdc_canonical_name (STRING, nullable)
├─ fdc_category (STRING, nullable)
├─ fdc_confidence (DECIMAL 0-1, nullable) # Parser's confidence
├─ is_correct_match (BOOLEAN) # Manual verification
├─ notes (TEXT)
└─ last_verified (TIMESTAMP)

INDEXES: ingredient_id, fdc_id

TABLE: ingredient_nutritional_data
├─ nutrition_id (PK, INT)
├─ ingredient_id (FK → ingredients.ingredient_id)
├─ serving_size_amount (DECIMAL)
├─ serving_size_unit (STRING) # "g", "ml", "cup", "piece"
├─ calories (DECIMAL)
├─ protein_g (DECIMAL)
├─ fat_g (DECIMAL)
├─ carbs_g (DECIMAL)
├─ fiber_g (DECIMAL)
├─ sodium_mg (DECIMAL)
├─ allergen_flags (JSON) # {"gluten": true, "dairy": false, ...}
├─ source (STRING) # "fdc", "usda", "user_input"
└─ updated_at (TIMESTAMP)

INDEXES: ingredient_id

---

# ============================================================================
# LOGISTICS & MATH (Phase 2: Grocery Lists & Recipe Scaling)
# ============================================================================

TABLE: ingredient_conversions (Reference Data)
├─ conversion_id (PK, INT)
├─ ingredient_id (FK → ingredients.ingredient_id)
├─ from_unit (STRING) # "cup"
├─ to_unit (STRING) # "gram"
├─ conversion_factor (DECIMAL) # 240
├─ is_approximate (BOOLEAN)
├─ confidence (DECIMAL 0-1)
└─ notes (TEXT)

INDEXES: ingredient_id, (from_unit, to_unit)

TABLE: grocery_lists (Phase 2 - User Shopping)
├─ grocery_list_id (PK, UUID)
├─ user_id (FK → users.user_id)
├─ name (STRING) # "Weekly shopping"
├─ planned_for_date (DATE)
├─ status (STRING) # "draft", "ready", "completed"
├─ created_at (TIMESTAMP)
├─ updated_at (TIMESTAMP)
└─ metadata (JSON)

INDEXES: user_id, status, planned_for_date

TABLE: grocery_list_items (Phase 2)
├─ item_id (PK, UUID)
├─ grocery_list_id (FK → grocery_lists.grocery_list_id)
├─ ingredient_id (FK → ingredients.ingredient_id)
├─ total_quantity (DECIMAL) # Aggregated across recipes
├─ unit (STRING) # Final unit for display
├─ metric_ml_equivalent (DECIMAL, nullable) # For volume items
├─ total_count_equivalent (DECIMAL, nullable) # For count items (eggs, bay leaves)
├─ aggregation_source (JSON) # [{recipe_id, original_qty, unit}, ...]
├─ checked_off (BOOLEAN)
└─ notes (STRING, nullable)

INDEXES: grocery_list_id, ingredient_id

---

# ============================================================================
# USER FEATURES (Phase 3 - Multi-user)
# ============================================================================

TABLE: users
├─ user_id (PK, UUID)
├─ email (STRING, UNIQUE)
├─ username (STRING, UNIQUE)
├─ password_hash (STRING)
├─ created_at (TIMESTAMP)
├─ updated_at (TIMESTAMP)
└─ preferences (JSON) # Dietary restrictions, allergies, etc.

TABLE: meal_plans
├─ meal_plan_id (PK, UUID)
├─ user_id (FK → users.user_id)
├─ name (STRING) # "Week of March 14"
├─ start_date (DATE)
├─ end_date (DATE)
├─ created_at (TIMESTAMP)
└─ updated_at (TIMESTAMP)

TABLE: meal_plan_items
├─ item_id (PK, UUID)
├─ meal_plan_id (FK → meal_plans.meal_plan_id)
├─ recipe_id (FK → recipes.recipe_id)
├─ day_of_week (INT) # 0-6 or date?
├─ meal_type (STRING) # "breakfast", "lunch", "dinner", "snack"
├─ servings_to_make (INT) # Scale factor
├─ created_at (TIMESTAMP)
└─ updated_at (TIMESTAMP)

---

# ============================================================================
# AUDIT & METADATA
# ============================================================================

TABLE: audit_log
├─ log_id (PK, INT)
├─ table_name (STRING) # "ingredients", "recipe_ingredients", etc.
├─ record_id (STRING)
├─ action (STRING) # "INSERT", "UPDATE", "DELETE"
├─ changed_fields (JSON) # {field: {old_value, new_value}}
├─ user_id (FK → users.user_id, nullable for system)
├─ timestamp (TIMESTAMP)
└─ reason (STRING, nullable)

INDEXES: table_name, timestamp, user_id

---

# ============================================================================
# WHAT'S NOT IN DATABASE (Stays as JSON in Git for Dev)
# ============================================================================

normalizer/ingredient_registry.json
├─ Master list of all 600-800 ingredients
├─ Seed data for ingredients table
├─ Version controlled in git
└─ Updated by developers before production deploy

normalizer/ingredient_corrections.json  
├─ Developer's known bad FDC mappings (10-12 items you've found)
├─ Version controlled in git
├─ Used during normalizer processing
└─ Logs/debugs why matches are rejected

---

# ============================================================================
# SUMMARY BY USE CASE
# ============================================================================

PHASE 1 ONLY (Parsing & Normalization):
├─ recipes (metadata)
├─ recipe_ingredients (links recipe to normalized ingredients)
├─ ingredients (canonical ingredient list)
├─ ingredient_aliases (for parser)
├─ ingredient_corrections (dev overrides)
└─ ingredient_fdc_mapping (reference/debugging)

PHASE 2 ADDITIONS (Grocery Lists & Scaling):
├─ ingredient_conversions (cups → grams)
├─ grocery_lists (user's shopping list)
├─ grocery_list_items (aggregated ingredient quantities)
└─ ingredient_substitutions (what can replace what)

PHASE 3 ADDITIONS (Multi-user):
├─ users (user accounts)
├─ meal_plans (user's weekly plan)
├─ meal_plan_items (recipes in that plan)
├─ ingredient_crowdsourced_corrections (public reports)
└─ audit_log (track all changes)

---

# ============================================================================
# BY USER VISIBILITY
# ============================================================================

USER-FACING (Visible in App):
├─ recipes
├─ meal_plans
├─ meal_plan_items
├─ grocery_lists
├─ grocery_list_items
├─ ingredient_substitutions (shown as "suggestions")
└─ ingredient_nutritional_data (shown in recipe details)

INTERNAL (Not visible to users):
├─ ingredients (canonical registry)
├─ ingredient_aliases (used for parsing only)
├─ ingredient_corrections (dev-only)
├─ ingredient_fdc_mapping (debugging)
├─ ingredient_conversions (used for math, not shown)
└─ audit_log (admin only)

SEMI-PUBLIC (For Phase 3 crowdsourcing):
└─ ingredient_crowdsourced_corrections (public sees issues, voting)

---

# ============================================================================
# FOR PHASE 2 GROCERY LIST AGGREGATION
# ============================================================================

Pseudocode workflow:
```
user_selects_recipes([rec_123, rec_456, rec_789])
↓
FOR each recipe:
  GET recipe_ingredients WHERE recipe_id = rec_X
  FOR each item:
    ingredient_id = item.ingredient_id
    qty = item.parsed_amount_data.total_quantity
    unit = item.parsed_amount_data.unit
    agg_type = item.parsed_amount_data.aggregation_type
    
    IF agg_type == "volume":
      convert_to_metric_ml(qty, unit) → add to grocery_list_items.metric_ml_equivalent
    ELSE IF agg_type == "count":
      add to grocery_list_items.total_count_equivalent
    ELSE IF agg_type == "unquantified":
      flag for manual review

AGGREGATE by ingredient_id
STORE in grocery_lists & grocery_list_items

OPTIONAL: Look up substitutions → suggest "You already have ham, need ham? Use prosciutto"
```

---

# ============================================================================
# KEY DESIGN DECISIONS
# ============================================================================

1. ingredient_id (not FDC ID):
   ✓ Your 600-800 ingredients each get unique ID
   ✓ Never changes even if FDC data wrong
   ✓ Can have multiple ingredient versions ("fresh basil" vs "dried basil")

2. recipe_ingredients (join table):
   ✓ Keeps parsed data with the recipe
   ✓ amount_data stored as JSON for flexibility
   ✓ Easy to scale recipes: multiply parsed_amount_data.quantity

3. ingredient_corrections (JSON):
   ✓ Lightweight, version-controlled
   ✓ Easy to communicate "these 10 things are broken"
   ✓ Can migrate to DB table later

4. Aggregation types stored in amount_data:
   ✓ Grocery lists know how to sum: 2 eggs + 3 eggs = 5 eggs
   ✓ vs 1 cup milk + 1/2 cup milk = 1.5 cups milk
   ✓ vs "oil for frying" + "oil for drizzling" = special handling

5. ingredient_conversions (global reference):
   ✓ "1 cup flour = 125g" applies everywhere
   ✓ Can be looked up during scaling
   ✓ Can be user-editable (Phase 3)

---

# ============================================================================
# QUESTIONS FOR YOU
# ============================================================================

1. Should users see ingredient_substitutions? 
   → If I double a recipe and I'm out of ham, show "Use prosciutto instead"?

2. ingredient_crowdsourced_corrections - approval workflow?
   → Only you approve before merging? Or vote-based (5+ agrees = auto-merge)?

3. Do you want per-user ingredient preferences/corrections?
   → Or is everything shared across all users?

4. For Phase 3, should users build their own categorizations?
   → Like "gluten-free alternatives" or "vegan substitutes"?

5. Want to support recipes at different scale levels?
   → Like store "base recipe" (serves 4), then let users make 6, 8, 12 servings?

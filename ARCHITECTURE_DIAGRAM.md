# Architecture & Data Flow Diagram

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          JUST MEAL PLANNER SYSTEM                           │
├─────────────────────────────────────────────────────────────────────────────┤

                              FRONTEND LAYER (Phase 4)
                          ┌─────────────────────────────┐
                          │   Interactive Web UI         │
                          │   (HTML + CSS + JavaScript)  │
                          │                              │
                          │  1. Recipe Input Form        │
                          │  2. Error Display            │
                          │  3. Recipe Confirmation      │
                          │  4. Ingredient Table         │
                          │  5. Yield Scaling            │
                          │  6. Grocery List Generator   │
                          └────────────┬──────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
              POST /scrape      POST /assign-recipe-id   GET /status
                    │                  │                  │
                    ▼                  ▼                  ▼
              ┌─────────────────────────────────────────────────┐
              │        API LAYER - Flask Backend (Phase 1)      │
              │                                                 │
              │  ┌──────────────┐      ┌──────────────┐       │
              │  │   Recipe     │      │   Recipe ID  │       │
              │  │   Scraper    │      │   Assignment │       │
              │  │              │      │              │       │
              │  │ • Validation │      │ • UUID Gen   │       │
              │  │ • URL Check  │      │ • Struct One │       │
              │  │ • Timeout    │      │              │       │
              │  └──────┬───────┘      └──────┬───────┘       │
              │         │                     │               │
              │         ▼                     ▼               │
              │  ┌─────────────────────────────────────┐      │
              │  │   Error Logger (error_logger.py)    │      │
              │  │                                     │      │
              │  │ • Error ID generation               │      │
              │  │ • Daily rotating logs               │      │
              │  │ • In-memory registry (100 errors)   │      │
              │  └─────────────────────────────────────┘      │
              └────────────┬─────────────────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
            ▼                             ▼
      ┌──────────────┐           ┌──────────────────┐
      │  Recipe      │           │  Error Response  │
      │  JSON        │           │  JSON with ID    │
      │  (success)   │           │  (error)         │
      └──────┬───────┘           └──────────────────┘
             │
             ▼
      ┌─────────────────────────────────┐
      │  PROCESSING LAYER (Phase 2 & 3) │
      │                                 │
      │  ┌───────────────────────────┐  │
      │  │  Ingredient Normalizer    │  │
      │  │  (NLP + ingredient_id)    │  │
      │  │                           │  │
      │  │ ✓ Parse ingredients      │  │
      │  │ ✓ Resolve with registry  │  │
      │  │ ✓ Confidence scoring     │  │
      │  │ ✓ Generate ingredient_id │  │
      │  └────────────┬──────────────┘  │
      │               │                 │
      │  ┌────────────▼──────────────┐  │
      │  │  Macro Normalizer         │  │
      │  │  (6-stage pipeline)       │  │
      │  │                           │  │
      │  │ 1. Field Standardization  │  │
      │  │ 2. Value Extraction       │  │
      │  │ 3. Serving Normalization  │  │
      │  │ 4. Validation             │  │
      │  │ 5. Confidence Scoring     │  │
      │  │ 6. Output Construction    │  │
      │  └────────────┬──────────────┘  │
      │               │                 │
      │  ┌────────────▼──────────────┐  │
      │  │  Registry Expansion Tool  │  │
      │  │  (registry_audit.py +     │  │
      │  │   registry_population_    │  │
      │  │   template.py)            │  │
      │  │                           │  │
      │  │ • Audit ingredients       │  │
      │  │ • Generate templates      │  │
      │  │ • Prioritize by frequency │  │
      │  └───────────────────────────┘  │
      └───────┬─────────────────────────┘
              │
        ┌─────┴──────┬──────────────┐
        │             │              │
        ▼             ▼              ▼
   ┌─────────┐  ┌──────────┐  ┌─────────────┐
   │Normalized│  │Normalized│  │Registry     │
   │Ingredients│  │Macros    │  │Templates    │
   │          │  │          │  │            │
   │(JSON)    │  │(JSON)    │  │(JSON)      │
   └─────┬────┘  └────┬─────┘  └─────┬──────┘
        │             │              │
        │ (Manual Curation Needed)   │
        │             │              │
        │             │    (Add FDC  │
        │             │     IDs)     │
        │             │              │
        └─────┬───────┴──────┬───────┘
              │              │
              ▼              ▼
        ┌─────────────────────────────┐
        │   DATA LAYER (SQL)          │
        │                             │
        │ ┌──────────────────────┐   │
        │ │  recipes table       │   │
        │ │  (with recipe_id)    │   │
        │ └──────────────────────┘   │
        │                             │
        │ ┌──────────────────────┐   │
        │ │  ingredients table   │   │
        │ │  (with ingredient_id)│   │
        │ └──────────────────────┘   │
        │                             │
        │ ┌──────────────────────┐   │
        │ │  recipe_macros table │   │
        │ │  (with macro data)   │   │
        │ └──────────────────────┘   │
        │                             │
        │ ┌──────────────────────┐   │
        │ │  registry entry      │   │
        │ │  (ingredient details)│   │
        │ └──────────────────────┘   │
        └─────────────────────────────┘
```

---

## Data Flow: Recipe Scraping to Grocery List

```
┌────────────────────────────────────────────────────────────────────────┐
│                            USER INPUTS URL                              │
│                                   │                                      │
│                                   ▼                                      │
│                    ┌──────────────────────────┐                         │
│                    │  Frontend: Recipe Input  │                         │
│                    │  (section 1)             │                         │
│                    └──────────┬───────────────┘                         │
│                               │                                        │
│                               │ (POST /scrape)                        │
│                               ▼                                        │
│            ┌─────────────────────────────────────┐                    │
│            │  Backend: Scraper                   │                    │
│            │  • Fetch recipe from URL            │                    │
│            │  • Parse with recipe_scrapers       │                    │
│            │  • Validate ingredients & title     │                    │
│            │  • Check for empty data             │                    │
│            └────────────┬────────────────────────┘                    │
│                         │                                             │
│               ┌─────────┴──────────┐                                 │
│               │                    │                                 │
│          (Valid)            (Invalid)                                │
│               │                    │                                 │
│               ▼                    ▼                                 │
│      ┌──────────────────┐  ┌─────────────────────┐                 │
│      │ Return Recipe    │  │ Log Error           │                 │
│      │ JSON + metadata  │  │ Generate Error ID   │                 │
│      │                  │  │ Return Error JSON   │                 │
│      └────────┬─────────┘  └────────────┬────────┘                 │
│              │                         │                           │
│              └────────────┬────────────┘                           │
│                          ▼                                         │
│           ┌────────────────────────────────┐                      │
│           │  Frontend: Error Handling      │                      │
│           │  (section 2)                   │                      │
│           │  Display error_id, message     │                      │
│           │  Show timestamp, source URL    │                      │
│           │  Offer "Retry" button          │                      │
│           └────────┬──────────────────────┘                       │
│                   │                                              │
│         ┌─────────▼────────────┐                                │
│         │                      │                                │
│    (If continues)         (Stop)                               │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────────────┐                                      │
│  │ Recipe Confirmation  │                                      │
│  │ (section 3)          │                                      │
│  │ Show recipe card     │                                      │
│  │ Metadata display     │                                      │
│  │ "Save & Assign ID"   │                                      │
│  └──────┬───────────────┘                                      │
│         │ (POST /assign-recipe-id)                            │
│         ▼                                                      │
│  ┌──────────────────────────┐                                │
│  │ Backend: Recipe ID Gen   │                                │
│  │ • Generate UUID          │                                │
│  │ • Format: rec_[uuid]     │                                │
│  │ • Return recipe + ID     │                                │
│  └──────┬───────────────────┘                                │
│         ▼                                                    │
│  ┌──────────────────────────┐                              │
│  │ Ingredient Normalizer    │                              │
│  │ (NLP + Registry)         │                              │
│  │ • Parse each ingredient  │                              │
│  │ • Resolve with registry  │                              │
│  │ • Generate ingredient_id │                              │
│  │ • Confidence scoring     │                              │
│  └──────┬───────────────────┘                              │
│         ▼                                                  │
│  ┌──────────────────────────────┐                         │
│  │ Normalized Ingredients JSON  │                         │
│  │ [                            │                         │
│  │   {                          │                         │
│  │     "original": "2 cups",    │                         │
│  │     "canonical": "flour",    │                         │
│  │     "ingredient_id": "...",  │                         │
│  │     "amount": 250,           │                         │
│  │     "unit": "g"              │                         │
│  │   }                          │                         │
│  │ ]                            │                         │
│  └──────┬──────────────────────┘                          │
│         ▼                                                 │
│  ┌──────────────────────────┐                            │
│  │ Ingredient Normalization │                            │
│  │ (section 4)              │                            │
│  │ Display in table:        │                            │
│  │ Original | Canonical     │                            │
│  │ Show ingredient_id       │                            │
│  │ Color code resolved      │                            │
│  └──────┬──────────────────┘                             │
│         │                                               │
│         ▼                                              │
│  ┌──────────────────────────┐                         │
│  │ Macro Normalizer         │                         │
│  │ (6-stage pipeline)       │                         │
│  │ • Extract nutrition data │                         │
│  │ • Standardize fields     │                         │
│  │ • Calculate per-serving  │                         │
│  │ • Validate values        │                         │
│  │ • Score confidence       │                         │
│  └──────┬───────────────────┘                         │
│         ▼                                            │
│  ┌──────────────────────────┐                       │
│  │ Normalized Macros JSON   │                       │
│  │ {                        │                       │
│  │   "recipe_id": "...",    │                       │
│  │   "macros": {            │                       │
│  │     "energy_kcal": {     │                       │
│  │       "per_recipe": 2024,│                       │
│  │       "per_serving": 253 │                       │
│  │     },                   │                       │
│  │     ...more macros...    │                       │
│  │   }                      │                       │
│  │ }                        │                       │
│  └──────┬───────────────────┘                       │
│         ▼                                          │
│  ┌───────────────────────────┐                    │
│  │ Yield Scaling             │                    │
│  │ (section 5)               │                    │
│  │ • Select servings 2/4/6/8 │                    │
│  │ • Multiply ingredients    │                    │
│  │ • Show scaled amounts     │                    │
│  │ • Display in table        │                    │
│  └───────┬───────────────────┘                    │
│          ▼                                       │
│  ┌──────────────────────────┐                  │
│  │ Grocery List Generator   │                  │
│  │ (section 6)              │                  │
│  │ • Aggregate ingredients  │                  │
│  │ • Group by category      │                  │
│  │ • Combine quantities     │                  │
│  │ • Show checkboxes        │                  │
│  │ • Export as text file    │                  │
│  └─────────────────────────┘                   │
│                                                │
│  ✓ COMPLETE DATA FLOW                         │
└────────────────────────────────────────────────┘
```

---

## Phase Dependencies

```
PHASE 1: Scraper Hardening
┌─────────────────────────────────┐
│ error_logger.py                 │ ← Foundation
│ OG-scraper/scraper.py           │   (Error handling infrastructure)
│ test_phase1.py                  │
└─────────────┬───────────────────┘
              │
              ▼
PHASE 2: Macro Pipeline
┌─────────────────────────────────┐
│ splitters/macros-splitter.py    │ ← Depends on Phase 1
│ macro-normalizer.py             │   (Structured recipe data)
└─────────────┬───────────────────┘
              │
        ┌─────┴──────┐
        │            │
        ▼            ▼
PHASE 3: Registry        PHASE 4: Frontend
┌──────────────────┐     ┌────────────────────┐
│ registry_audit   │     │ frontend/index.html│
│ registry_pop...  │     │ frontend/style.css │
│ PHASE_3_GUIDE.md │     │ frontend/app.js    │
└──────────────────┘     └─────────┬──────────┘
       │                          │
       │ (Manual curation)        │ (Requires running backend)
       │ (Merge registry)         │
       │                          │
       └──────────┬───────────────┘
                  ▼
         Integration & Testing
         (Database import + End-to-end)
```

---

## Key Data Structures

### Recipe Response (Phase 1)
```json
{
  "error": false,
  "recipe": {
    "title": "Spaghetti Carbonara",
    "servings": 4,
    "prep_time": 10,
    "cook_time": 15,
    "ingredients": [
      {"amount": 400, "unit": "g", "name": "spaghetti"},
      {"amount": 4, "unit": "count", "name": "eggs"}
    ]
  }
}
```

### Ingredient_ID Assignment (Phase 1)
```json
{
  "error": false,
  "recipe_id": "rec_550e8400-e29b-41d4-a716-446655440000",
  "recipe_json_with_id": {
    "id": "rec_550e8400-e29b-41d4-a716-446655440000",
    "title": "Spaghetti Carbonara",
    ...
  }
}
```

### Normalized Ingredient (Phase 3)
```json
{
  "original": "400g spaghetti",
  "canonical": "spaghetti",
  "ingredient_id": "ing_grains_pasta_001",
  "amount": 400,
  "unit": "g",
  "fdc_id": 167996,
  "confidence": "high",
  "source": "ingredient_registry_match"
}
```

### Normalized Macro (Phase 2)
```json
{
  "recipe_id": "rec_550e8400-e29b-41d4-a716-446655440000",
  "energy_kcal": {
    "per_recipe": 2400,
    "per_serving": 600,
    "confidence": "high"
  },
  "protein_g": {
    "per_recipe": 96,
    "per_serving": 24,
    "confidence": "high"
  }
}
```

### Ingredient Registry Entry (Phase 3)
```json
{
  "ingredient_id": "ing_grains_pasta_001",
  "canonical_name": "Spaghetti",
  "category": "Grains & Pasta",
  "type": "pasta_dried",
  "aliases": ["spaghetti", "spaghetti pasta"],
  "fdc_reference": {
    "fdc_ids": [167996],
    "fdc_reason": "Primary source: USDA FDC database"
  },
  "conversions": {
    "cup": 140,
    "gram": 1
  },
  "density_g_per_ml": null
}
```

---

## Error Flow Diagram

```
┌──────────────┐
│ Recipe URL   │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│ Validation Check         │
└──────┬───┬───┬───┬───────┘
       │   │   │   │
   ┌───┴─┐ │   │   │
   │     │ │   │   │
Invalid  │ │   │   Valid
   │     │ │   │     │
   │     │ │   │     ▼
   │     │ │   │ ┌─────────┐
   │     │ │   │ │ Success │
   │   ┌─┴─┴─┐ │ └─────────┘
   │   │     │ │
   │   │Validate: Empty Ingredients, Missing Title, etc.
   │   │
   ▼   ▼
ERROR BRANCH
   │
   ├─ validation_error (URL, format)
   ├─ empty_ingredients (ingredients array empty)
   ├─ scraper_error (recipe_scrapers exception)
   ├─ timeout (30s socket timeout)
   └─ connection_error (network failure)
        │
        ▼
┌─────────────────────────────┐
│ error_logger.log_error()    │
│ • Generate error_id         │
│ • Save to daily log file    │
│ • Add to memory registry    │
│ • Return structured error   │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│ Return Error Response to Frontend   │
│ {                                   │
│   "error": true,                    │
│   "error_id": "err_..._...",        │
│   "error_type": "...",              │
│   "error_message": "...",           │
│   "timestamp": "...",               │
│   "source_url": "..."               │
│ }                                   │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────┐
│ Frontend    │
│ Error       │
│ Display     │
│ (Section 2) │
└─────────────┘
```

---

## Summary: How Everything Connects

1. **User enters recipe URL in frontend**
   - Frontend validates URL format
   - Calls POST /scrape endpoint

2. **Scraper processes recipe**
   - Fetches HTML/JSON from URL
   - Parses with recipe_scrapers library
   - Validates has ingredients + title
   - If error: Logs to error_logger, returns error response
   - If valid: Returns recipe JSON

3. **User confirms recipe & assigns ID**
   - Frontend shows recipe card (Section 3)
   - User clicks "Save & Assign ID"
   - Calls POST /assign-recipe-id
   - Backend generates UUID (rec_[uuid])
   - Frontend stores in appState

4. **Ingredients are normalized**
   - NLP parser identifies each ingredient
   - Registry lookup finds ingredient_id
   - Confidence score added
   - Frontend displays in table (Section 4)

5. **Macros are normalized**
   - 6-stage pipeline processes nutrients
   - Per-recipe and per-serving calculated
   - Confidence score added
   - Available for yield scaling

6. **User adjusts yield**
   - Frontend: Select servings (2/4/6/8)
   - JavaScript multiplies ingredient amounts
   - Display updated in table (Section 5)

7. **Grocery list generated**
   - Aggregate ingredients from all recipes
   - Group by category
   - Combine duplicate items
   - Export to text file (Section 6)

8. **Data persisted to database** (for future)
   - Recipes table (with recipe_id)
   - Ingredients table (with ingredient_id)
   - Recipe_macros table (with nutrition)
   - Registry entries (ingredient catalogs)

---

**This architecture enables:** Error tracking, ingredient normalization, macro processing, registry expansion, and interactive UI all working together seamlessly.

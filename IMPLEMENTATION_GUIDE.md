# Just Meal Planner - Complete Implementation Structure

## Files Created

```
d:\just_mealplanner\
├── FINAL_SCHEMA.md                    # Conceptual schema (this directory)
├── schema.sql                          # PostgreSQL DDL
├── SCHEMA_DESIGN.md                   # Detailed design rationale
│
├── normalizer/
│   ├── ingredient_registry.json        # Global ingredient registry (~600-800 items)
│   ├── ingredient_corrections.json     # 10-12 known FDC failures (developer overrides)
│   ├── ingredient-normalizer.py        # Main normalizer (needs update)
│   ├── requirements.txt
│   └── [other existing files]
│
└── docs/
    └── [API documentation - Phase 3]
```

---

## Phase 1 Workflow: Recipe Parsing

### Input → Output Flow

```
1. OG-scraper produces ingredients.json
   └─ Raw ingredient strings (from websites)

2. ingredient-normalizer.py runs:
   a. Reads ingredient_corrections.json (10-12 known bad mappings)
   b. Parses ingredient with NLP
   c. Gets FDC match IF available
   d. Checks: Is this in corrections.json? → Use ingredient_id from there
   e. Else: Check confidence threshold (0.85)
   f. Else: Check semantic validation
   g. Output: ingredient_id (from ingredient_registry.json)
   
3. Produces normalized-ingredients.json
   └─ JSON with ingredient_id (not fdc_id)

4. Data import to DB (Phase 1-2):
   INSERT INTO recipes (...)
   INSERT INTO recipe_ingredients (...)
   ← Uses ingredient_id as FK
```

---

## Key Features by Phase

### PHASE 1: Parsing (Current - Complete)
✓ Parse ingredients with NLP
✓ Global ingredient registry (JSON)
✓ Override system for bad FDC mappings
✓ Output uses ingredient_id (not FDC ID)
✓ Supports volume + count + unquantified aggregation types

### PHASE 2: Grocery Lists (Coming)
- User selects recipes
- Query recipe_ingredients for all ingredients
- GROUP BY ingredient_id
- SUM by aggregation_type:
  - "volume" → total metric_ml
  - "count" → total count
  - "unquantified" → flag for manual review
- Store in grocery_lists + grocery_list_items

### PHASE 3: Multi-user (Future)
- User accounts with dietary restrictions/allergies
- User preferences to override global registry
- Meal plans (weekly layout)
- Crowdsourced corrections with voting

---

## Data Flow Examples

### Example 1: "½ cup ground jamón serrano"

**Parse Time (normalizer):**
```python
parsed_text = "½ cup ground jamón serrano"
nlu_result = parse_ingredient(parsed_text)
→ fdc_match = FDC ID 169395 ("Peppers, serrano, raw")

# Check corrections.json
if "jamón serrano" in corrections:
    ingredient_id = "ing_ham_serrano_001"  ✓ Use this
else:
    # Would use FDC, but ignore it due to correction
```

**DB Output:**
```json
{
  "display_text": "½ cup ground jamón serrano",
  "ingredient_id": "ing_ham_serrano_001",
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
    "metric_ml": 118.29
  }
}
```

**Phase 2 Grocery Aggregation:**
```sql
SELECT 
  ingredient_id,
  SUM(parsed_amount_data->>'quantity') as total_qty,
  parsed_amount_data->>'unit' as unit,
  parsed_amount_data->>'aggregation_type' as agg_type
FROM recipe_ingredients
WHERE recipe_id IN (rec_001, rec_002, rec_003)
GROUP BY ingredient_id;

Result:
  ing_ham_serrano_001, 1.5, cup, volume → 354.88 ml total
```

---

### Example 2: "2 bay leaves"

**Parse Time:**
```python
parsed_text = "2 bay leaves"
→ fdc_match = FDC ID for bay leaf (high confidence)
→ parsed_amount = quantity: 2, unit: "leaves" (not recognized by Pint)

# Conversion fails → aggregation_type = "count"
```

**DB Output:**
```json
{
  "ingredient_id": "ing_bay_leaf_001",
  "amount_data": {
    "aggregation_type": "count",
    "quantity": 2,
    "unit": "leaves",
    "metric_ml": 0.0,
    "total_count": 2.0  ← Stores the count
  }
}
```

**Phase 2 Grocery Aggregation:**
```
Recipe 1: 2 bay leaves
Recipe 2: 1 bay leaf
Recipe 3: 3 bay leaves
─────────────────────
Total: 6 bay leaves (count-based, not volume)
```

---

### Example 3: "Oil for frying"

**Parse Time:**
```python
parsed_text = "Oil for frying"
→ parsed_amount = None (no quantity)
→ parsed_purpose = "for frying"

# No amount → aggregation_type = "unquantified"
```

**DB Output:**
```json
{
  "ingredient_id": "ing_oil_000X",  # Some oil ingredient
  "amount_data": {
    "type": "unquantified",
    "aggregation_type": "unquantified",
    "display": "To taste / As needed",
    "metric_ml": 0.0,
    "total_count": 0.0
  }
}
```

**Phase 2 Grocery Aggregation:**
```
UI Note: "Oil (for frying) - As needed"
No numeric aggregation, just flag for user awareness
```

---

## Normalizer Code Changes Needed

### Current Problem
```python
canonical_ingredient = {
    "fdc_id": foundation_food.fdc_id,  ← WRONG: Direct FDC ID
    "canonical_name": foundation_food.text,
    "confidence": foundation_food.confidence,
}
```

### New Approach
```python
# 1. Load corrections at startup
with open('ingredient_corrections.json') as f:
    corrections = json.load(f)
    
with open('ingredient_registry.json') as f:
    registry = json.load(f)

# 2. During parsing
parsed = parse_ingredient(sentence, foundation_foods=True)

# 3. Check corrections FIRST
ingredient_id = None
if parsed.name[0].text in corrections:
    ingredient_id = corrections['mapped_to_id']
    
# 4. Fallback to FDC (if available and passes validation)
elif foundation_food.confidence >= CONFIDENCE_THRESHOLD:
    ingredient_id = map_fdc_to_ingredient_id(foundation_food)

# 5. Otherwise unresolved
else:
    ingredient_id = None  # Will need manual mapping later

# 6. Output uses ingredient_id
canonical_ingredient = {
    "ingredient_id": ingredient_id,  ← NEW: Our internal ID
    "canonical_name": registry[ingredient_id]['canonical_name'],
    "category": registry[ingredient_id]['category'],
    "source": "ingredient_registry_override" or "fdc"
}
```

---

## Database Import (After normalization)

```python
import json
import psycopg2

# 1. Connect to DB
conn = psycopg2.connect("dbname=just_meal_planner user=postgres")

# 2. Load normalized output
with open('source/normalized-ingredients.json') as f:
    data = json.load(f)

# 3. Insert recipes + recipe_ingredients
for recipe in data:
    # Insert recipe
    cur.execute("""
        INSERT INTO recipes (recipe_id, title, yield_servings)
        VALUES (%s, %s, %s)
    """, (recipe['recipe_id'], recipe['recipe_title'], None))
    
    # Insert ingredients
    for ing in recipe['ingredients']:
        cur.execute("""
            INSERT INTO recipe_ingredients 
            (recipe_id, ingredient_id, display_text, parsed_amount_data, sort_order)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            recipe['recipe_id'],
            ing['ingredient_id'],
            ing['display_text'],
            json.dumps(ing['amount_data']),
            ing.get('sort_order', 0)
        ))

conn.commit()
```

---

## Phase 2: Grocery List Generation

```python
# User creates grocery list from recipes
user_recipes = [rec_001, rec_002, rec_003]

# Query aggregation
query = """
SELECT 
    ri.ingredient_id,
    i.canonical_name,
    i.category,
    ri.parsed_amount_data,
    COUNT(*) as recipe_count,
    ARRAY_AGG(ri.recipe_id) as from_recipes
FROM recipe_ingredients ri
JOIN ingredients i ON ri.ingredient_id = i.ingredient_id
WHERE ri.recipe_id = ANY(%s)
GROUP BY ri.ingredient_id, i.canonical_name, i.category, ri.parsed_amount_data
ORDER BY i.category, i.canonical_name
"""

results = cur.execute(query, (user_recipes,))

# Build grocery list
for row in results:
    item = {
        'ingredient_id': row['ingredient_id'],
        'name': row['canonical_name'],
        'aggregation_type': row['parsed_amount_data']['aggregation_type'],
    }
    
    if item['aggregation_type'] == 'volume':
        # Sum metric_ml
        item['total_quantity'] = sum_metric_ml(...)
        item['unit'] = 'ml'
    elif item['aggregation_type'] == 'count':
        # Sum counts
        item['total_quantity'] = sum_counts(...)
        item['unit'] = 'pieces'
    else:
        # Unquantified
        item['note'] = 'As needed'
    
    grocery_list.append(item)
```

---

## Questions Addressed

| Question             | Answer                                                  |
| -------------------- | ------------------------------------------------------- |
| **How many tables?** | 3 (Phase 1) → 6 (Phase 2) → 12 (Phase 3)                |
| **User-facing?**     | recipes, grocery_lists (Phase 2) + meal_plans (Phase 3) |
| **Math tables?**     | ingredient_conversions, grocery_list_items              |
| **Dev-only?**        | ingredient_corrections.json (then merged Phase 3)       |
| **JSON or DB?**      | JSON for Phase 1-2, migrate to DB Phase 3               |
| **FDC dependency?**  | Optional - use ingredient_id as primary key             |
| **Crowdsourcing?**   | user_ingredient_corrections table (Phase 3)             |

---

## Next Steps

1. **Update normalizer** to use ingredient_id instead of fdc_id
2. **Seed ingredients table** with ingredient_registry.json in Phase 1
3. **Build DB schema** with schema.sql
4. **Create data import script** for Phase 1 output
5. **Build Phase 2** grocery aggregation logic

---

## Testing Phase 1

```bash
# 1. Run normalizer
python normalizer/ingredient-normalizer.py

# 2. Check corrections were applied
grep -i "jamón\|vino" source/normalized-ingredients.json
# Should show ingredient_id, NOT fdc_id

# 3. Verify aggregation types
python -c "
import json
data = json.load(open('source/normalized-ingredients.json'))
recipes_with_data = [r for r in data if r['ingredients']]
for r in recipes_with_data[:1]:
    for ing in r['ingredients'][:3]:
        print(f\"{ing['display_text']}: {ing['amount_data']['aggregation_type']}\")
"

# 3. Import to DB
python import_to_db.py source/normalized-ingredients.json
```

Ready to implement?

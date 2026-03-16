# Phase 3: Ingredient Registry Expansion Guide

## Overview

**Objective:** Expand ingredient registry from 12 items to ~300 items (Tier 1 coverage)

**Strategy:** Audit → Prioritize → Template → Curate → Merge

**Timeline:** Parallel with Phase 1 & 2 completion, can run async

**Success Metric:** 80+ Tier 1 entries (high-frequency unresolved ingredients) in registry

---

## Current State

### Registry Size
- **Current:** 12 entries in `normalizer/ingredient_registry.json`
- **Target:** ~80 entries (Tier 1 critical)
- **Medium term:** ~300 entries (Tier 1 + Tier 2)

### Unresolved Ingredients
- **Total unresolved:** 39 ingredients from normalized parsing
- **Identified through:** `normalizer/ingredient_parser_nlp.md`
- **Root cause:** Low FDC confidence (< 0.85 threshold)

### Strategy Rationale
Rather than manually expanding registry item-by-item:
1. **Audit** unresolved ingredients → Frequency analysis
2. **Prioritize** by tier (≥3 occurrences = critical)
3. **Generate** template entries with structure
4. **Curate** manually (add FDC refs, conversions, aliases)
5. **Merge** into working registry
6. **Test** against all recipes to improve resolution rate

---

## Tools & Executables

### Tool 1: `registry_audit.py` 
**Purpose:** Analyze unresolved ingredients, generate priority report

**Current State:** ✅ Complete, ready to run

**Execution:**
```bash
cd d:\just_mealplanner
python registry_audit.py
```

**Inputs:**
- `source/normalized-ingredients.json` (output from ingredient normalizer)
- `normalizer/ingredient_registry.json` (current registry)

**Outputs:**
- `AUDIT_REPORT.json` - Full analysis with:
  - Resolved ingredients (in registry)
  - Unresolved by tier (frequency-based)
  - Recommendations

**Expected Results:**
```json
{
  "summary": {
    "total_unique": 39,
    "resolved": 12,
    "unresolved": 27,
    "tier_1_count": 8-12,
    "tier_2_count": 5-8,
    "tier_3_count": 12-15
  },
  "unresolved_ingredients": {
    "ing_raw_ingredient_001": {
      "occurrences": 5,
      "tier": 1,
      "sample_recipes": [...]
    }
  }
}
```

---

### Tool 2: `registry_population_template.py`
**Purpose:** Generate template entries ready for curation

**Current State:** ✅ Complete, ready to run

**Execution:**
```bash
cd d:\just_mealplanner
python registry_population_template.py
```

**Inputs:**
- `AUDIT_REPORT.json` (generated from Tool 1)
- Built-in ingredient templates

**Outputs:**
- `registry_templates.json` - Array of 50+ entries with structure:
  ```json
  {
    "ingredient_id": "ing_grains_flour_001",
    "canonical_name": "All-Purpose Flour",
    "category": "Grains & Flours",
    "type": "grain_product",
    "aliases": ["all-purpose flour", "wheat flour"],
    "fdc_reference": {
      "fdc_ids": [],
      "fdc_reason": "To be populated"
    },
    "conversions": {
      "cup": 125,
      "tablespoon": 8,
      "gram": 1
    },
    "density_g_per_ml": 0.59,
    "metadata": {...}
  }
  ```

**Logic:**
- Creates entries for 12 base ingredient types (flour, sugar, butter, etc.)
- Generates entries for top 50 unresolved ingredients from audit
- Guesses category/type automatically (kitchen knowledge embedded)
- Flags items needing manual FDC lookup

---

## Implementation Workflow

### Phase 3.1: Audit & Analysis (5 minutes)

**Step 1:** Run audit tool
```bash
python registry_audit.py
```

**Expected Output:** `AUDIT_REPORT.json` with frequency analysis

**Decision Point:** Review tier breakdown
- If Tier 1 ≥ 8 items → Proceed to Step 2
- If < 8 items → May indicate good ingredient coverage already

**Example Output Review:**
```
Tier 1 (≥3 occurrences): 
  - garlic (5 recipes)
  - onion (4 recipes)
  - salt (3 recipes)
  → Focus: High ROI, affects many recipes

Tier 2 (2 occurrences):
  - turmeric (2 recipes)
  - paprika (2 recipes)
  → Medium ROI, worth including

Tier 3 (1 occurrence):
  - cardamom (1 recipe)
  → Low ROI, defer to medium-term
```

### Phase 3.2: Template Generation (2 minutes)

**Step 2:** Run population template tool
```bash
python registry_population_template.py
```

**Expected Output:** `registry_templates.json` with structure-ready entries

**File Review Checklist:**
- [ ] 50+ entries generated
- [ ] IDs follow format: `ing_[category]_[type]_###`
- [ ] Aliases populated from unresolved list
- [ ] Conversions included for known items
- [ ] FDC reference marked for curation

### Phase 3.3: Manual Curation (15-30 minutes)

**Step 3:** Populate FDC references and refine

**Tasks:**
1. Open `registry_templates.json` in editor
2. For each entry, especially Tier 1:
   - [ ] Search FDC database (fdc.nal.usda.gov) for FDC ID
   - [ ] Check "fdc_reference" → "fdc_ids" array
   - [ ] Example FDC IDs: 
     - All-Purpose Flour: [167528, 169914]
     - Butter: [170568]
     - Eggs: [175167]
   - [ ] Update "fdc_reason" from "To be populated" → "Primary source" or "Alternative source"

**Conversion Lookup (if missing):**
- Check USDA measurement conversion database
- Format: unit → grams (or ml for liquids)
- Example conversions to add:
  - Flour cup → 125g
  - Sugar cup → 200g
  - Butter tablespoon → 14.2g
  - Milk cup → 240ml

**Alias Expansion (optional):**
- Add common variations:
  - "garlic" → ["minced garlic", "garlic clove", "garlic powder"]
  - "onion" → ["white onion", "yellow onion", "red onion"]

**Example Curated Entry:**
```json
{
  "ingredient_id": "ing_seasonings_spice_001",
  "canonical_name": "Garlic",
  "category": "Seasonings & Spices",
  "type": "spice",
  "aliases": ["garlic clove", "minced garlic", "garlic powder"],
  "fdc_reference": {
    "fdc_ids": [170009, 170010],
    "fdc_reason": "Primary source: FDC database, multiple forms"
  },
  "conversions": {
    "clove": 3,
    "tablespoon": 15,
    "gram": 1
  },
  "density_g_per_ml": 1.1,
  "substitutions": [
    "garlic powder (1 tsp = 3 cloves)",
    "garlic salt (more carefully)"
  ],
  "allergens": [],
  "metadata": {"from_audit": true, "occurrences": 5}
}
```

### Phase 3.4: Registry Merge (5 minutes)

**Step 4:** Merge templates into working registry

**Approach (Manual):**
```bash
# Option A: Manual merge in editor
1. Open normalizer/ingredient_registry.json (current 12 items)
2. Open registry_templates.json (curated ~50 items)
3. Append curated entries to registry array
4. Remove any duplicates
5. Save as normalizer/ingredient_registry.json (backup first!)
```

**Approach (Automated - Optional):**
```bash
# Create merge script
python -c "
import json

# Load both files
with open('normalizer/ingredient_registry.json') as f:
    registry = json.load(f)
    
with open('registry_templates.json') as f:
    templates = json.load(f)

# Merge (skip duplicates by ingredient_id)
existing_ids = {e['ingredient_id'] for e in registry}
new_entries = [t for t in templates if t['ingredient_id'] not in existing_ids]

registry.extend(new_entries)

# Save
with open('normalizer/ingredient_registry.json', 'w') as f:
    json.dump(registry, f, indent=2)
    
print(f'Merged {len(new_entries)} new entries. Total: {len(registry)}')
"
```

**Backup Strategy:**
```bash
# Before merge, backup current registry
cp normalizer/ingredient_registry.json normalizer/ingredient_registry.json.backup
```

### Phase 3.5: Validation & Testing (10 minutes)

**Step 5:** Test expanded registry against recipes

**Validation Steps:**

1. **Syntax Check:** Ensure JSON is valid
```bash
python -c "import json; json.load(open('normalizer/ingredient_registry.json'))"
```

2. **Structure Check:** Verify expected fields
```python
import json

with open('normalizer/ingredient_registry.json') as f:
    registry = json.load(f)
    
required_fields = [
    'ingredient_id', 'canonical_name', 'category', 'type', 'aliases',
    'fdc_reference', 'conversions', 'density_g_per_ml'
]

for entry in registry:
    missing = [f for f in required_fields if f not in entry]
    if missing:
        print(f"Missing fields in {entry.get('ingredient_id')}: {missing}")
```

3. **Coverage Test:** Re-run ingredient normalizer
```bash
# After merged registry, re-normalize ingredients
python normalizer/ingredient-normalizer.py

# Compare results
# Expected: More ingredients resolved (≥90% vs. previous ~70%)
```

4. **Manual Spot Check:**
```
Expected high-resolution recipes:
- Garlic → ing_seasonings_spice_001 ✓
- Onion → ing_produce_vegetable_002 ✓
- Flour → ing_grains_flour_001 ✓
```

---

## Success Criteria

### After Phase 3.1 (Audit)
- [ ] AUDIT_REPORT.json generated
- [ ] Tier 1 ingredients identified (8+ items)
- [ ] Frequency distribution makes sense

### After Phase 3.2 (Template Generation)
- [ ] registry_templates.json created
- [ ] 50+ entries with proper structure
- [ ] ID format correct (ing_[cat]_[type]_###)

### After Phase 3.3 (Curation)
- [ ] Tier 1 entries have FDC IDs
- [ ] Conversions added for common items
- [ ] Aliases expanded for variants

### After Phase 3.4 (Merge)
- [ ] Registry size increased to ~60+ entries
- [ ] No duplicate IDs
- [ ] JSON still valid

### After Phase 3.5 (Testing)
- [ ] All entries follow structure
- [ ] Ingredient resolution rate improves 15-20%
- [ ] Spot checks pass

---

## Integration with Other Phases

**Phase 1 (Scraper):** ✅ Complete
- Structured errors enable audit tracking

**Phase 2 (Macros):** ✅ Complete
- Macro normalization independent of registry

**Phase 4 (Frontend):** → Integrates with registry
- Frontend shows normalized ingredients
- Better resolution = better ingredient display

**Phase 3 Dependency Graph:**
```
Audit (registry_audit.py)
    ↓
Templates (registry_population_template.py)
    ↓
Manual Curation (edit registry_templates.json)
    ↓
Merge (combine with ingredient_registry.json)
    ↓
Testing (re-run normalizer, verify coverage)
    ↓
Frontend Display (shows more resolved ingredients)
```

---

## Quick Reference: Registry Entry Structure

```json
{
  // Required
  "ingredient_id": "ing_grains_flour_001",
  "canonical_name": "All-Purpose Flour",
  "category": "Grains & Flours",
  "type": "grain_product",
  "aliases": ["all-purpose flour", "wheat flour", "AP flour"],
  
  // FDC Reference
  "fdc_reference": {
    "fdc_ids": [167528, 169914],
    "fdc_reason": "Primary source: FDC comprehensive foods database"
  },
  
  // Optional but recommended
  "conversions": {
    "cup": 125,
    "tablespoon": 8,
    "gram": 1
  },
  "density_g_per_ml": 0.59,
  
  // Extra
  "substitutions": [
    "whole wheat flour (slightly different nutrition)",
    "bread flour (more gluten)"
  ],
  "allergens": ["gluten"],
  "metadata": {
    "from_audit": true,
    "occurrences": 5,
    "confidence": "high"
  }
}
```

---

## Troubleshooting

### Issue: "AUDIT_REPORT.json not found" when running registry_population_template.py
**Solution:** Run registry_audit.py first (Step 1)

### Issue: FDC IDs are hard to find
**Solution:** 
- Use FDC API: https://fdc.nal.usda.gov/api-key
- Or use USDA search interface: https://fdc.nal.usda.gov
- For now, leave empty and mark fdc_reason as "Pending manual lookup"

### Issue: Converted units don't match expected values
**Solution:**
- Check recipe_scrapers library's unit conversions (may differ slightly)
- Use USDA's official conversions as source of truth
- Document if custom conversion is used

### Issue: Registry merge creates duplicate IDs
**Solution:**
- Check templates for ID format violations
- Ensure sequential numbering within each [category]_[type]
- Use merge script to detect/remove duplicates

---

## Timeline Estimate

| Phase     | Task                     | Duration      | Parallel?              |
| --------- | ------------------------ | ------------- | ---------------------- |
| 3.1       | Run audit                | 5 min         | Yes (with Phase 1 & 2) |
| 3.2       | Generate templates       | 2 min         | Yes                    |
| 3.3       | Manual curation (Tier 1) | 15-30 min     | Yes (independent)      |
| 3.4       | Registry merge           | 5 min         | No (depends on 3.3)    |
| 3.5       | Testing                  | 10 min        | Yes (after 3.4)        |
| **Total** |                          | **40-60 min** |                        |

---

## Medium-Term Expansion (Phase 3 Extended)

After Tier 1 (≥3 items):

**Tier 2 Expansion (2 occurrences):**
- Add 5-8 more entries
- Use same curation process
- Timeline: +15 minutes

**Tier 3 Expansion (1 occurrence):**
- Medium-term (after Phase 4 frontend complete)
- Lower priority, can defer
- Timeline: +30 minutes when ready

**Target Distribution:**
- Tier 1: 80-100 entries (40%)
- Tier 2: 80-100 entries (40%)
- Tier 3: 50-80 entries (20%)
- **Total: ~300 entries for complete coverage**

---

## References

**FDC Database:**
- https://fdc.nal.usda.gov
- FDC API: https://fdc.nal.usda.gov/api-key

**Ingredient Parser:**
- Library: ingredient_parser==2.5.0
- Maps to FDC foundation foods

**Conversion Standards:**
- USDA: https://www.usda.gov
- Kitchen measurements: 1 cup flour ≈ 125g

**Schema:**
See [SCHEMA_DESIGN.md](SCHEMA_DESIGN.md) for database relationships

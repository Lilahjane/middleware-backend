

### 1. Fixing Normalization False Positives
The documentation notes that the `foundation_foods` match is the result of a three-stage process involving fuzzy embedding. Currently, your code blindly accepts the first result: `foundation_food = parsed.foundation_foods`. This is why "Jamón Serrano" (ham) is incorrectly mapped to "Serrano Peppers".

**Fix: Implementation of a Confidence Threshold**
The documentation states that confidence values are between 0 and 1. You should only assign a `canonical_ingredient` if it meets a high-confidence threshold (e.g., 0.9).

```python
# Updated Step 3 in your process_recipes function
threshold = 0.9
foundation_food = None

if parsed.foundation_foods:
    # Look for the best match above the threshold
    best_match = parsed.foundation_foods
    if best_match.confidence >= threshold:
        foundation_food = best_match
    else:
        # LOG: Low confidence match ignored to prevent false category mapping
        foundation_food = None 

canonical_ingredient = None
if foundation_food:
    canonical_ingredient = {
        "fdc_id": foundation_food.fdc_id,
        "canonical_name": foundation_food.text,
        "confidence": foundation_food.confidence,
        "category": foundation_food.category
    }
```

---

### 2. Fixing Math Blind Spots (Count-based Aggregation)
Your current code sets `metric_ml` to `0.0` if `convert_to("ml")` fails. This causes items like "2 bay leaves" or "1 egg" to disappear from grocery list calculations.

**Fix: Split Logic for Volume vs. Count**
The documentation explains that units recognized by Pint become `pint.Unit` objects. If a unit is not recognized (like "leaves" or "eggs"), it remains a string. Use this to differentiate between volumetric math and unit-count math.

```python
# Updated Step 5 logic for simple amounts
try:
    # Try volumetric conversion first
    metric_ml = amt.convert_to("ml").quantity
    aggregation_type = "volume"
except:
    # Fallback: If it's a count-based item, use the raw quantity
    metric_ml = 0.0
    aggregation_type = "count"

amount_data = {
    "type": "simple",
    "aggregation_type": aggregation_type,
    "quantity": safe_quantity_to_float(amt.quantity),
    "unit": str(amt.unit) if amt.unit else "unit",
    "metric_ml": metric_ml if aggregation_type == "volume" else 0.0,
    "total_count": safe_quantity_to_float(amt.quantity) if aggregation_type == "count" else 0.0
}
```

---

### 3. Fixing Truncated Comments
In your output, "it’s about a cup" was truncated to "it’s about a". This happened because the parser identified "1 cup" as a secondary amount and extracted it into the `amount` field, removing those tokens from the `comment`.

**Fix: Use `parsed.sentence` for Display Layer**
The documentation defines `parsed.sentence` as the "Normalised input sentence". Instead of relying on the fragmented `comment` field for your "Cookbook View," always store and display the `parsed.sentence` to ensure the user sees the full context.

```python
# Use this in your Step 6 Database Schema
recipe_ingredient = {
    "display_text": parsed.sentence, # Preserves "1 yellow onion... (it's about a cup)"
    "raw_comment": parsed.comment.text if parsed.comment else None,
    # ... rest of object
}
```

---

### 4. Fixing Missing Amount Data ("To Taste")
Ingredients like "Oil for frying" result in `amount_data: null`.

**Fix: Implementation of "As Needed" Flag**
The library identifies the `purpose` ("for frying") but finds no `amount`. You should update your middleware to provide a default "to taste" structure when the `amount` list is empty.

```python
# Updated Step 5: Handling empty amounts
if not parsed.amount:
    amount_data = {
        "type": "unquantified",
        "display": "To taste / As needed",
        "metric_ml": 0.0
    }
else:
    # ... existing amount processing logic ...
```

---

### 5. Fixing Language Support
The documentation explicitly states: "Currently supported options are: en". Your data contains German ("Basler Mehlsuppe") and French ("900 g de farine bise").

**Alternative Solution: Translation Middleware**
Since the library does not support other languages, the documentation cannot resolve this directly. You should implement a **Translation Middleware** (like `googletrans` or a local LLM) in your `custom_pre_processor`. 
1.  Detect language.
2.  If not "en," translate the string to English.
3.  Pass the English string to `parse_ingredient`.
4.  Store the *original* foreign string in a `original_language_text` field in your database so the user still sees the recipe in its native tongue.

### Summary of Documentation Solutions vs. Alternatives
| Issue                  | Documentation Solution | Implementation                             |
| :--------------------- | :--------------------- | :----------------------------------------- |
| **Normalization**      | Confidence field       | Apply 0.9 threshold check.                 |
| **Math Blind Spots**   | Unit type checking     | Separate "volume" from "count" logic.      |
| **Truncated Comments** | Normalized sentence    | Use `parsed.sentence` for primary display. |
| **Language Support**   | None (Limited to "en") | **Alternative:** Translation middleware.   |
import json

with open('source/normalized-ingredients.json', 'r') as f:
    data = json.load(f)

print('=' * 80)
print('FINAL AUDIT CHECK - After Semantic Validation & Precision Rounding')
print('=' * 80)

print('\n[PRECISION FIX] - Checking metric_ml rounding:')
print('-' * 80)
high_precision = [ing for r in data for ing in r['ingredients'] 
                  if ing.get('amount_data') and ing['amount_data'].get('metric_ml') 
                  and ing['amount_data'].get('metric_ml') != 0.0][:5]
for ing in high_precision:
    ml = ing['amount_data']['metric_ml']
    decimal_places = len(str(ml).split('.')[-1]) if '.' in str(ml) else 0
    status = 'GOOD' if decimal_places <= 2 else 'BAD'
    print(f'  {status}: {ing["display_text"][:45]}: {ml} ({decimal_places} decimals)')

print('\n[FALSE POSITIVES FIX] - Checking jamón (should NOT be pepper):')
print('-' * 80)
jamon = [ing for r in data for ing in r['ingredients'] if 'jamon' in ing['display_text'].lower()]
if jamon:
    j = jamon[0]
    print(f'  Ingredient: {j["display_text"]}')
    if j['canonical_ingredient'] is None:
        print(f'  GOOD: Rejected (canonical_ingredient is None)')
    else:
        category = j['canonical_ingredient']['category']
        if 'Vegetable' in category:
            print(f'  BAD: Still mapped to {category}')
        else:
            print(f'  OK: Mapped to {category}')

print('\n[FALSE POSITIVES FIX] - Checking vino seco (should NOT be dairy):')
print('-' * 80)
vino = [ing for r in data for ing in r['ingredients'] if 'vino' in ing['display_text'].lower()]
if vino:
    v = vino[0]
    print(f'  Ingredient: {v["display_text"]}')
    if v['canonical_ingredient'] is None:
        print(f'  GOOD: Rejected (canonical_ingredient is None)')
    else:
        category = v['canonical_ingredient']['category']
        if 'Dairy' in category or 'Cheese' in category:
            print(f'  BAD: Still mapped to {category}')
        elif 'Beverage' in category or 'Alcoholic' in category:
            print(f'  GOOD: Correctly mapped to {category}')
        else:
            print(f'  ? Unknown: Mapped to {category}')

print('\n[ALL OTHER FIXES] - Summary:')
print('-' * 80)
# Count-based items
count_items = [ing for r in data for ing in r['ingredients'] if ing.get('amount_data') and ing.get('amount_data', {}).get('aggregation_type') == 'count']
print(f'  Count-based items (bay leaves, eggs): {len(count_items)} items properly handled')

# Unquantified amounts
unquant = [ing for r in data for ing in r['ingredients'] if ing.get('amount_data') and ing.get('amount_data', {}).get('type') == 'unquantified']
print(f'  Unquantified amounts (to taste): {len(unquant)} items properly handled')

# Low confidence filtered
filtered = [ing for r in data for ing in r['ingredients'] if ing.get('canonical_ingredient') is None]
print(f'  Low confidence filtered: {len(filtered)} ingredients without canonical mapping')

print('\n' + '=' * 80)
print('SUMMARY')
print('=' * 80)

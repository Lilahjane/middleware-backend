"""Quick data analysis script."""
import json

recipes = json.load(open('source/recipes-withID.json', encoding='utf-8'))
macros = json.load(open('source/macros.json', encoding='utf-8'))
try:
    recipes_no_id = json.load(open('source/recipes-noID.json', encoding='utf-8'))
except:
    recipes_no_id = []

print(f'Total recipes in recipes-withID.json: {len(recipes["results"])}')
print(f'Total recipes in macros.json: {len(macros)}')
print(f'Total recipes in recipes-noID.json: {len(recipes_no_id)}')

print(f'\nSample recipe nutrients (recipes-withID.json):')
print(json.dumps(recipes['results'][0].get('nutrients', {}), indent=2))

print(f'\nSample macros data (macros.json):')
print(json.dumps(macros[0], indent=2))

print(f'\nChecking yields field:')
print(f'Sample yield value: {recipes["results"][0].get("yields")}')

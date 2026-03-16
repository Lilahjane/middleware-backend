import json

INPUT_FILE = r"D:\just_mealplanner\source\macros.json"

def get_unique_macro_keys(path):
    with open(path, 'r', encoding='utf-8') as file:
        recipes = json.load(file)
    
    # A set automatically ignores duplicates
    unique_keys = set()
    
    for recipe in recipes:
        # Get the macros dictionary; use .get() to avoid errors if "macros" is missing
        macros = recipe.get("macros", {})
        
        # Add all keys found in this specific recipe's macros
        unique_keys.update(macros.keys())
            
    # Convert to a sorted list for a clean, alphabetical output
    return sorted(list(unique_keys))

# Run it
macro_labels = get_unique_macro_keys(INPUT_FILE)

print(f"Found {len(macro_labels)} unique macro keys:")
print(macro_labels)

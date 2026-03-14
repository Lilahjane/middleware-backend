import json
from pathlib import Path

# Use a Raw String (r"") for Windows paths to avoid backslash errors
INPUT_FILE_PATH = r"D:\just_mealplanner\source\recipes-withID.json"
OUTPUT_FILE_PATH = r"D:\just_mealplanner\source\recipes-withID.json"

def process_recipes():
    # 1. OPEN & LOAD
    with open(INPUT_FILE_PATH, 'r', encoding='utf-8') as file:
        # 'entire_json_dictionary' holds EVERYTHING in the file
        entire_json_dictionary = json.load(file)

    # 2. ACCESS THE ARRAY
    # 'all_recipes_list' holds the array/list found inside "results"
    all_recipes_list = entire_json_dictionary.get('results', [])

    # 3. LOOP THROUGH INDIVIDUAL OBJECTS
    for single_recipe_object in all_recipes_list:
        
        # --- LOGIC EXAMPLES ---
        
        # Pulling specific values
        recipe_id = single_recipe_object.get('id')
        error_val = single_recipe_object.get('error')
        author_val = single_recipe_object.get('author')

        # Check if error is null AND author is empty
        if error_val is None and author_val == "":
            # Update the object directly
            single_recipe_object['author'] = "System Flagged: Missing"
            
        # Working with the nested array inside the single object
        if "ingredients" in single_recipe_object:
            # This variable holds the list for THIS specific recipe
            current_ingredients = single_recipe_object['ingredients']
            # current_ingredients.append("New Item") 

    # 4. SAVE CHANGES
    # We save 'entire_json_dictionary' because it contains the 
    # updated 'all_recipes_list' inside it.
    with open(OUTPUT_FILE_PATH, 'w', encoding='utf-8') as file:
        json.dump(entire_json_dictionary, file, indent=2)

if __name__ == "__main__":
    process_recipes()
import json
import re
import re
INPUT_FILE = r"D:\just_mealplanner\source\macros.json"


def extract_number(value):
    if value is None:
        return None
    value = str(value)
    # fix european decimals
    value = value.replace(",", ".")
    match = re.search(r"\d+\.?\d*", value)
    if match:
        return float(match.group())
    return None

def load_nutrient_objects(path):
    with open(path, 'r', encoding='utf-8') as file:
        nutrient_objects = json.load(file) # nutrient_objects is the entirety of the INPUT_FILE this is the entry point for the code 
    return nutrient_objects #this makes the output of the module accessable to any other functions written here now
    

def get_calories(nutrient_objects):
    calories = []
    for object in nutrient_objects:
        single_cal_value = object.get("macros", {}).get("calories")
        num = extract_number(single_cal_value)
        calories.append(num)
    return calories

def get_carbohydrate(nutrient_objects):
    carbohydrates = []
    for object in nutrient_objects:
        single_carb_value = object.get("macros", {}).get("carbohydrateContent")
        num = extract_number(single_carb_value)
        carbohydrates.append(num)
    return carbohydrates


def get_cholesterol(nutrient_objects):
    cholesterol = []
    for object in nutrient_objects:
        single_cholesterol_value = object.get("macros", {}).get("cholesterolContent")
        num = extract_number(single_cholesterol_value)
        cholesterol.append(num)
    return cholesterol

def get_fat(nutrient_objects):
    fat = []
    for object in nutrient_objects:
        single_fat_value = object.get("macros", {}).get("fatContent")
        num = extract_number(single_fat_value)
        fat.append(num)
    return fat

def get_fiber(nutrient_objects):
    fiber = []
    for object in nutrient_objects:
        single_fiber_value = object.get("macros", {}).get("fiberContent")
        num = extract_number(single_fiber_value)
        fiber.append(num)
    return fiber

def get_net_carbs(nutrient_objects):
    net_carbs = []
    for object in nutrient_objects:
        single_net_carb_value = object.get("macros", {}).get("netCarbContent")
        num = extract_number(single_net_carb_value)
        net_carbs.append(num)
    return net_carbs

def get_protein(nutrient_objects):
    protein = []
    for object in nutrient_objects:
        single_protein_value = object.get("macros", {}).get("proteinContent")
        num = extract_number(single_protein_value)
        protein.append(num)
    return protein

def get_saturatedFat(nutrient_objects):
    saturated_fat = []
    for object in nutrient_objects:
        single_saturated_fat_value = object.get("macros", {}).get("saturatedFatContent")
        num = extract_number(single_saturated_fat_value)
        saturated_fat.append(num)
    return saturated_fat

def get_servingSize(nutrient_objects):
    serving_sizes = []
    for object in nutrient_objects:
        single_serving_size_value = object.get("macros", {}).get("servingSize")
        serving_sizes.append(single_serving_size_value)
    return serving_sizes

def get_sodium(nutrient_objects):
    sodium = []
    for object in nutrient_objects:
        single_sodium_value = object.get("macros", {}).get("sodiumContent")
        num = extract_number(single_sodium_value)
        sodium.append(num)
    return sodium

def get_sugar(nutrient_objects):
    sugar = []
    for object in nutrient_objects:
        single_sugar_value = object.get("macros", {}).get("sugarContent")
        num = extract_number(single_sugar_value)
        sugar.append(num)
    return sugar

def get_transFat(nutrient_objects):
    trans_fat   = []
    for object in nutrient_objects:
        single_trans_fat_value = object.get("macros", {}).get("transFatContent")
        num = extract_number(single_trans_fat_value)
        trans_fat.append(num)
    return trans_fat

def get_type(nutrient_objects):
    types = []
    for object in nutrient_objects:
        single_type_value = object.get("macros", {}).get("type")
        types.append(single_type_value) 
    return types

def get_unsaturatedFat(nutrient_objects):
    unsaturated_fat = []
    for object in nutrient_objects:
        single_unsaturated_fat_value = object.get("macros", {}).get("unsaturatedFatContent")
        num = extract_number(single_unsaturated_fat_value)
        unsaturated_fat.append(num)
    return unsaturated_fat

# load the json
nutrient_objects = load_nutrient_objects(INPUT_FILE)

#queries for each macro value
calories = get_calories(nutrient_objects)
carbohydrates = get_carbohydrate(nutrient_objects)
cholesterol = get_cholesterol(nutrient_objects)
fat = get_fat(nutrient_objects)
fiber = get_fiber(nutrient_objects)
net_carbs = get_net_carbs(nutrient_objects)
protein = get_protein(nutrient_objects) 
saturated_fat = get_saturatedFat(nutrient_objects)
serving_sizes = get_servingSize(nutrient_objects)
sodium = get_sodium(nutrient_objects)
sugar = get_sugar(nutrient_objects)
trans_fat = get_transFat(nutrient_objects)
types = get_type(nutrient_objects)
unsaturated_fat = get_unsaturatedFat(nutrient_objects)



#displayer
print(f"Calories: {calories}")
print(f"Carbohydrates: {carbohydrates}")
print(f"Cholesterol: {cholesterol}")
print(f"Fat: {fat}")
print(f"Fiber: {fiber}")
print(f"Net Carbs: {net_carbs}")
print(f"Protein: {protein}")
print(f"Saturated Fat: {saturated_fat}")
print(f"Serving Sizes: {serving_sizes}")
print(f"Sodium: {sodium}")
print(f"Sugar: {sugar}")
print(f"Trans_fat: {trans_fat}")
print(f"Types: {types}")
print(f"Unsaturated Fat: {unsaturated_fat}")
import re
import json
INPUT_FILE = r"D:\just_mealplanner\source\macros.json"

class NutritionCleaner:
    

    # nutrients that should be stored as milligrams
    MG_NUTRIENTS = {
        "sodium",
        "cholesterol"
    }

    def __init__(self):
        pass

    @staticmethod
    def clean_nutrient_objects(objects):
        cleaner = NutritionCleaner()
        cleaned_objects = []

        for obj in objects:  # only first 10 objects

            new_obj = obj.copy()

            macros = obj.get("macros", {})
            cleaned_macros = {}

            for key, value in macros.items():

                # skip these keys
                if key in {"servingSize", "type"}:
                    cleaned_macros[key] = value
                    continue

                cleaned_value = cleaner.clean_value(value, key)

                cleaned_macros[key] = cleaned_value

            new_obj["macros"] = cleaned_macros
            cleaned_objects.append(new_obj)

        return cleaned_objects

    def extract_number(self, value):
        """Extract first numeric value from a string."""

        if value is None:
            return None

        value = str(value)

        # convert comma decimals to periods
        value = value.replace(",", ".")

        match = re.search(r"\d+\.?\d*", value)

        if match:
            return float(match.group())

        return None


    def convert_units(self, value, raw_text, nutrient):
        """Convert units if needed (ex: g → mg)."""

        if value is None:
            return None

        text = str(raw_text).lower()

        if nutrient.lower() in self.MG_NUTRIENTS:

            # convert grams to mg
            if " g" in text or "grams" in text:
                return value * 1000

        return value


    def clean_value(self, raw_value, nutrient):
        """Full cleaning pipeline for one value."""

        number = self.extract_number(raw_value)

        cleaned = self.convert_units(number, raw_value, nutrient)

        return cleaned


    def clean_column(self, values, nutrient):
        """Clean an entire list of nutrient values."""

        cleaned_values = []

        for v in values:
            cleaned_values.append(self.clean_value(v, nutrient))

        return cleaned_values
    
    
def load_nutrient_objects(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)
    
    
nutrient_objects = load_nutrient_objects(INPUT_FILE)

cleaned = NutritionCleaner.clean_nutrient_objects(nutrient_objects)

print(json.dumps(cleaned, indent=2))
    
import uuid
import json

def add_id():
    with open('recipes-noID.json', 'r',encoding='utf-8') as file: #what does the r do?
        data = json.load(file)
    recipes = data.get('results', [])
    for recipe in recipes:
        recipe['id'] = generate_uuid_hex()
        
    with open('recipes-withID.json', 'w',encoding='utf-8') as file:
        json.dump(data, file, indent=2)

def generate_uuid_hex():
  """Generates a standard UUID (v4) as a 32-character hex string without hyphens."""
  return uuid.uuid4().hex

add_id()
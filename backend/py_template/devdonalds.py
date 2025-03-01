from dataclasses import dataclass
from typing import List, Dict, Union
from flask import Flask, request, jsonify
import re

# ==== Type Definitions, feel free to add or modify ===========================
@dataclass
class CookbookEntry:
	name: str

@dataclass
class RequiredItem():
	name: str
	quantity: int

@dataclass
class Recipe(CookbookEntry):
	required_items: List[RequiredItem]

@dataclass
class Ingredient(CookbookEntry):
	cook_time: int


# =============================================================================
# ==== HTTP Endpoint Stubs ====================================================
# =============================================================================
app = Flask(__name__)

# Store your recipes here!
cookbook: Dict[str, Union[Recipe, Ingredient]] = {}

# Task 1 helper (don't touch)
@app.route("/parse", methods=['POST'])
def parse():
	data = request.get_json()
	recipe_name = data.get('input', '')
	parsed_name = parse_handwriting(recipe_name)
	if parsed_name is None:
		return 'Invalid recipe name', 400
	return jsonify({'msg': parsed_name}), 200

# [TASK 1] ====================================================================
# Takes in a recipeName and returns it in a form that 
def parse_handwriting(recipeName: str) -> Union[str | None]:
	# remove - and _
    recipeName = recipeName.replace('-', ' ').replace('_', ' ')
    
    # remove everyhting except letters and whitespace
    recipeName = re.sub(r'[^a-zA-Z\s]', '', recipeName)
    
    # Capitalize the first letter of each word and make the others lowercase
    recipeName = recipeName.title()

    # Ensure only one whitespace between words and strip leading/trailing spaces
    recipeName = re.sub(r'\s+', ' ', recipeName).strip()

    return None if not recipeName else recipeName


# [TASK 2] ====================================================================
# Endpoint that adds a CookbookEntry to your magical cookbook
@app.route('/entry', methods=['POST'])
def create_entry():
    data = request.get_json()
    entry_type = data.get('type')
    name = data.get('name')

    if entry_type not in ['recipe', 'ingredient']:
        return jsonify({'error': 'Invalid type - must be recipe or ingredient'}), 400

    if name in cookbook:
        return jsonify({'error': 'Item already exists in cookbook'}), 400

    # Handle recipe entries
    if entry_type == 'recipe':
        required_items = data.get('requiredItems', [])

        if not is_valid_required_items(required_items):
            return jsonify({'error': 'Invalid required items.'}), 400
        
        add_recipe(name, required_items)

    # Handle ingredient entries
    elif entry_type == 'ingredient':
        cook_time = data.get('cookTime')
        
        if not is_valid_cook_time(cook_time):
            return jsonify({'error': 'Invalid cook time.'}), 400
        
        add_ingredient(name, cook_time)

    return '', 200

def is_valid_required_items(required_items):
    seen_items = set()
    for item in required_items:
        item_name = item.get('name')
        item_quantity = item.get('quantity')
        
        # ensure item quantity is a positive int
        if not isinstance(item_quantity, int) or item_quantity <= 0:
            return False
        
        # ensure unique item names
        if item_name in seen_items:
            return False

        seen_items.add(item_name)
    return True
    
def is_valid_cook_time(cook_time):
    return isinstance(cook_time, int) and cook_time >= 0

def add_recipe(name, required_items):
    cookbook[name] = Recipe(name=name, required_items=[RequiredItem(**item) for item in required_items])

def add_ingredient(name, cook_time):
    cookbook[name] = Ingredient(name=name, cook_time=cook_time)


# [TASK 3] ====================================================================
# Endpoint that returns a summary of a recipe that corresponds to a query name
@app.route('/summary', methods=['GET'])
def summary():
    recipe_name = request.args.get('name')
    recipe = cookbook.get(recipe_name)
    if not recipe or isinstance(recipe, Ingredient):
        return jsonify({'error': 'Recipe not found or invalid'}), 400
    
    ingredient_list = []
    total_cook_time = 0
    
    # Collecting ingredients
    for item in recipe.required_items:
        required_item = cookbook.get(item.name)
        if not required_item:
            return jsonify({'error': f'Ingredient or recipe {item.name} not found in cookbook'}), 400
        total_cook_time, ingredient_list = get_ingredients(required_item, item.quantity, ingredient_list, total_cook_time)

    return jsonify({
        'name': recipe_name,
        'cookTime': total_cook_time,
        'ingredients': ingredient_list
    }), 200


# Recursively collect ingredients
def get_ingredients(entry, quantity, ingredient_list, total_cook_time):
    if isinstance(entry, Ingredient):
        ingredient_list.append({'name': entry.name, 'quantity': quantity})
        total_cook_time += entry.cook_time * quantity
    elif isinstance(entry, Recipe):
        for item in entry.required_items:
            required_item = cookbook.get(item.name) # Ensure item exists in the cookbook
            if not required_item:
                raise ValueError(f'Ingredient or recipe {item.name} not found in cookbook')
            # Recursive call to gather ingredients
            total_cook_time, ingredient_list = get_ingredients(required_item, item.quantity, ingredient_list, total_cook_time)
    
    return total_cook_time, ingredient_list

# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == '__main__':
	app.run(debug=True, port=8080)

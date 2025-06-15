from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv
import os

def configure():
    load_dotenv()

app = Flask(__name__)
CORS(app)

user_data = {}  # Store user session data

@app.route("/get_recipe", methods=["POST"])
def get_recipe():
    try:
        data = request.get_json()
        user_input = data.get("message", "").strip().lower()

        user_id = data.get("session_id", "default_user")  # Track a single user session

        if user_id not in user_data:
            user_data[user_id] = {"step": "start"}  # Start fresh session

        step = user_data[user_id]["step"]

        # Step 0: Greeting
        if step == "start":
            if user_input in ["hi", "hello", "hey"]:
                user_data[user_id]["step"] = "bmi"
                return jsonify({"message": "Hello! Please enter your height (cm) and weight (kg) as 'height, weight'."})
            else:
                return jsonify({"message": "Please start by saying 'hi' or 'hello'."})

        # Step 1: Get BMI
        elif step == "bmi":
            try:
                height, weight = map(float, user_input.split(","))
                bmi = weight / ((height / 100) ** 2)
                user_data[user_id]["bmi"] = bmi
                user_data[user_id]["step"] = "preference"

                if bmi < 18.5:
                    category = "underweight"
                elif 18.5 <= bmi < 24.9:
                    category = "normal weight"
                elif 25 <= bmi < 29.9:
                    category = "overweight"
                else:
                    category = "obese"

                return jsonify({"message": f"Your BMI is {bmi:.1f} ({category}). Do you prefer vegetarian or non-vegetarian meals?"})
            except:
                return jsonify({"message": "Invalid input. Please enter your height and weight as 'height, weight'."})

        # Step 2: Get Vegetarian/Non-Vegetarian Preference
        elif step == "preference":
            if user_input in ["vegetarian", "veg", "non-vegetarian", "non veg", "nonveg"]:
                user_data[user_id]["preference"] = "vegetarian" if "veg" in user_input else "non-vegetarian"
                user_data[user_id]["step"] = "ingredients"
                return jsonify({"message": "Got it! Now, please enter the ingredients you have."})
            else:
                return jsonify({"message": "Please enter 'vegetarian' or 'non-vegetarian'."})

        # Step 3: Get Ingredients & Provide Three Meals
        elif step == "ingredients":
            user_data[user_id]["ingredients"] = ",".join(user_input.split()).lower()
            preference = user_data[user_id]["preference"]
            bmi_category = user_data[user_id]["bmi"]

            # Get recipes based on preference
            recipes = fetch_recipes(user_data[user_id]["ingredients"], preference)
            if not recipes:
                return jsonify({"message": "No suitable recipes found for your preference and ingredients."})

            # Select recipes for three meals
            meal_plan = select_meal_plan(recipes, bmi_category)

            if meal_plan:
                response_message = "🍽️ <b>Meal Plan Based on Your BMI:</b><br><br>"

                for meal, recipe in meal_plan.items():
                   if recipe:  # ✅ Only show details if a recipe exists
                    response_message += f"<b>🔹 {meal.capitalize()}</b><br>"
                    response_message += f"<b>📌 {recipe['title']}</b><br><br>"
                    response_message += f"{recipe['instructions']}<br><br>"
                    response_message += (
                             f"<b>⚡ Nutrition:</b> {recipe['calories']} kcal | "
                             f"{recipe['protein']}g Protein | {recipe['carbs']}g Carbs | {recipe['fat']}g Fat<br><br>"
            )
                   else:
                     response_message += f"<b>🔹 {meal.capitalize()}</b><br>❌ No recipe available.<br><br>"

                return jsonify({"message": response_message})

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"message": f"Server Error: {str(e)}"})

# Fetch Recipes Based on Ingredients and Preference
def fetch_recipes(ingredients, preference):
    url = f"https://api.spoonacular.com/recipes/findByIngredients?ingredients={ingredients}&number=10&apiKey={os.getenv('API_KEY')}"

    if preference == "vegetarian":
        url += "&diet=vegetarian"  # Ensure only vegetarian meals are fetched

    response = requests.get(url)

    if response.status_code != 200:
        return []

    recipes = response.json()
    detailed_recipes = []

    for recipe in recipes:
        details_url = f"https://api.spoonacular.com/recipes/{recipe['id']}/information?includeNutrition=true&apiKey={os.getenv('API_KEY')}"
        details_response = requests.get(details_url)

        if details_response.status_code == 200:
            details = details_response.json()

            # **Double-checking for vegetarian property**
            if preference == "vegetarian" and not details.get("vegetarian", False):
                continue  # Skip non-veg for vegetarians
            elif preference == "non-vegetarian" and details.get("vegetarian", False):
                continue  # Skip veg for non-vegetarians

            detailed_recipes.append({
                "title": details["title"],
                "instructions": details.get("instructions", "No instructions available."),
                "calories": details["nutrition"]["nutrients"][0]["amount"],
                "protein": details["nutrition"]["nutrients"][8]["amount"],
                "carbs": details["nutrition"]["nutrients"][3]["amount"],
                "fat": details["nutrition"]["nutrients"][1]["amount"]
            })

    return detailed_recipes

# Select Recipes for Three Meals Based on BMI
def select_meal_plan(recipes, bmi):
    meal_plan = {}

    # Categorize meals based on BMI
    if bmi < 18.5:
        meal_plan["breakfast"] = recipes[0] if len(recipes) > 0 else None
        meal_plan["lunch"] = recipes[1] if len(recipes) > 1 else None
        meal_plan["dinner"] = recipes[2] if len(recipes) > 2 else None
    elif 18.5 <= bmi < 24.9:
        meal_plan["breakfast"] = recipes[1] if len(recipes) > 1 else None
        meal_plan["lunch"] = recipes[2] if len(recipes) > 2 else None
        meal_plan["dinner"] = recipes[3] if len(recipes) > 3 else None
    elif 25 <= bmi < 29.9:
        meal_plan["breakfast"] = recipes[2] if len(recipes) > 2 else None
        meal_plan["lunch"] = recipes[3] if len(recipes) > 3 else None
        meal_plan["dinner"] = recipes[4] if len(recipes) > 4 else None
    else:
        meal_plan["breakfast"] = recipes[3] if len(recipes) > 3 else None
        meal_plan["lunch"] = recipes[4] if len(recipes) > 4 else None
        meal_plan["dinner"] = recipes[5] if len(recipes) > 5 else None

    return meal_plan

# ✅ Webhook for Dialogflow
@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json()
    print("🌍 Received Webhook Request:", req)  # Debugging output

    # Extract intent name
    intent = req.get("queryResult", {}).get("intent", {}).get("displayName", "")
    parameters = req.get("queryResult", {}).get("parameters", {})
    
    user_id = "default_user"

    # Ensure user session exists
    if user_id not in user_data:
        user_data[user_id] = {"step": "start"}

    # ✅ Handle "greeting_intent"
    if intent == "greeting_intent":
        user_data[user_id]["step"] = "bmi"
        return jsonify({"fulfillmentText": "Hello! Please enter your height (cm) and weight (kg) as 'height, weight'."})

    # ✅ Handle "bmi_intent"
    elif intent == "bmi_intent":
        try:
            height = float(parameters.get("height", 0))
            weight = float(parameters.get("weight", 0))

            if height > 0 and weight > 0:
                bmi = weight / ((height / 100) ** 2)
                user_data[user_id]["bmi"] = bmi
                user_data[user_id]["step"] = "preference"

                if bmi < 18.5:
                    category = "underweight"
                elif 18.5 <= bmi < 24.9:
                    category = "normal weight"
                elif 25 <= bmi < 29.9:
                    category = "overweight"
                else:
                    category = "obese"

                return jsonify({"fulfillmentText": f"Your BMI is {bmi:.1f} ({category}). Do you prefer vegetarian or non-vegetarian meals?"})
            else:
                return jsonify({"fulfillmentText": "Invalid input. Please enter your height and weight as 'height, weight'."})
        except:
            return jsonify({"fulfillmentText": "Invalid format. Please enter height and weight correctly."})

    # ✅ Handle "preference_intent"
    elif intent == "preference_intent":
        preference = parameters.get("preference", "").lower()
        if preference in ["vegetarian", "non-vegetarian"]:
            user_data[user_id]["preference"] = preference
            user_data[user_id]["step"] = "ingredients"
            return jsonify({"fulfillmentText": "Got it! Now, please enter the ingredients you have."})
        else:
            return jsonify({"fulfillmentText": "Please enter 'vegetarian' or 'non-vegetarian'."})

    # ✅ Handle "ingredients_intent"
    elif intent == "ingredients_intent":
        ingredient = parameters.get("ingredient", "").lower()
        if ingredient:
            user_data[user_id]["ingredients"] = ingredient
            preference = user_data[user_id]["preference"]
            bmi_category = user_data[user_id]["bmi"]

            # Fetch recipes
            recipes = fetch_recipes(user_data[user_id]["ingredients"], preference)
            if not recipes:
                return jsonify({"fulfillmentText": "No suitable recipes found for your preference and ingredients."})

            # Select recipes for three meals
            meal_plan = select_meal_plan(recipes, bmi_category)

            if meal_plan:
                response_message = "🍽️ <b>Meal Plan Based on Your BMI:</b><br><br>"
                for meal, recipe in meal_plan.items():
                    response_message += f"<b>🔹 {meal.capitalize()}</b><br>"
                    response_message += f"<b>📌 {recipe['title']}</b><br><br>"
                    response_message += f"{recipe['instructions']}<br><br>"
                    response_message += f"<b>⚡ Nutrition:</b> {recipe['calories']} kcal | {recipe['protein']}g Protein | {recipe['carbs']}g Carbs | {recipe['fat']}g Fat<br><br>"

                return jsonify({"fulfillmentText": response_message})
            else:
                return jsonify({"fulfillmentText": "<b>⚠️ No suitable meal plan found based on your BMI.</b>"})
        else:
            return jsonify({"fulfillmentText": "Please enter at least one ingredient."})

    elif intent == "random_recipe_intent":
        url = f"https://api.spoonacular.com/recipes/random?number=1&apiKey={os.getenv('API_KEY')}"
        response = requests.get(url)
        if response.status_code == 200:
            recipe = response.json()["recipes"][0]
            title = recipe.get("title", "No title")
            instructions = recipe.get("instructions", "No instructions provided.")
            return jsonify({"fulfillmentText": f"🍽️ Here's a random recipe!\n\n📌 {title}\n\n🧑‍🍳 {instructions}"})
        else:
            return jsonify({"fulfillmentText": "Sorry, I couldn't fetch a random recipe right now."})

    # ✅ Handle "recipe_intent" (If user directly asks for a recipe)
    elif intent == "recipe_intent":
        preference = user_data[user_id].get("preference", "")
        bmi_category = user_data[user_id].get("bmi", "")
        ingredients = user_data[user_id].get("ingredients", "")

        if not preference or not bmi_category or not ingredients:
            return jsonify({"fulfillmentText": "Please follow the steps in order. Start by saying 'Hi'."})

        # Fetch recipes
        recipes = fetch_recipes(ingredients, preference)
        if not recipes:
            return jsonify({"fulfillmentText": "No suitable recipes found for your preference and ingredients."})

        # Select recipes for three meals
        meal_plan = select_meal_plan(recipes, bmi_category)

        if meal_plan:
         response_message = "🍽️ <b>Meal Plan Based on Your BMI:</b><br><br>"

        for meal, recipe in meal_plan.items():
            if recipe:  # ✅ Only show details if a recipe exists
                response_message += f"<b>🔹 {meal.capitalize()}</b><br>"
                response_message += f"<b>📌 {recipe['title']}</b><br><br>"
                response_message += f"{recipe['instructions']}<br><br>"
                response_message += (
                    f"<b>⚡ Nutrition:</b> {recipe['calories']} kcal | "
                    f"{recipe['protein']}g Protein | {recipe['carbs']}g Carbs | {recipe['fat']}g Fat<br><br>"
                )
            else:
                response_message += f"<b>🔹 {meal.capitalize()}</b><br>❌ No recipe available.<br><br>"

        return jsonify({"fulfillmentText": response_message})

    elif intent == "sort_by_intent":
        sort_option = parameters.get("sort_option", "calories")
        ingredients = user_data[user_id].get("ingredients", "")
        preference = user_data[user_id].get("preference", "")

        if not ingredients:
            return jsonify({"fulfillmentText": "Please enter some ingredients first."})

        url = f"https://api.spoonacular.com/recipes/complexSearch?includeIngredients={ingredients}&sort={sort_option}&number=3&apiKey={os.getenv('API_KEY')}"
        if preference == "vegetarian":
            url += "&diet=vegetarian"

        response = requests.get(url)
        if response.status_code == 200:
            recipes = response.json().get("results", [])
            if not recipes:
                return jsonify({"fulfillmentText": "No recipes found with sorting."})

            reply = "📊 Here are sorted recipes:\n\n"
            for r in recipes:
                reply += f"🍽️ {r['title']}\n\n"
            return jsonify({"fulfillmentText": reply})
        else:
            return jsonify({"fulfillmentText": "Failed to fetch sorted recipes."})


if __name__ == "__main__":
    configure()
    app.run(debug=True, port=5000)
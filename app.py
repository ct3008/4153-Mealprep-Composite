import os
import requests
from fastapi import FastAPI, HTTPException, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from dotenv import load_dotenv
import uvicorn

# Initialize FastAPI
app = FastAPI()

load_dotenv()
# Get service URLs from environment variables
RECIPE_SERVICE_URL = os.getenv("RECIPE_LOCAL_URL")
NUTRITION_SERVICE_URL = os.getenv("NUTRITION_LOCAL_URL")
MEALPLAN_SERVICE_URL = os.getenv("MEALPLAN_LOCAL_URL")


# # Define a model to represent the filtered recipe and nutrition data
# class RecipeWithNutrition(BaseModel):
#     recipe_id: int
#     title: str
#     ingredients: list
#     instructions: str
#     nutrition: Optional[dict] = None  # Nutrition information as a nested dictionary

class RecipeWithNutrition(BaseModel):
    recipe_id: int
    title: str = Field(..., description="The title of the recipe")
    # ingredients: Optional[List[str]] = Field(default=[], description="List of ingredients")
    steps: str = Field(..., description="Instructions for the recipe")
    kid_friendly: bool
    nutrition: Dict[str, Optional[str]] = Field(default_factory=dict)

# Function to get data from the recipes microservice
def get_recipe_data(recipe_id: int):
    try:
        # response = requests.get(f"{RECIPE_SERVICE_URL}/recipes/{recipe_id}")
        response = requests.get(f"{RECIPE_SERVICE_URL}/recipes/")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recipe data: {e}")

# Function to get data from the nutrition microservice
def get_nutrition_data(recipe_id: int):
    try:
        # response = requests.get(f"{NUTRITION_SERVICE_URL}/nutrition/{recipe_id}")
        response = requests.get(f"{NUTRITION_SERVICE_URL}/")
        print("response: ", response)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching nutrition data: {e}")

# Function to aggregate and filter recipe and nutrition data
def get_filtered_recipe_with_nutrition(recipe_id: int):
    # Fetch recipe data
    recipe = get_recipe_data(recipe_id)[0]
    print("RECIPE: ", recipe)
    # Fetch nutrition data
    nutrition = get_nutrition_data(recipe_id)
    print("NUTRITION: ", nutrition)

    # Filter and format the result to return only necessary fields
    return {
        "recipe": recipe,
        "nutrition": nutrition
    }

@app.get("/composite/recipes_with_nutrition/{recipe_id}", response_model=RecipeWithNutrition)
async def recipe_with_nutrition(recipe_id: int):
    try:
        # Fetch data from both microservices
        recipe = get_recipe_data(recipe_id)[0]
        print("recipe: ", recipe)
        nutrition = get_nutrition_data(recipe_id)
        print("Nutrition: ", nutrition)

        # Combine data into a single response
        combined_data = {
            "recipe_id": recipe["recipe_id"],
            "title": recipe["name"],
            # "ingredients": recipe.get("ingredients"),
            "steps": recipe["steps"],
            "kid_friendly": recipe["kid_friendly"],
            "nutrition": nutrition
        }

        # Return combined data
        return combined_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check route
@app.get("/health")
def health_check():
    return {"status": "Composite service is running."}


if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=5006)
import os
import requests
from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from dotenv import load_dotenv
import uvicorn
import json
import aiohttp
import asyncio
import time
import logging
import time
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI
app = FastAPI()

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Get service URLs from environment variables
RECIPE_SERVICE_URL = os.getenv("RECIPE_LOCAL_URL")
NUTRITION_SERVICE_URL = os.getenv("NUTRITION_LOCAL_URL")
MEALPLAN_SERVICE_URL = os.getenv("MEALPLAN_LOCAL_URL")

# Middleware to log requests before and after
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")

    # Log before the request is processed
    start_time = time.time()

    # Call the next process in the pipeline
    response = await call_next(request)

    # Log after the request is processed
    process_time = time.time() - start_time
    logger.info(f"Response status: {response.status_code} | Time: {process_time:.4f}s")

    return response

class RecipeWithNutrition(BaseModel):
    recipe_id: int
    name: str = Field(..., description="The title of the recipe")
    steps: str = Field(..., description="Steps to cook")
    time_to_cook: int = Field(..., description="Time required to cook the recipe")
    meal_type: str = Field(..., description="Meal Type")
    calories_recipe: int = Field(..., description="Calories in the recipe")
    rating: float = Field(..., description="Rating of the recipe")
    goal: str = Field(..., description="Nutrition goal")  # Add any other fields as necessary
    calories_nutrition: float = Field(..., description="Calories from nutrition data")
    carbohydrates: float = Field(..., description="Carbohydrates from nutrition data")
    protein: float = Field(..., description="Protein from nutrition data")
    fiber: float = Field(..., description="Fiber from nutrition data")
    fat: float = Field(..., description="Fat from nutrition data")
    sugar: float = Field(..., description="Sugar from nutrition data")
    sodium: float = Field(..., description="Sodium from nutrition data")
    ingredient_alternatives: str = Field(..., description="Ingredient alternatives")
    diet_type: str = Field(..., description="Diet type")
    week_plan_id: int
    weeks: str = Field(..., description="Diet type")
    food: str = Field(..., description="Diet type")

class Recipe(BaseModel):
    recipe_id: int= Field(..., description="ID of recipe")
    name: str = Field(..., description="The title of the recipe")
    ingredients: list = Field(..., description="List of ingredients")
    steps: str = Field(..., description="Steps to cook")
    time_to_cook: int = Field(..., description="Time required to cook the recipe")
    meal_type: str = Field(..., description="Meal Type")
    calories: int = Field(..., description="Calories in the recipe")
    rating: float = Field(..., description="Rating of the recipe")
    links: Optional[dict] = Field(None, description="List of reachable links")
    

# Synchronous function to get data from the recipes microservice
def get_recipe_data_sync(recipe_id: int):
    try:
        response = requests.get(f"{RECIPE_SERVICE_URL}/recipes/id/{recipe_id}/")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recipe data: {e}")

# Synchronous function to get data from the nutrition microservice
def get_nutrition_data_sync(recipe_id: int):
    try:
        response = requests.get(f"{NUTRITION_SERVICE_URL}/api/nutrition/{recipe_id}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching nutrition data: {e}")

def get_mealplan_data_sync():
    try:
        response = requests.get(f"{MEALPLAN_SERVICE_URL}/mealprep?date=2024-10-30")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching nutrition data: {e}")

# Asynchronous function to get data from the recipes microservice
async def get_recipe_data_async(recipe_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{RECIPE_SERVICE_URL}/recipes/id/{recipe_id}/") as response:
            if response.status != 200:
                raise HTTPException(status_code=500, detail="Error fetching recipe data")
            return await response.json()

# Asynchronous function to get data from the nutrition microservice
async def get_nutrition_data_async(recipe_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{NUTRITION_SERVICE_URL}/api/nutrition/{recipe_id}") as response:
            if response.status != 200:
                raise HTTPException(status_code=500, detail="Error fetching nutrition data")
            return await response.json()
        
#hardcoded, but used as an example of properly connecting to the mealprep api
async def get_mealplan_data_async():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{MEALPLAN_SERVICE_URL}/mealprep?date=2024-10-30") as response:
            if response.status != 200:
                raise HTTPException(status_code=500, detail="Error fetching nutrition data")
            return await response.json()
        

# Composite endpoint to aggregate and filter recipe and nutrition data
@app.get("/composite/recipes_with_nutrition/{recipe_id}", response_model=RecipeWithNutrition)
async def recipe_with_nutrition(recipe_id: int):
    try:
        for i in range(2):  # Increase the number of iterations
            start_time_async = time.time()
            recipe, nutrition, mealplan = await asyncio.gather(
                get_recipe_data_async(recipe_id),
                get_nutrition_data_async(recipe_id),
                get_mealplan_data_async()
            )
            print("recipe: ", recipe)
            print("nutrition: ", nutrition)
            print("mealplan: ", mealplan[0])
            print("mealplan 2: ", mealplan[0][0])
            print("mealplan 3: ", mealplan[0][0]["week_plan_id"])
            total_time_async = time.time() - start_time_async
            print(f"Asynchronous call {i} took {total_time_async:.2f} seconds")

            start_time_sync = time.time()
            recipe_sync = get_recipe_data_sync(recipe_id)
            nutrition_sync = get_nutrition_data_sync(recipe_id)
            get_mealplan_data_sync()
            total_time_sync = time.time() - start_time_sync
            print(f"Synchronous call {i} took {total_time_sync:.2f} seconds")

        combined_data = {
            "recipe_id": recipe["recipe_id"],
            "name": recipe["name"],
            "steps": recipe["steps"],
            "time_to_cook": recipe["time_to_cook"],
            "meal_type": recipe["meal_type"],
            "calories_recipe": recipe["calories"],
            "rating": recipe["rating"],
            "goal": nutrition["goal"],
            "calories_nutrition": nutrition["calories"],
            "carbohydrates": nutrition["carbohydrates"],
            "protein": nutrition["protein"],
            "fiber": nutrition["fiber"],
            "fat": nutrition["fat"],
            "sugar": nutrition["sugar"],
            "sodium": nutrition["sodium"],
            "ingredient_alternatives": nutrition["ingredient_alternatives"],
            "diet_type": nutrition["diet_type"],
            "week_plan_id": mealplan[0][0]["week_plan_id"],
            "weeks": str(mealplan[0][0]),
            "food": str(mealplan[0][0])
        }

        # Return combined data
        return combined_data

    except Exception as e:
        print(f"An error occurred: {str(e)}")  # Print the error for debugging
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/composite/recipes/id/{recipe_id}", response_model=Recipe)
def get_recipe_details(recipe_id: int):
    try:
        start_time_async = time.time()
        recipe= get_recipe_data_sync(recipe_id)
        print("recipe: ", recipe)
        total_time_async = time.time() - start_time_async
        print(f"Recipe asynchronous call took {total_time_async:.2f} seconds")


        combined_data = {
            "recipe_id": recipe["recipe_id"],
            "name": recipe["name"],
            "ingredients": recipe["ingredients"],
            "steps": recipe["steps"],
            "time_to_cook": recipe["time_to_cook"],
            "meal_type": recipe["meal_type"],
            "calories": recipe["calories"],
            "rating": recipe["rating"]
        }

        # Return combined data
        return combined_data

    except Exception as e:
        print(f"An error occurred: {str(e)}")  # Print the error for debugging
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/composite/recipes", response_model=Recipe)
async def create_recipe_in_composite(recipe: Recipe):
    try:
        # Send a POST request to the recipe API to create a new recipe
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{RECIPE_SERVICE_URL}/recipes", json=recipe.dict()) as response:
                if response.status != 201:
                    raise HTTPException(status_code=response.status, detail="Failed to create recipe")
                # Return the newly created recipe data
                created_recipe = await response.json()
                return created_recipe
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating recipe: {e}")

# PUT endpoint to update an existing recipe
@app.put("/composite/recipes/id/{recipe_id}", response_model=Recipe)
async def update_recipe_in_composite(recipe_id: int, recipe: Recipe):
    print("Composite called")
    try:
        # Send a PUT request to the recipe API to update the recipe with recipe_id
        async with aiohttp.ClientSession() as session:
            print("Composite called: ", f"{RECIPE_SERVICE_URL}/recipes/id/{recipe_id}")
            print("Data: ",recipe.dict() )
            async with session.put(f"{RECIPE_SERVICE_URL}/recipes/id/{recipe_id}", json=recipe.dict()) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail="Failed to update recipe")
                # Return the updated recipe data
                updated_recipe = await response.json()
                return updated_recipe
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating recipe: {e}")


# POST endpoint for creating a new recipe via the composite service
@app.post("/composite/recipes", response_model=Recipe)
async def create_recipe_in_composite(recipe: Recipe):
    try:
        response = requests.post(f"{RECIPE_SERVICE_URL}/recipes", json=recipe.dict())
        response.raise_for_status()  # Raise an error for bad responses (e.g., 4xx or 5xx)

        # Return the response from the recipe microservice
        return response.json()
    except requests.RequestException as e:
        print(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create recipe: {e}")


@app.put("/composite/recipes/{recipe_id}", response_model=Recipe)
async def update_recipe_in_composite(recipe_id: int, recipe: Recipe):
    try:
        # Send a PUT request to the recipe API to update the recipe with recipe_id
        async with aiohttp.ClientSession() as session:
            async with session.put(f"{RECIPE_SERVICE_URL}/recipes/id/{recipe_id}", json=recipe.dict()) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail="Failed to update recipe")
                # Return the updated recipe data
                updated_recipe = await response.json()
                return updated_recipe
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating recipe: {e}")



# Example usage:
async def main():
    # For testing purposes, you can run the API here.
    pass

if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=5006)

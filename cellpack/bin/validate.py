import sys
import fire
import json

from cellpack.autopack.validation.recipe_validator import RecipeValidator, RecipeValidationError


def validate(recipe_path):
    try:
        with open(recipe_path, "r") as f:
            raw_recipe_data = json.load(f)
        
        RecipeValidator.validate_recipe(raw_recipe_data)
        
        print(f"Recipe {raw_recipe_data['name']} is valid")
    except RecipeValidationError as e:
        print("Recipe validation failed:", e)
        sys.exit(1)


def main():
    fire.Fire(validate)


if __name__ == "__main__":
    main()

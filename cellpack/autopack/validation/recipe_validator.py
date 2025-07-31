from pydantic import ValidationError
from .recipe_models import Recipe, RecipeObject



class RecipeValidator:
    @staticmethod
    def validate_recipe(recipe_data):
        try:
            recipe_model = Recipe(**recipe_data)
            validated_data = recipe_model.model_dump() #equivalent to .dict()   
            
            if "objects" in recipe_data and recipe_data["objects"]:
                validated_objects = {}
                for obj_name, obj_data in recipe_data["objects"].items():
                    validated_obj = RecipeObject(**obj_data)
                    validated_objects[obj_name] = validated_obj.model_dump()
                validated_data["objects"] = validated_objects
            
            return validated_data
            
        except ValidationError as e:
            print("Validation error:", e)
from .recipe_models import Recipe, RecipeObject, RecipeGradient


class RecipeValidator:
    @staticmethod
    def validate_recipe(recipe_data):
        # main recipe metadata
        recipe_model = Recipe(**recipe_data)
        validated_data = recipe_model.model_dump()  # equivalent to .dict()

        # individual objects
        if "objects" in recipe_data and recipe_data["objects"]:
            validated_objects = {}
            for obj_name, obj_data in recipe_data["objects"].items():
                validated_obj = RecipeObject(**obj_data)
                validated_objects[obj_name] = validated_obj.model_dump()
            validated_data["objects"] = validated_objects

        # individual gradients
        if "gradients" in recipe_data and recipe_data["gradients"]:
            validated_gradients = {}
            for gradient_name, gradient_data in recipe_data["gradients"].items():
                validated_gradient = RecipeGradient(**gradient_data)
                validated_gradients[gradient_name] = validated_gradient.model_dump()
            validated_data["gradients"] = validated_gradients

        return validated_data

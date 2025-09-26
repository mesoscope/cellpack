from .recipe_models import Recipe, RecipeObject, RecipeGradient


class RecipeValidator:
    @staticmethod
    def format_validation_error(validation_error):
        """
        Format a Pydantic ValidationError into a user-friendly message
        Shows field location and basic error info for quick debugging
        """
        error_lines = ["Validation errors found:"]

        for error in validation_error.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            error_msg = error["msg"]
            error_lines.append(f"  Field: {field_path}")
            error_lines.append(f"  Error: {error_msg}")

        return "\n".join(error_lines)

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

        # individual gradients - handle both dict and list formats
        if "gradients" in recipe_data and recipe_data["gradients"]:
            if isinstance(recipe_data["gradients"], dict):
                # dict format: {"gradient_name": {...}, ...}
                validated_gradients = {}
                for gradient_name, gradient_data in recipe_data["gradients"].items():
                    validated_gradient = RecipeGradient(**gradient_data)
                    validated_gradients[gradient_name] = validated_gradient.model_dump()
                validated_data["gradients"] = validated_gradients
            elif isinstance(recipe_data["gradients"], list):
                # list format: [{"name": "gradient_name", ...}, ...]
                validated_gradients = []
                for gradient_data in recipe_data["gradients"]:
                    if isinstance(gradient_data, dict):
                        validated_gradient = RecipeGradient(**gradient_data)
                        validated_gradients.append(validated_gradient.model_dump())
                    else:
                        validated_gradients.append(gradient_data)
                validated_data["gradients"] = validated_gradients

        return validated_data

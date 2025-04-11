import copy

from ..interface_objects.gradient_data import GradientData, ModeOptions


def convert(recipe_data_2_1):
    new_recipe = copy.deepcopy(recipe_data_2_1)
    new_recipe["format_version"] = "2.2"
    for object_name in recipe_data_2_1["objects"]:
        object_data = recipe_data_2_1["objects"][object_name]
        if "packing_mode" not in object_data:
            object_data["packing_mode"] = "random"
        else:
            packing_mode = object_data["packing_mode"]
            if len(packing_mode) == 0:
                object_data["packing_mode"] = "random"
    return new_recipe

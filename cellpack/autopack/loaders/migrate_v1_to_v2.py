from math import pi
from cellpack.autopack.interface_objects.ingredient_types import INGREDIENT_TYPE
from cellpack.autopack.loaders.util import create_file_info_object_from_full_path
from cellpack.autopack.loaders.recipe_loader import RecipeLoader
from .v1_v2_attribute_changes import *

def convert_to_representations(old_ingredient):
        from cellpack.autopack.loaders.recipe_loader import RecipeLoader
        representations = RecipeLoader.default_values["representations"].copy()
        if "sphereFile" in old_ingredient and old_ingredient["sphereFile"] is not None:
            representations["packing"] = create_file_info_object_from_full_path(
                old_ingredient["sphereFile"]
            )
        if "meshFile" in old_ingredient and old_ingredient["meshFile"] is not None:
            representations["mesh"] = create_file_info_object_from_full_path(
                old_ingredient["meshFile"]
            )
            if (
                "coordsystem" in old_ingredient
                and old_ingredient["coordsystem"] is not None
            ):
                representations["mesh"]["coordinate_system"] = old_ingredient[
                    "coordsystem"
                ]
        if "pdb" in old_ingredient and old_ingredient["pdb"] is not None:
            if ".pdb" in old_ingredient["pdb"]:
                representations["atomic"] = {
                    "path": "default",
                    "name": old_ingredient["pdb"],
                    "format": ".pdb",
                }
            else:
                representations["atomic"] = {
                    "id": old_ingredient["pdb"],
                    "format": ".pdb",
                }
            if "source" in old_ingredient and "transform" in old_ingredient["source"]:
                representations["atomic"]["transform"] = old_ingredient["source"][
                    "transform"
                ]

        return representations

def convert_rotation_range(old_ingredient):
    range_min = (
        old_ingredient["orientBiasRotRangeMin"]
        if "orientBiasRotRangeMin" in old_ingredient
        else -pi
    )
    range_max = (
        old_ingredient["orientBiasRotRangeMax"]
        if "orientBiasRotRangeMax" in old_ingredient
        else pi
    )
    return [range_min, range_max]

def migrate_ingredient(old_ingredient):
        new_ingredient = {}
        for attribute in list(old_ingredient):
            if attribute in v1_to_v2_name_map:
                if attribute == "Type":
                    value = ingredient_types_map[old_ingredient[attribute]]
                else:
                    value = old_ingredient[attribute]
                new_ingredient[v1_to_v2_name_map[attribute]] = value
            elif attribute in unused_attributes_list:
                del old_ingredient[attribute]
            elif attribute in convert_to_partners_map:
                if "partners" not in new_ingredient:
                    partners = {}
                    new_ingredient["partners"] = partners
                partners[convert_to_partners_map[attribute]] = old_ingredient[attribute]
        new_ingredient["orient_bias_range"] = convert_rotation_range(
            old_ingredient
        )
        new_ingredient["representations"] = convert_to_representations(
            old_ingredient
        )
        if new_ingredient["type"] == INGREDIENT_TYPE.SINGLE_SPHERE:
            new_ingredient["radius"] = old_ingredient["radii"][0][0]
        return new_ingredient

def check_required_attributes(old_ingredient_data):
    if "Type" not in old_ingredient_data:
        old_ingredient_data["Type"] = "SingleSphere"
    ingr_type = old_ingredient_data["Type"]
    required = required_attributes[ingr_type]
    for attr in required:
        if attr not in old_ingredient_data:
            raise ValueError(f"{ingr_type} data needs {attr}")

def split_ingredient_data(object_key, ingredient_data):
    composition_info = {"object": object_key}
    object_info = ingredient_data.copy()
    for attribute in attributes_move_to_composition:
        if attribute in ingredient_data:
            composition_info[attribute] = ingredient_data[attribute]
            del object_info[attribute]
    return object_info, composition_info

def get_v1_ingredient(ingredient_key, ingredient_data, region_list, objects_dict):
        check_required_attributes(ingredient_data)
        converted_ingredient = migrate_ingredient(ingredient_data)
        object_info, composition_info = split_ingredient_data(
            ingredient_key, converted_ingredient
        )
        region_list.append(composition_info)
        objects_dict[ingredient_key] = object_info


def convert_v1_to_v2(recipe_data):
    objects_dict = {}
    composition = {"space": {"regions": {}}}
    if "cytoplasme" in recipe_data:
        outer_most_region_array = []
        composition["space"]["regions"]["interior"] = outer_most_region_array
        for ingredient_key in recipe_data["cytoplasme"]["ingredients"]:
            ingredient_data = recipe_data["cytoplasme"]["ingredients"][
                ingredient_key
            ]
            get_v1_ingredient(
                ingredient_key,
                ingredient_data,
                outer_most_region_array,
                objects_dict,
            )
    return objects_dict, composition

def migrate_version(self,recipe, format_version="1.0"):
        new_recipe = {}

        if format_version == "1.0":
            new_recipe["version"] = recipe["recipe"]["version"]
            new_recipe["format_version"] = self.current_version
            new_recipe["name"] = recipe["recipe"]["name"]
            new_recipe["bounding_box"] = recipe["options"]["boundingBox"]
            (
                new_recipe["objects"],
                new_recipe["composition"],
            ) = convert_v1_to_v2(recipe)
        return new_recipe
from math import pi
from cellpack.autopack import load_file

from cellpack.autopack.interface_objects.ingredient_types import INGREDIENT_TYPE
from cellpack.autopack.loaders.utils import create_file_info_object_from_full_path
from cellpack.autopack.interface_objects.default_values import default_recipe_values
from .v1_v2_attribute_changes import (
    convert_to_partners_map,
    required_attributes,
    v1_to_v2_name_map,
    attributes_move_to_composition,
    ingredient_types_map,
    unused_attributes_list,
)

"""
we will be able to load older version recipes by migrating them to the new schema.
we are converting each part of older version data to the new structure in this file
"""


def get_representations(old_ingredient):
    representations = default_recipe_values["representations"].copy()
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
            representations["mesh"]["coordinate_system"] = old_ingredient["coordsystem"]
    # compartment value
    if "geom" in old_ingredient or "rep_file" in old_ingredient:
        full_path = (
            old_ingredient["geom"]
            if "geom" in old_ingredient
            else old_ingredient["rep_file"]
        )
        representations["mesh"] = create_file_info_object_from_full_path(full_path)
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
        else:
            _covert_partners(old_ingredient, new_ingredient, attribute)
    new_ingredient["orient_bias_range"] = convert_rotation_range(old_ingredient)
    new_ingredient["representations"] = get_representations(old_ingredient)
    if new_ingredient["type"] == INGREDIENT_TYPE.SINGLE_SPHERE:
        new_ingredient["radius"] = old_ingredient["radii"][0][0]
    if "partners" in new_ingredient and not new_ingredient["partners"].get("names"):
        del new_ingredient["partners"]
    return new_ingredient


def _covert_partners(old_ingredient, new_ingredient, attribute):
    if attribute in convert_to_partners_map:
        if "partners" not in new_ingredient:
            partners = {}
            new_ingredient["partners"] = partners
        new_ingredient["partners"][convert_to_partners_map[attribute]] = old_ingredient[
            attribute
        ]


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


def get_and_store_v2_object(ingredient_key, ingredient_data, region_list, objects_dict):
    if "include" in ingredient_data:
        ingredient_data = load_file(ingredient_data["include"], cache="recipes")
    check_required_attributes(ingredient_data)
    converted_ingredient = migrate_ingredient(ingredient_data)
    object_info, composition_info = split_ingredient_data(
        ingredient_key, converted_ingredient
    )
    if len(composition_info) == 1:
        # Compartments will always be a key referencing another
        # object within the composition dictionary
        # Ingredients will be small dictionaries stored in an array
        region_list.append(ingredient_key)
    else:
        region_list.append(composition_info)
    objects_dict[ingredient_key] = object_info


def convert(old_recipe):
    new_recipe = {}

    new_recipe["format_version"] = "2.0"
    new_recipe["version"] = old_recipe["recipe"]["version"]
    new_recipe["name"] = old_recipe["recipe"]["name"]
    new_recipe["bounding_box"] = old_recipe["options"]["boundingBox"]
    objects_dict = {}
    # TODO: check if composition structure is correct
    composition = {"space": {"regions": {}}}
    if "cytoplasme" in old_recipe:
        outer_most_region_array = []
        composition["space"]["regions"]["interior"] = outer_most_region_array
        for ingredient_key in old_recipe["cytoplasme"]["ingredients"]:
            ingredient_data = old_recipe["cytoplasme"]["ingredients"][ingredient_key]
            get_and_store_v2_object(
                ingredient_key,
                ingredient_data,
                outer_most_region_array,
                objects_dict,
            )
    if "compartments" in old_recipe:
        for compartment_name in old_recipe["compartments"]:
            # add the compartment to composition
            compartment_data = old_recipe["compartments"][compartment_name]
            compartment_data["Type"] = "mesh"

            composition[compartment_name] = {"object": compartment_name, "regions": {}}
            get_and_store_v2_object(
                compartment_name,
                compartment_data,
                outer_most_region_array,
                objects_dict,
            )

            for region_name in compartment_data:
                # add region to composition
                if region_name == "surface":
                    surface_array = []
                    composition[compartment_name]["regions"][
                        region_name
                    ] = surface_array
                    for ingredient_key in compartment_data[region_name]["ingredients"]:
                        ingredient_data = compartment_data[region_name]["ingredients"][
                            ingredient_key
                        ]
                        get_and_store_v2_object(
                            ingredient_key,
                            ingredient_data,
                            surface_array,
                            objects_dict,
                        )

                if region_name == "interior":
                    interior_array = []
                    composition[compartment_name]["regions"][
                        region_name
                    ] = interior_array
                    for ingredient_key in compartment_data[region_name]["ingredients"]:
                        ingredient_data = compartment_data[region_name]["ingredients"][
                            ingredient_key
                        ]
                        get_and_store_v2_object(
                            ingredient_key,
                            ingredient_data,
                            interior_array,
                            objects_dict,
                        )

    if "gradients" in old_recipe:
        new_recipe["gradients"] = old_recipe["gradients"]

    new_recipe["objects"] = objects_dict
    new_recipe["composition"] = composition
    return new_recipe

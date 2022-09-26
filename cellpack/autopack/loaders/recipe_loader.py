# -*- coding: utf-8 -*-
import copy
from math import pi
import os

import json
from json import encoder

import cellpack.autopack as autopack
from cellpack.autopack.loaders.util import create_file_info_object_from_full_path
from cellpack.autopack.utils import deep_merge
from .v1_v2_attribute_changes import (
    ingredient_types,
    v1_to_v2_name_map,
    unused_attributes_list,
    convert_to_partners_map,
    attributes_move_to_composition,
)
from cellpack.autopack.interface_objects.representations import Representations

encoder.FLOAT_REPR = lambda o: format(o, ".8g")
CURRENT_VERSION = "2.0"


class RecipeLoader(object):
    # TODO: add all default values here
    default_values = {
        "bounding_box": [[0, 0, 0], [100, 100, 100]],
        "representations": {"atomic": None, "packing": None, "mesh": None},
    }

    def __init__(self, input_file_path):
        _, file_extension = os.path.splitext(input_file_path)
        self.current_version = CURRENT_VERSION
        self.file_path = input_file_path
        self.file_extension = file_extension
        self.ingredient_list = []
        self.compartment_list = []
        autopack.current_recipe_path = os.path.dirname(self.file_path)
        self.recipe_data = self._read()

    @staticmethod
    def is_key(key_or_dict, composition_dict):
        """
        Helper function to find if data in composition list
        is a key or an object
        """
        is_key = not isinstance(key_or_dict, dict)
        if is_key:
            key = key_or_dict
            if key not in composition_dict:
                raise ValueError(f"{key} is not in composition dictionary")
            composition_info = composition_dict[key]
        else:
            composition_info = key_or_dict
        return is_key, composition_info

    @staticmethod
    def create_output_dir(out_base_folder, recipe_name, sub_dir=None):
        os.makedirs(out_base_folder, exist_ok=True)
        output_folder = os.path.join(out_base_folder, recipe_name)
        if sub_dir is not None:
            output_folder = os.path.join(output_folder, sub_dir)
        os.makedirs(output_folder, exist_ok=True)
        return output_folder

    @staticmethod
    def _resolve_object(key, objects):
        current_object = objects[key]
        inherit_key = current_object["inherit"]
        base_object = objects[inherit_key]
        new_object = deep_merge(copy.deepcopy(base_object), current_object)
        objects[key] = new_object

    @staticmethod
    def _sort(key, visited, stack, edges):
        visited[key] = True
        for element in edges[key]:
            if visited[element] is False:
                RecipeLoader._sort(element, visited, stack, edges)
        stack.append(key)

    @staticmethod
    def _topological_sort(objects):
        edges = dict()
        for key, values in objects.items():
            if key not in edges:
                edges[key] = []
            if "inherit" in values:
                edges[key].append(values["inherit"])
                # "sphere_25": ["base"]
                # "sphere_50": ["sphere_25"]
                # "base": []
        stack = []
        visited = {key: False for key in objects}
        for key, value in objects.items():
            if visited[key] is False:
                RecipeLoader._sort(key, visited, stack, edges)
        return stack

    @staticmethod
    def resolve_inheritance(objects):
        stack = RecipeLoader._topological_sort(objects)
        for key in stack:
            if "inherit" in objects[key]:
                RecipeLoader._resolve_object(key, objects)
        return objects

    def _request_sub_recipe(self, inode):
        filename = None
        if inode is not None:
            if "include" in inode:
                filename = inode["include"]
        if filename is not None:
            filename = autopack.retrieveFile(
                filename,
                # destination = recipe+os.sep+"recipe"+os.sep+"ingredients"+os.sep,
                cache="recipes",
            )
            with open(filename, "r") as fp:  # doesnt work with symbol link ?
                data = json.load(fp)
        elif inode is not None:
            data = inode
        else:
            print("filename is None and not ingredient dictionary provided")
            return None
        return data

    @staticmethod
    def _convert_to_representations(old_ingredient):
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

    @staticmethod
    def _convert_rotation_range(old_ingredient):
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

    @staticmethod
    def _migrate_ingredient(old_ingredient):
        new_ingredient = {}
        for attribute in list(old_ingredient):
            if attribute in v1_to_v2_name_map:
                if attribute == "Type":
                    converted_value = ingredient_types.convert(
                        old_ingredient[attribute]
                    )
                    new_ingredient[
                        v1_to_v2_name_map[attribute]
                    ] = converted_value.get_key_name()
                else:
                    new_ingredient[v1_to_v2_name_map[attribute]] = old_ingredient[
                        attribute
                    ]
            elif attribute in unused_attributes_list:
                del old_ingredient[attribute]
            elif attribute in convert_to_partners_map:
                if "partners" not in new_ingredient:
                    partners = {}
                    new_ingredient["partners"] = partners
                partners[convert_to_partners_map[attribute]] = old_ingredient[attribute]
        new_ingredient["orient_bias_range"] = RecipeLoader._convert_rotation_range(
            old_ingredient
        )
        new_ingredient["representations"] = RecipeLoader._convert_to_representations(
            old_ingredient
        )
        print("new_ingredient", new_ingredient)
        return new_ingredient

    @staticmethod
    def _split_ingredient_data(object_key, ingredient_data):
        composition_info = {"object": object_key}
        object_info = ingredient_data.copy()
        for attribute in attributes_move_to_composition:
            if attribute in ingredient_data:
                composition_info[attribute] = ingredient_data[attribute]
                del object_info[attribute]
        return object_info, composition_info

    @staticmethod
    def _get_v1_ingredient(ingredient_key, ingredient_data, region_list, objects_dict):
        converted_ingredient = RecipeLoader._migrate_ingredient(ingredient_data)
        object_info, composition_info = RecipeLoader._split_ingredient_data(
            ingredient_key, converted_ingredient
        )
        region_list.append(composition_info)
        objects_dict[ingredient_key] = object_info

    @staticmethod
    def _convert_v1_to_v2(recipe_data):
        objects_dict = {}
        composition = {"space": {"regions": {}}}
        if "cytoplasme" in recipe_data:
            outer_most_region_array = []
            composition["space"]["regions"]["interior"] = outer_most_region_array
            for ingredient_key in recipe_data["cytoplasme"]["ingredients"]:
                ingredient_data = recipe_data["cytoplasme"]["ingredients"][
                    ingredient_key
                ]
                RecipeLoader._get_v1_ingredient(
                    ingredient_key,
                    ingredient_data,
                    outer_most_region_array,
                    objects_dict,
                )
        return objects_dict, composition

    @staticmethod
    def _migrate_version(recipe, current_version, format_version="1.0"):
        new_recipe = {}
        if format_version == "1.0":
            new_recipe["version"] = recipe["recipe"]["version"]
            new_recipe["format_version"] = current_version
            new_recipe["name"] = recipe["recipe"]["name"]
            new_recipe["bounding_box"] = recipe["options"]["boundingBox"]
            (
                new_recipe["objects"],
                new_recipe["composition"],
            ) = RecipeLoader._convert_v1_to_v2(recipe)
        return new_recipe

    def _read(self):
        new_values = json.load(open(self.file_path, "r"))
        recipe_data = RecipeLoader.default_values.copy()
        recipe_data = deep_merge(recipe_data, new_values)

        if (
            "format_version" not in recipe_data
            or recipe_data["format_version"] != self.current_version
        ):
            input_format_version = (
                recipe_data["format_version"]
                if "format_version" in recipe_data
                else "1.0"
            )
            recipe_data = RecipeLoader._migrate_version(
                recipe_data, input_format_version, self.current_version
            )

        # TODO: request any external data before returning
        if "objects" in recipe_data:
            recipe_data["objects"] = RecipeLoader.resolve_inheritance(
                recipe_data["objects"]
            )
            for _, obj in recipe_data["objects"].items():
                reps = obj["representations"] if "representations" in obj else {}
                obj["representations"] = Representations(
                    mesh=reps.get("mesh", None),
                    atomic=reps.get("atomic", None),
                    packing=reps.get("packing", None),
                )
        return recipe_data

    def _load_json(self):
        """
        Read in a Json Recipe.
        """
        sortkey = str.lower

        new_values = json.load(open(self.file_path, "r"))
        recipe_data = RecipeLoader.default_values.copy()
        recipe_data.update(new_values)
        # are there any custom paths
        if "paths" in recipe_data["recipe"]:
            custom_paths = recipe_data["recipe"]["paths"]
            autopack.updateReplacePath(custom_paths)

        autopack.current_recipe_path = self.file_path
        if (
            "format_version" not in recipe_data
            or recipe_data["format_version"] != self.current_version
        ):
            recipe_data = RecipeLoader._migrate_version(recipe_data)

        if "cytoplasme" in recipe_data:
            ingrs_dic = recipe_data["cytoplasme"]["ingredients"]
            if len(ingrs_dic):
                for ing_name in sorted(ingrs_dic, key=sortkey):  # ingrs_dic:
                    # either xref or defined
                    ing_dic = ingrs_dic[ing_name]
                    sub_recipe = self._request_sub_recipe(inode=ing_dic)
                    recipe_data["cytoplasme"]["ingredients"][ing_name] = sub_recipe
        if "compartments" in recipe_data:
            # use some include ?
            if len(recipe_data["compartments"]):
                # include all compartments from given filename.
                # transform the geometry of the compartment packing rep
                for cname in recipe_data["compartments"]:
                    if cname == "include":
                        for i, compartment in enumerate(
                            recipe_data["compartments"]["include"]
                        ):
                            node = {"include": compartment["from"]}
                            sub_recipe = self._request_sub_recipe(inode=node)
                            recipe_data["compartments"][
                                compartment["from"]
                            ] = sub_recipe["compartments"]
                        continue
                    compartment_dict = recipe_data["compartments"][cname]
                    rep = None
                    if "rep" in compartment_dict:
                        rep = str(compartment_dict["rep"])
                    rep_file = ""
                    if "rep_file" in compartment_dict:
                        rep_file = str(compartment_dict["rep_file"])
                    #                print (len(rep),rep == '',rep=="",rep != "None",rep != "None" or len(rep) != 0)
                    if rep is not None and len(rep) != 0 and rep != "" and rep != "":
                        rname = rep_file.split("/")[-1]
                        fileName, fileExtension = os.path.splitext(rname)
                        if fileExtension == "":
                            rep_file = rep_file + fileExtension
                        else:
                            rep_file = rep_file + "." + fileExtension
                    else:
                        rep = None
                        rep_file = None

                    if "surface" in compartment_dict:
                        snode = compartment_dict["surface"]
                        ingrs_dic = snode["ingredients"]
                        if len(ingrs_dic):
                            for ing_name in sorted(
                                ingrs_dic, key=sortkey
                            ):  # ingrs_dic:
                                # either xref or defined
                                ing_dic = ingrs_dic[ing_name]
                                sub_recipe = self._request_sub_recipe(inode=ing_dic)
                                compartment_dict["surface"]["ingredients"][
                                    ing_name
                                ] = sub_recipe

                                # setup recipe
                    if "interior" in compartment_dict:
                        snode = compartment_dict["interior"]
                        ingrs_dic = snode["ingredients"]
                        if len(ingrs_dic):
                            for ing_name in sorted(
                                ingrs_dic, key=sortkey
                            ):  # ingrs_dic:
                                # either xref or defined
                                ing_dic = ingrs_dic[ing_name]
                                sub_recipe = self._request_sub_recipe(inode=ing_dic)
                                compartment_dict["interior"]["ingredients"][
                                    ing_name
                                ] = sub_recipe

        return recipe_data

    def get_all_ingredients(self, results_data_in):
        all_ingredients = []
        recipe_data = self.recipe_data
        if "cytoplasme" in results_data_in:
            if len(results_data_in["cytoplasme"]["ingredients"]) != 0:
                for ingredient in results_data_in["cytoplasme"]["ingredients"]:
                    all_ingredients.append(
                        {
                            "results": results_data_in["cytoplasme"]["ingredients"][
                                ingredient
                            ],
                            "recipe_data": recipe_data["cytoplasme"]["ingredients"][
                                ingredient
                            ],
                        }
                    )
        if "compartments" in results_data_in:
            for compartment in results_data_in["compartments"]:
                current_compartment = results_data_in["compartments"][compartment]
                if "surface" in current_compartment:
                    for ingredient in current_compartment["surface"]["ingredients"]:
                        all_ingredients.append(
                            {
                                "results": current_compartment["surface"][
                                    "ingredients"
                                ][ingredient],
                                "recipe_data": recipe_data["compartments"][compartment][
                                    "surface"
                                ]["ingredients"][ingredient],
                            }
                        )
                if "interior" in current_compartment:
                    for ingredient in current_compartment["interior"]["ingredients"]:
                        all_ingredients.append(
                            {
                                "results": current_compartment["interior"][
                                    "ingredients"
                                ][ingredient],
                                "recipe_data": recipe_data["compartments"][compartment][
                                    "interior"
                                ]["ingredients"][ingredient],
                            }
                        )
        return all_ingredients

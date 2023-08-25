# -*- coding: utf-8 -*-
import copy
import os

import json
from json import encoder


import cellpack.autopack as autopack
from cellpack.autopack.interface_objects.ingredient_types import INGREDIENT_TYPE
from cellpack.autopack.interface_objects.partners import Partners
from cellpack.autopack.utils import deep_merge, expand_object_using_key
from cellpack.autopack.interface_objects import (
    Representations,
    default_recipe_values,
    GradientData,
)
from cellpack.autopack.loaders.migrate_v1_to_v2 import convert as convert_v1_to_v2
from cellpack.autopack.loaders.migrate_v2_to_v2_1 import convert as convert_v2_to_v2_1

encoder.FLOAT_REPR = lambda o: format(o, ".8g")
CURRENT_VERSION = "2.1"


class RecipeLoader(object):
    # TODO: add all default values here
    default_values = default_recipe_values.copy()

    def __init__(self, input_file_path, db_handler=None, save_converted_recipe=False):
        _, file_extension = os.path.splitext(input_file_path)
        self.current_version = CURRENT_VERSION
        self.file_path = input_file_path
        self.db_handler = db_handler
        self.file_extension = file_extension
        self.ingredient_list = []
        self.compartment_list = []
        self.save_converted_recipe = save_converted_recipe
        autopack.CURRENT_RECIPE_PATH = os.path.dirname(self.file_path)
        self.recipe_data = self._read()

    @staticmethod
    def _resolve_object(key, objects):
        current_object = objects[key]
        new_object = expand_object_using_key(current_object, "inherit", objects)
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
            filename = autopack.get_local_file_location(
                filename,
                # destination = recipe+os.sep+"recipe"+os.sep+"ingredients"+os.sep,
                cache="recipes",
            )
            with open(filename, "r") as fp:  # doesn't work with symbol link ?
                data = json.load(fp)
        elif inode is not None:
            data = inode
        else:
            print("filename is None and not ingredient dictionary provided")
            return None
        return data

    def _save_converted_recipe(self, data):
        """
        Save converted recipe into a json file
        """
        path = autopack.CURRENT_RECIPE_PATH
        filename = data["name"]
        out_directory = f"{path}/converted/"
        if not os.path.exists(out_directory):
            os.makedirs(out_directory)
        full_path = f"{out_directory}/{filename}_fv{self.current_version}.json"
        with open(full_path, "w") as f:
            json.dump(data, f, indent=4)
        f.close()

    @staticmethod
    def _sanitize_format_version(recipe_data):
        if "format_version" not in recipe_data:
            format_version = "1.0"  # all recipes before we introduced versioning
        elif len(recipe_data["format_version"].split(".")) > 2:
            # We only use two places for format version, but people
            # might accidentally include a third number
            # ie 2.0.0 instead of 2.0
            split_numbers = recipe_data["format_version"].split(".")
            format_version = f"{split_numbers[0]}.{split_numbers[1]}"
        elif len(recipe_data["format_version"].split(".")) == 1:
            # We only use two places for format version, but people
            # might accidently include a third number
            # ie 2.0.0 instead of 2.0
            split_numbers = recipe_data["format_version"].split(".")
            format_version = f"{split_numbers[0]}.0"
        else:
            format_version = recipe_data["format_version"]
        return format_version

    def get_only_recipe_metadata(self):
        recipe_meta_data = {
            "format_version": self.recipe_data["format_version"],
            "version": self.recipe_data["version"],
            "name": self.recipe_data["name"],
            "bounding_box": self.recipe_data["bounding_box"],
            "composition": {},
        }
        return recipe_meta_data

    def _migrate_version(self, old_recipe):
        converted = False
        if old_recipe["format_version"] == "1.0":
            converted = True
            new_recipe = convert_v1_to_v2(old_recipe)
            old_recipe = copy.deepcopy(new_recipe)

        if old_recipe["format_version"] == "2.0":
            new_recipe = copy.deepcopy(old_recipe)
            converted = True

            new_recipe = convert_v2_to_v2_1(old_recipe)

        if converted:
            if self.save_converted_recipe:
                self._save_converted_recipe(new_recipe)

            return new_recipe

        else:
            raise ValueError(
                f"{old_recipe['format_version']} is not a format version we support"
            )

    @staticmethod
    def _get_grad_and_obj(obj_data, obj_dict, grad_dict):
        try:
            grad_name = obj_data["gradient"]["name"]
            obj_name = obj_data["name"]
        except KeyError as e:
            print(f"Missing keys in object: {e}")
            return obj_dict, grad_dict

        grad_dict[grad_name] = obj_data["gradient"]
        obj_dict[obj_name]["gradient"] = grad_name
        return obj_dict, grad_dict

    @staticmethod
    def _is_obj(comp_or_obj):
        # if the top level of a downloaded comp doesn't have the key `name`, it's an obj
        # TODO: true for all cases? better approaches?
        return not comp_or_obj.get("name") and "object" in comp_or_obj

    @staticmethod
    def _collect_and_sort_data(comp_data):
        """
        Collect all object and gradient info from the downloaded firebase composition data
        Return autopack object data dict and gradient data dict with name as key
        Return restructured composition dict with "composition" as key
        """
        objects = {}
        gradients = {}
        composition = {}
        for comp_name, comp_value in comp_data.items():
            composition[comp_name] = {}
            if "count" in comp_value and comp_value["count"] is not None:
                composition[comp_name]["count"] = comp_value["count"]
            if "object" in comp_value and comp_value["object"] is not None:
                composition[comp_name]["object"] = comp_value["object"]["name"]
                object_copy = copy.deepcopy(comp_value["object"])
                objects[object_copy["name"]] = object_copy
                if "gradient" in object_copy and isinstance(
                    object_copy["gradient"], dict
                ):
                    objects, gradients = RecipeLoader._get_grad_and_obj(
                        object_copy, objects, gradients
                    )
            if "regions" in comp_value and comp_value["regions"] is not None:
                for region_name in comp_value["regions"]:
                    composition[comp_name].setdefault("regions", {})[region_name] = []
                    for region_item in comp_value["regions"][region_name]:
                        if RecipeLoader._is_obj(region_item):
                            composition[comp_name]["regions"][region_name].append(
                                {
                                    "object": region_item["object"].get("name"),
                                    "count": region_item.get("count"),
                                }
                            )
                            object_copy = copy.deepcopy(region_item["object"])
                            objects[object_copy["name"]] = object_copy
                            if "gradient" in object_copy and isinstance(
                                object_copy["gradient"], dict
                            ):
                                objects, gradients = RecipeLoader._get_grad_and_obj(
                                    object_copy, objects, gradients
                                )
                        else:
                            composition[comp_name]["regions"][region_name].append(
                                region_item["name"]
                            )
        return objects, gradients, composition

    @staticmethod
    def _compile_recipe_from_firebase(db_recipe_data, obj_dict, grad_dict, comp_dict):
        """
        Compile recipe data from firebase recipe data into a ready-to-pack structure
        """
        recipe_data = {
            **{
                k: db_recipe_data[k]
                for k in ["format_version", "version", "name", "bounding_box"]
            },
            "objects": obj_dict,
            "composition": comp_dict,
        }
        if grad_dict:
            recipe_data["gradients"] = [{**v} for v in grad_dict.values()]
        return recipe_data

    def _read(self):
        new_values, database_name = autopack.load_file(
            self.file_path, self.db_handler, cache="recipes"
        )
        if database_name == "firebase":
            objects, gradients, composition = RecipeLoader._collect_and_sort_data(
                new_values["composition"]
            )
            new_values = RecipeLoader._compile_recipe_from_firebase(
                new_values, objects, gradients, composition
            )
        recipe_data = RecipeLoader.default_values.copy()
        recipe_data = deep_merge(recipe_data, new_values)
        recipe_data["format_version"] = RecipeLoader._sanitize_format_version(
            recipe_data
        )
        if recipe_data["format_version"] != self.current_version:
            recipe_data = self._migrate_version(recipe_data)

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
                # the key "all_partners" exists in obj["partners"] if the recipe is downloaded from a remote db
                partner_settings = (
                    []
                    if (
                        "partners" in obj
                        and "all_partners" in obj["partners"]
                        and not obj["partners"]["all_partners"]
                    )
                    else obj.get("partners", [])
                )
                obj["partners"] = Partners(partner_settings)
                if "type" in obj and not INGREDIENT_TYPE.is_member(obj["type"]):
                    raise TypeError(f"{obj['type']} is not an allowed type")

        # handle gradients
        # gradients in firebase recipes are already stored as a list of dicts
        if "gradients" in recipe_data and not isinstance(
            recipe_data["gradients"], list
        ):
            gradients = []
            for gradient_name, gradient_dict in recipe_data["gradients"].items():
                gradients.append(GradientData(gradient_dict, gradient_name).data)
            recipe_data["gradients"] = gradients
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

        autopack.CURRENT_RECIPE_PATH = self.file_path
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

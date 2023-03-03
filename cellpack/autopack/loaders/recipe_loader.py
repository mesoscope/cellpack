# -*- coding: utf-8 -*-
import os

import json
from json import encoder

import cellpack.autopack as autopack
from cellpack.autopack.interface_objects.ingredient_types import INGREDIENT_TYPE
from cellpack.autopack.utils import deep_merge, expand_object_using_key
from cellpack.autopack.interface_objects import Representations, default_recipe_values, GradientData
from cellpack.autopack.loaders.migrate_v1_to_v2 import convert

encoder.FLOAT_REPR = lambda o: format(o, ".8g")
CURRENT_VERSION = "2.0"


class RecipeLoader(object):
    # TODO: add all default values here
    default_values = default_recipe_values.copy()

    def __init__(self, input_file_path, save_converted_recipe=False):
        _, file_extension = os.path.splitext(input_file_path)
        self.current_version = CURRENT_VERSION
        self.file_path = input_file_path
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

    def _migrate_version(self, recipe):
        new_recipe = {}

        if recipe["format_version"] == "1.0":
            new_recipe["version"] = recipe["recipe"]["version"]
            new_recipe["format_version"] = self.current_version
            new_recipe["name"] = recipe["recipe"]["name"]
            new_recipe["bounding_box"] = recipe["options"]["boundingBox"]
            (
                new_recipe["objects"],
                new_recipe["composition"],
            ) = convert(recipe)
            if self.save_converted_recipe:
                self._save_converted_recipe(new_recipe)
        else:
            raise ValueError(
                f"{recipe['format_version']} is not a format version we support"
            )
        return new_recipe

    def _read(self):
        new_values = autopack.load_file(self.file_path, cache="recipes")
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
            if not INGREDIENT_TYPE.is_member(obj["type"]):
                raise TypeError(f"{obj['type']} is not an allowed type")
            
        # handle gradients
        if "gradients" in recipe_data:
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

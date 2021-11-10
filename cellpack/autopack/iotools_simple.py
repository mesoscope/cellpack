# -*- coding: utf-8 -*-
"""
Created on Sun Jan 27 09:04:10 2013

@author: Ludovic Autin
"""
import os

import json
from json import encoder

import cellpack.autopack as autopack

encoder.FLOAT_REPR = lambda o: format(o, ".8g")


class RecipeLoader(object):
    def __init__(self, input_file_path):
        _, file_extension = os.path.splitext(input_file_path)
        self.file_path = input_file_path
        self.file_extension = file_extension

    def read(self):
        if self.file_extension == ".xml":
            pass  # self.load_XML(setupfile)
        elif self.file_extension == ".py":  # execute ?
            pass  # return IOutils.load_Python(env,setupfile)
        elif self.file_extension == ".json":
            return self._load_json()

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

    def _load_json(self):
        """
        Read in a Json Recipe.
        """
        sortkey = str.lower

        recipe_data = json.load(open(self.file_path, "r"))
        # is there any cutoms paths
        if "paths" in recipe_data["recipe"]:
            custom_paths = recipe_data["recipe"]["paths"]
            autopack.updateReplacePath(custom_paths)

        autopack.current_recipe_path = self.file_path

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
                    # if cname == "include":
                    #     for i, ncompart in enumerate(
                    #         recipe_data["compartments"]["include"]
                    #     ):
                            # sub_recipe = 
                    comp_dic = recipe_data["compartments"][cname]
  
                    if "rep" in comp_dic:
                        rep = str(comp_dic["rep"])
                    rep_file = ""
                    if "rep_file" in comp_dic:
                        rep_file = str(comp_dic["rep_file"])
                    #                print (len(rep),rep == '',rep=="",rep != "None",rep != "None" or len(rep) != 0)
                    if rep != "None" and len(rep) != 0 and rep != "" and rep != "":
                        rname = rep_file.split("/")[-1]
                        fileName, fileExtension = os.path.splitext(rname)
                        if fileExtension == "":
                            rep_file = rep_file + fileExtension
                        else:
                            rep_file = rep_file + "." + fileExtension
                    else:
                        rep = None
                        rep_file = None

                    if "surface" in comp_dic:
                        snode = comp_dic["surface"]
                        ingrs_dic = snode["ingredients"]
                        if len(ingrs_dic):
                            for ing_name in sorted(ingrs_dic, key=sortkey):  # ingrs_dic:
                                # either xref or defined
                                ing_dic = ingrs_dic[ing_name]
                                sub_recipe = self._request_sub_recipe(inode=ing_dic)
                                comp_dic["surface"]["ingredients"][ing_name] = sub_recipe

                                # setup recipe
                    if "interior" in comp_dic:
                        snode = comp_dic["interior"]
                        ingrs_dic = snode["ingredients"]
                        if len(ingrs_dic):
                            for ing_name in sorted(ingrs_dic, key=sortkey):  # ingrs_dic:
                                # either xref or defined
                                ing_dic = ingrs_dic[ing_name]
                                sub_recipe = self._request_sub_recipe(inode=ing_dic)
                                comp_dic["interior"]["ingredients"][ing_name] = sub_recipe

                    return recipe_data
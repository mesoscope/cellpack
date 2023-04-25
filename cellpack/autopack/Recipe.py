# -*- coding: utf-8 -*-
"""
############################################################################
#
# autoPACK Authors: Graham T. Johnson, Mostafa Al-Alusi, Ludovic Autin,
# and Michel Sanner
#   Based on COFFEE Script developed by Graham Johnson between 2005 and 2010
#   with assistance from Mostafa Al-Alusi in 2009 and periodic input
#   from Arthur Olson's Molecular Graphics Lab
#
# Recipe.py Authors: Graham Johnson & Michel Sanner with editing/
# enhancement from Ludovic Autin
#
# Translation to Python initiated March 1, 2010 by Michel Sanner
# with Graham Johnson
#
# Class restructuring and organization: Michel Sanner
#
# This file "Recipe.py" is part of autoPACK, cellPACK.
#
#    autoPACK is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    autoPACK is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with autoPACK (See "CopyingGNUGPL" in the installation.
#    If not, see <http://www.gnu.org/licenses/>.
#
############################################################################
@author: Graham Johnson, Ludovic Autin, & Michel Sanner

# Hybrid version merged from Graham's Sept 6, 2011 and Ludo's April 2012
#version on May 16, 2012, re-merged on July 5, 2012 with thesis versions
"""

import logging
from random import random, seed


class Recipe:
    """
    a recipe provides ingredients that are each defining a protein identity
    along with radius and molarity for this protein.
    """

    def __init__(self, name="ext"):
        self.log = logging.getLogger("recipe")
        self.ingredients = []
        self.activeIngredients = []
        self.compartment = None  # the weeek ref ?
        # will be set when recipe is added to compartment
        self.exclude = []
        self.number = 0
        self.name = name

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
    def resolve_composition(recipe_data):
        composition_dict = recipe_data["composition"]
        # keys in reference_dict are downstream objects,
        # values in reference_dict refer to the immediate upstream object of the key
        reference_dict = {}
        # compartment_keys contains a list of keys of objects that act as compartments
        compartment_keys = []
        referenced_objects = []
        for key, entry in composition_dict.items():
            for _, obj_keys in entry.get(
                "regions", {}
            ).items():  # check if entry in compositions has regions
                if (
                    key not in compartment_keys
                ):  # add to compartment_keys if regions exist
                    compartment_keys.append(key)
                for obj_key in obj_keys:
                    if not isinstance(obj_key, dict):
                        reference_dict[obj_key] = key
                        referenced_objects.append(obj_key)
                    else:
                        obj_key = obj_key["object"]
                        referenced_objects.append(obj_key)

        root = set(composition_dict.keys()).difference(set(reference_dict.keys()))

        if len(root) > 1:
            root = list(root)
            root.sort()  # alphabetize for consisent testing
            raise Exception(f"Composition has multiple roots {root}")

        return (list(root)[0], compartment_keys, reference_dict, referenced_objects)

    def delIngredient(self, ingr):
        """remove the given ingredient from the recipe"""
        if ingr in self.ingredients:
            ind = self.ingredients.index(ingr)
            self.ingredients.pop(ind)
        if ingr not in self.exclude:
            self.exclude.append(ingr)

    def addIngredient(self, ingr):
        """add the given ingredient from the recipe"""
        if ingr.name.find(self.name) == -1:
            ingr.name = self.name + "_" + ingr.name
        # I'd like to turn this off but it breaks the GUI's ability to turn off
        # ingredients with the checkboxes and packs everything everytime if this is off.
        # Right now the ingredients become way too long with it on.
        if ingr not in self.ingredients:
            self.ingredients.append(ingr)
        ingr.recipe = self
        if ingr in self.exclude:
            ind = self.exclude.index(ingr)
            self.exclude.pop(ind)
        self.log.info("add ingredient %s", ingr.name)

    def setCount(self, volume, reset=True, **kw):  # area=False,
        """set the count of n of molecule for every ingredients
        in the recipe, and push them in te activeIngredient list
        David and Graham independently worked out and corrected the molarity calculation for Å as shown in the following lines
        M = moles/L
        6.022e23 ingredients/mole

        uPy works in Å by default (not ideal for mesoscale, but works with all molecular viewers that way), so given a volume in Å^3
        1L = (10cm)^3
        1cm = 10^(-2)m
        1Å = 10^(-10)m
        1cm = 10^(8)Å
        10cm = 10^(9)Å
        1L = (10cm)^3 = (10^(9)Å)^3 = 10^(27)Å^3

        M = 6.022x10^23/L = [6.022x10^23] / [10^(27)Å^3] = 6.022x10(-4)ing/Å^3
        numberIngredientsToPack = [0.0006022 ing/Å^3] * [volume Å^3]

        volume / ingredient in 1M = 1ing / 0.0006022 ing/Å^3 = 1660Å^3 * 1nm^3/1000Å^3 = 1.6nm^3

        Average distance between molecules is cubic root 3√(1.6nm^3) = 11.8Å = 1.18nm
        Thus the nbr should simply be
        nbr = densityInMolarity*[0.0006022 ing/Å^3] * [volume Å^3]
        see http://molbiol.edu.ru/eng/scripts/01_04.html
        http://www.ncbi.nlm.nih.gov/pmc/articles/PMC3910158/
        http://book.bionumbers.org/
        """
        seedNum = 14
        seed(seedNum)
        # this now allows consistent refilling via seed)
        # compute number of molecules for a given volume
        for i, ingr in enumerate(self.ingredients):
            # 6.02 / 10000)# 1x10^27 / 1x10^23 = 10000
            if reset:
                ingr.reset()
            # Overridden by next 18 lines marked Mod
            # by Graham 8/18/11 into Hybrid on 5/16/12
            # Mod by Graham 8/18/11: Needed this to give
            # ingredients an increasing chance to add one more molecule
            # based on modulus proximity to the next integer
            # Molarity = No. of molecules /(N X V)
            # doesnt seem to work anymore
            # =B7*POWER(10, 27)/100/1000/(6.0221415*POWER(10,23))
            # this eqauation seems wrong, it work for volume unit in m^3
            #            nbr = ingr.molarity * volume * .000602 #Mod by Graham 8/18/11
            # we work in angstrom->L->m
            # vnm is volume in nm^3
            # replace by 10e30 for angstrom^3
            # molarity = (nbr*10e27)/vnm/1000.0/(6.022*10e23) M
            # nbr = molarity*((6.022*10e23)*vnm*1000)/10e27   molecule
            # specific for M (mol / L) in a volume in Angstrom
            #            nbr = ingr.molarity * (volume/10e6) * 1000 * 0.000602
            #            nbi = int(nbr)              #Mod by Graham 8/18/11
            num_to_place_float = ingr.molarity * 0.0006022 * volume
            num_to_place_int = int(num_to_place_float)  # Mod by Graham 8/18/11
            remainder = (
                num_to_place_float % num_to_place_int
                if num_to_place_int != 0
                else num_to_place_float
            )

            # some chance that the fraction over the integer will result in another ingr being placed
            randval = random()
            if remainder >= randval:  # Mod by Graham 8/18/11
                num_to_place_int = num_to_place_int + 1

            ingr.vol_nbmol = ingr.left_to_place = num_to_place_int + ingr.count
            if ingr.left_to_place == 0:
                self.log.warning(
                    "WARNING GRAHAM: recipe ingredient %s has 0 molecules as target",
                    ingr.name,
                )
            else:
                self.activeIngredients.append(i)

    def resetIngrs(
        self,
    ):
        """reset the states of all recipe ingredients"""
        for ingr in self.ingredients:
            ingr.reset()

    def getMinMaxProteinSize(self):
        """get the mini and maxi radius from all recipe ingredients"""
        mini = 9999999.0
        maxi = 0

        for ingr in self.ingredients:
            if ingr.encapsulating_radius is None:
                ingr.encapsulating_radius = 400.0
            if ingr.encapsulating_radius > maxi:
                maxi = ingr.encapsulating_radius
            if ingr.min_radius < mini:
                mini = ingr.min_radius
        return mini, maxi

    def sort(self):
        """sort the ingredients using the min Radius"""
        # sort tuples in molecule list according to radius
        self.ingredients.sort(key=lambda x: x.min_radius)

    def printFillInfo(self, indent=""):
        """print the states of all recipe ingredients"""
        for ingr in self.ingredients:
            print(
                indent
                + "ingr: %s target: %3d placed %3d %s"
                % (ingr.pdb, ingr.left_to_place, ingr.counter, ingr.name)
            )

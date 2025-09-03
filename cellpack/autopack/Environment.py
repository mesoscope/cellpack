# -*- coding: utf-8 -*-
"""
autoPACK Authors: Graham T. Johnson, Mostafa Al-Alusi, Ludovic Autin, Michel Sanner
  Based on COFFEE Script developed by Graham Johnson between 2005 and 2010
  with assistance from Mostafa Al-Alusi in 2009 and periodic input
  from Arthur Olson's Molecular Graphics Lab

Environment.py Authors: Graham Johnson & Michel Sanner with editing/enhancement
from Ludovic Autin

HistoVol.py became Environment.py in the Spring of 2013 to generalize the terminology
away from biology

Translation to Python initiated March 1, 2010 by Michel Sanner with Graham Johnson

Class restructuring and organization: Michel Sanner

Copyright: Graham Johnson ©2010

This file "Environment.py" is part of autoPACK, cellPACK.
   autoPACK is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.
   autoPACK is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.
   You should have received a copy of the GNU General Public License
   along with autoPACK (See "CopyingGNUGPL" in the installation.
   If not, see <http://www.gnu.org/licenses/>.

@author: Graham Johnson, Ludovic Autin, & Michel Sanner

Hybrid version merged from Graham's Sept 2011 and Ludo's April 2012
version on May 16, 2012
Updated with final thesis HistoVol.py file from Sept 25, 2012 on July 5, 2012
with correct analysis tools
"""

import json
import logging
import os
import pickle
from collections import OrderedDict
from random import random, seed, uniform
from time import time
from typing import Any, Dict, List, Optional, Tuple, Union

from cellpack.autopack.ingredient.Ingredient import Ingredient
import numpy as np
from scipy.spatial import KDTree
from tqdm import tqdm

import cellpack.autopack as autopack
import cellpack.autopack.ingredient as ingredient
from cellpack.autopack import IOutils, get_cache_location, get_local_file_location
from cellpack.autopack.BaseGrid import BaseGrid as BaseGrid
from cellpack.autopack.interface_objects.packed_objects import PackedObjects
from cellpack.autopack.loaders.utils import create_output_dir
from cellpack.autopack.MeshStore import MeshStore
from cellpack.autopack.utils import (
    cmp_to_key,
    expand_object_using_key,
    get_max_value_from_distribution,
    get_min_value_from_distribution,
    get_value_from_distribution,
    ingredient_compare0,
    ingredient_compare1,
    ingredient_compare2,
)
from cellpack.autopack.writers import Writer

from .Compartment import Compartment, CompartmentList
from .Gradient import Gradient
from .ingredient import ActinIngredient, GrowIngredient
from .octree import Octree
from .randomRot import RandomRot
from .Recipe import Recipe

try:
    helper = autopack.helper
except ImportError:
    helper = None


# set default pickle protocol to highest level
pickle.DEFAULT_PROTOCOL = pickle.HIGHEST_PROTOCOL

SEED = 15
verbose = 0

log = logging.getLogger("env")


class Environment(CompartmentList):
    """
    The Environment class
    ==========================
    This class is main class in autopack. The class handle all the setup, initialization
    and process of the packing. We use xml or python for the setup.
    A environments is made of :
        a grid and the gradients if any
        a list of compartment and their recipes (surface and interior)
        a exterior recipe
        each recipe are made of a list of ingredients
    """

    def __init__(self, config: Dict, recipe: Dict) -> None:
        """
        Initialize the Environment with configuration and recipe data.

        Parameters
        ----------
        config
            Configuration dictionary containing packing parameters
        recipe
            Recipe dictionary containing environment specifications
        """
        CompartmentList.__init__(self)
        self.mesh_store = MeshStore()

        self.config_data = config
        self.recipe_data = recipe
        name = recipe["name"]
        self.log = logging.getLogger("env")
        self.log.propagate = False

        # From config file
        self.runTimeDisplay = config["live_packing"]
        self.place_method = config["place_method"]
        self.innerGridMethod = config["inner_grid_method"]
        self.format_output = config["format"]
        self.use_periodicity = config["use_periodicity"]
        self.overwrite_place_method = config["overwrite_place_method"]
        self.pickRandPt = not config["ordered_packing"]
        self.show_sphere_trees = config["show_sphere_trees"]
        self.show_grid_spheres = config["show_grid_plot"]
        self.boundingBox = np.array(recipe["bounding_box"])
        self.spacing = config["spacing"]
        self.load_from_grid_file = config["load_from_grid_file"]
        self.show_progress_bar = config["show_progress_bar"]
        self.name = name
        self.version = recipe.get("version", "default")
        # saving/pickle option
        self.saveResult = (
            "out" in config
            and not config["save_analyze_result"]
            and not config["number_of_packings"] > 1
        )
        self.out_folder = create_output_dir(config["out"], name, config["place_method"])
        self.base_name = f"{self.name}_{config['name']}_{self.version}"
        self.grid_file_out = (
            f"{self.out_folder}/{self.name}_{config['name']}_{self.version}_grid.dat"
        )
        self.previous_grid_file = None
        if self.load_from_grid_file:
            # first check if grid file path is specified in recipe
            if recipe.get("grid_file_path") is not None:
                self.grid_file_out = get_local_file_location(
                    recipe["grid_file_path"], cache="grids"
                )
            # check if grid file is already present in the output folder
            if os.path.isfile(self.grid_file_out):
                self.previous_grid_file = self.grid_file_out
        self.setupfile = ""
        self.current_path = None  # the path of the recipe file
        self.custom_paths = None
        self.grid_filename = None  #
        self.grid_result_filename = None  # str(gridn.getAttribute("grid_result"))

        self.timeUpDistLoopTotal = 0
        self.exteriorRecipe = None
        self.hgrid = []
        self.octree = None  # ongoing octree test, no need if openvdb wrapped to python
        self.grid = None  # Grid()  # the main grid
        self.encapsulatingGrid = (
            0  # Only override this with 0 for 2D packing- otherwise its very unsafe!
        )
        # 0 is the exterior, 1 is compartment 1 surface, -1 is compartment 1 interior
        self.nbCompartments = 1
        self.number = 0  # TODO: call this 'id' consistent with container
        self.order = {}  # give the order of drop ingredient by ptInd from molecules
        self.lastrank = 0

        # smallest and largest protein radii across all recipes
        self.smallestProteinSize = 999
        self.largestProteinSize = 0
        self.scaleER = 2.5  # hack in case problem with encapsulating radius
        self.computeGridParams = True

        self.EnviroOnly = False
        self.EnviroOnlyCompartiment = -1
        # bounding box of the Environment

        self.fbox_bb = None  # used for estimating the volume

        self.fbox = None  # Oct 20, 2012 Graham wonders if this is part of the problem
        self.fillBB = None  # bounding box for a given fill
        self.fillbb_insidepoint = (
            None  # Oct 20, 2012 Graham wonders if this is part of the problem
        )
        self.freePointMask = None

        self.randomRot = RandomRot()  # the class used to generate random rotation
        self.activeIngr = []
        self.activeIngre_saved = []
        self.freePtsUpdateThreshold = 0.0
        # optionally can provide a host and a viewer
        self.host = None
        self.afviewer = None

        # option for packing using host dynamics capability
        self.windowsSize = 100
        self.windowsSize_overwrite = False

        self.orthogonalBoxType = 0
        self.rejection_threshold = None
        # if use C4D RB dynamics, should be genralized
        self.springOptions = {}
        self.dynamicOptions = {}
        self.setupRBOptions()
        self.simulationTimes = 2.0

        # cancel dialog-> need to be develop more
        self.cancelDialog = False

        self.grab_cb = None
        self.pp_server = None
        self.seed_set = False
        self.seed_used = 0
        #
        self.nFill = 0
        self.cFill = 0
        self.FillName = ["F" + str(self.nFill)]

        self.traj_linked = False
        # do we sort the ingredient or not see  getSortedActiveIngredients
        self.pickWeightedIngr = True
        self.currtId = 0

        # gradient
        self.gradients = {}
        self.use_gradient = len(recipe.get("gradients", {})) > 0
        self.use_halton = False  # use halton for grid point distribution

        self.ingrLookForNeighbours = False  # Old Features to be test

        # debug with timer function
        self.nb_ingredient = 0
        self.totalNbIngr = 0
        self.treemode = "KDTree"
        self.close_ingr_bhtree = (
            None  # RBHTree(a.tolist(),range(len(a)),10,10,10,10,10,9999)
        )

        self.packed_objects = PackedObjects()

        # should be part of an independent module
        # could be a problem here for pp
        # can't pickle this dictionary
        self.rb_func_dic = {}
        # need options for the save/server data etc....
        # should it be in __init__ like other general options ?
        self.dump = False
        self.dump_freq = 120.0
        self.jsondic = None

        self.distancesAfterFill = []
        self.freePointsAfterFill = []
        self.nbFreePointsAfterFill = []
        self.distanceAfterFill = []
        self._setup()

    def _setup(self) -> None:
        """
        Setup the environment by resolving composition and creating objects.
        """
        if "composition" in self.recipe_data:
            (
                self.root_compartment,
                self.compartment_keys,
                self.reference_dict,
                self.referenced_objects,
            ) = Recipe.resolve_composition(self.recipe_data)
            self.create_objects()
        if self.use_gradient:
            for gradient_data in self.recipe_data["gradients"]:
                self.set_gradient(gradient_data)

    def clean_grid_cache(self, grid_file_name: str) -> None:
        """
        Clean the grid cache by removing the specified grid file.

        Parameters
        ----------
        grid_file_name
            Name of the grid file to remove from cache
        """
        local_file_path = get_cache_location(
            name=grid_file_name, cache="grids", destination=""
        )
        if os.path.exists(local_file_path):
            log.info(f"Removing grid cache file: {local_file_path}")
            os.remove(local_file_path)

    def get_compartment_object_by_name(
        self, compartment_name: str
    ) -> Optional[Compartment]:
        """
        Returns compartment object by name.

        Parameters
        ----------
        compartment_name
            Name of the compartment to retrieve

        Returns
        -------
        :
            Compartment object if found, None otherwise
        """
        for compartment in self.compartments:
            if compartment.name == compartment_name:
                return compartment

    def get_bounding_box_limits(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns the min and max limits for the bounding box.

        Returns
        -------
        :
            Tuple containing minimum and maximum bounds as numpy arrays
        """
        bb = np.array(self.boundingBox)
        min_bound = np.min(bb, axis=0)
        max_bound = np.max(bb, axis=0)
        return min_bound, max_bound

    def get_bounding_box_size(self) -> np.ndarray:
        """
        Returns the size of the bounding box in each dimension.

        Returns
        -------
        :
            Size of the bounding box as numpy array
        """
        bb = np.array(self.boundingBox)

        return np.abs(bb[1] - bb[0])

    def setSeed(self, seedNum: Union[int, float]) -> None:
        """
        Set the random seed for reproducible packing.

        Parameters
        ----------
        seedNum
            Seed number for random number generation
        """
        SEED = int(seedNum)
        np.random.seed(SEED)  # for gradient
        seed(SEED)
        self.randomRot.setSeed(seed=SEED)
        self.seed_set = True
        self.seed_used = SEED

    def _prep_ingredient_info(
        self, composition_info: Dict, ingredient_name: Optional[str] = None
    ) -> Dict:
        """
        Prepare ingredient information from composition data.

        Parameters
        ----------
        composition_info
            Dictionary containing composition information
        ingredient_name
            Optional name for the ingredient

        Returns
        -------
        :
            Validated ingredient information dictionary
        """
        objects_dict = self.recipe_data["objects"]
        object_key = composition_info["object"]
        ingredient_info = expand_object_using_key(
            composition_info, "object", objects_dict
        )
        ingredient_info["name"] = (
            ingredient_name if ingredient_name is not None else object_key
        )
        ingredient_info["object_name"] = object_key
        ingredient_info = ingredient.Ingredient.validate_ingredient_info(
            ingredient_info
        )
        return ingredient_info

    def _step_down(
        self, compartment_key: str, prev_compartment: Optional[Any] = None
    ) -> None:
        """
        Recursively create compartments and their ingredients.

        Parameters
        ----------
        compartment_key
            Key identifying the compartment in composition data
        prev_compartment
            Parent compartment object
        """
        parent = prev_compartment if prev_compartment is not None else self
        composition_dict = self.recipe_data["composition"]
        compartment = self.create_compartment(compartment_key, parent)
        compartment_info = composition_dict[compartment_key]
        for region_name, obj_keys in compartment_info.get(
            "regions", {}
        ).items():  # check if entry in compositions has regions
            recipe = Recipe(name=f"{compartment_key}_{region_name}")
            for key_or_dict in obj_keys:
                is_key, composition_info = Recipe.is_key(key_or_dict, composition_dict)
                if is_key and key_or_dict in self.compartment_keys:
                    key = key_or_dict
                    self._step_down(key, prev_compartment=compartment)
                else:
                    key = key_or_dict if is_key else None
                    ingredient_info = self._prep_ingredient_info(composition_info, key)
                    self.create_ingredient(recipe, ingredient_info)
            if region_name == "surface":
                compartment.setSurfaceRecipe(recipe)
            elif region_name == "interior":
                compartment.setInnerRecipe(recipe)

    def create_objects(self) -> None:
        """
        Instantiate compartments and ingredients contained within the recipe data.
        """
        composition_dict = self.recipe_data["composition"]

        if self.root_compartment is not None:
            root_compartment = composition_dict[self.root_compartment]
            # self.create_compartment(self.root_compartment)
            external_recipe = Recipe()
            for region_name, obj_keys in root_compartment.get(
                "regions", {}
            ).items():  # check if entry in compositions has regions
                for key_or_dict in obj_keys:
                    is_key, composition_info = Recipe.is_key(
                        key_or_dict, composition_dict
                    )
                    if is_key and key_or_dict in self.compartment_keys:
                        # key is pointing to another container
                        # make compartment and add ingredients inside it
                        key = key_or_dict
                        self._step_down(key)
                    else:
                        key = key_or_dict if is_key else None
                        ingredient_info = self._prep_ingredient_info(
                            composition_info, key
                        )
                        self.create_ingredient(external_recipe, ingredient_info)
            self.setExteriorRecipe(external_recipe)

    def reportprogress(
        self, label: Optional[str] = None, progress: Optional[float] = None
    ) -> None:
        """
        Report progress to the viewer if available.

        Parameters
        ----------
        label
            Progress label text
        progress
            Progress value between 0 and 1
        """
        if self.afviewer is not None and hasattr(self.afviewer, "vi"):
            self.afviewer.vi.progressBar(progress=progress, label=label)

    def set_partners_ingredient(self, ingr: Ingredient) -> None:
        """
        Set partner ingredients for the given ingredient.

        Parameters
        ----------
        ingr
            Ingredient object to set partners for
        """
        if ingr.partners is not None:
            for partner in ingr.partners.all_partners:
                partner_ingr = self.get_ingredient_by_name(partner.name)
                partner.set_ingredient(partner_ingr)
        if ingr.type == "Grow":
            # TODO: I don't think this code is needed,
            # but I haven't dug into it enough to delete it all yet
            ingr.prepare_alternates()

    def save_result(
        self,
        free_points: List,
        distances: List,
        all_objects: List,
        save_grid_logs: bool = False,
        save_result_as_file: bool = False,
    ) -> None:
        """
        Save packing results to files.

        Parameters
        ----------
        free_points
            List of free grid points
        distances
            List of distances to closest surfaces
        all_objects
            List of all packed objects
        save_grid_logs
            Whether to save grid logs as JSON
        save_result_as_file
            Whether to save results as a file
        """
        self.grid.free_points = free_points[:]
        self.grid.distToClosestSurf = distances[:]
        # should check extension filename for type of saved file
        if not os.path.isfile(self.grid_file_out) and self.load_from_grid_file:
            # do not overwrite if grid was loaded from file
            self.grid.result_filename = self.grid_file_out
            self.save_grids_to_pickle(self.grid_file_out)
        if save_grid_logs:
            self.saveGridLogsAsJson(self.result_file + "_grid-data.json")
        self.collectResultPerIngredient()
        if save_result_as_file:
            self.store()
        Writer(format=self.format_output).save(
            self,
            kwds=["compartment_id"],
            result=True,
            quaternion=True,
            seed_to_results_map={0: all_objects},
        )

    def loadResult(
        self,
        resultfilename: Optional[str] = None,
        restore_grid: bool = True,
        backward: bool = False,
        transpose: bool = True,
    ) -> Tuple[List, List, List]:
        """
        Load packing results from file.

        Parameters
        ----------
        resultfilename
            Path to result file to load
        restore_grid
            Whether to restore grid data
        backward
            Whether to use backward compatibility mode
        transpose
            Whether to transpose data

        Returns
        -------
        :
            Tuple containing loaded result data
        """
        result = [], [], []
        if resultfilename is None:
            resultfilename = self.result_file
            # check the extension of the filename none, txt or json
        fileName, fileExtension = os.path.splitext(resultfilename)
        if fileExtension == "":
            try:
                result = pickle.load(open(resultfilename, "rb"))
            except:  # noqa: E722
                print("can't read " + resultfilename)
                return [], [], []
        elif fileExtension == ".apr":
            try:
                result = pickle.load(open(resultfilename, "rb"))
            except:  # noqa: E722
                return self.load_asTxt(resultfilename=resultfilename)
        elif fileExtension == ".txt":
            return self.load_asTxt(resultfilename=resultfilename)
        elif fileExtension == ".json":
            if backward:
                return self.load_asJson(resultfilename=resultfilename)
            else:
                return IOutils.load_MixedasJson(
                    self, resultfilename=resultfilename, transpose=transpose
                )
        else:
            print("can't read or recognize " + resultfilename)
            return [], [], []
        return result

    def includeIngrRecipes(self, ingrname: str, include: bool) -> None:
        """
        Include or exclude ingredient from all recipes.

        Parameters
        ----------
        ingrname
            Name of ingredient to include/exclude
        include
            True to include, False to exclude
        """
        r = self.exteriorRecipe
        if self.includeIngrRecipe(ingrname, include, r):
            return
        for o in self.compartments:
            rs = o.surfaceRecipe
            if self.includeIngrRecipe(ingrname, include, rs):
                return
            ri = o.innerRecipe
            if self.includeIngrRecipe(ingrname, include, ri):
                return

    def includeIngrRecipe(self, ingrname: str, include: bool, rs: Any) -> bool:
        """
        Include or exclude ingredient from specific recipe.

        Parameters
        ----------
        ingrname
            Name of ingredient to include/exclude
        include
            Whether to include (True) or exclude (False) the ingredient
        rs
            Recipe object to modify

        Returns
        -------
        :
            True if ingredient was found and modified, False otherwise
        """
        for ingr in rs.exclude:
            if ingr.name == ingrname:
                if not include:
                    return True
                else:
                    rs.addIngredient(ingr)
                    return True
        for ingr in rs.ingredients:
            if ingrname == ingr.name:
                if not include:
                    rs.delIngredients(ingr)
                    return True
                else:
                    return True

    def includeIngredientRecipe(self, ingr: Ingredient, include: bool) -> None:
        """
        Include or exclude ingredient from its recipe.

        Parameters
        ----------
        ingr
            Ingredient object to include/exclude
        include
            Whether to include (True) or exclude (False) the ingredient
        """
        r = ingr.recipe  # ()
        if include:
            r.addIngredient(ingr)
        else:
            r.delIngredient(ingr)

    def sortIngredient(self, reset: bool = False) -> None:
        """
        Sort ingredients in all recipes by radius from large to small.

        Parameters
        ----------
        reset
            Whether to reset compartments before sorting
        """
        if self.exteriorRecipe:
            self.exteriorRecipe.sort()
        for o in self.compartments:
            if reset:
                o.reset()
            if o.innerRecipe:
                o.innerRecipe.sort()
            if o.surfaceRecipe:
                o.surfaceRecipe.sort()

    def resolve_gradient_data_objects(self, gradient_data: Dict) -> Dict:
        """
        Resolve gradient data objects for some modes.

        Parameters
        ----------
        gradient_data
            Dictionary containing gradient configuration

        Returns
        -------
        :
            Resolved gradient data dictionary
        """
        # TODO: check if other modes need to be resolved
        if gradient_data["mode"] == "surface":
            gradient_data["mode_settings"][
                "object"
            ] = self.get_compartment_object_by_name(
                gradient_data["mode_settings"]["object"]
            )
        return gradient_data

    def set_gradient(self, gradient_data: Dict) -> None:
        """
        Create a gradient and assign weight to points.

        Parameters
        ----------
        gradient_data
            Dictionary containing gradient configuration
        """
        gradient_data = self.resolve_gradient_data_objects(gradient_data)
        gradient = Gradient(gradient_data)
        # default gradient 1-linear Decoy X
        self.gradients[gradient_data["name"]] = gradient

    def callFunction(self, function: callable, args: List = [], kw: Dict = {}) -> Any:
        """
        Helper function to callback another function with given arguments.

        Parameters
        ----------
        function
            Function to call
        args
            List of positional arguments
        kw
            Dictionary of keyword arguments

        Returns
        -------
        :
            Result of function call
        """
        if len(kw):
            res = function(*args, **kw)
        else:
            res = function(*args)
        return res

    def is_two_d(self) -> bool:
        """
        Check if the environment is effectively 2D based on grid spacing.

        Returns
        -------
        :
            True if environment is 2D, False otherwise
        """
        grid_spacing = self.grid.gridSpacing
        bounding_box = self.boundingBox
        box_size = np.array(bounding_box[1]) - np.array(bounding_box[0])
        smallest_size = np.amin(box_size)
        return smallest_size <= grid_spacing

    def timeFunction(self, function: callable, args: List, kw: Dict) -> Any:
        """
        Measure the time for performing the provided function.

        Parameters
        ----------
        function
            Function to execute and time
        args
            List of arguments for the function
        kw
            Dictionary of keyword arguments

        Returns
        -------
        :
            Result of function execution
        """
        t1 = time()
        if len(kw):
            res = function(*args, **kw)
        else:
            res = function(*args)
        print(("time " + function.__name__, time() - t1))
        return res

    def SetRBOptions(self, obj: str = "moving", **kw) -> None:
        """
        Change the rigid body options.

        Parameters
        ----------
        obj
            Type of rigid body object
        **kw
            Keyword arguments for rigid body options
        """
        key = [
            "shape",
            "child",
            "dynamicsBody",
            "dynamicsLinearDamp",
            "dynamicsAngularDamp",
            "massClamp",
            "rotMassClamp",
        ]
        for k in key:
            val = kw.pop(k, None)
            if val is not None:
                self.dynamicOptions[obj][k] = val

    def SetSpringOptions(self, **kw) -> None:
        """
        Change the spring options, mainly used by C4D.

        Parameters
        ----------
        **kw
            Keyword arguments for spring options
        """
        key = ["stifness", "rlength", "damping"]
        for k in key:
            val = kw.pop(k, None)
            if val is not None:
                self.springOptions[k] = val

    def setupRBOptions(self) -> None:
        """
        Set default values for rigid body options.
        """
        self.springOptions["stifness"] = 1.0
        self.springOptions["rlength"] = 0.0
        self.springOptions["damping"] = 1.0
        self.dynamicOptions["spring"] = {}
        self.dynamicOptions["spring"]["child"] = True
        self.dynamicOptions["spring"]["shape"] = "auto"
        self.dynamicOptions["spring"]["dynamicsBody"] = "on"
        self.dynamicOptions["spring"]["dynamicsLinearDamp"] = 0.0
        self.dynamicOptions["spring"]["dynamicsAngularDamp"] = 0.0
        self.dynamicOptions["spring"]["massClamp"] = 1.0
        self.dynamicOptions["spring"]["rotMassClamp"] = 1.0
        self.dynamicOptions["moving"] = {}
        self.dynamicOptions["moving"]["child"] = True
        self.dynamicOptions["moving"]["shape"] = "auto"
        self.dynamicOptions["moving"]["dynamicsBody"] = "on"
        self.dynamicOptions["moving"]["dynamicsLinearDamp"] = 1.0
        self.dynamicOptions["moving"]["dynamicsAngularDamp"] = 1.0
        self.dynamicOptions["moving"]["massClamp"] = 0.001
        self.dynamicOptions["moving"]["rotMassClamp"] = 0.1
        self.dynamicOptions["static"] = {}
        self.dynamicOptions["static"]["child"] = True
        self.dynamicOptions["static"]["shape"] = "auto"
        self.dynamicOptions["static"]["dynamicsBody"] = "off"
        self.dynamicOptions["static"]["dynamicsLinearDamp"] = 0.0
        self.dynamicOptions["static"]["dynamicsAngularDamp"] = 0.0
        self.dynamicOptions["static"]["massClamp"] = 100.0
        self.dynamicOptions["static"]["rotMassClamp"] = 1
        self.dynamicOptions["surface"] = {}
        self.dynamicOptions["surface"]["child"] = True
        self.dynamicOptions["surface"]["shape"] = "auto"
        self.dynamicOptions["surface"]["dynamicsBody"] = "off"
        self.dynamicOptions["surface"]["dynamicsLinearDamp"] = 0.0
        self.dynamicOptions["surface"]["dynamicsAngularDamp"] = 0.0
        self.dynamicOptions["surface"]["massClamp"] = 100.0
        self.dynamicOptions["surface"]["rotMassClamp"] = 1

    def writeArraysToFile(self, f: Any) -> None:
        """
        Write grid arrays to file using pickle.

        Parameters
        ----------
        f
            File object to write to
        """
        pickle.dump(self.grid.masterGridPositions, f)
        pickle.dump(self.grid.compartment_ids, f)
        pickle.dump(self.grid.distToClosestSurf, f)

    def readArraysFromFile(self, f: Any) -> None:
        """
        Read grid arrays from file using pickle.

        Parameters
        ----------
        f
            File object to read from
        """
        pos = pickle.load(f)
        self.grid.masterGridPositions = pos

        id = pickle.load(f)
        self.grid.compartment_ids = id

        dist = pickle.load(f)
        self.grid.distToClosestSurf_store = self.grid.distToClosestSurf[:]
        if len(dist):
            self.grid.distToClosestSurf = dist  # grid+organelle+surf
        self.grid.free_points = list(range(len(id)))

    def saveGridToFile(self, gridFileOut: str) -> None:
        """
        Save the current grid and compartment information to file.

        Parameters
        ----------
        gridFileOut
            Path to output grid file
        """
        d = os.path.dirname(gridFileOut)
        if not os.path.exists(d):
            log.error(f"gridfilename path problem {gridFileOut}")
            return
        f = open(gridFileOut, "wb")  # 'w'
        self.writeArraysToFile(f)

        for compartment in self.compartments:
            compartment.saveGridToFile(f)
        log.debug(f"Saved grid to {gridFileOut}")
        f.close()

    def saveGridLogsAsJson(self, gridFileOut: str) -> None:
        """
        Save grid logs as JSON file.

        Parameters
        ----------
        gridFileOut
            Path to output JSON file
        """
        d = os.path.dirname(gridFileOut)
        if not os.path.exists(d):
            print("gridfilename path problem", gridFileOut)
        data = {}
        for i in range(len(self.grid.masterGridPositions)):
            data[i] = {
                "position": [
                    str(self.grid.masterGridPositions[i][0]),
                    str(self.grid.masterGridPositions[i][1]),
                    str(self.grid.masterGridPositions[i][2]),
                ],
                "distance": str(self.grid.distToClosestSurf[i]),
                "compartment": str(self.grid.compartment_ids[i]),
            }
        # data = {
        #     # "gridPositions": json.loads(self.grid.masterGridPositions),
        #     "distances": json.loads(self.grid.distToClosestSurf)
        # }
        with open(gridFileOut, "w") as f:
            json.dump(data, fp=f)
        f.close()

    @staticmethod
    def get_attributes_to_update() -> List[str]:
        """
        Get list of attributes that need to be updated when loading grids.

        Returns
        -------
        :
            List of attribute names to update
        """
        return [
            "faces",
            "vertices",
            "vnormals",
            "filename",
            "ref_obj",
            "bb",
            "center",
            "encapsulating_radius",
            "radius",
            "insidePoints",
            "surfacePoints",
            "surfacePointsCoords",
            "surfacePointsNormals",
            "ogsurfacePoints",
            "ogsurfacePointsNormals",
            "OGsrfPtsBht",
            "closestId",
        ]

    def restore_grids_from_pickle(self, grid_file_path: str) -> None:
        """
        Read and setup the grid from pickle file.

        Parameters
        ----------
        grid_file_path
            Path to grid pickle file
        """
        log.debug(f"Loading grid from {grid_file_path}")

        grid_objs = []
        comp_objs = []
        mesh_store_objs = []

        with open(grid_file_path, "rb") as file_obj:
            while True:
                try:
                    obj = pickle.load(file_obj)
                    if isinstance(obj, BaseGrid):
                        # load env grid
                        grid_objs.append(obj)
                    elif isinstance(obj, Compartment):
                        # load compartment grids
                        comp_objs.append(obj)
                    elif isinstance(obj, MeshStore):
                        # load mesh store
                        mesh_store_objs.append(obj)
                except EOFError:
                    break

        # setup env grid
        for grid_obj in grid_objs:
            self.grid = grid_obj

        # setup compartment grids
        for ct, _ in enumerate(self.compartments):
            for comp_obj in comp_objs:
                if (
                    hasattr(comp_obj, "name")
                    and comp_obj.name == self.compartments[ct].name
                ):
                    for update_attr in self.get_attributes_to_update():
                        setattr(
                            self.compartments[ct],
                            update_attr,
                            getattr(comp_obj, update_attr),
                        )

        # setup mesh store
        for mesh_store_obj in mesh_store_objs:
            self.mesh_store = mesh_store_obj

        # clear the triangles_tree cache
        for _, geom in self.mesh_store.scene.geometry.items():
            geom._cache.delete("triangles_tree")

        # reset grid
        self.grid.reset()

    def save_grids_to_pickle(self, grid_file_path: str) -> None:
        """
        Save the current grid and compartment grids to pickle file.

        Parameters
        ----------
        grid_file_path
            Path to output pickle file
        """
        log.info("Saving grid to %s", grid_file_path)
        if not os.path.exists(os.path.dirname(grid_file_path)):
            raise ValueError(f"Check grid file path: {grid_file_path}")
        with open(grid_file_path, "wb") as file_obj:
            # dump env grid
            pickle.dump(self.grid, file_obj)

            # dump compartment grids
            for compartment in self.compartments:
                pickle.dump(compartment, file_obj)

            # dump mesh store
            pickle.dump(self.mesh_store, file_obj)

    def restoreGridFromFile(self, gridFileName: str) -> None:
        """
        Read and setup the grid from the given filename (legacy method).

        Parameters
        ----------
        gridFileName
            Path to grid file
        """
        log.debug(f"Loading grid from {gridFileName}")
        aInteriorGrids = []
        aSurfaceGrids = []
        f = open(gridFileName, "rb")
        self.readArraysFromFile(f)
        for ct, compartment in enumerate(self.compartments):
            compartment.readGridFromFile(f)
            aInteriorGrids.append(compartment.insidePoints)
            aSurfaceGrids.append(compartment.surfacePoints)
            compartment.OGsrfPtsBht = KDTree(tuple(compartment.vertices), leafsize=10)
            compartment.compute_volume_and_set_count(
                self, compartment.surfacePoints, compartment.insidePoints, areas=None
            )
            self.compartments[ct] = compartment
        f.close()
        # TODO: restore surface distances on loading from grid
        self.grid.aInteriorGrids = aInteriorGrids
        self.grid.aSurfaceGrids = aSurfaceGrids

    def extractMeshComponent(
        self, obj: Any
    ) -> Tuple[Optional[List], Optional[List], Optional[List]]:
        """
        Extract mesh components (vertices, faces, normals) from object.

        Parameters
        ----------
        obj
            Object to extract mesh from

        Returns
        -------
        :
            Tuple containing vertices, faces, and normals lists
        """
        print("extractMeshComponent", helper.getType(obj))
        if helper is None:
            print("no Helper found")
            return None, None, None
        if helper.getType(obj) == helper.EMPTY:  # compartment master parent?
            childs = helper.getChilds(obj)
            for ch in childs:
                if helper.getType(ch) == helper.EMPTY:
                    c = helper.getChilds(ch)
                    # should be all polygon
                    faces = []
                    vertices = []
                    vnormals = []
                    for pc in c:
                        f, v, vn = helper.DecomposeMesh(
                            pc, edit=False, copy=False, tri=True, transform=True
                        )
                        faces.extend(f)
                        vertices.extend(v)
                        vnormals.extend(vn)
                    return vertices, faces, vnormals
                elif helper.getType(ch) == helper.POLYGON:
                    faces, vertices, vnormals = helper.DecomposeMesh(
                        ch, edit=False, copy=False, tri=True, transform=True
                    )
                    return vertices, faces, vnormals
                else:
                    continue
        elif helper.getType(obj) == helper.POLYGON:
            faces, vertices, vnormals = helper.DecomposeMesh(
                obj, edit=False, copy=False, tri=True, transform=True
            )
            return vertices, faces, vnormals
        else:
            print(
                "extractMeshComponent",
                helper.getType(obj),
                helper.POLYGON,
                helper.getType(obj) == helper.POLYGON,
            )
            return None, None, None

    def update_largest_smallest_size(self, ingr: Ingredient) -> None:
        """
        Update the largest and smallest protein sizes based on ingredient.

        Parameters
        ----------
        ingr
            Ingredient object to check sizes for
        """
        if ingr.encapsulating_radius > self.largestProteinSize:
            self.largestProteinSize = ingr.encapsulating_radius
        if ingr.min_radius < self.smallestProteinSize:
            self.smallestProteinSize = ingr.min_radius

    def create_ingredient(self, recipe: Any, arguments: Dict) -> None:
        """
        Create an ingredient and add it to the recipe.

        Parameters
        ----------
        recipe
            Recipe object to add ingredient to
        arguments
            Dictionary of ingredient parameters
        """
        if "place_method" not in arguments:
            arguments["place_method"] = self.place_method
        ingredient_type = arguments["type"]
        ingredient_class = ingredient.get_ingredient_class(ingredient_type)
        ingr = ingredient_class(**arguments)
        if "gradient" in arguments:
            ingr = Gradient.update_ingredient_gradient(ingr, arguments)
        if "results" in arguments:
            ingr.results = arguments["results"]
        ingr.initialize_mesh(self.mesh_store)
        recipe.addIngredient(ingr)
        self.update_largest_smallest_size(ingr)

    def create_compartment(self, compartment_key: str, parent: Any) -> Any:
        """
        Create a compartment object from recipe data.

        Parameters
        ----------
        compartment_key
            Key identifying the compartment
        parent
            Parent compartment or environment

        Returns
        -------
        :
            Created compartment object
        """
        comp_dic = self.recipe_data["composition"]
        obj_dic = self.recipe_data["objects"]

        if "object" in comp_dic[compartment_key]:
            # create compartment using object
            object_info = obj_dic[comp_dic[compartment_key]["object"]]
        else:
            # use bounding box
            object_info = {"bounding_box": self.boundingBox}

        compartment = Compartment(
            name=compartment_key,
            object_info=object_info,
        )
        self._add_compartment(compartment, parent)
        return compartment

    def _add_compartment(self, compartment: Any, parent: Any) -> None:
        """
        Add the given compartment to the environment.

        Parameters
        ----------
        compartment
            Compartment object to add
        parent
            Parent object for the compartment
        """
        compartment.setNumber(self.nbCompartments)
        self.nbCompartments += 1
        self.compartments.append(compartment)
        CompartmentList.add_compartment(parent, compartment)

    def compartment_id_for_nearest_grid_point(
        self, point: Union[List, np.ndarray]
    ) -> int:
        """
        Get compartment ID for the nearest grid point to given point.

        Parameters
        ----------
        point
            3D point coordinates

        Returns
        -------
        :
            Compartment ID of nearest grid point
        """
        # check if point inside  of the compartments
        # closest grid point is
        d, pid = self.grid.getClosestGridPoint(point)
        compartment_id = self.grid.compartment_ids[pid]
        return compartment_id

    def loopThroughIngr(
        self, cb_function: callable, kwargs: Optional[Dict] = None
    ) -> None:
        """
        Loop through all ingredients and apply callback function.

        Parameters
        ----------
        cb_function
            Callback function to apply to each ingredient
        kwargs
            Optional keyword arguments for callback function
        """
        if kwargs is None:
            kwargs = {}
        recipe = self.exteriorRecipe
        if recipe:
            for ingr in recipe.ingredients:
                cb_function(ingr, **kwargs)
        for compartment in self.compartments:
            surface_recipe = compartment.surfaceRecipe
            if surface_recipe:
                for ingr in surface_recipe.ingredients:
                    cb_function(ingr, **kwargs)
            inner_recipe = compartment.innerRecipe
            if inner_recipe:
                for ingr in inner_recipe.ingredients:
                    cb_function(ingr, **kwargs)

    def getIngrFromNameInRecipe(self, name: str, r: Any) -> Optional[Any]:
        """
        Get ingredient object by name from specific recipe.

        Parameters
        ----------
        name
            Name of ingredient to find
        r
            Recipe object to search in

        Returns
        -------
        :
            Ingredient object if found, None otherwise
        """
        if r:
            # check if name start with comp name
            # backward compatibility
            # legacy code
            # Problem when ingredient in different compartments
            # compartments is in the first three caractet like int_2 or surf_1
            for ingr in r.ingredients:
                if name == ingr.name:
                    return ingr
                elif name == ingr.composition_name:
                    return ingr
                #                elif name.find(ingr.composition_name) != -1 :
                #                    #check for
                #                    return ingr
            for ingr in r.exclude:
                if name == ingr.name:
                    return ingr
                elif name == ingr.composition_name:
                    return ingr
                #                elif name.find(ingr.composition_name) != -1 :
                #                    return ingr
        return None

    def get_ingredient_by_name(
        self, name: str, compartment_id: Optional[int] = None
    ) -> Optional[Any]:
        """
        Given an ingredient name and optionally the compartment number, retrieve the ingredient
        object instance.

        Parameters
        ----------
        name
            Name of ingredient to find
        compartment_id
            Optional compartment ID to search in

        Returns
        -------
        :
            Ingredient object if found, None otherwise
        """
        if compartment_id is None:
            r = self.exteriorRecipe
            ingr = self.getIngrFromNameInRecipe(name, r)
            if ingr is not None:
                return ingr
            for o in self.compartments:
                rs = o.surfaceRecipe
                ingr = self.getIngrFromNameInRecipe(name, rs)
                if ingr is not None:
                    return ingr
                ri = o.innerRecipe
                ingr = self.getIngrFromNameInRecipe(name, ri)
                if ingr is not None:
                    return ingr
        elif compartment_id == 0:
            r = self.exteriorRecipe
            ingr = self.getIngrFromNameInRecipe(name, r)
            if ingr is not None:
                return ingr
            else:
                return None
        elif compartment_id > 0:
            o = self.compartments[compartment_id - 1]
            rs = o.surfaceRecipe
            ingr = self.getIngrFromNameInRecipe(name, rs)
            if ingr is not None:
                return ingr
            else:
                return None
        else:  # <0
            o = self.compartments[(compartment_id * -1) - 1]
            ri = o.innerRecipe
            ingr = self.getIngrFromNameInRecipe(name, ri)
            if ingr is not None:
                return ingr
            else:
                return None

    def get_ingredients_in_tree(self, closest_ingredients: Dict) -> List:
        """
        Get ingredients from packed objects tree.

        Parameters
        ----------
        closest_ingredients
            Dictionary containing indices and distances

        Returns
        -------
        :
            List of ingredient objects and distances
        """
        ingredients = []
        packed_objects = self.packed_objects.get_ingredients()
        if len(packed_objects):
            nearby_packed_objects = [
                packed_objects[i] for i in closest_ingredients["indices"]
            ]
            for obj in nearby_packed_objects:
                ingredients.append([obj, closest_ingredients["distances"]])
        return ingredients

    def get_closest_ingredients(
        self, point: Union[List, np.ndarray], cutoff: float = 10.0
    ) -> Dict:
        """
        Get closest ingredients to a given point within cutoff distance.

        Parameters
        ----------
        point
            3D point coordinates
        cutoff
            Maximum distance to search for ingredients

        Returns
        -------
        :
            Dictionary containing indices and distances of closest ingredients
        """
        to_return = {"indices": [], "distances": []}
        np.zeros(self.totalNbIngr).astype("i")
        nb = 0
        number_packed = len(self.packed_objects.get_ingredients())
        if not number_packed:
            return to_return
        if self.close_ingr_bhtree is not None:
            # request kdtree
            nb = []
            self.log.info("finding partners")

            if number_packed >= 1:
                distance, nb = self.close_ingr_bhtree.query(
                    point, number_packed, distance_upper_bound=cutoff
                )  # len of ingr posed so far
                if number_packed == 1:
                    distance = [distance]
                    nb = [nb]
                to_return["indices"] = nb
                to_return["distances"] = distance  # sorted by distance short -> long
            return to_return
        else:
            return to_return

    def setExteriorRecipe(self, recipe: Any) -> None:
        """
        Set the exterior recipe and create weak reference.

        Parameters
        ----------
        recipe
            Recipe object to set as exterior recipe
        """
        assert isinstance(recipe, Recipe)
        self.exteriorRecipe = recipe
        recipe.compartment = self  # weakref.ref(self)
        for ingr in recipe.ingredients:
            ingr.compartment_id = 0

    def BuildCompartmentsGrids(self) -> None:
        """
        Build the compartments grid (interior and surface points) to be merged with main grid.
        """
        aInteriorGrids = []
        aSurfaceGrids = []
        # thread ?
        for compartment in self.compartments:
            compartment.initialize_shape(self.mesh_store)
            self.log.info(
                "in Environment,"
                f" compartment.is_orthogonal_bounding_box={compartment.is_orthogonal_bounding_box}"
            )
            (
                points_inside_compartments,
                points_on_compartment_surfaces,
            ) = compartment.BuildGrid(
                self, self.mesh_store
            )  # return inside and surface point
            aInteriorGrids.append(points_inside_compartments)
            aSurfaceGrids.append(points_on_compartment_surfaces)
        self.grid.aInteriorGrids = aInteriorGrids
        self.grid.aSurfaceGrids = aSurfaceGrids
        self.log.info("I'm out of the loop and have build my grid with inside points")
        self.log.info(
            f"build Grids {self.innerGridMethod}, {len(self.grid.aSurfaceGrids)}"
        )

    def build_compartment_grids(self) -> None:
        """
        Build compartment grids and setup surface points spatial tree.
        """
        self.log.info("file is None thus re/building grid distance")
        self.BuildCompartmentsGrids()

        if len(self.compartments):
            verts = np.array(self.compartments[0].surfacePointsCoords)
            for i in range(1, len(self.compartments)):
                verts = np.vstack([verts, self.compartments[i].surfacePointsCoords])
            self.grid.set_surfPtsBht(
                verts.tolist()
            )  # should do it only on inside grid point

    def extend_bounding_box_for_compartments(self, spacing: float) -> None:
        """
        Extend bounding box to fit all compartments.

        Parameters
        ----------
        spacing
            Grid spacing value
        """
        for _, compartment in enumerate(self.compartments):
            fits, bb = compartment.inBox(self.boundingBox, spacing)
            if not fits:
                self.boundingBox = bb

    def get_size_of_bounding_box(self) -> float:
        """
        Calculate the size of the bounding box.

        Returns
        -------
        :
            Size of bounding box as scalar value
        """
        box_boundary = np.array(self.boundingBox)
        return np.linalg.norm(box_boundary[1] - box_boundary[0])

    def buildGrid(self, rebuild: bool = True) -> None:
        """
        Build the main grid and merge compartment grids.

        Parameters
        ----------
        rebuild
            Whether to rebuild the grid from scratch
        """
        spacing = self.spacing or self.smallestProteinSize
        self.extend_bounding_box_for_compartments(spacing)

        boundingBox = self.boundingBox
        if self.use_halton:
            from cellpack.autopack.BaseGrid import HaltonGrid as Grid
        elif self.innerGridMethod == "floodfill":
            from cellpack.autopack.Environment import Grid
        else:
            from cellpack.autopack.BaseGrid import BaseGrid as Grid

        self.sortIngredient(reset=True)
        if self.grid is None or self.nFill == 0:
            self.log.info("####BUILD GRID - step %r", self.smallestProteinSize)
            self.fillBB = boundingBox
            self.grid = Grid(boundingBox=boundingBox, spacing=spacing)
            nbPoints = self.grid.gridVolume
            self.log.info("new Grid with %r %r", boundingBox, self.grid.gridVolume)
            if self.nFill == 0:
                self.grid.distToClosestSurf_store = self.grid.distToClosestSurf[:]
                nbPoints = self.grid.gridVolume

        elif self.grid is not None:
            self.log.info("$$$$$$$$  reset the grid")
            self.grid.reset()
            nbPoints = len(self.grid.free_points)
            self.log.info("$$$$$$$$  reset the grid")

        if self.previous_grid_file is not None:
            self.grid.filename = self.previous_grid_file
            if self.nFill == 0:  # first fill, after we can just reset
                self.log.info("restore from file")
                self.restore_grids_from_pickle(self.previous_grid_file)
        else:
            self.build_compartment_grids()

            # save grids to pickle
            self.grid.filename = self.grid_file_out
            self.previous_grid_file = self.grid_file_out
            self.save_grids_to_pickle(self.grid_file_out)

        self.exteriorVolume = self.grid.computeExteriorVolume(
            compartments=self.compartments,
            space=self.smallestProteinSize,
            fbox_bb=self.fbox_bb,
        )

        r = self.exteriorRecipe
        if r:
            r.setCount(self.exteriorVolume)  # should actually use the fillBB

        if not rebuild:
            for c in self.compartments:
                c.setCount()
        else:
            self.grid.distToClosestSurf_store = self.grid.distToClosestSurf[:]

        # distance = self.grid.distToClosestSurf  # [:]
        nbFreePoints = nbPoints  # -1
        # TODO: refactor this to work with new placed_objects data structure
        # for i, mingrs in enumerate(self.molecules):  # ( jtrans, rotMatj, self, ptInd )
        #     nbFreePoints = self.onePrevIngredient(
        #         i, mingrs, distance, nbFreePoints, self.molecules
        #     )
        # for organelle in self.compartments:
        #     for i, mingrs in enumerate(
        #         organelle.molecules
        #     ):  # ( jtrans, rotMatj, self, ptInd )
        #         nbFreePoints = self.onePrevIngredient(
        #             i, mingrs, distance, nbFreePoints, organelle.molecules
        #         )
        self.grid.nbFreePoints = nbFreePoints

        if self.use_gradient and len(self.gradients) and rebuild:
            for g in self.gradients:
                gradient = self.gradients[g]
                if gradient.mode == "surface":
                    if not hasattr(
                        gradient.mode_settings["object"], "surface_distances"
                    ):
                        gradient.mode_settings["object"].set_surface_distances(
                            self,
                            self.grid.masterGridPositions,
                            gradient.mode_settings.get("scale_to_next_surface", False),
                        )
                self.gradients[g].build_weight_map(
                    boundingBox, self.grid.masterGridPositions
                )

    def onePrevIngredient(
        self, i: int, mingrs: Tuple, distance: List, nbFreePoints: int, marray: List
    ) -> int:
        """
        Process one previously placed ingredient (unused method).

        Parameters
        ----------
        i
            Index of ingredient
        mingrs
            Tuple containing ingredient placement data
        distance
            List of distances
        nbFreePoints
            Number of free points
        marray
            Array of molecules

        Returns
        -------
        :
            Updated number of free points
        """
        jtrans, rotMatj, ingr, ptInd, _ = mingrs
        centT = ingr.transformPoints(jtrans, rotMatj, ingr.positions[-1])
        insidePoints = {}
        newDistPoints = {}
        mr = self.get_dpad(ingr.compartment_id)
        spacing = self.smallestProteinSize
        jitter = ingr.getMaxJitter(spacing)
        dpad = ingr.min_radius + mr + jitter
        insidePoints, newDistPoints = ingr.get_new_distance_values(
            jtrans=jtrans,
            rotMatj=rotMatj,
            gridPointsCoords=self.grid.masterGridPositions,
            distance=distance,
            dpad=dpad,
            centT=centT,
        )
        marray[i][3] = -ptInd  # uniq Id ?
        nbFreePoints = BaseGrid.updateDistances(
            self,
            insidePoints,
            newDistPoints,
            self.grid.free_points,
            nbFreePoints,
            distance,
            self.grid.masterGridPositions,
            0,
        )
        # should we reset the ingredient ? completion ?
        if not ingr.is_previous:
            ingr.firstTimeUpdate = True
            ingr.counter = 0
            ingr.rejectionCounter = 0
            ingr.completion = 0.0  # should actually count it
            if hasattr(
                ingr, "allIngrPts"
            ):  # Graham here on 5/16/12 are these two lines safe?
                del ingr.allIngrPts  # Graham here on 5/16/12 are these two lines safe?
        return nbFreePoints

    def getSortedActiveIngredients(self, allIngredients: List) -> Tuple[List, List]:
        """
        Sort active ingredients by priority and radius.

        Parameters
        ----------
        allIngredients
            List of all ingredient objects

        Returns
        -------
        :
            Tuple containing sorted ingredient lists (priority 0, priority 1+2)
        """
        ingr1 = []  # given priorities
        priorities1 = []
        ingr2 = []  # priority = 0 or none and will be assigned based on complexity
        priorities2 = []
        ingr0 = []  # negative values will pack first in order of abs[priority]
        priorities0 = []
        for ing in allIngredients:
            if ing.completion >= 1.0:
                continue  # ignore completed ingredients
            if ing.priority is None or ing.priority == 0:
                ingr2.append(ing)
                priorities2.append(ing.priority)
            elif ing.priority > 0:
                ingr1.append(ing)
                priorities1.append(ing.priority)
            else:
                # ing.priority    = -ing.priority
                ingr0.append(ing)
                priorities0.append(ing.priority)

        if self.pickWeightedIngr:
            try:
                ingr1.sort(key=cmp_to_key(ingredient_compare1))
                ingr2.sort(key=cmp_to_key(ingredient_compare2))
                ingr0.sort(key=cmp_to_key(ingredient_compare0))
            except Exception as e:  # noqa: E722
                print("ATTENTION INGR NOT SORTED", e)
        # GrahamAdded this stuff in summer 2011, beware!
        if len(ingr1) != 0:
            lowestIng = ingr1[len(ingr1) - 1]
            self.lowestPriority = lowestIng.priority
        else:
            self.lowestPriority = 1.0
        self.log.info("self.lowestPriority for Ing1 = %d", self.lowestPriority)
        self.totalRadii = 0
        for radii in ingr2:
            if radii.model_type == "Cylinders":
                r = max(radii.length / 2.0, radii.min_radius)
            elif radii.model_type == "Spheres":
                r = radii.min_radius
            elif radii.model_type == "Cube":
                r = radii.min_radius
            self.totalRadii = self.totalRadii + r
            self.log.info("self.totalRadii += %d = %d", r, self.totalRadii)
            if r == 0:
                # safety
                self.totalRadii = self.totalRadii + 1.0

        self.normalizedPriorities0 = []
        for priors2 in ingr2:
            if priors2.model_type == "Cylinders":
                r = max(priors2.length / 2.0, priors2.min_radius)
            elif priors2.model_type == "Spheres":
                r = priors2.min_radius
            norm_priority = float(r) / float(self.totalRadii) * self.lowestPriority
            self.normalizedPriorities0.append(norm_priority)
            priors2.priority = norm_priority
            self.log.info("self.normalizedPriorities0 = %r", self.normalizedPriorities0)
        activeIngr0 = ingr0  # +ingr1+ingr2  #cropped to 0 on 7/20/10

        self.log.info("len(activeIngr0) %d", len(activeIngr0))
        activeIngr12 = ingr1 + ingr2
        self.log.info("len(activeIngr12) %d", len(activeIngr12))
        packingPriorities = priorities0 + priorities1 + priorities2
        self.log.info("packingPriorities %r", packingPriorities)

        return activeIngr0, activeIngr12

    def clearRBingredient(self, ingr: Ingredient) -> None:
        """
        Clear rigid body nodes for an ingredient.

        Parameters
        ----------
        ingr
            Ingredient object to clear rigid body nodes for
        """
        if ingr.bullet_nodes[0] is not None:
            self.delRB(ingr.bullet_nodes[0])
        if ingr.bullet_nodes[1] is not None:
            self.delRB(ingr.bullet_nodes[1])

    def clear(self) -> None:
        """
        Clear all rigid body ingredients before closing.
        """
        # before closing remoeall rigidbody
        self.loopThroughIngr(self.clearRBingredient)

    def reset(self) -> None:
        """
        Reset everything to empty and not done
        """
        self.fbox_bb = None
        self.totnbJitter = 0
        self.jitterLength = 0.0
        r = self.exteriorRecipe
        self.resetIngrRecip(r)
        self.packed_objects = PackedObjects()
        for orga in self.compartments:
            orga.reset()
            rs = orga.surfaceRecipe
            self.resetIngrRecip(rs)
            ri = orga.innerRecipe
            self.resetIngrRecip(ri)
        if self.octree is not None:
            del self.octree
            self.octree = None
            # the reset doesnt touch the grid...
        # rapid node ?

    def resetIngrRecip(self, recip: Any) -> None:
        """
        Reset all ingredient of the given recipe

        Parameters
        ----------
        recip
            Recipe containing ingredients to reset
        """
        if recip:
            for ingr in recip.ingredients:
                # ingr.results = []
                ingr.firstTimeUpdate = True
                ingr.counter = 0
                ingr.rejectionCounter = 0
                ingr.completion = 0.0
                ingr.prev_alt = None
                ingr.start_positions = []
                if len(ingr.allIngrPts) > 0:
                    ingr.allIngrPts = []
                if hasattr(ingr, "isph"):
                    ingr.isph = None
                if hasattr(ingr, "icyl"):
                    ingr.icyl = None

            for ingr in recip.exclude:
                ingr.firstTimeUpdate = True
                ingr.counter = 0
                ingr.rejectionCounter = 0
                ingr.completion = 0.0
                ingr.prev_alt = None
                ingr.results = []
                ingr.start_positions = []

                if hasattr(ingr, "isph"):
                    ingr.isph = None
                if hasattr(ingr, "icyl"):
                    ingr.icyl = None
                if len(ingr.allIngrPts) > 0:
                    ingr.allIngrPts = []

    def getActiveIng(self) -> List[Any]:
        """
        Return all remaining active ingredients

        Returns
        -------
        :
            List of active ingredients with left_to_place > 0
        """
        allIngredients = []
        recipe = self.exteriorRecipe
        if recipe:
            for ingr in recipe.ingredients:
                ingr.counter = 0  # counter of placed molecules
                if ingr.left_to_place > 0:  # I DONT GET IT !
                    ingr.completion = 0.0
                    allIngredients.append(ingr)
                else:
                    ingr.completion = 1.0

        for compartment in self.compartments:
            recipe = compartment.surfaceRecipe
            if recipe:
                for ingr in recipe.ingredients:
                    ingr.counter = 0  # counter of placed molecules
                    if ingr.left_to_place > 0:
                        ingr.completion = 0.0
                        allIngredients.append(ingr)
                    else:
                        ingr.completion = 1.0

            recipe = compartment.innerRecipe
            if recipe:
                for ingr in recipe.ingredients:
                    ingr.counter = 0  # counter of placed molecules
                    if ingr.left_to_place > 0:
                        ingr.completion = 0.0
                        allIngredients.append(ingr)
                    else:
                        ingr.completion = 1.0
        return allIngredients

    def pickIngredient(self, vThreshStart: float, verbose: int = 0) -> Any:
        """
        Main function that decide the next ingredient the packing will try to
        drop. The picking is weighted or random

        Parameters
        ----------
        vThreshStart
            Threshold start value for ingredient picking
        verbose
            Verbosity level for logging

        Returns
        -------
        :
            Selected ingredient for packing
        """
        if self.pickWeightedIngr:
            if self.thresholdPriorities[0] == 2:
                # Graham here: Walk through -priorities first
                ingr = self.activeIngr[0]
            else:
                # prob = uniform(vRangeStart,1.0)
                # #Graham 9/21/11 This is wrong...
                # vRangeStart is the point index, need active list
                # i.e. thresholdPriority to be limited
                prob = uniform(0, 1.0)
                ingrInd = 0
                for threshProb in self.thresholdPriorities:
                    if prob <= threshProb:
                        break
                    ingrInd = ingrInd + 1
                if ingrInd < len(self.activeIngr):
                    ingr = self.activeIngr[ingrInd]
                else:
                    log.error(f"Error in Environment pick Ingredient: {ingrInd}")
                    ingr = self.activeIngr[0]
                if verbose:
                    print("weighted", prob, vThreshStart, ingrInd, ingr.name)
        else:
            r = random()  # randint(0, len(self.activeIngr)-1)#random()
            # n=int(r*(len(self.activeIngr)-1))
            n = int(r * len(self.activeIngr))
            ingr = self.activeIngr[n]
        #            print (r,n,ingr.name,len(self.activeIngr)) #Graham turned back on 5/16/12, but may be costly
        return ingr

    def get_dpad(self, compartment_id: int) -> float:
        """
        Return the largest encapsulating_radius and use it for padding

        Parameters
        ----------
        compartment_id
            ID of the compartment to get padding for

        Returns
        -------
        :
            Maximum radius for padding
        """
        mr = 0.0
        if compartment_id == 0:  # cytoplasm -> use cyto and all surfaces
            for ingr1 in self.activeIngr:
                if ingr1.compartment_id >= 0:
                    if hasattr(ingr1, "max_radius"):
                        r = ingr1.max_radius
                    else:
                        r = ingr1.encapsulating_radius
                    if r > mr:
                        mr = r
        else:
            for ingr1 in self.activeIngr:
                if (
                    ingr1.compartment_id == compartment_id
                    or ingr1.compartment_id == -compartment_id
                ):
                    if hasattr(ingr1, "max_radius"):
                        r = ingr1.max_radius
                    else:
                        r = ingr1.encapsulating_radius
                    if r > mr:
                        mr = r
        return mr

    def getPointToDrop(
        self,
        ingr: Ingredient,
        free_points: List[int],
        nbFreePoints: int,
        distance: List[float],
        spacing: float,
        compId: int,
        vRangeStart: float,
        vThreshStart: float,
    ) -> Tuple[bool, Union[int, float]]:
        """
        Decide next point to use for dropping a given ingredent. The picking can be
        random, based on closest distance, based on gradients, ordered.
        This function also update the available free point except when hack is on.

        Parameters
        ----------
        ingr
            Ingredient to place
        free_points
            List of available free points
        nbFreePoints
            Number of free points
        distance
            Distance array
        spacing
            Grid spacing
        compId
            Compartment ID
        vRangeStart
            Range start value
        vThreshStart
            Threshold start value

        Returns
        -------
        :
            Tuple of (success flag, point index or updated vRangeStart)
        """
        allIngrPts, allIngrDist = ingr.get_list_of_free_indices(
            distance,
            free_points,
            nbFreePoints,
            spacing,
            compId,
            self.freePtsUpdateThreshold,
        )

        if len(allIngrPts) == 0:
            t = time()
            ingr.completion = 1.0
            ind = self.activeIngr.index(ingr)
            # if ind == 0:
            vRangeStart = vRangeStart + self.normalizedPriorities[0]
            if ind > 0:
                # j = 0
                for j in range(ind):
                    self.thresholdPriorities[j] = (
                        self.thresholdPriorities[j] + self.normalizedPriorities[ind]
                    )
            self.activeIngr.pop(ind)
            # Start of massive overruling section from corrected thesis file of Sept. 25, 2012
            # this function also depend on the ingr.completiion that can be restored ?
            self.activeIngr0, self.activeIngr12 = self.callFunction(
                self.getSortedActiveIngredients, ([self.activeIngr])
            )
            self.log.info(f"No point left for ingredient {ingr.name}")
            self.log.info("len(allIngredients %d", len(self.activeIngr))
            self.log.info("len(self.activeIngr0) %d", len(self.activeIngr0))
            self.log.info("len(self.activeIngr12) %d", len(self.activeIngr12))

            self.activeIngre_saved = self.activeIngr[:]

            self.totalPriorities = 0  # 0.00001
            for priors in self.activeIngr12:
                pp = priors.priority
                self.totalPriorities = self.totalPriorities + pp
            previousThresh = 0
            self.normalizedPriorities = []
            self.thresholdPriorities = []
            # Graham- Once negatives are used, if picked random#
            # is below a number in this list, that item becomes
            # the active ingredient in the while loop below
            for priors in self.activeIngr0:
                self.normalizedPriorities.append(0)
                if self.pickWeightedIngr:
                    self.thresholdPriorities.append(2)
            for priors in self.activeIngr12:
                # pp1 = 0
                pp = priors.priority
                if self.totalPriorities != 0:
                    norm_priority = float(pp) / float(self.totalPriorities)
                else:
                    norm_priority = 0.0
                self.normalizedPriorities.append(norm_priority)
                if verbose > 1:
                    print(
                        "norm_priority is ",
                        norm_priority,
                        " pp is ",
                        pp,
                        " tp is ",
                        norm_priority + previousThresh,
                    )
                self.thresholdPriorities.append(norm_priority + previousThresh)
                previousThresh = norm_priority + float(previousThresh)
            self.activeIngr = self.activeIngr0 + self.activeIngr12
            self.log.info("time to reject the picking %d", time() - t)

            return False, vRangeStart

        if self.pickRandPt:
            self.log.info("picking random point")
            if ingr.packing_mode == "close":
                order = np.argsort(allIngrDist)
                # pick point with closest distance
                ptInd = allIngrPts[order[0]]
                if ingr.rejectionCounter < len(order):
                    ptInd = allIngrPts[order[ingr.rejectionCounter]]
                else:
                    ptIndr = int(uniform(0.0, 1.0) * len(allIngrPts))
                    ptInd = allIngrPts[ptIndr]

            elif ingr.packing_mode == "gradient" and self.use_gradient:
                # get the most probable point using the gradient
                # use the gradient weighted map and get mot probabl point
                self.log.info("pick point from gradients %d", (len(allIngrPts)))
                ptInd = Gradient.pick_point_for_ingredient(
                    ingr, allIngrPts, self.gradients
                )
            else:
                # pick a point randomly among free points
                # random or uniform?
                ptIndr = int(uniform(0.0, 1.0) * len(allIngrPts))
                ptInd = allIngrPts[ptIndr]
            if ptInd is None:
                t = time()
                self.log.info(f"No point left for ingredient {ingr.name}")
                ingr.completion = 1.0
                ind = self.activeIngr.index(ingr)
                # if ind == 0:
                vRangeStart = vRangeStart + self.normalizedPriorities[0]
                if ind > 0:
                    # j = 0
                    for j in range(ind):
                        self.thresholdPriorities[j] = (
                            self.thresholdPriorities[j] + self.normalizedPriorities[ind]
                        )
                self.activeIngr.pop(ind)
                if verbose > 1:
                    print(
                        "popping this gradient ingredient array must be redone using"
                        " Sept 25,",
                        " 2011 thesis version as above for nongradient ingredients,"
                        " TODO: July 5, 2012",
                    )
                self.thresholdPriorities.pop(ind)
                self.normalizedPriorities.pop(ind)
                if verbose > 1:
                    print(("time to reject the picking", time() - t))
                    print(("vRangeStart", vRangeStart))
                return False, vRangeStart

        else:
            self.log.info("sorting index")
            allIngrPts.sort()
            ptInd = allIngrPts[0]
        return True, ptInd

    def removeOnePoint(self, pt: int, free_points: List[int], nbFreePoints: int) -> int:
        """
        Remove one point from the free points list

        Parameters
        ----------
        pt
            Point index to remove
        free_points
            List of free points
        nbFreePoints
            Current number of free points

        Returns
        -------
        :
            Updated number of free points
        """
        try:
            # New system replaced by Graham on Aug 18, 2012
            nbFreePoints -= 1
            vKill = free_points[pt]
            vLastFree = free_points[nbFreePoints]
            free_points[vKill] = vLastFree
            free_points[vLastFree] = vKill
            # End New replaced by Graham on Aug 18, 2012
        except:  # noqa: E722
            pass
        return nbFreePoints

    def getTotalNbObject(
        self, allIngredients: List[Any], update_partner: bool = False
    ) -> int:
        """
        Calculate total number of objects to be placed

        Parameters
        ----------
        allIngredients
            List of all ingredients
        update_partner
            Whether to update partner ingredients

        Returns
        -------
        :
            Total number of objects to place
        """
        totalNbIngr = 0
        for ingr in allIngredients:
            if ingr.type == "Grow":
                totalNbIngr += int(
                    ingr.left_to_place * (ingr.length / ingr.unit_length)
                )
            else:
                totalNbIngr += ingr.left_to_place
            if update_partner:
                self.set_partners_ingredient(ingr)
        return totalNbIngr

    def prep_molecules_for_save(
        self, distances: List[float], free_points: List[int], nbFreePoints: int
    ) -> List[Any]:
        """
        Prepare molecules data for saving

        Parameters
        ----------
        distances
            Distance array
        free_points
            List of free points
        nbFreePoints
            Number of free points

        Returns
        -------
        :
            List of all packed objects
        """
        self.distancesAfterFill = distances[:]
        self.freePointsAfterFill = free_points[:]
        self.nbFreePointsAfterFill = nbFreePoints
        self.distanceAfterFill = distances[:]

        if self.runTimeDisplay and autopack.helper.host == "simularium":
            autopack.helper.writeToFile("./realtime", self.boundingBox)
        return self.packed_objects.get_all()

    def check_new_placement(self, new_position: List[float]) -> bool:
        """
        Check if a new placement position is valid

        Parameters
        ----------
        new_position
            Position coordinates to check

        Returns
        -------
        :
            True if placement is too close to existing objects
        """
        distances = self.get_all_distances(new_position)
        if len(distances) == 0:
            # nothing has been packed yet
            return False
        min_distance = min(distances)
        expected_min_distance = self.smallestProteinSize * 2
        if min_distance < expected_min_distance:
            log.error(
                f"New placement {new_position} is too close to existing objects."
                f" Minimum distance {min_distance} is less than expected"
                f" {expected_min_distance}."
            )
        return min_distance < expected_min_distance

    def distance_check_failed(self) -> bool:
        """
        Check if distance constraints are violated

        Returns
        -------
        :
            True if minimum distance is less than expected
        """
        distances = self.get_all_distances()
        if len(distances) == 0:
            # nothing has been packed yet
            return False
        min_distance = min(distances)
        expected_min_distance = self.smallestProteinSize * 2
        return min_distance < expected_min_distance + 0.001

    def update_variable_ingredient_attributes(self, allIngredients: List[Any]) -> None:
        """
        Updates variable attributes for all ingredients based on input options

        Parameters
        ----------
        allIngredients
            List of all ingredients to update
        """
        for ingr in allIngredients:
            if hasattr(ingr, "count_options") and ingr.count_options is not None:

                count = get_value_from_distribution(
                    distribution_options=ingr.count_options,
                    return_int=True,
                )
                if count is not None:
                    ingr.count = count
                    ingr.left_to_place = count

            if hasattr(ingr, "size_options") and ingr.size_options is not None:
                max_radius = get_max_value_from_distribution(
                    distribution_options=ingr.size_options
                )
                if max_radius is not None:
                    ingr.max_radius = max_radius

                min_radius = get_min_value_from_distribution(
                    distribution_options=ingr.size_options
                )
                if min_radius is not None:
                    ingr.min_radius = min_radius

    def add_seed_number_to_base_name(self, seed_number: int) -> str:
        """
        Add seed number to base name

        Parameters
        ----------
        seed_number
            Seed number to add

        Returns
        -------
        :
            Base name with seed number appended
        """
        return f"{self.base_name}_seed_{seed_number}"

    def set_result_file_name(self, seed_basename: str) -> None:
        """
        Sets the result file name using the output folder path and a given seed basename

        Parameters
        ----------
        seed_basename
            Base name with seed for the result file
        """
        self.result_file = str(self.out_folder / f"results_{seed_basename}")

    def update_after_place(self, grid_point_index: int) -> None:
        """
        Update tracking variables after successful placement

        Parameters
        ----------
        grid_point_index
            Index of the grid point where placement occurred
        """
        self.order[grid_point_index] = self.lastrank
        self.lastrank += 1
        self.nb_ingredient += 1

    def pack_grid(
        self,
        seedNum: int = 0,
        name: Optional[str] = None,
        vTestid: int = 3,
        **kw,
    ) -> List[Any]:
        """
        Fill the grid by picking an ingredient first and then
        find a suitable point using the ingredient's placer object

        Parameters
        ----------
        seedNum
            Random seed number
        name
            Name for this packing run
        vTestid
            Test ID value
        **kw
            Additional keyword arguments

        Returns
        -------
        :
            List of all packed objects
        """
        # set periodicity
        autopack.testPeriodicity = self.use_periodicity
        t1 = time()
        seed_base_name = self.add_seed_number_to_base_name(seedNum)
        self.set_result_file_name(seed_base_name)
        self.timeUpDistLoopTotal = 0
        self.static = []
        if self.grid is None:
            self.log.error("no grid setup")
            return
        # create a list of active ingredients indices in all recipes to allow
        # removing inactive ingredients when molarity is reached
        allIngredients = self.callFunction(self.getActiveIng)

        # set the number of ingredients to pack
        self.update_variable_ingredient_attributes(allIngredients)

        # verify partner
        usePP = False
        if "usePP" in kw:
            usePP = kw["usePP"]

        self.cFill = self.nFill

        if name is None:
            name = "F" + str(self.nFill)
        self.FillName.append(name)
        self.nFill += 1
        # seed random number generator
        self.setSeed(seedNum)
        # create copies of the distance array as they change when molecules
        # are added, this array can be restored/saved before filling
        free_points = self.grid.free_points[:]
        self.grid.nbFreePoints = nbFreePoints = len(free_points)  # -1
        if "fbox" in kw:
            self.fbox = kw["fbox"]
        if self.fbox is not None and not self.EnviroOnly:
            self.freePointMask = np.ones(nbFreePoints, dtype="int32")
            bb_insidepoint = self.grid.getPointsInCube(self.fbox, [0, 0, 0], 1.0)[:]
            self.freePointMask[bb_insidepoint] = 0
            bb_outside = np.nonzero(self.freePointMask)
            self.grid.compartment_ids[bb_outside] = 99999
        compartment_ids = self.grid.compartment_ids

        for compartment in self.compartments:
            compartment.store_packed_object(self)

        # why a copy? --> can we split ?
        distances = self.grid.distToClosestSurf[:]
        spacing = self.spacing or self.smallestProteinSize

        # DEBUG stuff, should be removed later
        self.jitterVectors = []
        self.jitterLength = 0.0
        self.totnbJitter = 0
        self.maxColl = 0.0
        self.successfullJitter = []
        self.failedJitter = []

        # this function also depend on the ingr.completiion that can be restored ?
        self.activeIngr0, self.activeIngr12 = self.callFunction(
            self.getSortedActiveIngredients, ([allIngredients])
        )

        self.log.info("len(allIngredients %d", len(allIngredients))
        self.log.info("len(self.activeIngr0) %d", len(self.activeIngr0))
        self.log.info("len(self.activeIngr12) %d", len(self.activeIngr12))
        self.activeIngre_saved = self.activeIngr[:]

        self.totalPriorities = 0  # 0.00001
        for priors in self.activeIngr12:
            pp = priors.priority
            self.totalPriorities = self.totalPriorities + pp
            self.log.info("totalPriorities = %d", self.totalPriorities)
        previousThresh = 0
        self.normalizedPriorities = []
        self.thresholdPriorities = []
        # Graham- Once negatives are used, if picked random#
        # is below a number in this list, that item becomes
        # the active ingredient in the while loop below
        for priors in self.activeIngr0:
            self.normalizedPriorities.append(0)
            if self.pickWeightedIngr:  # why ?
                self.thresholdPriorities.append(2)
        for priors in self.activeIngr12:
            # pp1 = 0
            pp = priors.priority
            if self.totalPriorities != 0:
                norm_priority = float(pp) / float(self.totalPriorities)
            else:
                norm_priority = 0.0
            self.normalizedPriorities.append(norm_priority)
            self.thresholdPriorities.append(norm_priority + previousThresh)
            previousThresh = norm_priority + float(previousThresh)
        self.activeIngr = self.activeIngr0 + self.activeIngr12

        nls = 0
        totalNumMols = 0
        self.totalNbIngr = self.getTotalNbObject(allIngredients, update_partner=True)
        if len(self.thresholdPriorities) == 0:
            for ingr in allIngredients:
                totalNumMols += ingr.left_to_place
            self.log.info("totalNumMols pack_grid if = %d", totalNumMols)
        else:
            for threshProb in self.thresholdPriorities:
                nameMe = self.activeIngr[nls]
                totalNumMols += nameMe.left_to_place
                self.log.info(
                    "threshprop pack_grid else is %f for ingredient: %s %s %d",
                    threshProb,
                    nameMe,
                    nameMe.name,
                    nameMe.left_to_place,
                )
                self.log.info("totalNumMols pack_grid else = %d", totalNumMols)
                nls += 1

        vRangeStart = 0.0
        tCancelPrev = time()
        ptInd = 0

        PlacedMols = 0
        vThreshStart = 0.0  # Added back by Graham on July 5, 2012 from Sept 25, 2011 thesis version

        # ==============================================================================
        #         #the big loop
        # ==============================================================================
        dump_freq = self.dump_freq  # 120.0#every minute
        dump = self.dump
        stime = time()
        if self.show_progress_bar:
            pbar = tqdm(total=totalNumMols, mininterval=0, miniters=1)
            pbar.set_description(f"Packing {self.name}_{self.version}")
        while nbFreePoints:
            self.log.info(
                ".........At start of while loop, with vRangeStart = %d", vRangeStart
            )

            # breakin test
            if len(self.activeIngr) == 0:
                self.log.warning("exit packing loop because of len****")
                if hasattr(self, "afviewer"):
                    if self.afviewer is not None and hasattr(self.afviewer, "vi"):
                        self.afviewer.vi.resetProgressBar()
                        self.afviewer.vi.progressBar(label="Filling Complete")
                break
            if vRangeStart > 1:
                self.log.info("exit packing loop because vRange and hence Done!!!****")
                break
            if self.cancelDialog:
                tCancel = time()
                if tCancel - tCancelPrev > 10.0:
                    cancel = self.displayCancelDialog()
                    if cancel:
                        self.log.info(
                            "canceled by user: we'll fill with current objects up to"
                            " time %d",  # noqa: E510
                            tCancel,
                        )
                        break
                    # if OK, do nothing, i.e., continue loop
                    # (but not the function continue)
                    tCancelPrev = time()

            # pick an ingredient
            ingr = self.pickIngredient(vThreshStart)
            if hasattr(self, "afviewer"):
                p = (
                    (float(PlacedMols)) / float(totalNumMols)
                ) * 100.0  # This code shows 100% of ingredients all the time
                if self.afviewer is not None and hasattr(self.afviewer, "vi"):
                    self.afviewer.vi.progressBar(
                        progress=int(p),
                        label=ingr.name + " " + str(ingr.completion),
                    )
                    if self.afviewer.renderDistance:
                        self.afviewer.vi.displayParticleVolumeDistance(distances, self)
            current_ingr_compartment = ingr.compartment_id
            # compute dpad which is the distance at which we need to update
            # distances after the drop is successfull
            max_radius = self.get_dpad(current_ingr_compartment)

            self.log.info(
                f"picked Ingr radius {ingr.min_radius}, compartment_id"
                f" {current_ingr_compartment}"
            )

            # find the points that can be used for this ingredient
            ##

            if ingr.compartment_id > 0:
                compartment = self.compartments[ingr.compartment_id - 1]
                surface_points = compartment.surfacePoints
                res = [True, surface_points[int(random() * len(surface_points))]]
            else:
                res = self.getPointToDrop(
                    ingr,
                    free_points,
                    nbFreePoints,
                    distances,
                    spacing,
                    compartment_ids,
                    vRangeStart,
                    vThreshStart,
                )  # (Bool, ptInd)
            if res[0]:
                ptInd = res[1]
                if ptInd > len(distances):
                    self.log.warning(
                        "point index outside of grid length, should never be true ",
                        ptInd,
                    )
                    continue
            else:
                self.log.info("vRangeStart coninue ", res)
                vRangeStart = res[1]
                continue
            # NOTE: should we do the close partner check here instead of in the place functions?
            # place the ingredient
            if self.overwrite_place_method:
                ingr.place_method = self.place_method

            if ingr.encapsulating_radius > self.largestProteinSize:
                self.largestProteinSize = ingr.encapsulating_radius

            self.log.info(
                "attempting to place near %d: %r",
                ptInd,
                self.grid.masterGridPositions[ptInd],
            )
            collision_possible = True
            # if distances[ptInd] >= ingr.encapsulating_radius + ingr.getMaxJitter(
            #     spacing
            # ):
            #     # there is no possible collision here
            #     collision_possible = False
            (
                success,
                insidePoints,
                newDistPoints,
            ) = ingr.attempt_to_pack_at_grid_location(
                self, ptInd, distances, max_radius, spacing, usePP, collision_possible
            )
            self.log.info(
                "after place attempt, placed: %r, number of free points:%d, length of"
                " free points=%d",
                success,
                nbFreePoints,
                len(free_points),
            )
            if success:
                nbFreePoints = BaseGrid.updateDistances(
                    insidePoints, newDistPoints, free_points, nbFreePoints, distances
                )
                self.grid.distToClosestSurf = np.array(distances[:])
                self.grid.free_points = np.array(free_points[:])
                self.grid.nbFreePoints = len(free_points)  # -1
                # update largest protein size
                # problem when the encapsulating_radius is actually wrong
                if ingr.encapsulating_radius > self.largestProteinSize:
                    self.largestProteinSize = ingr.encapsulating_radius

                PlacedMols += 1
                # if self.stop_on_collision:
                # ingredient_too_close = self.distance_check_failed()
                # if ingredient_too_close:
                #     print("GOT A FAIL", self.grid.masterGridPositions[ptInd])
                #     nbFreePoints = 0
                if self.show_progress_bar:
                    pbar.update(1)
            else:
                self.log.info("rejected %r", ingr.rejectionCounter)

            if ingr.completion >= 1.0:
                ind = self.activeIngr.index(ingr)

                self.log.info(f"completed*************** {ingr.name}")
                self.log.info(f"PlacedMols = {PlacedMols}")
                self.log.info(f"activeIngr index of {ingr.name}, {ind}")
                self.log.info(
                    f"threshold p len {len(self.thresholdPriorities)},"
                    f" {len(self.normalizedPriorities)}"
                )
                if ind > 0:
                    # j = 0
                    for j in range(ind):
                        if j >= len(self.thresholdPriorities) or j >= len(
                            self.normalizedPriorities
                        ):
                            continue
                        self.thresholdPriorities[j] = (
                            self.thresholdPriorities[j] + self.normalizedPriorities[ind]
                        )
                self.activeIngr.pop(ind)
                self.activeIngr0, self.activeIngr12 = self.callFunction(
                    self.getSortedActiveIngredients, ([self.activeIngr])
                )
                self.log.info(f"len(self.activeIngr0) {len(self.activeIngr0)}")
                self.log.info(f"len(self.activeIngr12) {len(self.activeIngr12)}")
                self.activeIngre_saved = self.activeIngr[:]

                self.totalPriorities = 0  # 0.00001
                for priors in self.activeIngr12:
                    pp = priors.priority
                    self.totalPriorities = self.totalPriorities + pp
                #                    print ('totalPriorities = ', self.totalPriorities)
                previousThresh = 0
                self.normalizedPriorities = []
                self.thresholdPriorities = []
                # Graham- Once negatives are used, if picked random#
                # is below a number in this list, that item becomes
                # the active ingredient in the while loop below
                for priors in self.activeIngr0:
                    self.normalizedPriorities.append(0)
                    if self.pickWeightedIngr:
                        self.thresholdPriorities.append(2)
                for priors in self.activeIngr12:
                    # pp1 = 0
                    pp = priors.priority
                    if self.totalPriorities != 0:
                        norm_priority = float(pp) / float(self.totalPriorities)
                    else:
                        norm_priority = 0.0
                    self.normalizedPriorities.append(norm_priority)
                    #                    print ('norm_priority is ', np, ' pp is ', pp, ' tp is ', np + previousThresh)
                    self.thresholdPriorities.append(norm_priority + previousThresh)
                    previousThresh = norm_priority + float(previousThresh)
                self.activeIngr = self.activeIngr0 + self.activeIngr12

            if dump and ((time() - stime) > dump_freq):
                all_objects = self.prep_molecules_for_save(
                    distances,
                    free_points,
                    nbFreePoints,
                )
                stime = time()
                self.log.info(f"placed {len(self.packed_objects.get_ingredients())}")
                if self.saveResult:
                    self.save_result(
                        free_points,
                        distances=distances,
                        all_objects=all_objects,
                    )

        t2 = time()
        if self.show_progress_bar:
            pbar.close()
        self.log.info("time to fill %d", t2 - t1)
        all_objects = self.prep_molecules_for_save(distances, free_points, nbFreePoints)
        if self.saveResult:
            self.save_result(
                free_points,
                distances=distances,
                all_objects=all_objects,
            )

        if kw.get("clean_grid_cache", False):
            grid_file_name = str(self.previous_grid_file).split(os.path.sep)[-1]
            self.clean_grid_cache(grid_file_name=grid_file_name)

        return all_objects

    def restore_molecules_array(self, ingr: Ingredient) -> None:
        """
        Restore molecules array for an ingredient

        Parameters
        ----------
        ingr
            Ingredient to restore molecules for
        """
        pass
        # if len(ingr.results):
        #     for elem in ingr.results:
        # TODO: fix this to reset ingredients from results
        # if ingr.compartment_id == 0:
        #     self.molecules.append(
        #         [elem[0], np.array(elem[1]), ingr, 0, ingr.radius]
        #     )
        # else:
        #     ingr.recipe.compartment.molecules.append(
        #         [elem[0], np.array(elem[1]), ingr, 0, ingr.radius]
        #     )

    def restore(
        self,
        result: List[Any],
        orgaresult: List[List[Any]],
        freePoint: List[int],
        tree: bool = False,
    ) -> Dict[str, Any]:
        """
        Restore environment state from saved results

        Parameters
        ----------
        result
            Main result data
        orgaresult
            Organelle result data
        freePoint
            Free point data
        tree
            Whether to build spatial tree

        Returns
        -------
        :
            Dictionary of restored ingredients
        """
        # should we used the grid ? the freePoint can be computed
        # result is [pos,rot,ingr.name,ingr.compartment_id,ptInd]
        # orgaresult is [[pos,rot,ingr.name,ingr.compartment_id,ptInd],[pos,rot,ingr.name,ingr.compartment_id,ptInd]...]
        # after restore we can build the grid and fill!
        # ingredient based dictionary
        # TODO: refactor with new packed_objects

        ingredients = {}
        molecules = []
        for elem in result:
            pos, rot, name, compartment_id, ptInd = elem
            # needto check the name if it got the comp rule
            ingr = self.get_ingredient_by_name(name, compartment_id)
            if ingr is not None:
                molecules.append([pos, np.array(rot), ingr, ptInd])
                if name not in ingredients:
                    ingredients[name] = [ingr, [], [], []]
                mat = np.array(rot)
                mat[:3, 3] = pos
                ingredients[name][1].append(pos)
                ingredients[name][2].append(np.array(rot))
                ingredients[name][3].append(np.array(mat))
                ingr.results.append([pos, rot])
        if self.exteriorRecipe:
            self.exteriorRecipe.molecules = molecules
        if len(orgaresult) == len(self.compartments):
            for i, o in enumerate(self.compartments):
                molecules = []
                for elem in orgaresult[i]:
                    pos, rot, name, compartment_id, ptInd = elem
                    ingr = self.get_ingredient_by_name(name, compartment_id)
                    if ingr is not None:
                        molecules.append([pos, np.array(rot), ingr, ptInd])
                        if name not in ingredients:
                            ingredients[name] = [ingr, [], [], []]
                        mat = np.array(rot)
                        mat[:3, 3] = pos
                        ingredients[name][1].append(pos)
                        ingredients[name][2].append(np.array(rot))
                        ingredients[name][3].append(np.array(mat))
                        ingr.results.append([pos, rot])
                o.molecules = molecules
        # consider that one filling have occured
        if len(self.packed_objects.get_ingredients()) and tree:
            self.close_ingr_bhtree = KDTree(
                self.packed_objects.get_positions(), leafsize=10
            )
        self.cFill = self.nFill
        self.ingr_result = ingredients
        if len(freePoint):
            self.restoreFreePoints(freePoint)
        return ingredients

    def restoreFreePoints(self, freePoint: List[int]) -> None:
        """
        Restore free points from saved data

        Parameters
        ----------
        freePoint
            List of free points to restore
        """
        self.free_points = self.freePointsAfterFill = freePoint
        self.nbFreePointsAfterFill = len(freePoint)
        self.distanceAfterFill = self.grid.distToClosestSurf
        self.distancesAfterFill = self.grid.distToClosestSurf

    def loadFreePoint(self, resultfilename: str) -> List[int]:
        """
        Load free points from file

        Parameters
        ----------
        resultfilename
            Path to result file

        Returns
        -------
        :
            List of free points loaded from file
        """
        rfile = open(resultfilename + "_free_points", "rb")
        freePoint = pickle.load(rfile)
        rfile.close()
        return freePoint

    def store(self, resultfilename: Optional[str] = None) -> None:
        """
        Store results to file

        Parameters
        ----------
        resultfilename
            Path to store results, uses default if None
        """
        if resultfilename is None:
            resultfilename = self.result_file
        resultfilename = autopack.fixOnePath(resultfilename)
        with open(resultfilename, "wb") as rfile:
            pickle.dump(self.packed_objects.get_ingredients(), rfile)
        with open(resultfilename + "_free_points", "wb") as rfile:
            pickle.dump(self.grid.free_points, rfile)

    @classmethod
    def dropOneIngr(
        self,
        pos: List[float],
        rot: np.ndarray,
        ingrname: str,
        ingrcompNum: int,
        ptInd: int,
        rad: float = 1.0,
    ) -> str:
        """
        Format one ingredient data as string

        Parameters
        ----------
        pos
            Position coordinates
        rot
            Rotation matrix
        ingrname
            Ingredient name
        ingrcompNum
            Ingredient compartment number
        ptInd
            Point index
        rad
            Radius value

        Returns
        -------
        :
            Formatted string representation
        """
        line = ""
        line += "<%f,%f,%f>," % (pos[0], pos[1], pos[2])
        r = rot.reshape(16)
        line += "<"
        for i in range(15):
            line += "%f," % (r[i])
        line += "%f>," % (r[15])
        line += "<%f>,<%s>,<%d>,<%d>\n" % (rad, ingrname, ingrcompNum, ptInd)
        return line

    @classmethod
    def getOneIngr(
        self, line: str
    ) -> Tuple[Tuple[float, float, float], Tuple[float, ...], str, int, int, float]:
        """
        Parse one ingredient from string line

        Parameters
        ----------
        line
            String line to parse

        Returns
        -------
        :
            Tuple of (position, rotation, ingredient name, compartment number, point index, radius)
        """
        elem = line.split("<")
        pos = eval(elem[1][:-2])
        rot = eval(elem[2][:-2])
        rad = eval(elem[3][:-2])
        ingrname = elem[4][:-2]
        ingrcompNum = eval(elem[5][:-2])
        ptInd = eval(elem[6].split(">")[0])
        return pos, rot, ingrname, ingrcompNum, ptInd, rad

    #    @classmethod
    def getOneIngrJson(
        self, ingr: Ingredient, ingrdic: Dict[str, Any]
    ) -> Tuple[List[Any], str, int, int, float]:
        """
        Get one ingredient data from JSON dictionary

        Parameters
        ----------
        ingr
            Ingredient object
        ingrdic
            Ingredient dictionary from JSON

        Returns
        -------
        :
            Tuple of (results, composition name, compartment ID, count, radius)
        """
        #        name_ingr = ingr.name
        #        if name_ingr not in ingrdic:
        #            name_ingr = ingr.composition_name
        #        for r in ingr.results:
        #            ingrdic[name_ingr]["results"].append([r[0]],r[1],)
        #        print ("growingr?",ingr,ingr.name,isinstance(ingr, GrowIngredient))
        if isinstance(ingr, GrowIngredient) or isinstance(ingr, ActinIngredient):
            ingr.nbCurve = ingrdic["nbCurve"]
            ingr.listePtLinear = []
            for i in range(ingr.nbCurve):
                ingr.listePtLinear.append(ingrdic["curve" + str(i)])
            #            print ("nbCurve?",ingr.nbCurve,ingrdic["nbCurve"])
        return (
            ingrdic["results"],
            ingr.composition_name,
            ingr.compartment_id,
            1,
            ingr.encapsulating_radius,
        )  # ingrdic["compartment_id"],1,ingrdic["encapsulating_radius"]

    def load_asTxt(
        self, resultfilename: Optional[str] = None
    ) -> Tuple[List[Any], List[List[Any]], List[int]]:
        """
        Load results from text file

        Parameters
        ----------
        resultfilename
            Path to result file, uses default if None

        Returns
        -------
        :
            Tuple of (result, organelle result, free points)
        """
        if resultfilename is None:
            resultfilename = self.result_file
        rfile = open(resultfilename, "r")
        # needto parse
        result = []
        orgaresult = []  # [[],]*len(self.compartments)
        for i in range(len(self.compartments)):
            orgaresult.append([])
        #        mry90 = helper.rotation_matrix(-math.pi/2.0, [0.0,1.0,0.0])
        #        np.array([[0.0, 1.0, 0.0, 0.0],
        #                 [-1., 0.0, 0.0, 0.0],
        #                 [0.0, 0.0, 1.0, 0.0],
        #                 [0.0, 0.0, 0.0, 1.0]])
        lines = rfile.readlines()
        for line in lines:
            if not len(line) or len(line) < 6:
                continue
            pos, rot, ingrname, ingrcompNum, ptInd, rad = self.getOneIngr(line)
            # should I multiply here
            r = np.array(rot).reshape(
                4, 4
            )  # np.matrix(mry90)*np.matrix(np.array(rot).reshape(4,4))
            if ingrcompNum == 0:
                result.append(
                    [np.array(pos), np.array(r), ingrname, ingrcompNum, ptInd]
                )
            else:
                orgaresult[abs(ingrcompNum) - 1].append(
                    [np.array(pos), np.array(r), ingrname, ingrcompNum, ptInd]
                )
            #        for i, orga in enumerate(self.compartments):
            #            orfile = open(resultfilename+"ogra"+str(i),'rb')
            #            orgaresult.append(pickle.load(orfile))
            #            orfile.close()
            #        rfile.close()
            #        rfile = open(resultfilename+"free_points",'rb')
        freePoint = []  # pickle.load(rfile)
        try:
            rfile = open(resultfilename + "_free_points", "rb")
            freePoint = pickle.load(rfile)
            rfile.close()
        except:  # noqa: E722
            pass
        return result, orgaresult, freePoint

    def collectResultPerIngredient(self) -> None:
        """
        Collect results per ingredient from packed objects
        """

        def cb(ingr):
            ingr.results = []

        self.loopThroughIngr(cb)
        for obj in self.packed_objects.get_ingredients():
            ingr = obj.ingredient
            if isinstance(ingr, GrowIngredient) or isinstance(ingr, ActinIngredient):
                pass  # already store
            else:
                ingr.results.append([obj.position, obj.rotation])

    def load_asJson(
        self, resultfilename: Optional[str] = None
    ) -> Tuple[List[Any], List[List[Any]], List[int]]:
        """
        Load results from JSON file

        Parameters
        ----------
        resultfilename
            Path to result file, uses default if None

        Returns
        -------
        :
            Tuple of (result, organelle result, free points)
        """
        if resultfilename is None:
            resultfilename = self.result_file
        with open(resultfilename, "r") as fp:  # doesnt work with symbol link ?
            if autopack.use_json_hook:
                self.result_json = json.load(
                    fp, object_pairs_hook=OrderedDict
                )  # ,indent=4, separators=(',', ': ')
            else:
                self.result_json = json.load(fp)
            # needto parse
        result = []
        orgaresult = []
        r = self.exteriorRecipe
        if r:
            if "exteriorRecipe" in self.result_json:
                for ingr in r.ingredients:
                    name_ingr = ingr.name
                    if name_ingr not in self.result_json["exteriorRecipe"]:
                        # backward compatiblity
                        if (
                            ingr.composition_name
                            not in self.result_json["exteriorRecipe"]
                        ):
                            continue
                        else:
                            name_ingr = ingr.composition_name
                    iresults, ingrname, ingrcompNum, ptInd, rad = self.getOneIngrJson(
                        ingr, self.result_json["exteriorRecipe"][name_ingr]
                    )
                    ingr.results = []
                    for r in iresults:
                        rot = np.array(r[1]).reshape(
                            4, 4
                        )  # np.matrix(mry90)*np.matrix(np.array(rot).reshape(4,4))
                        ingr.results.append([np.array(r[0]), rot])
                        result.append([np.array(r[0]), rot, ingrname, ingrcompNum, 1])
                    # organelle ingr
        for i, orga in enumerate(self.compartments):
            orgaresult.append([])
            # organelle surface ingr
            rs = orga.surfaceRecipe
            if rs:
                if orga.name + "_surfaceRecipe" in self.result_json:
                    for ingr in rs.ingredients:
                        name_ingr = ingr.name
                        # replace number by name ?
                        if (
                            orga.name + "_surf_" + ingr.composition_name
                            in self.result_json[orga.name + "_surfaceRecipe"]
                        ):
                            name_ingr = orga.name + "_surf_" + ingr.composition_name
                        if (
                            name_ingr
                            not in self.result_json[orga.name + "_surfaceRecipe"]
                        ):
                            # backward compatiblity
                            if (
                                ingr.composition_name
                                not in self.result_json[orga.name + "_surfaceRecipe"]
                            ):
                                continue
                            else:
                                name_ingr = ingr.composition_name
                        (
                            iresults,
                            ingrname,
                            ingrcompNum,
                            ptInd,
                            rad,
                        ) = self.getOneIngrJson(
                            ingr,
                            self.result_json[orga.name + "_surfaceRecipe"][name_ingr],
                        )
                        ingr.results = []
                        for r in iresults:
                            rot = np.array(r[1]).reshape(
                                4, 4
                            )  # np.matrix(mry90)*np.matrix(np.array(rot).reshape(4,4))
                            ingr.results.append([np.array(r[0]), rot])
                            orgaresult[abs(ingrcompNum) - 1].append(
                                [np.array(r[0]), rot, ingrname, ingrcompNum, 1]
                            )
            # organelle matrix ingr
            ri = orga.innerRecipe
            if ri:
                if orga.name + "_innerRecipe" in self.result_json:
                    for ingr in ri.ingredients:
                        name_ingr = ingr.name
                        if (
                            orga.name + "_int_" + ingr.composition_name
                            in self.result_json[orga.name + "_innerRecipe"]
                        ):
                            name_ingr = orga.name + "_int_" + ingr.composition_name
                        if (
                            name_ingr
                            not in self.result_json[orga.name + "_innerRecipe"]
                        ):
                            # backward compatiblity
                            if (
                                ingr.composition_name
                                not in self.result_json[orga.name + "_innerRecipe"]
                            ):
                                continue
                            else:
                                name_ingr = ingr.composition_name
                        (
                            iresults,
                            ingrname,
                            ingrcompNum,
                            ptInd,
                            rad,
                        ) = self.getOneIngrJson(
                            ingr,
                            self.result_json[orga.name + "_innerRecipe"][name_ingr],
                        )
                        ingr.results = []
                        for r in iresults:
                            rot = np.array(r[1]).reshape(
                                4, 4
                            )  # np.matrix(mry90)*np.matrix(np.array(rot).reshape(4,4))
                            ingr.results.append([np.array(r[0]), rot])
                            orgaresult[abs(ingrcompNum) - 1].append(
                                [np.array(r[0]), rot, ingrname, ingrcompNum, 1]
                            )
        freePoint = []  # pickle.load(rfile)
        try:
            rfile = open(resultfilename + "_free_points", "rb")
            freePoint = pickle.load(rfile)
            rfile.close()
        except:  # noqa: E722
            pass
        return result, orgaresult, freePoint

    def dropOneIngrJson(self, ingr: Ingredient, rdic: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create JSON dictionary for one ingredient

        Parameters
        ----------
        ingr
            Ingredient object
        rdic
            Result dictionary

        Returns
        -------
        :
            Dictionary containing ingredient data for JSON
        """
        adic = OrderedDict()  # [ingr.name]
        adic["compartment_id"] = ingr.compartment_id
        adic["encapsulating_radius"] = float(ingr.encapsulating_radius)
        adic["results"] = []
        for r in ingr.results:
            if hasattr(r[0], "tolist"):
                r[0] = r[0].tolist()
            if hasattr(r[1], "tolist"):
                r[1] = r[1].tolist()
            adic["results"].append([r[0], r[1]])
        if isinstance(ingr, GrowIngredient) or isinstance(ingr, ActinIngredient):
            adic["nbCurve"] = ingr.nbCurve
            for i in range(ingr.nbCurve):
                lp = np.array(ingr.listePtLinear[i])
                ingr.listePtLinear[i] = lp.tolist()
                adic["curve" + str(i)] = ingr.listePtLinear[i]
            #        print adic
        return adic

    def store_asJson(
        self, resultfilename: Optional[str] = None, indent: bool = True
    ) -> None:
        """
        Store results as JSON file

        Parameters
        ----------
        resultfilename
            Path to store results, uses default if None
        indent
            Whether to indent JSON output
        """
        if resultfilename is None:
            resultfilename = self.result_file
            resultfilename = autopack.fixOnePath(resultfilename)  # retireve?
        # if result file_name start with http?
        if resultfilename.find("http") != -1 or resultfilename.find("ftp") != -1:
            log.info(
                "Please provide a correct file name for the result file %s",
                resultfilename,
            )
        self.collectResultPerIngredient()
        self.result_json = OrderedDict()
        self.result_json["recipe"] = self.setupfile  # replace server?
        r = self.exteriorRecipe
        if r:
            self.result_json["exteriorRecipe"] = OrderedDict()
            for ingr in r.ingredients:
                self.result_json["exteriorRecipe"][
                    ingr.composition_name
                ] = self.dropOneIngrJson(ingr, self.result_json["exteriorRecipe"])

        # compartment ingr
        for orga in self.compartments:
            # compartment surface ingr
            rs = orga.surfaceRecipe
            if rs:
                self.result_json[orga.name + "_surfaceRecipe"] = OrderedDict()
                for ingr in rs.ingredients:
                    self.result_json[orga.name + "_surfaceRecipe"][
                        ingr.composition_name
                    ] = self.dropOneIngrJson(
                        ingr, self.result_json[orga.name + "_surfaceRecipe"]
                    )
            # compartment matrix ingr
            ri = orga.innerRecipe
            if ri:
                self.result_json[orga.name + "_innerRecipe"] = OrderedDict()
                for ingr in ri.ingredients:
                    self.result_json[orga.name + "_innerRecipe"][
                        ingr.composition_name
                    ] = self.dropOneIngrJson(
                        ingr, self.result_json[orga.name + "_innerRecipe"]
                    )
        with open(resultfilename, "w") as fp:  # doesnt work with symbol link ?
            if indent:
                json.dump(
                    self.result_json, fp, indent=1, separators=(",", ":")
                )  # ,indent=4, separators=(',', ': ')
            else:
                json.dump(
                    self.result_json, fp, separators=(",", ":")
                )  # ,indent=4, separators=(',', ': ')
        print("ok dump", resultfilename)

    @classmethod
    def convertPickleToText(
        self, resultfilename: Optional[str] = None, norga: int = 0
    ) -> None:
        """
        Convert pickle results to text format

        Parameters
        ----------
        resultfilename
            Path to result file, uses default if None
        norga
            Number of organelles
        """
        if resultfilename is None:
            resultfilename = self.result_file
        rfile = open(resultfilename)
        result = pickle.load(rfile)
        orgaresult = []
        for i in range(norga):
            orfile = open(resultfilename + "_organelle_" + str(i))
            orgaresult.append(pickle.load(orfile))
            orfile.close()
        rfile.close()
        rfile = open(resultfilename + "_free_points")
        rfile.close()
        rfile = open(resultfilename + ".txt", "w")
        line = ""
        for pos, rot, ingrName, compartment_id, ptInd in result:
            line += self.dropOneIngr(pos, rot, ingrName, compartment_id, ptInd)
            # result.append([pos,rot,ingr.name,ingr.compartment_id,ptInd])
        rfile.write(line)
        rfile.close()
        for i in range(norga):
            orfile = open(resultfilename + "_organelle_" + str(i) + ".txt", "w")
            result = []
            line = ""
            for pos, rot, ingrName, compartment_id, ptInd in orgaresult[i]:
                line += self.dropOneIngr(pos, rot, ingrName, compartment_id, ptInd)
            orfile.write(line)
            orfile.close()
            # freepoint

    def printFillInfo(self) -> None:
        """
        Print filling information for environment and compartments
        """
        r = self.exteriorRecipe
        if r is not None:
            print("    Environment exterior recipe:")
            r.printFillInfo("        ")

        for o in self.compartments:
            o.printFillInfo()

    def finishWithWater(
        self,
        free_points: Optional[List[int]] = None,
        nbFreePoints: Optional[int] = None,
    ) -> None:
        """
        Fill remaining space with water molecules

        Parameters
        ----------
        free_points
            List of free points, uses default if None
        nbFreePoints
            Number of free points, uses default if None
        """
        # self.freePointsAfterFill[:self.nbFreePointsAfterFill]
        # sphere sphere of 2.9A
        if free_points is None:
            free_points = self.freePointsAfterFill
        if nbFreePoints is None:
            nbFreePoints = self.nbFreePointsAfterFill
        # a freepoint is a voxel, how many water in the voxel
        # coords masterGridPositions

    # ==============================================================================
    # AFter this point, features development around physics engine and algo
    # octree
    # ==============================================================================

    def setupOctree(
        self,
    ) -> None:
        """
        Set up octree data structure for spatial partitioning
        """
        if self.octree is None:
            self.octree = Octree(
                self.grid.getRadius(), helper=helper
            )  # Octree((0,0,0),self.grid.getRadius())   #0,0,0 or center of grid?

    def delRB(self, node: Any) -> None:
        """
        Delete rigid body node

        Parameters
        ----------
        node
            Node to delete
        """
        return None

    def setGeomFaces(self, tris: Any, face: Any) -> None:
        """
        Set geometry faces

        Parameters
        ----------
        tris
            Triangle data
        face
            Face data
        """
        return None

    def addMeshRBOrganelle(self, o: Any) -> None:
        """
        Add mesh rigid body for organelle

        Parameters
        ----------
        o
            Organelle object
        """
        return None

    def addRB(
        self,
        ingr: Ingredient,
        translation: List[float],
        rotMat: List[List[float]],
        rtype: str = "single_sphere",
        static: bool = False,
    ) -> None:
        """
        Add a rigid body to the simulation environment.

        Parameters
        ----------
        ingr
            Ingredient object to add as rigid body
        translation
            Translation vector for the rigid body position
        rotMat
            Rotation matrix for the rigid body orientation
        rtype
            Type of rigid body representation
        static
            Whether the rigid body should be static or dynamic
        """
        return None

    def moveRBnode(
        self, node: Any, translation: List[float], rotMat: List[List[float]]
    ) -> None:
        """
        Move a rigid body node to a new position and orientation.

        Parameters
        ----------
        node
            The rigid body node to move
        translation
            New translation vector for the node
        rotMat
            New rotation matrix for the node
        """
        return None

    def getRotTransRB(self, node: Any) -> None:
        """
        Get the rotation and translation of a rigid body node.

        Parameters
        ----------
        node
            The rigid body node to query
        """
        return None

    def runBullet(self, ingr: Ingredient, simulationTimes: int, runTimeDisplay: bool) -> None:
        """
        Run bullet physics simulation for an ingredient.

        Parameters
        ----------
        ingr
            Ingredient to simulate
        simulationTimes
            Number of simulation steps to run
        runTimeDisplay
            Whether to display runtime information
        """
        return None

    def exportToBD_BOX(
        self,
        res_filename: Optional[str] = None,
        output: Optional[str] = None,
        bd_type: str = "flex",
    ) -> None:
        """
        Export simulation results to BD_BOX format.

        Parameters
        ----------
        res_filename
            Name of the result file to export from
        output
            Output file path
        bd_type
            Type of BD_BOX export format
        """
        # , call the BD_BOX exporter, plugin ? better if result store somewhere.
        # only sphere + boudary ?
        # sub ATM 216 225.0000 150.0000 525.0000 25.0000 -5.0000 50.0000 0.5922 1
        if bd_type == "flex":
            from bd_box import flex_box as bd_box
        else:
            from bd_box import rigid_box as bd_box
        if res_filename is None:
            res_filename = self.result_file
        self.bd = bd_box(res_filename, bounding_box=self.boundingBox)
        self.bd.makePrmFile()
        self.collectResultPerIngredient()
        r = self.exteriorRecipe
        if r:
            for ingr in r.ingredients:
                self.bd.addAutoPackIngredient(ingr)

        # compartment ingr
        for orga in self.compartments:
            # compartment surface ingr
            rs = orga.surfaceRecipe
            if rs:
                for ingr in rs.ingredients:
                    self.bd.addAutoPackIngredient(ingr)
            # compartment matrix ingr
            ri = orga.innerRecipe
            if ri:
                for ingr in ri.ingredients:
                    self.bd.addAutoPackIngredient(ingr)

        self.bd.write()

    def exportToTEM_SIM(
        self, res_filename: Optional[str] = None, output: Optional[str] = None
    ) -> None:
        """
        Export simulation results to TEM_SIM format.

        Parameters
        ----------
        res_filename
            Name of the result file to export from
        output
            Output file path
        """
        from tem_sim import tem_sim

        if res_filename is None:
            res_filename = self.result_file
        self.tem = tem_sim(res_filename, bounding_box=self.boundingBox)
        self.tem.setup()
        self.collectResultPerIngredient()
        r = self.exteriorRecipe
        if r:
            for ingr in r.ingredients:
                self.tem.addAutoPackIngredient(ingr)

        # compartment ingr
        for orga in self.compartments:
            # compartment surface ingr
            rs = orga.surfaceRecipe
            if rs:
                for ingr in rs.ingredients:
                    self.tem.addAutoPackIngredient(ingr)
            # compartment matrix ingr
            ri = orga.innerRecipe
            if ri:
                for ingr in ri.ingredients:
                    self.tem.addAutoPackIngredient(ingr)
        self.tem.write()

    def exportToTEM(self) -> None:
        """
        Export simulation results to TEM format with coordinate files.

        Limited to 20 ingredients. Creates coordinate.txt file for TEM-simulator.
        """
        # limited to 20 ingredients, call the TEM exporter plugin ?
        # ingredient -> PDB file or mrc volume file
        # ingredient -> coordinate.txt file
        p = []  # *0.05
        rr = []
        output = "iSutm_coordinate.txt"  # ingrname_.txt
        aStr = "# File created for TEM-simulator, version 1.3.\n"
        aStr += str(len(p)) + " 6\n"
        aStr += (
            "#            x             y             z           phi         theta    "
            "       psi\n"
        )
        for i in range(len(p)):
            aStr += "{0:14.4f}{1:14.4f}{2:14.4f}{3:14.4f}{4:14.4f}{5:14.4f}\n".format(
                p[i][0], p[i][1], p[i][2], rr[i][0], rr[i][1], rr[i][2]
            )
        f = open(output, "w")
        f.write(aStr)

    def exportToReaDDy(self) -> None:
        """
        Export simulation results to ReaDDy format.
        """
        # wehn I will get it running ... plugin ?
        return

        # ==============================================================================

    #         Animate
    # ==============================================================================

    def linkTraj(self) -> None:
        """
        Link trajectory for synchronized callback using autopack helper.

        Creates a synchronized callback for applying trajectory steps.
        """
        # link the traj usin upy for creating a new synchronized calleback?
        if not self.traj_linked:
            autopack.helper.synchronize(self.applyStep)
            self.traj_linked = True

    def unlinkTraj(self) -> None:
        """
        Unlink trajectory from synchronized callback.

        Removes the synchronized callback for trajectory steps.
        """
        # link the traj usin upy for creating a new synchronized calleback?
        if self.traj_linked:
            autopack.helper.unsynchronize(self.applyStep)
            self.traj_linked = False

    def applyStep(self, step: int) -> None:
        """
        Apply coordinates from a trajectory at a specific step.

        Handles correspondence between ingredient instances and coordinate files.

        Parameters
        ----------
        step
            The trajectory step to apply
        """
        # apply the coordinate from a trajectory at step step.
        # correspondance ingredients instance <-> coordinates file
        # trajectory class to handle
        print("Step is " + str(step))
        # if self.traj.traj_type=="dcd" or self.traj.traj_type=="xyz":
        self.traj.applyState_primitive_name(self, step)
        # ho can we apply to parent instance the rotatiotn?

    def create_voxelization(self, image_writer: Any) -> Any:
        """
        Update the image data for all molecules in the recipe by creating voxelized
        representations.

        Parameters
        ----------
        image_writer
            The image writer to use for writing the voxelized representations

        Returns
        -------
        :
            The updated image data
        """
        channel_colors = {}

        for obj in self.packed_objects.get_all():
            mesh_store = None
            if obj.name not in image_writer.image_data:
                image_writer.image_data[obj.name] = np.zeros(
                    image_writer.image_size, dtype=np.uint8
                )
                if obj.color is not None:
                    color = obj.color
                    if all([x <= 1 for x in obj.color]):
                        color = [int(col * 255) for col in obj.color]
                    channel_colors[obj.name] = color
            if obj.is_compartment:
                mesh_store = self.mesh_store

            image_writer.image_data[obj.name] = obj.ingredient.create_voxelization(
                image_data=image_writer.image_data[obj.name],
                bounding_box=self.boundingBox,
                voxel_size=image_writer.voxel_size,
                image_size=image_writer.image_size,
                position=obj.position,
                rotation=obj.rotation,
                hollow=image_writer.hollow,
                mesh_store=mesh_store,
            )
        image_writer.channel_colors = channel_colors

        return image_writer

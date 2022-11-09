# -*- coding: utf-8 -*-
"""
###############################################################################
#
# autoPACK Authors: Graham T. Johnson, Mostafa Al-Alusi, Ludovic Autin, Michel Sanner
#   Based on COFFEE Script developed by Graham Johnson between 2005 and 2010
#   with assistance from Mostafa Al-Alusi in 2009 and periodic input
#   from Arthur Olson's Molecular Graphics Lab
#
# Environment.py Authors: Graham Johnson & Michel Sanner with editing/enhancement
# from Ludovic Autin
# HistoVol.py became Environment.py in the Spring of 2013 to generalize the terminology
# away from biology
#
# Translation to Python initiated March 1, 2010 by Michel Sanner with Graham Johnson
#
# Class restructuring and organization: Michel Sanner
#
# Copyright: Graham Johnson ©2010
#
# This file "Environment.py" is part of autoPACK, cellPACK.
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
#
###############################################################################
@author: Graham Johnson, Ludovic Autin, & Michel Sanner

# Hybrid version merged from Graham's Sept 2011 and Ludo's April 2012
# version on May 16, 2012
# Updated with final thesis HistoVol.py file from Sept 25, 2012 on July 5, 2012
# with correct analysis tools

# TODO: fix the save/restore grid
"""

import os
from time import time
from random import random, uniform, seed
from scipy import spatial
import numpy
import pickle
import math
from math import pi
import json
from json import encoder
import logging
from collections import OrderedDict

# PANDA3D Physics engine ODE and Bullet
import panda3d

from panda3d.core import Mat3, Mat4, Vec3, BitMask32, NodePath
from panda3d.bullet import BulletRigidBodyNode

import cellpack.autopack as autopack
from cellpack.autopack.MeshStore import MeshStore
import cellpack.autopack.ingredient as ingredient
from cellpack.autopack.loaders.utils import create_output_dir
from cellpack.autopack.utils import (
    cmp_to_key,
    expand_object_using_key,
    ingredient_compare0,
    ingredient_compare1,
    ingredient_compare2,
)
from cellpack.autopack.writers import Writer
from .Compartment import CompartmentList, Compartment
from .Recipe import Recipe
from .ingredient import GrowIngredient, ActinIngredient
from cellpack.autopack import IOutils
from .octree import Octree
from .Gradient import Gradient
from .transformation import euler_from_matrix

# backward compatibility with kevin method
from cellpack.autopack.BaseGrid import BaseGrid as BaseGrid
from .trajectory import dcdTrajectory, molbTrajectory
from .randomRot import RandomRot

try:
    helper = autopack.helper
except ImportError:
    helper = None


encoder.FLOAT_REPR = lambda o: format(o, ".8g")

SEED = 15
LOG = False
verbose = 0


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

    def __init__(self, config=None, recipe=None):
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
        self.pickRandPt = not config["ordered_packing"]
        self.show_sphere_trees = config["show_sphere_trees"]
        self.show_grid_spheres = config["show_grid_plot"]
        self.boundingBox = numpy.array(recipe["bounding_box"])
        self.spacing = config["spacing"]
        self.load_from_grid_file = config["load_from_grid_file"]
        self.name = name

        # saving/pickle option
        self.saveResult = "out" in config
        self.out_folder = create_output_dir(config["out"], name, config["place_method"])
        self.result_file = f"{self.out_folder}/{self.name}_{config['name']}"
        self.grid_file_out = f"{self.out_folder}/{self.name}_{config['name']}_grid"

        should_load_grid_file = (
            os.path.isfile(self.grid_file_out) and self.load_from_grid_file
        )
        self.previous_grid_file = self.grid_file_out if should_load_grid_file else None
        self.setupfile = ""
        self.current_path = None  # the path of the recipe file
        self.custom_paths = None
        self.grid_filename = None  #
        self.grid_result_filename = None  # str(gridn.getAttribute("grid_result"))

        self.timeUpDistLoopTotal = 0
        self.exteriorRecipe = None
        self.hgrid = []
        self.world = None  # panda world for collision
        self.octree = None  # ongoing octree test, no need if openvdb wrapped to python
        self.grid = None  # Grid()  # the main grid
        self.encapsulatingGrid = (
            0  # Only override this with 0 for 2D packing- otherwise its very unsafe!
        )
        # 0 is the exterior, 1 is compartment 1 surface, -1 is compartment 1 interior
        self.nbCompartments = 1

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
        self.molecules = (
            []
        )  # list of ( (x,y,z), rotation, ingredient) triplet generated by packing
        self.ingr_result = {}

        self.randomRot = RandomRot()  # the class used to generate random rotation
        self.activeIngr = []
        self.activeIngre_saved = []
        self.freePtsUpdateThreshold = 0.0
        # optionally can provide a host and a viewer
        self.host = None
        self.afviewer = None

        # version of setup used
        self.version = "1.0"

        # option for packing using host dynamics capability
        self.windowsSize = 100
        self.windowsSize_overwrite = False

        self.orthogonalBoxType = 0
        self.overwritePlaceMethod = False
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

        self.use_gradient = False  # gradient control is also per ingredient
        self.use_halton = False  # use halton for grid point distribution

        self.ingrLookForNeighbours = False  # Old Features to be test

        # debug with timer function
        self.nb_ingredient = 0
        self.totalNbIngr = 0
        self.treemode = "cKDTree"
        self.close_ingr_bhtree = (
            None  # RBHTree(a.tolist(),range(len(a)),10,10,10,10,10,9999)
        )
        self.rTrans = []
        self.result = []
        self.rIngr = []
        self.rRot = []
        # should be part of an independent module
        self.panda_solver = "bullet"  # or bullet
        # could be a problem here for pp
        # can't pickle this dictionary
        self.rb_func_dic = {}
        # need options for the save/server data etc....
        # should it be in __init__ like other general options ?
        self.dump = True
        self.dump_freq = 120.0
        self.jsondic = None

        self.distancesAfterFill = []
        self.freePointsAfterFill = []
        self.nbFreePointsAfterFill = []
        self.distanceAfterFill = []
        self._setup()

    def _setup(self):
        if "composition" in self.recipe_data:
            (
                self.root_compartment,
                self.compartment_keys,
                self.reference_dict,
                self.referenced_objects,
            ) = Recipe.resolve_composition(self.recipe_data)
            self.create_objects()

    def setSeed(self, seedNum):
        SEED = int(seedNum)
        numpy.random.seed(SEED)  # for gradient
        seed(SEED)
        self.randomRot.setSeed(seed=SEED)
        self.seed_set = True
        self.seed_used = SEED

    def _prep_ingredient_info(self, composition_info, ingredient_name=None):
        objects_dict = self.recipe_data["objects"]
        object_key = composition_info["object"]
        ingredient_info = expand_object_using_key(
            composition_info, "object", objects_dict
        )
        ingredient_info["name"] = (
            ingredient_name if ingredient_name is not None else object_key
        )
        return ingredient_info

    def _step_down(self, compartment_key):
        composition_dict = self.recipe_data["composition"]
        compartment = self.create_compartment(compartment_key)
        compartment_info = composition_dict[compartment_key]
        for region_name, obj_keys in compartment_info.get(
            "regions", {}
        ).items():  # check if entry in compositions has regions
            recipe = Recipe(name=f"{compartment_key}_{region_name}")
            for key_or_dict in obj_keys:
                is_key, composition_info = Recipe.is_key(key_or_dict, composition_dict)
                if is_key and key_or_dict in self.compartment_keys:
                    key = key_or_dict
                    self._step_down(key)
                else:
                    key = key_or_dict if is_key else None
                    ingredient_info = self._prep_ingredient_info(composition_info, key)
                    self.create_ingredient(recipe, ingredient_info)
            if region_name == "surface":
                compartment.setSurfaceRecipe(recipe)
            elif region_name == "interior":
                compartment.setInnerRecipe(recipe)

    def create_objects(self):
        """
        Instantiate compartments and ingredients contained within the recipe data.
        """
        composition_dict = self.recipe_data["composition"]

        if self.root_compartment is not None:
            # create cytoplasme and set as exterior recipe
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
                        key = key_or_dict
                        self._step_down(key)
                    else:
                        key = key_or_dict if is_key else None
                        ingredient_info = self._prep_ingredient_info(
                            composition_info, key
                        )
                        self.create_ingredient(external_recipe, ingredient_info)
            self.setExteriorRecipe(external_recipe)

        if "gradients" in self.recipe_data:
            # TODO: deal with gradients here
            pass

    def reportprogress(self, label=None, progress=None):
        if self.afviewer is not None and hasattr(self.afviewer, "vi"):
            self.afviewer.vi.progressBar(progress=progress, label=label)

    def set_partners_ingredient(self, ingr):
        if ingr.partners_name:
            weightinitial = ingr.partners_weight
            total = len(ingr.partners_name)  # this is 1
            w = float(weightinitial)
            if len(ingr.partners_name) == 1:
                w = 1.0
                total = 2
                weightinitial = 1
            for i, iname in enumerate(ingr.partners_name):
                print("weight", iname, w, ((1.0 - weightinitial) / (total - 1.0)))
                ingr_partner = self.getIngrFromName(iname)
                if ingr_partner is None:
                    continue
                if i < len(ingr.partners_position):
                    partner = ingr.addPartner(
                        ingr_partner,
                        weight=w,
                        properties={"position": ingr.partners_position[i]},
                    )
                else:
                    partner = ingr.addPartner(ingr_partner, weight=w, properties={})
                for p in ingr_partner.properties:
                    partner.addProperties(p, ingr_partner.properties[p])
                w += ((1 - weightinitial) / (total - 1)) - weightinitial
            if ingr.type == "Grow":
                ingr.prepare_alternates()
        if ingr.excluded_partners_name:
            for iname in ingr.excluded_partners_name:
                ingr.addExcludedPartner(iname)
        ingr.env = self

    # def unpack_objects(self, objects):
    #     for key, value in objects.items():

    def save_result(
        self, free_points, distances, t0, vAnalysis, vTestid, seedNum, all_ingr_as_array
    ):
        self.grid.free_points = free_points[:]
        self.grid.distToClosestSurf = distances[:]
        # should check extension filename for type of saved file
        if not os.path.isfile(self.grid_file_out) and self.load_from_grid_file:
            # do not overwrite if grid was loaded from file
            self.grid.result_filename = self.grid_file_out
            self.saveGridToFile(self.grid_file_out)
        self.saveGridLogsAsJson(self.result_file + "_grid-data.json")
        self.collectResultPerIngredient()
        self.store()
        self.store_asTxt()
        Writer(format=self.format_output).save(self,
            self.result_file,
            kwds=["compNum"],
            result=True,
            quaternion=True,
            all_ingr_as_array=all_ingr_as_array,
            compartments=self.compartments)

        self.log.info("time to save result file %d", time() - t0)
        if vAnalysis == 1:
            #    START Analysis Tools: Graham added back this big chunk of code for analysis tools and graphic on 5/16/12 Needs to be cleaned up into a function and proper uPy code
            # totalVolume = self.grid.gridVolume*unitVol
            unitVol = self.grid.gridSpacing**3
            wrkDirRes = self.result_file + "_analyze_"
            for o in self.compartments:  # only for compartment ?
                # totalVolume -= o.surfaceVolume
                # totalVolume -= o.interiorVolume
                innerPointNum = len(o.insidePoints) - 1
                self.log.info("  .  .  .  . ")
                self.log.info("for compartment o = %s", o.name)
                self.log.info("inner Point Count = %d", innerPointNum)
                self.log.info("inner Volume = %s", o.interiorVolume)
                self.log.info("innerVolume temp Confirm = %d", innerPointNum * unitVol)
                usedPts = 0
                unUsedPts = 0
                vDistanceString = ""
                insidepointindce = numpy.nonzero(
                    numpy.equal(self.grid.compartment_ids, -o.number)
                )[0]
                for i in insidepointindce:  # xrange(innerPointNum):
                    #                        pt = o.insidePoints[i] #fpts[i]
                    #                        print (pt,type(pt))
                    # for pt in self.histo.freePointsAfterFill:#[:self.histo.nbFreePointsAfterFill]:
                    d = self.distancesAfterFill[i]
                    vDistanceString += str(d) + "\n"
                    if d <= 0:  # >self.smallestProteinSize-0.001:
                        usedPts += 1
                    else:
                        unUsedPts += 1
                filename = (
                    wrkDirRes
                    + "vResultMatrix1"
                    + o.name
                    + "_Testid"
                    + str(vTestid)
                    + "_Seed"
                    + str(seedNum)
                    + "_dists.txt"
                )  # Used this from thesis to overwrite less informative SVN version on next line on July 5, 2012
                #            filename = wrkDirRes+"/vDistances1.txt"
                f = open(filename, "w")
                f.write(vDistanceString)
                f.close()

                # result is [pos,rot,ingr.name,ingr.compNum,ptInd]
                # if resultfilename == None:
                # resultfilename = self.result_file
                resultfilenameT = (
                    wrkDirRes
                    + "vResultMatrix1"
                    + o.name
                    + "_Testid"
                    + str(vTestid)
                    + "_Seed"
                    + str(seedNum)
                    + "_Trans.txt"
                )  # Used this from thesis to overwrite less informative SVN version on next line on July 5, 2012
                resultfilenameR = (
                    wrkDirRes
                    + "vResultMatrix1"
                    + o.name
                    + "_Testid"
                    + str(vTestid)
                    + "_Seed"
                    + str(seedNum)
                    + "_Rot.txt"
                )
                vTranslationString = ""
                vRotationString = ""
                result = []
                matCount = 0
                for pos, rot, ingr, ptInd in o.molecules:
                    # BEGIN: newer code from Theis version added July 5, 2012
                    if hasattr(self, "afviewer"):
                        mat = rot.copy()
                        mat[:3, 3] = pos

                        # r = R.from_matrix(mat).as_euler("xyz", degrees=False)
                        r = euler_from_matrix(mat, "rxyz")
                        h1 = math.degrees(math.pi + r[0])
                        p1 = math.degrees(r[1])
                        b1 = math.degrees(-math.pi + r[2])
                        self.log.info("rot from matrix = %r %r %r %r", r, h1, p1, b1)
                        # END: newer code from Theis version added July 5, 2012
                    result.append([pos, rot])
                    pt3d = result[matCount][0]
                    (
                        x,
                        y,
                        z,
                    ) = pt3d

                    vTranslationString += (
                        str(x) + ",\t" + str(y) + ",\t" + str(z) + "\n"
                    )
                    # vRotationString += str(rot3d) #str(h)+ ",\t" + str(p) + ",\t" + str(b) + "\n"
                    vRotationString += (
                        str(h1)
                        + ",\t"
                        + str(p1)
                        + ",\t"
                        + str(b1)
                        + ",\t"
                        + ingr.name
                        + "\n"
                    )
                    matCount += 1

                rfile = open(resultfilenameT, "w")
                rfile.write(vTranslationString)
                rfile.close()

                rfile = open(resultfilenameR, "w")
                rfile.write(vRotationString)
                rfile.close()
                self.log.info("len(result) = %d", len(result))
                self.log.info("len(self.molecules) = %d", len(self.molecules))
                # Graham Note:  There is overused disk space- the rotation matrix is 4x4 with an offset of 0,0,0
                # and we have a separate translation vector in the results and molecules arrays.
                #  Get rid of the translation vector and move it to the rotation matrix to save space...
                # will that slow the time it takes to extract the vector from the matrix when we need to call it?
                self.log.info(
                    "*************************************************** vDistance String Should be on"
                )
                self.log.info("unitVolume2 = %d", unitVol)
                self.log.info("Number of Points Unused = %d", unUsedPts)
                self.log.info("Number of Points Used   = %d", usedPts)
                self.log.info("Volume Used   = %d", usedPts * unitVol)
                self.log.info("Volume Unused = %d", unUsedPts * unitVol)
                self.log.info("vTestid = %d", vTestid)
                self.log.info("self.grid.nbGridPoints = %r", self.grid.nbGridPoints)
                self.log.info("self.gridVolume = %d", self.grid.gridVolume)

        self.log.info("self.compartments In Environment = %d", len(self.compartments))
        if self.compartments == []:
            unitVol = self.grid.gridSpacing**3
            innerPointNum = len(free_points)
            self.log.info("  .  .  .  . ")
            self.log.info("inner Point Count = %d", innerPointNum)
            self.log.info("innerVolume temp Confirm = %d", innerPointNum * unitVol)
            usedPts = 0
            unUsedPts = 0
            # fpts = self.freePointsAfterFill
            vDistanceString = ""
            for i in range(innerPointNum):
                pt = free_points[i]  # fpts[i]
                # for pt in self.histo.freePointsAfterFill:#[:self.histo.nbFreePointsAfterFill]:
                d = self.distancesAfterFill[pt]
                vDistanceString += str(d) + "\n"
                if d <= 0:  # >self.smallestProteinSize-0.001:
                    usedPts += 1
                else:
                    unUsedPts += 1
            # Graham Note:  There is overused disk space- the rotation matrix is 4x4 with an offset of 0,0,0
            # and we have a separate translation vector in the results and molecules arrays.
            # Get rid of the translation vector and move it to the rotation matrix to save space...
            # will that slow the time it takes to extract the vector from the matrix when we need to call it?

            self.log.info("unitVolume2 = %d", unitVol)
            self.log.info("Number of Points Unused = %d", unUsedPts)
            self.log.info("Number of Points Used   = %d", usedPts)
            self.log.info("Volume Used   = %d", usedPts * unitVol)
            self.log.info("Volume Unused = %d", unUsedPts * unitVol)
            self.log.info("vTestid = %s", vTestid)
            self.log.info("self.nbGridPoints = %r", self.grid.nbGridPoints)
            self.log.info("self.gridVolume = %d", self.grid.gridVolume)
            self.log.info("histoVol.timeUpDistLoopTotal = %d", self.timeUpDistLoopTotal)

            #    END Analysis Tools: Graham added back this big chunk of code for analysis tools and graphic on 5/16/12 Needs to be cleaned up into a function and proper uPy code
        self.log.info("time to save end %d", time() - t0)

    def loadResult(
        self, resultfilename=None, restore_grid=True, backward=False, transpose=True
    ):
        result = [], [], []
        if resultfilename is None:
            resultfilename = self.result_file
            # check the extension of the filename none, txt or json
            # resultfilename = autopack.retrieveFile(resultfilename,cache="results")
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

    def includeIngrRecipes(self, ingrname, include):
        """
        Include or Exclude the given ingredient from the recipe.
        (similar to an active state toggle)
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

    def includeIngrRecipe(self, ingrname, include, rs):
        """
        Include or Exclude the given ingredient from the given recipe.
        (similar to an active state toggle)
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

    def includeIngredientRecipe(self, ingr, include):
        """lue
        Include or Exclude the given ingredient from the recipe.
        (similar to an active state toggle)
        """
        r = ingr.recipe  # ()
        if include:
            r.addIngredient(ingr)
        else:
            r.delIngredient(ingr)

    def sortIngredient(self, reset=False):
        # make sure all recipes are sorted from large to small radius
        if self.exteriorRecipe:
            self.exteriorRecipe.sort()
        for o in self.compartments:
            if reset:
                o.reset()
            if o.innerRecipe:
                o.innerRecipe.sort()
            if o.surfaceRecipe:
                o.surfaceRecipe.sort()

    def setGradient(self, **kw):
        """
        create a grdaient
        assign weight to point
        listorganelle influenced
        listingredient influenced
        """
        if "name" not in kw:
            print("name kw is required")
            return
        gradient = Gradient(**kw)
        # default gradient 1-linear Decoy X
        self.gradients[kw["name"]] = gradient

    def callFunction(self, function, args=[], kw={}):
        """
        helper function to callback another function with the
        given arguments and keywords.
        Optionally time stamp it.
        """

        if len(kw):
            res = function(*args, **kw)
        else:
            res = function(*args)
        return res

    def is_two_d(self):
        grid_spacing = self.grid.gridSpacing
        bounding_box = self.boundingBox
        box_size = numpy.array(bounding_box[1]) - numpy.array(bounding_box[0])
        smallest_size = numpy.amin(box_size)
        return smallest_size <= grid_spacing

    def timeFunction(self, function, args, kw):
        """
        Mesure the time for performing the provided function.

        @type  function: function
        @param function: the function to execute
        @type  args: liste
        @param args: the liste of arguments for the function


        @rtype:   list/array
        @return:  the center of mass of the coordinates
        """

        t1 = time()
        if len(kw):
            res = function(*args, **kw)
        else:
            res = function(*args)
        print(("time " + function.__name__, time() - t1))
        return res

    def SetRBOptions(self, obj="moving", **kw):
        """
        Change the rigid body options
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

    def SetSpringOptions(self, **kw):
        """
        Change the spring options, mainly used by C4D.
        """
        key = ["stifness", "rlength", "damping"]
        for k in key:
            val = kw.pop(k, None)
            if val is not None:
                self.springOptions[k] = val

    def setupRBOptions(self):
        """
        Set default value for rigid body options
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

    def writeArraysToFile(self, f):
        """write self.compartment_ids and self.distToClosestSurf to file. (pickle)"""
        pickle.dump(self.grid.masterGridPositions, f)
        pickle.dump(self.grid.compartment_ids, f)
        pickle.dump(self.grid.distToClosestSurf, f)

    def readArraysFromFile(self, f):
        """write self.compartment_ids and self.distToClosestSurf to file. (pickle)"""
        pos = pickle.load(f)
        self.grid.masterGridPositions = pos

        id = pickle.load(f)
        self.grid.compartment_ids = id

        dist = pickle.load(f)
        self.grid.distToClosestSurf_store = self.grid.distToClosestSurf[:]
        if len(dist):
            self.grid.distToClosestSurf = dist  # grid+organelle+surf
        self.grid.free_points = list(range(len(id)))

    def saveGridToFile(self, gridFileOut):
        """
        Save the current grid and the compartment grid information in a file. (pickle)
        """
        d = os.path.dirname(gridFileOut)
        print("SAVED GRID TO ", gridFileOut)
        if not os.path.exists(d):
            print("gridfilename path problem", gridFileOut)
            return
        f = open(gridFileOut, "wb")  # 'w'
        self.writeArraysToFile(f)

        for compartment in self.compartments:
            compartment.saveGridToFile(f)
        f.close()

    def saveGridLogsAsJson(self, gridFileOut):
        """
        Save the current grid and the compartment grid information in a file. (pickle)
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

    def restoreGridFromFile(self, gridFileName):
        """
        Read and setup the grid from the given filename. (pickle)
        """
        aInteriorGrids = []
        aSurfaceGrids = []
        f = open(gridFileName, "rb")
        self.readArraysFromFile(f)
        for compartment in self.compartments:
            compartment.readGridFromFile(f)
            aInteriorGrids.append(compartment.insidePoints)
            aSurfaceGrids.append(compartment.surfacePoints)
            compartment.OGsrfPtsBht = spatial.cKDTree(
                tuple(compartment.vertices), leafsize=10
            )
            compartment.compute_volume_and_set_count(
                self, compartment.surfacePoints, compartment.insidePoints, areas=None
            )
        f.close()
        self.grid.aInteriorGrids = aInteriorGrids
        self.grid.aSurfaceGrids = aSurfaceGrids

    def extractMeshComponent(self, obj):
        """
        Require host helper. Return the v,f,n of the given object
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

    def setCompartmentMesh(self, compartment, ref_obj):
        """
        Require host helper. Change the mesh of the given compartment and recompute
        inside and surface point.
        """
        if compartment.ref_obj == ref_obj:
            return
        if os.path.isfile(ref_obj):
            fileName, fileExtension = os.path.splitext(ref_obj)
            if helper is not None:  # neeed the helper
                helper.read(ref_obj)
                geom = helper.getObject(fileName)
                # reparent to the fill parent
                # rotate ?
                if helper.host != "c4d" and geom is not None:
                    # need to rotate the transform that carry the shape
                    helper.rotateObj(geom, [0.0, -pi / 2.0, 0.0])
        else:
            geom = helper.getObject(ref_obj)
        if geom is not None:
            vertices, faces, vnormals = self.extractMeshComponent(geom)
            compartment.setMesh(
                filename=ref_obj, vertices=vertices, faces=faces, vnormals=vnormals
            )

    def update_largest_smallest_size(self, ingr):
        if ingr.encapsulating_radius > self.largestProteinSize:
            self.largestProteinSize = ingr.encapsulating_radius
        if ingr.min_radius < self.smallestProteinSize:
            self.smallestProteinSize = ingr.min_radius

    def create_ingredient(self, recipe, arguments):
        if "place_method" not in arguments:
            arguments["place_method"] = self.place_method
        ingredient_type = arguments["type"]
        ingredient_class = ingredient.get_ingredient_class(ingredient_type)
        ingr = ingredient_class(**arguments)
        if (
            "gradient" in arguments
            and arguments["gradient"] != ""
            and arguments["gradient"] != "None"
        ):
            ingr.gradient = arguments["gradient"]
        if "results" in arguments:
            ingr.results = arguments["results"]
        ingr.initialize_mesh(self.mesh_store)
        recipe.addIngredient(ingr)
        self.update_largest_smallest_size(ingr)

    def create_compartment(self, compartment_key):
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
        compartment.initialize_shape(self.mesh_store)
        self._add_compartment(compartment)
        return compartment

    def _add_compartment(self, compartment):
        """
        Add the given compartment to the environment.
        Extend the main bounding box if needed
        """
        compartment.setNumber(self.nbCompartments)
        self.nbCompartments += 1
        CompartmentList._add_compartment(self, compartment)

    def compartment_id_for_nearest_grid_point(self, point):
        # check if point inside  of the compartments
        # closest grid point is
        d, pid = self.grid.getClosestGridPoint(point)
        compartment_id = self.grid.compartment_ids[pid]
        return compartment_id

    def longestIngrdientName(self):
        """
        Helper function for gui. Return the size of the longest ingredient name
        """
        M = 20
        r = self.exteriorRecipe
        if r:
            for ingr in r.ingredients:
                if len(ingr.name) > M:
                    M = len(ingr.name)
        for o in self.compartments:
            rs = o.surfaceRecipe
            if rs:
                for ingr in rs.ingredients:
                    if len(ingr.name) > M:
                        M = len(ingr.name)
            ri = o.innerRecipe
            if ri:
                for ingr in ri.ingredients:
                    if len(ingr.name) > M:
                        M = len(ingr.name)
        return M

    def loopThroughIngr(self, cb_function):
        """
        Helper function that loops through all ingredients of all recipes and applies the given
        callback function on each ingredients.
        """
        recipe = self.exteriorRecipe
        if recipe:
            for ingr in recipe.ingredients:
                cb_function(ingr)
        for compartment in self.compartments:
            surface_recipe = compartment.surfaceRecipe
            if surface_recipe:
                for ingr in surface_recipe.ingredients:
                    cb_function(ingr)
            inner_recipe = compartment.innerRecipe
            if inner_recipe:
                for ingr in inner_recipe.ingredients:
                    cb_function(ingr)

    def getIngrFromNameInRecipe(self, name, r):
        """
        Given an ingredient name and a recipe, retrieve the ingredient object instance
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
                elif name == ingr.o_name:
                    return ingr
                #                elif name.find(ingr.o_name) != -1 :
                #                    #check for
                #                    return ingr
            for ingr in r.exclude:
                if name == ingr.name:
                    return ingr
                elif name == ingr.o_name:
                    return ingr
                #                elif name.find(ingr.o_name) != -1 :
                #                    return ingr
        return None

    def getIngrFromName(self, name, compNum=None):
        """
        Given an ingredient name and optionally the compartment number, retrieve the ingredient object instance
        """
        if compNum is None:
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
        elif compNum == 0:
            r = self.exteriorRecipe
            ingr = self.getIngrFromNameInRecipe(name, r)
            if ingr is not None:
                return ingr
            else:
                return None
        elif compNum > 0:
            o = self.compartments[compNum - 1]
            rs = o.surfaceRecipe
            ingr = self.getIngrFromNameInRecipe(name, rs)
            if ingr is not None:
                return ingr
            else:
                return None
        else:  # <0
            o = self.compartments[(compNum * -1) - 1]
            ri = o.innerRecipe
            ingr = self.getIngrFromNameInRecipe(name, ri)
            if ingr is not None:
                return ingr
            else:
                return None

    def setExteriorRecipe(self, recipe):
        """
        Set the exterior recipe with the given one. Create the weakref.
        """
        assert isinstance(recipe, Recipe)
        self.exteriorRecipe = recipe
        recipe.compartment = self  # weakref.ref(self)
        for ingr in recipe.ingredients:
            ingr.compNum = 0

    def BuildCompartmentsGrids(self):
        """
        Build the compartments grid (interior and surface points) to be merged with the main grid
        """
        aInteriorGrids = []
        aSurfaceGrids = []
        # thread ?
        for compartment in self.compartments:
            self.log.info(
                f"in Environment, compartment.is_orthogonal_bounding_box={compartment.is_orthogonal_bounding_box}"
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

    def build_compartment_grids(self):
        self.log.info("file is None thus re/building grid distance")
        self.BuildCompartmentsGrids()

        if len(self.compartments):
            verts = numpy.array(self.compartments[0].surfacePointsCoords)
            for i in range(1, len(self.compartments)):
                verts = numpy.vstack([verts, self.compartments[i].surfacePointsCoords])
            self.grid.set_surfPtsBht(
                verts.tolist()
            )  # should do it only on inside grid point

    def extend_bounding_box_for_compartments(self):
        for _, compartment in enumerate(self.compartments):
            fits, bb = compartment.inBox(self.boundingBox, self.smallestProteinSize)
            if not fits:
                self.boundingBox = bb

    def buildGrid(
        self,
        rebuild=True,
        lookup=0,
    ):
        """
        The main build grid function. Setup the main grid and merge the
        compartment grid. The setup is de novo or using previously built grid
        or restored using given file.
        """
        self.extend_bounding_box_for_compartments()

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
            spacing = self.spacing or self.smallestProteinSize
            self.grid = Grid(boundingBox=boundingBox, spacing=spacing, lookup=lookup)
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
                self.restoreGridFromFile(self.previous_grid_file)
        else:
            self.build_compartment_grids()

        self.exteriorVolume = self.grid.computeExteriorVolume(
            compartments=self.compartments,
            space=self.smallestProteinSize,
            fbox_bb=self.fbox_bb,
        )
        if self.previous_grid_file is None:
            self.saveGridToFile(self.grid_file_out)
            self.grid.filename = self.grid_file_out
            self.previous_grid_file = self.grid_file_out

        r = self.exteriorRecipe
        if r:
            r.setCount(self.exteriorVolume)  # should actually use the fillBB
        if not rebuild:
            for c in self.compartments:
                c.setCount()
        else:
            self.grid.distToClosestSurf_store = self.grid.distToClosestSurf[:]
        if self.use_gradient and len(self.gradients) and rebuild:
            for g in self.gradients:
                self.gradients[g].buildWeigthMap(
                    boundingBox, self.grid.masterGridPositions
                )
        if self.previous_grid_file is not None:
            distance = self.grid.distToClosestSurf  # [:]
            nbFreePoints = nbPoints  # -1              #Graham turned this off on 5/16/12 to match August Repair for May Hybrid
            for i, mingrs in enumerate(
                self.molecules
            ):  # ( jtrans, rotMatj, self, ptInd )
                nbFreePoints = self.onePrevIngredient(
                    i, mingrs, distance, nbFreePoints, self.molecules
                )
            for organelle in self.compartments:
                for i, mingrs in enumerate(
                    organelle.molecules
                ):  # ( jtrans, rotMatj, self, ptInd )
                    nbFreePoints = self.onePrevIngredient(
                        i, mingrs, distance, nbFreePoints, organelle.molecules
                    )
            self.grid.nbFreePoints = nbFreePoints

    def onePrevIngredient(self, i, mingrs, distance, nbFreePoints, marray):
        """
        Unused
        """
        jtrans, rotMatj, ingr, ptInd = mingrs
        centT = ingr.transformPoints(jtrans, rotMatj, ingr.positions[-1])
        insidePoints = {}
        newDistPoints = {}
        mr = self.get_dpad(ingr.compNum)
        spacing = self.smallestProteinSize
        jitter = ingr.getMaxJitter(spacing)
        dpad = ingr.min_radius + mr + jitter
        insidePoints, newDistPoints = ingr.getInsidePoints(
            self.grid,
            self.grid.masterGridPositions,
            dpad,
            distance,
            centT=centT,
            jtrans=jtrans,
            rotMatj=rotMatj,
        )
        # update free points
        if len(insidePoints) and self.place_method.find("panda") != -1:
            print(ingr.name, " is inside")
            self.checkPtIndIngr(ingr, insidePoints, i, ptInd, marray)
            # ingr.inside_current_grid = True
        else:
            # not in the grid
            print(ingr.name, " is outside")
            # rbnode = ingr.rbnode[ptInd]
            # ingr.rbnode.pop(ptInd)
            marray[i][3] = -ptInd  # uniq Id ?
            # ingr.rbnode[-1] = rbnode
        # doesnt seem to work properly...
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

    def checkPtIndIngr(self, ingr, insidePoints, i, ptInd, marray):
        """
        We need to check if the point indice is correct in the case of panda packing.
        as the pt indice in the result array have a different meaning.
        """
        # change key for rbnode too
        rbnode = None
        if ptInd in ingr.rbnode:
            rbnode = ingr.rbnode[ptInd]
            ingr.rbnode.pop(ptInd)
        elif -ptInd in ingr.rbnode:
            rbnode = ingr.rbnode[-ptInd]
            ingr.rbnode.pop(-ptInd)
        else:
            print("ptInd " + str(ptInd) + " not in ingr.rbnode")
        if i < len(marray):
            marray[i][3] = insidePoints.keys()[0]
            ingr.rbnode[insidePoints.keys()[0]] = rbnode

    def getSortedActiveIngredients(self, allIngredients):
        """
        Sort the active ingredient according their pirority and radius.
        # first get the ones with a packing priority
        # Graham- This now works in concert with ingredient picking

        # Graham here- In the new setup, priority is infinite with abs[priority] increasing (+)
        # An ingredients with (-) priority will pack from greatest abs[-priority] one at a time
        #     to lease abs[-priority]... each ingredient will attempt to reach its molarity
        #     before moving on to the next ingredient, and all (-) ingredients will try to
        #     deposit before other ingredients are tested.
        # An ingredient with (+) priority will recieve a weighted value based on its abs[priority]
        #     e.g. an ingredient with a priority=10 will be 10x more likely to be picked than
        #     an ingredient with a priority=1.
        # An ingredient with the default priority=0 will recieve a weighted value based on its
        #     complexity. (currently complexity = min_radius), thus a more 'complex' ingredient
        #     will more likely try to pack before a less 'complex' ingredient.
        #     IMPORTANT: the +priority list does not fully mix with the priority=0 list, but this
        #     should be an option... currently, the priority=0 list is normalized against a range
        #     up to the smallest +priority ingredient and appended to the (+) list
        # TODO: Add an option to allow + ingredients to be weighted by assigned priority AND complexity
        #     Add an option to allow priority=0 ingredients to fit into the (+) ingredient list
        #       rather than appending to the end.
        #     Even better, add an option to set the max priority for the 0list and then plug the results
        #       into the (+) ingredient list.
        #     Get rid of the (-), 0, (+) system and recreate this as a new flag and a class function
        #        so we can add multiple styles of sorting and weighting systems.
        #     Make normalizedPriorities and thresholdPriorities members of Ingredient class to avoid
        #        building these arrays.
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
            np = float(r) / float(self.totalRadii) * self.lowestPriority
            self.normalizedPriorities0.append(np)
            priors2.priority = np
            self.log.info("self.normalizedPriorities0 = %r", self.normalizedPriorities0)
        activeIngr0 = ingr0  # +ingr1+ingr2  #cropped to 0 on 7/20/10

        self.log.info("len(activeIngr0) %d", len(activeIngr0))
        activeIngr12 = ingr1 + ingr2
        self.log.info("len(activeIngr12) %d", len(activeIngr12))
        packingPriorities = priorities0 + priorities1 + priorities2
        self.log.info("packingPriorities %r", packingPriorities)

        return activeIngr0, activeIngr12

    def clearRBingredient(self, ingr):
        if ingr.bullet_nodes[0] is not None:
            self.delRB(ingr.bullet_nodes[0])
        if ingr.bullet_nodes[1] is not None:
            self.delRB(ingr.bullet_nodes[1])

    def clear(self):
        # before closing remoeall rigidbody
        self.loopThroughIngr(self.clearRBingredient)

    def reset(self):
        """Reset everything to empty and not done"""
        self.fbox_bb = None
        self.totnbJitter = 0
        self.jitterLength = 0.0
        r = self.exteriorRecipe
        self.resetIngrRecip(r)
        self.molecules = []
        for orga in self.compartments:
            # orga.reset()
            rs = orga.surfaceRecipe
            self.resetIngrRecip(rs)
            ri = orga.innerRecipe
            self.resetIngrRecip(ri)
            orga.molecules = []
        self.ingr_result = {}
        if self.world is not None:
            # need to clear all node
            #            nodes = self.rb_panda[:]
            #            for node in nodes:
            #                self.delRB(node)
            self.static = []
            self.moving = None
        if self.octree is not None:
            del self.octree
            self.octree = None
            # the reset doesnt touch the grid...

        self.rTrans = []
        self.rIngr = []
        self.rRot = []
        self.result = []
        # rapid node ?

    def resetIngrRecip(self, recip):
        """Reset all ingredient of the given recipe"""
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

    def getActiveIng(self):
        """Return all remaining active ingredients"""
        allIngredients = []
        recipe = self.exteriorRecipe
        if recipe is not None:
            if not hasattr(recipe, "molecules"):
                recipe.molecules = []
        if recipe:
            for ingr in recipe.ingredients:
                ingr.counter = 0  # counter of placed molecules
                if ingr.left_to_place > 0:  # I DONT GET IT !
                    ingr.completion = 0.0
                    allIngredients.append(ingr)
                else:
                    ingr.completion = 1.0

        for compartment in self.compartments:
            if not hasattr(compartment, "molecules"):
                compartment.molecules = []
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

    def pickIngredient(self, vThreshStart, verbose=0):
        """
        Main function that decide the next ingredient the packing will try to
        drop. The picking is weighted or random
        """
        if self.pickWeightedIngr:
            if self.thresholdPriorities[0] == 2:
                # Graham here: Walk through -priorities first
                ingr = self.activeIngr[0]
            else:
                # prob = uniform(vRangeStart,1.0)  #Graham 9/21/11 This is wrong...vRangeStart is the point index, need active list i.e. thresholdPriority to be limited
                prob = uniform(0, 1.0)
                ingrInd = 0
                for threshProb in self.thresholdPriorities:
                    if prob <= threshProb:
                        break
                    ingrInd = ingrInd + 1
                if ingrInd < len(self.activeIngr):
                    ingr = self.activeIngr[ingrInd]
                else:
                    print("error in Environment pick Ingredient", ingrInd)
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

    def get_dpad(self, compNum):
        """Return the largest encapsulating_radius and use it for padding"""
        mr = 0.0
        if compNum == 0:  # cytoplasm -> use cyto and all surfaces
            for ingr1 in self.activeIngr:
                if ingr1.compNum >= 0:
                    r = ingr1.encapsulating_radius
                    if r > mr:
                        mr = r
        else:
            for ingr1 in self.activeIngr:
                if ingr1.compNum == compNum or ingr1.compNum == -compNum:
                    r = ingr1.encapsulating_radius
                    if r > mr:
                        mr = r
        return mr

    def getPointToDrop(
        self,
        ingr,
        free_points,
        nbFreePoints,
        distance,
        spacing,
        compId,
        vRangeStart,
        vThreshStart,
    ):
        """
        Decide next point to use for dropping a given ingredent. The picking can be
        random, based on closest distance, based on gradients, ordered.
        This function also update the available free point except when hack is on.
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
                    np = float(pp) / float(self.totalPriorities)
                else:
                    np = 0.0
                self.normalizedPriorities.append(np)
                if verbose > 1:
                    print("np is ", np, " pp is ", pp, " tp is ", np + previousThresh)
                self.thresholdPriorities.append(np + previousThresh)
                previousThresh = np + float(previousThresh)
            self.activeIngr = self.activeIngr0 + self.activeIngr12
            self.log.info("time to reject the picking %d", time() - t)

            return False, vRangeStart

        if self.pickRandPt:
            self.log.info("picking random point")
            if ingr.packing_mode == "close":
                order = numpy.argsort(allIngrDist)
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
                ptInd = self.gradients[ingr.gradient].pickPoint(allIngrPts)
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
                        "popping this gradient ingredient array must be redone using Sept 25, 2011 thesis version as above for nongraient ingredients, TODO: July 5, 2012"
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

    def removeOnePoint(self, pt, free_points, nbFreePoints):
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

    def getTotalNbObject(self, allIngredients, update_partner=False):
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

    def pack_grid(
        self,
        seedNum=14,
        name=None,
        vTestid=3,
        vAnalysis=0,
        **kw,
    ):
        """
        ## Fill the grid by picking an ingredient first and then
        ## find a suitable point using the ingredient's placer object
        """
        # set periodicity
        autopack.testPeriodicity = self.use_periodicity
        t1 = time()
        self.timeUpDistLoopTotal = 0
        self.static = []
        if self.grid is None:
            self.log.error("no grid setup")
            return
        # create a list of active ingredients indices in all recipes to allow
        # removing inactive ingredients when molarity is reached
        allIngredients = self.callFunction(self.getActiveIng)
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
            self.freePointMask = numpy.ones(nbFreePoints, dtype="int32")
            bb_insidepoint = self.grid.getPointsInCube(self.fbox, [0, 0, 0], 1.0)[:]
            self.freePointMask[bb_insidepoint] = 0
            bb_outside = numpy.nonzero(self.freePointMask)
            self.grid.compartment_ids[bb_outside] = 99999
        compartment_ids = self.grid.compartment_ids
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
                np = float(pp) / float(self.totalPriorities)
            else:
                np = 0.0
            self.normalizedPriorities.append(np)
            self.thresholdPriorities.append(np + previousThresh)
            previousThresh = np + float(previousThresh)
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

        # if bullet build the organel rbnode
        if self.place_method == "pandaBullet":
            self.setupPanda()

        # ==============================================================================
        #         #the big loop
        # ==============================================================================
        dump_freq = self.dump_freq  # 120.0#every minute
        dump = self.dump
        stime = time()

        while nbFreePoints:
            self.log.info(
                ".........At start of while loop, with vRangeStart = %d", vRangeStart
            )

            # breakin test
            if len(self.activeIngr) == 0:
                self.log.warn("exit packing loop because of len****")
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
                            "canceled by user: we'll fill with current objects up to time %d",  # noqa: E510
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

            current_ingr_compartment = ingr.compNum
            # compute dpad which is the distance at which we need to update
            # distances after the drop is successfull
            max_radius = self.get_dpad(current_ingr_compartment)

            self.log.info(
                f"picked Ingr radius {ingr.min_radius}, compNum {current_ingr_compartment}"
            )

            # find the points that can be used for this ingredient
            ##

            if ingr.compNum > 0:
                compartment = self.compartments[ingr.compNum - 1]
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
            if self.overwritePlaceMethod:
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
                "after place attempt, placed: %r, number of free points:%d, length of free points=%d",
                success,
                nbFreePoints,
                len(free_points),
            )
            if success:
                nbFreePoints = BaseGrid.updateDistances(
                    insidePoints, newDistPoints, free_points, nbFreePoints, distances
                )
                self.grid.distToClosestSurf = numpy.array(distances[:])
                self.grid.free_points = numpy.array(free_points[:])
                self.grid.nbFreePoints = len(free_points)  # -1
                # update largest protein size
                # problem when the encapsulating_radius is actually wrong
                if ingr.encapsulating_radius > self.largestProteinSize:
                    self.largestProteinSize = ingr.encapsulating_radius
                PlacedMols += 1
            else:
                self.log.info("rejected %r", ingr.rejectionCounter)

            if ingr.completion >= 1.0:
                ind = self.activeIngr.index(ingr)

                self.log.info(f"completed*************** {ingr.name}")
                self.log.info(f"PlacedMols = {PlacedMols}")
                self.log.info(f"activeIngr index of {ingr.name}, {ind}")
                self.log.info(
                    f"threshold p len {len(self.thresholdPriorities)}, {len(self.normalizedPriorities)}"
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
                        np = float(pp) / float(self.totalPriorities)
                    else:
                        np = 0.0
                    self.normalizedPriorities.append(np)
                    #                    print ('np is ', np, ' pp is ', pp, ' tp is ', np + previousThresh)
                    self.thresholdPriorities.append(np + previousThresh)
                    previousThresh = np + float(previousThresh)
                self.activeIngr = self.activeIngr0 + self.activeIngr12
            if dump and ((time() - stime) > dump_freq):
                # self.collectResultPerIngredient()
                print("SAVING", self.result_file)
                # TODO: save out intermediate simularium files
                stime = time()

        self.distancesAfterFill = distances[:]
        self.freePointsAfterFill = free_points[:]
        self.nbFreePointsAfterFill = nbFreePoints
        self.distanceAfterFill = distances[:]
        t2 = time()
        self.log.info("time to fill %d", t2 - t1)
        if self.runTimeDisplay and autopack.helper.host == "simularium":
            autopack.helper.writeToFile(None, "./realtime", self.boundingBox)

        if self.afviewer is not None and hasattr(self.afviewer, "vi"):
            self.afviewer.vi.progressBar(label="Filling Complete")
            self.afviewer.vi.resetProgressBar()
        ingredients = {}
        all_ingr_as_array = self.molecules
        for pos, rot, ingr, ptInd in self.molecules:
            if ingr.name not in ingredients:
                ingredients[ingr.name] = [ingr, [], [], []]
            mat = rot.copy()
            mat[:3, 3] = pos
            ingredients[ingr.name][1].append(pos)
            ingredients[ingr.name][2].append(rot)
            ingredients[ingr.name][3].append(numpy.array(mat))
        for compartment in self.compartments:
            for pos, rot, ingr, ptInd in compartment.molecules:
                if ingr.name not in ingredients:
                    ingredients[ingr.name] = [ingr, [], [], []]
                mat = rot.copy()
                mat[:3, 3] = pos
                ingredients[ingr.name][1].append(pos)
                ingredients[ingr.name][2].append(rot)
                ingredients[ingr.name][3].append(numpy.array(mat))
                all_ingr_as_array.append([pos, rot, ingr, ptInd])
        self.ingr_result = ingredients
        print(f"placed {len(self.molecules)}")
        if self.saveResult:
            self.save_result(
                free_points,
                distances=distances,
                t0=t2,
                vAnalysis=vAnalysis,
                vTestid=vTestid,
                seedNum=seedNum,
                all_ingr_as_array=all_ingr_as_array,
            )

    def displayCancelDialog(self):
        print(
            "Popup CancelBox: if Cancel Box is up for more than 10 sec, close box and continue loop from here"
        )

    def restore_molecules_array(self, ingr):
        if len(ingr.results):
            for elem in ingr.results:
                if ingr.compNum == 0:
                    self.molecules.append([elem[0], numpy.array(elem[1]), ingr, 0])
                else:
                    ingr.recipe.compartment.molecules.append(
                        [elem[0], numpy.array(elem[1]), ingr, 0]
                    )

    def restore(self, result, orgaresult, freePoint, tree=False):
        # should we used the grid ? the freePoint can be computed
        # result is [pos,rot,ingr.name,ingr.compNum,ptInd]
        # orgaresult is [[pos,rot,ingr.name,ingr.compNum,ptInd],[pos,rot,ingr.name,ingr.compNum,ptInd]...]
        # after restore we can build the grid and fill!
        # ingredient based dictionary
        ingredients = {}
        molecules = []
        for elem in result:
            pos, rot, name, compNum, ptInd = elem
            # needto check the name if it got the comp rule
            ingr = self.getIngrFromName(name, compNum)
            if ingr is not None:
                molecules.append([pos, numpy.array(rot), ingr, ptInd])
                if name not in ingredients:
                    ingredients[name] = [ingr, [], [], []]
                mat = numpy.array(rot)
                mat[:3, 3] = pos
                ingredients[name][1].append(pos)
                ingredients[name][2].append(numpy.array(rot))
                ingredients[name][3].append(numpy.array(mat))
                self.rTrans.append(numpy.array(pos).flatten())
                self.rRot.append(numpy.array(rot))  # rotMatj
                self.rIngr.append(ingr)
                ingr.results.append([pos, rot])
        self.molecules = molecules
        if self.exteriorRecipe:
            self.exteriorRecipe.molecules = molecules
        if len(orgaresult) == len(self.compartments):
            for i, o in enumerate(self.compartments):
                molecules = []
                for elem in orgaresult[i]:
                    pos, rot, name, compNum, ptInd = elem
                    ingr = self.getIngrFromName(name, compNum)
                    if ingr is not None:
                        molecules.append([pos, numpy.array(rot), ingr, ptInd])
                        if name not in ingredients:
                            ingredients[name] = [ingr, [], [], []]
                        mat = numpy.array(rot)
                        mat[:3, 3] = pos
                        ingredients[name][1].append(pos)
                        ingredients[name][2].append(numpy.array(rot))
                        ingredients[name][3].append(numpy.array(mat))
                        self.rTrans.append(numpy.array(pos).flatten())
                        self.rRot.append(numpy.array(rot))  # rotMatj
                        self.rIngr.append(ingr)
                        ingr.results.append([pos, rot])
                o.molecules = molecules
        # consider that one filling have occured
        if len(self.rTrans) and tree:
            self.close_ingr_bhtree = spatial.cKDTree(self.rTrans, leafsize=10)
        self.cFill = self.nFill
        self.ingr_result = ingredients
        if len(freePoint):
            self.restoreFreePoints(freePoint)
        return ingredients

    def restoreFreePoints(self, freePoint):
        self.free_points = self.freePointsAfterFill = freePoint
        self.nbFreePointsAfterFill = len(freePoint)
        self.distanceAfterFill = self.grid.distToClosestSurf
        self.distancesAfterFill = self.grid.distToClosestSurf

    def loadFreePoint(self, resultfilename):
        rfile = open(resultfilename + "free_points", "rb")
        freePoint = pickle.load(rfile)
        rfile.close()
        return freePoint

    def store(self, resultfilename=None):
        if resultfilename is None:
            resultfilename = self.result_file
        resultfilename = autopack.fixOnePath(resultfilename)
        rfile = open(resultfilename, "wb")
        # pickle.dump(self.molecules, rfile)
        # OR
        result = []
        for pos, rot, ingr, ptInd in self.molecules:
            result.append([pos, rot, ingr.name, ingr.compNum, ptInd])
        pickle.dump(result, rfile)
        rfile.close()
        for i, orga in enumerate(self.compartments):
            orfile = open(resultfilename + "organelle" + str(i), "wb")
            result = []
            for pos, rot, ingr, ptInd in orga.molecules:
                result.append([pos, rot, ingr.name, ingr.compNum, ptInd])
            pickle.dump(result, orfile)
            #            pickle.dump(orga.molecules, orfile)
            orfile.close()
        rfile = open(resultfilename + "free_points", "wb")
        pickle.dump(self.grid.free_points, rfile)
        rfile.close()

    @classmethod
    def dropOneIngr(self, pos, rot, ingrname, ingrcompNum, ptInd, rad=1.0):
        line = ""
        line += ("<%f,%f,%f>,") % (pos[0], pos[1], pos[2])
        r = rot.reshape(16)
        line += "<"
        for i in range(15):
            line += ("%f,") % (r[i])
        line += ("%f>,") % (r[15])
        line += "<%f>,<%s>,<%d>,<%d>\n" % (rad, ingrname, ingrcompNum, ptInd)
        return line

    @classmethod
    def getOneIngr(self, line):
        elem = line.split("<")
        pos = eval(elem[1][:-2])
        rot = eval(elem[2][:-2])
        rad = eval(elem[3][:-2])
        ingrname = elem[4][:-2]
        ingrcompNum = eval(elem[5][:-2])
        ptInd = eval(elem[6].split(">")[0])
        return pos, rot, ingrname, ingrcompNum, ptInd, rad

    #    @classmethod
    def getOneIngrJson(self, ingr, ingrdic):
        #        name_ingr = ingr.name
        #        if name_ingr not in ingrdic:
        #            name_ingr = ingr.o_name
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
            ingr.o_name,
            ingr.compNum,
            1,
            ingr.encapsulating_radius,
        )  # ingrdic["compNum"],1,ingrdic["encapsulating_radius"]

    def load_asTxt(self, resultfilename=None):
        if resultfilename is None:
            resultfilename = self.result_file
        rfile = open(resultfilename, "r")
        # needto parse
        result = []
        orgaresult = []  # [[],]*len(self.compartments)
        for i in range(len(self.compartments)):
            orgaresult.append([])
        #        mry90 = helper.rotation_matrix(-math.pi/2.0, [0.0,1.0,0.0])
        #        numpy.array([[0.0, 1.0, 0.0, 0.0],
        #                 [-1., 0.0, 0.0, 0.0],
        #                 [0.0, 0.0, 1.0, 0.0],
        #                 [0.0, 0.0, 0.0, 1.0]])
        lines = rfile.readlines()
        for line in lines:
            if not len(line) or len(line) < 6:
                continue
            pos, rot, ingrname, ingrcompNum, ptInd, rad = self.getOneIngr(line)
            # should I multiply here
            r = numpy.array(rot).reshape(
                4, 4
            )  # numpy.matrix(mry90)*numpy.matrix(numpy.array(rot).reshape(4,4))
            if ingrcompNum == 0:
                result.append(
                    [numpy.array(pos), numpy.array(r), ingrname, ingrcompNum, ptInd]
                )
            else:
                orgaresult[abs(ingrcompNum) - 1].append(
                    [numpy.array(pos), numpy.array(r), ingrname, ingrcompNum, ptInd]
                )
            #        for i, orga in enumerate(self.compartments):
            #            orfile = open(resultfilename+"ogra"+str(i),'rb')
            #            orgaresult.append(pickle.load(orfile))
            #            orfile.close()
            #        rfile.close()
            #        rfile = open(resultfilename+"free_points",'rb')
        freePoint = []  # pickle.load(rfile)
        try:
            rfile = open(resultfilename + "free_points", "rb")
            freePoint = pickle.load(rfile)
            rfile.close()
        except:  # noqa: E722
            pass
        return result, orgaresult, freePoint

    def collectResultPerIngredient(self):
        def cb(ingr):
            ingr.results = []

        self.loopThroughIngr(cb)
        for pos, rot, ingr, ptInd in self.molecules:
            if isinstance(ingr, GrowIngredient) or isinstance(ingr, ActinIngredient):
                pass  # already store
            else:
                ingr.results.append([pos, rot])
        for i, orga in enumerate(self.compartments):
            for pos, rot, ingr, ptInd in orga.molecules:
                if isinstance(ingr, GrowIngredient) or isinstance(
                    ingr, ActinIngredient
                ):
                    pass  # already store
                else:
                    ingr.results.append([pos, rot])

    def load_asJson(self, resultfilename=None):
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
                        if ingr.o_name not in self.result_json["exteriorRecipe"]:
                            continue
                        else:
                            name_ingr = ingr.o_name
                    iresults, ingrname, ingrcompNum, ptInd, rad = self.getOneIngrJson(
                        ingr, self.result_json["exteriorRecipe"][name_ingr]
                    )
                    ingr.results = []
                    for r in iresults:
                        rot = numpy.array(r[1]).reshape(
                            4, 4
                        )  # numpy.matrix(mry90)*numpy.matrix(numpy.array(rot).reshape(4,4))
                        ingr.results.append([numpy.array(r[0]), rot])
                        result.append(
                            [numpy.array(r[0]), rot, ingrname, ingrcompNum, 1]
                        )
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
                            orga.name + "_surf_" + ingr.o_name
                            in self.result_json[orga.name + "_surfaceRecipe"]
                        ):
                            name_ingr = orga.name + "_surf_" + ingr.o_name
                        if (
                            name_ingr
                            not in self.result_json[orga.name + "_surfaceRecipe"]
                        ):
                            # backward compatiblity
                            if (
                                ingr.o_name
                                not in self.result_json[orga.name + "_surfaceRecipe"]
                            ):
                                continue
                            else:
                                name_ingr = ingr.o_name
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
                            rot = numpy.array(r[1]).reshape(
                                4, 4
                            )  # numpy.matrix(mry90)*numpy.matrix(numpy.array(rot).reshape(4,4))
                            ingr.results.append([numpy.array(r[0]), rot])
                            orgaresult[abs(ingrcompNum) - 1].append(
                                [numpy.array(r[0]), rot, ingrname, ingrcompNum, 1]
                            )
            # organelle matrix ingr
            ri = orga.innerRecipe
            if ri:
                if orga.name + "_innerRecipe" in self.result_json:
                    for ingr in ri.ingredients:
                        name_ingr = ingr.name
                        if (
                            orga.name + "_int_" + ingr.o_name
                            in self.result_json[orga.name + "_innerRecipe"]
                        ):
                            name_ingr = orga.name + "_int_" + ingr.o_name
                        if (
                            name_ingr
                            not in self.result_json[orga.name + "_innerRecipe"]
                        ):
                            # backward compatiblity
                            if (
                                ingr.o_name
                                not in self.result_json[orga.name + "_innerRecipe"]
                            ):
                                continue
                            else:
                                name_ingr = ingr.o_name
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
                            rot = numpy.array(r[1]).reshape(
                                4, 4
                            )  # numpy.matrix(mry90)*numpy.matrix(numpy.array(rot).reshape(4,4))
                            ingr.results.append([numpy.array(r[0]), rot])
                            orgaresult[abs(ingrcompNum) - 1].append(
                                [numpy.array(r[0]), rot, ingrname, ingrcompNum, 1]
                            )
        freePoint = []  # pickle.load(rfile)
        try:
            rfile = open(resultfilename + "free_points", "rb")
            freePoint = pickle.load(rfile)
            rfile.close()
        except:  # noqa: E722
            pass
        return result, orgaresult, freePoint

    def dropOneIngrJson(self, ingr, rdic):
        adic = OrderedDict()  # [ingr.name]
        adic["compNum"] = ingr.compNum
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
                lp = numpy.array(ingr.listePtLinear[i])
                ingr.listePtLinear[i] = lp.tolist()
                adic["curve" + str(i)] = ingr.listePtLinear[i]
            #        print adic
        return adic

    def store_asJson(self, resultfilename=None, indent=True):
        if resultfilename is None:
            resultfilename = self.result_file
            resultfilename = autopack.fixOnePath(resultfilename)  # retireve?
        # if result file_name start with http?
        if resultfilename.find("http") != -1 or resultfilename.find("ftp") != -1:
            print(
                "please provide a correct file name for the result file ",
                resultfilename,
            )
        self.collectResultPerIngredient()
        self.result_json = OrderedDict()
        self.result_json["recipe"] = self.setupfile  # replace server?
        r = self.exteriorRecipe
        if r:
            self.result_json["exteriorRecipe"] = OrderedDict()
            for ingr in r.ingredients:
                self.result_json["exteriorRecipe"][ingr.o_name] = self.dropOneIngrJson(
                    ingr, self.result_json["exteriorRecipe"]
                )

        # compartment ingr
        for orga in self.compartments:
            # compartment surface ingr
            rs = orga.surfaceRecipe
            if rs:
                self.result_json[orga.name + "_surfaceRecipe"] = OrderedDict()
                for ingr in rs.ingredients:
                    self.result_json[orga.name + "_surfaceRecipe"][
                        ingr.o_name
                    ] = self.dropOneIngrJson(
                        ingr, self.result_json[orga.name + "_surfaceRecipe"]
                    )
            # compartment matrix ingr
            ri = orga.innerRecipe
            if ri:
                self.result_json[orga.name + "_innerRecipe"] = OrderedDict()
                for ingr in ri.ingredients:
                    self.result_json[orga.name + "_innerRecipe"][
                        ingr.o_name
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

    def store_asTxt(self, resultfilename=None):
        if resultfilename is None:
            resultfilename = self.result_file
        resultfilename = autopack.fixOnePath(resultfilename)
        rfile = open(resultfilename + ".txt", "w")  # doesnt work with symbol link ?
        # pickle.dump(self.molecules, rfile)
        # OR
        line = ""
        line += "<recipe include = " + self.setupfile + ">\n"
        for pos, rot, ingr, ptInd in self.molecules:
            line += self.dropOneIngr(
                pos, rot, ingr.name, ingr.compNum, ptInd, rad=ingr.encapsulating_radius
            )
            # result.append([pos,rot,ingr.name,ingr.compNum,ptInd])
        rfile.write(line)
        # write the curve point

        rfile.close()
        for i, orga in enumerate(self.compartments):
            orfile = open(resultfilename + "_organelle_" + str(i) + ".txt", "w")
            line = ""
            for pos, rot, ingr, ptInd in orga.molecules:
                line += self.dropOneIngr(
                    pos,
                    rot,
                    ingr.name,
                    ingr.compNum,
                    ptInd,
                    rad=ingr.encapsulating_radius,
                )
            orfile.write(line)
            #            pickle.dump(orga.molecules, orfile)
            orfile.close()
        #        rfile = open(resultfilename+"free_points", 'w')
        #        pickle.dump(self.free_points, rfile)
        #        rfile.close()

    @classmethod
    def convertPickleToText(self, resultfilename=None, norga=0):
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
        rfile = open(resultfilename + "free_points")
        rfile.close()
        rfile = open(resultfilename + ".txt", "w")
        line = ""
        for pos, rot, ingrName, compNum, ptInd in result:
            line += self.dropOneIngr(pos, rot, ingrName, compNum, ptInd)
            # result.append([pos,rot,ingr.name,ingr.compNum,ptInd])
        rfile.write(line)
        rfile.close()
        for i in range(norga):
            orfile = open(resultfilename + "_organelle_" + str(i) + ".txt", "w")
            result = []
            line = ""
            for pos, rot, ingrName, compNum, ptInd in orgaresult[i]:
                line += self.dropOneIngr(pos, rot, ingrName, compNum, ptInd)
            orfile.write(line)
            #            pickle.dump(orga.molecules, orfile)
            orfile.close()
            # freepoint

    def printFillInfo(self):
        r = self.exteriorRecipe
        if r is not None:
            print("    Environment exterior recipe:")
            r.printFillInfo("        ")

        for o in self.compartments:
            o.printFillInfo()

    def finishWithWater(self, free_points=None, nbFreePoints=None):
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
    # panda bullet
    # panda ode
    # ==============================================================================

    def setupOctree(
        self,
    ):
        if self.octree is None:
            self.octree = Octree(
                self.grid.getRadius(), helper=helper
            )  # Octree((0,0,0),self.grid.getRadius())   #0,0,0 or center of grid?

    def setupPanda(self):
        try:
            import panda3d
        except Exception:
            return
        from panda3d.core import loadPrcFileData

        if self.grid is not None:
            loadPrcFileData(
                "", "bullet-sap-extents " + str(self.grid.diag)
            )  # grid may not be setup
        if self.world is None:
            if panda3d is None:
                return
            loadPrcFileData(
                "",
                """
   load-display p3tinydisplay # to force CPU only rendering (to make it available as an option if everything else fail, use aux-display p3tinydisplay)
   audio-library-name null # Prevent ALSA errors
   show-frame-rate-meter 0
   sync-video 0
   bullet-max-objects 10240
   bullet-broadphase-algorithm sap
   bullet-sap-extents 10000.0
   textures-power-2 up
   textures-auto-power-2 #t
""",
            )
            #            loadPrcFileData("", "window-type none" )
            # Make sure we don't need a graphics engine
            # (Will also prevent X errors / Display errors when starting on linux without X server)
            #            loadPrcFileData("", "audio-library-name null" ) # Prevent ALSA errors
            #            loadPrcFileData('', 'bullet-enable-contact-events true')
            #            loadPrcFileData('', 'bullet-max-objects 10240')#10240
            #            loadPrcFileData('', 'bullet-broadphase-algorithm sap')#aabb
            #            loadPrcFileData('', 'bullet-sap-extents 10000.0')#
            if autopack.helper is not None and autopack.helper.nogui:
                loadPrcFileData("", "window-type offscreen")
            else:
                loadPrcFileData("", "window-type None")

            from direct.showbase.ShowBase import ShowBase

            base = ShowBase()
            base.disableMouse()
            self.base = base
            from panda3d.core import Vec3

            if self.panda_solver == "bullet":
                from panda3d.bullet import BulletWorld

                # global variable from panda3d
                self.worldNP = render.attachNewNode("World")  # noqa: F821
                self.world = BulletWorld()
                self.BitMask32 = BitMask32
            elif self.panda_solver == "ode":
                from panda3d.ode import OdeWorld, OdeHashSpace

                self.world = OdeWorld()
                # or hashspace ?
                self.ode_space = (
                    OdeHashSpace()
                )  # OdeQuadTreeSpace(center,extends,depth)
                self.ode_space.set_levels(-2, 6)
                self.ode_space.setAutoCollideWorld(self.world)

            self.world.setGravity(Vec3(0, 0, 0))
            self.static = []
            self.moving = None
            self.rb_panda = []
        for o in self.compartments:
            if o.rbnode is None:
                o.rbnode = o.addShapeRB()  # addMeshRBOrganelle(o)

    def add_rb_node(self, ingr, trans, mat):
        if ingr.type == "Mesh":
            return ingr.add_rb_mesh(self.worldNP)
        elif self.panda_solver == "ode" and ingr.type == "Sphere":
            mat3x3 = Mat3(
                mat[0], mat[1], mat[2], mat[4], mat[5], mat[6], mat[8], mat[9], mat[10]
            )
            return ingr.add_rb_node_ode(self.world, trans, mat3x3)
        return ingr.add_rb_node(self.worldNP)

    def delRB(self, node):
        if panda3d is None:
            return
        if self.panda_solver == "bullet":
            self.world.removeRigidBody(node)
            np = NodePath(node)
            if np is not None:
                np.removeNode()
        elif self.panda_solver == "ode":
            node.destroy()

        if node in self.rb_panda:
            self.rb_panda.pop(self.rb_panda.index(node))
        if node in self.static:
            self.static.pop(self.static.index(node))
        if node == self.moving:
            self.moving = None

    def setGeomFaces(self, tris, face):
        if panda3d is None:
            return
            # have to add vertices one by one since they are not in order
        if len(face) == 2:
            face = numpy.array([face[0], face[1], face[1], face[1]], dtype="int")
        for i in face:
            tris.addVertex(i)
        tris.closePrimitive()

    def addMeshRBOrganelle(self, o):
        if panda3d is None:
            return
        helper = autopack.helper
        if not autopack.helper.nogui:
            geom = helper.getObject(o.gname)
            if geom is None:
                o.gname = "%s_Mesh" % o.name
                geom = helper.getObject(o.gname)
            faces, vertices, vnormals = helper.DecomposeMesh(
                geom, edit=False, copy=False, tri=True, transform=True
            )
        else:
            faces = o.faces
            vertices = o.vertices
        inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode(o.name))
        inodenp.node().setMass(1.0)

        from panda3d.core import (
            GeomVertexFormat,
            GeomVertexWriter,
            GeomVertexData,
            Geom,
            GeomTriangles,
        )
        from panda3d.bullet import (
            BulletTriangleMesh,
            BulletTriangleMeshShape,
        )

        # step 1) create GeomVertexData and add vertex information
        format = GeomVertexFormat.getV3()
        vdata = GeomVertexData("vertices", format, Geom.UHStatic)
        vertexWriter = GeomVertexWriter(vdata, "vertex")
        [vertexWriter.addData3f(v[0], v[1], v[2]) for v in vertices]

        # step 2) make primitives and assign vertices to them
        tris = GeomTriangles(Geom.UHStatic)
        [self.setGeomFaces(tris, face) for face in faces]

        # step 3) make a Geom object to hold the primitives
        geom = Geom(vdata)
        geom.addPrimitive(tris)
        # step 4) create the bullet mesh and node
        mesh = BulletTriangleMesh()
        mesh.addGeom(geom)
        shape = BulletTriangleMeshShape(mesh, dynamic=False)  # BulletConvexHullShape
        # or
        # shape = BulletConvexHullShape()
        # shape.add_geom(geom)
        # inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode(ingr.name))
        # inodenp.node().setMass(1.0)
        inodenp.node().addShape(
            shape
        )  # ,TransformState.makePos(Point3(0, 0, 0)))#, pMat)#TransformState.makePos(Point3(jtrans[0],jtrans[1],jtrans[2])))#rotation ?

        if self.panda_solver == "bullet":
            inodenp.setCollideMask(BitMask32.allOn())
            inodenp.node().setAngularDamping(1.0)
            inodenp.node().setLinearDamping(1.0)
            #            inodenp.setMat(pmat)
            self.world.attachRigidBody(inodenp.node())
            inodenp = inodenp.node()
        return inodenp

    def addRB(self, ingr, trans, rotMat, rtype="single_sphere", static=False):
        # Sphere
        if panda3d is None:
            return None
        if autopack.verbose > 1:
            print("add RB bullet ", ingr.name)
        mat = rotMat.copy()
        #        mat[:3, 3] = trans
        #        mat = mat.transpose()
        mat = mat.transpose().reshape((16,))

        pmat = Mat4(
            mat[0],
            mat[1],
            mat[2],
            mat[3],
            mat[4],
            mat[5],
            mat[6],
            mat[7],
            mat[8],
            mat[9],
            mat[10],
            mat[11],
            trans[0],
            trans[1],
            trans[2],
            mat[15],
        )
        inodenp = None
        inodenp = self.add_rb_node(ingr, trans, mat)
        if self.panda_solver == "bullet":
            inodenp.setCollideMask(BitMask32.allOn())
            inodenp.node().setAngularDamping(1.0)
            inodenp.node().setLinearDamping(1.0)
            inodenp.setMat(pmat)
            self.world.attachRigidBody(inodenp.node())
            inodenp = inodenp.node()
        elif self.panda_solver == "ode":
            inodenp.setCollideBits(BitMask32(0x00000002))
            inodenp.setCategoryBits(BitMask32(0x00000001))
            # boxGeom.setBody(boxBody)
        self.rb_panda.append(inodenp)
        # self.moveRBnode(inodenp.node(), trans, rotMat)
        return inodenp

    def moveRBnode(self, node, trans, rotMat):
        if panda3d is None:
            return
        rotation_matrix = rotMat.copy()
        #        mat[:3, 3] = trans
        #        mat = mat.transpose()
        rotation_matrix = rotation_matrix.transpose().reshape((16,))
        if True in numpy.isnan(rotation_matrix).flatten():
            print("problem Matrix", node)
            return
        if self.panda_solver == "bullet":
            pMat = Mat4(
                rotation_matrix[0],
                rotation_matrix[1],
                rotation_matrix[2],
                rotation_matrix[3],
                rotation_matrix[4],
                rotation_matrix[5],
                rotation_matrix[6],
                rotation_matrix[7],
                rotation_matrix[8],
                rotation_matrix[9],
                rotation_matrix[10],
                rotation_matrix[11],
                trans[0],
                trans[1],
                trans[2],
                rotation_matrix[15],
            )
            nodenp = NodePath(node)
            nodenp.setMat(pMat)
        elif self.panda_solver == "ode":
            mat3x3 = Mat3(
                rotation_matrix[0],
                rotation_matrix[1],
                rotation_matrix[2],
                rotation_matrix[4],
                rotation_matrix[5],
                rotation_matrix[6],
                rotation_matrix[8],
                rotation_matrix[9],
                rotation_matrix[10],
            )
            body = node.get_body()
            body.setPosition(Vec3(trans[0], trans[1], trans[2]))
            body.setRotation(mat3x3)

    def getRotTransRB(self, node):
        if panda3d is None:
            return
        nodenp = NodePath(node)
        m = nodenp.getMat()
        M = numpy.array(m)
        rRot = numpy.identity(4)
        rRot[:3, :3] = M[:3, :3]
        rTrans = M[3, :3]
        return rTrans, rRot

    def runBullet(self, ingr, simulationTimes, runTimeDisplay):
        if panda3d is None:
            return
        done = False
        t1 = time()
        simulationTimes = 5.0
        while not done:
            # should do it after a jitter run
            #        for i in xrange(10):
            dt = globalClock.getDt()  # noqa: F821, global variable from panda3d
            self.world.doPhysics(
                dt, 100, 1.0 / 500.0
            )  # world.doPhysics(dt, 10, 1.0/180.0)100, 1./500.#2, 1.0/120.0
            # check number of contact betwee currrent and rest ?
            r = [
                (self.world.contactTestPair(self.moving, n).getNumContacts() > 0)
                for n in self.static
            ]
            done = not (True in r)
            if runTimeDisplay:
                # move self.moving and update
                nodenp = NodePath(self.moving)
                ma = nodenp.getMat()
                self.afviewer.vi.setObjectMatrix(
                    ingr.moving_geom, numpy.array(ma), transpose=False
                )  # transpose ?
                self.afviewer.vi.update()
            if (time() - t1) > simulationTimes:
                done = True
                break

                # ==============================================================================
            #               Export -> another file ?
            # ==============================================================================

    def exportToBD_BOX(self, res_filename=None, output=None, bd_type="flex"):
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

    def exportToTEM_SIM(self, res_filename=None, output=None):
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

    def exportToTEM(
        self,
    ):
        # limited to 20 ingredients, call the TEM exporter plugin ?
        # ingredient -> PDB file or mrc volume file
        # ingredient -> coordinate.txt file
        p = []  # *0.05
        rr = []
        output = "iSutm_coordinate.txt"  # ingrname_.txt
        aStr = "# File created for TEM-simulator, version 1.3.\n"
        aStr += str(len(p)) + " 6\n"
        aStr += "#            x             y             z           phi         theta           psi\n"
        for i in range(len(p)):
            aStr += "{0:14.4f}{1:14.4f}{2:14.4f}{3:14.4f}{4:14.4f}{5:14.4f}\n".format(
                p[i][0], p[i][1], p[i][2], rr[i][0], rr[i][1], rr[i][2]
            )
        f = open(output, "w")
        f.write(aStr)

    def exportToReaDDy(self):
        # wehn I will get it running ... plugin ?
        return

        # ==============================================================================

    #         Animate
    # ==============================================================================
    def readTraj(self, filename):
        self.collectResultPerIngredient()
        lenIngrInstance = len(self.molecules)
        for orga in self.compartments:
            lenIngrInstance += len(orga.molecules)
        fileName, fileExtension = os.path.splitext(filename)
        if fileExtension == ".dcd":
            self.traj = dcdTrajectory(filename, lenIngrInstance)
        elif fileExtension == ".molb":
            self.traj = molbTrajectory(filename, lenIngrInstance)
        self.traj.completeMapping(self)

    def linkTraj(self):
        # link the traj usin upy for creating a new synchronized calleback?
        if not self.traj_linked:
            autopack.helper.synchronize(self.applyStep)
            self.traj_linked = True

    def unlinkTraj(self):
        # link the traj usin upy for creating a new synchronized calleback?
        if self.traj_linked:
            autopack.helper.unsynchronize(self.applyStep)
            self.traj_linked = False

    def applyStep(self, step):
        # apply the coordinate from a trajectory at step step.
        # correspondance ingredients instance <-> coordinates file
        # trajectory class to handle
        print("Step is " + str(step))
        # if self.traj.traj_type=="dcd" or self.traj.traj_type=="xyz":
        self.traj.applyState_primitive_name(self, step)
        # ho can we apply to parent instance the rotatiotn?

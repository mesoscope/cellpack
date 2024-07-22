# -*- coding: utf-8 -*-
############################################################################
#
# autoPACK Authors: Graham T. Johnson, Mostafa Al-Alusi, Ludovic Autin,
#   and Michel Sanner
#   Based on COFFEE Script developed by Graham Johnson
#    between 2005 and 2010
#   with assistance from Mostafa Al-Alusi in 2009 and periodic input
#   from Arthur Olson's Molecular Graphics Lab
#
# Ingredient.py Authors: Graham Johnson & Michel Sanner with
#  editing/enhancement from Ludovic Autin
#
# Translation to Python initiated March 1, 2010 by Michel Sanner
#  with Graham Johnson
#
# Class restructuring and organization: Michel Sanner
#
# Copyright: Graham Johnson ©2010
#
# This file "Ingredient.py" is part of autoPACK, cellPACK.
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
# @author: Graham Johnson, Ludovic Autin, & Michel Sanner


# Hybrid version merged from Graham's Sept 2011 and Ludo's April 2012
# version on May 16, 2012
# Updated with Correct Sept 25, 2011 thesis version on July 5, 2012

# TODO: Describe Ingredient class here at high level
from scipy import spatial
import numpy
import logging
import collada
from scipy.spatial.transform import Rotation as R
from math import pi
from random import uniform, gauss, random
from time import time
import math

from cellpack.autopack.interface_objects.ingredient_types import INGREDIENT_TYPE
from cellpack.autopack.interface_objects.packed_objects import PackedObject
from cellpack.autopack.utils import get_distance, get_value_from_distribution

from .utils import (
    ApplyMatrix,
    getNormedVectorOnes,
    rotVectToVect,
    rotax,
)

from cellpack.autopack.upy.simularium.simularium_helper import simulariumHelper
import cellpack.autopack as autopack
from cellpack.autopack.ingredient.agent import Agent
from cellpack.autopack.interface_objects.meta_enum import MetaEnum

helper = autopack.helper
reporthook = None
if helper is not None:
    reporthook = helper.reporthook


class DistributionTypes(MetaEnum):
    # All available distribution types
    UNIFORM = "uniform"
    NORMAL = "normal"
    LIST = "list"


class DistributionOptions(MetaEnum):
    # All available distribution options
    MIN = "min"
    MAX = "max"
    MEAN = "mean"
    STD = "std"
    LIST_VALUES = "list_values"


REQUIRED_DISTRIBUTION_OPTIONS = {
    DistributionTypes.UNIFORM: [DistributionOptions.MIN, DistributionOptions.MAX],
    DistributionTypes.NORMAL: [DistributionOptions.MEAN, DistributionOptions.STD],
    DistributionTypes.LIST: [DistributionOptions.LIST_VALUES],
}


class IngredientInstanceDrop:
    def __init__(self, ptId, position, rotation, ingredient, rb=None):
        self.ptId = ptId
        self.position = position
        self.rotation = rotation
        self.ingredient = ingredient
        self.rigid_body = rb
        self.name = ingredient.name + str(ptId)
        x, y, z = position
        rad = ingredient.encapsulating_radius
        self.bb = ([x - rad, y - rad, z - rad], [x + rad, y + rad, z + rad])
        # maybe get bb from mesh if any ?
        if self.ingredient.mesh is not None:
            self.bb = autopack.helper.getBoundingBox(self.ingredient.mesh)
            for i in range(3):
                self.bb[0][i] = self.bb[0][i] + self.position[i]
                self.bb[1][i] = self.bb[1][i] + self.position[i]


# the ingredient should derive from a class of Agent
class Ingredient(Agent):
    static_id = 0
    """
    Base class for Ingredients that can be added to a Recipe.
    Ingredients provide:
        - a molarity used to compute how many to place
        - a generic density value
        - a unit associated with the density value
        - a jitter amplitude vector specifying by how much the jittering
        algorithm can move from the grid position.
        - a number of jitter attempts
        - an optional color used to draw the ingredient default (white)
        - an optional name
        - an optional pdb ID
        - an optional packing priority. If omitted the priority will be based
        on the radius with larger radii first
        ham here: (-)priority object will pack from high to low one at a time
        (+)priority will be weighted by assigned priority value
        (0)packignPriority will be weighted by complexity and appended to what is left
        of the (+) values
        - an optional principal vector used to align the ingredient
        - recipe will be a weakref to the Recipe this Ingredient belongs to
        - compartment_id is the compartment number (0 for cytoplasm, positive for compartment
        surface and negative compartment interior
        - Attributes used by the filling algorithm:
        - count counts the number of placed ingredients during a fill
        - counter is the target number of ingredients to place
        - completion is the ratio of placed/target
        - rejectionCounter is used to eliminate ingredients after too many failed
        attempts

    """

    ARGUMENTS = [
        "color",
        "count",
        "count_options",
        "cutoff_boundary",
        "cutoff_surface",
        "distance_expression",
        "distance_function",
        "force_random",
        "gradient",
        "gradient_weights",
        "is_attractor",
        "max_jitter",
        "molarity",
        "name",
        "jitter_attempts",
        "offset",
        "orient_bias_range",
        "overwrite_distance_function",
        "packing_mode",
        "priority",
        "partners",
        "perturb_axis_amplitude",
        "place_method",
        "principal_vector",
        "rejection_threshold",
        "representations",
        "resolution_dictionary",
        "rotation_axis",
        "rotation_range",
        "size_options",
        "type",
        "use_orient_bias",
        "use_rotation_axis",
        "weight",
    ]

    def __init__(
        self,
        type="single_sphere",
        color=None,
        count=0,
        count_options=None,
        cutoff_boundary=None,
        cutoff_surface=0.0,
        distance_expression=None,
        distance_function=None,
        force_random=False,  # avoid any binding
        gradient=None,
        gradient_weights=None,
        is_attractor=False,
        max_jitter=(1, 1, 1),
        molarity=0.0,
        name=None,
        jitter_attempts=5,
        object_name=None,
        offset=[0, 0, 0],
        orient_bias_range=[-pi, pi],
        overwrite_distance_function=True,  # overWrite
        packing_mode="random",
        priority=0,
        partners=None,
        perturb_axis_amplitude=0.1,
        place_method="jitter",
        principal_vector=(1, 0, 0),
        rejection_threshold=30,
        representations=None,
        resolution_dictionary=None,
        rotation_axis=None,
        rotation_range=6.2831,
        size_options=None,
        use_orient_bias=False,
        use_rotation_axis=False,
        weight=0.2,
    ):
        super().__init__(
            name,
            molarity,
            distance_expression=distance_expression,
            distance_function=distance_function,
            force_random=force_random,
            gradient=gradient,
            gradient_weights=gradient_weights,
            is_attractor=is_attractor,
            overwrite_distance_function=overwrite_distance_function,
            packing_mode=packing_mode,
            partners=partners,
            place_method=place_method,
            weight=weight,
        )
        self.log = logging.getLogger("ingredient")
        self.log.propagate = False

        self.molarity = molarity
        self.count = count
        self.count_options = count_options
        self.size_options = size_options
        self.priority = priority
        self.log.info(
            "priority %d,  self.priority %r",
            priority,
            self.priority,
        )
        if name is None:
            name = "%f" % molarity
        self.log.info("CREATE INGREDIENT %s %r", str(name), rejection_threshold)
        self.name = str(name)
        self.composition_name = str(name)
        self.object_name = str(object_name)
        self.type = type
        self.mesh = None
        self.representations = representations

        self.offset = offset
        self.color = color  # color used for sphere display
        if self.color == "None":
            self.color = None
        self.model_type = "Spheres"
        self.rRot = []
        self.tTrans = []
        self.htrans = []
        self.moving = None
        self.moving_geom = None
        self.rb_nodes = []  # store rbnode. no more than X ?
        self.bullet_nodes = [None, None]  # try only store 2, and move them when needd
        self.limit_nb_nodes = 50
        self.vi = autopack.helper
        self.min_radius = 1
        self.min_distance = 0
        self.deepest_level = 1
        self.is_previous = False
        self.vertices = []
        self.faces = []
        self.vnormals = []
        # self._place = self.place
        children = []
        self.children = children
        self.rbnode = {}  # keep the rbnode if any
        self.collisionLevel = 0  # self.deepest_level
        # first level used for collision detection
        self.max_jitter = max_jitter
        # (1,1,1) means 1/2 grid spacing in all directions

        self.perturb_axis_amplitude = perturb_axis_amplitude

        self.principal_vector = principal_vector

        self.recipe = None  # will be set when added to a recipe
        self.compartment_id = None
        self.compId_accepted = (
            []
        )  # if this list is defined, point picked outise the list are rejected

        # added to a compartment
        self.left_to_place = count
        self.vol_nbmol = 0

        # Packing tracking values
        self.jitter_attempts = (
            jitter_attempts  # number of jitter attempts for translation
        )
        self.nbPts = 0
        self.allIngrPts = (
            []
        )  # the list of available grid points for this ingredient to pack
        self.counter = 0  # target number of molecules for a fill
        self.completion = 0.0  # ratio of counter/count
        self.rejectionCounter = 0
        self.verts = None
        self.rad = None
        self.rapid_model = None
        # TODO : geometry : 3d object or procedural from PDB
        # TODO : usekeyword resolution->options dictionary of res :
        # TODO : {"simple":{"cms":{"parameters":{"gridres":12}},
        # TODO :            "obj":{"parameters":{"name":"","filename":""}}
        # TODO :            }
        # TODO : "med":{"method":"cms","parameters":{"gridres":30}}
        # TODO : "high":{"method":"msms","parameters":{"gridres":30}}
        # TODO : etc...

        self.rejection_threshold = rejection_threshold

        # need to build the basic shape if one provided
        self.current_resolution = "Low"  # should come from data
        self.available_resolution = ["Low", "Med", "High"]  # 0,1,2

        if resolution_dictionary is None:
            resolution_dictionary = {"Low": "", "Med": "", "High": ""}
        self.resolution_dictionary = resolution_dictionary

        self.use_rotation_axis = use_rotation_axis
        self.rotation_axis = rotation_axis
        self.rotation_range = rotation_range
        self.use_orient_bias = use_orient_bias
        self.orientBiasRotRangeMin = orient_bias_range[0]
        self.orientBiasRotRangeMax = orient_bias_range[1]

        # cutoff are used for picking point far from surface and boundary
        self.cutoff_boundary = cutoff_boundary
        self.cutoff_surface = cutoff_surface

        self.compareCompartment = False
        self.compareCompartmentTolerance = 0
        self.compareCompartmentThreshold = 0.0

        self.updateOwnFreePts = False  # work for rer python not ??
        self.haveBeenRejected = False

        self.distances_temp = []
        self.centT = None  # transformed position
        self.results = []

        self.unique_id = Ingredient.static_id
        Ingredient.static_id += 1
        self.score = ""
        self.organism = ""
        # add tiling property ? as any ingredient coud tile as hexagon. It is just the packing type

    @staticmethod
    def validate_distribution_options(distribution_options):
        """
        Validates distribution options and returns validated distribution options
        """
        if "distribution" not in distribution_options:
            raise Exception("Ingredient count options must contain a distribution")
        if not DistributionTypes.is_member(distribution_options["distribution"]):
            raise Exception(
                f"{distribution_options['distribution']} is not a valid distribution"
            )
        for required_option in REQUIRED_DISTRIBUTION_OPTIONS.get(
            distribution_options["distribution"], []
        ):
            if required_option not in distribution_options:
                raise Exception(
                    f"Missing option '{required_option}' for {distribution_options['distribution']} distribution"
                )
        return distribution_options

    @staticmethod
    def validate_ingredient_info(ingredient_info):
        """
        Validates ingredient info and returns validated ingredient info
        """
        if "count" not in ingredient_info:
            raise Exception("Ingredient info must contain a count")

        if ingredient_info["count"] < 0:
            raise Exception("Ingredient count must be greater than or equal to 0")

        if "count_options" in ingredient_info:
            ingredient_info["count_options"] = Ingredient.validate_distribution_options(
                ingredient_info["count_options"]
            )

        if "size_options" in ingredient_info:
            ingredient_info["size_options"] = Ingredient.validate_distribution_options(
                ingredient_info["size_options"]
            )

        # check if gradient information is entered correctly
        if "gradient" in ingredient_info:
            if not isinstance(ingredient_info["gradient"], (list, str)):
                raise Exception(
                    (
                        f"Invalid gradient: {ingredient_info['gradient']} "
                        f"for ingredient {ingredient_info['name']}"
                    )
                )
            if (
                ingredient_info["gradient"] == ""
                or ingredient_info["gradient"] == "None"
            ):
                raise Exception(
                    f"Missing gradient for ingredient {ingredient_info['name']}"
                )

            # if multiple gradients are provided with weights, check if weights are correct
            if isinstance(ingredient_info["gradient"], list):
                if "gradient_weights" in ingredient_info:
                    # check if gradient_weights are missing
                    if not isinstance(ingredient_info["gradient_weights"], list):
                        raise Exception(
                            f"Invalid gradient weights for ingredient {ingredient_info['name']}"
                        )
                    if len(ingredient_info["gradient"]) != len(
                        ingredient_info["gradient_weights"]
                    ):
                        raise Exception(
                            f"Missing gradient weights for ingredient {ingredient_info['name']}"
                        )

        return ingredient_info

    def reset(self):
        """reset the states of an ingredient"""
        self.counter = 0
        self.left_to_place = 0.0
        self.completion = 0.0

    def has_pdb(self):
        return self.representations.has_pdb()

    def has_mesh(self):
        return self.representations.has_mesh()

    def use_mesh(self):
        self.representations.set_active("mesh")
        return self.representations.get_mesh_path()

    def use_pdb(self):
        self.representations.set_active("atomic")
        return self.representations.get_pdb_path()

    def setTilling(self, comp):
        if self.packing_mode == "hexatile":
            from cellpack.autopack.hexagonTile import tileHexaIngredient

            self.tilling = tileHexaIngredient(
                self, comp, self.encapsulating_radius, init_seed=self.env.seed_used
            )
        elif self.packing_mode == "squaretile":
            from cellpack.autopack.hexagonTile import tileSquareIngredient

            self.tilling = tileSquareIngredient(
                self, comp, self.encapsulating_radius, init_seed=self.env.seed_used
            )
        elif self.packing_mode == "triangletile":
            from cellpack.autopack.hexagonTile import tileTriangleIngredient

            self.tilling = tileTriangleIngredient(
                self, comp, self.encapsulating_radius, init_seed=self.env.seed_used
            )

    def initialize_mesh(self, mesh_store):
        # get the collision mesh
        mesh_path = self.representations.get_mesh_path()
        meshName = self.representations.get_mesh_name()
        meshType = "file"
        self.mesh = None
        if mesh_path is not None:
            if meshType == "file":
                self.mesh = self.getMesh(mesh_path, meshName, mesh_store)
                self.log.info(f"OK got {self.mesh}")
                if self.mesh is None:
                    # display a message ?
                    self.log.warning("no geometries for ingredient " + self.name)
            # TODO: add back in raw option
            elif meshType == "raw":
                # need to build the mesh from v,f,n
                self.buildMesh(mesh_store)

        if self.mesh is not None:
            self.getEncapsulatingRadius()

    def DecomposeMesh(self, poly, edit=True, copy=False, tri=True, transform=True):
        helper = autopack.helper
        m = None
        if helper.host == "dejavu":
            m = helper.getMesh(poly)
            tr = False
        else:
            m = helper.getMesh(helper.getName(poly))
            tr = True
        self.log.info("Decompose Mesh ingredient %s %s", helper.getName(poly), m)
        # what about empty, hierarchical, should merged all the data?
        faces, vertices, vnormals = helper.DecomposeMesh(
            m, edit=edit, copy=copy, tri=tri, transform=tr
        )
        return faces, vertices, vnormals

    def getEncapsulatingRadius(self, mesh=None):
        if self.vertices is None or not len(self.vertices):
            if self.mesh:
                helper = autopack.helper
                if helper.host == "3dsmax":
                    return
                if mesh is None:
                    mesh = self.mesh
                self.log.info("getEncapsulatingRadius %r %r", self.mesh, mesh)
                self.faces, self.vertices, vnormals = self.DecomposeMesh(
                    mesh, edit=True, copy=False, tri=True
                )
        # encapsulating radius ?
        v = numpy.array(self.vertices, "f")
        try:
            length = numpy.sqrt(
                (v * v).sum(axis=1)
            )  # FloatingPointError: underflow encountered in multiply
            r = float(max(length)) + 15.0
            self.log.info(
                "self.encapsulating_radius %r %r", self.encapsulating_radius, r
            )
            self.encapsulating_radius = r
        except Exception:
            pass

    def getData(self):
        if self.vertices is None or not len(self.vertices):
            if self.mesh:
                return self.mesh.faces, self.mesh.vertices, self.mesh.vertex_normals

    def get_rb_model(self, alt=False):
        ret = 0
        if alt:
            ret = 1
        if self.bullet_nodes[ret] is None:
            self.bullet_nodes[ret] = self.env.addRB(
                self, [0.0, 0.0, 0.0], numpy.identity(4), rtype=self.type
            )
        return self.bullet_nodes[ret]

    def getMesh(self, filename, geomname, mesh_store):
        """
        Create a mesh representation from a filename for the ingredient

        @type  filename: string
        @param filename: the name of the input file
        @type  geomname: string
        @param geomname: the name of the output geometry

        @rtype:   DejaVu.IndexedPolygons/HostObjec
        @return:  the created mesh
        """
        # depending the extension of the filename, can be eitherdejaVu file, fbx or wavefront
        # no extension is DejaVu
        # should we try to see if it already exist in the scene
        mesh = mesh_store.get_object(geomname)
        if mesh is not None:
            self.log.info("retrieve %s %r", geomname, mesh)
            return mesh
        # identify extension
        file_name, file_extension = mesh_store.get_mesh_filepath_and_extension(filename)
        if file_extension.lower() == ".fbx":
            # use the host helper if any to read
            if helper is not None:  # neeed the helper
                helper.read(filename)

        elif file_extension == ".dae":
            self.log.info("read dae withHelper", filename, helper, autopack.helper)
            # use the host helper if any to read
            return None
            if helper is None:
                # need to get the mesh directly. Only possible if dae or dejavu format
                # get the dejavu heper but without the View, and in nogui mode
                h = simulariumHelper(vi="nogui")
                dgeoms = h.read(filename)
                # v,vn,f = dgeoms.values()[0]["mesh"]
                self.vertices, self.vnormals, self.faces = helper.combineDaeMeshData(
                    dgeoms.values()
                )
                self.vnormals = (
                    []
                )  # helper.normal_array(self.vertices,numpy.array(self.faces))
                geom = h.createsNmesh(geomname, self.vertices, None, self.faces)[0]
                return geom
            else:  # if helper is not None:#neeed the helper
                if helper.host == "dejavu" and helper.nogui:
                    dgeoms = helper.read(filename)
                    v, vn, f = list(dgeoms.values())[0]["mesh"]
                    self.log.info("vertices nb is %d", len(v))
                    self.vertices, self.vnormals, self.faces = (
                        v,
                        vn,
                        f,
                    )  # helper.combineDaeMeshData(dgeoms.values())
                    self.vnormals = (
                        []
                    )  # helper.normal_array(self.vertices,numpy.array(self.faces))
                    geom = helper.createsNmesh(
                        geomname, self.vertices, self.vnormals, self.faces
                    )[0]
                    return geom
                else:
                    if helper.host != "dejavu":
                        if collada is not None:
                            # need to get the mesh directly. Only possible if dae or dejavu format
                            # get the dejavu heper but without the View, and in nogui mode
                            h = simulariumHelper(vi="nogui")
                            dgeoms = h.read_mesh_file(filename)
                            # should combine both
                            self.vertices, vnormals, self.faces = h.combineDaeMeshData(
                                dgeoms.values()
                            )  # dgeoms.values()[0]["mesh"]
                            self.vnormals = helper.normal_array(
                                self.vertices, numpy.array(self.faces)
                            )
                helper.read(filename)
                geom = helper.getObject(geomname)
                if geom is None:
                    geom = helper.getObject(self.pdb.split(".")[0])
                    # rename it
                    if geom is None:
                        return None
                # rotate ?
                if helper.host == "3dsmax":  # or helper.host.find("blender") != -1:
                    helper.resetTransformation(
                        geom
                    )  # remove rotation and scale from importing??maybe not?
                if helper.host.find("blender") != -1:
                    helper.resetTransformation(geom)
                # if self.coordsystem == "left" :
                #                        mA = helper.rotation_matrix(-math.pi/2.0,[1.0,0.0,0.0])
                #                        mB = helper.rotation_matrix(math.pi/2.0,[0.0,0.0,1.0])
                #                        m=matrix(mA)*matrix(mB)
                #                        helper.setObjectMatrix(geom,matrice=m)
                #                if helper.host != "c4d"  and helper.host != "dejavu" and self.coordsystem == "left" and helper.host != "softimage" and helper.host.find("blender") == -1:
                # what about softimage
                # need to rotate the transform that carry the shape, maya ? or not ?
                #                    helper.rotateObj(geom,[0.0,-math.pi/2.0,0.0])#wayfront as well euler angle
                # swicth the axe?
                #                    oldv = self.principal_vector[:]
                #                    self.principal_vector = [oldv[2],oldv[1],oldv[0]]
                if helper.host == "softimage" and self.coordsystem == "left":
                    helper.rotateObj(
                        geom, [0.0, -math.pi / 2.0, 0.0], primitive=True
                    )  # need to rotate the primitive
                if helper.host == "c4d" and self.coordsystem == "right":
                    helper.resetTransformation(geom)
                    helper.rotateObj(
                        geom, [0.0, math.pi / 2.0, math.pi / 2.0], primitive=True
                    )
                p = helper.getObject("autopackHider")
                if p is None:
                    p = helper.newEmpty("autopackHider")
                    if helper.host.find("blender") == -1:
                        helper.toggleDisplay(p, False)
                helper.reParent(geom, p)
                return geom
            return None
        else:  # host specific file
            if helper is not None:  # neeed the helper
                helper.read(
                    filename
                )  # doesnt get the regular file ? conver state to object
                geom = helper.getObject(geomname)
                p = helper.getObject("autopackHider")
                if p is None:
                    p = helper.newEmpty("autopackHider")
                    if helper.host.find("blender") == -1:
                        helper.toggleDisplay(p, False)
                helper.reParent(geom, p)
                return geom
            return None

    def buildMesh(self, mesh_store):
        """
        Create a polygon mesh object from a dictionary verts,faces,normals
        """
        geom, vertices, faces, vnormals = mesh_store.build_mesh(
            self.mesh_info["file"], self.mesh_info["name"]
        )
        self.vertices = vertices
        self.faces = faces
        self.mesh = geom
        return geom

    def jitterPosition(self, position, spacing, normal=None):
        """
        position are the 3d coordiantes of the grid point
        spacing is the grid spacing
        this will jitter gauss(0., 0.3) * Ingredient.max_jitter
        """
        if self.compartment_id > 0:
            vx, vy, vz = v1 = self.principal_vector
            # surfacePointsNormals problem here
            v2 = normal
            try:
                rotMat = numpy.array(rotVectToVect(v1, v2), "f")
            except Exception as e:
                self.log.error(e)
                rotMat = numpy.identity(4)

        jx, jy, jz = self.max_jitter
        dx = (
            jx * spacing * uniform(-1.0, 1.0)
        )  # This needs to use the same rejection if outside of the sphere that the uniform cartesian jitters have.  Shoiuld use oneJitter instead?
        dy = jy * spacing * uniform(-1.0, 1.0)
        dz = jz * spacing * uniform(-1.0, 1.0)
        #        d2 = dx*dx + dy*dy + dz*dz
        #        if d2 < jitter2:
        if self.compartment_id > 0:  # jitter less among normal
            dx, dy, dz, dum = numpy.dot(rotMat, (dx, dy, dz, 0))
        position[0] += dx
        position[1] += dy
        position[2] += dz
        return numpy.array(position)

    def getMaxJitter(self, spacing):
        # self.max_jitter: each value is the max it can move
        # along that axis, but not cocurrently, ie, can't move
        # in the max x AND max y direction at the same time
        return max(self.max_jitter) * spacing

    def swap(self, d, n):
        d.rotate(-n)
        d.popleft()
        d.rotate(n)

    def deleteblist(self, d, n):
        del d[n]

    def get_cuttoff_value(self, spacing):
        """Returns the min value a grid point needs to be away from a surfance
        in order for this ingredient to pack. Only needs to be calculated once
        per ingredient once the jitter is set."""
        if self.min_distance > 0:
            return self.min_distance
        radius = self.min_radius
        jitter = self.getMaxJitter(spacing)

        if self.packing_mode == "close":
            cut = radius - jitter
        else:
            cut = radius - jitter
        self.min_distance = cut
        return cut

    def checkIfUpdate(self, nbFreePoints, threshold):
        """Check if we need to update the distance array. Part of the hack free points"""
        if hasattr(self, "nbPts"):
            if hasattr(self, "firstTimeUpdate") and not self.firstTimeUpdate:
                # if it has been updated before
                # check the number of inside points for this ingredient over the total
                # number of free points left
                ratio = float(self.nbPts) / float(nbFreePoints)
                # threshold defaults to zero. It's set by the env, `freePtsUpdateThreshold`
                if ratio > threshold:
                    return True
                else:
                    if self.haveBeenRejected and self.rejectionCounter > 5:
                        self.haveBeenRejected = False
                        return True
                    # do we check to total freepts? or crowded state ?
                    else:
                        return False
            else:
                self.firstTimeUpdate = False
                return True
        else:
            return True

    def get_list_of_free_indices(
        self,
        distances,
        free_points,
        nbFreePoints,
        spacing,
        comp_ids,
        threshold,
    ):
        allIngrPts = []
        allIngrDist = []
        current_comp_id = self.compartment_id
        # gets min distance an object has to be away to allow packing for this object
        cuttoff = self.get_cuttoff_value(spacing)
        if self.packing_mode == "close":
            # Get an array of free points where the distance is greater than half the cuttoff value
            # and less than the cutoff. Ie an array where the distances are all very small.
            # this also masks the array to only include points in the current commpartment
            all_distances = numpy.array(distances)[free_points]
            distance_mask = numpy.logical_and(
                numpy.less_equal(all_distances, cuttoff),
                numpy.greater_equal(all_distances, cuttoff / 2.0),
            )
            # mask compartments Id as well
            compartment_mask = numpy.array(comp_ids)[free_points] == current_comp_id
            mask_ind = numpy.nonzero(
                numpy.logical_and(distance_mask, compartment_mask)
            )[0]
            allIngrPts = numpy.array(free_points)[mask_ind].tolist()
            allIngrDist = numpy.array(distances)[mask_ind].tolist()
        else:
            starting_array = free_points
            array_length = nbFreePoints
            # if this ingredient has a grid point array already from a previous pass, and it's shorter
            # than the total number of free points, start there for picking points, because it means
            # we've already filtered out some points that are too close to surfaces for this ingredient to
            # pack and we don't want to have to filter them out again.
            if len(self.allIngrPts) > 0 and len(self.allIngrPts) < nbFreePoints:
                starting_array = self.allIngrPts
                array_length = len(self.allIngrPts)

            # use periodic update according size ratio grid
            update = self.checkIfUpdate(nbFreePoints, threshold)
            self.log.info(f"check if update: {update}")
            if update:
                # Only return points that aren't so close to a surface that we know the
                # ingredient won't fit
                for i in range(array_length):
                    pt_index = starting_array[i]
                    d = distances[pt_index]
                    if comp_ids[pt_index] == current_comp_id and d >= cuttoff:
                        allIngrPts.append(pt_index)
                self.allIngrPts = allIngrPts
            else:
                if len(self.allIngrPts) > 0:
                    allIngrPts = self.allIngrPts
                else:
                    allIngrPts = free_points[:nbFreePoints]
                    self.allIngrPts = allIngrPts
        return allIngrPts, allIngrDist

    def perturbAxis(self, amplitude):
        # modify axis using gaussian distribution but clamp
        # at amplitutde
        x, y, z = self.principal_vector
        stddev = amplitude * 0.5
        dx = gauss(0.0, stddev)
        if dx > amplitude:
            dx = amplitude
        elif dx < -amplitude:
            dx = -amplitude
        dy = gauss(0.0, stddev)
        if dy > amplitude:
            dy = amplitude
        elif dy < -amplitude:
            dy = -amplitude
        dz = gauss(0.0, stddev)
        if dz > amplitude:
            dz = amplitude
        elif dz < -amplitude:
            dz = -amplitude
        # if self.name=='2bg9 ION CHANNEL/RECEPTOR':
        return (x + dx, y + dy, z + dz)

    def transformPoints(self, trans, rot, points):
        output = []
        rot = numpy.array(rot)
        for point in points:
            output.append(numpy.matmul(rot[0:3, 0:3], point) + trans)
        return output

    def transformPoints_mult(self, trans, rot, points):
        tx, ty, tz = trans
        pos = []
        for xs, ys, zs in points:
            x = rot[0][0] * xs + rot[0][1] * ys + rot[0][2] * zs + tx
            y = rot[1][0] * xs + rot[1][1] * ys + rot[1][2] * zs + ty
            z = rot[2][0] * xs + rot[2][1] * ys + rot[2][2] * zs + tz
            pos.append([x, y, z])
        return numpy.array(pos)

    def apply_rotation(self, rot, point, origin=[0, 0, 0]):
        r = R.from_matrix([rot[0][:3], rot[1][:3], rot[2][:3]])
        new_pos = r.apply(point)
        return new_pos + numpy.array(origin)

    def alignRotation(self, jtrans, gradients):
        # for surface points we compute the rotation which
        # aligns the principal_vector with the surface normal
        vx, vy, vz = v1 = self.principal_vector
        # surfacePointsNormals problem here
        gradient_center = gradients[self.gradient].direction
        v2 = numpy.array(gradient_center) - numpy.array(jtrans)
        try:
            rotMat = numpy.array(rotVectToVect(v1, v2), "f")
        except Exception as e:
            self.log.error(f"{self.name}, {e}")
            rotMat = numpy.identity(4)
        return rotMat

    def getAxisRotation(self, rot):
        """
        combines a rotation about axis to incoming rot.
        rot aligns the principal_vector with the surface normal
        rot aligns the principal_vector with the biased diretion
        """
        if self.perturb_axis_amplitude != 0.0:
            axis = self.perturbAxis(self.perturb_axis_amplitude)
        else:
            axis = self.principal_vector
        tau = uniform(-pi, pi)
        rrot = rotax((0, 0, 0), axis, tau, transpose=1)
        rot = numpy.dot(rot, rrot)
        return rot

    def getBiasedRotation(self, rot, weight=None):
        """
        combines a rotation about axis to incoming rot
        """
        # -30,+30 ?
        if weight is not None:
            tau = uniform(-pi * weight, pi * weight)  # (-pi, pi)
        else:
            tau = gauss(
                self.orientBiasRotRangeMin, self.orientBiasRotRangeMax
            )  # (-pi, pi)
        rrot = rotax((0, 0, 0), self.rotation_axis, tau, transpose=1)
        rot = numpy.dot(rot, rrot)
        return rot

    def correctBB(self, p1, p2, radc):
        # unprecised
        x1, y1, z1 = p1
        x2, y2, z2 = p2
        #        bb = ( [x1-radc, y1-radc, z1-radc], [x2+radc, y2+radc, z2+radc] )
        mini = []
        maxi = []
        for i in range(3):
            mini.append(min(p1[i], p2[i]) - radc)
            maxi.append(max(p1[i], p2[i]) + radc)
        return numpy.array([numpy.array(mini).flatten(), numpy.array(maxi).flatten()])
        # precised:

    def getListCompFromMask(self, cId, ptsInSphere):
        # cID ie [-2,-1,-2,0...], ptsinsph = [519,300,etc]
        current = self.compartment_id
        if current < 0:  # inside
            ins = [i for i, x in enumerate(cId) if x == current]
            # surf=[i for i,x in enumerate(cId) if x == -current]
            liste = ins  # +surf
        if current > 0:  # surface
            ins = [i for i, x in enumerate(cId) if x == current]
            surf = [i for i, x in enumerate(cId) if x == -current]
            extra = [i for i, x in enumerate(cId) if x < 0]
            liste = ins + surf + extra
        elif current == 0:  # extracellular
            liste = [i for i, x in enumerate(cId) if x == current]
        return liste

    def get_new_distances_and_inside_points(
        self,
        env,
        packing_location,
        rotation_matrix,
        grid_point_index,
        grid_distance_values,
        new_dist_points,
        inside_points,
        signed_distance_to_surface=None,
    ):
        if signed_distance_to_surface is None:
            grid_point_location = env.grid.masterGridPositions[grid_point_index]
            signed_distance_to_surface = self.get_signed_distance(
                packing_location,
                grid_point_location,
                rotation_matrix,
            )

        if signed_distance_to_surface <= 0:  # point is inside dropped ingredient
            if grid_point_index not in inside_points or abs(
                signed_distance_to_surface
            ) < abs(inside_points[grid_point_index]):
                inside_points[grid_point_index] = signed_distance_to_surface
        elif (
            signed_distance_to_surface < grid_distance_values[grid_point_index]
        ):  # point in region of influence
            # need to update the distances of the master grid with new smaller distance
            if grid_point_index in new_dist_points:
                new_dist_points[grid_point_index] = min(
                    signed_distance_to_surface, new_dist_points[grid_point_index]
                )
            else:
                new_dist_points[grid_point_index] = signed_distance_to_surface
        return inside_points, new_dist_points

    def is_point_in_correct_region(self, point):
        # crude location check (using nearest grid point)
        nearest_grid_point_compartment_id = (
            self.env.compartment_id_for_nearest_grid_point(point)
        )  # offset ?
        compartment_ingr_belongs_in = self.compartment_id
        if compartment_ingr_belongs_in == 0:
            compartment = self.env
        else:
            # env isn't included in the compartment list
            # getting the compartment, regardless of the region
            compartment = self.env.compartments[abs(compartment_ingr_belongs_in) - 1]
        if compartment_ingr_belongs_in > 0:  # surface ingredient
            if self.type == "Grow":
                # need a list of accepted compartment_id
                check = False
                if len(self.compMask):
                    check = nearest_grid_point_compartment_id in self.compMask
                else:
                    check = True
                return check
            return True

        elif compartment_ingr_belongs_in < 0:
            # check if point is inside the compartment this ingr belongs in
            # more detailed check that just the nearest grid point
            inside = compartment.is_point_inside_mesh(
                point, self.env.grid.diag, self.env.mesh_store, ray=3
            )
            return inside
        elif compartment_ingr_belongs_in == 0:  # shouldnt be in any compartments
            for o in self.env.compartments:
                inside = o.is_point_inside_mesh(
                    point, self.env.grid.diag, self.env.mesh_store, ray=3
                )
                # if inside a compartment, we can't pack here.
                if inside:
                    return False
            return compartment_ingr_belongs_in == nearest_grid_point_compartment_id

    def far_enough_from_surfaces(self, point, cutoff):
        # check if clear of all other compartment surfaces
        ingredient_compartment = self.get_compartment(self.env)
        ingredient_compartment_id = self.compartment_id
        for compartment in self.env.compartments:
            if (
                ingredient_compartment_id > 0
                and ingredient_compartment.name == compartment.name
            ):
                continue
            # checking compartments I don't belong to
            res = compartment.OGsrfPtsBht.query(point)
            if len(res) == 2:
                d = res[0]
                if d < cutoff:
                    # too close to a surface
                    return False
        return True

    def point_is_available(self, newPt):
        """Takes in a vector returns a boolean"""
        point_in_correct_region = True
        far_from_surfaces = False
        on_grid = self.env.grid.is_point_inside_bb(
            newPt,
            dist=self.cutoff_boundary,
            jitter=getNormedVectorOnes(self.max_jitter),
        )
        if on_grid:
            point_in_correct_region = self.is_point_in_correct_region(newPt)
            if point_in_correct_region:
                # check how far from surface ?
                far_from_surfaces = self.far_enough_from_surfaces(
                    newPt, cutoff=self.cutoff_surface
                )

                return far_from_surfaces
            else:
                return False
        else:
            return False

    def oneJitter(self, env, trans, rotMat):
        jtrans = self.randomize_translation(env, trans, rotMat)
        rotMatj = self.randomize_rotation(rotMat, env)
        return jtrans, rotMatj

    def get_new_jitter_location_and_rotation(
        self, env, starting_pos, starting_rotation
    ):
        if self.packing_mode[-4:] == "tile":
            packing_location = starting_pos
            packing_rotation = starting_rotation[:]
            return packing_location, packing_rotation

        return self.oneJitter(env, starting_pos, starting_rotation)

    def getIngredientsInBox(self, env, jtrans, rotMat, compartment):
        if env.windowsSize_overwrite:
            radius = env.windowsSize
        else:
            radius = (
                self.min_radius
                + env.largestProteinSize
                + env.smallestProteinSize
                + env.windowsSize
            )
        x, y, z = jtrans
        bb = (
            [x - radius, y - radius, z - radius],
            [x + radius, y + radius, z + radius],
        )
        if self.model_type == "Cylinders":
            cent1T = self.transformPoints(
                jtrans, rotMat, self.positions[self.deepest_level]
            )
            cent2T = self.transformPoints(
                jtrans, rotMat, self.positions2[self.deepest_level]
            )
            bbs = []
            for radc, p1, p2 in zip(self.radii, cent1T, cent2T):
                bb = self.correctBB(p1, p2, radc)
                bbs.append(bb)
            # get min and max from all bbs
            maxBB = [0, 0, 0]
            minBB = [9999, 9999, 9999]
            for bb in bbs:
                for i in range(3):
                    if bb[0][i] < minBB[i]:
                        minBB[i] = bb[0][i]
                    if bb[1][i] > maxBB[i]:
                        maxBB[i] = bb[1][i]
                    if bb[1][i] < minBB[i]:
                        minBB[i] = bb[1][i]
                    if bb[0][i] > maxBB[i]:
                        maxBB[i] = bb[0][i]
            bb = [minBB, maxBB]
        if env.runTimeDisplay > 1:
            box = self.vi.getObject("partBox")
            if box is None:
                box = self.vi.Box("partBox", cornerPoints=bb, visible=1)
            else:
                self.vi.toggleDisplay(box, True)
                self.vi.updateBox(box, cornerPoints=bb)
                self.vi.update()
                #            sleep(1.0)
        # pointsInCube = env.grid.getPointsInCube(bb, jtrans, radius)
        # should we got all ingre from all recipes?
        # can use the kdtree for it...
        # maybe just add the surface if its not already the surface
        ingredients = []
        for obj in compartment.packed_objects.get():
            ingredients.append([obj, get_distance(obj.position, jtrans)])

        return ingredients

    def get_partners(self, env, jtrans, rotMat, organelle):
        closest_ingredients = env.get_closest_ingredients(jtrans, cutoff=env.grid.diag)
        if not len(closest_ingredients["indices"]):
            near_by_ingredients = self.getIngredientsInBox(
                env, jtrans, rotMat, organelle
            )
        else:
            near_by_ingredients = env.get_ingredients_in_tree(closest_ingredients)
        placed_partners = []
        if not len(near_by_ingredients):
            self.log.info("no close ingredient found")
            return [], []
        else:
            self.log.info("nb close ingredient %s", self.name)
        for i in range(len(near_by_ingredients)):
            packed_ingredient = near_by_ingredients[i][0].ingredient
            distance = near_by_ingredients[i][1]
            if self.packing_mode == "closePartner":
                if self.partners.is_partner(packed_ingredient.name):
                    placed_partners.append(
                        [
                            i,
                            self.partners.get_partner_by_ingr_name(
                                packed_ingredient.name
                            ),
                            distance,
                        ]
                    )
            if packed_ingredient.is_attractor:
                # add all ingredients as possible partners
                # attractors are universal attractors
                if not self.partners.is_partner(packed_ingredient.name):
                    part = self.partners.get_partner_by_ingr_name(
                        packed_ingredient.name
                    )
                    if part is None:
                        part = self.partners.add_partner(
                            packed_ingredient, weight=packed_ingredient.weight
                        )
                    if packed_ingredient.distance_expression is not None:
                        part.distance_expression = packed_ingredient.distance_expression
                    placed_partners.append([i, part, distance])
        if not placed_partners:
            self.log.info("no partner found in close ingredient %s", self.packing_mode)
            return [], []
        else:
            return near_by_ingredients, placed_partners

    def get_new_pos(self, ingr, pos, rot, positions_to_adjust):
        """
        Takes positions_to_adjust, such as an array of spheres at a level in a
        sphere tree, and adjusts them relative to the given position and rotation
        """
        if positions_to_adjust is None:
            positions_to_adjust = ingr.positions[0]
        return self.transformPoints(pos, rot, positions_to_adjust)

    def check_against_one_packed_ingr(self, index, level, search_tree):
        ingredient_instance = self.env.packed_objects.get_ingredients()[index]
        ingredient_class = ingredient_instance.ingredient
        positions_of_packed_ingr_spheres = self.get_new_pos(
            ingredient_class,
            ingredient_instance.position,
            ingredient_instance.rotation,
            ingredient_class.positions[level],
        )
        # check distances between the spheres at this level in the ingr we are packing
        # to the spheres at this level in the ingr already placed
        # return the number of distances for the spheres we are trying to place
        dist_from_packed_spheres_to_new_spheres, ind = search_tree.query(
            positions_of_packed_ingr_spheres, len(self.positions[level])
        )
        # return index of sph1 closest to pos of packed ingr
        cradii = numpy.array(self.radii[level])[ind]
        oradii = numpy.array(
            self.env.packed_objects.get_ingredients()[index].ingredient.radii[level]
        )
        sumradii = numpy.add(cradii.transpose(), oradii).transpose()
        sD = dist_from_packed_spheres_to_new_spheres - sumradii
        return len(numpy.nonzero(sD < 0.0)[0]) != 0

    def np_check_collision(self, packing_location, rotation):
        has_collision = False
        # no ingredients packed yet
        packed_objects = self.env.packed_objects.get_ingredients()
        if not len(packed_objects):
            return has_collision
        else:
            if self.env.close_ingr_bhtree is None:
                self.env.close_ingr_bhtree = spatial.cKDTree(
                    self.env.packed_objects.get_positions(), leafsize=10
                )
        # starting at level 0, check encapsulating radii
        level = 0
        total_levels = 0 if not hasattr(self, "positions") else len(self.positions)
        (
            distances_from_packing_location_to_all_ingr,
            ingr_indexes,
        ) = self.env.close_ingr_bhtree.query(packing_location, len(packed_objects))
        radii_of_placed_ingr = numpy.array(
            self.env.packed_objects.get_encapsulating_radii()
        )[ingr_indexes]
        overlap_distance = distances_from_packing_location_to_all_ingr - (
            self.encapsulating_radius + radii_of_placed_ingr
        )
        # if overlap_distance is negative, the encapsualting radii are overlapping
        overlap_indexes = numpy.nonzero(overlap_distance < 0.0)[0]

        if len(overlap_indexes) != 0:
            level = level + 1
            # single sphere ingr will exit here.
            if level >= total_levels:
                has_collision = True
            # for each packed ingredient that had a collision, we want to check the more
            # detailed geometry, ie walk down the sphere tree file.
            while level < total_levels:
                pos_of_attempting_ingr = self.get_new_pos(
                    self, packing_location, rotation, self.positions[level]
                )
                search_tree_for_new_ingr = spatial.cKDTree(pos_of_attempting_ingr)
                collision_at_this_level = False
                # NOTE: At certain lengths of overlap_indices, it might help to remove items from the list
                # if they dont have a collision at a non max level, but for short arrays, removing indices
                # takes longer than not checking it.
                for overlap_index in overlap_indexes:
                    index = ingr_indexes[overlap_index]
                    collision_at_this_level = self.check_against_one_packed_ingr(
                        index, level, search_tree_for_new_ingr
                    )
                    if collision_at_this_level:
                        break
                level += 1
                if collision_at_this_level:
                    if level == total_levels:
                        # found collision at lowest level, break all the way out
                        return True
                del search_tree_for_new_ingr
        return has_collision

    def checkDistance(self, liste_nodes, point, cutoff):
        for node in liste_nodes:
            rTrans, rRot = self.env.getRotTransRB(node)
            d = self.vi.measure_distance(rTrans, point)
            print("checkDistance", d, d < cutoff)

    def get_rbNodes(
        self, close_indice, currentpt, removelast=False, prevpoint=None, getInfo=False
    ):
        # move around the rbnode and return it
        # self.env.loopThroughIngr( self.env.reset_rbnode )
        if self.compartment_id == 0:
            organelle = self.env
        else:
            organelle = self.env.compartments[abs(self.compartment_id) - 1]
        nodes = []
        #        a=numpy.asarray(self.env.rTrans)[close_indice["indices"]]
        #        b=numpy.array([currentpt,])
        distances = close_indice[
            "distances"
        ]  # spatial.distance.cdist(a,b)#close_indice["distance"]
        for nid, n in enumerate(close_indice["indices"]):
            if n == -1:
                continue
            # if n == len(close_indice["indices"]):
            #                continue
            if n >= len(self.env.rIngr):
                continue
            ingr = self.env.rIngr[n]
            if len(distances):
                if distances[nid] == 0.0:
                    continue
                if (
                    distances[nid]
                    > (ingr.encapsulating_radius + self.encapsulating_radius)
                    * self.env.scaleER
                ):
                    continue

            jtrans = self.env.rTrans[n]
            rotMat = self.env.rRot[n]
            if prevpoint is not None:
                # if prevpoint == jtrans : continue
                d = self.vi.measure_distance(
                    numpy.array(jtrans), numpy.array(prevpoint)
                )
                if d == 0:  # same point
                    continue
            if self.type == "Grow":
                if self.name == ingr.name:
                    c = len(self.env.rIngr)
                    if (n == c) or n == (c - 1):  # or  (n==(c-2)):
                        continue
            if ingr.name in self.partners and self.type == "Grow":
                c = len(self.env.rIngr)
                if (n == c) or n == (c - 1):  # or (n==c-2):
                    continue
            if self.name in ingr.partners and ingr.type == "Grow":
                c = len(self.env.rIngr)
                if (n == c) or n == (c - 1):  # or (n==c-2):
                    continue
                    #            if self.packing_mode == 'hexatile' :
                    #                #no self collition for testing
                    #                if self.name == ingr.name :
                    #                    continue
            rbnode = ingr.get_rb_model(alt=(ingr.name == self.name))
            if getInfo:
                nodes.append([rbnode, jtrans, rotMat, ingr])
            else:
                nodes.append(rbnode)
        # append organelle rb nodes
        for o in self.env.compartments:
            if self.compartment_id > 0 and o.name == organelle.name:
                # this i notworking for growing ingredient like hair.
                # should had after second segments
                if self.type != "Grow":
                    continue
                else:
                    # whats the current length
                    if len(self.results) <= 1:
                        continue
            orbnode = o.get_rb_model()
            if orbnode is not None:
                # test distance to surface ?
                res = o.OGsrfPtsBht.query(tuple(numpy.array([currentpt])))
                if len(res) == 2:
                    d = res[0][0]
                    if d < self.encapsulating_radius:
                        if not getInfo:
                            nodes.append(orbnode)
                        else:
                            nodes.append([orbnode, [0, 0, 0], numpy.identity(4), o])
                            #        if self.compartment_id < 0 or self.compartment_id == 0 :
                            #            for o in self.env.compartments:
                            #                if o.rbnode is not None :
                            #                    if not getInfo :
                            #                        nodes.append(o.rbnode)
        self.env.nodes = nodes
        return nodes

    def update_data_tree(self):
        if len(self.env.packed_objects.get_ingredients()) >= 1:
            self.env.close_ingr_bhtree = spatial.cKDTree(
                self.env.packed_objects.get_positions(), leafsize=10
            )

    def pack_at_grid_pt_location(
        self,
        env,
        jtrans,
        rotation_matrix,
        dpad,
        grid_point_distances,
        inside_points,
        new_dist_points,
        pt_index,
    ):

        packing_location = jtrans
        radius_of_area_to_check = self.encapsulating_radius + dpad
        self.store_packed_object(packing_location, rotation_matrix, pt_index)

        bounding_points_to_check = self.get_all_positions_to_check(packing_location)

        for bounding_point_position in bounding_points_to_check:
            grid_points_to_update = env.grid.getPointsInSphere(
                bounding_point_position, radius_of_area_to_check
            )
            for grid_point_index in grid_points_to_update:
                (
                    inside_points,
                    new_dist_points,
                ) = self.get_new_distances_and_inside_points(
                    env,
                    bounding_point_position,
                    rotation_matrix,
                    grid_point_index,
                    grid_point_distances,
                    new_dist_points,
                    inside_points,
                )
        return inside_points, new_dist_points

    def remove_from_realtime_display(env, moving):
        pass
        # env.afvi.vi.deleteObject(moving)

    def reject(
        self,
    ):
        # got rejected
        self.haveBeenRejected = True
        self.rejectionCounter += 1
        self.log.info("Failed ingr:%s rejections:%d", self.name, self.rejectionCounter)
        if (
            self.rejectionCounter >= self.rejection_threshold
        ):  # Graham set this to 6000 for figure 13b (Results Fig 3 Test1) otehrwise it fails to fill small guys
            self.log.info("PREMATURE ENDING of ingredient %s", self.name)
            self.completion = 1.0

    def store_packed_object(self, position, rotation, index):
        packed_object = PackedObject(
            position=position,
            rotation=rotation,
            radius=self.get_radius(),
            pt_index=index,
            ingredient=self,
        )
        self.env.packed_objects.add(packed_object)
        if self.compartment_id != 0:
            compartment = self.get_compartment(self.env)
            compartment.packed_objects.add(packed_object)

    def place(
        self,
        env,
        dropped_position,
        dropped_rotation,
        grid_point_index,
        new_inside_points,
    ):
        self.nbPts = self.nbPts + len(new_inside_points)

        env.update_after_place(grid_point_index)

        if self.packing_mode[-4:] == "tile":
            nexthexa = self.tilling.dropTile(
                self.tilling.idc,
                self.tilling.edge_id,
                dropped_position,
                dropped_rotation,
            )
            self.log.info("drop next hexa %s", nexthexa.name)
        # add one to molecule counter for this ingredient
        self.counter += 1
        self.completion = float(self.counter) / float(self.left_to_place)
        self.rejectionCounter = 0
        self.update_data_tree()

    def update_ingredient_size(self):
        # update the size of the ingredient based on input options
        if hasattr(self, "size_options") and self.size_options is not None:
            if self.type == INGREDIENT_TYPE.SINGLE_SPHERE:
                radius = get_value_from_distribution(
                    distribution_options=self.size_options
                )
                if radius is not None:
                    self.radius = radius
                    self.encapsulating_radius = radius

    def attempt_to_pack_at_grid_location(
        self,
        env,
        ptInd,
        grid_point_distances,
        max_radius,
        spacing,
        usePP,
        collision_possible,
    ):
        success = False
        jitter = self.getMaxJitter(spacing)
        self.update_ingredient_size()

        dpad = self.min_radius + max_radius + jitter
        self.vi = autopack.helper
        self.env = env  # NOTE: do we need to store the env on the ingredient?
        self.log.info(
            "PLACING INGREDIENT %s, place_method=%s, index=%d, position=%r",
            self.name,
            self.place_method,
            ptInd,
            env.grid.masterGridPositions[ptInd],
        )
        compartment = self.get_compartment(env)
        gridPointsCoords = env.grid.masterGridPositions
        rotation_matrix = self.get_rotation(ptInd, env, compartment)
        target_grid_point_position = gridPointsCoords[
            ptInd
        ]  # drop point, surface points.
        if numpy.sum(self.offset) != 0.0:
            target_grid_point_position = (
                numpy.array(target_grid_point_position)
                + ApplyMatrix([self.offset], rotation_matrix)[0]
            )
        target_grid_point_position = gridPointsCoords[
            ptInd
        ]  # drop point, surface points.

        current_visual_instance = None
        if env.runTimeDisplay:
            current_visual_instance = self.handle_real_time_visualization(
                autopack.helper, ptInd, target_grid_point_position, rotation_matrix
            )
        is_realtime = current_visual_instance is not None
        # NOTE: move the target point for close partner check.
        # I think this should be done ealier, when we're getting the point index
        if self.packing_mode == "closePartner":
            target_grid_point_position, rotation_matrix = self.close_partner_check(
                env,
                target_grid_point_position,
                rotation_matrix,
                compartment,
                env.afviewer,
                current_visual_instance,
            )
            if target_grid_point_position is None:
                return False, {}, {}
        is_fiber = self.type == "Grow" or self.type == "Actine"
        collision_possible = True
        if collision_possible or is_fiber:
            if is_fiber:
                success, jtrans, rotMatj, insidePoints, newDistPoints = self.grow_place(
                    env,
                    ptInd,
                    env.grid.free_points,
                    env.grid.nbFreePoints,
                    grid_point_distances,
                    dpad,
                )
            elif self.place_method == "jitter":
                (
                    success,
                    jtrans,
                    rotMatj,
                    insidePoints,
                    newDistPoints,
                ) = self.jitter_place(
                    env,
                    target_grid_point_position,
                    rotation_matrix,
                    current_visual_instance,
                    grid_point_distances,
                    dpad,
                    ptInd,
                )
            elif self.place_method == "spheresSST":
                (
                    success,
                    jtrans,
                    rotMatj,
                    insidePoints,
                    newDistPoints,
                ) = self.spheres_SST_place(
                    env,
                    compartment,
                    ptInd,
                    target_grid_point_position,
                    rotation_matrix,
                    current_visual_instance,
                    grid_point_distances,
                    dpad,
                )

            else:
                self.log.error("Can't pack using this method %s", self.place_method)
                self.reject()
                return False, {}, {}
        else:
            # blind packing without further collision checks
            # TODO: make this work for ingredients other than single spheres

            success = True
            (jtrans, rotMatj) = self.get_new_jitter_location_and_rotation(
                env, target_grid_point_position, rotation_matrix
            )
            (insidePoints, newDistPoints) = self.pack_at_grid_pt_location(
                env,
                jtrans,
                rotMatj,
                dpad,
                grid_point_distances,
                insidePoints,
                newDistPoints,
                ptInd,
            )
        if success:
            if is_realtime:
                autopack.helper.set_object_static(
                    current_visual_instance, jtrans, rotMatj
                )
            self.place(env, jtrans, rotMatj, ptInd, insidePoints)
        else:
            if is_realtime:
                self.remove_from_realtime_display(current_visual_instance)
            self.reject()

        return success, insidePoints, newDistPoints

    def get_rotation(self, pt_ind, env, compartment):
        # compute rotation matrix rotMat
        comp_num = self.compartment_id

        rot_mat = numpy.identity(4)
        if comp_num > 0:
            # for surface points we compute the rotation which
            # aligns the principal_vector with the surface normal
            v1 = self.principal_vector
            v2 = compartment.get_normal_for_point(
                pt_ind, env.grid.masterGridPositions[pt_ind], env.mesh_store
            )
            try:
                rot_mat = numpy.array(rotVectToVect(v1, v2), "f")
            except Exception as e:
                print(f"PROBLEM: {self.name}, {e}")
                rot_mat = numpy.identity(4)
        else:
            # this is where we could apply biased rotation ie gradient/attractor
            if self.use_rotation_axis:
                if sum(self.rotation_axis) == 0.0:
                    rot_mat = numpy.identity(4)
                elif (
                    self.use_orient_bias and self.packing_mode == "gradient"
                ):  # you need a gradient here
                    rot_mat = self.alignRotation(
                        env.grid.masterGridPositions[pt_ind], env.gradients
                    )
                else:
                    rot_mat = env.helper.rotation_matrix(
                        random() * self.rotation_range, self.rotation_axis
                    )
            # for other points we get a random rotation
            else:
                rot_mat = env.randomRot.get()
        return rot_mat

    def randomize_rotation(self, rotation, env):
        # randomize rotation about axis
        jitter_rotation = numpy.identity(4)
        if self.compartment_id > 0:
            jitter_rotation = self.getAxisRotation(rotation)
        else:
            if self.use_rotation_axis:
                if sum(self.rotation_axis) == 0.0:
                    jitter_rotation = numpy.identity(4)
                    # Graham Oct 16,2012 Turned on always rotate below as default.  If you want no rotation
                    # set use_rotation_axis = 1 and set rotation_axis = 0, 0, 0 for that ingredient
                elif self.use_orient_bias and self.packing_mode == "gradient":
                    jitter_rotation = self.getBiasedRotation(rotation, weight=None)
                else:
                    # should we align to this rotation_axis ?
                    jitter_rotation = env.helper.rotation_matrix(
                        random() * self.rotation_range, self.rotation_axis
                    )
            else:
                if env is not None:
                    jitter_rotation = env.randomRot.get()
                    if self.rotation_range != 0.0:
                        return jitter_rotation
                    else:
                        return rotation.copy()
                else:
                    jitter_rotation = rotation.copy()
        return jitter_rotation

    def randomize_translation(self, env, translation, rotation):
        # jitter points location
        spacing = env.grid.gridSpacing
        jitter = spacing / 2.0
        jitter_sq = jitter * jitter
        jx, jy, jz = self.max_jitter
        tx, ty, tz = translation
        dx, dy, dz, d2 = [0.0, 0.0, 0.0, 0.0]
        jitter_trans = [0.0, 0.0, 0.0]

        if jitter_sq > 0.0:
            found = False
            # NOTE: making sure it hasn't picked a jitter point outside of the
            # sphere created by the half way point to the next grid points
            # TODO: Try seeing if this can be calculated more efficently using
            # polar coordinates
            while not found:
                dx = jx * jitter * uniform(-1.0, 1.0)
                dy = jy * jitter * uniform(-1.0, 1.0)
                dz = jz * jitter * uniform(-1.0, 1.0)
                d2 = dx * dx + dy * dy + dz * dz
                if d2 < jitter_sq:
                    if self.compartment_id > 0:  # jitter less among normal
                        dx, dy, dz, _ = numpy.dot(rotation, (dx, dy, dz, 0))
                    jitter_trans = (tx + dx, ty + dy, tz + dz)
                    found = True
        else:
            jitter_trans = translation
        return jitter_trans

    def update_display_rt(self, current_instance, translation, rotation):
        mat = rotation.copy()
        mat[:3, 3] = translation
        autopack.helper.move_object(current_instance, translation, mat)

        autopack.helper.update()

    def rigid_place(
        self,
        env,
        ptInd,
        compartment,
        target_grid_point_position,
        rotation_matrix,
        nbFreePoints,
        distance,
        dpad,
        moving,
    ):
        """
        drop the ingredient on grid point ptInd
        """
        afvi = env.afviewer
        simulationTimes = env.simulationTimes
        runTimeDisplay = env.runTimeDisplay
        springOptions = env.springOptions
        is_realtime = moving is not None

        jtrans, rotMatj = self.oneJitter(
            env, target_grid_point_position, rotation_matrix
        )

        # here should go the simulation
        # 1- we build the ingredient if not already and place the ingredient at jtrans, rotMatj
        moving = None
        static = []
        target = None
        targetPoint = jtrans
        #        import c4d
        # c4d.documents.RunAnimation(c4d.documents.GetActiveDocument(), True)

        if is_realtime:
            self.update_display_rt(moving, jtrans, rotMatj)
        # 2- get the neighboring object from ptInd
        near_by_ingredients, placed_partners = self.get_partners(
            env, jtrans, rotation_matrix, compartment
        )
        for i, elem in enumerate(near_by_ingredients):
            ing = elem[2]
            t = elem[0]
            r = elem[1]
            ind = elem[3]
            # print "neighbour",ing.name
            if hasattr(ing, "mesh_3d"):
                # create an instance of mesh3d and place it
                name = ing.name + str(ind)
                if ing.mesh_3d is None:
                    ipoly = afvi.vi.Sphere(
                        name, radius=self.radii[0][0], parent=afvi.staticMesh
                    )[0]
                    afvi.vi.setTranslation(ipoly, pos=t)
                else:
                    ipoly = afvi.vi.newInstance(
                        name,
                        ing.mesh_3d,
                        matrice=r,  # .GetDown()
                        location=t,
                        parent=afvi.staticMesh,
                    )
                static.append(ipoly)
            elif ing.type == "Grow":
                name = ing.name + str(ind)
                ipoly = afvi.vi.newInstance(
                    name, afvi.orgaToMasterGeom[ing], parent=afvi.staticMesh
                )
                static.append(ipoly)

        if placed_partners:
            if not self.force_random:
                targetPoint = self.pick_partner_grid_index(
                    near_by_ingredients,
                    placed_partners,
                    current_packing_position=jtrans,
                )
                if targetPoint is None:
                    targetPoint = jtrans
            else:
                targetPoint = jtrans
        # setup the target position
        if self.place_method == "spring":
            afvi.vi.setRigidBody(afvi.movingMesh, **env.dynamicOptions["spring"])
            # target can be partner position?
            target = afvi.vi.getObject("target" + name)
            if target is None:
                target = afvi.vi.Sphere("target" + name, radius=5.0)[0]
            afvi.vi.setTranslation(target, pos=targetPoint)
            afvi.vi.addObjectToScene(None, target)
            # 3- we setup the spring (using the sphere position empty)
            spring = afvi.vi.getObject("afspring")
            if spring is None:
                spring = afvi.vi.createSpring(
                    "afspring", targetA=moving, tragetB=target, **springOptions
                )
            else:
                afvi.vi.updateSpring(
                    spring, targetA=moving, tragetB=target, **springOptions
                )
        else:
            # before assigning should get outside thge object
            afvi.vi.setRigidBody(afvi.movingMesh, **env.dynamicOptions["moving"])
            afvi.vi.setTranslation(self.moving, pos=targetPoint)
        afvi.vi.setRigidBody(afvi.staticMesh, **env.dynamicOptions["static"])
        # 4- we run the simulation
        # c4d.documents.RunAnimation(c4d.documents.GetActiveDocument(), False,True)
        # if runTimeDisplay :
        afvi.vi.update()
        #        rTrans = afvi.vi.ToVec(afvi.vi.getTranslation(moving))
        #        rRot = afvi.vi.getMatRotation(moving)

        # print afvi.vi.ToVec(moving.GetAllPoints()[0])
        # afvi.vi.animationStart(duration = simulationTimes)
        # afvi.vi.update()
        afvi.vi.frameAdvanced(duration=simulationTimes, display=runTimeDisplay)  # ,
        # 5- we get the resuling transofrmation matrix and decompose ->rTrans rRot
        # if runTimeDisplay :
        afvi.vi.update()
        rTrans = afvi.vi.ToVec(afvi.vi.getTranslation(moving))
        rRot = afvi.vi.getMatRotation(moving)
        #        M=moving.GetMg()
        # print afvi.vi.ToVec(moving.GetAllPoints()[0])

        # 6- clean and delete everything except the spring
        afvi.vi.deleteObject(moving)
        afvi.vi.deleteObject(target)
        for o in static:
            afvi.vi.deleteObject(o)
        jtrans = rTrans[:]
        rotMatj = rRot[:]
        centT = self.transformPoints(jtrans, rotMatj, self.positions[-1])

        insidePoints = {}
        newDistPoints = {}
        insidePoints, newDistPoints = self.get_new_distance_values(
            env.grid,
            env.masterGridPositions,
            dpad,
            distance,
            centT,
            jtrans,
            rotMatj,
            dpad,
        )

        # save dropped ingredient

        env.rTrans.append(jtrans)
        env.result.append([jtrans, rotMatj, self, ptInd])
        env.rRot.append(rotMatj)
        env.rIngr.append(self)

        self.rRot.append(rotMatj)
        self.tTrans.append(jtrans)

        self.log.info(
            "Success nbfp:%d %d/%d dpad %.2f",
            nbFreePoints,
            self.counter,
            self.count,
            dpad,
        )

        success = True
        return success, jtrans, rotMatj, insidePoints, newDistPoints

    def merge_place_results(self, new_results, accum_results):
        for pt in new_results:
            if pt not in accum_results:
                accum_results[pt] = new_results[pt]
            else:
                if new_results[pt] <= 0 and accum_results[pt] > 0:
                    # newly inside point
                    accum_results[pt] = new_results[pt]
                elif new_results[pt] <= 0 and accum_results[pt] <= 0:
                    # was already inside, get closet distance
                    if abs(new_results[pt]) < abs(accum_results[pt]):
                        accum_results[pt] = new_results[pt]
                else:
                    accum_results[pt] = min(accum_results[pt], new_results[pt])

        return accum_results

    def get_all_positions_to_check(self, packing_location):
        """Takes a starting position in the packing space, and returns all the points that
        need to be tested for a collision as an array.

            If the point isn't close to an edge, will return just the staring point.
            If the point is close to the side of the bounding box, will return an array of 2.
            If the point is close to an edge of the bb (which is a "corner" in 2D), will return an array of 3.
            If the point is close to a corner in 3D will return an array of 8.
        """
        points_to_check = [packing_location]
        # periodicity check
        if self.packing_mode != "graident":
            periodic_pos = self.env.grid.getPositionPeridocity(
                packing_location,
                getNormedVectorOnes(self.max_jitter),
                self.encapsulating_radius,
            )
            points_to_check.extend(periodic_pos)
        return points_to_check

    def jitter_place(
        self,
        env,
        targeted_master_grid_point,
        rot_mat,
        moving,
        distance,
        dpad,
        pt_index,
    ):
        """
        Check if the given grid point is available for packing using the jitter collision detection
        method. Returns packing location and new grid point values if packing is successful.
        """

        packing_location = None
        is_realtime = moving is not None
        level = self.collisionLevel
        for attempt_number in range(self.jitter_attempts):
            insidePoints = {}
            newDistPoints = {}

            (
                packing_location,
                packing_rotation,
            ) = self.get_new_jitter_location_and_rotation(
                env, targeted_master_grid_point, rot_mat
            )

            self.log.info(
                f"Jitter attempt {attempt_number} for {self.name} at {packing_location}"
            )

            if is_realtime:
                self.update_display_rt(moving, packing_location, packing_rotation)
                self.vi.update()

            if not self.point_is_available(packing_location):
                # jittered out of container or too close to boundary
                # check next random jitter
                continue

            collision_results = []
            points_to_check = self.get_all_positions_to_check(packing_location)

            for pt in points_to_check:
                (
                    collision,
                    new_inside_points,
                    new_dist_points,
                ) = self.collision_jitter(
                    pt,
                    packing_rotation,
                    level,
                    env.grid.masterGridPositions,
                    distance,
                    env,
                    dpad,
                )
                collision_results.extend([collision])
                if is_realtime:
                    box = self.vi.getObject("collBox")
                    self.vi.changeObjColorMat(
                        box,
                        [0.5, 0, 0] if True in collision_results else [0, 0.5, 0],
                    )
                    self.update_display_rt(moving, pt, packing_rotation)
                if collision:
                    # found a collision, break this loop
                    break
                else:
                    insidePoints = self.merge_place_results(
                        new_inside_points,
                        insidePoints,
                    )
                    newDistPoints = self.merge_place_results(
                        new_dist_points,
                        newDistPoints,
                    )
            if self.collides_with_compartment(env, packing_location, packing_rotation):
                continue

            if is_realtime:
                box = self.vi.getObject("collBox")
                self.vi.changeObjColorMat(box, [1, 0, 0] if collision else [0, 1, 0])
            if True not in collision_results:
                self.log.info(
                    "no collision, new points %d, %d",
                    len(insidePoints),
                    len(newDistPoints),
                )
                for pt in points_to_check:
                    self.store_packed_object(pt, packing_rotation, pt_index)
                return (
                    True,
                    packing_location,
                    packing_rotation,
                    insidePoints,
                    newDistPoints,
                )
        return False, packing_location, packing_rotation, {}, {}

    def lookForNeighbours(self, env, trans, rotMat, organelle):
        near_by_ingredients, placed_partners = self.get_partners(
            env, trans, rotMat, organelle
        )
        targetPoint = trans
        found = False
        if placed_partners:
            self.log.info("partner found")
            if not self.force_random:
                for jitterPos in range(self.jitter_attempts):  #
                    targetPoint = self.pick_partner_grid_index(
                        near_by_ingredients,
                        placed_partners,
                        current_packing_position=trans,
                    )
                    if targetPoint is not None:
                        break
                if targetPoint is None:
                    found = False
                    return targetPoint, rotMat, found
                else:  # maybe get the ptid that can have it
                    found = True
                    if self.compartment_id > 0:
                        # surface
                        d, i = organelle.OGsrfPtsBht.query(targetPoint)
                        vx, vy, vz = v1 = self.principal_vector
                        # surfacePointsNormals problem here
                        v2 = organelle.ogsurfacePointsNormals[i]
                        try:
                            rotMat = numpy.array(rotVectToVect(v1, v2), "f")
                        except Exception as e:
                            self.log.warning("PROBLEM %s %r", self.name, e)
                            rotMat = numpy.identity(4)
                    # find a newpoint here?
                    return targetPoint, rotMat, found

            else:
                targetPoint = trans
        else:
            self.log.info("no partner found")
        return targetPoint, rotMat, found

    def get_compartment(self, env):
        if self.compartment_id == 0:
            return env
        else:
            return env.compartments[abs(self.compartment_id) - 1]

    def close_partner_check(
        self, env, translation, rotation, compartment, afvi, moving
    ):
        target_point, rot_matrix, found = self.lookForNeighbours(
            env,
            translation,
            rotation,
            compartment,
        )
        if not found and self.counter != 0:
            self.reject()
            return None, None

        # if partner:pickNewPoit like in fill3
        if moving is not None:
            self.update_display_rt(moving, target_point, rot_matrix)
        return target_point, rot_matrix

    def handle_real_time_visualization(self, helper, ptInd, target_point, rot_mat):
        name = self.name
        instance_id = f"{name}-{ptInd}"  # copy of the ingredient being packed
        obj = helper.getObject(name)  # parent object of all the instances
        if obj is None:
            helper.add_object_to_scene(None, self, instance_id, target_point, rot_mat)
        else:
            helper.add_new_instance_and_update_time(
                name, self, instance_id, target_point, rot_mat
            )

        return instance_id

    def spheres_SST_place(
        self,
        env,
        compartment,
        ptInd,
        target_grid_point_position,
        rotation_matrix,
        moving,
        distance,
        dpad,
    ):
        """
        drop the ingredient on grid point ptInd
        """
        is_realtime = moving is not None

        targetPoint = target_grid_point_position

        if is_realtime:
            self.update_display_rt(moving, targetPoint, rotation_matrix)

        # do we get the list of neighbours first > and give a different trans...closer to the partner
        # we should look up for an available ptID around the picked partner if any
        # getListCloseIngredient
        # should se a distance_of_influence ? or self.env.largestProteinSize+self.encapsulating_radius*2.0
        # or the grid diagonal
        # we need to change here in case tilling, the pos,rot ade deduced fromte tilling.
        if self.packing_mode[-4:] == "tile":
            if self.tilling is None:
                self.setTilling(compartment)
            if self.counter != 0:
                # pick the next Hexa pos/rot.
                t, collision_results = self.tilling.getNextHexaPosRot()
                if len(t):
                    rotation_matrix = collision_results
                    targetPoint = t
                    if is_realtime:
                        self.update_display_rt(moving, targetPoint, rotation_matrix)
                else:
                    return False, None, None, {}, {}
            else:
                self.tilling.init_seed(env.seed_used)
        # we may increase the jitter, or pick from xyz->Id free for its radius
        # create the rb only once and not at ever jitter
        # rbnode = histoVol.callFunction(self.env.addRB,(self, jtrans, rotMat,),{"rtype":self.type},)
        # jitter loop
        # level = self.collisionLevel
        for attempt_number in range(self.jitter_attempts):
            insidePoints = {}
            newDistPoints = {}
            env.totnbJitter += 1

            (
                packing_location,
                packing_rotation,
            ) = self.get_new_jitter_location_and_rotation(
                env,
                targetPoint,
                rotation_matrix,
            )
            if is_realtime:
                self.update_display_rt(moving, packing_location, packing_rotation)

            collision_results = []
            rbnode = self.get_rb_model()
            pts_to_check = self.get_all_positions_to_check(packing_location)
            for pt in pts_to_check:
                collision = self.np_check_collision(pt, packing_rotation)
                collision_results.extend([collision])
                if is_realtime:
                    self.update_display_rt(moving, packing_location, packing_rotation)
                if collision:
                    break
            t = time()
            if not self.point_is_available(packing_location):
                continue
            if True in collision_results:
                continue

            # need to check compartment too
            self.log.info("no collision")
            # if self.compareCompartment:
            #     collision = self.compareCompartmentPrimitive(
            #         level,
            #         packing_location,
            #         packing_rotation,
            #         gridPointsCoords,
            #         distance,
            #     )
            #     collision_results.extend([collision])
            if True not in collision_results:
                env.static.append(rbnode)
                env.moving = None

                for pt in pts_to_check:
                    new_inside_pts, new_dist_points = self.pack_at_grid_pt_location(
                        env,
                        pt,
                        packing_rotation,
                        dpad,
                        distance,
                        insidePoints,
                        newDistPoints,
                        ptInd,
                    )
                    insidePoints = self.merge_place_results(
                        new_inside_pts, insidePoints
                    )
                    newDistPoints = self.merge_place_results(
                        new_dist_points, newDistPoints
                    )

                success = True
                return (
                    success,
                    packing_location,
                    packing_rotation,
                    insidePoints,
                    newDistPoints,
                )

        success = False
        return success, packing_location, packing_rotation, insidePoints, newDistPoints

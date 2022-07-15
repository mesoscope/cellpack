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
import os
from scipy import spatial
from panda3d.bullet import BulletRigidBodyNode
import numpy
import logging
import collada
from scipy.spatial.transform import Rotation as R
from math import sqrt, pi
from random import uniform, gauss, random
from time import time
import math

from .utils import (
    ApplyMatrix,
    getNormedVectorOnes,
    rotVectToVect,
    rotax,
)

from cellpack.autopack.upy.simularium.simularium_helper import simulariumHelper
import cellpack.autopack as autopack
from cellpack.autopack.ingredient.agent import Agent

helper = autopack.helper
reporthook = None
if helper is not None:
    reporthook = helper.reporthook


class IngredientInstanceDrop:
    def __init__(self, ptId, position, rotation, ingredient, rb=None):
        self.ptId = ptId
        self.position = position
        self.rotation = rotation
        self.ingredient = ingredient
        self.rigid_body = rb
        self.name = ingredient.name + str(ptId)
        x, y, z = position
        rad = ingredient.encapsulatingRadius
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
        ham here: (-)packingPriority object will pack from high to low one at a time
        (+)packingPriority will be weighted by assigned priority value
        (0)packignPriority will be weighted by complexity and appended to what is left
        of the (+) values
        - an optional principal vector used to align the ingredient
        - recipe will be a weakref to the Recipe this Ingredient belongs to
        - compNum is the compartment number (0 for cytoplasm, positive for compartment
        surface and negative compartment interior
        - Attributes used by the filling algorithm:
        - nbMol counts the number of placed ingredients during a fill
        - counter is the target number of ingredients to place
        - completion is the ratio of placed/target
        - rejectionCounter is used to eliminate ingredients after too many failed
        attempts

    """

    ARGUMENTS = [
        "color",
        "coordsystem",
        "cutoff_boundary",
        "cutoff_surface",
        "distExpression",
        "distFunction",
        "encapsulatingRadius",
        "excluded_partners_name",
        "force_randoom" "isAttractor",
        "jitterMax",
        "meshFile",
        "meshName",
        "meshObject",
        "molarity",
        "name",
        "nbJitter",
        "nbMol",
        "offset",
        "orientBiasRotRangeMax",
        "orientBiasRotRangeMin",
        "overwrite_distFunc",
        "packingMode",
        "packingPriority",
        "partners_name",
        "partners_position",
        "partners_weight",
        "pdb",
        "perturbAxisAmplitude",
        "placeType",
        "positions",
        "positions2",
        "principalVector",
        "proba_binding",
        "proba_not_binding",
        "properties",
        "radii",
        "radius",
        "rejectionThreshold",
        "resolution_dictionary",
        "rotAxis",
        "rotRange",
        "source",
        "sphereFile",
        "Type",
        "useOrientBias",
        "useRotAxis",
        "weight",
    ]

    def __init__(
        self,
        Type="MultiSphere",
        color=None,
        coordsystem="right",
        cutoff_boundary=None,
        cutoff_surface=None,
        distExpression=None,
        distFunction=None,
        encapsulatingRadius=0,
        excluded_partners_name=None,
        force_random=False,  # avoid any binding
        gradient="",
        isAttractor=False,
        jitterMax=(1, 1, 1),
        meshFile=None,
        meshName=None,
        meshObject=None,
        meshType="file",
        molarity=0.0,
        name=None,
        nbJitter=5,
        nbMol=0,
        offset=None,
        orientBiasRotRangeMax=-pi,
        orientBiasRotRangeMin=-pi,
        overwrite_distFunc=True,  # overWrite
        packingMode="random",
        packingPriority=0,
        partners_name=None,
        partners_position=None,
        pdb=None,
        perturbAxisAmplitude=0.1,
        placeType="jitter",
        positions2=None,
        positions=None,
        principalVector=(1, 0, 0),
        proba_binding=0.5,
        proba_not_binding=0.5,  # chance to actually not bind
        properties=None,
        radii=None,
        rejectionThreshold=30,
        resolution_dictionary=None,
        rotAxis=None,
        rotRange=6.2831,
        source=None,
        sphereFile=None,
        useOrientBias=False,
        useRotAxis=False,
        weight=0.2,  # use for affinity ie partner.weight
    ):
        super().__init__(
            name,
            molarity,
            distExpression=distExpression,
            distFunction=distFunction,
            excluded_partners_name=excluded_partners_name,
            force_random=force_random,
            gradient=gradient,
            isAttractor=isAttractor,
            overwrite_distFunc=overwrite_distFunc,
            packingMode=packingMode,
            partners_name=partners_name,
            partners_position=partners_position,
            placeType=placeType,
            proba_binding=proba_binding,
            proba_not_binding=proba_not_binding,
            properties=properties,
            weight=weight,
        )
        self.log = logging.getLogger("ingredient")
        self.log.propagate = False

        self.molarity = molarity
        self.packingPriority = packingPriority
        self.log.info(
            "packingPriority %d,  self.packingPriority %r",
            packingPriority,
            self.packingPriority,
        )
        if name is None:
            name = "%f" % molarity
        self.log.info("CREATE INGREDIENT %s %r", str(name), rejectionThreshold)
        self.name = str(name)
        self.o_name = str(name)
        self.Type = Type
        self.pdb = pdb  # pmv ?
        self.transform_sources = None
        self.source = None
        self.mesh = None
        self.mesh_info = {
            "file": meshFile,
            "name": meshName,
            "type": meshType,
            "object": meshObject,
        }

        self.offset = [0, 0, 0]  # offset to apply for membrane binding
        if offset:
            self.offset = offset

        # should deal with source of the object
        if source:
            sources = source.keys()
            self.source = source
            if "pdb" in sources:
                self.pdb = source["pdb"]
            if "transform" in sources:
                self.transform_sources = source["transform"]
                if "offset" in source["transform"]:
                    self.offset = source["transform"]["offset"]
        else:
            self.source = {
                "pdb": self.pdb,
                "transform": {"center": True, "offset": [0, 0, 0]},
            }
            self.transform_sources = {
                "transform": {"center": True, "offset": [0, 0, 0]}
            }

        self.color = color  # color used for sphere display
        if self.color == "None":
            self.color = None
        self.modelType = "Spheres"
        self.rRot = []
        self.tTrans = []
        self.htrans = []
        self.moving = None
        self.moving_geom = None
        self.rb_nodes = []  # store rbnode. no more than X ?
        self.bullet_nodes = [None, None]  # try only store 2, and move them when needd
        self.limit_nb_nodes = 50
        self.vi = autopack.helper
        self.minRadius = 0
        self.min_distance = 0
        self.encapsulatingRadius = encapsulatingRadius
        self.deepest_level = 1
        self.is_previous = False
        self.vertices = []
        self.faces = []
        self.vnormals = []
        # self._place = self.place
        children = []
        self.sphereFile = sphereFile
        # level 0 should be encapsulated sphere ?
        if sphereFile is not None and str(sphereFile) != "None":
            sphereFileo = autopack.retrieveFile(sphereFile, cache="collisionTrees")
            fileName, fileExtension = os.path.splitext(sphereFile)
            self.log.info("sphereTree %r", sphereFileo)
            if sphereFileo is not None and os.path.isfile(sphereFileo):
                self.sphereFile = sphereFile
                sphereFile = sphereFileo
                if fileExtension == ".mstr":  # BD_BOX format
                    data = numpy.loadtxt(sphereFileo, converters={0: lambda s: 0})
                    positions = data[:, 1:4]
                    radii = data[:, 4]
                    self.minRadius = min(radii)
                    # np.apply_along_axis(np.linalg.norm, 1, c)
                    self.encapsulatingRadius = max(
                        numpy.sqrt(numpy.einsum("ij,ij->i", positions, positions))
                    )  # shoud be max distance
                    self.minRadius = self.encapsulatingRadius
                    positions = [positions]
                    radii = [radii]
                elif fileExtension == ".sph":
                    min_radius, rM, positions, radii, children = self.getSpheres(
                        sphereFileo
                    )
                    # if a user didn't set this properly before
                    if not len(radii):
                        self.minRadius = 1.0
                        self.encapsulatingRadius = 1.0
                    else:
                        # minRadius is used to compute grid spacing. It represents the
                        # smallest radius around the anchor point(i.e.
                        # the point where the
                        # ingredient is dropped that needs to be free
                        self.minRadius = min_radius
                        # encapsulatingRadius is the radius of the sphere
                        # centered at 0,0,0
                        # and encapsulate the ingredient
                        self.encapsulatingRadius = rM
                else:
                    self.log.info(
                        "sphere file extension not recognized %r", fileExtension
                    )
        self.set_sphere_positions(positions, radii)

        self.positions2 = positions2
        self.children = children
        self.rbnode = {}  # keep the rbnode if any
        self.collisionLevel = 0  # self.deepest_level
        # first level used for collision detection
        self.jitterMax = jitterMax
        # (1,1,1) means 1/2 grid spacing in all directions

        self.perturbAxisAmplitude = perturbAxisAmplitude

        self.principalVector = principalVector

        self.recipe = None  # will be set when added to a recipe
        self.compNum = None
        self.compId_accepted = (
            []
        )  # if this list is defined, point picked outise the list are rejected
        # should be self.compNum per default
        # will be set when recipe is added to HistoVol
        # added to a compartment
        self.nbMol = nbMol
        self.left_to_place = nbMol
        self.vol_nbmol = 0

        # Packing tracking values
        self.nbJitter = nbJitter  # number of jitter attempts for translation
        self.nbPts = 0
        self.allIngrPts = (
            []
        )  # the list of available grid points for this ingredient to pack
        self.counter = 0  # target number of molecules for a fill
        self.completion = 0.0  # ratio of counter/nbMol
        self.rejectionCounter = 0
        self.verts = None
        self.rad = None
        self.rapid_model = None
        if self.encapsulatingRadius <= 0.0 or self.encapsulatingRadius < max(
            self.radii[0]
        ):
            self.encapsulatingRadius = max(self.radii[0])  #
        # TODO : geometry : 3d object or procedural from PDB
        # TODO : usekeyword resolution->options dictionary of res :
        # TODO : {"simple":{"cms":{"parameters":{"gridres":12}},
        # TODO :            "obj":{"parameters":{"name":"","filename":""}}
        # TODO :            }
        # TODO : "med":{"method":"cms","parameters":{"gridres":30}}
        # TODO : "high":{"method":"msms","parameters":{"gridres":30}}
        # TODO : etc...
        if coordsystem:
            self.coordsystem = coordsystem
        self.rejectionThreshold = rejectionThreshold

        # need to build the basic shape if one provided
        self.current_resolution = "Low"  # should come from data
        self.available_resolution = ["Low", "Med", "High"]  # 0,1,2

        if resolution_dictionary is None:
            resolution_dictionary = {"Low": "", "Med": "", "High": ""}
        self.resolution_dictionary = resolution_dictionary

        # how to get the geom of different res?
        self.representation = None
        self.representation_file = None

        self.useRotAxis = useRotAxis
        self.rotAxis = rotAxis
        self.rotRange = rotRange
        self.useOrientBias = useOrientBias
        self.orientBiasRotRangeMin = orientBiasRotRangeMin
        self.orientBiasRotRangeMax = orientBiasRotRangeMax

        # cutoff are used for picking point far from surface and boundary
        self.cutoff_boundary = cutoff_boundary
        self.cutoff_surface = float(cutoff_surface or self.encapsulatingRadius)
        if properties is None:
            properties = {}
        self.properties = properties  # four tout

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

    def set_sphere_positions(self, positions, radii):
        # positions and radii are passed to the constructor
        # check the format old nested array, new array of dictionary
        nLOD = 0
        if positions is not None:
            nLOD = len(positions)

        self.positions = []
        self.radii = []
        if positions is not None and isinstance(positions[0], dict):
            for i in range(nLOD):
                c = numpy.array(positions[i]["coords"])
                n = int(len(c) / 3)
                self.positions.append(c.reshape((n, 3)).tolist())
                self.radii.append(radii[i]["radii"])
            if len(self.radii) == 0:
                self.radii = [[10]]  # some default value ?
                self.positions = [[[0, 0, 0]]]
            self.deepest_level = len(radii) - 1
        else:  # regular nested
            if (
                positions is None or positions[0] is None or positions[0][0] is None
            ):  # [0][0]
                positions = [[[0, 0, 0]]]

            else:
                if radii is not None:
                    delta = numpy.array(positions[0])
                    rM = sqrt(max(numpy.sum(delta * delta, 1)))
                    self.encapsulatingRadius = max(rM, self.encapsulatingRadius)
            # if radii is not None and positions is not None:
            # for r, c in zip(radii, positions):
            #     assert len(r) == len(c)
            if radii is not None:
                self.deepest_level = len(radii) - 1
            if radii is None:
                radii = [[0]]
            self.radii = radii
            self.positions = positions
        if self.minRadius == 0:
            self.minRadius = min(min(self.radii))

    def reset(self):
        """reset the states of an ingredient"""
        self.counter = 0
        self.left_to_place = 0.0
        self.completion = 0.0

    def setTilling(self, comp):
        if self.packingMode == "hexatile":
            from cellpack.autopack.hexagonTile import tileHexaIngredient

            self.tilling = tileHexaIngredient(
                self, comp, self.encapsulatingRadius, init_seed=self.env.seed_used
            )
        elif self.packingMode == "squaretile":
            from cellpack.autopack.hexagonTile import tileSquareIngredient

            self.tilling = tileSquareIngredient(
                self, comp, self.encapsulatingRadius, init_seed=self.env.seed_used
            )
        elif self.packingMode == "triangletile":
            from cellpack.autopack.hexagonTile import tileTriangleIngredient

            self.tilling = tileTriangleIngredient(
                self, comp, self.encapsulatingRadius, init_seed=self.env.seed_used
            )

    def initialize_mesh(self, mesh_store):
        # get the collision mesh
        meshFile = self.mesh_info["file"]
        meshName = self.mesh_info["name"]
        meshObject = self.mesh_info["object"]
        meshType = self.mesh_info["type"]
        self.mesh = None
        if meshFile is not None:
            if meshType == "file":
                self.mesh = self.getMesh(meshFile, meshName)  # self.name)
                self.log.info("OK got", self.mesh)
                if self.mesh is None:
                    # display a message ?
                    self.log.warning("no geometries for ingredient " + self.name)
                # should we reparent it ?
            elif meshType == "raw":
                # need to build the mesh from v,f,n
                self.buildMesh(mesh_store)
        elif meshObject is not None:
            self.mesh = meshObject

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

    def getSpheres(self, sphereFile):
        """
        get spherical approximation of shape
        """
        # file format is space separated
        # float:Rmin float:Rmax
        # int:number of levels
        # int: number of spheres in first level
        # x y z r i j k ...# first sphere in first level and 0-based indices
        # of spheres in next level covererd by this sphere
        # ...
        # int: number of spheres in second level
        f = open(sphereFile)
        datao = f.readlines()
        f.close()

        # strip comments
        data = [x for x in datao if x[0] != "#" and len(x) > 1 and x[0] != "\r"]

        rmin, rmax = list(map(float, data[0].split()))
        nblevels = int(data[1])
        radii = []
        centers = []
        children = []
        line = 2
        for level in range(nblevels):
            rl = []
            cl = []
            ch = []
            nbs = int(data[line])
            line += 1
            for n in range(nbs):
                w = data[line].split()
                x, y, z, r = list(map(float, w[:4]))
                if level < nblevels - 1:  # get sub spheres indices
                    ch.append(list(map(int, w[4:])))
                cl.append((x, y, z))
                rl.append(r)
                line += 1
            centers.append(cl)
            radii.append(rl)
            children.append(ch)
        # we ignore the hierarchy for now
        return rmin, rmax, centers, radii, children

    def rejectOnce(self, rbnode, moving, afvi):
        if rbnode:
            self.env.callFunction(self.env.delRB, (rbnode,))
        if afvi is not None and moving is not None:
            afvi.vi.deleteObject(moving)
        self.haveBeenRejected = True
        self.rejectionCounter += 1
        if (
            self.rejectionCounter >= self.rejectionThreshold
        ):  # Graham set this to 6000 for figure 13b (Results Fig 3 Test1) otherwise it fails to fill small guys
            self.log.info("PREMATURE ENDING of ingredient rejectOnce", self.name)
            self.completion = 1.0

    def addRBsegment(self, pt1, pt2):
        # ovewrite by grow ingredient
        pass

    def add_rb_mesh(self, worldNP):
        inodenp = worldNP.attachNewNode(BulletRigidBodyNode(self.name))
        inodenp.node().setMass(1.0)
        if self.mesh is None:
            return
        self.getData()
        if not len(self.vertices):
            return inodenp
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
        [vertexWriter.addData3f(v[0], v[1], v[2]) for v in self.vertices]

        # step 2) make primitives and assign vertices to them
        tris = GeomTriangles(Geom.UHStatic)
        [self.setGeomFaces(tris, face) for face in self.faces]

        # step 3) make a Geom object to hold the primitives
        geom = Geom(vdata)
        geom.addPrimitive(tris)
        # step 4) create the bullet mesh and node
        #        if ingr.convex_hull:
        #            shape = BulletConvexHullShape()
        #            shape.add_geom(geom)
        #        else :
        mesh = BulletTriangleMesh()
        mesh.addGeom(geom)
        shape = BulletTriangleMeshShape(mesh, dynamic=False)  # BulletConvexHullShape
        print("shape ok", shape)
        # inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode(ingr.name))
        # inodenp.node().setMass(1.0)
        inodenp.node().addShape(
            shape
        )  # ,TransformState.makePos(Point3(0, 0, 0)))#, pMat)#TransformState.makePos(Point3(jtrans[0],jtrans[1],jtrans[2])))#rotation ?
        return inodenp

    def SetKw(self, **kw):
        for k in kw:
            setattr(self, k, kw[k])

    def Set(self, **kw):
        self.nbMol = 0
        if "nbMol" in kw:
            self.nbMol = int(kw["nbMol"])
        if "molarity" in kw:
            self.molarity = kw["molarity"]
        if "priority" in kw:
            self.packingPriority = kw["priority"]
        if "packingMode" in kw:
            self.packingMode = kw["packingMode"]
        if "compMask" in kw:
            if type(kw["compMask"]) is str:
                self.compMask = eval(kw["compMask"])
            else:
                self.compMask = kw["compMask"]

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
            self.log.info("self.encapsulatingRadius %r %r", self.encapsulatingRadius, r)
            self.encapsulatingRadius = r
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
                self, [0.0, 0.0, 0.0], numpy.identity(4), rtype=self.Type
            )
        return self.bullet_nodes[ret]

    def getMesh(self, filename, geomname, mesh_store):
        """
        Create a mesh representation from a filename for the ingredient

        @type  filename: string
        @param filename: the name of the input file
        @type  geomname: string
        @param geomname: the name of the ouput geometry

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
                #                    oldv = self.principalVector[:]
                #                    self.principalVector = [oldv[2],oldv[1],oldv[0]]
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
        this will jitter gauss(0., 0.3) * Ingredient.jitterMax
        """
        if self.compNum > 0:
            vx, vy, vz = v1 = self.principalVector
            # surfacePointsNormals problem here
            v2 = normal
            try:
                rotMat = numpy.array(rotVectToVect(v1, v2), "f")
            except Exception as e:
                self.log.error(e)
                rotMat = numpy.identity(4)

        jx, jy, jz = self.jitterMax
        dx = (
            jx * spacing * uniform(-1.0, 1.0)
        )  # This needs to use the same rejection if outside of the sphere that the uniform cartesian jitters have.  Shoiuld use oneJitter instead?
        dy = jy * spacing * uniform(-1.0, 1.0)
        dz = jz * spacing * uniform(-1.0, 1.0)
        #        d2 = dx*dx + dy*dy + dz*dz
        #        if d2 < jitter2:
        if self.compNum > 0:  # jitter less among normal
            dx, dy, dz, dum = numpy.dot(rotMat, (dx, dy, dz, 0))
        position[0] += dx
        position[1] += dy
        position[2] += dz
        return numpy.array(position)

    def getMaxJitter(self, spacing):
        # self.jitterMax: each value is the max it can move
        # along that axis, but not cocurrently, ie, can't move
        # in the max x AND max y direction at the same time
        return max(self.jitterMax) * spacing

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
        radius = self.minRadius
        jitter = self.getMaxJitter(spacing)

        if self.packingMode == "close":
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
        current_comp_id = self.compNum
        # gets min distance an object has to be away to allow packing for this object
        cuttoff = self.get_cuttoff_value(spacing)
        if self.packingMode == "close":
            # Get an array of free points where the distance is greater than half the cuttoff value
            # and less than the cutoff. Ie an array where the distances are all very small.
            # this also masks the array to only include points in the current commpartment
            all_distances = numpy.array(distances)[free_points]
            mask = numpy.logical_and(
                numpy.less_equal(all_distances, cuttoff),
                numpy.greater_equal(all_distances, cuttoff / 2.0),
            )
            # mask compartments Id as well
            mask_comp = numpy.array(comp_ids)[free_points] == current_comp_id
            mask_ind = numpy.nonzero(numpy.logical_and(mask, mask_comp))[0]
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
        x, y, z = self.principalVector
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

    def alignRotation(self, jtrans):
        # for surface points we compute the rotation which
        # aligns the principalVector with the surface normal
        vx, vy, vz = v1 = self.principalVector
        # surfacePointsNormals problem here
        gradient_center = self.env.gradients[self.gradient].direction
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
        rot aligns the principalVector with the surface normal
        rot aligns the principalVector with the biased diretion
        """
        if self.perturbAxisAmplitude != 0.0:
            axis = self.perturbAxis(self.perturbAxisAmplitude)
        else:
            axis = self.principalVector
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
        rrot = rotax((0, 0, 0), self.rotAxis, tau, transpose=1)
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

    def checkDistSurface(self, point, cutoff):
        if not hasattr(self, "histoVol"):
            return False
        if self.compNum == 0:
            compartment = self.env
        else:
            compartment = self.env.compartments[abs(self.compNum) - 1]
        compNum = self.compNum
        if compNum < 0:
            sfpts = compartment.surfacePointsCoords
            delta = numpy.array(sfpts) - numpy.array(point)
            delta *= delta
            distA = numpy.sqrt(delta.sum(1))
            test = distA < cutoff
            if True in test:
                return True
        elif compNum == 0:
            for o in self.env.compartments:
                sfpts = o.surfacePointsCoords
                delta = numpy.array(sfpts) - numpy.array(point)
                delta *= delta
                distA = numpy.sqrt(delta.sum(1))
                test = distA < cutoff
                if True in test:
                    return True
        return False

    def getListCompFromMask(self, cId, ptsInSphere):
        # cID ie [-2,-1,-2,0...], ptsinsph = [519,300,etc]
        current = self.compNum
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

    def isInGoodComp(self, pId, nbs=None):
        # cID ie [-2,-1,-2,0...], ptsinsph = [519,300,etc]
        current = self.compNum
        cId = self.env.grid.compartment_ids[pId]
        if current <= 0:  # inside
            if current != cId:
                return False
            return True
        if current > 0:  # surface
            if current != cId and -current != cId:
                return False
            return True
        return False

    def compareCompartmentPrimitive(
        self, level, jtrans, rotMatj, gridPointsCoords, distance
    ):
        collisionComp = self.collides_with_compartment(
            jtrans, rotMatj, level, gridPointsCoords, self.env
        )

        return collisionComp

    def checkCompartment(self, ptsInSphere, nbs=None):
        trigger = False
        if self.compareCompartment:
            cId = numpy.take(
                self.env.grid.compartment_ids, ptsInSphere, 0
            )  # shoud be the same ?
            if nbs is not None:
                if self.compNum <= 0 and nbs != 0:
                    return trigger, True
            L = self.getListCompFromMask(cId, ptsInSphere)

            if len(cId) <= 1:
                return trigger, True
            p = float(len(L)) / float(
                len(cId)
            )  # ratio accepted compId / totalCompId-> want 1.0
            if p < self.compareCompartmentTolerance:
                trigger = True
                return trigger, True
            # threshold
            if (
                self.compareCompartmentThreshold != 0.0
                and p < self.compareCompartmentThreshold
            ):
                return trigger, True
                # reject the ingr
        return trigger, False

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

    def collision_jitter(
        self,
        jtrans,
        rotMat,
        level,
        gridPointsCoords,
        current_grid_distances,
        env,
        dpad,
    ):
        """
        Check spheres for collision
        """
        centers = self.positions[level]
        radii = self.radii[level]
        # should we also check for outside the main grid ?
        # wouldnt be faster to do sphere-sphere distance test ? than points/points from the grid
        centT = self.transformPoints(jtrans, rotMat, centers)  # centers)
        # sphNum = 0  # which sphere in the sphere tree we're checking
        # self.distances_temp = []
        insidePoints = {}
        newDistPoints = {}
        at_max_level = level == self.deepest_level and (level + 1) == len(
            self.positions
        )
        for radius_of_ing_being_packed, posc in zip(radii, centT):
            x, y, z = posc
            radius_of_area_to_check = (
                radius_of_ing_being_packed + dpad
            )  # extends the packing ingredient's bounding box to be large enough to include masked gridpoints of the largest possible ingrdient in the receipe
            #  TODO: add realtime render here that shows all the points being checked by the collision

            pointsToCheck = env.grid.getPointsInSphere(
                posc, radius_of_area_to_check
            )  # indices
            # check for collisions by looking at grid points in the sphere of radius radc
            delta = numpy.take(gridPointsCoords, pointsToCheck, 0) - posc
            delta *= delta
            distA = numpy.sqrt(delta.sum(1))

            for pti in range(len(pointsToCheck)):
                grid_point_index = pointsToCheck[
                    pti
                ]  # index of master grid point that is inside the sphere
                distance_to_packing_location = distA[
                    pti
                ]  # is that point's distance from the center of the sphere (packing location)
                # distance is an array of distance of closest contact to anything currently in the grid
                collision = (
                    current_grid_distances[grid_point_index]
                    + distance_to_packing_location
                    <= radius_of_ing_being_packed
                )

                if collision:
                    # an object is too close to the sphere at this level
                    if not at_max_level:
                        # if we haven't made it all the way down the sphere tree,
                        # check a level down
                        new_level = level + 1
                        # NOTE: currently with sphere trees, no children seem present
                        # get sphere that are children of this one
                        # ccenters = []
                        # cradii = []
                        # for sphInd in self.children[level][sphNum]:
                        #     ccenters.append(nxtLevelSpheres[sphInd])
                        #     cradii.append(nxtLevelRadii[sphInd])
                        return self.collision_jitter(
                            jtrans,
                            rotMat,
                            new_level,
                            gridPointsCoords,
                            current_grid_distances,
                            env,
                            dpad,
                        )
                    else:
                        self.log.info(
                            "grid point already occupied %f",
                            current_grid_distances[grid_point_index],
                        )
                        return True, {}, {}
                if not at_max_level:
                    # we don't want to calculate new distances if we are not
                    # at the highest geo
                    # but getting here means there was no collision detected
                    # so the loop can continue
                    continue
                signed_distance_to_sphere_surface = (
                    distance_to_packing_location - radius_of_ing_being_packed
                )

                (
                    insidePoints,
                    newDistPoints,
                ) = self.get_new_distances_and_inside_points(
                    env,
                    jtrans,
                    rotMat,
                    grid_point_index,
                    current_grid_distances,
                    newDistPoints,
                    insidePoints,
                    signed_distance_to_sphere_surface,
                )

            if not at_max_level:
                # we didn't find any colisions with the this level, but we still want
                # the inside points to be based on the most detailed geom
                new_level = self.deepest_level
                return self.collision_jitter(
                    jtrans,
                    rotMat,
                    new_level,
                    gridPointsCoords,
                    current_grid_distances,
                    env,
                    dpad,
                )
        return False, insidePoints, newDistPoints

    def checkPointComp(self, point):
        # if grid too sparse this will not work.
        # ptID = self.env.grid.getPointFrom3D(point)
        cID = self.env.getPointCompartmentId(point)  # offset ?
        # dist,ptID = self.env.grid.getClosestGridPoint(point)
        if self.compNum == 0:
            organelle = self.env
        else:
            organelle = self.env.compartments[abs(self.compNum) - 1]
        if self.compNum > 0:  # surface ingredient
            if self.Type == "Grow":
                # need a list of accepted compNum
                check = False
                if len(self.compMask):
                    if cID not in self.compMask:
                        check = False
                    else:
                        check = True
                else:
                    check = True
                # if cID > 0 : #surface point look at surface cutoff
                #                    if dist < self.cutoff_surface :
                #                        check = False
                #                    else :
                #                        check = True #grid probably too sparse, need to check where we are
                return check
            return True
        # for i,o in self.env.compartments:
        #        if self.compNum != cID:
        #            return False
        #        else :
        #            return True
        if self.compNum < 0:
            inside = organelle.checkPointInside(
                point, self.env.grid.diag, self.env.mesh_store, ray=3
            )
            if inside:  # and cID < 0:
                return True
            else:
                return False
                #            if inside and self.compNum >=0 :
                #                return False
                #            if not inside and self.compNum < 0 :
                #                return False
        if self.compNum == 0:  # shouldnt be in any compartments
            for o in self.env.compartments:
                inside = o.checkPointInside(
                    point, self.env.grid.diag, self.env.mesh_store, ray=3
                )
                if inside:
                    return False
        if self.compNum != cID:
            return False
        else:
            return True

    def checkPointSurface(self, point, cutoff):
        if not hasattr(self, "histoVol"):
            return False
        if self.compNum == 0:
            compartment = self.env
        else:
            compartment = self.env.compartments[abs(self.compNum) - 1]
        compNum = self.compNum
        for o in self.env.compartments:
            if self.compNum > 0 and o.name == compartment.name:
                continue
            self.log.info("test compartment %s %r", o.name, o.OGsrfPtsBht)
            res = o.OGsrfPtsBht.query(tuple(numpy.array([point])))
            if len(res) == 2:
                d = res[0][0]
                # pt=res[1][0]
                self.log.info(
                    "distance is %r %r", d, cutoff
                )  # d can be wrond for some reason,
                if d < cutoff:
                    return True
                if compNum < 0 and o.name == compartment.name:
                    inside = o.checkPointInside(
                        numpy.array(point), self.env.grid.diag, self.env.mesh_store
                    )
                    self.log.info("inside ? %r", inside)
                    if not inside:
                        return True
        return False

    def point_is_not_available(self, newPt):
        """Takes in a vector returns a boolean"""
        inComp = True
        closeS = False
        inside = self.env.grid.checkPointInside(
            newPt, dist=self.cutoff_boundary, jitter=getNormedVectorOnes(self.jitterMax)
        )
        if inside:
            inComp = self.checkPointComp(newPt)
            if inComp:
                # check how far from surface ?
                closeS = self.checkPointSurface(newPt, cutoff=self.cutoff_surface)
        return not inside or closeS or not inComp

    def oneJitter(self, env, trans, rotMat):
        jtrans = self.randomize_translation(env, trans, rotMat)
        rotMatj = self.randomize_rotation(rotMat, env)
        return jtrans, rotMatj

    def get_new_jitter_location_and_rotation(
        self, env, starting_pos, starting_rotation
    ):
        if self.packingMode[-4:] == "tile":
            packing_location = starting_pos
            packing_rotation = starting_rotation[:]
            return packing_location, packing_rotation

        return self.oneJitter(env, starting_pos, starting_rotation)

    def getInsidePoints(
        self,
        grid,
        gridPointsCoords,
        dpad,
        distance,
        centT=None,
        jtrans=None,
        rotMatj=None,
    ):
        return self.get_new_distance_values(
            jtrans, rotMatj, gridPointsCoords, distance, dpad
        )
        # return self.get_new_distance_values(
        #    grid, gridPointsCoords, dpad, distance, centT, jtrans, rotMatj, dpad
        # )

    def getIngredientsInBox(self, histoVol, jtrans, rotMat, compartment, afvi):
        if histoVol.windowsSize_overwrite:
            rad = histoVol.windowsSize
        else:
            #            rad = self.minRadius*2.0# + histoVol.largestProteinSize + \
            # histoVol.smallestProteinSize + histoVol.windowsSize
            rad = (
                self.minRadius
                + histoVol.largestProteinSize
                + histoVol.smallestProteinSize
                + histoVol.windowsSize
            )
        x, y, z = jtrans
        bb = ([x - rad, y - rad, z - rad], [x + rad, y + rad, z + rad])
        if self.modelType == "Cylinders":
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
        if histoVol.runTimeDisplay > 1:
            box = self.vi.getObject("partBox")
            if box is None:
                box = self.vi.Box("partBox", cornerPoints=bb, visible=1)
            else:
                self.vi.toggleDisplay(box, True)
                self.vi.updateBox(box, cornerPoints=bb)
                self.vi.update()
                #            sleep(1.0)
        pointsInCube = histoVol.grid.getPointsInCube(bb, jtrans, rad)
        # should we got all ingre from all recipes?
        # can use the kdtree for it...
        # maybe just add the surface if its not already the surface
        mingrs = [m for m in compartment.molecules if m[3] in pointsInCube]
        return mingrs

    def getIngredientsInTree(self, close_indice):
        if len(self.env.rIngr):
            ingrs = [self.env.rIngr[i] for i in close_indice["indices"]]
            return [
                numpy.array(self.env.rTrans)[close_indice["indices"]],
                numpy.array(self.env.rRot)[close_indice["indices"]],
                ingrs,
                close_indice["distances"],
            ]
        else:
            return []

    def getListePartners(
        self, histoVol, jtrans, rotMat, organelle, afvi, close_indice=None
    ):
        if close_indice is None:
            mingrs = self.getIngredientsInBox(histoVol, jtrans, rotMat, organelle, afvi)
        else:
            # mingrs = zip(*mingrs)
            mingrs = self.getIngredientsInTree(close_indice)
        listePartner = []
        if not len(mingrs) or not len(mingrs[2]):
            self.log.info("no close ingredient found")
            return [], []
        else:
            self.log.info("nb close ingredient %s", self.name)
        listePartner = []
        for i in range(len(mingrs[2])):
            ing = mingrs[2][i]
            t = mingrs[0][i]
            if self.packingMode == "closePartner":
                if ing.o_name in self.partners_name or ing.name in self.partners_name:
                    listePartner.append([i, self.partners[ing.name], mingrs[3][i]])
                    #                                         autopack.helper.measure_distance(jtrans,mingrs[0][i])])
            if (
                ing.isAttractor
            ):  # and self.compNum <= 0: #always attract! or rol a dice ?sself.excluded_partners.has_key(name)
                if (
                    ing.name not in self.partners_name
                    and self.name not in ing.excluded_partners_name
                    and ing.name not in self.excluded_partners_name
                ):
                    self.log.info("shoul attract %s" + self.name)
                    part = self.getPartner(ing.name)
                    if part is None:
                        part = self.addPartner(ing, weight=ing.weight)
                    if ing.distExpression is not None:
                        part.distExpression = ing.distExpression
                    d = afvi.vi.measure_distance(jtrans, t)
                    listePartner.append([i, part, d])
        if not listePartner:
            self.log.info("no partner found in close ingredient %s", self.packingMode)
            return [], []
        else:
            return mingrs, listePartner

    def getTransform(self):
        tTrans = self.vi.ToVec(self.vi.getTranslation(self.moving))
        self.htrans.append(tTrans)
        avg = numpy.average(numpy.array(self.htrans))
        d = self.vi.measure_distance(tTrans, avg)
        if d < 5.0:
            return True
        else:
            return False

    def get_new_pos(self, ingr, pos, rot, positions_to_adjust):
        """
        Takes positions_to_adjust, such as an array of spheres at a level in a
        sphere tree, and adjusts them relative to the given position and rotation
        """
        if positions_to_adjust is None:
            positions_to_adjust = ingr.positions[0]
        return self.transformPoints(pos, rot, positions_to_adjust)

    def check_against_one_packed_ingr(self, index, level, search_tree):
        overlapped_ingr = self.env.rIngr[index]
        positions_of_packed_ingr_spheres = self.get_new_pos(
            self.env.rIngr[index],
            self.env.rTrans[index],
            self.env.rRot[index],
            overlapped_ingr.positions[level],
        )
        # check distances between the spheres at this level in the ingr we are packing
        # to the spheres at this level in the ingr already placed
        # return the number of distances for the spheres we are trying to place
        dist_from_packed_spheres_to_new_spheres, ind = search_tree.query(
            positions_of_packed_ingr_spheres, len(self.positions[level])
        )
        # return index of sph1 closest to pos of packed ingr
        cradii = numpy.array(self.radii[level])[ind]
        oradii = numpy.array(self.env.rIngr[index].radii[level])
        sumradii = numpy.add(cradii.transpose(), oradii).transpose()
        sD = dist_from_packed_spheres_to_new_spheres - sumradii
        return len(numpy.nonzero(sD < 0.0)[0]) != 0

    def np_check_collision(self, packing_location, rotation):
        has_collision = False
        # no ingredients packed yet
        if not len(self.env.rTrans):
            return has_collision
        else:
            if self.env.close_ingr_bhtree is None:
                self.env.close_ingr_bhtree = spatial.cKDTree(
                    self.env.rTrans, leafsize=10
                )
        # starting at level 0, check encapsulating radii
        level = 0
        total_levels = len(self.positions)
        (
            distances_from_packing_location_to_all_ingr,
            ingr_indexes,
        ) = self.env.close_ingr_bhtree.query(packing_location, len(self.env.rTrans))
        radii_of_placed_ingr = numpy.array(
            [ing.encapsulatingRadius for ing in self.env.rIngr]
        )[ingr_indexes]
        overlap_distance = distances_from_packing_location_to_all_ingr - (
            self.encapsulatingRadius + radii_of_placed_ingr
        )
        # if overlap_distance is negative, the encapsualting radii are overlapping
        overlap_indexes = numpy.nonzero(overlap_distance < 0.0)[0]

        if len(overlap_indexes) != 0:
            level = level + 1
            # single sphere ingr will exit here.
            if level == total_levels:
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

        # the compartment the ingr belongs to
        if self.compNum == 0:
            current_ingr_compartment = self.env
        else:
            # NOTE: env.compartments only includes compartments >=1, ie not the
            # bounding box/comp==0. So need to subtrack 1 from the id of the compartment
            # to index into this list.
            current_ingr_compartment = self.env.compartments[abs(self.compNum) - 1]
        for compartment in self.env.compartments:
            if current_ingr_compartment.name == compartment.name:
                continue
            distances, ingr_indexes = compartment.OGsrfPtsBht.query(packing_location)

            # NOTE: this could be optimized by walking down the sphere tree representation
            # of the instead of going right to the bottom
            if distances < self.encapsulatingRadius + compartment.encapsulatingRadius:
                pos_of_attempting_ingr = self.get_new_pos(
                    self, packing_location, rotation, self.positions[total_levels - 1]
                )
                distances, ingr_indexes = compartment.OGsrfPtsBht.query(
                    pos_of_attempting_ingr
                )

                radii = self.radii[total_levels - 1][ingr_indexes]
                overlap_distance = distances - numpy.array(radii)
                overlap_indexes = numpy.nonzero(overlap_distance < 0.0)[0]
                if len(overlap_indexes) != 0:
                    return True
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
        if self.compNum == 0:
            organelle = self.env
        else:
            organelle = self.env.compartments[abs(self.compNum) - 1]
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
                    > (ingr.encapsulatingRadius + self.encapsulatingRadius)
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
            if self.Type == "Grow":
                if self.name == ingr.name:
                    c = len(self.env.rIngr)
                    if (n == c) or n == (c - 1):  # or  (n==(c-2)):
                        continue
            if ingr.name in self.partners and self.Type == "Grow":
                c = len(self.env.rIngr)
                if (n == c) or n == (c - 1):  # or (n==c-2):
                    continue
            if self.name in ingr.partners and ingr.Type == "Grow":
                c = len(self.env.rIngr)
                if (n == c) or n == (c - 1):  # or (n==c-2):
                    continue
                    #            if self.packingMode == 'hexatile' :
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
            if self.compNum > 0 and o.name == organelle.name:
                # this i notworking for growing ingredient like hair.
                # should had after second segments
                if self.Type != "Grow":
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
                    if d < self.encapsulatingRadius:
                        if not getInfo:
                            nodes.append(orbnode)
                        else:
                            nodes.append([orbnode, [0, 0, 0], numpy.identity(4), o])
                            #        if self.compNum < 0 or self.compNum == 0 :
                            #            for o in self.env.compartments:
                            #                if o.rbnode is not None :
                            #                    if not getInfo :
                            #                        nodes.append(o.rbnode)
        self.env.nodes = nodes
        return nodes

    def getClosePairIngredient(self, point, histoVol, cutoff=10.0):
        R = {"indices": [], "distances": []}
        radius = [ingr.encapsulatingRadius for ingr in self.env.rIngr]
        radius.append(self.encapsulatingRadius)
        pos = self.env.rTrans[:]  # ).tolist()
        pos.append([point[0], point[1], point[2]])
        ind = len(pos) - 1
        bht = spatial.cKDTree(pos, leafsize=10)
        # find all pairs for which the distance is less than 1.1
        # times the sum of the radii
        pairs = bht.query_ball_point(pos, radius)
        for p in pairs:
            if p[0] == ind:
                R["indices"].append(p[1])
            elif p[1] == ind:
                R["indices"].append(p[0])
        print("getClosePairIngredient ", R)
        print("all pairs ", pairs)
        print("query was ind ", ind)
        return R

    def getClosestIngredient(self, point, histoVol, cutoff=10.0):
        # may have to rebuild the whale tree every time we add a point
        # grab the current result
        # set the bhtree
        # get closest ClosePoints()
        #        raw_input()
        #        return self.getClosePairIngredient(point,histoVol,cutoff=cutoff)
        R = {"indices": [], "distances": []}
        numpy.zeros(histoVol.totalNbIngr).astype("i")
        nb = 0
        self.log.info(
            "treemode %s, len rTrans=%d", histoVol.treemode, len(histoVol.rTrans)
        )
        if not len(histoVol.rTrans):
            return R
        # else:
        #     if histoVol.treemode == "bhtree":
        #         if histoVol.close_ingr_bhtree is None:
        #             histoVol.close_ingr_bhtree = bhtreelib.BHtree(
        #                 histoVol.rTrans,
        #                 [ing.encapsulatingRadius for ing in histoVol.rIngr],
        #                 10,
        #             )
        if histoVol.close_ingr_bhtree is not None:
            # request kdtree
            nb = []
            self.log.info("finding partners")
            if len(histoVol.rTrans) >= 1:
                #                    nb = histoVol.close_ingr_bhtree.query_ball_point(point,cutoff)
                #                else :#use the general query, how many we want
                distance, nb = histoVol.close_ingr_bhtree.query(
                    point, len(histoVol.rTrans), distance_upper_bound=cutoff
                )  # len of ingr posed so far
                if len(histoVol.rTrans) == 1:
                    distance = [distance]
                    nb = [nb]
                R["indices"] = nb
                R["distances"] = distance  # sorted by distance short -> long
            return R
        else:
            return R
            #        closest = histoVol.close_ingr_bhtree.closestPointsArray(tuple(numpy.array([point,])), cutoff, 0)#returnNullIfFail
            #        print ("getClosestIngredient",closest,cutoff )
            #        return closest

    def update_data_tree(
        self, jtrans, rotMatj, ptInd=0, pt1=None, pt2=None, updateTree=True
    ):
        # self.env.static.append(rbnode)
        # self.env.moving = None
        self.env.nb_ingredient += 1
        self.env.rTrans.append(numpy.array(jtrans).flatten().tolist())
        self.env.rRot.append(numpy.array(rotMatj))  # rotMatj
        self.env.rIngr.append(self)
        if pt1 is not None:
            self.env.result.append(
                [
                    [
                        numpy.array(pt1).flatten().tolist(),
                        numpy.array(pt2).flatten().tolist(),
                    ],
                    rotMatj.tolist(),
                    self,
                    ptInd,
                ]
            )
        else:
            self.env.result.append(
                [
                    numpy.array(jtrans).flatten().tolist(),
                    numpy.array(rotMatj),
                    self,
                    ptInd,
                ]
            )
        if updateTree:
            if len(self.env.rTrans) >= 1:
                self.env.close_ingr_bhtree = spatial.cKDTree(
                    self.env.rTrans, leafsize=10
                )

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
            self.rejectionCounter >= self.rejectionThreshold
        ):  # Graham set this to 6000 for figure 13b (Results Fig 3 Test1) otehrwise it fails to fill small guys
            self.log.info("PREMATURE ENDING of ingredient %s", self.name)
            self.completion = 1.0

    def place(
        self,
        env,
        compartment,
        dropped_position,
        dropped_rotation,
        grid_point_index,
        new_inside_points,
        new_dist_values,
    ):
        self.nbPts = self.nbPts + len(new_inside_points)
        # self.update_distances(new_inside_points, new_dist_values)
        compartment.molecules.append(
            [dropped_position, dropped_rotation, self, grid_point_index]
        )
        env.order[grid_point_index] = env.lastrank
        env.lastrank += 1
        env.nb_ingredient += 1

        if self.packingMode[-4:] == "tile":
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
        self.update_data_tree(dropped_position, dropped_rotation, grid_point_index)

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
        dpad = self.minRadius + max_radius + jitter
        self.vi = autopack.helper
        self.env = env  # NOTE: do we need to store the env on the ingredient?
        self.log.info(
            "PLACING INGREDIENT %s, placeType=%s, index=%d, position=%r",
            self.name,
            self.placeType,
            ptInd,
            env.grid.masterGridPositions[ptInd],
        )
        compartment = self.get_compartment(env)
        gridPointsCoords = env.masterGridPositions
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
        if env.ingrLookForNeighbours and self.packingMode == "closePartner":
            target_grid_point_position, rotation_matrix = self.close_partner_check(
                target_grid_point_position,
                rotation_matrix,
                compartment,
                env.afviewer,
                current_visual_instance,
            )
        is_fiber = self.Type == "Grow" or self.Type == "Actine"
        if collision_possible or is_fiber:
            # grow doesnt use panda.......but could use all the geom produce by the grow as rb
            if is_fiber:
                success, jtrans, rotMatj, insidePoints, newDistPoints = self.grow_place(
                    env,
                    ptInd,
                    env.grid.freePoints,
                    env.grid.nbFreePoints,
                    grid_point_distances,
                    dpad,
                )
            elif self.placeType == "jitter":
                (
                    success,
                    jtrans,
                    rotMatj,
                    insidePoints,
                    newDistPoints,
                ) = self.jitter_place(
                    env,
                    compartment,
                    target_grid_point_position,
                    rotation_matrix,
                    current_visual_instance,
                    grid_point_distances,
                    dpad,
                    env.afviewer,
                )
            elif self.placeType == "spheresSST":
                (
                    success,
                    jtrans,
                    rotMatj,
                    insidePoints,
                    newDistPoints,
                ) = self.pandaBullet_placeBHT(
                    env,
                    compartment,
                    ptInd,
                    target_grid_point_position,
                    rotation_matrix,
                    current_visual_instance,
                    grid_point_distances,
                    dpad,
                )
            elif self.placeType == "pandaBullet":
                (
                    success,
                    jtrans,
                    rotMatj,
                    insidePoints,
                    newDistPoints,
                ) = self.pandaBullet_place(
                    env,
                    ptInd,
                    grid_point_distances,
                    dpad,
                    env.afviewer,
                    compartment,
                    gridPointsCoords,
                    rotation_matrix,
                    target_grid_point_position,
                    current_visual_instance,
                    usePP=usePP,
                )
            elif (
                self.placeType == "pandaBulletRelax"
                or self.placeType == "pandaBulletSpring"
            ):
                (
                    success,
                    jtrans,
                    rotMatj,
                    insidePoints,
                    newDistPoints,
                ) = self.pandaBullet_relax(
                    env,
                    ptInd,
                    compartment,
                    target_grid_point_position,
                    rotation_matrix,
                    grid_point_distances,
                    dpad,
                    current_visual_instance,
                    dpad,
                )
            else:
                self.log.error("Can't pack using this method %s", self.placeType)
                self.reject()
                return False, {}, {}
        else:
            # blind packing without further collision checks
            # TODO: make this work for ingredients other than single spheres

            success = True
            newDistPoints = {}
            insidePoints = {}

            (jtrans, rotMatj,) = self.get_new_jitter_location_and_rotation(
                env, target_grid_point_position, rotation_matrix
            )

            packing_location = jtrans
            radius_of_area_to_check = self.encapsulatingRadius + dpad

            bounding_points_to_check = self.get_all_positions_to_check(packing_location)

            for bounding_point_position in bounding_points_to_check:

                grid_points_to_update = env.grid.getPointsInSphere(
                    bounding_point_position, radius_of_area_to_check
                )
                for grid_point_index in grid_points_to_update:
                    (
                        insidePoints,
                        newDistPoints,
                    ) = self.get_new_distances_and_inside_points(
                        env,
                        bounding_point_position,
                        rotMatj,
                        grid_point_index,
                        grid_point_distances,
                        newDistPoints,
                        insidePoints,
                    )

        if success:
            if is_realtime:
                autopack.helper.set_object_static(
                    current_visual_instance, jtrans, rotMatj
                )
            self.place(
                env, compartment, jtrans, rotMatj, ptInd, insidePoints, newDistPoints
            )
        else:
            if is_realtime:
                self.remove_from_realtime_display(current_visual_instance)
            self.reject()

        return success, insidePoints, newDistPoints

    def get_rotation(self, pt_ind, env, compartment):
        # compute rotation matrix rotMat
        comp_num = self.compNum

        rot_mat = numpy.identity(4)
        if comp_num > 0:
            # for surface points we compute the rotation which
            # aligns the principalVector with the surface normal
            v1 = self.principalVector
            v2 = compartment.get_normal_for_point(
                pt_ind, env.masterGridPositions[pt_ind], env.mesh_store
            )
            try:
                rot_mat = numpy.array(rotVectToVect(v1, v2), "f")
            except Exception:
                print("PROBLEM ", self.name)
                rot_mat = numpy.identity(4)
        else:
            # this is where we could apply biased rotation ie gradient/attractor
            if self.useRotAxis:
                if sum(self.rotAxis) == 0.0:
                    rot_mat = numpy.identity(4)
                elif (
                    self.useOrientBias and self.packingMode == "gradient"
                ):  # you need a gradient here
                    rot_mat = self.alignRotation(env.masterGridPositions[pt_ind])
                else:
                    rot_mat = autopack.helper.rotation_matrix(
                        random() * self.rotRange, self.rotAxis
                    )
            # for other points we get a random rotation
            else:
                rot_mat = env.randomRot.get()
        return rot_mat

    def randomize_rotation(self, rotation, histovol):
        # randomize rotation about axis
        jitter_rotation = numpy.identity(4)
        if self.compNum > 0:
            jitter_rotation = self.getAxisRotation(rotation)
        else:
            if self.useRotAxis:
                if sum(self.rotAxis) == 0.0:
                    jitter_rotation = numpy.identity(4)
                    # Graham Oct 16,2012 Turned on always rotate below as default.  If you want no rotation
                    # set useRotAxis = 1 and set rotAxis = 0, 0, 0 for that ingredient
                elif self.useOrientBias and self.packingMode == "gradient":
                    jitter_rotation = self.getBiasedRotation(rotation, weight=None)
                # weight = 1.0 - self.env.gradients[self.gradient].weight[ptInd])
                else:
                    # should we align to this rotAxis ?
                    jitter_rotation = autopack.helper.rotation_matrix(
                        random() * self.rotRange, self.rotAxis
                    )
            else:
                if histovol is not None:
                    jitter_rotation = histovol.randomRot.get()
                    if self.rotRange != 0.0:
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
        jx, jy, jz = self.jitterMax
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
                    if self.compNum > 0:  # jitter less among normal
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
        histoVol,
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
        afvi = histoVol.afviewer
        simulationTimes = histoVol.simulationTimes
        runTimeDisplay = histoVol.runTimeDisplay
        springOptions = histoVol.springOptions
        is_realtime = moving is not None

        jtrans, rotMatj = self.oneJitter(
            histoVol, target_grid_point_position, rotation_matrix
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
        mingrs, listePartner = self.getListePartners(
            histoVol, jtrans, rotation_matrix, compartment, afvi
        )
        for i, elem in enumerate(mingrs):
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
            elif ing.Type == "Grow":
                name = ing.name + str(ind)
                ipoly = afvi.vi.newInstance(
                    name, afvi.orgaToMasterGeom[ing], parent=afvi.staticMesh
                )
                static.append(ipoly)

        if listePartner:  # self.packingMode=="closePartner":
            self.log.info("len listePartner = %d", len(listePartner))
            if not self.force_random:
                targetPoint, weight = self.pickPartner(
                    mingrs, listePartner, currentPos=jtrans
                )
                if targetPoint is None:
                    targetPoint = jtrans
            else:
                targetPoint = jtrans
        # setup the target position
        if self.placeType == "spring":
            afvi.vi.setRigidBody(afvi.movingMesh, **histoVol.dynamicOptions["spring"])
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
            afvi.vi.setRigidBody(afvi.movingMesh, **histoVol.dynamicOptions["moving"])
            afvi.vi.setTranslation(self.moving, pos=targetPoint)
        afvi.vi.setRigidBody(afvi.staticMesh, **histoVol.dynamicOptions["static"])
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
            histoVol.grid,
            histoVol.masterGridPositions,
            dpad,
            distance,
            centT,
            jtrans,
            rotMatj,
            dpad,
        )

        # save dropped ingredient

        histoVol.rTrans.append(jtrans)
        histoVol.result.append([jtrans, rotMatj, self, ptInd])
        histoVol.rRot.append(rotMatj)
        histoVol.rIngr.append(self)

        self.rRot.append(rotMatj)
        self.tTrans.append(jtrans)

        self.log.info(
            "Success nbfp:%d %d/%d dpad %.2f",
            nbFreePoints,
            self.counter,
            self.nbMol,
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
        if self.packingMode != "graident":
            periodic_pos = self.env.grid.getPositionPeridocity(
                packing_location,
                getNormedVectorOnes(self.jitterMax),
                self.encapsulatingRadius,
            )
            points_to_check.extend(periodic_pos)
        return points_to_check

    def jitter_place(
        self,
        env,
        compartment,
        targeted_master_grid_point,
        rot_mat,
        moving,
        distance,
        dpad,
        afvi,
    ):
        """
        Check if the given grid point is available for packing using the jitter collision detection
        method. Returns packing location and new grid point values if packing is successful.
        """

        packing_location = None
        is_realtime = moving is not None
        level = self.collisionLevel
        for attempt_number in range(self.nbJitter):
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

            if self.point_is_not_available(packing_location):
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
                    env.masterGridPositions,
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

            if is_realtime:
                box = self.vi.getObject("collBox")
                self.vi.changeObjColorMat(box, [1, 0, 0] if collision else [0, 1, 0])
            if True not in collision_results:
                self.log.info(
                    "no collision, new points %d, %d",
                    len(insidePoints),
                    len(newDistPoints),
                )
                return (
                    True,
                    packing_location,
                    packing_rotation,
                    insidePoints,
                    newDistPoints,
                )
        return False, packing_location, packing_rotation, {}, {}

    def lookForNeighbours(self, trans, rotMat, organelle, afvi, closest_indice=None):
        mingrs, listePartner = self.getListePartners(
            self.env, trans, rotMat, organelle, afvi, close_indice=closest_indice
        )
        targetPoint = trans
        found = False
        if listePartner:  # self.packingMode=="closePartner":
            self.log.info("partner found")
            if not self.force_random:
                for jitterPos in range(self.nbJitter):  #
                    targetPoint, weight = self.pickPartner(
                        mingrs, listePartner, currentPos=trans
                    )
                    if targetPoint is not None:
                        break
                if targetPoint is None:
                    targetPoint = trans
                else:  # maybe get the ptid that can have it
                    found = True
                    if self.compNum > 0:
                        # surface
                        d, i = organelle.OGsrfPtsBht.query(targetPoint)
                        vx, vy, vz = v1 = self.principalVector
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

    def pandaBullet_collision(self, pos, rot, rbnode, getnodes=False):
        collision = False
        liste_nodes = []
        if len(self.env.rTrans) != 0:
            closesbody_indice = self.getClosestIngredient(
                pos,
                self.env,
                cutoff=self.env.largestProteinSize + self.encapsulatingRadius * 2.0,
            )  # vself.radii[0][0]*2.0
            if len(closesbody_indice["indices"]) != 0:
                self.log.info("get RB %d", len(closesbody_indice["indices"]))
                if rbnode is None:
                    rbnode = self.get_rb_model()
                    self.env.moveRBnode(rbnode, pos, rot)
                    self.log.info("get RB for %s", self.name)
                liste_nodes = self.get_rbNodes(closesbody_indice, pos, getInfo=True)
                self.log.info("test collision against  %d", len(liste_nodes))
                for node in liste_nodes:
                    self.log.info("collision test with %r", node)
                    self.env.moveRBnode(node[0], node[1], node[2])  # Pb here ?
                    collision = (
                        self.env.world.contactTestPair(rbnode, node[0]).getNumContacts()
                        > 0
                    )
                    if collision:
                        break
        if getnodes:
            return collision, liste_nodes
        else:
            return collision

    def get_compartment(self, env):
        if self.compNum == 0:
            return env
        else:
            return env.compartments[abs(self.compNum) - 1]

    def close_partner_check(self, translation, rotation, compartment, afvi, moving):
        bind = True
        self.log.info("look for ingredient %r", translation)
        # roll a dice about proba_not_binding
        if self.proba_not_binding != 0:  # between 0 and 1
            b = random()
            if b <= self.proba_not_binding:
                bind = False
        if bind:
            closesbody_indice = self.getClosestIngredient(
                translation, self.env, cutoff=self.env.grid.diag
            )  # vself.radii[0][0]*2.0
            target_point, rot_matrix, found = self.lookForNeighbours(
                translation,
                rotation,
                compartment,
                afvi,
                closest_indice=closesbody_indice,
            )
            if not found and self.counter != 0:
                self.reject()
                return translation, rotation

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

    def pandaBullet_place(
        self,
        histoVol,
        ptInd,
        distance,
        dpad,
        afvi,
        compartment,
        gridPointsCoords,
        rot_matrix,
        target_point,
        moving,
        usePP=False,
    ):
        """
        drop the ingredient on grid point ptInd
        """
        histoVol.setupPanda()
        is_realtime = moving is not None
        # we need to change here in case tilling, the pos,rot ade deduced fromte tilling.
        if self.packingMode[-4:] == "tile":

            if self.tilling is None:
                self.setTilling(compartment)
            if self.counter != 0:
                # pick the next Hexa pos/rot.
                t, collision_results = self.tilling.getNextHexaPosRot()
                if len(t):
                    rot_matrix = collision_results
                    trans = t
                    target_point = trans
                    if is_realtime:
                        self.update_display_rt(moving, target_point, rot_matrix)
                else:
                    return False, None, None, {}, {}  # ,targetPoint, rotMat
            else:
                self.tilling.init_seed(histoVol.seed_used)

        packing_location = None
        level = self.collisionLevel

        for jitter_attempt in range(self.nbJitter):
            histoVol.totnbJitter += 1

            (
                packing_location,
                packing_rotation,
            ) = self.get_new_jitter_location_and_rotation(
                histoVol,
                target_point,
                rot_matrix,
            )

            if is_realtime:
                self.update_display_rt(moving, target_point, rot_matrix)

            if self.point_is_not_available(packing_location):
                # jittered into wrong compartment,
                # go to next jitter
                continue

            collision_results = []
            rbnode = self.get_rb_model()

            points_to_check = self.get_all_positions_to_check(
                packing_location
            )  # includes periodic points, if appropriate
            for pt in points_to_check:
                histoVol.callFunction(
                    histoVol.moveRBnode,
                    (
                        rbnode,
                        pt,
                        packing_rotation,
                    ),
                )
                collision = self.pandaBullet_collision(pt, packing_rotation, rbnode)
                collision_results.extend([collision])
                if True in collision_results:
                    # break out of point check loop, not this jitter loop
                    break
            t = time()
            # checked packing location and periodic positions
            if True in collision_results:
                # found a collision, should check next jitter
                continue

            # need to check compartment too
            self.log.info("no additional collisions, checking compartment")
            if self.compareCompartment:

                collisionComp = self.compareCompartmentPrimitive(
                    level,
                    packing_location,
                    packing_rotation,
                    gridPointsCoords,
                    distance,
                )
                collision_results.extend([collisionComp])

            # got all the way through the checks with no collision
            if True not in collision_results:
                insidePoints = {}
                newDistPoints = {}
                t3 = time()

                # self.update_data_tree(jtrans,rotMatj,ptInd=ptInd)?
                self.env.static.append(rbnode)
                self.env.moving = None

                for pt in points_to_check:
                    self.env.rTrans.append(pt)
                    self.env.rRot.append(packing_rotation)
                    self.env.rIngr.append(self)
                    self.env.result.append([pt, packing_rotation, self, ptInd])

                    new_inside_points, new_dist_points = self.get_new_distance_values(
                        pt,
                        packing_rotation,
                        gridPointsCoords,
                        distance,
                        dpad,
                        self.deepest_level,
                    )
                    insidePoints = self.merge_place_results(
                        new_inside_points,
                        insidePoints,
                    )
                    newDistPoints = self.merge_place_results(
                        new_dist_points,
                        newDistPoints,
                    )
                self.log.info("compute distance loop %d", time() - t3)

                # rebuild kdtree
                if len(self.env.rTrans) >= 1:
                    self.env.close_ingr_bhtree = spatial.cKDTree(
                        self.env.rTrans, leafsize=10
                    )
                if self.packingMode[-4:] == "tile":
                    self.tilling.dropTile(
                        self.tilling.idc,
                        self.tilling.edge_id,
                        packing_location,
                        packing_rotation,
                    )

                success = True
                return (
                    success,
                    packing_location,
                    packing_rotation,
                    insidePoints,
                    newDistPoints,
                )

        # never found a place to pack
        success = False
        if self.packingMode[-4:] == "tile":
            if self.tilling.start.nvisit[self.tilling.edge_id] >= 2:
                self.tilling.start.free_pos[self.tilling.edge_id] = 0

        return success, None, None, {}, {}

    def pandaBullet_placeBHT(
        self,
        histoVol,
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
        histoVol.setupPanda()
        is_realtime = moving is not None

        gridPointsCoords = histoVol.masterGridPositions

        targetPoint = target_grid_point_position

        if is_realtime:
            self.update_display_rt(moving, targetPoint, rotation_matrix)

        # do we get the list of neighbours first > and give a different trans...closer to the partner
        # we should look up for an available ptID around the picked partner if any
        # getListCloseIngredient
        # should se a distance_of_influence ? or self.env.largestProteinSize+self.encapsulatingRadius*2.0
        # or the grid diagonal
        # we need to change here in case tilling, the pos,rot ade deduced fromte tilling.
        if self.packingMode[-4:] == "tile":
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
                self.tilling.init_seed(histoVol.seed_used)
        # we may increase the jitter, or pick from xyz->Id free for its radius
        # create the rb only once and not at ever jitter
        # rbnode = histoVol.callFunction(self.env.addRB,(self, jtrans, rotMat,),{"rtype":self.Type},)
        # jitter loop
        level = self.collisionLevel

        for attempt_number in range(self.nbJitter):
            insidePoints = {}
            newDistPoints = {}
            histoVol.totnbJitter += 1

            (
                packing_location,
                packing_rotation,
            ) = self.get_new_jitter_location_and_rotation(
                histoVol,
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
            if self.point_is_not_available(packing_location):
                continue
            if True in collision_results:
                continue

            # need to check compartment too
            self.log.info("no collision")
            if self.compareCompartment:
                collision = self.compareCompartmentPrimitive(
                    level,
                    packing_location,
                    packing_rotation,
                    gridPointsCoords,
                    distance,
                )
                collision_results.extend([collision])
            if True not in collision_results:
                # self.update_data_tree(jtrans,rotMatj,ptInd=ptInd)?
                self.env.static.append(rbnode)
                self.env.moving = None

                for pt in pts_to_check:
                    self.env.rTrans.append(pt)
                    self.env.rRot.append(packing_rotation)
                    self.env.rIngr.append(self)
                    self.env.result.append([pt, packing_rotation, self, ptInd])
                    new_inside_pts, new_dist_points = self.get_new_distance_values(
                        pt,
                        packing_rotation,
                        gridPointsCoords,
                        distance,
                        dpad,
                        self.deepest_level,
                    )
                    insidePoints = self.merge_place_results(
                        new_inside_pts, insidePoints
                    )
                    newDistPoints = self.merge_place_results(
                        new_dist_points, newDistPoints
                    )
                # rebuild kdtree
                if len(self.env.rTrans) >= 1:
                    del self.env.close_ingr_bhtree
                    self.env.close_ingr_bhtree = spatial.cKDTree(
                        self.env.rTrans, leafsize=10
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

    def pandaBullet_relax(
        self,
        histoVol,
        ptInd,
        compartment,
        target_grid_point_position,
        rotation_matrix,
        distance,
        dpad,
        moving,
        drop=True,
    ):
        """
        drop the ingredient on grid point ptInd
        """
        histoVol.setupPanda()
        afvi = histoVol.afviewer
        simulationTimes = histoVol.simulationTimes
        runTimeDisplay = histoVol.runTimeDisplay
        is_realtime = moving is not None
        gridPointsCoords = histoVol.grid.masterGridPositions
        insidePoints = {}
        newDistPoints = {}
        jtrans, rotMatj = self.oneJitter(
            histoVol, target_grid_point_position, rotation_matrix
        )
        # here should go the simulation
        # 1- we build the ingredient if not already and place the ingredient at jtrans, rotMatj
        targetPoint = jtrans
        if is_realtime:
            if hasattr(self, "mesh_3d"):
                # create an instance of mesh3d and place it
                name = self.name + str(ptInd)
                if self.mesh_3d is None:
                    self.moving_geom = afvi.vi.Sphere(
                        name, radius=self.radii[0][0], parent=afvi.movingMesh
                    )[0]
                    afvi.vi.setTranslation(self.moving_geom, pos=jtrans)
                else:
                    self.moving_geom = afvi.vi.newInstance(
                        name,
                        self.mesh_3d,
                        matrice=rotMatj,
                        location=jtrans,
                        parent=afvi.movingMesh,
                    )
        # 2- get the neighboring object from ptInd
        if histoVol.ingrLookForNeighbours:
            mingrs, listePartner = self.getListePartners(
                histoVol, jtrans, rotation_matrix, compartment, afvi
            )
            for i, elem in enumerate(mingrs):
                ing = elem[2]
                t = elem[0]
                r = elem[1]
                ind = elem[3]
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
                            matrice=r,
                            location=t,
                            parent=afvi.staticMesh,
                        )
                elif ing.Type == "Grow":
                    name = ing.name + str(ind)
                    ipoly = afvi.vi.newInstance(
                        name, afvi.orgaToMasterGeom[ing], parent=afvi.staticMesh
                    )

            if listePartner:  # self.packingMode=="closePartner":
                self.log.info("len listePartner = %d", len(listePartner))
                if not self.force_random:
                    targetPoint, weight = self.pickPartner(
                        mingrs, listePartner, currentPos=jtrans
                    )
                    if targetPoint is None:
                        targetPoint = jtrans
                else:
                    targetPoint = jtrans
                    #       should be panda util
                    #        add the rigid body
        self.env.moving = rbnode = self.env.callFunction(
            self.env.addRB,
            (
                self,
                jtrans,
                rotation_matrix,
            ),
            {"rtype": self.Type},
        )
        self.env.callFunction(
            self.env.moveRBnode,
            (
                rbnode,
                jtrans,
                rotMatj,
            ),
        )
        # run he simulation for simulationTimes
        histoVol.callFunction(
            self.env.runBullet,
            (
                self,
                simulationTimes,
                runTimeDisplay,
            ),
        )
        # cb=self.getTransfo)
        rTrans, rRot = self.env.getRotTransRB(rbnode)
        # 5- we get the resuling transofrmation matrix and decompose ->rTrans rRot
        # use
        # r=[ (self.env.world.contactTestPair(rbnode, n).getNumContacts() > 0 ) for n in self.env.static]
        self.env.static.append(rbnode)

        jtrans = rTrans[:]
        rotMatj = rRot[:]
        insidePoints, newDistPoints = self.get_new_distance_values(
            jtrans, rotMatj, gridPointsCoords, distance, dpad
        )
        self.rRot.append(rotMatj)
        self.tTrans.append(jtrans)
        success = True
        return success, jtrans, rotMatj, insidePoints, newDistPoints

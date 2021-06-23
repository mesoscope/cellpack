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
import time
from random import random, uniform, seed
import bisect
from scipy import spatial
import numpy
import pickle
from math import floor, exp, cos, sqrt, pow as mathPow, pi

# PANDA3D Physics engine ODE and Bullet
import panda3d

from panda3d.core import Mat3, Mat4, Vec3, Point3
from panda3d.core import TransformState
from panda3d.core import BitMask32
from panda3d.bullet import BulletSphereShape, BulletBoxShape, BulletCylinderShape

from panda3d.bullet import BulletRigidBodyNode
from panda3d.ode import OdeBody, OdeMass
from panda3d.ode import OdeSphereGeom
from panda3d.core import NodePath

from cellpack.mgl_tools.bhtree import bhtreelib
from cellpack.mgl_tools.upy.hostHelper import vdistance

import cellpack.autopack as autopack
from .Compartment import CompartmentList
from .Recipe import Recipe
from .Ingredient import GrowIngredient, ActinIngredient
from .ray import vlen, vdiff
from cellpack.autopack import IOutils
from cellpack.autopack.transformation import angle_between_vectors

# backward compatibility with kevin method
from cellpack.autopack.Grid import Grid as G

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from .randomRot import RandomRot

try:
    helper = autopack.helper
except ImportError:
    helper = None
print("Environment helper is " + str(helper))

# could replace by a faster json python library
try:
    import simplejson as json
    from simplejson import encoder
except ImportError:
    import json
    from json import encoder
encoder.FLOAT_REPR = lambda o: format(o, ".8g")

LISTPLACEMETHOD = autopack.LISTPLACEMETHOD
SEED = 14
LOG = False
verbose = 0


def ingredient_compare1(x, y):
    """
    sort ingredients using decreasing priority and decreasing radii for
    priority ties and decreasing completion for radii ties
    for priority > 0
    """
    p1 = x.packingPriority
    p2 = y.packingPriority
    if p1 < p2:  # p1 > p2
        return 1
    elif p1 == p2:  # p1 == p1
        r1 = x.minRadius
        r2 = y.minRadius
        if r1 > r2:  # r1 < r2
            return 1
        elif r1 == r2:  # r1 == r2
            c1 = x.completion
            c2 = y.completion
            if c1 > c2:  # c1 > c2
                return 1
            elif c1 == c2:
                return 0
            else:
                return -1
        else:
            return -1
    else:
        return -1


def ingredient_compare0(x, y):
    """
    sort ingredients using decreasing priority and decreasing radii for
    priority ties and decreasing completion for radii ties
    for priority < 0
    """
    p1 = x.packingPriority
    p2 = y.packingPriority
    if p1 > p2:  # p1 > p2
        return 1
    elif p1 == p2:  # p1 == p1
        r1 = x.minRadius
        r2 = y.minRadius
        if r1 > r2:  # r1 < r2
            return 1
        elif r1 == r2:  # r1 == r2
            c1 = x.completion
            c2 = y.completion
            if c1 > c2:  # c1 > c2
                return 1
            elif c1 == c2:
                return 0
            else:
                return -1
        else:
            return -1
    else:
        return -1


def ingredient_compare2(x, y):
    """
    sort ingredients using decreasing radii and decresing completion
    for radii matches:
    priority = 0
    """
    c1 = x.minRadius
    c2 = y.minRadius
    if c1 < c2:
        return 1
    elif c1 == c2:
        r1 = x.completion
        r2 = y.completion
        if r1 > r2:
            return 1
        elif r1 == r2:
            return 0
        else:
            return -1
    else:  # x < y
        return -1


def cmp_to_key(mycmp):
    "Convert a cmp= function into a key= function"

    class K:
        def __init__(self, obj, *args):
            self.obj = obj

        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0

        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0

        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0

        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0

        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0

        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0

    return K


class Gradient:
    """
    The Gradient class
    ==========================
    This class handle the use of gradient to control the packing.
    The class define different and setup type of gradient,
    as well as the sampling function
    """

    def __init__(self, name, mode="X", description="", direction=None, bb=None, **kw):
        self.name = name
        self.description = description
        self.start = []
        self.end = []
        self.bb = [[], []]
        if bb is not None:
            self.computeStartEnd()
        self.function = self.defaultFunction  # lambda ?
        self.weight = None
        self.liste_mode = ["X", "Y", "Z", "-X", "-Y", "-Z", "direction", "radial"]
        self.mode = mode  # can X,Y,Z,-X,-Y,-Z,"direction" custom vector
        self.weight_mode = (
            "gauss"  # "linear" #linear mode for weight generation linearpos linearneg
        )
        if "weight_mode" in kw:
            self.weight_mode = kw["weight_mode"]
        self.pick_mode = "rnd"
        if "pick_mode" in kw:
            self.pick_mode = kw["pick_mode"]
        self.axes = {"X": 0, "-X": 0, "Y": 1, "-Y": 1, "Z": 2, "-Z": 2}
        self.directions = {
            "X": [1, 0, 0],
            "-X": [-1, 0, 0],
            "Y": [0, 1, 0],
            "-Y": [0, -1, 0],
            "Z": [0, 0, 1],
            "-Z": [0, 0, -1],
        }
        self.radius = 10.0
        if "radius" in kw:
            self.radius = kw["radius"]
        self.weight_threshold = 0.0
        if direction is None:
            self.direction = self.directions[self.mode]
        else:
            self.direction = direction  # from direction get start and end point
        self.distance = 0.0
        self.gblob = 4.0
        # Note : theses functions could also be used to pick an ingredient
        self.pick_functions = {
            "max": self.getMaxWeight,
            "min": self.getMinWeight,
            "rnd": self.getRndWeighted,
            "linear": self.getLinearWeighted,
            "binary": self.getBinaryWeighted,
            "sub": self.getSubWeighted,
            "reg": self.getForwWeight,
        }
        self.liste_weigth_mode = self.pick_functions.keys()
        self.liste_options = [
            "mode",
            "weight_mode",
            "pick_mode",
            "direction",
            "radius",
            "gblob",
        ]
        self.OPTIONS = {
            "mode": {
                "name": "mode",
                "values": self.liste_mode,
                "default": "X",
                "type": "liste",
                "description": "gradient direction",
                "min": 0,
                "max": 0,
            },
            "weight_mode": {
                "name": "weight_mode",
                "values": ["linear", "square", "cube", "gauss", "half-gauss"],
                "default": "linear",
                "type": "liste",
                "description": "calcul of the weight method",
                "min": 0,
                "max": 0,
            },
            "pick_mode": {
                "name": "weight_mode",
                "values": self.liste_weigth_mode,
                "default": "linear",
                "type": "liste",
                "description": "picking random weighted method",
                "min": 0,
                "max": 0,
            },
            "direction": {
                "name": "direction",
                "value": [0.5, 0.5, 0.5],
                "default": [0.5, 0.5, 0.5],
                "type": "vector",
                "description": "gradient custom direction",
                "min": -2000.0,
                "max": 2000.0,
            },
            "description": {
                "name": "description",
                "value": self.description,
                "default": "a gradient",
                "type": "label",
                "description": None,
                "min": 0,
                "max": 0,
            },
            "radius": {
                "name": "radius",
                "value": self.radius,
                "default": 100.0,
                "type": "float",
                "description": "radius for the radial mode",
                "min": 0,
                "max": 2000.0,
            },
            "gblob": {
                "name": "gblob",
                "value": self.gblob,
                "default": 4.0,
                "type": "float",
                "description": "bobliness the gaussian mode",
                "min": 0.1,
                "max": 2000.0,
            },
        }

    def getCenter(self):
        """get the center of the gradient grid"""
        center = [0.0, 0.0, 0.0]
        for i in range(3):
            center[i] = (self.bb[0][i] + self.bb[1][i]) / 2.0
        return center

    def computeStartEnd(self):
        """get the overal direction of the gradient"""
        # using bb and direction
        self.start = numpy.array(self.bb[0])
        self.end = numpy.array(self.bb[1]) * numpy.array(self.direction)
        self.vgradient = self.end - self.start
        # self.distance = math.sqrt(numpy.sum(d*d))

    def defaultFunction(self, xyz):
        """
        #linear function 0->0.1
        #project xyz on direction
        """
        x = numpy.dot(xyz, self.direction)
        v = (x * 1.0) / (self.distance)
        return v

    def pickPoint(self, listPts):
        """
        pick next random point according to the choosen function
        """
        return self.pick_functions[self.pick_mode](listPts)

    def buildWeigthMap(self, bb, MasterPosition):
        """
        build the actual gradient value according the gradint mode
        """
        print("gradient ", self.name, self.mode)
        if self.mode in self.axes:
            self.buildWeigthMapAxe(bb, MasterPosition)
        elif self.mode == "direction":
            self.buildWeigthMapDirection(bb, MasterPosition)
        elif self.mode == "radial":
            self.buildWeigthMapRadial(bb, MasterPosition)

    def get_gauss_weights(self, N, degree=5):
        """
        given a number of point compute the gaussian weight for each
        """
        degree = N / 2
        window = N  # degree*2#-1
        weight = numpy.array([1.0]) * window
        weightGauss = []
        for i in range(int(window)):
            i = i - degree + 1
            frac = i / float(window)
            gauss = 1 / (numpy.exp((self.gblob * (frac)) ** 2))
            weightGauss.append(gauss)
        return numpy.array(weightGauss) * weight

    def get_gauss_weights1(self, N):
        """
        given a number of point compute the gaussian weight for each
        (alternative function)
        """
        support_points = [(float(3 * i) / float(N)) ** 2.0 for i in range(-N, N + 1)]
        gii_factors = [exp(-(i / 2.0)) for i in support_points]
        ki = float(sum(gii_factors))
        return [giin / ki for giin in gii_factors]

    def getDirectionLength(self, bb=None, direction=None):
        if direction is None:
            direction = self.direction
        if bb is None:
            bb = self.bb
        # assume grid orthogonal
        maxinmini = []
        a = []
        axes = ["X", "Y", "Z"]
        for i, ax in enumerate(axes):
            angle = angle_between_vectors(self.directions[ax], direction)
            a.append(angle)
            maxi = max(bb[1][i], bb[0][i])
            mini = min(bb[1][i], bb[0][i])
            maxinmini.append([mini, maxi])
        m = min(a)
        axi = a.index(m)
        L = maxinmini[axi][1] - maxinmini[axi][0]
        vdot = numpy.dot(
            numpy.array(self.directions[axes[axi]]), numpy.array(direction)
        )  # cos a * |A|*|B|
        Ld = (1.0 / vdot) * (cos(m) * L)
        return Ld, maxinmini

    def buildWeigthMapRadial(self, bb, MasterPosition):
        """
        from a given point (self.direction) build a radial weight
        according the chosen mode
        (linear, gauss, etc...)
        """
        N = len(MasterPosition)
        self.bb = bb
        radial_point = self.direction
        NW = N / 3
        self.weight = []
        xl, yl, zl = bb[0]
        xr, yr, zr = bb[1]

        if self.weight_mode == "gauss":  # 0-1-0
            d = self.get_gauss_weights(
                NW
            )  # numpy.random.normal(0.5, 0.1, NW) #one dimension
        elif self.weight_mode == "half-gauss":  # 0-1
            d = self.get_gauss_weights(NW * 2)[NW:]
        for ptid in range(N):
            dist = vdistance(MasterPosition[ptid], radial_point)
            if self.weight_mode == "linear":
                w = (
                    (1.0 - (abs(dist) / self.radius))
                    if abs(dist) < self.radius
                    else 0.0
                )
                self.weight.append(w)  #
            elif self.weight_mode == "square":
                w = (
                    mathPow((1.0 - (abs(dist) / self.radius)), 2)
                    if abs(dist) < self.radius
                    else 0.0
                )
                self.weight.append(w)  #
            elif self.weight_mode == "cube":
                w = (
                    mathPow((1.0 - (abs(dist) / self.radius)), 3)
                    if abs(dist) < self.radius
                    else 0.0
                )
                self.weight.append(w)  #
            elif self.weight_mode == "gauss":
                w = abs(dist) / self.radius if abs(dist) < self.radius else 1.0
                i = int(w * N / 3) if int(w * N / 3) < len(d) else len(d) - 1
                self.weight.append(d[i])
            elif self.weight_mode == "half-gauss":
                w = abs(dist) / self.radius if abs(dist) < self.radius else 1.0
                i = int(w * N / 3) if int(w * N / 3) < len(d) else len(d) - 1
                self.weight.append(d[i])

    def buildWeigthMapDirection(self, bb, MasterPosition):
        """
        from a given direction build a linear weigth according the choosen mode
        (linear, gauss, etc...)
        """
        N = len(MasterPosition)
        self.bb = bb
        axe = self.direction
        NW = N / 3
        self.weight = []
        center = self.getCenter()
        L, maxinmini = self.getDirectionLength(bb)
        if self.weight_mode == "gauss":
            d = self.get_gauss_weights(
                NW
            )  # numpy.random.normal(0.5, 0.1, NW) #one dimension
        elif self.weight_mode == "half-gauss":  # 0-1
            d = self.get_gauss_weights(NW * 2)[NW:]
        for ptid in range(N):
            pt = numpy.array(MasterPosition[ptid]) - numpy.array(
                center
            )  # [maxinmini[0][0],maxinmini[1][0],maxinmini[2][0]])
            vdot = numpy.dot(pt, numpy.array(axe))
            p = ((L / 2.0) + vdot) / L
            if self.weight_mode == "linear":
                self.weight.append(p)  # -0.5->0.5 axe value normalized?
            elif self.weight_mode == "square":
                self.weight.append(mathPow(p, 2))  #
            elif self.weight_mode == "cube":
                self.weight.append(mathPow(p, 3))  #
            elif self.weight_mode == "gauss":
                #                p goes from 0.0 to 1.0
                if p < 0.1:
                    p = 0.0
                i = int(p * NW) if int(p * NW) < len(d) else len(d) - 1
                # w = d[i] if d[i] > 0.9 else 0.0
                self.weight.append(d[i])

    def buildWeigthMapAxe(self, bb, MasterPosition, Axe="X"):
        """
        from a given axe (X,Y,Z) build a linear weight according the chosen mode
        (linear, gauss, etc...)
        """
        N = len(MasterPosition)
        NW = N / 3
        self.bb = bb
        ind = self.axes[self.mode]
        maxi = max(bb[1][ind], bb[0][ind])
        mini = min(bb[1][ind], bb[0][ind])
        self.weight = []
        if self.weight_mode == "gauss":
            d = self.get_gauss_weights(
                N / 3
            )  # d = numpy.random.normal(0.5, 0.1, N/3) #one dimension
        elif self.weight_mode == "half-gauss":  # 0-1
            d = self.get_gauss_weights(NW * 2)[NW:]  # TODO: fix error here
        for ptid in range(N):
            p = (MasterPosition[ptid][ind] - mini) / (maxi - mini)
            if self.weight_mode == "linear":
                self.weight.append(p)  # -0.5->0.5 axe value normalized?
            elif self.weight_mode == "square":
                self.weight.append(mathPow(p, 2))  #
            elif self.weight_mode == "cube":
                self.weight.append(mathPow(p, 3))  #
            elif self.weight_mode == "gauss":
                vax = p  # (MasterPosition[ptid][ind]-mini)/(maxi-mini) #0-1 on the axes
                i = int(vax * N / 3) if int(vax * N / 3) < len(d) else len(d) - 1
                self.weight.append(d[i])
            elif self.weight_mode == "half-gauss":
                i = int(p * N / 3) if int(p * N / 3) < len(d) else len(d) - 1
                self.weight.append(d[i])

    def getMaxWeight(self, listPts):
        """
        from the given list of grid point indice, get the point with the maximum weight
        """
        ptInd = listPts[0]
        m = 0.0
        for pointIndex in listPts:
            if self.weight[pointIndex] > m:
                m = self.weight[pointIndex]
                ptInd = pointIndex
        if self.weight[ptInd] < self.weight_threshold:
            ptInd = None
        return ptInd

    def getMinWeight(self, listPts):
        """
        from the given list of grid point indice, get the point with the minimum weight
        """
        ptInd = listPts[0]
        m = 1.1
        for pointIndex in listPts:
            if self.weight[pointIndex] < m and self.weight[pointIndex] != 0:
                m = self.weight[pointIndex]
                ptInd = pointIndex
        if self.weight[ptInd] < self.weight_threshold:
            return None
        return ptInd

    def getRndWeighted(self, listPts):
        """
        From http://glowingpython.blogspot.com/2012/09/weighted-random-choice.html
        Weighted random selection
        returns n_picks random indexes.
        the chance to pick the index i
        is give by the weight weights[i].
        """
        weight = numpy.take(self.weight, listPts)
        t = numpy.cumsum(weight)
        s = numpy.sum(weight)
        i = numpy.searchsorted(t, numpy.random.rand(1) * s)[0]
        return listPts[i]

    def getLinearWeighted(self, listPts):
        """
        From:
        http://eli.thegreenplace.net/2010/01/22/weighted-random-generation-in-python/
        The following is a simple function to implement weighted random selection in
        Python.
        Given a list of weights, it returns an index randomly,
        according to these weights [2].
        For example, given [2, 3, 5] it returns 0 (the index of the first element)
        with probability 0.2,
        1 with probability 0.3 and 2 with probability 0.5.
        The weights need not sum up to anything in particular,
        and can actually be arbitrary Python floating point numbers.
        """
        totals = []
        running_total = 0
        weights = numpy.take(self.weight, listPts)
        for w in weights:
            running_total += w
            totals.append(running_total)

        rnd = random() * running_total
        for i, total in enumerate(totals):
            if rnd < total:
                return listPts[i]

    def getBinaryWeighted(self, listPts):
        """
        From
        http://eli.thegreenplace.net/2010/01/22/weighted-random-generation-in-python/
        Note that the loop in the end of the function is simply looking
        for a place to insert rnd in a sorted list. Therefore, it can be
        speed up by employing binary search. Python comes with one built-in,
        just use the bisect module.
        """
        totals = []
        running_total = 0

        weights = numpy.take(self.weight, listPts)
        for w in weights:
            running_total += w
            totals.append(running_total)

        rnd = random() * running_total
        i = bisect.bisect_right(totals, rnd)
        return listPts[i]

    def getForwWeight(self, listPts):
        dice = random()
        # sorted ?
        for i in listPts:
            if self.weight[i] > dice and self.weight[i] != 0:
                return i

    def getSubWeighted(self, listPts):
        """
        From
        http://eli.thegreenplace.net/2010/01/22/weighted-random-generation-in-python/
        This method is about twice as fast as the binary-search technique,
        although it has the same complexity overall. Building the temporary
        list of totals turns out to be a major part of the functions runtime.
        This approach has another interesting property. If we manage to sort
        the weights in descending order before passing them to
        weighted_choice_sub, it will run even faster since the random
        call returns a uniformly distributed value and larger chunks of
        the total weight will be skipped in the beginning.
        """

        weights = numpy.take(self.weight, listPts)
        rnd = random() * sum(weights)
        for i, w in enumerate(weights):
            rnd -= w
            if rnd < 0:
                return listPts[i]


class Grid(G):
    """
    The Grid class
    ==========================
    This class handle the use of grid to control the packing. The grid keep information
    of 3d positions, distances, freePoints and inside/surface points from organelles.
    NOTE : this class could be completely replaced if openvdb is wrapped to python.
    """

    def __init__(self, boundingBox=([0, 0, 0], [0.1, 0.1, 0.1]), space=10.0):
        # a grid is attached to an environement
        G.__init__(self, boundingBox=boundingBox, space=space, setup=False)
        self.boundingBox = boundingBox
        # this list provides the id of the component this grid points belongs
        # to. The id is an integer where 0 is the Histological Volume, and +i is
        # the surface of compartment i and -i is the interior of compartment i
        # in the list self. compartments
        self.gridPtId = []
        # will be a list of indices into 3D of Environment
        # of points that have not yet been used by the packing algorithm
        # entries are removed from this list as grid points are used up
        # during packing. This list is used to pick points randomly during
        # the packing
        self.freePoints = []
        self.nbFreePoints = 0
        # this list evolves in parallel with self.freePoints and provides
        # the distance to the closest surface (either an already placed
        # object (or an compartment surface NOT IMPLEMENTED)
        self.distToClosestSurf = []
        self.distToClosestSurf_store = []

        self.diag = self.getDiagonal()
        self.gridSpacing = space * 1.1547
        self.nbGridPoints = None
        self.nbSurfacePoints = 0
        self.gridVolume = 0  # will be the toatl number of grid points
        # list of (x,y,z) for each grid point (x index moving fastest)
        self.masterGridPositions = []

        # this are specific for each compartment
        self.aInteriorGrids = []
        self.aSurfaceGrids = []
        # bhtree
        self.surfPtsBht = None
        self.ijkPtIndice = []
        self.filename = None  # used for storing before pack so no need rebuild
        self.result_filename = None  # used after pack to store result

        self.encapsulatingGrid = 1
        self.gridVolume, self.nbGridPoints = self.computeGridNumberOfPoint(
            boundingBox, space
        )
        self.create3DPointLookup()
        self.getDiagonal()
        self.nbSurfacePoints = 0
        self.gridPtId = numpy.zeros(self.gridVolume, "i")  # [0]*nbPoints
        # self.distToClosestSurf = [self.diag]*self.gridVolume#surface point too?
        self.distToClosestSurf = (
            numpy.ones(self.gridVolume) * self.diag
        )  # (self.distToClosestSurf)
        self.freePoints = list(range(self.gridVolume))
        self.nbFreePoints = len(self.freePoints)

    def reset(
        self,
    ):
        # reset the  distToClosestSurf and the freePoints
        # boundingBox shoud be the same otherwise why keeping the grid

        self.distToClosestSurf[:] = self.diag
        self.freePoints = list(range(len(self.freePoints)))
        self.nbFreePoints = len(self.freePoints)
        self.distancesAfterFill = []
        self.freePointsAfterFill = []
        self.nbFreePointsAfterFill = []
        self.distanceAfterFill = []

    def removeFreePoint(self, pti):
        tmp = self.freePoints[self.nbFreePoints]  # last one
        self.freePoints[self.nbFreePoints] = pti
        self.freePoints[pti] = tmp
        self.nbFreePoints -= 1

    # Very dangerous to manipulate the grids... lets solve this problem much earlier
    # in the setup with the new PseudoCode
    #    def updateDistances(self, histoVol ,insidePoints, freePoints,
    #                        nbFreePoints ):
    #        verbose = histoVol.verbose
    #        nbPts = len(insidePoints)
    #        for pt in insidePoints:  #Reversing is not necessary if you use the
    # correct Swapping GJ Aug 17,2012
    #            try :
    #                # New system replaced by Graham on Aug 18, 2012
    #                nbFreePoints -= 1
    #                vKill = freePoints[pt]
    #                vLastFree = freePoints[nbFreePoints]
    #                freePoints[vKill] = vLastFree
    #                freePoints[vLastFree] = vKill
    #            except :
    #                pass
    #
    #        return nbFreePoints,freePoints
    #
    #    def removeFreePointdeque(self,pti):
    #        self.freePoints.remove(pti)

    def create3DPointLookup(self, boundingBox=None):
        """
        Fill the orthogonal bounding box described by two global corners
        with an array of points spaces pGridSpacing apart.:
        """
        if boundingBox is None:
            boundingBox = self.boundingBox
        xl, yl, zl = boundingBox[0]
        xr, yr, zr = boundingBox[1]

        nx, ny, nz = self.nbGridPoints
        pointArrayRaw = numpy.zeros((nx * ny * nz, 3), "f")
        self.ijkPtIndice = numpy.zeros((nx * ny * nz, 3), "i")
        space = self.gridSpacing
        # Vector for lower left broken into real of only the z coord.
        i = 0
        for zi in range(nz):
            for yi in range(ny):
                for xi in range(nx):
                    pointArrayRaw[i] = (
                        xl + xi * space,
                        yl + yi * space,
                        zl + zi * space,
                    )
                    self.ijkPtIndice[i] = (xi, yi, zi)
                    i += 1
        self.masterGridPositions = pointArrayRaw

    def getPointFrom3D(self, pt3d):
        """
        get point number from 3d coordinates
        """
        x, y, z = pt3d  # Continuous 3D point to be discretized
        spacing1 = (
            1.0 / self.gridSpacing
        )  # Grid spacing = diagonal of the voxel determined by smalled packing radius
        (
            NX,
            NY,
            NZ,
        ) = (
            self.nbGridPoints
        )  # vector = [length, height, depth] of grid, units = gridPoints
        OX, OY, OZ = self.boundingBox[0]  # origin of Pack grid
        # Algebra gives nearest gridPoint ID to pt3D
        i = min(NX - 1, max(0, round((x - OX) * spacing1)))
        j = min(NY - 1, max(0, round((y - OY) * spacing1)))
        k = min(NZ - 1, max(0, round((z - OZ) * spacing1)))
        return int(k * NX * NY + j * NX + i)

    def getIJK(self, ptInd):
        """
        get i,j,k (3d) indices from u (1d)
        """
        # ptInd = k*(sizex)*(sizey)+j*(sizex)+i;#want i,j,k
        return self.ijkPtIndice[ptInd]

    def checkPointInside(self, pt3d, dist=None, jitter=[1, 1, 1]):
        """
        Check if the given 3d points is inside the grid
        """
        origin = numpy.array(self.boundingBox[0])
        E = numpy.array(self.boundingBox[1])
        P = numpy.array(pt3d)
        test1 = P < origin
        test2 = P > E
        if True in test1 or True in test2:
            # outside
            return False
        else:
            if dist is not None:
                # distance to closest wall
                d1 = P - origin
                s1 = min(x for x in (d1 * jitter) if x != 0)
                # s1 = numpy.sum(d1*d1)
                d2 = E - P
                s2 = min(x for x in (d2 * jitter) if x != 0)
                # s2 = numpy.sum(d2*d2)
                if s1 <= dist or s2 <= dist:
                    return False
            return True

    def getCenter(self):
        """
        Get the center of the grid
        """
        center = [0.0, 0.0, 0.0]
        for i in range(3):
            center[i] = (self.boundingBox[0][i] + self.boundingBox[1][i]) / 2.0
        return center

    def getRadius(self):
        """
        Get the radius the grid
        """
        d = numpy.array(self.boundingBox[0]) - numpy.array(self.boundingBox[1])
        s = numpy.sum(d * d)
        return sqrt(s)

    def getPointsInCube(self, bb, pt, radius, addSP=True, info=False):
        """
        Return all grid points indicesinside the given bouding box.
        """
        spacing1 = 1.0 / self.gridSpacing
        NX, NY, NZ = self.nbGridPoints
        OX, OY, OZ = self.boundingBox[
            0
        ]  # origin of Pack grid-> bottom lef corner not origin
        ox, oy, oz = bb[0]
        ex, ey, ez = bb[1]

        i0 = int(max(0, floor((ox - OX) * spacing1)))
        i1 = int(min(NX, int((ex - OX) * spacing1) + 1))
        j0 = int(max(0, floor((oy - OY) * spacing1)))
        j1 = int(min(NY, int((ey - OY) * spacing1) + 1))
        k0 = int(max(0, floor((oz - OZ) * spacing1)))
        k1 = int(min(NZ, int((ez - OZ) * spacing1) + 1))

        zPlaneLength = NX * NY

        ptIndices = []
        for z in range(int(k0), int(k1)):
            offz = z * zPlaneLength
            for y in range(int(j0), int(j1)):
                off = y * NX + offz
                for x in range(int(i0), int(i1)):
                    ptIndices.append(x + off)

        # add surface points
        if addSP and self.nbSurfacePoints != 0:
            result = numpy.zeros((self.nbSurfacePoints,), "i")
            nb = self.surfPtsBht.closePoints(tuple(pt), radius, result)
            dimx, dimy, dimz = self.nbGridPoints
            ptIndices.extend(
                list(map(lambda x, length=self.gridVolume: x + length, result[:nb]))
            )
        return ptIndices

    def computeGridNumberOfPoint(self, boundingBox, space):
        """
        Return the grid size : total number of point and number of point per axes
        """
        xl, yl, zl = boundingBox[0]
        xr, yr, zr = boundingBox[1]

        # Graham Added on Oct17 to allow for truly 2D grid for test packs,
        # may break everything!
        encapsulatingGrid = self.encapsulatingGrid

        from math import ceil

        nx = int(ceil((xr - xl) / space)) + encapsulatingGrid
        ny = int(ceil((yr - yl) / space)) + encapsulatingGrid
        nz = int(ceil((zr - zl) / space)) + encapsulatingGrid
        return nx * ny * nz, (nx, ny, nz)

        # ==============================================================================

    # TO DO File IO
    # ==============================================================================
    def save(self):
        pass

    def restore(self):
        pass


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

    def __init__(self, name="H"):
        CompartmentList.__init__(self)
        self.verbose = verbose  # "global variable Verbose"
        self.timeUpDistLoopTotal = 0
        self.name = name
        self.exteriorRecipe = None
        self.hgrid = []
        self.world = None  # panda world for collision
        self.octree = None  # ongoing octree test, no need if openvdb wrapp to python
        self.grid = None  # Grid()  # the main grid
        self.encapsulatingGrid = (
            0  # Only override this with 0 for 2D packing- otherwise its very unsafe!
        )
        # 0 is the exterior, 1 is compartment 1 surface, -1 is compartment 1 interior
        self.nbCompartments = 1
        self.name = "out"

        self.order = {}  # give the order of drop ingredient by ptInd from molecules
        self.lastrank = 0

        # smallest and largest protein radii across all recipes
        self.smallestProteinSize = 99999999
        self.largestProteinSize = 0
        self.scaleER = 2.5  # hack in case problem with encapsulating radius
        self.computeGridParams = True

        self.EnviroOnly = False
        self.EnviroOnlyCompartiment = -1
        # bounding box of the Environment

        self.boundingBox = [[0, 0, 0], [0.1, 0.1, 0.1]]
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
        self.ingr_added = {}

        self.randomRot = RandomRot()  # the class used to generate random rotation
        self.activeIngr = []
        self.activeIngre_saved = []

        # optionally can provide a host and a viewer
        self.host = None
        self.afviewer = None

        # version of setup used
        self.version = "1.0"

        # option for packing using host dynamics capability
        self.windowsSize = 100
        self.windowsSize_overwrite = False

        self.runTimeDisplay = False
        self.placeMethod = "jitter"
        self.innerGridMethod = "bhtree"  # or sdf
        self.orthogonalBoxType = 0
        self.overwritePlaceMethod = False
        self.rejectionThreshold = None
        # if use C4D RB dynamics, should be genralized
        self.springOptions = {}
        self.dynamicOptions = {}
        self.setupRBOptions()
        self.simulationTimes = 2.0

        # saving/pickle option
        self.saveResult = False
        self.resultfile = ""
        self.setupfile = ""
        self.current_path = None  # the path of the recipe file
        self.custom_paths = None
        self.useXref = True
        self.grid_filename = None  #
        self.grid_result_filename = None  # str(gridn.getAttribute("grid_result"))

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
        self.pickRandPt = True  # point pick randomly or one after the other?
        self.currtId = 0

        # gradient
        self.gradients = {}

        self.use_gradient = False  # gradient control is also per ingredient
        self.use_halton = False  # use halton for grid point distribution

        self.ingrLookForNeighbours = False  # Old Features to be test

        # debug with timer function
        self._timer = False
        self._hackFreepts = False  # hack for speed up ?
        self.freePtsUpdateThreshold = 0.0
        self.nb_ingredient = 0
        self.totalNbIngr = 0
        self.treemode = "cKDTree"  # "bhtree"
        self.close_ingr_bhtree = (
            None  # RBHTree(a.tolist(),range(len(a)),10,10,10,10,10,9999)
        )
        self.rTrans = []
        self.result = []
        self.rIngr = []
        self.rRot = []
        self.listPlaceMethod = LISTPLACEMETHOD
        # should be part of an independent module
        self.panda_solver = "bullet"  # or bullet
        # could be a problem here for pp
        # can't pickle this dictionary
        self.rb_func_dic = {}
        self.use_periodicity = False
        self.gridbiasedPeriodicity = None  # unused here
        # need options for the save/server data etc....
        # should it be in __init__ like other general options ?
        self.dump = True
        self.dump_freq = 120.0
        self.jsondic = None

        self.distancesAfterFill = []
        self.freePointsAfterFill = []
        self.nbFreePointsAfterFill = []
        self.distanceAfterFill = []

        self.OPTIONS = {
            "smallestProteinSize": {
                "name": "smallestProteinSize",
                "value": 15,
                "default": 15,
                "type": "int",
                "description": "Smallest ingredient packing radius override (low=accurate | high=fast)",  # noqa: E501
                "mini": 1.0,
                "maxi": 1000.0,
                "width": 30,
            },
            "largestProteinSize": {
                "name": "largestProteinSize",
                "value": 0,
                "default": 0,
                "type": "int",
                "description": "largest Protein Size",
                "width": 30,
            },
            "computeGridParams": {
                "name": "computeGridParams",
                "value": True,
                "default": True,
                "type": "bool",
                "description": "compute Grid Params",
                "width": 100,
            },
            "EnviroOnly": {
                "name": "EnviroOnly",
                "value": False,
                "default": False,
                "type": "bool",
                "description": "Histo volume Only",
                "width": 30,
            },
            "windowsSize": {
                "name": "windowsSize",
                "value": 100,
                "default": 100,
                "type": "int",
                "description": "windows Size",
                "width": 30,
            },
            "runTimeDisplay": {
                "name": "runTimeDisplay",
                "value": False,
                "default": False,
                "type": "bool",
                "description": "Display packing in realtime (slow)",
                "width": 150,
            },
            "placeMethod": {
                "name": "placeMethod",
                "value": "jitter",
                "values": self.listPlaceMethod,
                "default": "placeMethod",
                "type": "liste",
                "description": "Overriding Packing Method = ",
                "width": 30,
            },
            "use_gradient": {
                "name": "use_gradient",
                "value": False,
                "default": False,
                "type": "bool",
                "description": "Use gradients if defined",
                "width": 150,
            },
            "gradients": {
                "name": "gradients",
                "value": "",
                "values": [],
                "default": "",
                "type": "liste",
                "description": "Gradients available",
                "width": 150,
            },
            "innerGridMethod": {
                "name": "innerGridMethod",
                "value": "jordan3",
                "values": [
                    "bhtree",
                    #                                           "sdf",
                    "jordan",
                    "jordan3",
                    "pyray",
                    "floodfill",
                    #                                           "binvox",
                    "trimesh",
                    "scanline",
                ],
                "default": "jordan3",
                "type": "liste",
                "description": "Method to calculate the inner grid:",
                "width": 30,
            },
            "overwritePlaceMethod": {
                "name": "overwritePlaceMethod",
                "value": True,
                "default": True,
                "type": "bool",
                "description": "Overwrite per-ingredient packing method with Overriding Packing Method:",  # noqa: E501
                "width": 300,
            },
            "saveResult": {
                "name": "saveResult",
                "value": False,
                "default": False,
                "type": "bool",
                "description": "Save packing result to .apr file (enter full path below):",  # noqa: E501
                "width": 200,
            },
            "resultfile": {
                "name": "resultfile",
                "value": "fillResult",
                "default": "fillResult",
                "type": "filename",
                "description": "result filename",
                "width": 200,
            },
            # cancel dialog
            "cancelDialog": {
                "name": "cancelDialog",
                "value": False,
                "default": False,
                "type": "bool",
                "description": "compute Grid Params",
                "width": 30,
            },
            # do we sort the ingredient or not see  getSortedActiveIngredients
            "pickWeightedIngr": {
                "name": "pickWeightedIngr",
                "value": True,
                "default": True,
                "type": "bool",
                "description": "Prioritize ingredient selection by packingWeight",
                "width": 200,
            },
            "pickRandPt": {
                "name": "pickRandPt",
                "value": True,
                "default": True,
                "type": "bool",
                "description": "Pick drop position point randomly",
                "width": 200,
            },
            # gradient
            "ingrLookForNeighbours": {
                "name": "ingrLookForNeighbours",
                "value": False,
                "default": False,
                "type": "bool",
                "description": "Look for ingredients attractor and partner",
                "width": 30,
            },
            # debug with timer function
            "_timer": {
                "name": "_timer",
                "value": False,
                "default": False,
                "type": "bool",
                "description": "evaluate time per function",
                "width": 30,
            },
            "_hackFreepts": {
                "name": "_hackFreepts",
                "value": False,
                "default": False,
                "type": "bool",
                "description": "no free point update",
                "width": 30,
            },
            "freePtsUpdateThreshold": {
                "name": "freePtsUpdateThreshold",
                "value": 0.0,
                "default": 0.0,
                "type": "float",
                "description": "Mask grid while packing (0=always | 1=never)",
                "mini": 0.0,
                "maxi": 1.0,
                "width": 30,
            },
            "use_periodicity": {
                "name": "use_periodicity",
                "value": False,
                "default": False,
                "type": "bool",
                "description": "Use periodic condition",
                "width": 200,
            },
        }
        self.setDefaultOptions()

    def Setup(self, setupfile):
        # parse the given fill for
        # 1-fillin option
        # 2-recipe
        # use XML with tag description of the setup:
        # filling name root
        # Environment option
        # cytoplasme recipe if any and its ingredient
        # compartment name= mesh ?
        # orga surfaceingr#file or direct
        # orga interioringr#file or direct
        # etc...
        pass

    def setSeed(self, seedNum):
        SEED = int(seedNum)
        numpy.random.seed(SEED)  # for gradient
        seed(SEED)
        self.randomRot.setSeed(seed=SEED)
        self.seed_set = True
        self.seed_used = SEED

    def reportprogress(self, label=None, progress=None):
        if self.afviewer is not None and hasattr(self.afviewer, "vi"):
            self.afviewer.vi.progressBar(progress=progress, label=label)

    def makeIngredient(self, **kw):
        """
        Helper function to make an ingredient, pass all arguments as keywords.
        """
        from autopack.Ingredient import (
            SingleSphereIngr,
            MultiSphereIngr,
            SingleCubeIngr,
        )
        from autopack.Ingredient import MultiCylindersIngr, GrowIngredient

        ingr = None

        if kw["Type"] == "SingleSphere":
            kw["position"] = kw["positions"][0][0]
            kw["radius"] = kw["radii"][0][0]
            del kw["positions"]
            del kw["radii"]
            ingr = SingleSphereIngr(**kw)
        elif kw["Type"] == "MultiSphere":
            ingr = MultiSphereIngr(**kw)
        elif kw["Type"] == "MultiCylinder":
            ingr = MultiCylindersIngr(**kw)
        elif kw["Type"] == "SingleCube":
            kw["positions"] = [
                [
                    [0, 0, 0],
                    [0, 0, 0],
                    [0, 0, 0],
                ]
            ]
            kw["positions2"] = None
            ingr = SingleCubeIngr(**kw)
        elif kw["Type"] == "Grow":
            ingr = GrowIngredient(**kw)
        elif kw["Type"] == "Actine":
            ingr = ActinIngredient(**kw)
        if "gradient" in kw and kw["gradient"] != "" and kw["gradient"] != "None":
            ingr.gradient = kw["gradient"]
        return ingr

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
            if ingr.Type == "Grow":
                ingr.prepare_alternates()
        if ingr.excluded_partners_name:
            for iname in ingr.excluded_partners_name:
                ingr.addExcludedPartner(iname)
        ingr.histoVol = self

    def set_recipe_ingredient(self, xmlnode, recipe, io_ingr):
        # get the defined ingredient
        ingrnodes = xmlnode.getElementsByTagName("ingredient")
        for ingrnode in ingrnodes:
            ingre = io_ingr.makeIngredientFromXml(inode=ingrnode, recipe=self.name)
            if ingre:
                recipe.addIngredient(ingre)
            else:
                print(
                    "PROBLEM creating ingredient from ",
                    ingrnode,
                )
            # check for includes
        ingrnodes_include = xmlnode.getElementsByTagName("include")
        for inclnode in ingrnodes_include:
            xmlfile = str(inclnode.getAttribute("filename"))
            ingre = io_ingr.makeIngredientFromXml(filename=xmlfile, recipe=self.name)
            if ingre:
                recipe.addIngredient(ingre)
            else:
                print("PROBLEM creating ingredient from ", ingrnode)
            # look for overwritten attribute

    def load_recipe(self, setupfile):
        if setupfile is None:
            setupfile = self.setupfile
        else:
            self.setupfile = setupfile
        # check the extension of the filename none, txt or json
        fileName, fileExtension = os.path.splitext(setupfile)
        if fileExtension == ".xml":
            return IOutils.load_XML(self, setupfile)
        elif fileExtension == ".py":  # execute ?
            return IOutils.load_Python(self, setupfile)
        elif fileExtension == ".json":
            return IOutils.load_Json(self, setupfile)
        else:
            print("can't read or recognize " + setupfile)
            return None
        return None

    def loadRecipeString(self, astring):
        return IOutils.load_JsonString(self, astring)

    def saveRecipe(
        self,
        setupfile,
        useXref=None,
        format_output="json",
        mixed=False,
        kwds=None,
        result=False,
        grid=False,
        packing_options=False,
        indent=False,
        quaternion=False,
        transpose=False,
    ):
        #        if result :
        #            self.collectResultPerIngredient()
        if useXref is None:
            useXref = self.useXref
        if format_output == "json":
            if mixed:
                IOutils.save_Mixed_asJson(
                    self,
                    setupfile,
                    useXref=useXref,
                    kwds=kwds,
                    result=result,
                    indent=indent,
                    grid=grid,
                    packing_options=packing_options,
                    quaternion=quaternion,
                    transpose=transpose,
                )
            else:
                IOutils.save_asJson(self, setupfile, useXref=useXref, indent=indent)
        elif format_output == "xml":
            IOutils.save_asXML(self, setupfile, useXref=useXref)
        elif format_output == "python":
            IOutils.save_asPython(self, setupfile, useXref=useXref)
        else:
            print(
                "format output " + format_output + " not recognized (json,xml,python)"
            )

    def saveNewRecipe(self, filename):
        from autopack.IOutils import serializedRecipe, saveResultBinary

        djson, all_pos, all_rot = serializedRecipe(
            self, False, True
        )  # transpose, use_quaternion, result=False, lefthand=False
        with open(filename + "_serialized.json", "w") as f:
            f.write(djson)
        saveResultBinary(self, filename + "_serialized.bin", False, True, lefthand=True)
        saveResultBinary(
            self, filename + "_serialized_tr.bin", True, True, lefthand=True
        )  # transpose, quaternio, left hand

    def loadResult(
        self, resultfilename=None, restore_grid=True, backward=False, transpose=True
    ):
        result = [], [], []
        if resultfilename is None:
            resultfilename = self.resultfile
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
            #            o.molecules = []
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

    def setDefaultOptions(self):
        """reset all the options to their default values"""
        for options in self.OPTIONS:
            if options == "gradients":
                continue
            setattr(self, options, self.OPTIONS[options]["default"])

    def callFunction(self, function, args=[], kw={}):
        """
        helper function to callback another function with the
        given arguments and keywords.
        Optionally time stamp it.
        """
        if self._timer:
            res = self.timeFunction(function, args, kw)
        else:
            if len(kw):
                res = function(*args, **kw)
            else:
                res = function(*args)
        return res

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

        t1 = time.time()
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
        """write self.gridPtId and self.distToClosestSurf to file. (pickle)"""
        pickle.dump(self.grid.masterGridPositions, f)
        pickle.dump(self.grid.gridPtId, f)
        pickle.dump(self.grid.distToClosestSurf, f)

    def readArraysFromFile(self, f):
        """write self.gridPtId and self.distToClosestSurf to file. (pickle)"""
        pos = pickle.load(f)
        self.grid.masterGridPositions = pos

        id = pickle.load(f)
        # assert len(id)==len(self.gridPtId)
        self.grid.gridPtId = id

        dist = pickle.load(f)
        # assert len(dist)==len(self.distToClosestSurf)
        self.grid.distToClosestSurf_store = self.grid.distToClosestSurf[:]
        if len(dist):
            self.grid.distToClosestSurf = dist  # grid+organelle+surf
        self.grid.freePoints = list(range(len(id)))

    def saveGridToFile(self, gridFileOut):
        """
        Save the current grid and the compartment grid information in a file. (pickle)
        """
        d = os.path.dirname(gridFileOut)
        if not os.path.exists(d):
            print("gridfilename path problem", gridFileOut)
            return
        f = open(gridFileOut, "wb")  # 'w'
        self.writeArraysToFile(f)  # save self.gridPtId and self.distToClosestSurf

        for compartment in self.compartments:
            compartment.saveGridToFile(f)
        f.close()

    def restoreGridFromFile(self, gridFileName):
        """
        Read and setup the grid from the given filename. (pickle)
        """
        #        from bhtree import bhtreelib
        from scipy import spatial

        aInteriorGrids = []
        aSurfaceGrids = []
        f = open(gridFileName, "rb")
        self.readArraysFromFile(f)  # read gridPtId and distToClosestSurf
        for compartment in self.compartments:
            compartment.readGridFromFile(f)
            aInteriorGrids.append(compartment.insidePoints)
            aSurfaceGrids.append(compartment.surfacePoints)
            compartment.OGsrfPtsBht = spatial.cKDTree(
                tuple(compartment.vertices), leafsize=10
            )
            compartment.computeVolumeAndSetNbMol(
                self, compartment.surfacePoints, compartment.insidePoints, areas=None
            )
        f.close()
        self.grid.aInteriorGrids = aInteriorGrids
        self.grid.aSurfaceGrids = aSurfaceGrids

    def setMinMaxProteinSize(self):
        """
        Retrieve and store mini and maxi ingredient size
        """
        self.smallestProteinSize = 999999
        self.largestProteinSize = 0
        for compartment in self.compartments:
            mini, maxi = compartment.getMinMaxProteinSize()
            if mini < self.smallestProteinSize:
                self.computeGridParams = True
                self.smallestProteinSize = mini

            if maxi > self.largestProteinSize:
                self.computeGridParams = True
                self.largestProteinSize = maxi

        if self.exteriorRecipe:
            smallest, largest = self.exteriorRecipe.getMinMaxProteinSize()

            if smallest < self.smallestProteinSize:
                self.smallestProteinSize = smallest

            if largest > self.largestProteinSize:
                self.largestProteinSize = largest

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

    def addCompartment(self, compartment):
        """
        Add the given compartment to the environment.
        Extend the main bounding box if needed
        """
        compartment.setNumber(self.nbCompartments)
        self.nbCompartments += 1

        fits, bb = compartment.inBox(self.boundingBox)

        if not fits:
            self.boundingBox = bb
        CompartmentList.addCompartment(self, compartment)

    def getPointCompartmentId(self, point, ray=3):
        # check if point inside  of the compartments
        # closest grid point is
        d, pid = self.grid.getClosestGridPoint(point)
        cid = self.grid.gridPtId[pid]
        return cid
        ncomp = len(self.compartments)
        if ncomp:
            comp = ncomp
            for i in range(ncomp):
                inside = self.compartments[comp - 1].checkPointInside_rapid(
                    point, self.grid.diag, ray=ray
                )
                if inside:
                    return -(comp)
                comp = comp - 1
            # the point is not inside , is it on the surface ? ie distance to surface < X?
            for i in range(ncomp):
                distance, nb = self.compartments[i].OGsrfPtsBht.query(point)
                if distance < 1.0:
                    return i + 1
        return 0

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
        Build the comparmtents grid (intrior and surface points) to be merged with the main grid
        """
        aInteriorGrids = []
        aSurfaceGrids = []
        # thread ?
        for compartment in self.compartments:
            if autopack.verbose:
                print(
                    "in Environment, compartment.isOrthogonalBoundingBox =",
                    compartment.isOrthogonalBoundingBox,
                )
            a, b = compartment.BuildGrid(self)  # return inside and surface point
            aInteriorGrids.append(a)
            aSurfaceGrids.append(b)

        self.grid.aInteriorGrids = aInteriorGrids
        self.grid.aSurfaceGrids = aSurfaceGrids
        if autopack.verbose:
            print("I'm out of the loop and have build my grid with inside points")
            print("build Grids", self.innerGridMethod, len(self.grid.aSurfaceGrids))

    def buildGrid(
        self,
        boundingBox=None,
        gridFileIn=None,
        rebuild=True,
        gridFileOut=None,
        previousFill=False,
        previousfreePoint=None,
        lookup=2,
    ):
        """
        The main build grid function. Setup the main grid and merge the
        compartment grid. The setup is de novo or using previously builded grid
        or restored using given file.
        """
        if self.use_halton:
            from cellpack.autopack.Grid import HaltonGrid as Grid
        elif self.innerGridMethod == "floodfill":
            from cellpack.autopack.Environment import Grid
        else:
            from cellpack.autopack.Grid import Grid
        # check viewer, and setup the progress bar
        self.reportprogress(label="Building the Master Grid")
        if self.smallestProteinSize == 0:
            # compute it automatically
            self.setMinMaxProteinSize()
        # get and test the bounding box
        if boundingBox is None:
            boundingBox = self.boundingBox
        else:
            assert len(boundingBox) == 2
            assert len(boundingBox[0]) == 3
            assert len(boundingBox[1]) == 3
        self.sortIngredient(reset=rebuild)
        self.reportprogress(label="Computing the number of grid points")
        if gridFileIn is not None:
            if not os.path.isfile(gridFileIn):
                gridFileIn = None
        if self.nFill == 0:
            rebuild = True
        if rebuild or gridFileIn is not None or self.grid is None or self.nFill == 0:
            # save bb for current fill
            print("####BUILD GRID - step ", self.smallestProteinSize)
            self.fillBB = boundingBox
            self.grid = Grid(
                boundingBox=boundingBox, space=self.smallestProteinSize, lookup=lookup
            )
            nbPoints = self.grid.gridVolume
            if autopack.verbose:
                print("new Grid with  ", boundingBox, self.grid.gridVolume)
            if rebuild:
                self.grid.distToClosestSurf_store = self.grid.distToClosestSurf[:]
                nbPoints = self.grid.gridVolume
        else:
            if autopack.verbose:
                print("$$$$$$$$  reset the grid")
            self.grid.reset()
            nbPoints = len(self.grid.freePoints)
            if autopack.verbose:
                print("$$$$$$$$  reset the grid")
        if autopack.verbose:
            print(
                "$$$$$$$$  gridVolume = nbPoints = ",
                nbPoints,
                " grid.nbGridPoints = ",
                self.grid.nbGridPoints,
            )

        if gridFileIn is not None:  # and not rebuild:
            if autopack.verbose:
                print("file in for building grid but it doesnt work well")
            self.grid.filename = gridFileIn
            if self.nFill == 0:  # first fill, after we can just reset
                print("restore from file")
                self.restoreGridFromFile(gridFileIn)
        elif (gridFileIn is None and rebuild) or self.nFill == 0:
            # assign ids to grid points
            if autopack.verbose:
                print("file is None thus re/building grid distance")
            self.BuildCompartmentsGrids()
            self.exteriorVolume = self.grid.computeExteriorVolume(
                compartments=self.compartments,
                space=self.smallestProteinSize,
                fbox_bb=self.fbox_bb,
            )
        else:
            print("file is not rebuild nor restore from file")
        if len(self.compartments):
            verts = numpy.array(self.compartments[0].surfacePointsCoords)
            for i in range(1, len(self.compartments)):
                verts = numpy.vstack([verts, self.compartments[i].surfacePointsCoords])
            self.grid.set_surfPtsBht(
                verts.tolist()
            )  # should do it only on inside grid point
        if gridFileOut is not None and gridFileIn is None:
            self.saveGridToFile(gridFileOut)
            self.grid.filename = gridFileOut
        r = self.exteriorRecipe
        if r:
            r.setCount(self.exteriorVolume)  # should actually use the fillBB
        if not rebuild:
            # self.grid.distToClosestSurf = self.grid.distToClosestSurf_store[:]
            for c in self.compartments:
                c.setCount()
        else:
            self.grid.distToClosestSurf_store = self.grid.distToClosestSurf[:]
        print("file is not rebuild nor restore from file")
        if self.use_gradient and len(self.gradients) and rebuild:
            for g in self.gradients:
                self.gradients[g].buildWeigthMap(
                    boundingBox, self.grid.masterGridPositions
                )
        if previousFill:
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
        self.setCompatibility()

    def BuildGrids(self):
        """
        Build the comparmtents grid (intrior and surface points) to be merged with the main grid
        Note :
        #New version allows for orthogonal box to be used as an organelle requireing no expensive InsidePoints test
        # FIXME make recursive?
        """
        aInteriorGrids = []
        aSurfaceGrids = []
        a = []
        b = []
        for compartment in self.compartments:
            print(
                "in Environment, compartment.isOrthogonalBoundingBox =",
                compartment.isOrthogonalBoundingBox,
            )
            b = []
            if compartment.isOrthogonalBoundingBox == 1:
                self.EnviroOnly = True
                print(
                    ">>>>>>>>>>>>>>>>>>>>>>>>> Not building a grid because I'm an Orthogonal Bounding Box"
                )
                a = self.grid.getPointsInCube(
                    compartment.bb, None, None
                )  # This is the highspeed shortcut for inside points! and no surface! that gets used if the fillSelection is an orthogonal box and there are no other compartments.
                self.grid.gridPtId[a] = -compartment.number
                compartment.surfacePointsCoords = None
                bb0x, bb0y, bb0z = compartment.bb[0]
                bb1x, bb1y, bb1z = compartment.bb[1]
                AreaXplane = (bb1y - bb0y) * (bb1z - bb0z)
                AreaYplane = (bb1x - bb0x) * (bb1z - bb0z)
                AreaZplane = (bb1y - bb0y) * (bb1x - bb0x)
                vSurfaceArea = (
                    abs(AreaXplane) * 2 + abs(AreaYplane) * 2 + abs(AreaZplane) * 2
                )
                print("vSurfaceArea = ", vSurfaceArea)
                compartment.insidePoints = a
                compartment.surfacePoints = b
                compartment.surfacePointsCoords = []
                compartment.surfacePointsNormals = []
                print(
                    " %d inside pts, %d tot grid pts, %d master grid"
                    % (len(a), len(a), len(self.grid.masterGridPositions))
                )
                compartment.computeVolumeAndSetNbMol(self, b, a, areas=vSurfaceArea)
                print("The size of the grid I build = ", len(a))

            if (
                self.innerGridMethod == "sdf"
                and compartment.isOrthogonalBoundingBox != 1
            ):  # A fillSelection can now be a mesh too... it can use either of these methods
                a, b = compartment.BuildGrid_utsdf(
                    self
                )  # to make the outer most selection from the master and then the compartment
            elif (
                self.innerGridMethod == "bhtree"
                and compartment.isOrthogonalBoundingBox != 1
            ):  # surfaces and interiors will be subtracted from it as normal!
                a, b = compartment.BuildGrid(self)
            elif (
                self.innerGridMethod == "jordan"
                and compartment.isOrthogonalBoundingBox != 1
            ):  # surfaces and interiors will be subtracted from it as normal!
                a, b = compartment.BuildGrid_jordan(self)
            elif (
                self.innerGridMethod == "jordan3"
                and compartment.isOrthogonalBoundingBox != 1
            ):  # surfaces and interiors will be subtracted from it as normal!
                a, b = compartment.BuildGrid_jordan(self, ray=3)
            elif (
                self.innerGridMethod == "pyray"
                and compartment.isOrthogonalBoundingBox != 1
            ):  # surfaces and interiors will be subtracted from it as normal!
                a, b = compartment.BuildGrid_pyray(self)
            elif (
                self.innerGridMethod == "floodfill"
                and compartment.isOrthogonalBoundingBox != 1
            ):  # surfaces and interiors will be subtracted from it as normal!
                a, b = compartment.BuildGrid_kevin(self)
            elif (
                self.innerGridMethod == "binvox"
                and compartment.isOrthogonalBoundingBox != 1
            ):  # surfaces and interiors will be subtracted from it as normal!
                a, b = compartment.BuildGrid_binvox(self)
            elif (
                self.innerGridMethod == "trimesh"
                and compartment.isOrthogonalBoundingBox != 1
            ):  # surfaces and interiors will be subtracted from it as normal!
                a, b = compartment.BuildGrid_trimesh(self)
            elif (
                self.innerGridMethod == "scanline"
                and compartment.isOrthogonalBoundingBox != 1
            ):  # surfaces and interiors will be subtracted from it as normal!
                a, b = compartment.BuildGrid_scanline(self)

            aInteriorGrids.append(a)
            print("I'm ruther in the loop")
            aSurfaceGrids.append(b)

        self.grid.aInteriorGrids = aInteriorGrids
        print("I'm out of the loop and have build my grid with inside points")
        self.grid.aSurfaceGrids = aSurfaceGrids
        print("build Grids", self.innerGridMethod, len(self.grid.aSurfaceGrids))

    def buildGridOld(
        self,
        boundingBox=None,
        gridFileIn=None,
        rebuild=True,
        gridFileOut=None,
        previousFill=False,
        previousfreePoint=None,
    ):
        """
        The main build grid function. Setup the main grid and merge the
        compartment grid. The setup is de novo or using previously builded grid
        or restored using given file. This funcion should be
        split in smaller function for clarity.
        """
        if self.afviewer is not None and hasattr(self.afviewer, "vi"):
            self.afviewer.vi.progressBar(label="Building the Master Grid")
        if boundingBox is None:
            boundingBox = self.boundingBox
        else:
            assert len(boundingBox) == 2
            assert len(boundingBox[0]) == 3
            assert len(boundingBox[1]) == 3
        # make sure all recipes are sorted from large to small radius
        if self.exteriorRecipe:
            self.exteriorRecipe.sort()

        for o in self.compartments:
            o.molecules = []
            if rebuild:
                o.reset()
            if o.innerRecipe:
                o.innerRecipe.sort()
            if o.surfaceRecipe:
                o.surfaceRecipe.sort()

        if self.afviewer is not None and hasattr(self.afviewer, "vi"):
            self.afviewer.vi.progressBar(label="Computing the number of grid points")
        if rebuild or gridFileIn is not None:
            # save bb for current fill
            self.fillBB = boundingBox
            grid = Grid()
            self.grid = grid
            grid.boundingBox = boundingBox
            # compute grid spacing
            grid.gridSpacing = space = self.smallestProteinSize * 1.1547  # 2/sqrt(3)
            print("$$$$$$$$  ", boundingBox, space, self.smallestProteinSize)
            grid.gridVolume, grid.nbGridPoints = self.callFunction(
                grid.computeGridNumberOfPoint, (boundingBox, space)
            )
        grid = self.grid
        nbPoints = self.grid.gridVolume
        print(
            "$$$$$$$$  gridVolume = nbPoints = ",
            nbPoints,
            " grid.nbGridPoints = ",
            self.grid.nbGridPoints,
        )
        # compute 3D point coordiantes for all grid points
        if rebuild or gridFileIn is not None:
            self.callFunction(
                grid.create3DPointLookup
            )  # generate grid.masterGridPositions
            grid.nbSurfacePoints = 0
            # self.isFree = numpy.ones( (nbPoints,), 'i') # Will never shrink
            # Id is set set to None initially
            grid.gridPtId = numpy.zeros(nbPoints)  # [0]*nbPoints

        xl, yl, zl = boundingBox[0]
        xr, yr, zr = boundingBox[1]
        # distToClosestSurf is set to self.diag initially
        self.grid.diag = diag = vlen(vdiff((xr, yr, zr), (xl, yl, zl)))
        if rebuild or gridFileIn is not None:
            self.grid.distToClosestSurf = [diag] * nbPoints  # surface point too?
            self.grid.distToClosestSurf = numpy.array(self.grid.distToClosestSurf)
            self.grid.freePoints = list(range(nbPoints))
        else:
            # just reset
            self.grid.distToClosestSurf = [diag] * len(
                self.grid.distToClosestSurf
            )  # surface point too?
            self.grid.distToClosestSurf = numpy.array(self.grid.distToClosestSurf)
            self.grid.freePoints = list(range(len(self.grid.freePoints)))
            nbPoints = len(self.grid.freePoints)
        #        print 'DIAG', diag,self.grid.distToClosestSurf
        self.grid.distToClosestSurf_store = self.grid.distToClosestSurf[:]
        #        if gridFileIn is None :
        #            gridFileIn = self.grid_filename
        #        if gridFileOut is None :
        #            gridFileOut= self.grid_filename
        #        if self.grid_filename is not None and not os.path.isfile(self.grid_filename):
        #            gridFileIn = None

        #        if rebuild :
        # this restore/store the grid information of the organelle.
        if gridFileIn is not None:  # and not rebuild:
            print("file in for building grid but it doesnt work well")
            self.grid.filename = gridFileIn
            if self.nFill == 0:  # ?:
                print("restore from file")
                self.restoreGridFromFile(gridFileIn)
        elif gridFileIn is None and rebuild:
            # assign ids to grid points
            print("file is None for building grid")
            self.BuildGrids()
        else:
            print("file is not rebuild")
        if gridFileOut is not None:
            self.saveGridToFile(gridFileOut)
            self.grid.filename = gridFileOut
            # get new set of freePoints which includes surface points
            #       nbPoints = nbPoints-1            #Graham Turned off this redundant nbPoints-1 call on 8/27/11
            #       nbPoints = nbPoints-1          #Graham Turned this one off on 5/16/12 to match August repair in Hybrid
        grid.nbFreePoints = nbPoints  # -1
        grdPts = grid.masterGridPositions
        grid.nbFreePoints = len(grdPts)
        # build BHTree for surface points (off grid)
        if rebuild:
            verts = []
            for orga in self.compartments:
                if orga.surfacePointsCoords:
                    for pt3d in orga.surfacePointsCoords:
                        verts.append(pt3d)

            from bhtree import bhtreelib

            grid.surfPtsBht = None
            if verts:
                grid.surfPtsBht = bhtreelib.BHtree(verts, None, 10)

        # build list of compartments without a recipe#????
        noRecipe = []
        if self.exteriorRecipe is None:
            noRecipe.append(0)
        for o in self.compartments:
            if o.surfaceRecipe is None:
                noRecipe.append(o.number)
            if o.innerRecipe is None:
                noRecipe.append(-o.number)

        # compute exterior volume
        unitVol = grid.gridSpacing ** 3
        totalVolume = grid.gridVolume * unitVol
        if self.fbox_bb is not None:
            V, nbG = self.callFunction(
                grid.computeGridNumberOfPoint, (self.fbox_bb, space)
            )
            totalVolume = V * unitVol
        for o in self.compartments:
            # totalVolume -= o.surfaceVolume
            totalVolume -= o.interiorVolume
        self.exteriorVolume = totalVolume

        r = self.exteriorRecipe
        if r:
            r.setCount(totalVolume)  # should actually use the fillBB

        if self.use_gradient and len(self.gradients) and rebuild:
            for g in self.gradients:
                self.gradients[g].buildWeigthMap(boundingBox, grid.masterGridPositions)
        if not rebuild:
            self.grid.distToClosestSurf = self.grid.distToClosestSurf_store[:]
        else:
            self.grid.distToClosestSurf_store = self.grid.distToClosestSurf[:]

            # we should be able here to update the number of free point using a
            # previous grid overlap
        if previousFill:  # actually if there is a previous fill
            # get the intersecting point and update freePoints from this one if they
            # are not free previousfreePoint
            # compute the intersection bounding box and get ptindice for both grid
            # by getPointsInCube
            # check which one are in freePoints from previous,
            # and update the current one
            # update the curentpass
            #            #how to update the distance for each prest ingr ?
            distance = self.grid.distToClosestSurf  # [:]
            nbFreePoints = nbPoints
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
        self.setCompatibility()

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
        dpad = ingr.minRadius + mr + jitter
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
        if len(insidePoints) and self.placeMethod.find("panda") != -1:
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
        # (self, histoVol,insidePoints, newDistPoints, freePoints,
        #        nbFreePoints, distance, masterGridPositions, verbose)
        # doesnt seem to work properly...
        nbFreePoints = ingr.updateDistances(
            self,
            insidePoints,
            newDistPoints,
            self.grid.freePoints,
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
        #        else :
        #            nmol = len(self.molecules)
        #            for j,organelle in enumerate(self.organelles):
        #                print (i,nmol+len(organelle.molecules))
        #                if i < nmol+len(organelle.molecules):
        #                    organelle.molecules[i-nmol][3]=insidePoints.keys()[0]
        #                    ingr.rbnode[insidePoints.keys()[0]] = rbnode
        #                else :
        #                    nmol+=len(organelle.molecules)

    def setCompatibility(self):
        """
        in earlier version the grid was part of the environment class.
        Since we split the grid in her own class, to avoid some error during the transition
        we alias all the function and attribute.
        """
        self.getPointsInCube = self.grid.getPointsInCube
        self.boundingBox = self.grid.boundingBox
        self.gridPtId = self.grid.gridPtId
        self.freePoints = self.grid.freePoints
        self.diag = self.grid.diag
        self.gridSpacing = self.grid.gridSpacing
        self.nbGridPoints = self.grid.nbGridPoints
        self.nbSurfacePoints = self.grid.nbSurfacePoints
        self.gridVolume = (
            self.grid.gridVolume
        )  # will be the toatl number of grid points
        self.masterGridPositions = self.grid.masterGridPositions
        self.aInteriorGrids = self.grid.aInteriorGrids
        self.aSurfaceGrids = self.grid.aSurfaceGrids
        self.surfPtsBht = self.grid.surfPtsBht
        self.gridPtId = self.grid.gridPtId = numpy.array(self.grid.gridPtId, int)

    def getSortedActiveIngredients(self, allIngredients, verbose=0):
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
        #     complexity. (currently complexity = minRadius), thus a more 'complex' ingredient
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
        ingr0 = []  # negative values will pack first in order of abs[packingPriority]
        priorities0 = []
        for ing in allIngredients:
            if ing.completion >= 1.0:
                continue  # ignore completed ingredients
            if ing.packingPriority is None or ing.packingPriority == 0:
                ingr2.append(ing)
                priorities2.append(ing.packingPriority)
            elif ing.packingPriority > 0:
                ingr1.append(ing)
                priorities1.append(ing.packingPriority)
            else:
                # ing.packingPriority    = -ing.packingPriority
                ingr0.append(ing)
                priorities0.append(ing.packingPriority)

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
            self.lowestPriority = lowestIng.packingPriority
        else:
            self.lowestPriority = 1.0
        if verbose:
            print("self.lowestPriority for Ing1 = ", self.lowestPriority)
        self.totalRadii = 0
        for radii in ingr2:
            if radii.modelType == "Cylinders":
                r = max(radii.length / 2.0, radii.minRadius)
            elif radii.modelType == "Spheres":
                r = radii.minRadius
            elif radii.modelType == "Cube":
                r = radii.minRadius
            self.totalRadii = self.totalRadii + r
            if verbose:
                print("self.totalRadii += ", r, "=", self.totalRadii)
            if r == 0:
                # safety
                self.totalRadii = self.totalRadii + 1.0

        self.normalizedPriorities0 = []
        for priors2 in ingr2:
            if priors2.modelType == "Cylinders":
                r = max(priors2.length / 2.0, priors2.minRadius)
            elif priors2.modelType == "Spheres":
                r = priors2.minRadius
            np = float(r) / float(self.totalRadii) * self.lowestPriority
            self.normalizedPriorities0.append(np)
            priors2.packingPriority = np
            if verbose:
                print("self.normalizedPriorities0 = ", self.normalizedPriorities0)
        activeIngr0 = ingr0  # +ingr1+ingr2  #cropped to 0 on 7/20/10

        if verbose:
            print("len(activeIngr0)", len(activeIngr0))
        activeIngr12 = ingr1 + ingr2
        if verbose:
            print("len(activeIngr12)", len(activeIngr12))
        packingPriorities = priorities0 + priorities1 + priorities2
        if verbose:
            print("priorities0 is ", priorities0)
            print("priorities1 is ", priorities1)
            print("priorities2 is ", priorities2)
            print("packingPriorities", packingPriorities)

        return activeIngr0, activeIngr12

    #    import fill3isolated # Graham cut the outdated fill3 from this document and put it in a separate file. turn on here if you want to use it.

    def updateIngr(self, ingr, completion=0.0, nbMol=0, counter=0):
        """helper function for updating the ingredient completion, nbmol and counter"""
        ingr.counter = counter
        ingr.nbMol = nbMol
        ingr.completion = completion

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
                if hasattr(
                    ingr, "allIngrPts"
                ):  # Graham here on 5/16/12 are these two lines safe?
                    del (
                        ingr.allIngrPts
                    )  # Graham here on 5/16/12 are these two lines safe?
                if hasattr(ingr, "isph"):
                    ingr.isph = None
                if hasattr(ingr, "icyl"):
                    ingr.icyl = None
                if hasattr(ingr, "allIngrPts"):
                    delattr(ingr, "allIngrPts")
                #                if hasattr(ingr,"rb_nodes"):
                #                    for node in ingr.rb_nodes:
                #                        self.delRB(node)
                #                    ingr.rb_nodes=[]
            for ingr in recip.exclude:
                ingr.start_positions = []
                ingr.prev_alt = None
                ingr.results = []
                ingr.firstTimeUpdate = True
                ingr.counter = 0
                ingr.rejectionCounter = 0
                ingr.completion = 0.0
                if hasattr(
                    ingr, "allIngrPts"
                ):  # Graham here on 5/16/12 are these two lines safe?
                    del ingr.allIngrPts
                if hasattr(ingr, "isph"):
                    ingr.isph = None
                if hasattr(ingr, "icyl"):
                    ingr.icyl = None
                if hasattr(ingr, "allIngrPts"):
                    delattr(ingr, "allIngrPts")
                #                if hasattr(ingr,"rb_nodes"):
                #                    for node in ingr.rb_nodes:
                #                        self.delRB(node)
                #                    ingr.rb_nodes=[]

    def resetIngr(self, ingr):
        """Reset the given ingredient (count, completion, nmol)"""
        ingr.counter = 0
        ingr.nbMol = 0
        ingr.completion = 0.0

    def getActiveIng(self):
        """Return all remaining active ingredients"""
        allIngredients = []
        r = self.exteriorRecipe
        if r is not None:
            if not hasattr(r, "molecules"):
                r.molecules = []
        if r:
            for ingr in r.ingredients:
                ingr.counter = 0  # counter of placed molecules
                if ingr.nbMol > 0:  # I DONT GET IT !
                    ingr.completion = 0.0
                    allIngredients.append(ingr)
                else:
                    ingr.completion = 1.0

        for o in self.compartments:
            if not hasattr(o, "molecules"):
                o.molecules = []
            r = o.surfaceRecipe
            if r:
                for ingr in r.ingredients:
                    ingr.counter = 0  # counter of placed molecules
                    if ingr.nbMol > 0:
                        ingr.completion = 0.0
                        allIngredients.append(ingr)
                    else:
                        ingr.completion = 1.0

            r = o.innerRecipe
            if r:
                for ingr in r.ingredients:
                    ingr.counter = 0  # counter of placed molecules
                    #                    print "nbMol",ingr.nbMol
                    if ingr.nbMol > 0:
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
            # if verbose:
            #    print "random in activeIngr"
            r = random()  # randint(0, len(self.activeIngr)-1)#random()
            # n=int(r*(len(self.activeIngr)-1))
            n = int(r * len(self.activeIngr))
            ingr = self.activeIngr[n]
        #            print (r,n,ingr.name,len(self.activeIngr)) #Graham turned back on 5/16/12, but may be costly
        return ingr

    def get_dpad(self, compNum):
        """Return the largest encapsulatingRadius and use it for padding"""
        mr = 0.0
        if compNum == 0:  # cytoplasm -> use cyto and all surfaces
            for ingr1 in self.activeIngr:
                if ingr1.compNum >= 0:
                    r = ingr1.encapsulatingRadius
                    if r > mr:
                        mr = r
        else:
            for ingr1 in self.activeIngr:
                if ingr1.compNum == compNum or ingr1.compNum == -compNum:
                    r = ingr1.encapsulatingRadius
                    if r > mr:
                        mr = r
        return mr

    def checkIfUpdate(self, ingr, nbFreePoints, verbose=False):
        """Check if we need to update the distance array. Part of the hack free points"""
        if hasattr(ingr, "nbPts"):
            if hasattr(ingr, "firstTimeUpdate") and not ingr.firstTimeUpdate:
                ratio = float(ingr.nbPts) / float(nbFreePoints)
                if verbose:
                    print(
                        "checkIfUpdate: ratio = ",
                        ratio,
                        "nbFreePoints = ",
                        nbFreePoints,
                        "ingr.nbPts = ",
                        ingr.nbPts,
                    )
                if ratio > self.freePtsUpdateThreshold:
                    return True
                else:
                    if ingr.haveBeenRejected and ingr.rejectionCounter > 5:
                        ingr.haveBeenRejected = False
                        return True
                    # do we check to total freepts? or crowded state ?
                    else:
                        return False
            else:
                ingr.firstTimeUpdate = False
                return True
        else:
            return True

    def getPointToDrop(
        self,
        ingr,
        radius,
        jitter,
        freePoints,
        nbFreePoints,
        distance,
        compId,
        compNum,
        vRangeStart,
        vThreshStart,
        verbose=False,
    ):
        """
        Decide next point to use for dropping a given ingredent. The picking can be
        random, based on closest distance, based on gradients, ordered.
        This function also update the available free point except when hack is on.
        """
        verbose = autopack.verbose
        radius = ingr.encapsulatingRadius
        if ingr.packingMode == "close":
            allIngrPts = []
            allIngrDist = []
            if ingr.modelType == "Cylinders" and ingr.useLength:
                cut = ingr.length  # - jitter
            #            if ingr.modelType=='Cube' : #radius iactually the size
            #                cut = min(self.radii[0]/2.)-jitter
            #            elif ingr.cutoff_boundary is not None :
            #                #this may work if we have the distance from the border
            #                cut  = radius+ingr.cutoff_boundary-jitter
            else:
                cut = radius  # - jitter
            alld = numpy.array(distance)[freePoints]
            mask = numpy.logical_and(
                numpy.less_equal(alld, cut), numpy.greater_equal(alld, cut * 0.5)
            )
            # mask_ind = numpy.nonzero(mask)[0]
            # mask compartments Id as well
            mask_comp = numpy.array(compId)[freePoints] == compNum
            mask_ind = numpy.nonzero(numpy.logical_and(mask, mask_comp))[0]
            allIngrPts = numpy.array(freePoints)[mask_ind].tolist()
            allIngrDist = numpy.array(distance)[mask_ind].tolist()
            # for pt in freePoints:  # [:nbFreePoints]:
            #    d = distance[pt]  # look up the distance
            #    if compId[pt] == compNum and d >= cut:
            #        allIngrPts.append(pt)
            #        allIngrDist.append(d)
            # if verbose > 1:
            #    print("time to filter using for loop ", time() - t1)
        else:
            allIngrPts = []
            if ingr.modelType == "Cylinders" and ingr.useLength:
                cut = ingr.length - jitter
            else:
                cut = radius - jitter
            # for pt in freePoints[:nbFreePoints]:
            if verbose > 1:
                print("find grid point with distance >= ", cut)
            if hasattr(ingr, "allIngrPts") and self._hackFreepts:
                allIngrPts = ingr.allIngrPts
                if verbose > 1:
                    print("Running nofreepoint HACK")
            else:
                # use periodic update according size ration grid
                update = self.checkIfUpdate(ingr, nbFreePoints)
                if update:
                    if verbose > 1:
                        print("in update loop")
                    for i in range(nbFreePoints):
                        pt = freePoints[i]
                        d = distance[pt]
                        if compId[pt] == compNum and d >= cut:
                            allIngrPts.append(pt)
                    # allIngrDist.append(d)
                    ingr.allIngrPts = allIngrPts
                    ingr.cut = cut
                    if verbose:
                        print("getPointToDrop len(allIngrPts) = ", len(allIngrPts))
                else:
                    if hasattr(ingr, "allIngrPts"):
                        allIngrPts = ingr.allIngrPts
                    else:
                        allIngrPts = freePoints[:nbFreePoints]
                        ingr.allIngrPts = allIngrPts

        if verbose > 1:
            print("len (allIngrPts) = ", len(allIngrPts))
        if len(allIngrPts) == 0:
            t = time.time()
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
                self.getSortedActiveIngredients, (self.activeIngr, False)
            )
            if verbose > 1:
                print(
                    "No point left for ingredient %s %f minRad %.2f jitter %.3f in component %d"
                    % (ingr.name, ingr.molarity, radius, jitter, compNum)
                )
                print("len(allIngredients", len(self.activeIngr))
                print("len(self.activeIngr0)", len(self.activeIngr0))
                print("len(self.activeIngr12)", len(self.activeIngr12))
            self.activeIngre_saved = self.activeIngr[:]

            self.totalPriorities = 0  # 0.00001
            for priors in self.activeIngr12:
                pp = priors.packingPriority
                self.totalPriorities = self.totalPriorities + pp
                if verbose > 1:
                    print("totalPriorities = ", self.totalPriorities)
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
                pp = priors.packingPriority
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

            #            nls=0
            #            totalNumMols = 0
            #            for threshProb in self.thresholdPriorities:
            #                nameMe = self.activeIngr[nls]
            #                if verbose:
            #                    print ('threshprop Get Point is %f for ingredient: %s %s %d'%(threshProb, nameMe,nameMe.name,nameMe.nbMol))
            #                totalNumMols += nameMe.nbMol
            #                if verbose:
            #                    print ('totalNumMols Get Point= ', totalNumMols)
            #                nls+=1

            # print 'vThreshStart before = ', vThreshStart
            # vThreshStart = self.thresholdPriorities[0]
            # print 'vThreshStart after = ', vThreshStart
            # print 'because vself.thresholdPriorities[0] = ', self.thresholdPriorities[0]

            # self.thresholdPriorities.pop(ind)
            # self.normalizedPriorities.pop(ind)
            if verbose > 1:
                print("time to reject the picking", time.time() - t)
            # End of massive overruling section from corrected thesis file of Sept. 25, 2011
            # this chunk overwrites the next three lines from July version. July 5, 2012
            #            self.thresholdPriorities.pop(ind)
            #            self.normalizedPriorities.pop(ind)
            return False, vRangeStart

        if self.pickRandPt:
            if ingr.packingMode == "close":
                order = numpy.argsort(allIngrDist)
                # pick point with closest distance
                ptInd = allIngrPts[order[0]]
                # 5 rejection
                if ingr.rejectionCounter < len(order):
                    ptInd = allIngrPts[order[ingr.rejectionCounter]]
                else:
                    ptIndr = int(uniform(0.0, 1.0) * len(allIngrPts))
                    ptInd = allIngrPts[ptIndr]
                # if (ingr.rejectionCounter % 5) == 0:
                #      ptIndr = allIngrPts[order[1]]#int(random() * len(allIngrPts))
                #      ptInd = allIngrPts[ptIndr]
                # if ingr.rejectionCounter >= 50:
                #     ptIndr = int(uniform(0.0, 1.0) * len(allIngrPts))
                #     ptInd = allIngrPts[ptIndr]
            elif ingr.packingMode == "gradient" and self.use_gradient:
                # get the most probable point using the gradient
                # use the gradient weighted map and get mot probabl point
                if verbose > 1:
                    print("pick point from gradients", (len(allIngrPts)))
                ptInd = self.gradients[ingr.gradient].pickPoint(allIngrPts)
            else:
                # pick a point randomly among free points
                # random or uniform?
                ptIndr = int(uniform(0.0, 1.0) * len(allIngrPts))
                ptInd = allIngrPts[ptIndr]
            if ptInd is None:
                t = time.time()
                if verbose > 1:
                    print(
                        "No point left for ingredient %s %f minRad %.2f jitter %.3f in component %d"
                        % (ingr.name, ingr.molarity, radius, jitter, compNum)
                    )
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
                    print(("time to reject the picking", time.time() - t))
                    print(("vRangeStart", vRangeStart))
                return False, vRangeStart

        else:
            #            t3=time()
            allIngrPts.sort()
            ptInd = allIngrPts[0]
        return True, ptInd

    #    import fill4isolated # Graham cut the outdated fill4 from this document and put it in a separate file. turn on here if you want to use it.
    def removeOnePoint(self, pt, freePoints, nbFreePoints):
        try:
            # New system replaced by Graham on Aug 18, 2012
            nbFreePoints -= 1
            vKill = freePoints[pt]
            vLastFree = freePoints[nbFreePoints]
            freePoints[vKill] = vLastFree
            freePoints[vLastFree] = vKill
            # End New replaced by Graham on Aug 18, 2012
        except:  # noqa: E722
            pass
        return nbFreePoints

    def getTotalNbObject(self, allIngredients, update_partner=False):
        totalNbIngr = 0
        for ingr in allIngredients:
            if ingr.Type == "Grow":
                totalNbIngr += int(ingr.nbMol * (ingr.length / ingr.uLength))
            else:
                totalNbIngr += ingr.nbMol
            if update_partner:
                self.set_partners_ingredient(ingr)
        return totalNbIngr

    def pack_grid(
        self,
        seedNum=14,
        stepByStep=False,
        verbose=False,
        sphGeom=None,
        labDistGeom=None,
        debugFunc=None,
        name=None,
        vTestid=3,
        vAnalysis=0,
        **kw
    ):
        """
        the latest packing loop
        ## this packing should be able to continue from a previous one
        ## Fill the grid by picking an ingredient first and then
        ## find a suitable point using the ingredient's placer object
        """
        # set periodicity
        autopack.verbose = verbose
        autopack.testPeriodicity = self.use_periodicity
        self.grid.testPeriodicity = self.use_periodicity

        t1 = time.time()
        self.timeUpDistLoopTotal = 0  # Graham added to try to make universal "global variable Verbose" on Aug 28
        self.static = []
        if self.grid is None:
            if verbose > 1:
                print("no grid setup")
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
        # are added, theses array can be restored/saved before feeling
        freePoints = self.grid.freePoints[:]
        self.grid.nbFreePoints = nbFreePoints = len(freePoints)  # -1
        if "fbox" in kw:
            self.fbox = kw["fbox"]
        if self.fbox is not None and not self.EnviroOnly:
            self.freePointMask = numpy.ones(nbFreePoints, dtype="int32")
            bb_insidepoint = self.grid.getPointsInCube(self.fbox, [0, 0, 0], 1.0)[:]
            self.freePointMask[bb_insidepoint] = 0
            bb_outside = numpy.nonzero(self.freePointMask)
            self.grid.gridPtId[bb_outside] = 99999
        compId = self.grid.gridPtId
        # why a copy? --> can we split ?
        distance = self.grid.distToClosestSurf[:]

        spacing = self.smallestProteinSize

        # DEBUG stuff, should be removed later
        self.jitterVectors = []
        self.jitterLength = 0.0
        self.totnbJitter = 0
        self.maxColl = 0.0
        self.successfullJitter = []
        self.failedJitter = []

        # this function also depend on the ingr.completiion that can be restored ?
        self.activeIngr0, self.activeIngr12 = self.callFunction(
            self.getSortedActiveIngredients, (allIngredients, verbose)
        )

        if verbose > 1:
            print("len(allIngredients", len(allIngredients))
            print("len(self.activeIngr0)", len(self.activeIngr0))
            print("len(self.activeIngr12)", len(self.activeIngr12))
        self.activeIngre_saved = self.activeIngr[:]

        self.totalPriorities = 0  # 0.00001
        for priors in self.activeIngr12:
            pp = priors.packingPriority
            self.totalPriorities = self.totalPriorities + pp
            if verbose > 1:
                print("totalPriorities = ", self.totalPriorities)
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
            pp = priors.packingPriority
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

        nls = 0
        totalNumMols = 0
        self.totalNbIngr = self.getTotalNbObject(allIngredients, update_partner=True)
        if len(self.thresholdPriorities) == 0:
            for ingr in allIngredients:
                totalNumMols += ingr.nbMol
            if verbose > 1:
                print("totalNumMols pack_grid if = ", totalNumMols)
        else:
            for threshProb in self.thresholdPriorities:
                nameMe = self.activeIngr[nls]
                totalNumMols += nameMe.nbMol
                if verbose > 1:
                    print(
                        "threshprop pack_grid else is %f for ingredient: %s %s %d"
                        % (threshProb, nameMe, nameMe.name, nameMe.nbMol)
                    )
                    print("totalNumMols pack_grid else = ", totalNumMols)
                nls += 1

        vRangeStart = 0.0
        tCancelPrev = time.time()
        ptInd = 0

        PlacedMols = 0
        vThreshStart = 0.0  # Added back by Graham on July 5, 2012 from Sept 25, 2011 thesis version

        # if bullet build the organel rbnode
        if self.placeMethod == "pandaBullet":
            self.setupPanda()

        # if usePP:
        #     # deprecated in python 3
        #     import pp
        #     self.grab_cb = IOutils.GrabResult()
        #     self.pp_server = pp.Server(ncpus=autopack.ncpus)
        # ==============================================================================
        #         #the big loop
        # ==============================================================================
        dump_freq = self.dump_freq  # 120.0#every minute
        dump = self.dump
        stime = time.time()
        while nbFreePoints:
            if verbose > 1:
                print(
                    ".........At start of while loop, with vRangeStart = ", vRangeStart
                )
                print("Points Remaining", nbFreePoints, len(freePoints))
                print("len(self.activeIngr)", len(self.activeIngr))

            # breakin test
            if len(self.activeIngr) == 0:
                print("exit packing loop because of len****")
                if hasattr(self, "afviewer"):
                    if self.afviewer is not None and hasattr(self.afviewer, "vi"):
                        self.afviewer.vi.resetProgressBar()
                        self.afviewer.vi.progressBar(label="Filling Complete")
                break
            if vRangeStart > 1:
                print("exit packing loop because vRange and hence Done!!!****")
                break
            if self.cancelDialog:
                tCancel = time.time()
                if tCancel - tCancelPrev > 10.0:
                    cancel = self.displayCancelDialog()
                    if cancel:
                        print(
                            "canceled by user: we'll fill with current objects up to time",  # noqa: E510
                            tCancel,
                        )
                        break
                    # if OK, do nothing, i.e., continue loop
                    # (but not the function continue)
                    tCancelPrev = time.time()
            # pick an ingredient

            ingr = self.callFunction(self.pickIngredient, (vThreshStart,))
            if verbose > 1:
                print("picked Ingr ", ingr.name)
            if hasattr(self, "afviewer"):
                # C4D safety check added by Graham on July 10, 2012 until we can fix
                # the uPy status bar for C4D
                # if self.host == 'c4d':
                try:
                    import c4d

                    p = float(PlacedMols) / float(totalNumMols) * 100.0
                    c4d.StatusSetBar(int(p))
                    c4d.StatusSetText(ingr.name + " " + str(ingr.completion))

                except ImportError:
                    p = (
                        (float(PlacedMols)) / float(totalNumMols)
                    ) * 100.0  # This code shows 100% of ingredients all the time
                    if self.afviewer is not None and hasattr(self.afviewer, "vi"):
                        self.afviewer.vi.progressBar(
                            progress=int(p),
                            label=ingr.name + " " + str(ingr.completion),
                        )
                        if self.afviewer.renderDistance:
                            self.afviewer.vi.displayParticleVolumeDistance(
                                distance, self
                            )

            compNum = ingr.compNum
            radius = ingr.minRadius
            jitter = self.callFunction(ingr.getMaxJitter, (spacing,))

            # compute dpad which is the distance at which we need to update
            # distances after the drop is successfull
            mr = self.get_dpad(compNum)
            dpad = ingr.minRadius + mr + jitter

            if verbose > 2:
                print("picked Ingr radius compNum dpad", radius, compNum, dpad)

            # find the points that can be used for this ingredients
            ##
            res = [True, int(random() * len(freePoints))]
            if PlacedMols != 0:
                res = self.callFunction(
                    self.getPointToDrop,
                    [
                        ingr,
                        radius,
                        jitter,
                        freePoints,
                        nbFreePoints,
                        distance,
                        compId,
                        compNum,
                        vRangeStart,
                        vThreshStart,
                    ],
                )
            elif ingr.compNum > 0:
                allSrfpts = list(
                    self.compartments[ingr.compNum - 1].surfacePointsNormals.keys()
                )
                res = [True, allSrfpts[int(random() * len(allSrfpts))]]
            #  Replaced this with Sept 25, 2011 thesis version on July 5, 2012
            if verbose > 1:
                print("get drop point res", res)
            if res[0]:
                ptInd = res[1]
                if ptInd > len(distance):
                    print("problem ", ptInd)
                    continue
            else:
                if verbose > 1:
                    print("vRangeStart coninue ", res)
                vRangeStart = res[1]
                continue
                print("picked ", ptInd, distance[ptInd])
            # place the ingredient
            if self.overwritePlaceMethod:
                ingr.placeType = self.placeMethod
            # if self.rejectionThreshold is not None:
            #    ingr.rejectionThreshold = self.rejectionThreshold
            # check the largestProteinSize
            if ingr.encapsulatingRadius > self.largestProteinSize:
                self.largestProteinSize = ingr.encapsulatingRadius
                # histoVol, ptInd, freePoints, nbFreePoints, distance, dpad,usePP,
            # stepByStep=False, verbose=False,
            success, nbFreePoints = self.callFunction(
                ingr.place,
                (
                    self,
                    ptInd,
                    freePoints,
                    nbFreePoints,
                    distance,
                    dpad,
                    usePP,
                    stepByStep,
                    verbose,
                ),
                {"debugFunc": debugFunc},
            )
            if success:
                self.grid.distToClosestSurf = numpy.array(distance[:])
                self.grid.freePoints = numpy.array(freePoints[:])
                self.grid.nbFreePoints = len(freePoints)  # -1
                if verbose > 1:
                    print("success", ingr.completion)
                # update largest protein size
                # problem when the encapsulatingRadius is actually wrong
                if ingr.encapsulatingRadius > self.largestProteinSize:
                    self.largestProteinSize = ingr.encapsulatingRadius
                PlacedMols += 1
            else:
                if verbose > 1:
                    print("rejected", ingr.rejectionCounter)
                    print("picked reduced ?", ptInd, distance[ptInd])

            if ingr.completion >= 1.0:
                ind = self.activeIngr.index(ingr)
                if verbose > 1:
                    print("completed***************", ingr.name)
                    print("PlacedMols = ", PlacedMols)
                    print("activeIngr index of ", ingr.name, ind)
                    print(
                        "threshold p len ",
                        len(self.thresholdPriorities),
                        len(self.normalizedPriorities),
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
                    self.getSortedActiveIngredients, (self.activeIngr, verbose)
                )
                if verbose > 2:
                    print("len(self.activeIngr", len(self.activeIngr))
                    print("len(self.activeIngr0)", len(self.activeIngr0))
                    print("len(self.activeIngr12)", len(self.activeIngr12))
                self.activeIngre_saved = self.activeIngr[:]

                self.totalPriorities = 0  # 0.00001
                for priors in self.activeIngr12:
                    pp = priors.packingPriority
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
                    pp = priors.packingPriority
                    if self.totalPriorities != 0:
                        np = float(pp) / float(self.totalPriorities)
                    else:
                        np = 0.0
                    self.normalizedPriorities.append(np)
                    #                    print ('np is ', np, ' pp is ', pp, ' tp is ', np + previousThresh)
                    self.thresholdPriorities.append(np + previousThresh)
                    previousThresh = np + float(previousThresh)
                self.activeIngr = self.activeIngr0 + self.activeIngr12
            if dump and ((time.time() - stime) > dump_freq):
                self.collectResultPerIngredient()
                print("SAVING", self.resultfile)
                self.saveRecipe(
                    self.resultfile + "_temporaray.json",
                    useXref=True,
                    mixed=True,
                    kwds=["source", "name", "positions", "radii"],
                    result=True,
                    grid=False,
                    packing_options=False,
                    indent=False,
                    quaternion=True,
                    transpose=False,
                )
                self.saveRecipe(
                    self.resultfile + "_temporaray_tr.json",
                    useXref=True,
                    mixed=True,
                    kwds=["source", "name", "positions", "radii"],
                    result=True,
                    grid=False,
                    packing_options=False,
                    indent=False,
                    quaternion=True,
                    transpose=True,
                )
                stime = time.time()

        self.distancesAfterFill = distance[:]
        self.freePointsAfterFill = freePoints[:]
        self.nbFreePointsAfterFill = nbFreePoints
        self.distanceAfterFill = distance[:]
        # self.rejectionCount = rejectionCount
        #        c4d.documents.RunAnimation(doc, True)
        t2 = time.time()
        print("time to fill", t2 - t1)

        if self.saveResult:
            self.grid.freePoints = freePoints[:]
            self.grid.distToClosestSurf = distance[:]
            # shoul check extension filename for type of saved file
            self.saveGridToFile(self.resultfile + "grid")
            self.grid.result_filename = self.resultfile + "grid"
            self.collectResultPerIngredient()
            self.store()
            self.store_asTxt()
            #            self.store_asJson(resultfilename=self.resultfile+".json")
            self.saveRecipe(
                self.resultfile + ".json",
                useXref=False,
                mixed=True,
                kwds=["compNum"],
                result=True,
                quaternion=True,
                grid=False,
                packing_options=False,
                indent=False,
            )  # pdb ?
            # self.saveGridToFile_asTxt(self.resultfile+"grid")freePointsAfterFill
            # should we save to text as well
            print("time to save in fil5", time.time() - t2)
            #            vAnalysis = 0
            if vAnalysis == 1:
                #    START Analysis Tools: Graham added back this big chunk of code for analysis tools and graphic on 5/16/12 Needs to be cleaned up into a function and proper uPy code
                unitVol = self.grid.gridSpacing ** 3
                # totalVolume = self.grid.gridVolume*unitVol
                wrkDirRes = self.resultfile + "_analyze_"
                print("self.compartments = ", self.compartments)
                for o in self.compartments:  # only for compartment ?
                    # totalVolume -= o.surfaceVolume
                    # totalVolume -= o.interiorVolume
                    innerPointNum = len(o.insidePoints) - 1
                    print("  .  .  .  . ")
                    print("for compartment o = ", o.name)
                    print("inner Point Count = ", innerPointNum)
                    print("inner Volume = ", o.interiorVolume)
                    print("innerVolume temp Confirm = ", innerPointNum * unitVol)
                    usedPts = 0
                    unUsedPts = 0
                    # fpts = self.freePointsAfterFill
                    vDistanceString = ""
                    insidepointindce = numpy.nonzero(
                        numpy.equal(self.grid.gridPtId, -o.number)
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
                    # resultfilename = self.resultfile
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
                    )  # Used this from thesis to overwrite less informative SVN version on next line on July 5, 2012
                    #            resultfilenameT = wrkDirRes+"/vResultMatrix1" + o.name + "_Trans.txt"
                    #            resultfilenameR = wrkDirRes+"/vResultMatrix1" + o.name + "_Rot.txt"
                    # pickle.dump(self.molecules, rfile)
                    # OR
                    vTranslationString = ""
                    vRotationString = ""
                    result = []
                    matCount = 0
                    # Add safety check for C4D until we can get uPy working for this matrix to hbp rotation function?
                    #            from c4d import utils   # Removed by Graham on July 10, 2012 because replaced with more recent Thesis code on July 5, 2012 below
                    # what do you save everthing inleft hand ? and you actually dont use it ??
                    # Note July 4, 2012: the results are saved as right handed (see 2, 1, 0 for h, p, b) and used for analysis tools
                    # Note July 5, 2012: I found the better version we made and added it below to override the C4D version!
                    for pos, rot, ingr, ptInd in o.molecules:
                        # vMatrixString += str(result([pos]))+"\n"
                        # BEGIN: newer code from Theis version added July 5, 2012
                        if hasattr(self, "afviewer"):
                            mat = rot.copy()
                            mat[:3, 3] = pos
                            import math
                            from ePMV import comput_util as c

                            r = c.matrixToEuler(mat)
                            h1 = math.degrees(math.pi + r[0])
                            p1 = math.degrees(r[1])
                            b1 = math.degrees(-math.pi + r[2])
                            # angles[0] = 180.0+angles[0]
                            # angles[2] = 180.0-angles[2]
                            # hmat = self.afviewer.vi.FromMat(mat,transpose=True)
                            # rot = utils.MatrixToHPB(hmat)
                            print("rot from matrix = ", r, h1, p1, b1)
                            # END: newer code from Theis version added July 5, 2012
                        result.append([pos, rot])
                        pt3d = result[matCount][0]
                        (
                            x,
                            y,
                            z,
                        ) = pt3d  # ADDDED this line back from newer code from Theis version added July 5, 2012
                        # BEGIN: retired SVN version, retired July 5, 2012
                        #                x, y, z = pt3d
                        #                rot3d = result[matCount][1][2]
                        #                h1 = rot3d[2]
                        #                p1 = rot3d[1]
                        #                b1 = rot3d[0]
                        #                rot3d = result[matCount][1][1]
                        #                h2 = rot3d[2]
                        #                p2 = rot3d[1]
                        #                b2 = rot3d[0]
                        #                rot3d = result[matCount][1][0]
                        #                h3 = rot3d[2]
                        #                p3 = rot3d[1]
                        #                b3 = rot3d[0]
                        # can we test for C4D for these last 6 lines until we can get same functionality from uPy?
                        #                off = c4d.Vector(0)
                        #                vec = c4d.Matrix(off, c4d.Vector(h1, p1, b1), c4d.Vector(h2,p2,b2), c4d.Vector(h3,p3,b3) )
                        #                print vec
                        #                #m = rot3d #obj.GetMg()
                        #                rot = utils.MatrixToHPB(vec)
                        #                print 'rot from matrix = ', rot
                        # END: retired SVN version, retired July 5, 2012
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
                        )  # ADDDED this line back from newer code from Theis version added July 5, 2012 to replace next line from SVN
                        #                vRotationString += str(h1)+ ",\t" + str(p1) + ",\t" + str(b1) + ingr.name +"\n"
                        # vRotationString += str( (result[matCount][1]).x )+"\n"
                        matCount += 1

                    # result.append([pos,rot,ingr.name,ingr.compNum,ptInd])
                    # d = self.distancesAfterFill[pt]
                    # vDistanceString += str(d)+"\n"
                    # pickle.dump(result, rfile)
                    rfile = open(resultfilenameT, "w")
                    rfile.write(vTranslationString)
                    rfile.close()

                    rfile = open(resultfilenameR, "w")
                    rfile.write(vRotationString)
                    rfile.close()
                    print("len(result) = ", len(result))
                    print("len(self.molecules) = ", len(self.molecules))
                    # Graham Note:  There is overused disk space- the rotation matrix is 4x4 with an offset of 0,0,0
                    # and we have a separate translation vector in the results and molecules arrays.
                    #  Get rid of the translation vector and move it to the rotation matrix to save space...
                    # will that slow the time it takes to extract the vector from the matrix when we need to call it?
                    print(
                        "*************************************************** vDistance String Should be on"
                    )
                    print("unitVolume2 = ", unitVol)
                    print("Number of Points Unused = ", unUsedPts)
                    print("Number of Points Used   = ", usedPts)
                    print("Volume Used   = ", usedPts * unitVol)
                    print("Volume Unused = ", unUsedPts * unitVol)
                    print("vTestid = ", vTestid)
                    print("self.nbGridPoints = ", self.nbGridPoints)
                    print("self.gridVolume = ", self.gridVolume)
                    #        self.exteriorVolume = totalVolume

            print("self.compartments In Environment = ", len(self.compartments))
            if self.compartments == []:
                # o = self.histoVol
                #                o = self.exteriorRecipe
                unitVol = self.grid.gridSpacing ** 3
                innerPointNum = len(freePoints)
                print("  .  .  .  . ")
                print("inner Point Count = ", innerPointNum)
                print("innerVolume temp Confirm = ", innerPointNum * unitVol)
                usedPts = 0
                unUsedPts = 0
                # fpts = self.freePointsAfterFill
                vDistanceString = ""
                for i in range(innerPointNum):
                    pt = freePoints[i]  # fpts[i]
                    # for pt in self.histo.freePointsAfterFill:#[:self.histo.nbFreePointsAfterFill]:
                    d = self.distancesAfterFill[pt]
                    vDistanceString += str(d) + "\n"
                    if d <= 0:  # >self.smallestProteinSize-0.001:
                        usedPts += 1
                    else:
                        unUsedPts += 1
                    #                filename = wrkDirRes+"/vResultMatrix1" + o.name + "_Testid" + str(vTestid) + "_Seed" + str(seedNum) + "_dists.txt" # Used this from thesis to overwrite less informative SVN version on next line on July 5, 2012
                    #                #            filename = wrkDirRes+"/vDistances1.txt"
                    #                f = open(filename,"w")
                    #                vMyString = "I am on" + "\nThis is a new line."
                    #                f.write(vDistanceString)
                    #                f.close()
                    #                resultfilenameT = wrkDirRes+"/vResultMatrix1" + o.name + "_Testid" + str(vTestid) + "_Seed" + str(seedNum) + "_Trans.txt" # Used this from thesis to overwrite less informative SVN version on next line on July 5, 2012
                    #                resultfilenameR = wrkDirRes+"/vResultMatrix1" + o.name + "_Testid" + str(vTestid) + "_Seed" + str(seedNum) + "_Rot.txt" # Used this from thesis to overwrite less informative SVN version on next line on July 5, 2012
                    #                vTranslationString = ""
                    #                vRotationString = ""
                    #                result=[]
                    #                matCount = 0
                    #                # Add safety check for C4D until we can get uPy working for this matrix to hbp rotation function?
                    #                #            from c4d import utils   # Removed by Graham on July 10, 2012 because replaced with more recent Thesis code on July 5, 2012 below
                    #                #what do you save everthing in left hand ? and you actually dont use it ??
                    #                # Note July 4, 2012: the results are saved as right handed (see 2, 1, 0 for h, p, b) and used for analysis tools
                    #                # Note July 5, 2012: I found the better version we made and added it below to override the C4D version!
                    #                for pos, rot, ingr, ptInd in o.molecules:
                    #                    #vMatrixString += str(result([pos]))+"\n"
                    #                    # BEGIN: newer code from Theis version added July 5, 2012
                    #                    if hasattr(self,"afviewer"):
                    #                        mat = rot.copy()
                    #                        mat[:3, 3] = pos
                    #                        import math
                    #                        from ePMV import comput_util as c
                    #                        r  = c.matrixToEuler(mat)
                    #                        h1 = math.degrees(math.pi + r[0])
                    #                        p1 = math.degrees(r[1])
                    #                        b1 = math.degrees(-math.pi + r[2])
                    #                        #angles[0] = 180.0+angles[0]
                    #                        #angles[2] = 180.0-angles[2]
                    #                        #hmat = self.afviewer.vi.FromMat(mat,transpose=True)
                    #                        #rot = utils.MatrixToHPB(hmat)
                    #                        print 'rot from matrix = ', r,h1,p1,b1
                    #                    # END: newer code from Theis version added July 5, 2012
                    #                    result.append([pos,rot])
                    #                    pt3d = result[matCount][0]
                    #                    x, y, z = pt3d #  ADDDED this line back from newer code from Theis version added July 5, 2012
                    #                    vTranslationString += str(x)+ ",\t" + str(y) + ",\t" + str(z) + "\n"
                    #                    vRotationString += str(h1)+ ",\t" + str(p1) + ",\t" + str(b1) + ",\t" + ingr.name +"\n"  #  ADDDED this line back from newer code from Theis version
                    #                    matCount += 1
                    #                rfile = open(resultfilenameT, 'w')
                    #                rfile.write( vTranslationString )
                    #                rfile.close()
                    #
                    #                rfile = open(resultfilenameR, 'w')
                    #                rfile.write( vRotationString )
                    #                rfile.close()
                    #                print ('len(result) = ', len(result))
                    #                print ('len(self.molecules) = ', len(self.molecules))
                # Graham Note:  There is overused disk space- the rotation matrix is 4x4 with an offset of 0,0,0
                # and we have a separate translation vector in the results and molecules arrays.
                # Get rid of the translation vector and move it to the rotation matrix to save space...
                # will that slow the time it takes to extract the vector from the matrix when we need to call it?
                print(
                    "*************************************************** vDistance String Should be on"
                )
                print("unitVolume2 = ", unitVol)
                print("Number of Points Unused = ", unUsedPts)
                print("Number of Points Used   = ", usedPts)
                print("Volume Used   = ", usedPts * unitVol)
                print("Volume Unused = ", unUsedPts * unitVol)
                print("vTestid = ", vTestid)
                print("self.nbGridPoints = ", self.nbGridPoints)
                print("self.gridVolume = ", self.gridVolume)
                print("histoVol.timeUpDistLoopTotal = ", self.timeUpDistLoopTotal)

                # totalVolume = self.grid.gridVolume*unitVol
                # fpts = self.nbFreePointsAfterFill
                #        print 'self.freePointsAfterFill = ', self.freePointsAfterFill
                # print 'nnbFreePointsAfterFill = ', self.nbFreePointsAfterFill
                # print 'Total Points = ', self.grid.gridVolume
                # print 'Total Volume = ', totalVolume
                #    END Analysis Tools: Graham added back this big chunk of code for analysis tools and graphic on 5/16/12 Needs to be cleaned up into a function and proper uPy code
        print("time to save end", time.time() - t2)
        if self.afviewer is not None and hasattr(self.afviewer, "vi"):
            self.afviewer.vi.progressBar(label="Filling Complete")
            self.afviewer.vi.resetProgressBar()
        ingredients = {}
        for pos, rot, ingr, ptInd in self.molecules:
            if ingr.name not in ingredients:
                ingredients[ingr.name] = [ingr, [], [], []]
            mat = rot.copy()
            mat[:3, 3] = pos
            ingredients[ingr.name][1].append(pos)
            ingredients[ingr.name][2].append(rot)
            ingredients[ingr.name][3].append(numpy.array(mat))
        for o in self.compartments:
            for pos, rot, ingr, ptInd in o.molecules:
                if ingr.name not in ingredients:
                    ingredients[ingr.name] = [ingr, [], [], []]
                mat = rot.copy()
                mat[:3, 3] = pos
                ingredients[ingr.name][1].append(pos)
                ingredients[ingr.name][2].append(rot)
                ingredients[ingr.name][3].append(numpy.array(mat))
        self.ingr_result = ingredients
        if self.treemode == "bhtree":
            from bhtree import bhtreelib

            bhtreelib.freeBHtree(self.close_ingr_bhtree)
        #        bhtreelib.FreeRBHTree(self.close_ingr_bhtree)
        #        del self.close_ingr_bhtree

    def displayCancelDialog(self):
        print(
            "Popup CancelBox: if Cancel Box is up for more than 10 sec, close box and continue loop from here"
        )

    #        from pyubic.cinema4d.c4dUI import TimerDialog
    #        dialog = TimerDialog()
    #        dialog.init()
    #        dialog.Open(async=True, pluginid=25555589, width=120, height=100)
    #        tt=time.time()
    # while dialog.IsOpen():
    #    if time.time()-tt > 5.:
    #        print "time.time()-tt = ", time.time()-tt
    #        dialog.Close()
    #        cancel = dialog._cancel
    #        cancel=c4d.gui.QuestionDialog('WannaCancel?') # Removed by Graham on July 10, 2012 because it may no longer be needed, but test it TODO
    #        return cancel

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
            #            print ("inr,name,compNum",ingr.name,name,compNum)
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
                    # print ("inr,name,compNum",name,compNum,i,o.name,ingr)
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
            if self.treemode == "bhtree":  # "cKDTree"
                if len(self.rTrans) >= 1:
                    bhtreelib.freeBHtree(self.close_ingr_bhtree)
                self.close_ingr_bhtree = bhtreelib.BHtree(self.rTrans, None, 10)
            else:
                self.close_ingr_bhtree = spatial.cKDTree(self.rTrans, leafsize=10)
        self.cFill = self.nFill
        # if name == None :
        #        name = "F"+str(self.nFill)
        #        self.FillName.append(name)
        #        self.nFill+=1
        self.ingr_result = ingredients
        if len(freePoint):
            self.restoreFreePoints(freePoint)
        return ingredients

    def restoreFreePoints(self, freePoint):
        self.freePoints = self.freePointsAfterFill = freePoint
        self.nbFreePointsAfterFill = len(freePoint)
        self.distanceAfterFill = self.grid.distToClosestSurf
        self.distancesAfterFill = self.grid.distToClosestSurf

    def loadFreePoint(self, resultfilename):
        rfile = open(resultfilename + "freePoints", "rb")
        freePoint = pickle.load(rfile)
        rfile.close()
        return freePoint

    def store(self, resultfilename=None):
        if resultfilename is None:
            resultfilename = self.resultfile
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
            orfile = open(resultfilename + "ogra" + str(i), "wb")
            result = []
            for pos, rot, ingr, ptInd in orga.molecules:
                result.append([pos, rot, ingr.name, ingr.compNum, ptInd])
            pickle.dump(result, orfile)
            #            pickle.dump(orga.molecules, orfile)
            orfile.close()
        rfile = open(resultfilename + "freePoints", "wb")
        pickle.dump(self.freePoints, rfile)
        rfile.close()

    @classmethod
    def dropOneIngr(self, pos, rot, ingrname, ingrcompNum, ptInd, rad=1.0):
        line = ""
        line += ("<%f,%f,%f>,") % (pos[0], pos[1], pos[2])
        r = rot.reshape(
            16,
        )
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
            ingr.encapsulatingRadius,
        )  # ingrdic["compNum"],1,ingrdic["encapsulatingRadius"]

    def load_asTxt(self, resultfilename=None):
        #        from upy.hostHelper import Helper as helper
        if resultfilename is None:
            resultfilename = self.resultfile
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
            #        rfile = open(resultfilename+"freePoints",'rb')
        freePoint = []  # pickle.load(rfile)
        try:
            rfile = open(resultfilename + "freePoints", "rb")
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
        #        from upy.hostHelper import Helper as helper
        if resultfilename is None:
            resultfilename = self.resultfile
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
                    #                    print ("rlen ",len(iresults),name_ingr)
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
                            orga.name + "_surf__" + ingr.o_name
                            in self.result_json[orga.name + "_surfaceRecipe"]
                        ):
                            name_ingr = orga.name + "_surf__" + ingr.o_name
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
                        #                        print ("rlen ",len(iresults),name_ingr)
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
                            orga.name + "_int__" + ingr.o_name
                            in self.result_json[orga.name + "_innerRecipe"]
                        ):
                            name_ingr = orga.name + "_int__" + ingr.o_name
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
                        #                        print ("rlen ",len(iresults),name_ingr)
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
            rfile = open(resultfilename + "freePoints", "rb")
            freePoint = pickle.load(rfile)
            rfile.close()
        except:  # noqa: E722
            pass
        return result, orgaresult, freePoint

    def dropOneIngrJson(self, ingr, rdic):
        adic = OrderedDict()  # [ingr.name]
        adic["compNum"] = ingr.compNum
        adic["encapsulatingRadius"] = float(ingr.encapsulatingRadius)
        adic["results"] = []
        #        print ("dropi ",ingr.name,len(ingr.results))
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
            resultfilename = self.resultfile
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
            resultfilename = self.resultfile
        resultfilename = autopack.fixOnePath(resultfilename)
        rfile = open(resultfilename + ".txt", "w")  # doesnt work with symbol link ?
        # pickle.dump(self.molecules, rfile)
        # OR
        line = ""
        line += "<recipe include = " + self.setupfile + ">\n"
        for pos, rot, ingr, ptInd in self.molecules:
            line += self.dropOneIngr(
                pos, rot, ingr.name, ingr.compNum, ptInd, rad=ingr.encapsulatingRadius
            )
            # result.append([pos,rot,ingr.name,ingr.compNum,ptInd])
        rfile.write(line)
        # write the curve point

        rfile.close()
        for i, orga in enumerate(self.compartments):
            orfile = open(resultfilename + "ogra" + str(i) + ".txt", "w")
            line = ""
            for pos, rot, ingr, ptInd in orga.molecules:
                line += self.dropOneIngr(
                    pos,
                    rot,
                    ingr.name,
                    ingr.compNum,
                    ptInd,
                    rad=ingr.encapsulatingRadius,
                )
            orfile.write(line)
            #            pickle.dump(orga.molecules, orfile)
            orfile.close()
        #        rfile = open(resultfilename+"freePoints", 'w')
        #        pickle.dump(self.freePoints, rfile)
        #        rfile.close()

    @classmethod
    def convertPickleToText(self, resultfilename=None, norga=0):
        if resultfilename is None:
            resultfilename = self.resultfile
        rfile = open(resultfilename)
        result = pickle.load(rfile)
        orgaresult = []
        for i in range(norga):
            orfile = open(resultfilename + "ogra" + str(i))
            orgaresult.append(pickle.load(orfile))
            orfile.close()
        rfile.close()
        rfile = open(resultfilename + "freePoints")
        rfile.close()
        rfile = open(resultfilename + ".txt", "w")
        line = ""
        for pos, rot, ingrName, compNum, ptInd in result:
            line += self.dropOneIngr(pos, rot, ingrName, compNum, ptInd)
            # result.append([pos,rot,ingr.name,ingr.compNum,ptInd])
        rfile.write(line)
        rfile.close()
        for i in range(norga):
            orfile = open(resultfilename + "ogra" + str(i) + ".txt", "w")
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

    def finishWithWater(self, freePoints=None, nbFreePoints=None):
        # self.freePointsAfterFill[:self.nbFreePointsAfterFill]
        # sphere sphere of 2.9A
        if freePoints is None:
            freePoints = self.freePointsAfterFill
        if nbFreePoints is None:
            nbFreePoints = self.nbFreePointsAfterFill
        # a freepoint is a voxel, how many water in the voxel
        # coords masterGridPositions

    def estimateVolume(self, boundingBox, spacing):
        # need to box N point and coordinaePoint
        #        xl,yl,zl = boundingBox[0]
        #        xr,yr,zr = boundingBox[1]
        #        realTotalVol = (xr-xl)*(yr-yl)*(zr-zl)
        grid = Grid()
        grid.boundingBox = boundingBox
        grid.gridSpacing = spacing  # = self.smallestProteinSize*1.1547  # 2/sqrt(3)????
        grid.gridVolume, grid.nbGridPoints = self.callFunction(
            grid.computeGridNumberOfPoint, (boundingBox, spacing)
        )
        unitVol = spacing ** 3
        realTotalVol = grid.gridVolume * unitVol

        r = self.exteriorRecipe
        if r:
            r.setCount(realTotalVol, reset=False)
        for o in self.compartments:
            o.estimateVolume(hBB=grid.boundingBox)
            rs = o.surfaceRecipe
            if rs:
                realTotalVol = o.surfaceVolume
                rs.setCount(realTotalVol, reset=False)
            ri = o.innerRecipe
            if ri:
                realTotalVol = o.interiorVolume
                ri.setCount(realTotalVol, reset=False)

    def estimateVolume_old(self, boundingBox, spacing):
        # need to box N point and coordinaePoint
        pad = 10.0
        grid = Grid()
        grid.boundingBox = boundingBox
        grid.gridSpacing = spacing  # = self.smallestProteinSize*1.1547  # 2/sqrt(3)????
        grid.gridVolume, grid.nbGridPoints = self.callFunction(
            grid.computeGridNumberOfPoint, (boundingBox, spacing)
        )
        nbPoints = grid.gridVolume
        # compute 3D point coordiantes for all grid points
        self.callFunction(grid.create3DPointLookup)
        grid.gridPtId = [0] * nbPoints
        xl, yl, zl = boundingBox[0]
        xr, yr, zr = boundingBox[1]
        realTotalVol = (xr - xl) * (yr - yl) * (zr - zl)
        print("totalVolume %f for %d points" % (realTotalVol, nbPoints))
        # distToClosestSurf is set to self.diag initially
        grid.diag = diag = vlen(vdiff((xr, yr, zr), (xl, yl, zl)))
        distance = grid.distToClosestSurf = [diag] * nbPoints
        # foreach ingredient get estimation of insidepoint and report the percantage of total point in Volume
        r = self.exteriorRecipe
        if r:
            for ingr in r.ingredients:
                insidePoints, newDistPoints = ingr.getInsidePoints(
                    grid,
                    grid.masterGridPositions,
                    pad,
                    distance,
                    centT=ingr.positions[-1],
                    jtrans=[0.0, 0.0, 0.0],
                    rotMatj=numpy.identity(4),
                )
                ingr.nbPts = len(insidePoints)
                onemol = (realTotalVol * float(ingr.nbPts)) / float(nbPoints)
                ingr.vol_nbmol = int(ingr.molarity * onemol)
                print(
                    "ingr %s has %d points representing %f for one mol thus %d mol"
                    % (ingr.name, ingr.nbPts, onemol, ingr.vol_nbmol)
                )
            #                ingr.vol_nbmol = ?
        for o in self.compartments:
            rs = o.surfaceRecipe
            if rs:
                for ingr in rs.ingredients:
                    insidePoints, newDistPoints = ingr.getInsidePoints(
                        grid,
                        grid.masterGridPositions,
                        pad,
                        distance,
                        centT=ingr.positions[-1],
                        jtrans=[0.0, 0.0, 0.0],
                        rotMatj=numpy.identity(4),
                    )
                    ingr.nbPts = len(insidePoints)
                    onemol = (realTotalVol * float(ingr.nbPts)) / float(nbPoints)
                    ingr.vol_nbmol = int(ingr.molarity * onemol)
            ri = o.innerRecipe
            if ri:
                for ingr in ri.ingredients:
                    insidePoints, newDistPoints = ingr.getInsidePoints(
                        grid,
                        grid.masterGridPositions,
                        pad,
                        distance,
                        centT=ingr.positions[-1],
                        jtrans=[0.0, 0.0, 0.0],
                        rotMatj=numpy.identity(4),
                    )
                    ingr.nbPts = len(insidePoints)
                    onemol = (realTotalVol * float(ingr.nbPts)) / float(nbPoints)
                    ingr.vol_nbmol = int(ingr.molarity * onemol)

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
            #            from autopack.octree import Octree
            from autopack import octree_exteneded as octree
            from autopack.octree_exteneded import Octree

            octree.MINIMUM_SIZE = self.smallestProteinSize
            octree.MAX_OBJECTS_PER_NODE = 10
            self.octree = Octree(
                self.grid.getRadius(), helper=helper
            )  # Octree((0,0,0),self.grid.getRadius())   #0,0,0 or center of grid?

    def setupPanda(
        self,
    ):
        try:
            import panda3d
        except Exception:
            return
        self.rb_func_dic = {
            "bullet": {
                "SingleSphere": self.addSingleSphereRB,
                "SingleCube": self.addSingleCubeRB,
                "MultiSphere": self.addMultiSphereRB,
                "MultiCylinder": self.addMultiCylinderRB,
                "Grow": self.addMultiCylinderRB,
                "Mesh": self.addMeshRB,
            },
            "ode": {
                "SingleSphere": self.addSingleSphereRBODE,
            },
        }
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

    def addSingleSphereRBODE(self, ingr, pMat, jtrans, rotMat):
        if panda3d is None:
            return
        body = OdeBody(self.world)
        M = OdeMass()
        M.setSphereTotal(1.0, ingr.encapsulatingRadius)
        body.setMass(M)
        body.setPosition(Vec3(jtrans[0], jtrans[1], jtrans[2]))
        body.setRotation(pMat)
        # the geometry for the collision ?
        geom = OdeSphereGeom(self.ode_space, ingr.encapsulatingRadius)
        geom.setBody(body)
        return geom

    def addSingleSphereRB(self, ingr, pMat, jtrans, rotMat):
        if panda3d is None:
            return
        shape = BulletSphereShape(ingr.encapsulatingRadius)
        inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode(ingr.name))
        inodenp.node().setMass(1.0)
        #        inodenp.node().addShape(shape)
        inodenp.node().addShape(
            shape, TransformState.makePos(Point3(0, 0, 0))
        )  # rotation ?
        #        spherenp.setPos(-2, 0, 4)
        return inodenp

    def addMultiSphereRB(self, ingr, pMat, jtrans, rotMat):
        if panda3d is None:
            return
        inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode(ingr.name))
        inodenp.node().setMass(1.0)
        centT = ingr.positions[
            0
        ]  # ingr.transformPoints(jtrans, rotMat, ingr.positions[0])
        for radc, posc in zip(ingr.radii[0], centT):
            shape = BulletSphereShape(radc)
            inodenp.node().addShape(
                shape, TransformState.makePos(Point3(posc[0], posc[1], posc[2]))
            )  #
        return inodenp

    def multiSphereRB(self, name, pos, rad):
        if panda3d is None:
            return
        inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode(name))
        inodenp.node().setMass(1.0)
        # centT = ingr.positions[0]#ingr.transformPoints(jtrans, rotMat, ingr.positions[0])
        #        for i in range(len(pos)):#
        #            posc = pos[i]
        #            radc = rad[i]
        for radc, posc in zip(rad, pos):
            shape = BulletSphereShape(radc)
            inodenp.node().addShape(
                shape, TransformState.makePos(Point3(posc[0], posc[1], posc[2]))
            )  #
        return inodenp

    def addSingleCubeRB(self, ingr, pMat, jtrans, rotMat):
        if panda3d is None:
            return
        halfextents = ingr.bb[1]
        shape = BulletBoxShape(
            Vec3(halfextents[0], halfextents[1], halfextents[2])
        )  # halfExtents
        inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode(ingr.name))
        inodenp.node().setMass(1.0)
        #        inodenp.node().addShape(shape)
        inodenp.node().addShape(
            shape, TransformState.makePos(Point3(0, 0, 0))
        )  # , pMat)#TransformState.makePos(Point3(jtrans[0],jtrans[1],jtrans[2])))#rotation ?
        #        spherenp.setPos(-2, 0, 4)
        return inodenp

    def addMultiCylinderRB(self, ingr, pMat, jtrans, rotMat):
        if panda3d is None:
            return
        helper = autopack.helper
        inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode(ingr.name))
        inodenp.node().setMass(1.0)
        centT1 = ingr.positions[
            0
        ]  # ingr.transformPoints(jtrans, rotMat, ingr.positions[0])
        centT2 = ingr.positions2[
            0
        ]  # ingr.transformPoints(jtrans, rotMat, ingr.positions2[0])
        for radc, p1, p2 in zip(ingr.radii[0], centT1, centT2):
            length, mat = helper.getTubePropertiesMatrix(p1, p2)
            pMat = self.pandaMatrice(mat)
            #            d = numpy.array(p1) - numpy.array(p2)
            #            s = numpy.sum(d*d)
            Point3(
                ingr.principalVector[0],
                ingr.principalVector[1],
                ingr.principalVector[2],
            )
            shape = BulletCylinderShape(
                radc, length, 1
            )  # math.sqrt(s), 1)# { XUp = 0, YUp = 1, ZUp = 2 } or LVector3f const half_extents
            inodenp.node().addShape(shape, TransformState.makeMat(pMat))  #
        return inodenp

    def addMeshRBOld(self, ingr, pMat, jtrans, rotMat):
        if panda3d is None:
            return
        helper = autopack.helper
        if ingr.mesh is None:
            return
        faces, vertices, vnormals = helper.DecomposeMesh(
            ingr.mesh, edit=False, copy=False, tri=True, transform=True
        )
        from panda3d.bullet import BulletTriangleMesh, BulletTriangleMeshShape

        mesh = BulletTriangleMesh()
        points3d = [Point3(v[0], v[1], v[2]) for v in vertices]
        for f in faces:
            mesh.addTriangle(points3d[f[0]], points3d[f[1]], points3d[f[2]])

        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode(ingr.name))
        inodenp.node().setMass(1.0)
        inodenp.node().addShape(
            shape, TransformState.makePos(Point3(0, 0, 0))
        )  # , pMat)#TransformState.makePos(Point3(jtrans[0],jtrans[1],jtrans[2])))#rotation ?
        return inodenp

    def setGeomFaces(self, tris, face):
        if panda3d is None:
            return
            # have to add vertices one by one since they are not in order
        if len(face) == 2:
            face = numpy.array([face[0], face[1], face[1], face[1]], dtype="int")
        for i in face:
            tris.addVertex(i)
        tris.closePrimitive()

    def addMeshRB(self, ingr, pMat, jtrans, rotMat):
        if panda3d is None:
            return
        inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode(ingr.name))
        inodenp.node().setMass(1.0)
        if ingr.mesh is None:
            return
        ingr.getData()
        if not len(ingr.vertices):
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
        [vertexWriter.addData3f(v[0], v[1], v[2]) for v in ingr.vertices]

        # step 2) make primitives and assign vertices to them
        tris = GeomTriangles(Geom.UHStatic)
        [self.setGeomFaces(tris, face) for face in ingr.faces]

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
        print("shape ok", shape)
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

    def pandaMatrice(self, mat):
        if panda3d is None:
            return
        mat = mat.transpose().reshape((16,))
        #        print mat,len(mat),mat.shape
        pMat = Mat4(
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
            mat[12],
            mat[13],
            mat[14],
            mat[15],
        )
        return pMat

    def addRB(self, ingr, trans, rotMat, rtype="SingleSphere", static=False):
        # Sphere
        if panda3d is None:
            return None
        if autopack.verbose > 1:
            print("add RB bullet ", ingr.name)
        mat = rotMat.copy()
        #        mat[:3, 3] = trans
        #        mat = mat.transpose()
        mat = mat.transpose().reshape((16,))
        mat3x3 = Mat3(
            mat[0], mat[1], mat[2], mat[4], mat[5], mat[6], mat[8], mat[9], mat[10]
        )
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
        pMat = TransformState.makeMat(pmat)
        if self.panda_solver == "ode":
            pMat = mat3x3
        inodenp = None
        #        print (pMat)
        if ingr.use_mesh_rb:
            rtype = "Mesh"
            # print ("#######RBNode Mesh ####", ingr.name, ingr.rbnode,self.rb_func_dic[rtype])
        inodenp = self.rb_func_dic[self.panda_solver][rtype](ingr, pMat, trans, rotMat)
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
        mat = rotMat.copy()
        #        mat[:3, 3] = trans
        #        mat = mat.transpose()
        mat = mat.transpose().reshape((16,))
        if True in numpy.isnan(mat).flatten():
            print("problem Matrix", node)
            return
        if self.panda_solver == "bullet":
            pMat = Mat4(
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
            nodenp = NodePath(node)
            nodenp.setMat(pMat)
        elif self.panda_solver == "ode":
            mat3x3 = Mat3(
                mat[0], mat[1], mat[2], mat[4], mat[5], mat[6], mat[8], mat[9], mat[10]
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
            print(done, dt, "time", time() - t1)
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
            res_filename = self.resultfile
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
            res_filename = self.resultfile
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

    def exportToReaDDy(
        self,
    ):
        # wehn I will get it running ... plugin ?
        return

        # ==============================================================================

    #         Animate
    # ==============================================================================
    def readTraj(self, filename):
        from autopack.trajectory import dcdTrajectory, molbTrajectory

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

    def linkTraj(
        self,
    ):
        # link the traj usin upy for creating a new synchronized calleback?
        if not self.traj_linked:
            autopack.helper.synchronize(self.applyStep)
            self.traj_linked = True

    def unlinkTraj(
        self,
    ):
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

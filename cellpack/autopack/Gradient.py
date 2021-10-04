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

import numpy
from random import random
import bisect
from math import exp, cos, pow as mathPow
from cellpack.mgl_tools.upy.hostHelper import vdistance
from cellpack.autopack.transformation import angle_between_vectors


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
        self.list_mode = ["X", "Y", "Z", "-X", "-Y", "-Z", "direction", "radial"]
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
        self.list_weight_mode = self.pick_functions.keys()
        self.list_options = [
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
                "values": self.list_mode,
                "default": "X",
                "type": "list",
                "description": "gradient direction",
                "min": 0,
                "max": 0,
            },
            "weight_mode": {
                "name": "weight_mode",
                "values": ["linear", "square", "cube", "gauss", "half-gauss"],
                "default": "linear",
                "type": "list",
                "description": "calcul of the weight method",
                "min": 0,
                "max": 0,
            },
            "pick_mode": {
                "name": "weight_mode",
                "values": self.list_weight_mode,
                "default": "linear",
                "type": "list",
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
        """get the overall direction of the gradient"""
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
        pick next random point according to the chosen function
        """
        return self.pick_functions[self.pick_mode](listPts)

    def buildWeigthMap(self, bb, MasterPosition):
        """
        build the actual gradient value according the gradint mode
        """
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
        from a given direction build a linear weight according the chosen mode
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

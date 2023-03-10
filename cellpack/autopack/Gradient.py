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
from math import cos
from cellpack.autopack.transformation import angle_between_vectors
from cellpack.autopack.utils import get_distances_from_point
from cellpack.autopack.interface_objects.gradient_data import DIRECTION_MAP


class Gradient:
    """
    The Gradient class
    ==========================
    This class handle the use of gradient to control the packing.
    The class define different and setup type of gradient,
    as well as the sampling function
    """

    def __init__(self, gradient_data):
        self.name = gradient_data["name"]
        self.description = gradient_data["description"]
        self.mode = gradient_data["mode"]
        self.weight_mode = gradient_data["weight_mode"]
        self.pick_mode = gradient_data["pick_mode"]
        self.mode_settings = gradient_data["mode_settings"]

        self.weight = None
        self.bb = None  # this is set when weight map is built in the env

        self.axes = {"X": 0, "-X": 0, "Y": 1, "-Y": 1, "Z": 2, "-Z": 2}

        self.weight_threshold = 0.0
        self.distance = 0.0
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

        self.function = self.defaultFunction  # lambda ?

    def get_center(self):
        """get the center of the gradient grid"""
        center = [0.0, 0.0, 0.0]
        for i in range(3):
            center[i] = (self.bb[0][i] + self.bb[1][i]) / 2.0
        return center

    def defaultFunction(self, xyz, direction):
        """
        #linear function 0->0.1
        #project xyz on direction
        """
        x = numpy.dot(xyz, direction)
        v = (x * 1.0) / (self.distance)
        return v
    
    def normalize_vector(self, vector):
        """
        Normalize to unit vector
        """
        return vector / numpy.linalg.norm(vector)

    def pickPoint(self, listPts):
        """
        pick next random point according to the chosen function
        """
        return self.pick_functions[self.pick_mode](listPts)

    def build_weight_map(self, bb, master_grid_positions):
        """
        build the actual gradient value according the gradient mode
        """
        if self.mode in self.axes:
            self.build_axis_weight_map(bb, master_grid_positions)
        elif self.mode == "vector":
            self.build_directional_weight_map(bb, master_grid_positions)
        elif self.mode == "radial":
            self.build_radial_weight_map(bb, master_grid_positions)
        elif self.mode == "surface":
            self.build_surface_distance_weight_map()

    def get_gauss_weights(self, number_of_points, degree=5):
        """
        given a number of points compute the gaussian weight for each
        """
        degree = number_of_points / 2.0
        weightGauss = []

        for i in range(int(number_of_points)):
            i = i - degree + 1
            frac = i / number_of_points
            gauss = numpy.exp(-((self.gblob * (frac)) ** 2))
            weightGauss.append(gauss)
        return numpy.array(weightGauss) * number_of_points

    def build_radial_weight_map(self, bb, master_grid_positions):
        self.bb = bb
        center = self.mode_settings.get("center")
        radius = self.mode_settings.get("radius")
        distances = get_distances_from_point(master_grid_positions, center)
        self.distances = numpy.where(distances < radius, distances, radius) / radius
        self.set_weights_by_mode()

    def build_surface_distance_weight_map(self):
        """
        build a map of weights based on the distance from a surface
        assumes self.distances include surface distances
        """
        if getattr(self.object, "surface_distances", None) is None:
            raise ValueError("Surface distances are not set")
        elif self.scale_to_next_surface:
            self.distances = self.object.scaled_distance_to_next_surface
        else:
            self.distances = self.object.surface_distances / self.object.max_distance
        self.set_weights_by_mode()

    def build_directional_weight_map(self, bb, master_grid_positions):
        """
        from a given direction build a linear weight according the chosen mode
        (linear, gauss, etc...)
        """        
        self.bb = bb
        direction = self.mode_settings["direction"]
        direction = self.normalize_vector(direction)
        self.weight = []
        center = self.mode_settings.get("center", self.get_center())
        distances = numpy.dot(master_grid_positions - center, direction)
        max_d = max(distances)
        min_d = min(distances)
        self.distances = (distances - min_d) / (max_d - min_d)
        self.set_weights_by_mode()

    def build_axis_weight_map(self, bb, master_grid_positions):
        """
        from a given axe (X,Y,Z) build a linear weight according the chosen mode
        (linear, gauss, etc...)
        """
        self.bb = bb
        ind = self.axes[self.mode]
        maxi = max(bb[1][ind], bb[0][ind])
        mini = min(bb[1][ind], bb[0][ind])
        self.weight = []
        self.distances = (master_grid_positions[:, ind] - mini) / (maxi - mini)
        self.set_weights_by_mode()

    def set_weights_by_mode(self):
        scaled_distances = self.distances
        if (max(scaled_distances) > 1.0) or (min(scaled_distances) < 0.0):
            self.log.error(
                "CHECK CALCULATED DISTANCES",
                f"Max: {max(scaled_distances)}, Min: {min(scaled_distances)}",
            )
        if self.weight_mode == "linear":
            self.weight = 1.0 - scaled_distances
        elif self.weight_mode == "square":
            self.weight = (1.0 - scaled_distances) ** 2
        elif self.weight_mode == "cube":
            self.weight = (1.0 - scaled_distances) ** 3
        self.weight[numpy.isnan(self.weight)] = 0
        # TODO: talk to Ludo about calculating gaussian weights

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

    def getRndWeighted(self, list_of_pts):
        """
        From http://glowingpython.blogspot.com/2012/09/weighted-random-choice.html
        Weighted random selection
        returns n_picks random indexes.
        the chance to pick the index i
        is give by the weight weights[i].
        """
        weight = numpy.take(self.weight, list_of_pts)
        t = numpy.cumsum(weight)
        s = numpy.sum(weight)
        i = numpy.searchsorted(t, numpy.random.rand(1) * s)[0]
        return list_of_pts[i]

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

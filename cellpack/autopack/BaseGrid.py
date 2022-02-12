# -*- coding: utf-8 -*-
"""
###############################################################################
#
# autoPACK Authors: Graham T. Johnson, Mostafa Al-Alusi, Ludovic Autin, Michel Sanner
#   Based on COFFEE Script developed by Graham Johnson between 2005 and 2010
#   with assistance from Mostafa Al-Alusi in 2009 and periodic input
#   from Arthur Olson's Molecular Graphics Lab
#
# BaseGrid.py Authors: Graham Johnson & Michel Sanner with editing/enhancement from Ludovic Autin
#
# Translation to Python initiated March 1, 2010 by Michel Sanner with Graham Johnson
#
# Class restructuring and organization: Michel Sanner
#
# Copyright: Graham Johnson ©2010
#
# This file "BaseGrid.py" is part of autoPACK, cellPACK.
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
@author: Ludovic Autin, Graham Johnson,  & Michel Sanner
"""
import logging
import numpy
from scipy import spatial
import math
from math import ceil, floor
from random import randrange
import cellpack.autopack as autopack
from cellpack.autopack.ldSequence import cHaltonSequence3
from cellpack.mgl_tools.RAPID import RAPIDlib
from cellpack.mgl_tools.bhtree import bhtreelib


# Kevin Grid point class
class gridPoint:
    def __init__(self, i, globalC, isPolyhedron):
        self.index = int(i)
        self.isOutside = None
        self.minDistance = (
            99999  # Only store a number here if within certain distance from polyhedron
        )
        self.representsPolyhedron = isPolyhedron
        self.closeFaces = []
        self.closestFaceIndex = 0
        self.testedEndpoint = None
        self.allDistances = (
            []
        )  # Stores a tuple list of distances to all points. (point,distance) = (5,2.5)
        self.globalCoord = numpy.array(
            globalC
        )  # Stores the global coordinate associated with this point


class BaseGrid:
    """
    The Grid class
    ==========================
    This class handle the use of grid to control the packing. The grid keep information of
    3d positions, distances, freePoints and inside/surface points from organelles.
    NOTE : thi class could be completely replace if openvdb is wrapped to python.
    """

    @staticmethod
    def reorder_free_points(pt, freePoints, nbFreePoints):
        # TODO: move this to env class, ing shouldn't aware of the whole grid
        # Swap the newly inside point value with the value of the last free point
        # Point will no longer be considered "free" because it will be beyond the range of
        # nbFreePoints. The value of the point itself is the history of it's original index
        # so any future swaps will still result in the correct index being move into the range
        # of nbFreePoints
        nbFreePoints -= 1
        vKill = freePoints[pt]
        vLastFree = freePoints[nbFreePoints]
        freePoints[vKill] = vLastFree
        freePoints[vLastFree] = vKill
        # Turn on these printlines if there is a problem with incorrect points showing in display points
        # self.log.debug("*************pt = masterGridPointValue = %d", pt)
        # self.log.debug("nbFreePointAfter = %d", nbFreePoints)
        # self.log.debug("vKill = %d", vKill)
        # self.log.debug("vLastFree = %d", vLastFree)
        # self.log.debug("freePoints[vKill] = %d", freePoints[vKill])
        # self.log.debug("freePoints[vLastFree] = %d", freePoints[vLastFree])
        # self.log.debug("pt = masterGridPointValue = %d", pt)
        # self.log.debug("freePoints[nbFreePoints-1] = %d", freePoints[nbFreePoints])
        # self.log.debug("freePoints[pt] = %d", freePoints[pt])
        # freePoints will now have all the available indices between 0 and nbFreePoints in
        # freePoints[nbFreePoints:] won't necessarily be the indices of inside points
        return freePoints, nbFreePoints

    @staticmethod
    def updateDistances(
        insidePoints,
        newDistPoints,
        freePoints,
        nbFreePoints,
        distance,
    ):
        # self.log.info(
        #     "*************updating Distances %d %d", nbFreePoints, len(insidePoints)
        # )
        # TODO: move this to env class, ing shouldn't aware of the whole grid

        # t1 = time()
        # distChanges = {}
        for pt, dist in list(insidePoints.items()):
            try:
                freePoints, nbFreePoints = BaseGrid.reorder_free_points(
                    pt, freePoints, nbFreePoints
                )
            except Exception:
                print(pt, "not in freeePoints********************************")
                pass
            distance[pt] = dist
        # self.log.debug("update free points loop %d", time() - t1)
        # t2 = time()
        for pt, dist in list(newDistPoints.items()):
            if pt not in insidePoints:

                distance[pt] = dist
        # self.log.debug("update distance loop %d", time() - t2)
        return nbFreePoints

    def __init__(
        self, boundingBox=([0, 0, 0], [0.1, 0.1, 0.1]), space=1, setup=True, lookup=0
    ):
        self.log = logging.getLogger("grid")
        self.log.propagate = False

        if None in boundingBox[0] or None in boundingBox[1]:
            boundingBox = ([0, 0, 0], [1000, 1000, 1000])
        # a grid is attached to an environnement
        self.boundingBox = boundingBox

        # this list provides the id of the component this grid points belongs
        # to. The id is an integer where 0 is the Histological Volume, and +i is
        # the surface of compartment i and -i is the interior of compartment i
        # in the list self. compartments
        self.gridPtId = []
        # will be a list of indices into 3D of compartment
        # of points that have not yet been used by the fill algorithm
        # entries are removed from this list as grid points are used up
        # during hte fill. This list is used to pick points randomly during
        # the fill
        self.freePoints = []
        self.nbFreePoints = 0
        # this list evolves in parallel with self.freePoints and provides
        # the distance to the closest surface (either an already placed
        # object (or an compartment surface NOT IMPLEMENTED)
        self.distToClosestSurf = []
        self.distToClosestSurf_store = []
        self.diag = self.getDiagonal()
        self.gridSpacing = space  # * 1.1547#cubic grid with a diagonal spacing equal to that smallest packing radius
        self.nbGridPoints = None
        self.nbSurfacePoints = 0
        self.gridVolume = 0  # will be the total number of grid points
        # list of (x,y,z) for each grid point (x index moving fastest)
        self.masterGridPositions = []
        self._x = None
        self._y = None
        self._z = None

        # this are specific for each compartment
        self.aInteriorGrids = []
        self.aSurfaceGrids = []
        # bhtree
        self.surfPtsBht = None
        self.ijkPtIndice = []
        self.filename = None  # used for storing before fill so no need rebuild
        self.result_filename = None  # used after fill to store result
        self.tree = None
        self.tree_free = None
        self.encapsulatingGrid = 0
        self.lookup = lookup
        self.center = None
        self.backup = None
        if setup:
            self.setup(self.boundingBox, space)
            # use np.roll to have periodic condition
            # what about collision ?

    def setup(self, boundingBox, space):
        # TODO : verify the gridSpacing calculation / setup after reading the recipe
        if space == 0:
            space = 20
        self.gridSpacing = space  # * 1.1547
        self.boundingBox = boundingBox

        if self.lookup == 0:
            self.create3DPointLookupCover()
        elif self.lookup == 1:
            self.create3DPointLookup()
        elif self.lookup == 2:
            self.create3DPointLookup_loop()

        nx, ny, nz = self.nbGridPoints
        self.ijkPtIndice = self.cartesian([range(nx), range(ny), range(nz)])

        self.getDiagonal()
        self.nbSurfacePoints = 0
        self.log.info("SETUP BASE GRID %d %d", self.gridVolume, self.gridSpacing)
        self.gridPtId = numpy.zeros(self.gridVolume, "i")  # [0]*nbPoints
        # self.distToClosestSurf = [self.diag]*self.gridVolume#surface point too?
        self.distToClosestSurf = (
            numpy.ones(self.gridVolume) * self.diag
        )  # (self.distToClosestSurf)
        self.freePoints = list(range(self.gridVolume))
        self.nbFreePoints = len(self.freePoints)
        self.log.info(
            "Lookup: %d, bounding box: %r, gridSpacing %r, length gridPtId %r",
            self.lookup,
            boundingBox,
            self.gridSpacing,
            len(self.gridPtId),
        )
        self.setupBoundaryPeriodicity()
        return self.gridSpacing

    def reset(
        self,
    ):
        # reset the  distToClosestSurf and the freePoints
        # boundingBox should be the same otherwise why keeping the grid
        # self.gridPtId = numpy.zeros(self.gridVolume,'i')
        # self.distToClosestSurf = numpy.ones(self.gridVolume)*self.diag#(self.distToClosestSurf)
        self.log.info("reset Grid distance to closest surface and freePoints")
        self.distToClosestSurf = (
            numpy.array(self.distToClosestSurf[:]) * 0.0
        ) + self.diag
        # self.distToClosestSurf[:] = self.diag  # numpy.array([self.diag]*len(self.distToClosestSurf))#surface point too?
        self.freePoints = list(range(len(self.freePoints)))
        self.nbFreePoints = len(self.freePoints)

    def removeFreePoint(self, pti):
        tmp = self.freePoints[self.nbFreePoints]  # last one
        self.freePoints[self.nbFreePoints] = pti
        self.freePoints[pti] = tmp
        self.nbFreePoints -= 1

    def getDiagonal(self, boundingBox=None):
        if boundingBox is None:
            boundingBox = self.boundingBox
        self.diag = numpy.sqrt(
            (numpy.array(boundingBox[0]) - numpy.array(boundingBox[1])) ** 2
        ).sum()
        return self.diag

    def create3DPointLookup_loop(self, boundingBox=None):
        """
        Fill the orthogonal bounding box described by two global corners
        with an array of points spaces pGridSpacing apart.:
        """
        if boundingBox is None:
            boundingBox = self.boundingBox
        xl, yl, zl = boundingBox[0]
        self.gridVolume, self.nbGridPoints = self.computeGridNumberOfPoint(
            boundingBox, self.gridSpacing
        )
        nx, ny, nz = self.nbGridPoints
        pointArrayRaw = numpy.zeros((nx * ny * nz, 3), "f")
        self.ijkPtIndice = numpy.zeros((nx * ny * nz, 3), "i")  # this is unused
        space = self.gridSpacing
        # Vector for lower left broken into real of only the z coord.
        i = 0
        padding = space / 2.0
        for zi in range(nz):
            for yi in range(ny):
                for xi in range(nx):

                    x = xl + xi * space + padding
                    y = yl + yi * space + padding
                    z = zl + zi * space + padding
                    pointArrayRaw[i] = (x, y, z)
                    self.ijkPtIndice[i] = (xi, yi, zi)
                    i += 1
        self.log.info("grid spacing %d", space)
        self.masterGridPositions = pointArrayRaw

    def create3DPointLookup(self, boundingBox=None):
        """
        Fill the orthogonal bounding box described by two global corners
        with an array of points spaces pGridSpacing apart. Optimized version using
        numpy broadcasting
        """
        if boundingBox is None:
            boundingBox = self.boundingBox
        space = self.gridSpacing
        # we want the diagonal of the voxel, not the diagonal of the plane, so the second 1.1547 is was incorrect
        environmentBoxEqualFillBox = False

        self.log.info("Using create3DPointLookup")
        if environmentBoxEqualFillBox:  # environment.environmentBoxEqualFillBox:
            self._x = x = numpy.arange(
                boundingBox[0][0], boundingBox[1][0], space
            )  # *1.1547) gridspacing is already multiplied by 1.1547
            self._y = y = numpy.arange(
                boundingBox[0][1], boundingBox[1][1], space
            )  # *1.1547)
            self._z = z = numpy.arange(
                boundingBox[0][2], boundingBox[1][2], space
            )  # *1.1547)
        else:
            self._x = x = numpy.arange(
                boundingBox[0][0] - space, boundingBox[1][0] + space, space
            )  # *1.1547) gridspacing is already multiplied by 1.1547
            self._y = y = numpy.arange(
                boundingBox[0][1] - space, boundingBox[1][1] + space, space
            )  # *1.1547)
            self._z = z = numpy.arange(
                boundingBox[0][2] - space, boundingBox[1][2] + space, space
            )  # *1.1547)
        nx = len(
            x
        )  # sizes must be +1 or the right, top, and back edges don't get any points using this numpy.arange method
        ny = len(y)
        nz = len(z)
        # Dec 5 2013, we need to confirm that the getPointsInBox function is also using +1, or potential neighbors will be missed
        # This used to be fine, but it may have changed?

        self.nbGridPoints = [nx, ny, nz]
        self.gridVolume = nx * ny * nz
        self.ijkPtIndice = numpy.ndindex(nx, ny, nz)
        # this is 60% faster than the for loop
        #        self.masterGridPositions = numpy.array(list(numpy.broadcast(*numpy.ix_(x, y, z))))
        #        self.masterGridPositions = numpy.vstack(numpy.meshgrid(x,y,z)).reshape(3,-1).T
        self.masterGridPositions = (
            numpy.vstack(numpy.meshgrid(x, y, z, copy=False)).reshape(3, -1).T
        )
        # this ay be faster but don't know the implication

    # from http://stackoverflow.com/questions/18253210/creating-a-numpy-array-of-3d-coordinates-from-three-1d-arrays

    def create3DPointLookupCover(self, boundingBox=None):
        """
        Fill the orthogonal bounding box described by two global corners
        with an array of points spaces pGridSpacing apart. Optimized version using
        numpy broadcasting
        """
        if boundingBox is None:
            boundingBox = self.boundingBox
        space = self.gridSpacing
        S = numpy.array(boundingBox[1]) - numpy.array(boundingBox[0])
        NX, NY, NZ = numpy.around(S / (self.gridSpacing))  # / 1.1547))
        if NX == 0:
            NX = 1
        if NY == 0:
            NY = 1
        if NZ == 0:
            NZ = 1
        self.log.info("using create3DPointLookupCover")
        # we want the diagonal of the voxel, not the diagonal of the plane, so the second 1.1547 is was incorrect
        environmentBoxEqualFillBox = True
        # np.linspace(2.0, 3.0, num=5)
        if environmentBoxEqualFillBox:  # environment.environmentBoxEqualFillBox:
            self._x = x = numpy.linspace(
                boundingBox[0][0], boundingBox[1][0], int(NX)
            )  # *1.1547) gridspacing is already multiplied by 1.1547
            self._y = y = numpy.linspace(
                boundingBox[0][1], boundingBox[1][1], int(NY)
            )  # *1.1547)
            self._z = z = numpy.linspace(
                boundingBox[0][2], boundingBox[1][2], int(NZ)
            )  # *1.1547)
        else:
            self._x = x = numpy.arange(
                boundingBox[0][0], boundingBox[1][0] + space, space
            )  # *1.1547) gridspacing is already multiplied by 1.1547
            self._y = y = numpy.arange(
                boundingBox[0][1], boundingBox[1][1] + space, space
            )  # *1.1547)
            self._z = z = numpy.arange(
                boundingBox[0][2], boundingBox[1][2] + space, space
            )  # *1.1547)
        xyz = numpy.meshgrid(x, y, z, copy=False)
        nx = len(
            x
        )  # sizes must be +1 or the right, top, and back edges don't get any points using this numpy.arange method
        ny = len(y)
        nz = len(z)
        self.gridSpacing = (x[1] - x[0]) * 1.1547  # ? should I multiply here ?
        self.nbGridPoints = [nx, ny, nz]
        self.gridVolume = nx * ny * nz
        self.ijkPtIndice = numpy.ndindex(nx, ny, nz)
        self.masterGridPositions = numpy.vstack(xyz).reshape(3, -1).T

    #        self.masterGridPositions = numpy.vstack(numpy.meshgrid(x,y,z,copy=False)).reshape(3,-1).T

    def getPointCompartmentId(self, point, ray=1):
        # check if point inside on of the compartments
        # surface point ?
        n_comp = len(self.histoVol.compartments)
        if n_comp:
            for i in range(n_comp):
                inside = self.checkPointInside_rapid(
                    self.histoVol.compartments[i],
                    point,
                    self.histoVol.grid.diag,
                    ray=ray,
                )
                if inside:
                    return -(i + 1)
                    # comp=comp-1
            # the point is not inside , is it on the surface ? ie distance to surface < X?
            for i in range(n_comp):
                distance, nb = self.histoVol.compartments[i].OGsrfPtsBht.query(point)
                if distance < 10.0:
                    return i + 1
        return 0

    def getClosestGridPoint(self, pt3d):
        if self.tree is None:
            self.tree = spatial.cKDTree(self.masterGridPositions, leafsize=10)
        distance, nb = self.tree.query(pt3d)  # len of ingr posed so far
        return distance, nb

    def getClosestFreeGridPoint(
        self, pt3d, compId=None, updateTree=True, ball=0.0, distance=0.0
    ):
        free_indices = self.freePoints[: self.nbFreePoints]
        arr = numpy.array(self.masterGridPositions[free_indices])
        indices = numpy.nonzero(numpy.equal(self.gridPtId[free_indices], compId))
        distances = self.distToClosestSurf[free_indices]
        if not len(indices):
            return None
        tree_free = spatial.cKDTree(arr[indices], leafsize=10)
        arr = arr[indices]
        # arr of free indice in compartments
        res = tree_free.query_ball_point(pt3d, ball)  # max distance
        if not len(res):
            return None
        all_distances = distances[res]
        all_pts = arr[res]
        ind = numpy.nonzero(
            numpy.logical_and(
                numpy.greater_equal(all_distances, distance),
                numpy.less(all_distances, distance * 1.5),
            )
        )[0]
        if not len(ind):
            return None
        # should pick closest ?
        targetPoint = all_pts[
            ind[randrange(len(ind))]
        ]  # randomly pick free surface point at given distance
        return targetPoint

        free_indices = self.freePoints[: self.nbFreePoints]
        arr = numpy.array(self.masterGridPositions[free_indices])
        if self.tree_free is None or updateTree:
            if compId is not None:
                arr = numpy.array(self.masterGridPositions[free_indices])
                indices = numpy.nonzero(
                    numpy.equal(self.gridPtId[free_indices], compId)
                )
                self.tree_free = spatial.cKDTree(arr[indices], leafsize=10)
                arr = arr[indices]
            else:
                self.tree_free = spatial.cKDTree(
                    self.masterGridPositions[: self.nbFreePoints], leafsize=10
                )
        if distance != 0.0:
            res = self.tree_free.query_ball_point(pt3d, distance)  #
            return 0, res, arr
        else:
            res = self.tree_free.query(pt3d)  # len of ingr posed so far
            return res, arr

    def cartesian(self, arrays, out=None):
        """
        #http://stackoverflow.com/questions/1208118/using-numpy-to-build-an-array-of-all-combinations-of-two-arrays
        Generate a cartesian product of input arrays.

        Parameters
        ----------
        arrays : list of array-like
            1-D arrays to form the cartesian product of.
        out : ndarray
            Array to place the cartesian product in.

        Returns
        -------
        out : ndarray
            2-D array of shape (M, len(arrays)) containing cartesian products
            formed of input arrays.

        Examples
        --------
        >>> cartesian(([1, 2, 3], [4, 5], [6, 7]))
        array([[1, 4, 6],
               [1, 4, 7],
               [1, 5, 6],
               [1, 5, 7],
               [2, 4, 6],
               [2, 4, 7],
               [2, 5, 6],
               [2, 5, 7],
               [3, 4, 6],
               [3, 4, 7],
               [3, 5, 6],
               [3, 5, 7]])

        """

        arrays = [numpy.asarray(x) for x in arrays]
        dtype = arrays[0].dtype

        n = numpy.prod([x.size for x in arrays])
        if out is None:
            out = numpy.zeros([n, len(arrays)], dtype=dtype)

        m = int(n / arrays[0].size)
        out[:, 0] = numpy.repeat(arrays[0], m)
        if arrays[1:]:
            self.cartesian(arrays[1:], out=out[0:m, 1:])
            for j in range(1, arrays[0].size):
                out[j * m : (j + 1) * m, 1:] = out[0:m, 1:]
        return out

    def getPointFrom3D(self, pt3d):
        """
        get point number from 3d coordinates
        """
        x, y, z = pt3d  # Continuous 3D point to be discretized
        spacing1 = (
            1.0 / self.gridSpacing
        )  # Grid spacing = diagonal of the voxel determined by smallest packing radius
        (
            NX,
            NY,
            NZ,
        ) = (
            self.nbGridPoints
        )  # vector = [length, height, depth] of grid, units = gridPoints
        OX, OY, OZ = self.boundingBox[0]  # origin of fill grid
        # Algebra gives nearest gridPoint ID to pt3D
        i = min(NX - 1, max(0, round((x - OX) * spacing1)))
        j = min(NY - 1, max(0, round((y - OY) * spacing1)))
        k = min(NZ - 1, max(0, round((z - OZ) * spacing1)))
        return int(k * NX * NY + j * NX + i)

    def getIJK(self, ptInd):
        """
        get i,j,k (3d) indices from u (1d)
        only work for grid point, not compartments points
        """
        if ptInd > self.nbGridPoints[0] * self.nbGridPoints[1] * self.nbGridPoints[2]:
            return [0, 0, 0]
        return self.ijkPtIndice[ptInd]

    def setupBoundaryPeriodicity(self):
        # we create a dictionary for the adjacent cell of the current grid.
        self.sizeXYZ = numpy.array(self.boundingBox[1]) - numpy.array(
            self.boundingBox[0]
        )
        self.periodic_table = {}
        self.periodic_table["left"] = (
            numpy.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]) * self.sizeXYZ
        )
        self.periodic_table["right"] = (
            numpy.array([[-1, 0, 0], [0, -1, 0], [0, 0, -1]]) * self.sizeXYZ
        )

    def getPositionPeridocity(self, pt3d, jitter, cutoff):
        tr = []
        if autopack.biasedPeriodicity:
            biased = numpy.array(autopack.biasedPeriodicity)
        else:
            biased = numpy.array(jitter)
        if not autopack.testPeriodicity:
            return tr
        ox, oy, oz = self.boundingBox[0]
        ex, ey, ez = self.boundingBox[1]
        px, py, pz = pt3d
        p_xyz = [0, 0, 0]
        # can I use rapid and find the collision ?

        # distance plane X
        dist_origin_x = px - ox
        dist_edge_x = ex - px
        dx = 0
        if dist_origin_x < dist_edge_x:
            dx = dist_origin_x  # 1
            p_xyz[0] = 1
        else:
            dx = dist_edge_x  # -1
            p_xyz[0] = -1
        if dx < cutoff and dx != 0:
            pass
        else:
            p_xyz[0] = 0
        # distance plane Y
        doy = py - oy
        dey = ey - py
        dy = 0
        if doy < dey:
            dy = doy  # 1
            p_xyz[1] = 1
        else:
            dy = dey  # -1
            p_xyz[1] = -1
        if dy < cutoff and dy != 0.0:
            pass
        else:
            p_xyz[1] = 0
        # distance plane Z
        doz = pz - oz
        dez = ez - pz
        dz = 0
        if doz < dez:
            dz = doz  # 1
            p_xyz[2] = 1
        else:
            dz = dez  # -1
            p_xyz[2] = -1
        if dz < cutoff and dz != 0:
            pass
        else:
            p_xyz[2] = 0
        p_xyz = numpy.array(p_xyz) * biased
        # for 2D we need 3 corner tiles
        # for 3D we need 7 corner tiles
        corner = numpy.zeros((4, 3))
        indices_non_zero = numpy.nonzero(p_xyz)[0]

        for i in indices_non_zero:
            # i is the axis that is close to the point
            tr.append(pt3d + (self.periodic_table["left"][i] * p_xyz[i]))  # 0,1,2
            corner[0] += self.periodic_table["left"][i] * p_xyz[i]  # 1
            # the corner are
            # X+Y+Z corner[0]
            # X+Y+0 corner[1]
            # X+0+Z corner[2]
            # 0+Y+Z corner[3]
        if len(indices_non_zero) == 2:
            # two axis cross-> three pos
            tr.append(pt3d + corner[0])
        if len(indices_non_zero) == 3:
            # in a corner need total 7 pos, never happen in 2D
            corner[1] = (
                self.periodic_table["left"][0] * p_xyz[0]
                + self.periodic_table["left"][1] * p_xyz[1]
            )
            corner[2] = (
                self.periodic_table["left"][0] * p_xyz[0]
                + self.periodic_table["left"][2] * p_xyz[2]
            )
            corner[3] = (
                self.periodic_table["left"][1] * p_xyz[1]
                + self.periodic_table["left"][2] * p_xyz[2]
            )
            for i in range(4):  # 4+1=5
                tr.append(pt3d + corner[i])
        return tr

    def checkPointInside(self, pt3d, dist=None, jitter=[1, 1, 1], bb=None):
        """
        Check if the given 3d points is inside the grid
        """
        if bb is None:
            bb = self.boundingBox
        origin = numpy.array(bb[0])
        edge = numpy.array(bb[1])
        for i in range(len(edge)):
            if edge[i] < self.gridSpacing:
                edge[i] = self.gridSpacing

        packing_location = numpy.array(pt3d)  # *jitter
        test1 = packing_location < origin
        test2 = packing_location > edge
        if True in test1 or True in test2:
            # outside
            return False
        else:
            if dist is not None:
                # distance to closest wall
                d1 = (packing_location - origin) * jitter
                s1 = min(x for x in d1[d1 != 0] if x != 0)
                d2 = (edge - packing_location) * jitter
                s2 = min(x for x in d2[d2 != 0] if x != 0)
                if s1 <= dist or s2 <= dist:
                    self.log.info("s1 s2 smaller than dist %d %d %d", s1, s2, dist)
                    return False
            return True

    def getCenter(self):
        """
        Get the center of the grid
        """
        if self.center is None:
            self.center = [0.0, 0.0, 0.0]
            for i in range(3):
                self.center[i] = (self.boundingBox[0][i] + self.boundingBox[1][i]) / 2.0
        return self.center

    def getRadius(self):
        """
        Get the radius the grid
        """
        d = numpy.array(self.boundingBox[0]) - numpy.array(self.boundingBox[1])
        s = numpy.sum(d * d)
        return math.sqrt(s)

    def getPointsInSphere(self, pt, radius):
        if self.tree is None:
            self.tree = spatial.cKDTree(self.masterGridPositions, leafsize=10)
        # add surface points
        ptIndices = self.tree.query_ball_point(pt, radius)  # , n_jobs=-1)
        return ptIndices

    def getPointsInCubeFillBB(self, bb, pt, radius, addSP=True, info=False):
        """
        Return all grid points indices inside the given bounding box.
        NOTE : need to fix with grid build with numpy arrange
        """
        spacing1 = 1.0 / self.gridSpacing
        NX, NY, NZ = self.nbGridPoints
        OX, OY, OZ = self.boundingBox[
            0
        ]  # origin of fill grid-> bottom lef corner not origin
        ox, oy, oz = bb[0]
        ex, ey, ez = bb[1]

        i0 = int(max(0, floor((ox - OX) * spacing1)))
        i1 = int(min(NX, int((ex - OX) * spacing1)) + 1)

        j0 = int(max(0, floor((oy - OY) * spacing1)))
        j1 = int(min(NY, int((ey - OY) * spacing1)) + 1)

        k0 = int(max(0, floor((oz - OZ) * spacing1)))
        k1 = int(min(NZ, int((ez - OZ) * spacing1)) + 1)

        i0 = int(min(NX - 1, max(0, round((ox - OX) * spacing1))))
        j0 = int(min(NY - 1, max(0, round((oy - OY) * spacing1))))
        k0 = int(min(NZ - 1, max(0, round((oz - OZ) * spacing1))))
        i1 = int(min(NX, max(0, round((ex - OX) * spacing1))))
        j1 = int(min(NY, max(0, round((ey - OY) * spacing1))))
        k1 = int(min(NZ, max(0, round((ez - OZ) * spacing1))))

        if NZ == 1:
            k0 = 0
            k1 = 1
        elif NY == 1:
            j0 = 0
            j1 = 1
        elif NX == 1:
            i0 = 0
            i1 = 1

        ptIndices = []
        pid = numpy.mgrid[i0:i1, j0:j1, k0:k1]
        ijk = numpy.vstack(pid).reshape(3, -1).T
        # in case 2D, meaning one of the dimension is 1
        if NZ == 1:
            ptIndices = [p[2] + p[1] + NX * p[0] for p in ijk]
        elif NY == 1:
            ptIndices = [p[2] + p[1] + NX * p[0] for p in ijk]
        elif NX == 1:
            ptIndices = [p[2] + NY * p[1] + p[0] for p in ijk]
        else:
            0.02451198
        # add surface points
        if addSP and self.nbSurfacePoints != 0:
            result = numpy.zeros((self.nbSurfacePoints,), "i")
            nb = self.surfPtsBht.closePoints(tuple(pt), radius, result)
            #            nb = self.surfPtsBht.query(tuple(pt),k=self.nbSurfacePoints)
            ptIndices.extend(
                list(map(lambda x, length=self.gridVolume: x + length, result[:nb]))
            )
        return ptIndices

    def test_points_in_bb(self, bb, pt):
        # given a bounding box, does the point is contains in it
        origin = numpy.array(bb[0])
        E = numpy.array(bb[1])
        P = numpy.array(pt)  # *jitter
        test1 = P < origin
        test2 = P > E
        inside = False
        if True in test1 or True in test2:
            # outside
            inside = False
        return inside

    def getPointsInCube(self, bb, pt, radius, addSP=True, info=False):
        """
        Return all grid points indicesinside the given bounding box.
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
        encapsulatingGrid = self.encapsulatingGrid
        # Graham Added on Oct17 to allow for truly 2D grid for test fills... may break everything!
        nx = int(ceil((xr - xl) / space)) + encapsulatingGrid
        ny = int(ceil((yr - yl) / space)) + encapsulatingGrid
        nz = int(ceil((zr - zl) / space)) + encapsulatingGrid
        #        nx = nx if (nx == 1) else nx-1
        #        ny = ny if (ny == 1) else ny-1
        #        nz = nz if (nz == 1) else nz-1
        return nx * ny * nz, (nx, ny, nz)

    def set_surfPtsBht(self, verts):
        self.surfPtsBht = None
        if verts is not None and len(verts):
            self.surfPtsBht = bhtreelib.BHtree(verts, None, 10)
        self.nbSurfacePoints = len(verts)

    def set_surfPtscht(self, verts):

        self.surfPtsBht = None
        if verts is not None and len(verts):
            self.surfPtsBht = spatial.cKDTree(verts, leafsize=10)
        self.nbSurfacePoints = len(verts)

    def computeExteriorVolume(self, compartments=None, space=None, fbox_bb=None):
        # compute exterior volume, totalVolume without compartments volume
        unitVol = self.gridSpacing**3
        totalVolume = self.gridVolume * unitVol
        if fbox_bb is not None:
            V, nbG = self.computeGridNumberOfPoint(fbox_bb, space)
            totalVolume = V * unitVol
        if compartments is not None:
            for o in compartments:
                # totalVolume -= o.surfaceVolume
                totalVolume -= o.interiorVolume
        return totalVolume

    def computeVolume(self, space=None, fbox_bb=None):
        # compute exterior volume, totalVolume without compartments volume
        unitVol = self.gridSpacing**3
        totalVolume = self.gridVolume * unitVol
        if fbox_bb is not None:
            V, nbG = self.computeGridNumberOfPoint(fbox_bb, space)
            totalVolume = V * unitVol
        return totalVolume

    def create_rapid_model(self):
        self.rapid_model = RAPIDlib.RAPID_model()
        # need triangle and vertices
        self.rapid_model.addTriangles(
            numpy.array(self.vertices, "f"), numpy.array(self.faces, "i")
        )

    def get_rapid_model(self):
        if self.rapid_model is None:
            self.create_rapid_model()
        return self.rapid_model

    def one_rapid_ray(self, pt1, pt2, diag):
        # return number of triangle /triangle contact
        helper = autopack.helper
        rm = self.get_rapid_model()
        v1 = numpy.array(pt1)
        direction = helper.unit_vector(pt2 - pt1) * diag
        v2 = v1 + direction
        if sum(v1) == 0.0:
            v3 = v2 + numpy.array([0.0, 1.0, 0.0])
        else:
            v3 = v2 + helper.unit_vector(numpy.cross(v1, v2))
        f = [0, 1, 2]
        ray_model = RAPIDlib.RAPID_model()
        ray_model.addTriangles(
            numpy.array([v1, v2, v3], "f"),
            numpy.array(
                [f],
                "i",
            ),
        )
        RAPIDlib.RAPID_Collide_scaled(
            numpy.identity(3),
            numpy.array([0.0, 0.0, 0.0], "f"),
            1.0,
            rm,
            numpy.identity(3),
            numpy.array([0.0, 0.0, 0.0], "f"),
            1.0,
            ray_model,
            RAPIDlib.cvar.RAPID_ALL_CONTACTS,
        )
        # could display it ?
        return RAPIDlib.cvar.RAPID_num_contacts

    def checkPointInside_rapid(self, point, diag, ray=1):
        # we want to be sure to cover the organelle
        if diag < self.diag:
            diag = self.diag
        inside = False
        v1 = numpy.array(point)
        self.getCenter()
        count1 = self.one_rapid_ray(v1, v1 + numpy.array([0.0, 0.0, 1.1]), diag)
        r = (count1 % 2) == 1  # inside ?
        # we need 2 out of 3 ?
        if ray == 3:
            count2 = self.one_rapid_ray(v1, numpy.array(self.center), diag)
            if (count2 % 2) == 1 and r:
                return True
            count3 = self.one_rapid_ray(v1, v1 + numpy.array([0.0, 1.1, 0.0]), diag)
            if (count3 % 2) == 1 and r:
                return True
            return False
        if r:  # odd inside
            inside = True
        return inside

    def getSurfaceInnerPoints_jordan(self, vertices, faces, ray=1):
        """
        Only computes the inner point. No grid.
        This is independent from the packing. Help build ingredient sphere tree and representation.
        - Uses BHTree to compute surface points
        - Uses Jordan raycasting to determine inside/outside (defaults to 1 iteration, can use 3 iterations)
        """
        self.vertices = vertices
        self.faces = faces
        self.rapid_model = None
        self.center = None
        xl, yl, zl = self.boundingBox[0]  # lower left bounding box corner
        xr, yr, zr = self.boundingBox[1]  # upper right bounding box corner
        # distToClosestSurf is set to self.diag initially
        distances = self.distToClosestSurf
        diag = self.diag

        # Get surface points using bhtree (stored in bht and OGsrfPtsBht)
        # otherwise, regard vertices as surface points.

        self.ogsurfacePoints = vertices[
            :
        ]  # Makes a copy of the vertices and vnormals lists
        surfacePoints = srfPts = self.ogsurfacePoints

        # self.OGsrfPtsBht = bht =  bhtreelib.BHtree(tuple(srfPts), None, 10)
        self.OGsrfPtsBht = bht = spatial.cKDTree(tuple(srfPts), leafsize=10)

        insidePoints = []
        grdPos = self.masterGridPositions
        closest = bht.query(tuple(grdPos))

        self.closestId = closest[1]
        new_distances = closest[0]
        mask = distances[: len(grdPos)] > new_distances
        n_indices = numpy.nonzero(mask)
        distances[n_indices] = new_distances[n_indices]
        self.grid_distances = distances
        # returnNullIfFail = 0
        for ptInd in range(len(grdPos)):  # len(grdPos)):
            inside = False  # inside defaults to False (meaning outside), unless evidence is found otherwise.
            # t2=time()
            coord = [
                grdPos.item((ptInd, 0)),
                grdPos.item((ptInd, 1)),
                grdPos.item((ptInd, 2)),
            ]  # grdPos[ptInd]
            insideBB = self.checkPointInside(
                coord, dist=new_distances.item(ptInd)
            )  # inside the BB of the surface ?
            if insideBB:
                r = self.checkPointInside_rapid(coord, diag, ray=ray)
                if r:  # odd inside
                    insidePoints.append(
                        grdPos[ptInd]
                    )  # Append the index to the list of inside indices.
            p = (ptInd / float(len(grdPos))) * 100.0
            if (ptInd % 100) == 0:
                self.log.info(
                    "points from jordan",
                    int(p),
                    str(ptInd)
                    + "/"
                    + str(len(grdPos))
                    + " inside "
                    + str(inside)
                    + " "
                    + str(insideBB),
                )
        return insidePoints, surfacePoints

        # ==============================================================================

    # TO DO File IO
    # ==============================================================================
    def save(self):
        pass

    def restore(self):
        pass


# don't forget to use spatial.distance.cdist
class HaltonGrid(BaseGrid):
    def __init__(self, boundingBox=([0, 0, 0], [0.1, 0.1, 0.1]), space=1, setup=False):
        BaseGrid.__init__(
            self, boundingBox=boundingBox, space=space, setup=setup, lookup=1
        )
        self.haltonseq = cHaltonSequence3()
        self.tree = None
        self.lookup = 1
        self.gridSpacing = space
        if setup:
            self.setup(boundingBox, space)

    def getPointFrom3D(self, pt3d):
        """
        get point number from 3d coordinates
        """
        # actually look at closest point using ckd tree
        # nb = self.tree.query_ball_point(point,cutoff)
        nb = self.tree.query(pt3d, 1)  # len of ingr posed so far
        return nb

    def getScale(self, boundingBox=None):
        if boundingBox is None:
            boundingBox = self.boundingBox
        t_xyz = numpy.array(boundingBox[0])
        scale_xyz = numpy.array(boundingBox[1]) - t_xyz
        return scale_xyz, t_xyz

    def getNBgridPoints(
        self,
    ):
        a = numpy.array(self.boundingBox[0])
        b = numpy.array(self.boundingBox[1])
        lx = abs(int((a[0] - b[0]) / self.gridSpacing))
        ly = abs(int((a[1] - b[1]) / self.gridSpacing))
        lz = abs(int((a[2] - b[2]) / self.gridSpacing))
        return [lx, ly, lz]

    def create3DPointLookup(self, boundingBox=None):
        # we overwrite here by using the halton sequence dimension 5 to get
        # the coordinate
        self.haltonseq.reset()
        self.nbGridPoints = self.getNBgridPoints()
        nx, ny, nz = self.nbGridPoints
        pointArrayRaw = numpy.zeros((nx * ny * nz, 3), "f")
        self.ijkPtIndice = numpy.zeros((nx * ny * nz, 3), "i")
        scale_xyz, t_xyz = self.getScale()
        i = 0
        for zi in range(nz):
            for yi in range(ny):
                for xi in range(nx):
                    self.haltonseq.inc()
                    pointArrayRaw[i] = numpy.array(
                        [self.haltonseq.mX, self.haltonseq.mY, self.haltonseq.mZ]
                    )
                    self.ijkPtIndice[i] = (xi, yi, zi)
                    i += 1
        # scale the value from the halton(0...1) to grid bounding box
        self.masterGridPositions = pointArrayRaw * scale_xyz + t_xyz
        self.tree = spatial.cKDTree(self.masterGridPositions, leafsize=10)

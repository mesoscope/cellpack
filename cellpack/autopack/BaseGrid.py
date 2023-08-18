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
    3d positions, distances, free_points and inside/surface points from organelles.
    NOTE : thi class could be completely replace if openvdb is wrapped to python.
    """

    @staticmethod
    def reorder_free_points(pt, free_points, nbFreePoints):
        # Swap the newly inside point value with the value of the last free point
        # Point will no longer be considered "free" because it will be beyond the range of
        # nbFreePoints. The value of the point itself is the history of it's original index
        # so any future swaps will still result in the correct index being move into the range
        # of nbFreePoints
        nbFreePoints -= 1
        vKill = free_points[pt]
        vLastFree = free_points[nbFreePoints]
        free_points[vKill] = vLastFree
        free_points[vLastFree] = vKill
        # Turn on these printlines if there is a problem with incorrect points showing in display points
        # self.log.debug("*************pt = masterGridPointValue = %d", pt)
        # self.log.debug("nbFreePointAfter = %d", nbFreePoints)
        # self.log.debug("vKill = %d", vKill)
        # self.log.debug("vLastFree = %d", vLastFree)
        # self.log.debug("free_points[vKill] = %d", free_points[vKill])
        # self.log.debug("free_points[vLastFree] = %d", free_points[vLastFree])
        # self.log.debug("pt = masterGridPointValue = %d", pt)
        # self.log.debug("free_points[nbFreePoints-1] = %d", free_points[nbFreePoints])
        # self.log.debug("free_points[pt] = %d", free_points[pt])
        # free_points will now have all the available indices between 0 and nbFreePoints in
        # free_points[nbFreePoints:] won't necessarily be the indices of inside points
        return free_points, nbFreePoints

    @staticmethod
    def updateDistances(
        insidePoints,
        newDistPoints,
        free_points,
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
                free_points, nbFreePoints = BaseGrid.reorder_free_points(
                    pt, free_points, nbFreePoints
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
        self, boundingBox=([0, 0, 0], [0.1, 0.1, 0.1]), spacing=20, setup=True
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
        self.compartment_ids = []
        # will be a list of indices into 3D of compartment
        # of points that have not yet been used by the fill algorithm
        # entries are removed from this list as grid points are used up
        # during hte fill. This list is used to pick points randomly during
        # the fill
        self.free_points = []
        self.nbFreePoints = 0
        # this list evolves in parallel with self.free_points and provides
        # the distance to the closest surface (either an already placed
        # object (or an compartment surface NOT IMPLEMENTED)
        self.distToClosestSurf = []
        self.distToClosestSurf_store = []
        self.diag = self.getDiagonal()
        self.gridSpacing = spacing  # #cubic grid with a diagonal spacing equal to that smallest packing radius
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
        # Treee
        self.surfPtsBht = None
        self.ijkPtIndice = []
        self.filename = None  # used for storing before fill so no need rebuild
        self.result_filename = None  # used after fill to store result
        self.tree = None
        self.tree_free = None
        self.encapsulatingGrid = 0
        self.center = None
        self.backup = None
        if setup:
            self.setup(self.boundingBox)
            # use np.roll to have periodic condition
            # what about collision ?

    def setup(self, boundingBox):
        # TODO : verify the gridSpacing calculation / setup after reading the recipe

        self.boundingBox = boundingBox

        self.create_grid_point_positions()
        nx, ny, nz = self.nbGridPoints
        self.ijkPtIndice = self.cartesian([range(nx), range(ny), range(nz)])

        self.getDiagonal()
        self.nbSurfacePoints = 0
        self.log.info(f"SETUP BASE GRID {self.gridVolume} {self.gridSpacing}")
        self.compartment_ids = numpy.zeros(self.gridVolume, "i")  # [0]*nbPoints
        # self.distToClosestSurf = [self.diag]*self.gridVolume#surface point too?
        self.distToClosestSurf = (
            numpy.ones(self.gridVolume) * self.diag
        )  # (self.distToClosestSurf)
        self.free_points = list(range(self.gridVolume))
        self.nbFreePoints = len(self.free_points)
        self.log.info(
            "gridSpacing %r, length compartment_ids %r",
            self.gridSpacing,
            len(self.compartment_ids),
        )
        self.setupBoundaryPeriodicity()
        return self.gridSpacing

    def reset(
        self,
    ):
        # reset the  distToClosestSurf and the free_points
        # boundingBox should be the same otherwise why keeping the grid
        self.log.info("reset Grid distance to closest surface and free_points")
        self.distToClosestSurf = (
            numpy.array(self.distToClosestSurf[:]) * 0.0
        ) + self.diag
        # self.distToClosestSurf[:] = self.diag  # numpy.array([self.diag]*len(self.distToClosestSurf))#surface point too?
        self.free_points = list(range(len(self.free_points)))
        self.nbFreePoints = len(self.free_points)

    def removeFreePoint(self, pti):
        tmp = self.free_points[self.nbFreePoints]  # last one
        self.free_points[self.nbFreePoints] = pti
        self.free_points[pti] = tmp
        self.nbFreePoints -= 1

    def getDiagonal(self, boundingBox=None):
        if boundingBox is None:
            boundingBox = self.boundingBox
        self.diag = numpy.linalg.norm(
            (numpy.array(boundingBox[0]) - numpy.array(boundingBox[1]))
        )
        return self.diag

    def slow_box_fill(self, boundingBox=None):
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
        self.log.info(f"grid spacing {space}")
        self.masterGridPositions = pointArrayRaw

    # from http://stackoverflow.com/questions/18253210/creating-a-numpy-array-of-3d-coordinates-from-three-1d-arrays

    def create_grid_point_positions(self, boundingBox=None):
        """
        Fill the orthogonal bounding box described by two global corners
        with an array of points spaces pGridSpacing apart. Optimized version using
        numpy broadcasting
        """
        if boundingBox is None:
            boundingBox = self.boundingBox
        space = self.gridSpacing
        padding = space / 2.0
        grid_dimensions = [[], [], []]
        for axis in range(len(grid_dimensions)):
            start = boundingBox[0][axis] + padding
            stop = boundingBox[1][axis]
            if stop < start:
                # bounding box is smaller than grid spacing, ie in 2D packings
                grid_dimensions[axis] = numpy.array(
                    [(boundingBox[0][axis] + boundingBox[1][axis]) / 2]
                )
            else:
                grid_dimensions[axis] = numpy.arange(start, stop, space)

        self.log.info("using create_grid_point_positions")

        self._x = x = grid_dimensions[0]
        self._y = y = grid_dimensions[1]
        self._z = z = grid_dimensions[2]

        xyz = numpy.meshgrid(x, y, z, copy=False)
        nx = len(
            x
        )  # sizes must be +1 or the right, top, and back edges don't get any points using this numpy.arange method
        ny = len(y)
        nz = len(z)
        self.gridSpacing = x[1] - x[0]

        self.nbGridPoints = [nx, ny, nz]
        self.gridVolume = nx * ny * nz
        self.ijkPtIndice = numpy.ndindex(nx, ny, nz)
        self.masterGridPositions = numpy.vstack(xyz).reshape(3, -1).T

    def getClosestGridPoint(self, pt3d):
        if self.tree is None:
            self.tree = spatial.cKDTree(self.masterGridPositions, leafsize=10)
        distance, nb = self.tree.query(pt3d)  # len of ingr posed so far
        return distance, nb

    def getClosestFreeGridPoint(
        self, pt3d, compId=None, updateTree=True, ball=0.0, distance=0.0
    ):
        free_indices = self.free_points[: self.nbFreePoints]
        arr = numpy.array(self.masterGridPositions[free_indices])
        indices = numpy.nonzero(numpy.equal(self.compartment_ids[free_indices], compId))
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

        free_indices = self.free_points[: self.nbFreePoints]
        arr = numpy.array(self.masterGridPositions[free_indices])
        if self.tree_free is None or updateTree:
            if compId is not None:
                arr = numpy.array(self.masterGridPositions[free_indices])
                indices = numpy.nonzero(
                    numpy.equal(self.compartment_ids[free_indices], compId)
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

    def is_point_inside_bb(self, pt3d, dist=None, jitter=[1, 1, 1], bb=None):
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
        # given a bounding box bb, is point pt inside it
        origin = numpy.array(bb[0])
        corner = numpy.array(bb[1])
        point_to_check = numpy.array(pt)  # *jitter
        test1 = point_to_check < origin
        test2 = point_to_check > corner
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
            self.surfPtsBht = spatial.cKDTree(verts, leafsize=10)
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
        BaseGrid.__init__(self, boundingBox=boundingBox, spacing=space, setup=setup)
        self.haltonseq = cHaltonSequence3()
        self.tree = None
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

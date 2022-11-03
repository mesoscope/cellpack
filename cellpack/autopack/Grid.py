from cellpack.autopack.BaseGrid import BaseGrid

import numpy


class Grid(BaseGrid):
    """
    The Grid class
    ==========================
    This class handle the use of grid to control the packing. The grid keep information
    of 3d positions, distances, free_points and inside/surface points from organelles.
    NOTE : this class could be completely replaced if openvdb is wrapped to python.
    """

    def __init__(self, boundingBox=([0, 0, 0], [0.1, 0.1, 0.1]), space=10.0, lookup=0):
        # a grid is attached to an environnement
        BaseGrid.__init__(
            self, boundingBox=boundingBox, spacing=space, setup=False, lookup=lookup
        )

        self.gridSpacing = space
        self.encapsulatingGrid = 1
        self.gridVolume, self.nbGridPoints = self.computeGridNumberOfPoint(
            boundingBox, space
        )
        self.create3DPointLookup()
        self.free_points = list(range(self.gridVolume))
        self.nbFreePoints = len(self.free_points)

    def reset(self):
        # reset the  distToClosestSurf and the free_points
        # boundingBox shoud be the same otherwise why keeping the grid

        self.distToClosestSurf[:] = self.diag
        self.free_points = list(range(len(self.free_points)))
        self.nbFreePoints = len(self.free_points)
        self.distancesAfterFill = []
        self.freePointsAfterFill = []
        self.nbFreePointsAfterFill = []
        self.distanceAfterFill = []

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

    def getIJK(self, ptInd):
        """
        get i,j,k (3d) indices from u (1d)
        """
        # ptInd = k*(sizex)*(sizey)+j*(sizex)+i;#want i,j,k
        return self.ijkPtIndice[ptInd]
        # ==============================================================================

    # TO DO File IO
    # ==============================================================================
    def save(self):
        pass

    def restore(self):
        pass

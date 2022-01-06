# -*- coding: utf-8 -*-

import numpy
from scipy import spatial
from numpy import matrix
from math import sqrt
from panda3d.core import Point3, TransformState
from panda3d.bullet import BulletSphereShape, BulletRigidBodyNode
from random import uniform, gauss, random
from time import time
import math

from cellpack.mgl_tools.bhtree import bhtreelib
from cellpack.autopack.transformation import angle_between_vectors
from cellpack.autopack.ldSequence import SphereHalton
from cellpack.autopack.BaseGrid import BaseGrid as BaseGrid
from .utils import rotVectToVect

import cellpack.autopack as autopack

from .multi_cylinder import MultiCylindersIngr

helper = autopack.helper


class GrowIngredient(MultiCylindersIngr):
    def __init__(
        self,
        molarity=0.0,
        radii=None,
        positions=None,
        positions2=None,
        sphereFile=None,
        packingPriority=0,
        name=None,
        pdb=None,
        color=None,
        nbJitter=5,
        jitterMax=(1, 1, 1),
        perturbAxisAmplitude=0.1,
        length=10.0,
        closed=False,
        modelType="Cylinders",
        biased=1.0,
        principalVector=(1, 0, 0),
        meshFile=None,
        packingMode="random",
        placeType="jitter",
        marge=20.0,
        meshObject=None,
        orientation=(1, 0, 0),
        nbMol=0,
        Type="Grow",
        walkingMode="sphere",
        **kw
    ):

        MultiCylindersIngr.__init__(
            self,
            molarity=molarity,
            radii=radii,
            positions=positions,
            positions2=positions2,
            sphereFile=sphereFile,
            packingPriority=packingPriority,
            name=name,
            pdb=pdb,
            color=color,
            nbJitter=nbJitter,
            jitterMax=jitterMax,
            perturbAxisAmplitude=perturbAxisAmplitude,
            principalVector=principalVector,
            meshFile=meshFile,
            packingMode=packingMode,
            placeType=placeType,
            meshObject=meshObject,
            nbMol=nbMol,
            Type=Type,
            **kw
        )
        if name is None:
            name = "%s_%f" % (str(radii), molarity)
        self.name = name
        self.singleSphere = False
        self.modelType = modelType
        self.collisionLevel = 0
        self.minRadius = self.radii[0][0]
        self.encapsulatingRadius = self.radii[0][0]
        self.marge = marge
        self.length = length
        self.closed = closed
        self.nbCurve = 0
        self.results = []
        self.start_positions = []
        self.listePtLinear = []
        self.listePtCurve = []  # snake
        self.Ptis = []  # snakePts
        self.startGridPoint = []
        self.currentLength = 0.0  # snakelength
        self.direction = None  # direction of growing
        # can be place either using grid point/jittering or dynamics
        #        self.uLength = 0. #length of the cylinder or averall radius for sphere, this is the lenght of one unit
        self.uLength = 0
        if "uLength" in kw:
            self.uLength = kw["uLength"]
        if self.positions2 is None:
            if self.uLength == 0:
                self.uLength = self.radii[0][0]
            self.vector = numpy.array(self.principalVector) * self.uLength / 2.0
            self.positions = [[(self.vector * -1.0).tolist()]]
            self.positions2 = [[self.vector.tolist()]]
        else:
            if self.positions2 is not None:
                v, u = self.vi.measure_distance(
                    self.positions, self.positions2, vec=True
                )
                self.uLength = abs(u)
            else:
                self.uLength = self.radii[0][0]
        self.encapsulatingRadius = self.uLength / 2.0
        self.unitNumberF = 0  # number of unit pose so far forward
        self.unitNumberR = 0  # number of unit pose so far reverse
        self.orientation = orientation
        self.seedOnPlus = True  # The filament should continue to grow on its (+) end
        self.seedOnMinus = False  # The filamen should continue to grow on its (-) end.
        #        if self.compNum > 0 :
        #            self.seedOnMinus = False
        self.vector = [0.0, 0.0, 0.0]
        self.biased = biased
        self.absoluteLengthMax = 99999999.9999  # (default value is infinite or some safety number like 1billion)
        self.probableLengthEquation = None
        # (this can be a number or an equation, e.g., every actin should grow to
        # 10 units long, or this actin fiber seed instance should grow to (random*10)^2
        # actually its a function of self.uLength like self.uLength * 10. or *(random*10)^2
        self.ingGrowthMatrix = numpy.identity(4)
        # (ultimately, we'll build a database for these (David Goodsell has a few examples),
        # but users should be able to put in their own, so for a test for now, lets say we'll
        # grow one unit for a singleSphereIng r=60 along its X as [55,0,0;1,0,0;0,1,0;0,0,1]
        self.ingGrowthWobbleFormula = None
        # (this could be a rotation matrix to make a helix, or just a formula,
        # like the precession algorithm Michel and I already put in
        # for surface ingredients.
        self.constraintMarge = False
        self.cutoff_boundary = 1.0
        self.cutoff_surface = 5.0
        self.useHalton = True
        self.use_rbsphere = (
            False  # use sphere instead of cylinder or collision with bullet
        )
        if "useHalton" in kw:
            self.useHalton = kw["useHalton"]
        if "constraintMarge" in kw:
            self.constraintMarge = kw["constraintMarge"]
        if "cutoff_boundary" in kw:
            self.cutoff_boundary = kw["cutoff_boundary"]
        if "cutoff_surface" in kw:
            self.cutoff_surface = kw["cutoff_surface"]
        if "use_rbsphere" in kw:
            self.use_rbsphere = kw["use_rbsphere"]
        if "encapsulatingRadius" in kw:
            self.use_rbsphere = kw["encapsulatingRadius"]
        # mesh object representing one uLength? or a certain length
        self.unitParent = None
        self.unitParentLength = 0.0
        self.walkingMode = walkingMode  # ["sphere","lattice"]
        self.walkingType = "stepbystep"  # or atonce
        self.compMask = []
        self.prev_v3 = []
        # default should be compId
        if "compMask" in kw:
            if type(kw["compMask"]) is str:
                self.compMask = eval(kw["compMask"])
            else:
                self.compMask = kw["compMask"]
        # create a simple geom if none pass?
        # self.compMask=[]
        if self.mesh is None and autopack.helper is not None:
            p = None
            if not autopack.helper.nogui:
                # build a cylinder and make it length uLength, radius radii[0]
                # this mesh is used bu RAPID for collision
                p = autopack.helper.getObject("autopackHider")
                if p is None:
                    p = autopack.helper.newEmpty("autopackHider")
                    if autopack.helper.host.find("blender") == -1:
                        autopack.helper.toggleDisplay(p, False)
            # is axis working ?
            self.mesh = autopack.helper.Cylinder(
                self.name + "_basic",
                radius=self.radii[0][0] * 1.24,
                length=self.uLength,
                res=32,
                parent="autopackHider",
                axis=self.orientation,
            )[0]
            if autopack.helper.nogui:
                self.getData()
        self.sphere_points_nb = 50000
        self.sphere_points = numpy.array(SphereHalton(self.sphere_points_nb, 5))
        self.sphere_points_mask = numpy.ones(self.sphere_points_nb, "i")
        self.sphere_points_masked = None

        # need to define the binder/modifier. This is different from partner
        # Every nth place alternative repesentation
        # name proba is this for ingredient in general ?
        self.alternates_names = []
        if "alternates_names" in kw:
            self.alternates_names = kw["alternates_names"]
        self.alternates_proba = []
        if "alternates_proba" in kw:
            self.alternates_proba = kw["alternates_proba"]
        self.alternates_weight = []
        if "alternates_weight" in kw:
            self.alternates_weight = kw["alternates_weight"]
        self.prev_alt = None
        self.prev_was_alternate = False
        self.prev_alt_pt = None
        self.mini_interval = 2
        self.alternate_interval = 0
        # keep record of point Id that are bound to alternate and change the
        # representation according.
        self.safetycutoff = 10

        self.KWDS["length"] = {}
        self.KWDS["closed"] = {}
        self.KWDS["uLength"] = {}
        self.KWDS["biased"] = {}
        self.KWDS["marge"] = {}
        self.KWDS["orientation"] = {}
        self.KWDS["walkingMode"] = {}
        self.KWDS["constraintMarge"] = {}
        self.KWDS["useHalton"] = {}
        self.KWDS["compMask"] = {}
        self.KWDS["use_rbsphere"] = {}

        self.OPTIONS["length"] = {
            "name": "length",
            "value": self.length,
            "default": self.length,
            "type": "float",
            "min": 0,
            "max": 10000,
            "description": "snake total length",
        }
        self.OPTIONS["uLength"] = {
            "name": "uLength",
            "value": self.uLength,
            "default": self.uLength,
            "type": "float",
            "min": 0,
            "max": 10000,
            "description": "snake unit length",
        }
        self.OPTIONS["closed"] = {
            "name": "closed",
            "value": False,
            "default": False,
            "type": "bool",
            "min": 0.0,
            "max": 0.0,
            "description": "closed snake",
        }
        self.OPTIONS["biased"] = {
            "name": "biased",
            "value": 0.0,
            "default": 0.0,
            "type": "float",
            "min": 0,
            "max": 10,
            "description": "snake biased",
        }
        self.OPTIONS["marge"] = {
            "name": "marge",
            "value": 10.0,
            "default": 10.0,
            "type": "float",
            "min": 0,
            "max": 10000,
            "description": "snake angle marge",
        }
        self.OPTIONS["constraintMarge"] = {
            "name": "constraintMarge",
            "value": False,
            "default": False,
            "type": "bool",
            "min": 0.0,
            "max": 0.0,
            "description": "lock the marge",
        }
        self.OPTIONS["orientation"] = {
            "name": "orientation",
            "value": [0.0, 1.0, 0.0],
            "default": [0.0, 1.0, 0.0],
            "min": 0,
            "max": 1,
            "type": "vector",
            "description": "snake orientation",
        }
        self.OPTIONS["walkingMode"] = {
            "name": "walkingMode",
            "value": "random",
            "values": ["sphere", "lattice"],
            "min": 0.0,
            "max": 0.0,
            "default": "sphere",
            "type": "liste",
            "description": "snake mode",
        }
        self.OPTIONS["useHalton"] = {
            "name": "useHalton",
            "value": True,
            "default": True,
            "type": "bool",
            "min": 0.0,
            "max": 0.0,
            "description": "use spherica halton distribution",
        }
        self.OPTIONS["compMask"] = {
            "name": "compMask",
            "value": "0",
            "values": "0",
            "min": 0.0,
            "max": 0.0,
            "default": "0",
            "type": "string",
            "description": "allowed compartments",
        }
        self.OPTIONS["use_rbsphere"] = {
            "name": "use_rbsphere",
            "value": False,
            "default": False,
            "type": "bool",
            "min": 0.0,
            "max": 0.0,
            "description": "use sphere instead of cylinder wih bullet",
        }

    def get_new_distance_values(
        self, jtrans, rotMatj, gridPointsCoords, distance, dpad, level=0
    ):
        insidePoints = {}
        newDistPoints = {}
        cent1T = self.transformPoints(jtrans, rotMatj, self.positions[-1])
        cent2T = self.transformPoints(jtrans, rotMatj, self.positions2[-1])

        for radc, p1, p2 in zip(self.radii[-1], cent1T, cent2T):

            x1, y1, z1 = p1
            x2, y2, z2 = p2
            vx, vy, vz = vect = (x2 - x1, y2 - y1, z2 - z1)
            lengthsq = vx * vx + vy * vy + vz * vz
            length = sqrt(lengthsq)
            cx, cy, cz = posc = x1 + vx * 0.5, y1 + vy * 0.5, z1 + vz * 0.5
            radt = length + radc + dpad
            bb = ([cx - radt, cy - radt, cz - radt], [cx + radt, cy + radt, cz + radt])
            pointsInCube = self.env.callFunction(
                self.env.grid.getPointsInCube, (bb, posc, radt)
            )

            pd = numpy.take(gridPointsCoords, pointsInCube, 0) - p1
            dotp = numpy.dot(pd, vect)
            d2toP1 = numpy.sum(pd * pd, 1)
            dsq = d2toP1 - dotp * dotp / lengthsq

            pd2 = numpy.take(gridPointsCoords, pointsInCube, 0) - p2
            d2toP2 = numpy.sum(pd2 * pd2, 1)

            for pti, pt in enumerate(pointsInCube):
                if pt in insidePoints:
                    continue

                if dotp[pti] < 0.0:  # outside 1st cap
                    d = sqrt(d2toP1[pti])
                    if d < distance[pt]:  # point in region of influence
                        if pt in newDistPoints:
                            if d < newDistPoints[pt]:
                                newDistPoints[pt] = d
                        else:
                            newDistPoints[pt] = d
                elif dotp[pti] > lengthsq:
                    d = sqrt(d2toP2[pti])
                    if d < distance[pt]:  # point in region of influence
                        if pt in newDistPoints:
                            if d < newDistPoints[pt]:
                                newDistPoints[pt] = d
                        else:
                            newDistPoints[pt] = d
                else:
                    d = sqrt(dsq[pti]) - radc
                    if d < 0.0:  # point is inside dropped sphere
                        if pt in insidePoints:
                            if d < insidePoints[pt]:
                                insidePoints[pt] = d
                        else:
                            insidePoints[pt] = d
        return insidePoints, newDistPoints

    def resetSphereDistribution(self):
        # given a radius, create the sphere distribution
        self.sphere_points = SphereHalton(self.sphere_points_nb, 5)
        self.sphere_points_mask = numpy.ones(self.sphere_points_nb, "i")

    def getNextPoint(self):
        # pick a random point from the sphere point distribution
        pointsmask = numpy.nonzero(self.sphere_points_mask)[0]
        if not len(pointsmask):
            print("no sphere point available from mask")
            return None
        ptIndr = int(uniform(0.0, 1.0) * len(pointsmask))
        sp_pt_indice = pointsmask[ptIndr]
        np = numpy.array(self.sphere_points[sp_pt_indice]) * numpy.array(self.jitterMax)
        return (
            numpy.array(self.vi.unit_vector(np)) * self.uLength
        )  # biased by jitterMax ?

    def mask_sphere_points_boundary(self, pt, boundingBox=None):
        if boundingBox is None:
            boundingBox = self.env.fillBB
        pts = (numpy.array(self.sphere_points) * self.uLength) + pt
        points_mask = numpy.nonzero(self.sphere_points_mask)[0]
        if len(points_mask):
            mask = [not self.point_is_not_available(pt) for pt in pts[points_mask]]
            if len(mask):
                self.sphere_points_mask[points_mask] = numpy.logical_and(
                    mask, self.sphere_points_mask[points_mask]
                )

    def mask_sphere_points_ingredients(self, pt, listeclosest):
        listeclosest = [
            elem
            for elem in listeclosest
            if not isinstance(elem[3], autopack.Compartment.Compartment)
        ]
        points_mask = numpy.nonzero(self.sphere_points_mask)[0]
        if len(listeclosest) and len(points_mask):
            points = numpy.array(listeclosest)[:, 1]
            ingrs = numpy.array(listeclosest)[:, 3]
            radius = [float(ingr.encapsulatingRadius) for ingr in ingrs]
            # this distance is between unit vector and 3d points...
            # translate and scale the spheres points
            sp = numpy.array(self.sphere_points, dtype=numpy.float64, copy=False)
            dp = sp[points_mask] * self.uLength + pt
            pts = numpy.array(points.tolist(), dtype=numpy.float64, copy=False)
            # distance between sphere point and ingredient positions
            distances = spatial.distance.cdist(pts, dp)
            # empty mask for the point
            mask = numpy.nonzero(numpy.ones(len(dp)))[0]
            # mas cumulative ?for
            for i in range(len(distances)):
                # if distance is >= to ingredient encapsulatingRadius we keep the point
                m = numpy.greater_equal(distances[i], radius[i])
                mask = numpy.logical_and(mask, m)
            # ponts to keep
            self.sphere_points_mask[points_mask] = numpy.logical_and(
                mask, self.sphere_points_mask[points_mask]
            )
            # indices = numpy.nonzero(mask)[0]#indice f
            # i = self.sphere_points_mask[indices]
            # self.sphere_points_mask = i

    def mask_sphere_points_dihedral(self, v1, v2, marge_out, marge_diedral, v3=[]):
        points_mask = numpy.nonzero(self.sphere_points_mask)[0]
        if len(v3):
            #            a=angle_between_vectors(self.vi.unit_vector(v2),self.sphere_points[points_mask], axis=1)
            d = angle_between_vectors(
                self.vi.unit_vector(v3), self.sphere_points[points_mask], axis=1
            )

            if type(marge_out) is float:
                marge_out = [0.0, marge_out]
            # mask1 = numpy.logical_and(a<math.radians(marge_out[1]), a > math.radians(marge_out[0]))#794
            mask4 = numpy.less(d, math.radians(5))  # 18
            #            mask3 = numpy.logical_and(mask4,mask1)#0?

            self.sphere_points_mask[points_mask] = numpy.logical_and(
                mask4, self.sphere_points_mask[points_mask]
            )
        else:
            a = angle_between_vectors(
                self.vi.unit_vector(v2), self.sphere_points[points_mask], axis=1
            )
            b = angle_between_vectors(
                self.vi.unit_vector(v1), self.sphere_points[points_mask], axis=1
            )
            if type(marge_out) is float:
                marge_out = [0.0, marge_out]
            if type(marge_diedral) is float:
                marge_diedral = [0.0, marge_diedral]
            mask1 = numpy.logical_and(
                a < math.radians(marge_out[1]), a > math.radians(marge_out[0])
            )
            mask2 = numpy.logical_and(
                b < math.radians(marge_diedral[1]), b > math.radians(marge_diedral[0])
            )
            mask3 = numpy.logical_and(mask1, mask2)
            self.sphere_points_mask[points_mask] = numpy.logical_and(
                mask3, self.sphere_points_mask[points_mask]
            )

    def mask_sphere_points_angle(self, v, marge_in):
        # mask first with angle
        # adjust the points to current transfomation? or normalize current vector ?
        points_mask = numpy.nonzero(self.sphere_points_mask)[0]
        a = angle_between_vectors(
            self.vi.unit_vector(v), self.sphere_points[points_mask], axis=1
        )
        if type(marge_in) is float:
            mask = numpy.less(a, math.radians(marge_in))
        else:
            mask = numpy.logical_and(
                a < math.radians(marge_in[1]), a > math.radians(marge_in[0])
            )

        self.sphere_points_mask[points_mask] = numpy.logical_and(
            mask, self.sphere_points_mask[points_mask]
        )

    def mask_sphere_points_vector(self, v, pt, alternate):
        points_mask = numpy.nonzero(self.sphere_points_mask)[0]
        # pick the point that are close to pt2-pt3
        # align v to pt1-pt2, apply to pt2-pt3
        # mesure angle
        pta = self.partners[alternate].getProperties("pt1")
        ptb = self.partners[alternate].getProperties("pt2")
        ptc = self.partners[alternate].getProperties("pt3")
        toalign = numpy.array(ptb) - numpy.array(pta)
        m = numpy.array(rotVectToVect(toalign, v)).transpose()
        m[3, :3] = numpy.array(pt)  # jtrans
        pts = autopack.helper.ApplyMatrix([pta], m.transpose())  # transpose ?
        v = numpy.array(pt) - pts[0]
        m[3, :3] = numpy.array(pt) + v
        newPts = autopack.helper.ApplyMatrix([ptb, ptc], m.transpose())  # transpose ?
        a = angle_between_vectors(
            self.vi.unit_vector(newPts[1] - newPts[0]),
            self.sphere_points[points_mask],
            axis=1,
        )
        mask = numpy.less(a, math.radians(5.0))
        self.sphere_points_mask[points_mask] = numpy.logical_and(
            mask, self.sphere_points_mask[points_mask]
        )

    def mask_sphere_points(
        self,
        v,
        pt,
        marge,
        listeclosest,
        cutoff,
        alternate=None,
        pv=None,
        marge_diedral=None,
        v3=[],
    ):
        # self.sphere_points_mask=numpy.ones(10000,'i')
        if marge_diedral is not None:
            self.mask_sphere_points_dihedral(pv, v, marge, marge_diedral, v3)
        else:
            if alternate is not None:
                self.mask_sphere_points_vector(v, pt, alternate)
            else:
                self.mask_sphere_points_angle(v, marge)
                # storethe mask point
        sphere_points_mask_copy = numpy.copy(self.sphere_points_mask)
        self.mask_sphere_points_ingredients(pt, listeclosest)
        if not len(numpy.nonzero(self.sphere_points_mask)[0]):
            self.sphere_points_mask = numpy.copy(sphere_points_mask_copy)
            # self.mask_sphere_points_boundary(pt)
            #        print ("after mask2 ",len( numpy.nonzero(self.sphere_points_mask)[0]))

    def reset(self):
        self.nbCurve = 0
        self.results = []
        self.listePtLinear = []
        self.listePtCurve = []  # snake
        self.Ptis = []  # snakePts
        self.currentLength = 0.0  # snakelength
        # update he cylinder ?

    def getNextPtIndCyl(self, jtrans, rotMatj, freePoints, histoVol):
        #        print jtrans, rotMatj
        cent2T = self.transformPoints(jtrans, rotMatj, self.positions[-1])
        jx, jy, jz = self.jitterMax
        jitter = self.getMaxJitter(histoVol.smallestProteinSize)
        if len(cent2T) == 1:
            cent2T = cent2T[0]
        tx, ty, tz = cent2T
        dx = (
            jx * jitter * gauss(0.0, 0.3)
        )  # This is an incorrect jitter use the uniform random with sphereical rejection
        dy = jy * jitter * gauss(0.0, 0.3)
        dz = jz * jitter * gauss(0.0, 0.3)
        nexPt = (tx + dx, ty + dy, tz + dz)
        # where is this point in the grid
        # ptInd = histoVol.grid.getPointFrom3D(nexPt)
        t, r = self.oneJitter(histoVol.smallestProteinSize, cent2T, rotMatj)
        dist, ptInd = histoVol.grid.getClosestGridPoint(t)
        dv = numpy.array(nexPt) - numpy.array(cent2T)
        d = numpy.sum(dv * dv)
        return ptInd, dv, sqrt(d)

    def getJtransRot_r(self, pt1, pt2, length=None):
        if length is None:
            length = self.uLength
        v = numpy.array(pt2) - numpy.array(pt1)
        pmx = rotVectToVect(numpy.array(self.orientation) * length, v, i=None)
        return (
            numpy.array(pmx),
            numpy.array(pt1) + numpy.array(v) / 2.0,
        )  # .transpose()jtrans

    def getJtransRot(self, pt1, pt2):
        v, d = self.vi.measure_distance(pt1, pt2, vec=True)
        length, mat = autopack.helper.getTubePropertiesMatrix(pt1, pt2)
        return (
            numpy.array(mat),
            numpy.array(pt1) + numpy.array(v) / 2.0,
        )  # .transpose()jtrans

        # Start jtrans section that is new since Sept 8, 2011 version
        n = numpy.array(pt1) - numpy.array(pt2)
        # normalize the vector n
        nn = self.vi.unit_vector(n)  # why normalize ?

        # get axis of rotation between the plane normal and Z
        v1 = nn
        v2 = numpy.array([0.0, 0.0, 1.0])  # self.orientation) #[0.,0.,1.0]
        cr = numpy.cross(v1, v2)
        axis = self.vi.unit_vector(cr)

        # get the angle between the plane normal and Z
        angle = self.vi.angle_between_vectors(v2, v1)
        # get the rotation matrix between plane normal and Z

        mx = self.vi.rotation_matrix(-angle, axis)  # .transpose()-angle ?
        # End jtrans section that is new since Sept 8, 2011 version
        matrix = mx.transpose()  # self.vi.ToMat(mx).transpose()#Why ToMat here ?
        rotMatj = matrix.reshape((4, 4))
        return (
            rotMatj.transpose(),
            numpy.array(pt1) + numpy.array(v) / 2.0,
        )  # .transpose()jtrans

    def walkLatticeSurface(
        self,
        pts,
        distance,
        histoVol,
        size,
        mask,
        marge=999.0,
        checkcollision=True,
        saw=True,
    ):
        cx, cy, cz = posc = pts
        step = histoVol.grid.gridSpacing * size
        bb = ([cx - step, cy - step, cz - step], [cx + step, cy + step, cz + step])
        pointsInCube = histoVol.grid.getPointsInCube(bb, posc, step, addSP=False)
        o = self.env.compartments[abs(self.compNum) - 1]
        sfpts = o.surfacePointsCoords

        found = False
        attempted = 0
        safetycutoff = 200
        if self.runTimeDisplay:
            name = "walking" + self.name
            sp = self.vi.getObject(name)
            if sp is None:
                sp = self.vi.Sphere(name, radius=10.0)[0]

            self.vi.update()
        while not found:
            if attempted > safetycutoff:
                return None, False
            newPtId = int(random() * len(sfpts))
            v = sfpts[newPtId]  # histoVol.grid.masterGridPositions[newPtId]
            if self.runTimeDisplay:
                self.vi.setTranslation(sp, self.vi.FromVec(v))
                self.vi.update()
            if saw:  # check if already taken, but didnt prevent cross
                if pointsInCube[newPtId] in self.Ptis:
                    attempted += 1
                    continue
            cx, cy, cz = posc = pts
            angle = self.vi.angle_between_vectors(numpy.array(posc), numpy.array(v))
            v, d = self.vi.measure_distance(numpy.array(posc), numpy.array(v), vec=True)
            if abs(math.degrees(angle)) <= marge:
                closeS = self.checkPointSurface(v, cutoff=self.cutoff_surface)
                inComp = self.checkPointComp(v)
                if closeS or not inComp:  # or d > self.uLength:
                    attempted += 1
                    continue
                if checkcollision:
                    m = numpy.identity(4)
                    collision = self.checkSphCollisions(
                        [v],
                        [float(self.uLength) * 1.0],
                        [0.0, 0.0, 0.0],
                        m,
                        0,
                        histoVol.grid.masterGridPositions,
                        distance,
                        histoVol,
                    )
                    if not collision:
                        found = True
                        self.Ptis.append(pointsInCube[newPtId])
                        return v, True
                    else:  # increment the range
                        if not self.constraintMarge:
                            if marge >= 180:
                                return None, False
                            marge += 1
                        attempted += 1
                        continue
                found = True
                self.Ptis.append(pointsInCube[newPtId])
                return v, True
            else:
                attempted += 1
                continue

    def walkLattice(
        self, pts, distance, histoVol, size, marge=999.0, checkcollision=True, saw=True
    ):
        # take the next random point in the windows size +1 +2
        # extended = histoVol.getPointsInCube()
        cx, cy, cz = posc = pts  # histoVol.grid.masterGridPositions[ptId]
        step = histoVol.grid.gridSpacing * size
        bb = ([cx - step, cy - step, cz - step], [cx + step, cy + step, cz + step])
        if self.runTimeDisplay > 1:
            box = self.vi.getObject("collBox")
            if box is None:
                box = self.vi.Box("collBox", cornerPoints=bb, visible=1)
            else:
                #                    self.vi.toggleDisplay(box,True)
                self.vi.updateBox(box, cornerPoints=bb)
                self.vi.update()
        pointsInCube = histoVol.grid.getPointsInCube(bb, posc, step, addSP=False)
        pointsInCubeCoords = numpy.take(
            histoVol.grid.masterGridPositions, pointsInCube, 0
        )
        # take a random point from it OR use gradient info OR constrain by angle
        found = False
        attempted = 0
        safetycutoff = 200
        if self.runTimeDisplay:
            name = "walking" + self.name
            sp = self.vi.getObject(name)
            if sp is None:
                sp = self.vi.Sphere(name, radius=10.0)[0]
            namep = "latticePoints"
            pts = self.vi.getObject(namep)
            if pts is None:
                pts = self.vi.Points(namep)
            pts.Set(vertices=pointsInCubeCoords)
            # sp.SetAbsPos(self.vi.FromVec(startingPoint))
            self.vi.update()
        while not found:
            if attempted > safetycutoff:
                return None, False
            newPtId = int(random() * len(pointsInCube))
            v = pointsInCubeCoords[
                newPtId
            ]  # histoVol.grid.masterGridPositions[newPtId]
            if self.runTimeDisplay:
                self.vi.setTranslation(sp, self.vi.FromVec(v))
                self.vi.update()
            if saw:  # check if already taken, but didnt prevent cross
                if pointsInCube[newPtId] in self.Ptis:
                    attempted += 1
                    continue
            angle = self.vi.angle_between_vectors(numpy.array(posc), numpy.array(v))
            v, d = self.vi.measure_distance(numpy.array(posc), numpy.array(v), vec=True)
            if abs(math.degrees(angle)) <= marge:
                closeS = self.checkPointSurface(v, cutoff=self.cutoff_surface)
                inComp = self.checkPointComp(v)
                if closeS or not inComp:  # or d > self.uLength:
                    attempted += 1
                    continue
                if checkcollision:
                    m = numpy.identity(4)
                    collision = self.collision_jitter(
                        [v],
                        [float(self.uLength) * 1.0],
                        [0.0, 0.0, 0.0],
                        m,
                        0,
                        histoVol.grid.masterGridPositions,
                        distance,
                        histoVol,
                    )
                    if not collision:
                        found = True
                        self.Ptis.append(pointsInCube[newPtId])
                        return v, True
                    else:  # increment the range
                        if not self.constraintMarge:
                            if marge >= 180:
                                return None, False
                            marge += 1
                        attempted += 1
                        continue
                found = True
                self.Ptis.append(pointsInCube[newPtId])
                return v, True
            else:
                attempted += 1
                continue

    def walkSphere(
        self, pt1, pt2, distance, histoVol, dpad, marge=90.0, checkcollision=True
    ):
        """use a random point on a sphere of radius uLength, and useCylinder collision on the grid"""
        v, d = self.vi.measure_distance(pt1, pt2, vec=True)
        found = False
        attempted = 0
        pt = [0.0, 0.0, 0.0]
        angle = 0.0
        safetycutoff = 10000
        if self.constraintMarge:
            safetycutoff = 200
        if self.runTimeDisplay:
            name = "walking" + self.name
            sp = self.vi.getObject(name)
            if sp is None:
                sp = self.vi.Sphere(name, radius=2.0)[0]
            # sp.SetAbsPos(self.vi.FromVec(startingPoint))
            self.vi.update()
        while not found:
            # main loop thattryto found the next point (similar to jitter)
            if attempted >= safetycutoff:
                return None, False  # numpy.array(pt2).flatten()+numpy.array(pt),False
            pt = self.vi.randpoint_onsphere(
                self.uLength
            )  # *numpy.array(self.jitterMax)
            # the new position is the previous point (pt2) plus the random point
            newPt = numpy.array(pt2).flatten() + numpy.array(pt)
            if self.runTimeDisplay >= 2:
                self.vi.setTranslation(sp, newPt)
                self.vi.update()
            # compute the angle between the previous direction (pt1->pt2) and the new random one (pt)
            angle = self.vi.angle_between_vectors(numpy.array(v), numpy.array(pt))
            # first test angle less than the constraint angle
            if abs(math.degrees(angle)) <= marge:
                # check if in bounding box
                inside = histoVol.grid.checkPointInside(
                    newPt, dist=self.cutoff_boundary, jitter=self.jitterMax
                )
                closeS = self.checkPointSurface(newPt, cutoff=self.cutoff_surface)
                inComp = self.checkPointComp(newPt)
                if not inside or closeS or not inComp:
                    if not self.constraintMarge:
                        if marge >= 175:
                            return None, False
                        marge += 1
                    else:
                        attempted += 1
                    continue
                # optionally check for collision
                if checkcollision:
                    if self.modelType == "Cylinders":
                        # outise is consider as collision...?
                        #                        rotMatj,jtrans=self.getJtransRot(numpy.array(pt2).flatten(),newPt)
                        m = [
                            [1.0, 0.0, 0.0, 0.0],
                            [0.0, 1.0, 0.0, 0.0],
                            [0.0, 0.0, 1.0, 0.0],
                            [0.0, 0.0, 0.0, 1.0],
                        ]

                        #                        collision = self.checkSphCollisions([newPt,],[float(self.uLength)*1.,],
                        #                                            [0.,0.,0.], m, 0,
                        #                                            histoVol.grid.masterGridPositions,
                        #                                            distance,
                        #                                            histoVol)
                        # use panda ?
                        collision = self.checkCylCollisions(
                            [numpy.array(pt2).flatten()],
                            [newPt],
                            self.radii[-1],
                            [0.0, 0.0, 0.0],
                            m,
                            histoVol.grid.masterGridPositions,
                            distance,
                            histoVol,
                            dpad,
                        )
                        if not collision:
                            found = True
                            return numpy.array(pt2).flatten() + numpy.array(pt), True
                        else:  # increment the range
                            if not self.constraintMarge:
                                if marge >= 180:
                                    return None, False
                                marge += 1
                            else:
                                attempted += 1
                            continue
                else:
                    found = True
                    return numpy.array(pt2).flatten() + numpy.array(pt), True
                    #                attempted += 1
            else:
                attempted += 1
                continue
            attempted += 1
        return numpy.array(pt2).flatten() + numpy.array(pt), True

    def getInterpolatedSphere(self, pt1, pt2):
        v, d = self.vi.measure_distance(pt1, pt2, vec=True)
        #        d=self.uLength
        sps = numpy.arange(0, d, self.minRadius * 2)
        r = []
        p = []
        pt1 = numpy.array(pt1)
        pt2 = numpy.array(pt2)
        vn = numpy.array(v) / numpy.linalg.norm(numpy.array(v))  # normalized
        p.append(pt1)
        r.append(self.minRadius)
        for i, sp in enumerate(sps[1:]):
            r.append(self.minRadius)
            p.append(pt1 + (vn * sp))
        p.append(pt2)
        r.append(self.minRadius)
        return [r, p]

    def addRBsegment(self, pt1, pt2, nodeid=""):
        # build a rigid body of multisphere along pt1topt2
        r, p = self.getInterpolatedSphere(pt1, pt2)
        print("pos len", len(p), " ", len(r))
        inodenp = self.add_rb_multi_sphere()
        print("node build ", inodenp)
        inodenp.setCollideMask(self.env.BitMask32.allOn())
        inodenp.node().setAngularDamping(1.0)
        inodenp.node().setLinearDamping(1.0)
        print("attach node to world")
        # inodenp.setMat(pmat)
        self.env.world.attachRigidBody(inodenp.node())
        print("node attached to world")
        inodenp = inodenp.node()
        print("add msphere ", inodenp)
        self.env.rb_panda.append(inodenp)
        return inodenp

    def walkSpherePanda(
        self, pt1, pt2, distance, histoVol, marge=90.0, checkcollision=True, usePP=False
    ):
        """use a random point on a sphere of radius uLength, and useCylinder collision on the grid"""
        v, d = self.vi.measure_distance(pt1, pt2, vec=True)
        found = False
        attempted = 0
        pt = [0.0, 0.0, 0.0]
        safetycutoff = self.rejectionThreshold
        if self.constraintMarge:
            safetycutoff = self.rejectionThreshold
        if self.runTimeDisplay:
            name = "walking" + self.name
            sp = self.vi.getObject(name)
            if sp is None:
                sp = self.vi.Sphere(name, radius=2.0)[0]
            # sp.SetAbsPos(self.vi.FromVec(startingPoint))
            self.vi.update()
        liste_nodes = []
        cutoff = self.env.largestProteinSize + self.uLength
        closesbody_indice = self.getClosestIngredient(pt2, self.env, cutoff=cutoff)
        liste_nodes = self.get_rbNodes(
            closesbody_indice, pt2, prevpoint=pt1, getInfo=True
        )
        alternate, ia = self.pick_alternate()
        print("pick alternate", alternate, ia, self.prev_alt)
        if self.prev_was_alternate:
            alternate = None
        p_alternate = None  # self.partners[alternate]#self.env.getIngrFromNameInRecipe(alternate,self.recipe )
        # if p_alternate.getProperties("bend"):
        nextPoint = None  # p_alternate.getProperties("pt2")
        marge_in = None  # p_alternate.getProperties("marge_in")
        dihedral = None  # p_alternate.getProperties("diehdral")#for next point
        length = None  # p_alternate.getProperties("length")#for next point
        # prepare halton if needed
        newPt = None
        newPts = []
        if self.prev_alt is not None:  # and self.prev_alt_pt is not None:
            p_alternate = self.partners[self.prev_alt]
            dihedral = p_alternate.getProperties("diehdral")
            nextPoint = p_alternate.getProperties("pt2")
            # v3=numpy.array(p_alternate.getProperties("pt4"))-numpy.array(p_alternate.getProperties("pt3"))
            marge_out = p_alternate.getProperties("marge_out")  # marge out ?
            if dihedral is not None:
                self.mask_sphere_points(
                    v,
                    pt1,
                    marge_out,
                    liste_nodes,
                    0,
                    pv=self.prev_vec,
                    marge_diedral=dihedral,
                    v3=self.prev_v3,
                )
            alternate = None
        if self.prev_alt is not None:
            point_is_not_available = True
        elif alternate and not self.prev_was_alternate:
            # next point shouldnt be an alternate
            p_alternate = self.partners[
                alternate
            ]  # self.env.getIngrFromNameInRecipe(alternate,self.recipe )
            # if p_alternate.getProperties("bend"):
            entrypoint = p_alternate.getProperties("pt1")
            nextPoint = p_alternate.getProperties("pt2")
            marge_in = p_alternate.getProperties("marge_in")
            dihedral = p_alternate.getProperties("diehdral")  # for next point
            length = p_alternate.getProperties("length")  # for next point
            if entrypoint is not None:
                self.mask_sphere_points(
                    v,
                    pt2,
                    marge_in,
                    liste_nodes,
                    0,
                    pv=None,
                    marge_diedral=None,
                    alternate=alternate,
                )
            elif marge_in is not None:
                self.mask_sphere_points(
                    v, pt2, marge_in, liste_nodes, 0, pv=None, marge_diedral=None
                )
            else:
                self.mask_sphere_points(v, pt2, marge + 2.0, liste_nodes, 0)
            self.prev_was_alternate = True
        elif self.useHalton:
            self.mask_sphere_points(v, pt2, marge + 2.0, liste_nodes, 0)
        if histoVol.runTimeDisplay:
            points_mask = numpy.nonzero(self.sphere_points_mask)[0]
            verts = self.sphere_points[points_mask] * self.uLength + pt2
            name = "Hcloud" + self.name
            pc = self.vi.getObject(name)
            if pc is None:
                pc = self.vi.PointCloudObject(name, vertices=verts)[0]
            else:
                self.vi.updateMesh(pc, vertices=verts)
            self.vi.update()

        while not found:
            print("attempt ", attempted, marge)
            # main loop thattryto found the next point (similar to jitter)
            if attempted >= safetycutoff:
                print("break too much attempt ", attempted, safetycutoff)
                return None, False  # numpy.array(pt2).flatten()+numpy.array(pt),False
            # pt = numpy.array(self.vi.randpoint_onsphere(self.uLength,biased=(uniform(0.,1.0)*marge)/360.0))*numpy.array([1,1,0])
            point_is_not_available = True
            newPt = None
            if self.prev_alt is not None:
                if dihedral is not None:
                    newPt = self.pickAlternateHalton(pt1, pt2, None)
                elif nextPoint is not None:
                    newPt = self.prev_alt_pt
                if newPt is None:
                    print(
                        "no sphere points available with prev_alt", dihedral, nextPoint
                    )
                    self.prev_alt = None
                    return None, False
                    attempted += 1  # ?
                    continue
            elif alternate:
                if marge_in is not None:
                    newPt = self.pickAlternateHalton(pt1, pt2, length)
                    if newPt is None:
                        print("no sphere points available with marge_in")
                        return None, False
                    jtrans, rotMatj = self.get_alternate_position(
                        alternate, ia, v, pt2, newPt
                    )
                elif nextPoint is not None:
                    newPts, jtrans, rotMatj = self.place_alternate(
                        alternate, ia, v, pt1, pt2
                    )
                    # found = self.check_alternate_collision(pt2,newPts,jtrans,rotMatj)
                    newPt = newPts[0]
                    # attempted should be to safetycutoff
                    attempted = safetycutoff
                    if newPt is None:
                        print("no  points available place_alternate")
                        return None, False
                else:  # no constraint we just place alternate relatively to the given halton new points
                    newPt = self.pickAlternateHalton(pt1, pt2, length)
                    if newPt is None:
                        print("no sphere points available with marge_in")
                        return None, False
                    jtrans, rotMatj = self.get_alternate_position(
                        alternate, ia, v, pt2, newPt
                    )
            elif self.useHalton:
                newPt = self.pickHalton(pt1, pt2)
                if newPt is None:
                    print("no sphere points available with marge_in")
                    return None, False
            else:
                newPt = self.pickRandomSphere(pt1, pt2, marge, v)
            if histoVol.runTimeDisplay:
                self.vi.setTranslation(sp, newPt)
                self.vi.update()
            print("picked point", newPt)
            if newPt is None:
                print("no  points available")
                return None, False
            r = [False]
            point_is_not_available = self.point_is_not_available(newPt)
            print(
                "point is available",
                point_is_not_available,
                self.constraintMarge,
                marge,
                attempted,
                self.rejectionThreshold,
            )
            if point_is_not_available:
                if not self.constraintMarge:
                    if marge >= 175:
                        attempted += 1
                        continue
                    if attempted % (self.rejectionThreshold / 3) == 0 and not alternate:
                        marge += 1
                        attempted = 0
                        # need to recompute the mask
                        if not alternate and self.useHalton and self.prev_alt is None:
                            self.sphere_points_mask = numpy.ones(
                                self.sphere_points_nb, "i"
                            )
                            self.mask_sphere_points(v, pt2, marge + 2.0, liste_nodes, 0)
                            if histoVol.runTimeDisplay:
                                points_mask = numpy.nonzero(self.sphere_points_mask)[0]
                                verts = (
                                    self.sphere_points[points_mask] * self.uLength + pt2
                                )
                                name = "Hcloud" + self.name
                                pc = self.vi.getObject(name)
                                if pc is None:
                                    pc = self.vi.PointCloudObject(name, vertices=verts)[
                                        0
                                    ]
                                else:
                                    self.vi.updateMesh(pc, vertices=verts)
                                self.vi.update()
                attempted += 1
                print("rejected boundary")
                continue
            if checkcollision:
                collision = False
                cutoff = histoVol.largestProteinSize + self.uLength
                if not alternate:
                    prev = None
                    if len(histoVol.rTrans) > 2:
                        prev = histoVol.rTrans[-1]

                    a = numpy.array(newPt) - numpy.array(pt2).flatten()
                    numpy.array(pt2).flatten() + a
                    # this s where we use panda
                    rotMatj = [
                        [1.0, 0.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0, 0.0],
                        [0.0, 0.0, 1.0, 0.0],
                        [0.0, 0.0, 0.0, 1.0],
                    ]
                    jtrans = [0.0, 0.0, 0.0]
                    # move it or generate it inplace
                    #                    oldpos1=self.positions
                    #                    oldpos2=self.positions2
                    #                    self.positions=[[numpy.array(pt2).flatten()],]
                    #                    self.positions2=[[newPt],]
                    #                    if self.use_rbsphere :
                    #                        rbnode = self.addRBsegment(numpy.array(pt2).flatten(),newPt)
                    #                    else :
                    #                        rbnode = histoVol.callFunction(histoVol.addRB,(self, numpy.array(jtrans), numpy.array(rotMatj),),{"rtype":self.Type},)#cylinder
                    #                    #histoVol.callFunction(histoVol.moveRBnode,(rbnode, jtrans, rotMatj,))
                    # if inside organelle check for collision with it ?
                    #                    self.positions=oldpos1
                    #                    self.positions2=oldpos2
                    rotMatj, jtrans = self.getJtransRot(
                        numpy.array(pt2).flatten(), newPt
                    )
                    rbnode = self.get_rb_model()
                    self.env.callFunction(
                        self.env.moveRBnode,
                        (
                            rbnode,
                            jtrans,
                            rotMatj,
                        ),
                    )
                    if len(self.env.rTrans) == 0:
                        r = [False]
                    else:
                        prev = None
                        if len(self.env.rTrans) > 2:
                            prev = self.env.rTrans[-1]
                        closesbody_indice = self.getClosestIngredient(
                            newPt, histoVol, cutoff=cutoff
                        )  # vself.radii[0][0]*2.0
                        if len(closesbody_indice) == 0:
                            print("No CloseBody")
                            r = [False]  # closesbody_indice[0] == -1
                        else:
                            print("collision get RB ", len(closesbody_indice))
                            liste_nodes = self.get_rbNodes(
                                closesbody_indice, jtrans, prevpoint=prev, getInfo=True
                            )
                            if usePP:
                                # use self.grab_cb and self.pp_server
                                # Divide the task or just submit job
                                n = 0
                                self.env.grab_cb.reset()
                                for i in range(len(liste_nodes) / autopack.ncpus):
                                    for c in range(autopack.ncpus):
                                        self.env.pp_server.submit(
                                            self.env.world.contactTestPair,
                                            (rbnode, liste_nodes[n][0]),
                                            callback=self.env.grab_cb.grab,
                                        )
                                        n += 1
                                    self.env.pp_server.wait()
                                    r.extend(self.env.grab_cb.collision[:])
                                    if True in r:
                                        break
                            else:
                                for node in liste_nodes:
                                    self.env.moveRBnode(node[0], node[1], node[2])
                                    col = (
                                        self.env.world.contactTestPair(
                                            rbnode, node[0]
                                        ).getNumContacts()
                                        > 0
                                    )
                                    print("collision? ", col)
                                    r = [col]
                                    if col:
                                        break
                    collision = True in r
                    if not collision:
                        self.alternate_interval += 1
                        if self.alternate_interval >= self.mini_interval:
                            self.prev_was_alternate = False
                        self.prev_alt = None
                        self.prev_vec = None
                        self.update_data_tree(
                            numpy.array(pt2).flatten(), rotMatj, pt1=pt2, pt2=newPt
                        )  # jtrans
                        #                        histoVol.callFunction(histoVol.delRB,(rbnode,))
                        return newPt, True

                else:
                    print("alternate collision")
                    rotMatj1, jtrans1 = self.getJtransRot_r(
                        numpy.array(pt2).flatten(), newPt
                    )
                    # collision,liste_nodes = self.collision_rapid(jtrans1,rotMatj1,cutoff=cutoff,usePP=usePP,point=newPt)
                    # the collision shouldnt look for previous cylinder
                    collision_alternate, liste_nodes = self.partners[
                        alternate
                    ].ingr.pandaBullet_collision(jtrans, rotMatj, None, getnodes=True)
                    collision = (
                        collision_alternate  # (collision or collision_alternate)
                    )
                    if not collision:
                        # what about point in curve and result
                        # self.update_data_tree(jtrans1,rotMatj1,pt1=pt2,pt2=newPt)
                        # self.update_data_tree(jtrans1,rotMatj1,pt1=newPt,pt2=newPts[1])
                        self.partners[alternate].ingr.update_data_tree(jtrans, rotMatj)
                        self.compartment.molecules.append(
                            [jtrans, rotMatj, self.partners[alternate].ingr, 0]
                        )  # transpose ?
                        newv, d1 = self.vi.measure_distance(pt2, newPt, vec=True)
                        # v,d2 = self.vi.measure_distance(newPt,newPts[1],vec=True)
                        # self.currentLength += d1
                        if dihedral is not None:
                            self.prev_alt = alternate
                            self.prev_v3 = self.getV3(
                                numpy.array(pt2).flatten(), newPt, alternate
                            )
                        self.prev_vec = v
                        if nextPoint is not None and dihedral is None:
                            self.prev_alt_pt = newPts[1]
                        # treat special case of starting other ingr
                        start_ingr_name = self.partners[alternate].getProperties(
                            "st_ingr"
                        )
                        if start_ingr_name is not None:
                            # add new starting positions
                            start_ingr = self.env.getIngrFromName(start_ingr_name)
                            matrice = numpy.array(rotMatj)  # .transpose()
                            matrice[3, :3] = jtrans
                            newPts = self.get_alternate_starting_point(
                                numpy.array(pt2).flatten(), newPt, alternate
                            )
                            start_ingr.start_positions.append([newPts[0], newPts[1]])
                            start_ingr.nbMol += 1
                            # add a mol
                        # we need to store
                        self.alternate_interval = 0
                        return newPt, True
                    else:
                        self.prev_alt_pt = None  # print (" collide ?",collision)
                if collision:  # increment the range
                    if alternate:
                        attempted = safetycutoff
                    elif not self.constraintMarge:
                        if marge >= 180:  # pi
                            attempted += 1
                            continue
                        if (
                            attempted % (self.rejectionThreshold / 3) == 0
                            and not alternate
                        ):
                            marge += 1
                            attempted = 0
                            # need to recompute the mask
                            if (
                                not alternate
                                and self.useHalton
                                and self.prev_alt is None
                            ):
                                self.sphere_points_mask = numpy.ones(
                                    self.sphere_points_nb, "i"
                                )
                                self.mask_sphere_points(
                                    v, pt2, marge + 2.0, liste_nodes, 0
                                )
                                if self.runTimeDisplay:
                                    points_mask = numpy.nonzero(
                                        self.sphere_points_mask
                                    )[0]
                                    v = (
                                        self.sphere_points[points_mask] * self.uLength
                                        + pt2
                                    )
                                    name = "Hcloud" + self.name
                                    sp = self.vi.getObject(name)
                                    if sp is None:
                                        pc = self.vi.PointCloudObject(
                                            "bbpoint", vertices=v
                                        )[0]
                                    else:
                                        self.vi.updateMesh(pc, vertices=v)
                                    self.vi.update()
                        else:
                            attempted += 1
                    else:
                        attempted += 1
                    print("rejected collision")
                    continue
            else:
                found = True
                #                histoVol.callFunction(histoVol.delRB,(rbnode,))
                return numpy.array(pt2).flatten() + numpy.array(pt), True
            print("end loop add attempt ", attempted)
            attempted += 1
        # histoVol.callFunction(histoVol.delRB,(rbnode,))
        return numpy.array(pt2).flatten() + numpy.array(pt), True

    def walkSpherePandaOLD(
        self, pt1, pt2, distance, histoVol, marge=90.0, checkcollision=True, usePP=False
    ):
        """use a random point on a sphere of radius uLength, and useCylinder collision on the grid"""
        v, d = self.vi.measure_distance(pt1, pt2, vec=True)
        found = False
        attempted = 0
        pt = [0.0, 0.0, 0.0]
        angle = 0.0
        safetycutoff = 1000
        if self.constraintMarge:
            safetycutoff = 200
        if self.runTimeDisplay:
            name = "walking" + self.name
            sp = self.vi.getObject(name)
            if sp is None:
                sp = self.vi.Sphere(name, radius=2.0)[0]
            # sp.SetAbsPos(self.vi.FromVec(startingPoint))
            self.vi.update()
        liste_nodes = []
        while not found:
            print("attempt ", attempted, marge)
            # main loop thattryto found the next point (similar to jitter)
            if attempted >= safetycutoff:
                print("break too much attempt ", attempted, safetycutoff)
                return None, False  # numpy.array(pt2).flatten()+numpy.array(pt),False
            # pt = numpy.array(self.vi.randpoint_onsphere(self.uLength,biased=(uniform(0.,1.0)*marge)/360.0))*numpy.array([1,1,0])
            test = False
            if self.useHalton:
                self.mask_sphere_points(v, pt2, marge + 2.0, liste_nodes, 0)
                p = self.getNextPoint()
                if p is None:
                    print("no sphere points available")
                    return (
                        None,
                        False,
                    )  # numpy.array(pt2).flatten()+numpy.array(pt),False
                p = numpy.array(p) * self.uLength
                pt = numpy.array(p) * numpy.array(self.jitterMax)  # ?
                newPt = numpy.array(pt2).flatten() + numpy.array(pt)
                if self.runTimeDisplay >= 2:
                    self.vi.setTranslation(sp, newPt)
                    self.vi.update()
                test = True
            else:
                p = self.vi.advance_randpoint_onsphere(
                    self.uLength, marge=math.radians(marge), vector=v
                )
                pt = numpy.array(p) * numpy.array(self.jitterMax)  # ?
                # the new position is the previous point (pt2) plus the random point
                newPt = numpy.array(pt2).flatten() + numpy.array(pt)
                if self.runTimeDisplay >= 2:
                    self.vi.setTranslation(sp, newPt)
                    self.vi.update()
                # compute the angle between the previous direction (pt1->pt2) and the new random one (pt)
                angle = self.vi.angle_between_vectors(numpy.array(v), numpy.array(pt))
                test = abs(math.degrees(angle)) <= marge + 2.0
            if test:
                r = [False]
                # check if in bounding box
                inComp = True
                closeS = False
                inside = histoVol.grid.checkPointInside(
                    newPt, dist=self.cutoff_boundary, jitter=self.jitterMax
                )
                if inside:
                    inComp = self.checkPointComp(newPt)
                    if inComp:
                        # check how far from surface ?
                        closeS = self.checkPointSurface(
                            newPt, cutoff=self.cutoff_surface
                        )
                if not inside or closeS or not inComp:
                    print(
                        "inside,closeS ", not inside, closeS, not inComp, newPt, marge
                    )
                    if not self.constraintMarge:
                        if marge >= 175:
                            print("no second point not constraintMarge 1 ", marge)
                            return None, False
                        marge += 1
                    else:
                        print("inside,closeS ", inside, closeS, inComp, newPt, marge)
                        attempted += 1
                    continue
                # optionally check for collision
                if checkcollision:
                    # this s where we use panda
                    rotMatj = [
                        [1.0, 0.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0, 0.0],
                        [0.0, 0.0, 1.0, 0.0],
                        [0.0, 0.0, 0.0, 1.0],
                    ]
                    jtrans = [0.0, 0.0, 0.0]
                    # move it or generate it inplace
                    oldpos1 = self.positions
                    oldpos2 = self.positions2
                    self.positions = [
                        [numpy.array(pt2).flatten()],
                    ]
                    self.positions2 = [
                        [newPt],
                    ]
                    if self.use_rbsphere:
                        print("new RB ")
                        rbnode = self.addRBsegment(numpy.array(pt2).flatten(), newPt)
                    else:
                        rbnode = histoVol.callFunction(
                            histoVol.addRB,
                            (
                                self,
                                numpy.array(jtrans),
                                numpy.array(rotMatj),
                            ),
                            {"rtype": self.Type},
                        )  # cylinder
                    # histoVol.callFunction(histoVol.moveRBnode,(rbnode, jtrans, rotMatj,))
                    # if inside organelle check for collision with it ?
                    self.positions = oldpos1
                    self.positions2 = oldpos2
                    # check collision using bullet
                    # get closest object?
                    cutoff = histoVol.largestProteinSize + self.uLength
                    if len(self.env.rTrans) == 0:
                        r = [False]
                    else:
                        prev = None
                        if len(self.env.rTrans) > 2:
                            prev = self.env.rTrans[-1]
                        closesbody_indice = self.getClosestIngredient(
                            newPt, histoVol, cutoff=cutoff
                        )  # vself.radii[0][0]*2.0
                        if len(closesbody_indice) == 0:
                            r = [False]  # closesbody_indice[0] == -1
                        else:
                            liste_nodes = self.get_rbNodes(
                                closesbody_indice, jtrans, prevpoint=prev, getInfo=True
                            )
                            if usePP:
                                # use self.grab_cb and self.pp_server
                                # Divide the task or just submit job
                                n = 0
                                self.env.grab_cb.reset()
                                for i in range(len(liste_nodes) / autopack.ncpus):
                                    for c in range(autopack.ncpus):
                                        self.env.pp_server.submit(
                                            self.env.world.contactTestPair,
                                            (rbnode, liste_nodes[n][0]),
                                            callback=self.env.grab_cb.grab,
                                        )
                                        n += 1
                                    self.env.pp_server.wait()
                                    r.extend(self.env.grab_cb.collision[:])
                                    if True in r:
                                        break
                            else:
                                for node in liste_nodes:
                                    col = (
                                        self.env.world.contactTestPair(
                                            rbnode, node[0]
                                        ).getNumContacts()
                                        > 0
                                    )
                                    r = [col]
                                    if col:
                                        break
                    collision = True in r
                    if not collision:
                        histoVol.static.append(rbnode)
                        histoVol.moving = None
                        found = True
                        histoVol.nb_ingredient += 1
                        histoVol.rTrans.append(numpy.array(pt2).flatten())
                        histoVol.rRot.append(numpy.array(rotMatj))  # rotMatj r
                        histoVol.rIngr.append(self)
                        histoVol.result.append(
                            [[numpy.array(pt2).flatten(), newPt], rotMatj, self, 0]
                        )
                        histoVol.callFunction(histoVol.delRB, (rbnode,))
                        # histoVol.close_ingr_bhtree.InsertRBHPoint((jtrans[0],jtrans[1],jtrans[2]),radius,None,histoVol.nb_ingredient)
                        if histoVol.treemode == "bhtree":  # "cKDTree"
                            # if len(histoVol.rTrans) > 1 : bhtreelib.freeBHtree(histoVol.close_ingr_bhtree)
                            histoVol.close_ingr_bhtree = bhtreelib.BHtree(
                                histoVol.rTrans, None, 10
                            )
                        else:
                            # rebuild kdtree
                            if len(self.env.rTrans) > 1:
                                histoVol.close_ingr_bhtree = spatial.cKDTree(
                                    histoVol.rTrans, leafsize=10
                                )
                        return numpy.array(pt2).flatten() + numpy.array(pt), True
                    else:  # increment the range
                        if not self.constraintMarge:
                            if marge >= 180:  # pi
                                return None, False
                            marge += 1
                        else:
                            attempted += 1
                        continue
                else:
                    found = True
                    histoVol.callFunction(histoVol.delRB, (rbnode,))
                    return numpy.array(pt2).flatten() + numpy.array(pt), True
            else:
                print("not in the marge ", abs(math.degrees(angle)), marge)
                attempted += 1
                continue
            attempted += 1
        histoVol.callFunction(histoVol.delRB, (rbnode,))
        return numpy.array(pt2).flatten() + numpy.array(pt), True

    def walkSphereRAPIDold(
        self, pt1, pt2, distance, histoVol, marge=90.0, checkcollision=True, usePP=False
    ):
        """use a random point on a sphere of radius uLength, and useCylinder collision on the grid"""
        v, d = self.vi.measure_distance(pt1, pt2, vec=True)
        found = False
        attempted = 0
        pt = [0.0, 0.0, 0.0]
        angle = 0.0
        safetycutoff = 50
        if self.constraintMarge:
            safetycutoff = 50
        if self.runTimeDisplay:
            name = "walking" + self.name
            sp = self.vi.getObject(name)
            if sp is None:
                sp = self.vi.Sphere(name, radius=2.0)[0]
            self.vi.update()
        # do we use the cylindr or the alternate / partner
        liste_nodes = []
        cutoff = self.env.largestProteinSize + self.uLength
        closesbody_indice = self.getClosestIngredient(pt2, self.env, cutoff=cutoff)
        liste_nodes = self.get_rapid_nodes(closesbody_indice, pt2, prevpoint=pt1)
        # mask using boundary and ingredient
        # self.mask_sphere_points_boundary(pt2)
        # self.mask_sphere_points_ingredients(pt2,liste_nodes)
        # mask_sphere_points_start = self.sphere_points_mask[:]
        while not found:
            self.sphere_points_mask = numpy.ones(
                10000, "i"
            )  # mask_sphere_points_start[:]
            dihedral = None
            nextPoint = None
            # liste_nodes=[]
            print("attempt ", attempted, marge)
            # main loop thattryto found the next point (similar to jitter)
            if attempted >= safetycutoff:
                print("break too much attempt ", attempted, safetycutoff)
                return None, False  # numpy.array(pt2).flatten()+numpy.array(pt),False
            # pt = numpy.array(self.vi.randpoint_onsphere(self.uLength,biased=(uniform(0.,1.0)*marge)/360.0))*numpy.array([1,1,0])
            test = False
            newPt = None
            alternate, ia = self.pick_alternate()
            print("pick alternate", alternate, ia, self.prev_alt)
            # thats the ame of the ingedient used as alternate
            if self.prev_alt is not None:  # and self.prev_alt_pt is not None:
                newPt = self.prev_alt_pt
                test = True
                if self.prev_alt_pt is not None:
                    self.prev_alt_pt = None
                alternate = None
            t1 = time()
            if newPt is not None:
                test = True
            # elif autopack.helper.measure_distance(pt1,pt2) == 0.0:
            #                return None,False
            elif alternate:
                p_alternate = self.partners[
                    alternate
                ]  # self.env.getIngrFromNameInRecipe(alternate,self.recipe )
                # if p_alternate.getProperties("bend"):
                nextPoint = p_alternate.getProperties("pt2")
                marge_in = p_alternate.getProperties("marge_in")
                dihedral = p_alternate.getProperties("diehdral")  # for next point
                length = p_alternate.getProperties("length")  # for next point
                if marge_in is not None:
                    self.mask_sphere_points(
                        v, pt2, marge_in, liste_nodes, 0, pv=None, marge_diedral=None
                    )
                    p = self.getNextPoint()
                    if p is None:
                        print("no sphere points available with marge_in")
                        # try again ?
                        attempted += 1
                        continue
                        # return None,False
                    if length is not None:
                        p = (p / self.uLength) * length
                    newPt = numpy.array(pt2).flatten() + numpy.array(p)
                    jtrans, rotMatj = self.get_alternate_position(
                        alternate, ia, v, pt2, newPt
                    )
                else:
                    newPts, jtrans, rotMatj = self.place_alternate(
                        alternate, ia, v, pt1, pt2
                    )
                    # found = self.check_alternate_collision(pt2,newPts,jtrans,rotMatj)
                    newPt = newPts[0]
                test = True
            elif self.useHalton:
                self.mask_sphere_points(v, pt2, marge + 2.0, liste_nodes, 0)
                p = self.getNextPoint()
                if p is None:
                    print("no sphere points available with halton", pt2, v)
                    marge += 1
                    attempted += 1
                    continue
                p = numpy.array(p)  # *self.uLength
                pt = numpy.array(p)  # *numpy.array(self.jitterMax)#?
                newPt = numpy.array(pt2).flatten() + numpy.array(pt)
                test = True
            else:
                p = self.vi.advance_randpoint_onsphere(
                    self.uLength, marge=math.radians(marge), vector=v
                )
                pt = numpy.array(p) * numpy.array(self.jitterMax)
                # the new position is the previous point (pt2) plus the random point
                newPt = numpy.array(pt2).flatten() + numpy.array(pt)
                # compute the angle between the previous direction (pt1->pt2) and the new random one (pt)
                angle = self.vi.angle_between_vectors(numpy.array(v), numpy.array(pt))
                test = abs(math.degrees(angle)) <= marge + 2.0
            if self.runTimeDisplay >= 2:
                self.vi.setTranslation(sp, newPt)
                self.vi.update()
            print("time to pick point ", time() - t1)
            if test:
                test = self.point_is_not_available(newPt)
                if test:
                    if not self.constraintMarge:
                        if marge >= 175:
                            print("no second point not constraintMarge 1 ", marge)
                            return None, False
                        marge += 1
                    else:
                        attempted += 1
                    print("rejected boundary")
                    continue
                # optionally check for collision
                if checkcollision:
                    collision = False
                    cutoff = histoVol.largestProteinSize + self.uLength
                    if not alternate:
                        prev = None
                        if len(histoVol.rTrans) > 2:
                            prev = histoVol.rTrans[-1]
                        # this s where we use panda
                        rotMatj = [
                            [1.0, 0.0, 0.0, 0.0],
                            [0.0, 1.0, 0.0, 0.0],
                            [0.0, 0.0, 1.0, 0.0],
                            [0.0, 0.0, 0.0, 1.0],
                        ]
                        jtrans = [0.0, 0.0, 0.0]
                        #                    rbnode = self.get_rapid_model()
                        rotMatj, jtrans = self.getJtransRot(
                            numpy.array(pt2).flatten(), newPt
                        )
                        collision, liste_nodes = self.collision_rapid(
                            jtrans,
                            rotMatj,
                            cutoff=cutoff,
                            usePP=usePP,
                            point=newPt,
                            prevpoint=prev,
                        )
                        if not collision:
                            self.prev_alt = None
                            self.update_data_tree(jtrans, rotMatj, pt1=pt2, pt2=newPt)
                            return newPt, True
                    else:
                        rotMatj1, jtrans1 = self.getJtransRot_r(
                            numpy.array(pt2).flatten(), newPt
                        )
                        collision, liste_nodes = self.collision_rapid(
                            jtrans1, rotMatj1, cutoff=cutoff, usePP=usePP, point=newPt
                        )
                        # the collision shouldnt look for previous cylinder
                        collision_alternate, liste_nodes = self.partners[
                            alternate
                        ].ingr.collision_rapid(
                            jtrans, rotMatj, usePP=usePP, liste_nodes=liste_nodes
                        )
                        collision = (
                            collision_alternate  # (collision or collision_alternate)
                        )
                        #                        print "collision",collision,collision_alternate,len(liste_nodes)
                        if not collision:
                            # what about point in curve and result
                            # self.update_data_tree(jtrans1,rotMatj1,pt1=pt2,pt2=newPt)
                            # self.update_data_tree(jtrans1,rotMatj1,pt1=newPt,pt2=newPts[1])
                            self.partners[alternate].ingr.update_data_tree(
                                jtrans, rotMatj
                            )
                            self.compartment.molecules.append(
                                [
                                    jtrans,
                                    rotMatj.transpose(),
                                    self.partners[alternate].ingr,
                                    0,
                                ]
                            )
                            newv, d1 = self.vi.measure_distance(pt2, newPt, vec=True)
                            # v,d2 = self.vi.measure_distance(newPt,newPts[1],vec=True)
                            # self.currentLength += d1
                            self.prev_alt = alternate
                            if dihedral is not None:
                                self.mask_sphere_points(
                                    newv,
                                    pt2,
                                    marge_in,
                                    liste_nodes,
                                    0,
                                    pv=v,
                                    marge_diedral=dihedral,
                                )
                                p = self.getNextPoint()
                                self.prev_alt_pt = numpy.array(
                                    newPt
                                ).flatten() + numpy.array(pt)
                            elif nextPoint is not None:
                                self.prev_alt_pt = newPts[1]
                            # treat special case of starting other ingr
                            start_ingr_name = self.partners[alternate].getProperties(
                                "st_ingr"
                            )
                            if start_ingr_name is not None:
                                # add new starting positions
                                start_ingr = self.env.getIngrFromName(start_ingr_name)
                                matrice = numpy.array(rotMatj)  # .transpose()
                                matrice[3, :3] = jtrans
                                newPts = self.get_alternate_starting_point(
                                    matrice, alternate
                                )
                                start_ingr.start_positions.append(
                                    [newPts[0], newPts[1]]
                                )
                            return newPt, True
                        else:
                            self.prev_alt_pt = None
                    if collision:  # increment the range
                        if not self.constraintMarge:
                            if marge >= 180:  # pi
                                print("no second point not constraintMarge 2 ", marge)
                                return None, False
                            # print ("upate marge because collision ", marge)
                            marge += 1
                        else:
                            #                            print ("collision")
                            attempted += 1
                        print("rejected collision")
                        continue
                else:
                    found = True
                    #                    print ("found !")
                    return numpy.array(pt2).flatten() + numpy.array(pt), True
                    #                attempted += 1
            else:
                print("not in the marge ", abs(math.degrees(angle)), marge)
                attempted += 1
                continue
            print("end loop add attempt ", attempted)
            attempted += 1
        return numpy.array(pt2).flatten() + numpy.array(pt), True

    def pickHalton(self, pt1, pt2):
        p = self.getNextPoint()
        if p is None:
            return None
        p = numpy.array(p)  # *self.uLength
        pt = numpy.array(p)  # *numpy.array(self.jitterMax)#?
        return numpy.array(pt2).flatten() + numpy.array(pt)

    def pickRandomSphere(self, pt1, pt2, marge, v):
        p = self.vi.advance_randpoint_onsphere(
            self.uLength, marge=math.radians(marge), vector=v
        )
        pt = numpy.array(p) * numpy.array(self.jitterMax)
        # the new position is the previous point (pt2) plus the random point
        newPt = numpy.array(pt2).flatten() + numpy.array(pt)
        # compute the angle between the previous direction (pt1->pt2) and the new random one (pt)
        #        angle=self.vi.angle_between_vectors(numpy.array(v),numpy.array(pt))
        #        test= abs(math.degrees(angle)) <= marge+2.0
        return newPt

    def pickAlternateHalton(self, pt1, pt2, length):
        p = self.getNextPoint()
        if p is None:
            return None
            # return None,False
        if length is not None:
            p = (p / self.uLength) * length
        newPt = numpy.array(pt2).flatten() + numpy.array(p)
        return newPt

    def walkSphereRAPID(
        self, pt1, pt2, distance, histoVol, marge=90.0, checkcollision=True, usePP=False
    ):
        """use a random point on a sphere of radius uLength, and useCylinder collision on the grid"""
        v, d = self.vi.measure_distance(pt1, pt2, vec=True)
        found = False
        attempted = 0
        pt = [0.0, 0.0, 0.0]
        safetycutoff = self.rejectionThreshold  # angle  / 360
        sp = None
        pc = None
        if self.constraintMarge:
            safetycutoff = self.rejectionThreshold
        if histoVol.runTimeDisplay:
            name = "walking" + self.name
            sp = self.vi.getObject(name)
            if sp is None:
                sp = self.vi.Sphere(name, radius=2.0)[0]
            # sp.SetAbsPos(self.vi.FromVec(startingPoint))
            self.vi.update()
        # do we use the cylinder or the alternate / partner
        liste_nodes = []
        cutoff = self.env.largestProteinSize + self.uLength
        closesbody_indice = self.getClosestIngredient(pt2, self.env, cutoff=cutoff)
        liste_nodes = self.get_rapid_nodes(closesbody_indice, pt2, prevpoint=pt1)
        # mask using boundary and ingredient
        # self.mask_sphere_points_boundary(pt2)
        # self.mask_sphere_points_ingredients(pt2,liste_nodes)
        # mask_sphere_points_start = self.sphere_points_mask[:]
        alternate, ia = self.pick_alternate()
        print("pick alternate", alternate, ia, self.prev_alt)
        if self.prev_was_alternate:
            alternate = None
        p_alternate = None  # self.partners[alternate]#self.env.getIngrFromNameInRecipe(alternate,self.recipe )
        # if p_alternate.getProperties("bend"):
        nextPoint = None  # p_alternate.getProperties("pt2")
        marge_in = None  # p_alternate.getProperties("marge_in")
        dihedral = None  # p_alternate.getProperties("diehdral")#for next point
        length = None  # p_alternate.getProperties("length")#for next point
        # prepare halton if needed
        newPt = None
        newPts = []
        # thats the name of the ingedient used as alternate
        if self.prev_alt is not None:  # and self.prev_alt_pt is not None:
            p_alternate = self.partners[self.prev_alt]
            dihedral = p_alternate.getProperties("diehdral")
            nextPoint = p_alternate.getProperties("pt2")
            marge_in = p_alternate.getProperties("marge_out")  # marge out ?
            if dihedral is not None:
                self.mask_sphere_points(
                    v,
                    pt1,
                    marge_in,
                    liste_nodes,
                    0,
                    pv=self.prev_vec,
                    marge_diedral=dihedral,
                )
            alternate = None
        if self.prev_alt is not None:
            point_is_not_available = True
        elif alternate and not self.prev_was_alternate:
            # next point shouldnt be an alternate
            p_alternate = self.partners[
                alternate
            ]  # self.env.getIngrFromNameInRecipe(alternate,self.recipe )
            # if p_alternate.getProperties("bend"):
            nextPoint = p_alternate.getProperties("pt2")
            marge_in = p_alternate.getProperties("marge_in")
            dihedral = p_alternate.getProperties("diehdral")  # for next point
            length = p_alternate.getProperties("length")  # for next point
            if marge_in is not None:
                self.mask_sphere_points(
                    v, pt2, marge_in, liste_nodes, 0, pv=None, marge_diedral=None
                )
            else:
                self.mask_sphere_points(v, pt2, marge + 2.0, liste_nodes, 0)
            self.prev_was_alternate = True
        elif self.useHalton:
            self.mask_sphere_points(v, pt2, marge + 2.0, liste_nodes, 0)
        if histoVol.runTimeDisplay:
            points_mask = numpy.nonzero(self.sphere_points_mask)[0]
            verts = self.sphere_points[points_mask] * self.uLength + pt2
            name = "Hcloud" + self.name
            pc = self.vi.getObject(name)
            if pc is None:
                pc = self.vi.PointCloudObject(name, vertices=verts)[0]
            else:
                self.vi.updateMesh(pc, vertices=verts)
            self.vi.update()

        while not found:
            # try to drop at newPoint,
            #            self.sphere_points_mask = numpy.ones(10000,'i') #mask_sphere_points_start[:]
            # dihedral= None
            # nextPoint = None
            # liste_nodes=[]
            print("attempt ", attempted, marge)
            # main loop thattryto found the next point (similar to jitter)
            if attempted > safetycutoff:
                print("break too much attempt ", attempted, safetycutoff)
                return None, False  # numpy.array(pt2).flatten()+numpy.array(pt),False
            # pt = numpy.array(self.vi.randpoint_onsphere(self.uLength,biased=(uniform(0.,1.0)*marge)/360.0))*numpy.array([1,1,0])
            point_is_not_available = True
            newPt = None
            if self.prev_alt is not None:
                if dihedral is not None:
                    newPt = self.pickAlternateHalton(pt1, pt2, None)
                elif nextPoint is not None:
                    newPt = self.prev_alt_pt
                if newPt is None:
                    print(
                        "no sphere points available with prev_alt", dihedral, nextPoint
                    )
                    self.prev_alt = None
                    return None, False
                    attempted += 1
                    continue
            elif alternate:
                if marge_in is not None:
                    newPt = self.pickAlternateHalton(pt1, pt2, length)
                    if newPt is None:
                        print("no sphere points available with marge_in")
                        return None, False
                    jtrans, rotMatj = self.get_alternate_position(
                        alternate, ia, v, pt2, newPt
                    )
                elif nextPoint is not None:
                    newPts, jtrans, rotMatj = self.place_alternate(
                        alternate, ia, v, pt1, pt2
                    )
                    # found = self.check_alternate_collision(pt2,newPts,jtrans,rotMatj)
                    newPt = newPts[0]
                    if newPt is None:
                        print("no  points available place_alternate")
                        return None, False
                else:  # no constraint we just place alternate relatively to the given halton new points
                    newPt = self.pickAlternateHalton(pt1, pt2, length)
                    if newPt is None:
                        print("no sphere points available with marge_in")
                        return None, False
                    jtrans, rotMatj = self.get_alternate_position(
                        alternate, ia, v, pt2, newPt
                    )
            elif self.useHalton:
                newPt = self.pickHalton(pt1, pt2)
                if newPt is None:
                    print("no sphere points available with marge_in")
                    return None, False
            else:
                newPt = self.pickRandomSphere(pt1, pt2, marge, v)
            if histoVol.runTimeDisplay:
                self.vi.setTranslation(sp, newPt)
                self.vi.update()
            print("picked point", newPt)
            if newPt is None:
                print("no  points available")
                return None, False
            point_is_not_available = self.point_is_not_available(newPt)
            if point_is_not_available:
                if not self.constraintMarge:
                    if marge >= 175:
                        attempted += 1
                        continue
                        # print ("no second point not constraintMarge 1 ", marge)
                        # self.prev_alt = None
                        # return None,False
                    if attempted % (self.rejectionThreshold / 3) == 0:
                        marge += 1
                        attempted = 0
                        # need to recompute the mask
                        if not alternate and self.useHalton and self.prev_alt is None:
                            self.sphere_points_mask = numpy.ones(
                                self.sphere_points_nb, "i"
                            )
                            self.mask_sphere_points(v, pt2, marge + 2.0, liste_nodes, 0)
                            if histoVol.runTimeDisplay:
                                points_mask = numpy.nonzero(self.sphere_points_mask)[0]
                                verts = (
                                    self.sphere_points[points_mask] * self.uLength + pt2
                                )
                                name = "Hcloud" + self.name
                                pc = self.vi.getObject(name)
                                if pc is None:
                                    pc = self.vi.PointCloudObject(name, vertices=verts)[
                                        0
                                    ]
                                else:
                                    self.vi.updateMesh(pc, vertices=verts)
                                self.vi.update()
                attempted += 1
                print("rejected boundary")
                continue
            # optionally check for collision
            if checkcollision:
                collision = False
                cutoff = histoVol.largestProteinSize + self.uLength
                if not alternate:
                    prev = None
                    if len(histoVol.rTrans) > 2:
                        prev = histoVol.rTrans[-1]
                    a = numpy.array(newPt) - numpy.array(pt2).flatten()
                    numpy.array(pt2).flatten() + a
                    # this s where we use panda
                    rotMatj = [
                        [1.0, 0.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0, 0.0],
                        [0.0, 0.0, 1.0, 0.0],
                        [0.0, 0.0, 0.0, 1.0],
                    ]
                    jtrans = [0.0, 0.0, 0.0]
                    #                    rbnode = self.get_rapid_model()
                    rotMatj, jtrans = self.getJtransRot(
                        numpy.array(pt2).flatten(), newPt
                    )
                    collision, liste_nodes = self.collision_rapid(
                        jtrans,
                        rotMatj,
                        cutoff=cutoff,
                        usePP=usePP,
                        point=newPt,
                        prevpoint=prev,
                    )
                    if not collision:
                        self.alternate_interval += 1
                        if self.alternate_interval >= self.mini_interval:
                            self.prev_was_alternate = False
                        self.prev_alt = None
                        self.prev_vec = None
                        self.update_data_tree(jtrans, rotMatj, pt1=pt2, pt2=newPt)
                        return newPt, True
                else:
                    rotMatj1, jtrans1 = self.getJtransRot_r(
                        numpy.array(pt2).flatten(), newPt
                    )
                    # collision,liste_nodes = self.collision_rapid(jtrans1,rotMatj1,cutoff=cutoff,usePP=usePP,point=newPt)
                    # the collision shouldnt look for previous cylinder
                    collision_alternate, liste_nodes = self.partners[
                        alternate
                    ].ingr.collision_rapid(
                        jtrans, rotMatj, usePP=usePP
                    )  # ,liste_nodes=liste_nodes)
                    collision = (
                        collision_alternate  # (collision or collision_alternate)
                    )
                    if not collision:
                        # what about point in curve and result
                        # self.update_data_tree(jtrans1,rotMatj1,pt1=pt2,pt2=newPt)
                        # self.update_data_tree(jtrans1,rotMatj1,pt1=newPt,pt2=newPts[1])
                        self.partners[alternate].ingr.update_data_tree(jtrans, rotMatj)
                        self.compartment.molecules.append(
                            [
                                jtrans,
                                rotMatj.transpose(),
                                self.partners[alternate].ingr,
                                0,
                            ]
                        )
                        newv, d1 = self.vi.measure_distance(pt2, newPt, vec=True)
                        # v,d2 = self.vi.measure_distance(newPt,newPts[1],vec=True)
                        # self.currentLength += d1
                        if dihedral is not None:
                            self.prev_alt = alternate
                            # self.prev_v3 = self.getV3
                        self.prev_vec = v
                        if nextPoint is not None and dihedral is None:
                            self.prev_alt_pt = newPts[1]
                        # treat special case of starting other ingr
                        start_ingr_name = self.partners[alternate].getProperties(
                            "st_ingr"
                        )
                        if start_ingr_name is not None:
                            # add new starting positions
                            start_ingr = self.env.getIngrFromName(start_ingr_name)
                            matrice = numpy.array(rotMatj)  # .transpose()
                            matrice[3, :3] = jtrans
                            snewPts = self.get_alternate_starting_point(
                                matrice, alternate
                            )
                            start_ingr.start_positions.append([snewPts[0], snewPts[1]])
                            start_ingr.nbMol += 1
                            # add a mol
                        # we need to store
                        self.alternate_interval = 0
                        return newPt, True
                    else:
                        self.prev_alt_pt = None
                if collision:  # increment the range
                    if not self.constraintMarge:
                        if marge >= 180:  # pi
                            attempted += 1
                            continue
                        if attempted % (self.rejectionThreshold / 3) == 0:
                            marge += 1
                            attempted = 0
                            # need to recompute the mask
                            if (
                                not alternate
                                and self.useHalton
                                and self.prev_alt is None
                            ):
                                self.sphere_points_mask = numpy.ones(
                                    self.sphere_points_nb, "i"
                                )
                                self.mask_sphere_points(
                                    v, pt2, marge + 2.0, liste_nodes, 0
                                )
                                if self.runTimeDisplay:
                                    points_mask = numpy.nonzero(
                                        self.sphere_points_mask
                                    )[0]
                                    v = (
                                        self.sphere_points[points_mask] * self.uLength
                                        + pt2
                                    )
                                    name = "Hcloud" + self.name
                                    sp = self.vi.getObject(name)
                                    if sp is None:
                                        pc = self.vi.PointCloudObject(
                                            "bbpoint", vertices=v
                                        )[0]
                                    else:
                                        self.vi.updateMesh(pc, vertices=v)
                                    self.vi.update()
                        else:
                            attempted += 1
                    else:
                        attempted += 1
                    print("rejected collision")
                    continue
            else:
                found = True
                return numpy.array(pt2).flatten() + numpy.array(pt), True
            print("end loop add attempt ", attempted)
            attempted += 1
        return numpy.array(pt2).flatten() + numpy.array(pt), True

    def resetLastPoint(self, listePtCurve):
        self.env.nb_ingredient -= 1
        self.env.rTrans.pop(len(self.env.rTrans) - 1)
        self.env.rRot.pop(len(self.env.rRot) - 1)  # rotMatj
        self.env.rIngr.pop(len(self.env.rIngr) - 1)
        self.env.result.pop(len(self.env.result) - 1)
        if self.env.treemode == "bhtree":  # "cKDTree"
            if len(self.env.rTrans) > 1:
                bhtreelib.freeBHtree(self.env.close_ingr_bhtree)
            if len(self.env.rTrans):
                self.env.close_ingr_bhtree = bhtreelib.BHtree(self.env.rTrans, None, 10)
        else:
            # rebuild kdtree
            if len(self.env.rTrans) > 1:
                self.env.close_ingr_bhtree = spatial.cKDTree(
                    self.env.rTrans, leafsize=10
                )

        # also remove from the result ?
        self.results.pop(len(self.results) - 1)
        self.currentLength -= self.uLength
        # not enought the information is still here
        listePtCurve.pop(len(listePtCurve) - 1)

    def grow(
        self,
        previousPoint,
        startingPoint,
        secondPoint,
        listePtCurve,
        listePtLinear,
        histoVol,
        ptInd,
        freePoints,
        nbFreePoints,
        distance,
        dpad,
        stepByStep=False,
        r=False,
        usePP=False,
    ):
        # r is for reverse growing
        Done = False
        runTimeDisplay = histoVol.runTimeDisplay
        gridPointsCoords = histoVol.grid.masterGridPositions
        if runTimeDisplay:
            parent = histoVol.afviewer.orgaToMasterGeom[self]
        k = 0
        success = False
        safetycutoff = self.safetycutoff
        #        if self.constraintMarge:
        #            safetycutoff = 50
        counter = 0
        mask = None
        if self.walkingMode == "lattice" and self.compNum > 0:
            o = self.env.compartments[abs(self.compNum) - 1]
            v = o.surfacePointsCoords
            mask = numpy.ones(len(v), int)
        alternate = False
        previousPoint_store = None
        while not Done:
            # rest the mask
            self.sphere_points_mask = numpy.ones(10000, "i")
            alternate = False
            print("attempt K ", k)
            if k > safetycutoff:
                print("break safetycutoff", k)
                return success, nbFreePoints, freePoints
            previousPoint_store = previousPoint
            previousPoint = startingPoint
            startingPoint = secondPoint
            if runTimeDisplay:  # or histoVol.afviewer.doSpheres:
                name = str(len(listePtLinear)) + "sp" + self.name + str(ptInd)
                if r:
                    name = str(len(listePtLinear) + 1) + "sp" + self.name + str(ptInd)
                sp = self.vi.Sphere(name, radius=self.radii[0][0], parent=parent)[0]
                self.vi.setTranslation(sp, pos=startingPoint)
                #                sp.SetAbsPos(self.vi.FromVec(startingPoint))
                # sp=self.vi.newInstance(name,histoVol.afviewer.pesph,
                #                                       location=startingPoint,parent=parent)
                # self.vi.scaleObj(sp,self.radii[0][0])
                self.vi.update()
            # pick next point and test collision.
            if self.walkingMode == "sphere":
                if self.placeType == "pandaBullet":
                    secondPoint, success = self.walkSpherePanda(
                        previousPoint,
                        startingPoint,
                        distance,
                        histoVol,
                        marge=self.marge,
                        checkcollision=True,
                        usePP=usePP,
                    )
                    if secondPoint is None:
                        return False, nbFreePoints, freePoints
                elif self.placeType == "RAPID":
                    # call function
                    t1 = time()
                    secondPoint, success = self.walkSphereRAPID(
                        previousPoint,
                        startingPoint,
                        distance,
                        histoVol,
                        marge=self.marge,
                        checkcollision=True,
                        usePP=usePP,
                    )
                    print("walk rapid ", time() - t1)
                    if secondPoint is None:
                        return False, nbFreePoints, freePoints
                else:
                    secondPoint, success = self.walkSphere(
                        previousPoint,
                        startingPoint,
                        distance,
                        histoVol,
                        dpad,
                        marge=self.marge,
                        checkcollision=True,
                    )
            if self.walkingMode == "lattice" and self.compNum > 0:
                secondPoint, success, mask = self.walkLatticeSurface(
                    startingPoint,
                    distance,
                    histoVol,
                    2,
                    mask,
                    marge=self.marge,
                    checkcollision=False,
                    saw=True,
                )
            elif self.walkingMode == "lattice":
                secondPoint, success = self.walkLattice(
                    startingPoint,
                    distance,
                    histoVol,
                    2,
                    marge=self.marge,
                    checkcollision=False,
                    saw=True,
                )
            if secondPoint is None or not success:  # no available point? try again ?
                secondPoint = numpy.array(previousPoint)
                startingPoint = previousPoint_store
                k += 1
                continue

            if len(secondPoint) == 2:
                alternate = True
                startingPoint = secondPoint[0]
                secondPoint = secondPoint[1]
            v, d = self.vi.measure_distance(startingPoint, secondPoint, vec=True)

            rotMatj, jtrans = self.getJtransRot(startingPoint, secondPoint)
            if r:
                # reverse mode
                rotMatj, jtrans = self.getJtransRot(secondPoint, startingPoint)
            cent1T = self.transformPoints(jtrans, rotMatj, self.positions[-1])
            cent2T = self.transformPoints(jtrans, rotMatj, self.positions2[-1])
            print(
                "here is output of walk",
                secondPoint,
                startingPoint,
                success,
                alternate,
                len(secondPoint),
            )
            if success:
                print("success grow")
                # do not append if alternate was used
                if self.prev_alt is None:
                    self.results.append([jtrans, rotMatj])
                if r:
                    if alternate:
                        listePtLinear.insert(0, startingPoint)
                    listePtLinear.insert(0, secondPoint)
                else:
                    if alternate:
                        listePtLinear.append(startingPoint)
                    listePtLinear.append(secondPoint)
                self.currentLength += d
                if runTimeDisplay:
                    print("cylinder with", cent1T, cent2T)
                    name = str(len(listePtLinear)) + self.name + str(ptInd) + "cyl"
                    if r:
                        name = (
                            str(len(listePtLinear) + 1) + self.name + str(ptInd) + "cyl"
                        )
                    self.vi.oneCylinder(
                        name,
                        cent1T,
                        cent2T,
                        parent=parent,
                        instance=histoVol.afviewer.becyl,
                        radius=self.radii[0][0],
                    )
                    self.vi.update()
                if r:
                    listePtCurve.insert(0, jtrans)
                else:
                    listePtCurve.append(jtrans)
                # if success:
                #            for jtrans,rotMatj in self.results:
                # every two we update distance from the previous
                if len(self.results) >= 1:
                    # jtrans, rotMatj = self.results[-1]
                    #                    print "trasnfor",jtrans,rotMatj
                    # cent1T=self.transformPoints(jtrans, rotMatj, self.positions[-1])
                    insidePoints = {}
                    newDistPoints = {}
                    #                    rotMatj=[[ 1.,  0.,  0.,  0.],
                    #                       [ 0.,  1.,  0.,  0.],
                    #                       [ 0.,  0.,  1.,  0.],
                    #                       [ 0.,  0.,  0.,  1.]]
                    #                    jtrans = [0.,0.,0.]
                    #                    #move it or generate it inplace
                    #                    oldpos1=self.positions
                    #                    oldpos2=self.positions2
                    #                    if len(cent1T) == 1 :
                    #                        cent1T=cent1T[0]
                    #                    if len(cent2T) == 1 :
                    #                        cent2T=cent2T[0]
                    #                    self.positions=[[cent1T],]
                    #                    self.positions2=[[cent2T],]
                    # rbnode = histoVol.callFunction(histoVol.addRB,(self, numpy.array(jtrans), numpy.array(rotMatj),),{"rtype":self.Type},)#cylinder
                    # histoVol.callFunction(histoVol.moveRBnode,(rbnode, jtrans, rotMatj,))
                    insidePoints, newDistPoints = self.getInsidePoints(
                        histoVol.grid,
                        gridPointsCoords,
                        dpad,
                        distance,
                        centT=cent1T,
                        jtrans=jtrans,
                        rotMatj=rotMatj,
                    )

                    nbFreePoints = BaseGrid.updateDistances(
                        insidePoints,
                        newDistPoints,
                        freePoints,
                        nbFreePoints,
                        distance,
                    )

                if histoVol.afviewer is not None and hasattr(histoVol.afviewer, "vi"):
                    histoVol.afviewer.vi.progressBar(
                        progress=int((self.currentLength / self.length) * 100),
                        label=self.name
                        + str(self.currentLength / self.length)
                        + " "
                        + str(self.nbCurve)
                        + "/"
                        + str(self.nbMol),
                    )
                else:
                    autopack.helper.progressBar(
                        progress=int((self.currentLength / self.length) * 100),
                        label=self.name
                        + str(self.currentLength / self.length)
                        + " "
                        + str(self.nbCurve)
                        + "/"
                        + str(self.nbMol),
                    )

                    # Start Graham on 5/16/12 This progress bar doesn't work properly... compare with my version in HistoVol
                if self.currentLength >= self.length:
                    Done = True
                    self.counter = counter + 1

            else:
                secondPoint = startingPoint
                break
        return success, nbFreePoints, freePoints

    def updateGrid(
        self,
        rg,
        histoVol,
        dpad,
        freePoints,
        nbFreePoints,
        distance,
        gridPointsCoords,
    ):
        insidePoints = {}
        newDistPoints = {}
        for i in range(rg):  # len(self.results)):
            jtrans, rotMatj = self.results[-i]
            cent1T = self.transformPoints(jtrans, rotMatj, self.positions[-1])
            new_inside_pts, new_dist_points = self.getInsidePoints(
                histoVol.grid,
                gridPointsCoords,
                dpad,
                distance,
                centT=cent1T,
                jtrans=jtrans,
                rotMatj=rotMatj,
            )
            insidePoints = self.merge_place_results(new_inside_pts, insidePoints)
            newDistPoints = self.merge_place_results(new_dist_points, newDistPoints)
            # update free points
            nbFreePoints = BaseGrid.updateDistances(
                new_inside_pts, new_dist_points, freePoints, nbFreePoints, distance
            )
        return insidePoints, newDistPoints, nbFreePoints, freePoints

    def getFirstPoint(self, ptInd, seed=0):
        if self.compNum > 0:  # surfacegrowing: first point is aling to the normal:
            v2 = self.env.compartments[abs(self.compNum) - 1].surfacePointsNormals[
                ptInd
            ]
            secondPoint = (
                numpy.array(self.startingpoint) + numpy.array(v2) * self.uLength
            )
        else:
            # randomize the orientation in the hemisphere following the direction.
            v = self.vi.rotate_about_axis(
                numpy.array(self.orientation),
                random() * math.radians(self.marge),  # or marge ?
                axis=list(self.orientation).index(0),
            )
            self.vector = (
                numpy.array(v).flatten() * self.uLength * self.jitterMax
            )  # = (1,0,0)self.vector.flatten()
            secondPoint = self.startingpoint + self.vector
            # seed="F"
            if seed:
                seed = "R"
                secondPoint = self.startingpoint - self.vector
            else:
                seed = "F"
            inside = self.env.grid.checkPointInside(
                secondPoint, dist=self.cutoff_boundary, jitter=self.jitterMax
            )
            closeS = False
            if inside and self.compNum <= 0:
                # only if not surface ingredient
                closeS = self.checkPointSurface(secondPoint, cutoff=self.cutoff_surface)
            if not inside or closeS:
                safety = 30
                k = 0
                while not inside or closeS:
                    if k > safety:
                        # print("cant find first inside point", inside, closeS)
                        return None
                    else:
                        k += 1
                    p = self.vi.advance_randpoint_onsphere(
                        self.uLength, marge=math.radians(self.marge), vector=self.vector
                    )
                    pt = numpy.array(p) * numpy.array(self.jitterMax)
                    secondPoint = self.startingpoint + numpy.array(pt)
                    inside = self.env.grid.checkPointInside(
                        secondPoint, dist=self.cutoff_boundary, jitter=self.jitterMax
                    )
                    if self.compNum <= 0:
                        closeS = self.checkPointSurface(
                            secondPoint, cutoff=self.cutoff_surface
                        )
            if self.runTimeDisplay:
                parent = self.env.afviewer.orgaToMasterGeom[self]
                name = "Startsp" + self.name + seed
                # sp=self.vi.Sphere(name,radius=self.radii[0][0],parent=parent)[0]
                if seed == "F":
                    # sp=self.vi.newInstance(name,self.env.afviewer.pesph,
                    #                   location=self.startingpoint,parent=parent)
                    # self.vi.scaleObj(sp,self.radii[0][0])
                    sp = self.vi.Sphere(name, radius=self.radii[0][0], parent=parent)[0]
                    self.vi.setTranslation(sp, pos=self.startingpoint)
                    #            sp.SetAbsPos(self.vi.FromVec(startingPoint))
                self.vi.oneCylinder(
                    name + "cyl",
                    self.startingpoint,
                    secondPoint,
                    instance=self.env.afviewer.becyl,
                    parent=parent,
                    radius=self.radii[0][0],
                )
                self.vi.update()
        return secondPoint

    def add_rb_multi_sphere(self):
        inodenp = self.env.worldNP.attachNewNode(BulletRigidBodyNode(self.name))
        inodenp.node().setMass(1.0)
        level = self.deepest_level
        centers = self.positions[level]
        radii = self.radii[level]
        for radc, posc in zip(radii, centers):
            shape = BulletSphereShape(radc)
            inodenp.node().addShape(
                shape, TransformState.makePos(Point3(posc[0], posc[1], posc[2]))
            )  #
        return inodenp

    def grow_place(
        self,
        env,
        ptInd,
        freePoints,
        nbFreePoints,
        distance,
        dpad,
        usePP=False,
    ):
        if type(self.compMask) is str:
            self.compMask = eval(self.compMask)
            self.prepare_alternates()
        success = True
        self.vi = autopack.helper
        self.env = env
        gridPointsCoords = env.grid.masterGridPositions
        self.runTimeDisplay = env.runTimeDisplay
        normal = None

        # jitter the first point
        if self.compNum > 0:
            normal = env.compartments[abs(self.compNum) - 1].surfacePointsNormals[ptInd]
        self.startingpoint = previousPoint = startingPoint = self.jitterPosition(
            numpy.array(env.grid.masterGridPositions[ptInd]),
            env.smallestProteinSize,
            normal=normal,
        )
        print(self.positions, self.positions2)
        v, u = self.vi.measure_distance(self.positions, self.positions2, vec=True)
        self.vector = numpy.array(self.orientation) * self.uLength

        # if u != self.uLength:
        #     self.positions2 = [[self.vector]]
        if self.compNum == 0:
            compartment = self.env
        else:
            compartment = self.env.compartments[abs(self.compNum) - 1]
        self.compartment = compartment

        secondPoint = self.getFirstPoint(ptInd)
        # check collision ?
        # if we have starting position available use it
        if self.nbCurve < len(self.start_positions):
            self.startingpoint = previousPoint = startingPoint = self.start_positions[
                self.nbCurve
            ][0]
            secondPoint = self.start_positions[self.nbCurve][1]
        if secondPoint is None:
            return success, nbFreePoints
        rotMatj, jtrans = self.getJtransRot(startingPoint, secondPoint)
        # test for collision
        # return success, nbFreePoints
        self.results.append([jtrans, rotMatj])
        if self.placeType == "pandaBullet":
            self.env.nb_ingredient += 1
            self.env.rTrans.append(numpy.array(startingPoint).flatten())
            self.env.rRot.append(numpy.array(numpy.identity(4)))  # rotMatj
            self.env.rIngr.append(self)
            self.env.result.append(
                [[numpy.array(startingPoint).flatten(), secondPoint], rotMatj, self, 0]
            )
        # if len(self.env.rTrans) > 1 : bhtreelib.freeBHtree(self.env.close_ingr_bhtree)
        #           if len(self.env.rTrans) : self.env.close_ingr_bhtree=bhtreelib.BHtree( self.env.rTrans, None, 10)
        elif self.placeType == "RAPID":
            self.env.nb_ingredient += 1
            self.env.rTrans.append(numpy.array(jtrans).flatten())
            self.env.rRot.append(numpy.array(rotMatj))  # rotMatj
            self.env.rIngr.append(self)
            self.env.result.append(
                [[numpy.array(startingPoint).flatten(), secondPoint], rotMatj, self, 0]
            )

        if self.env.treemode == "bhtree":  # "cKDTree"
            # if len(self.env.rTrans) > 1 : bhtreelib.freeBHtree(self.env.close_ingr_bhtree)
            if len(self.env.rTrans):
                self.env.close_ingr_bhtree = bhtreelib.BHtree(self.env.rTrans, None, 10)
        else:
            # rebuild kdtree
            if len(self.env.rTrans) > 1:
                self.env.close_ingr_bhtree = spatial.cKDTree(
                    self.env.rTrans, leafsize=10
                )

        self.currentLength = 0.0
        #        self.Ptis=[ptInd,histoVol.grid.getPointFrom3D(secondPoint)]
        dist, pid = env.grid.getClosestGridPoint(secondPoint)
        self.Ptis = [ptInd, pid]
        listePtCurve = [jtrans]
        listePtLinear = [startingPoint, secondPoint]
        # grow until reach self.currentLength >= self.length
        # or attempt > safety
        success, nbFreePoints, freePoints = self.grow(
            previousPoint,
            startingPoint,
            secondPoint,
            listePtCurve,
            listePtLinear,
            env,
            ptInd,
            freePoints,
            nbFreePoints,
            distance,
            dpad,
            stepByStep=False,
            usePP=usePP,
        )
        insidePoints, newDistPoints, nbFreePoints, freePoints = self.updateGrid(
            2,
            env,
            dpad,
            freePoints,
            nbFreePoints,
            distance,
            gridPointsCoords,
        )
        if self.seedOnMinus:
            success, nbFreePoints, freePoints = self.grow(
                previousPoint,
                listePtLinear[1],
                listePtLinear[0],
                listePtCurve,
                listePtLinear,
                env,
                ptInd,
                freePoints,
                nbFreePoints,
                distance,
                dpad,
                stepByStep=False,
                r=True,
            )
            insidePoints, newDistPoints, nbFreePoints, freePoints = self.updateGrid(
                2,
                env,
                dpad,
                freePoints,
                nbFreePoints,
                distance,
                gridPointsCoords,
            )
        # store result in molecule
        self.log.info("res %d", len(self.results))
        for i in range(len(self.results)):
            jtrans, rotMatj = self.results[-i]
            dist, ptInd = env.grid.getClosestGridPoint(jtrans)
            compartment.molecules.append([jtrans, rotMatj, self, ptInd])
            # reset the result ?
        self.results = []
        #        print ("After :",listePtLinear)
        self.listePtCurve.append(listePtCurve)
        self.listePtLinear.append(listePtLinear)
        self.nbCurve += 1
        self.completion = float(self.nbCurve) / float(self.nbMol)
        self.log.info("completion %r %r %r", self.completion, self.nbCurve, self.nbMol)
        return success, jtrans, rotMatj, insidePoints, newDistPoints

    def prepare_alternates(
        self,
    ):
        if len(self.partners):
            self.alternates_names = (
                self.partners.keys()
            )  # self.partners_name#[p.name for p in self.partners.values()]
            # self.alternates_weight = [self.partners[name].weight for name in self.partners]
            self.alternates_weight = [
                self.partners[name].ingr.weight for name in self.partners
            ]
            self.alternates_proba = [
                self.partners[name].ingr.proba_binding for name in self.partners
            ]

    def prepare_alternates_proba(
        self,
    ):
        thw = []
        tw = 0.0
        weights = self.alternates_proba  # python3?#dict.copy().keys()
        for i, w in enumerate(weights):
            tw += w
            thw.append(tw)
        self.alternates_proba = thw

    def pick_random_alternate(
        self,
    ):
        if not len(self.alternates_names):
            return None, 0
        r = uniform(0, 1.0)
        ar = uniform(0, 1.0)
        # weights = self.alternates_weight[:]
        proba = self.alternates_proba[:]
        alti = int((r * (len(self.alternates_names))))  # round?
        if ar < proba[alti]:
            return self.alternates_names[alti], alti
        return None, 0

    def pick_alternate(
        self,
    ):
        # whats he current length ie number of point so far
        # whats are he number of alternate and theyre proba
        # pick an alternate according length and proba
        # liste_proba
        # liste_alternate
        # dice = uniform(0.0,1.0)
        # int(uniform(0.0,1.0)*len(self.sphere_points_mask))
        alt_name = None
        # if it is the first two segment dont do it
        if self.currentLength <= self.uLength * 2.0:
            return None, 0
        # return self.pick_random_alternate()
        weights = self.alternates_weight  # python3?#dict.copy().keys()
        rnd = uniform(0, 1.0) * sum(weights)  # * (self.currentLength / self.length)
        i = 0
        for i, w in enumerate(weights):
            rnd -= w
            if rnd < 0:
                r = uniform(0, 1.0)
                #                print (r,self.alternates_proba[i])
                if r < self.alternates_proba[i]:
                    alt_name = self.alternates_names[i]
                break
        # alternates_names point to an ingredients id?
        return alt_name, i

    def get_alternate_position(self, alternate, alti, v, pt1, pt2):
        length = self.partners[alternate].getProperties("length")
        # rotation that align snake orientation to current segment
        rotMatj, jtrans = self.getJtransRot_r(
            numpy.array(pt1).flatten(), numpy.array(pt2).flatten(), length=length
        )
        # jtrans is the position between pt1 and pt2
        prevMat = numpy.array(rotMatj)
        # jtrans=autopack.helper.ApplyMatrix([jtrans],prevMat.transpose())[0]
        prevMat[3, :3] = numpy.array(pt1)  # jtrans
        rotMatj = numpy.identity(4)
        # oldv is v we can ether align to v or newv
        newv = numpy.array(pt2) - numpy.array(pt1)
        # use v ? for additional point ?
        ptb = self.partners[alternate].getProperties("pt2")
        ptc = self.partners[alternate].getProperties("pt3")
        toalign = numpy.array(ptc) - numpy.array(ptb)
        m = numpy.array(rotVectToVect(toalign, newv)).transpose()
        m[3, :3] = numpy.array(pt1)  # jtrans
        pts = autopack.helper.ApplyMatrix([ptb], m.transpose())  # transpose ?
        v = numpy.array(pt1) - pts[0]
        m[3, :3] = numpy.array(pt1) + v  # - (newpt1-pts[0])

        # rotMatj,jt=self.getJtransRot_r(numpy.array(ptb).flatten(),
        #                                   numpy.array(ptc).flatten(),
        #                                   length = length)
        # rotMatj[3,:3] = -numpy.array(ptb)
        # globalM1 = numpy.array(matrix(rotMatj)*matrix(prevMat))
        #
        # offset = numpy.array(ptb)+toalign/2.0
        # npts=numpy.array([pta,ptb,offset,ptc])-numpy.array([ptb])
        # pts=autopack.helper.ApplyMatrix(npts,globalM1.transpose())#transpose ?
        # trans = numpy.array(jtrans)-1.5*pts[1]-pts[2]
        # now apply matrix and get the offset
        # prevMat = numpy.array(globalM1)
        # jtrans=autopack.helper.ApplyMatrix([jtrans],prevMat.transpose())[0]
        # prevMat[3,:3] = jtrans
        # npt2=autopack.helper.ApplyMatrix([ptb],prevMat.transpose())[0]
        # offset = numpy.array(npt2) -numpy.array(pt1)
        # jtrans=numpy.array(jtrans)-offset
        # toalign = numpy.array(ptb) -numpy.array(pta)
        # globalM2 = numpy.array(rotVectToVect(toalign,v))
        # compare to superimposition_matrix
        # print globalM1,quaternion_from_matrix(globalM1).tolist()
        # print globalM2,quaternion_from_matrix(globalM2).tolist()
        # center them
        # c1=autopack.helper.getCenter([ptb,ptc])
        # c2=autopack.helper.getCenter([pt1,pt2])
        # globalM = superimposition_matrix(numpy.array([ptb,ptc])-c1,numpy.array([pt1,pt2])-c2)
        # print globalM,quaternion_from_matrix(globalM).tolist()
        rotMatj = numpy.identity(4)
        rotMatj[:3, :3] = m[:3, :3].transpose()
        jtrans = m[3, :3]
        # print ("will try to place alterate at ",jtrans)
        return jtrans, rotMatj

    def get_alternate_position_p(self, alternate, alti, v, pt1, pt2):
        length = self.partners[alternate].getProperties("length")
        rotMatj, jtrans = self.getJtransRot_r(
            numpy.array(pt1).flatten(), numpy.array(pt2).flatten(), length=length
        )
        prevMat = numpy.array(rotMatj)
        # jtrans=autopack.helper.ApplyMatrix([jtrans],prevMat.transpose())[0]
        prevMat[3, :3] = jtrans
        rotMatj = numpy.identity(4)

        localMR = self.partners_position[alti]
        # instead use rotVectToVect from current -> to local ->
        # align  p2->p3 vector to pt1->pt2
        globalM = numpy.array(matrix(localMR) * matrix(prevMat))
        jtrans = globalM[3, :3]
        rotMatj[:3, :3] = globalM[:3, :3]
        # print ("will try to place alterate at ",jtrans)
        return jtrans, rotMatj

    def getV3(self, pt1, pt2, alternate):
        length = self.partners[alternate].getProperties("length")
        rotMatj, jtrans = self.getJtransRot_r(
            numpy.array(pt1).flatten(), numpy.array(pt2).flatten(), length=length
        )
        # jtrans is the position between pt1 and pt2
        prevMat = numpy.array(rotMatj)
        prevMat[3, :3] = numpy.array(pt1)  # jtrans
        newv = numpy.array(pt2) - numpy.array(pt1)
        ptb = self.partners[alternate].getProperties("pt2")
        ptc = self.partners[alternate].getProperties("pt3")
        ptd = self.partners[alternate].getProperties("pt4")
        toalign = numpy.array(ptc) - numpy.array(ptb)
        m = numpy.array(rotVectToVect(toalign, newv)).transpose()
        m[3, :3] = numpy.array(pt1)  # jtrans
        pts = autopack.helper.ApplyMatrix([ptb], m.transpose())  # transpose ?
        v = numpy.array(pt1) - pts[0]
        m[3, :3] = numpy.array(pt1) + v
        newPts = autopack.helper.ApplyMatrix([ptc, ptd], m.transpose())  # transpose ?
        return numpy.array(newPts[1]) - numpy.array(newPts[0])

    def get_alternate_starting_point(self, pt1, pt2, alternate):
        spt1 = self.partners[alternate].getProperties("st_pt1")
        spt2 = self.partners[alternate].getProperties("st_pt2")

        length = self.partners[alternate].getProperties("length")
        rotMatj, jtrans = self.getJtransRot_r(
            numpy.array(pt1).flatten(), numpy.array(pt2).flatten(), length=length
        )
        # jtrans is the position between pt1 and pt2
        prevMat = numpy.array(rotMatj)
        prevMat[3, :3] = numpy.array(pt1)  # jtrans
        newv = numpy.array(pt2) - numpy.array(pt1)
        ptb = self.partners[alternate].getProperties("pt2")
        ptc = self.partners[alternate].getProperties("pt3")
        toalign = numpy.array(ptc) - numpy.array(ptb)
        m = numpy.array(rotVectToVect(toalign, newv)).transpose()
        m[3, :3] = numpy.array(pt1)  # jtrans
        pts = autopack.helper.ApplyMatrix([ptb], m.transpose())  # transpose ?
        v = numpy.array(pt1) - pts[0]
        m[3, :3] = numpy.array(pt1) + v
        newPts = autopack.helper.ApplyMatrix([spt1, spt2], m.transpose())  # transpose ?
        return newPts

    def place_alternate(self, alternate, alti, v, pt1, pt2):
        pta = self.partners[alternate].getProperties("pt1")
        ptb = self.partners[alternate].getProperties("pt2")
        ptc = self.partners[alternate].getProperties("pt3")
        ptd = self.partners[alternate].getProperties("pt4")
        prevMat = numpy.identity(4)
        if ptb is not None:
            rotMatj, jtrans = self.getJtransRot_r(
                numpy.array(pt1).flatten(), numpy.array(pt2).flatten()
            )
            toalign = numpy.array(ptb) - numpy.array(pta)
            newv = numpy.array(pt2) - numpy.array(pt1)
            prevMat = numpy.array(rotVectToVect(toalign, newv))
            newPts = autopack.helper.ApplyMatrix(
                [ptc, ptd], prevMat.transpose()
            )  # partner positions ?
            prevMat[3, :3] = jtrans
        else:
            newPt = self.pickHalton(pt1, pt2)
            newPts = [newPt]
            rotMatj, jtrans = self.getJtransRot_r(
                numpy.array(pt2).flatten(), numpy.array(newPt).flatten()
            )
            prevMat = numpy.array(rotMatj)
            # jtrans=autopack.helper.ApplyMatrix([jtrans],prevMat.transpose())[0]
            prevMat[3, :3] = jtrans
        rotMatj = numpy.identity(4)
        return newPts, jtrans, rotMatj

    def place_alternate_p(self, alternate, alti, v, pt1, pt2):
        # previou transformation
        #        distance,mat = autopack.helper.getTubePropertiesMatrix(pt1,pt2)
        #        prevMat = numpy.array(mat)
        # rotMatj,jtrans=self.getJtransRot(numpy.array(pt2).flatten(),numpy.array(pt1).flatten())
        # should apply first to get the new list of point, and length
        p_alternate = self.partners[
            alternate
        ]  # self.env.getIngrFromNameInRecipe(alternate,self.recipe )
        # if p_alternate.getProperties("bend"):
        out1 = p_alternate.getProperties("pt1")
        out2 = p_alternate.getProperties("pt2")
        if out1 is not None:
            rotMatj, jtrans = self.getJtransRot_r(
                numpy.array(pt1).flatten(), numpy.array(pt2).flatten()
            )
            prevMat = numpy.array(rotMatj)
            # jtrans=autopack.helper.ApplyMatrix([jtrans],prevMat.transpose())[0]
            prevMat[3, :3] = jtrans
            newPts = autopack.helper.ApplyMatrix(
                [out1, out2], prevMat.transpose()
            )  # partner positions ?
        else:
            newPt = self.pickHalton(pt1, pt2)
            newPts = [newPt]
            rotMatj, jtrans = self.getJtransRot_r(
                numpy.array(pt2).flatten(), numpy.array(newPt).flatten()
            )
            prevMat = numpy.array(rotMatj)
            # jtrans=autopack.helper.ApplyMatrix([jtrans],prevMat.transpose())[0]
            prevMat[3, :3] = jtrans
        rotMatj = numpy.identity(4)
        # print ("som math",out1,out2,newPts)
        # need also to get the alternate_ingredint new position and add it.
        localMR = self.partners_position[alti]
        globalM = numpy.array(matrix(localMR) * matrix(prevMat))
        jtrans = globalM[3, :3]
        rotMatj[:3, :3] = globalM[:3, :3]
        #        print ("will try to place alterate at ",jtrans)
        return newPts, jtrans, rotMatj
        # we need to add this guy a new mol and tak in account his molarity ?
        # should actually the partner system and the step/step


class ActinIngredient(GrowIngredient):
    def __init__(
        self,
        molarity,
        radii=[[50.0]],
        positions=None,
        positions2=None,
        sphereFile=None,
        packingPriority=0,
        name=None,
        pdb=None,
        color=None,
        nbJitter=5,
        jitterMax=(1, 1, 1),
        perturbAxisAmplitude=0.1,
        length=10.0,
        closed=False,
        modelType="Cylinders",
        biased=1.0,
        Type="Actine",
        principalVector=(1, 0, 0),
        meshFile=None,
        packingMode="random",
        placeType="jitter",
        marge=35.0,
        influenceRad=100.0,
        meshObject=None,
        orientation=(1, 0, 0),
        nbMol=0,
        **kw
    ):

        GrowIngredient.__init__(
            self,
            molarity,
            radii,
            positions,
            positions2,
            sphereFile,
            packingPriority,
            name,
            pdb,
            color,
            nbJitter,
            jitterMax,
            perturbAxisAmplitude,
            length,
            closed,
            modelType,
            biased,
            principalVector,
            meshFile,
            packingMode,
            placeType,
            marge,
            meshObject,
            orientation,
            nbMol,
            Type,
            **kw
        )
        if name is None:
            name = "Actine_%s_%f" % (str(radii), molarity)
        self.isAttractor = True
        self.constraintMarge = True
        self.seedOnMinus = True
        self.influenceRad = influenceRad
        self.oneSuperTurn = 825.545  # cm from c4d graham file
        self.oneDimerSize = 100.0  # 200 =2
        self.cutoff_surface = 50.0
        self.cutoff_boundary = 1.0

    def updateFromBB(self, grid):
        return
        r = grid.getRadius()
        self.positions = [0.0, 0.0, 0.0]
        self.positions2 = [r, 0.0, 0.0]
        self.principalVector = [1.0, 0.0, 0.0]
        self.uLength = r
        self.length = 2 * r

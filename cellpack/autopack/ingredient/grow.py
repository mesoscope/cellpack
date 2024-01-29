# -*- coding: utf-8 -*-

import numpy
from scipy import spatial
from numpy import matrix
from math import pi, sqrt
from random import uniform, gauss, random
import math
from cellpack.autopack.ingredient.Ingredient import Ingredient

from cellpack.autopack.transformation import angle_between_vectors
from cellpack.autopack.ldSequence import SphereHalton
from cellpack.autopack.BaseGrid import BaseGrid as BaseGrid
from .utils import rotVectToVect, get_reflected_point

import cellpack.autopack as autopack

from .multi_cylinder import MultiCylindersIngr

helper = autopack.helper


class GrowIngredient(MultiCylindersIngr):
    ARGUMENTS = Ingredient.ARGUMENTS
    ARGUMENTS.extend(
        [
            "length",
            "closed",
            "uLength",
            "biased",
            "marge",
            "orientation",
            "walkignMode",
            "constraintMarge",
            "useHalton",
            "compMask",
            "use_rbsphere",
        ]
    )

    def __init__(
        self,
        available_regions=None,
        type="Grow",
        biased=1.0,
        closed=False,
        color=None,
        compMask=None,
        constraintMarge=False,
        cutoff_boundary=1.0,
        cutoff_surface=0.5,
        gradient=None,
        is_attractor=False,
        max_jitter=(1, 1, 1),
        length=10.0,
        marge=20.0,
        meshFile=None,
        meshObject=None,
        model_type="Cylinders",
        molarity=0.0,
        name=None,
        jitter_attempts=5,
        count=0,
        count_options=None,
        orientation=(1, 0, 0),
        orient_bias_range=[-pi, pi],
        priority=0,
        packing_mode="random",
        partners=None,
        perturb_axis_amplitude=0.1,
        place_method="jitter",
        positions=None,
        positions2=None,
        principal_vector=(1, 0, 0),
        radii=None,
        representations=None,
        rejection_threshold=30,
        rotation_axis=[0.0, 0.0, 0.0],
        rotation_range=6.2831,
        source=None,
        uLength=0,
        use_rbsphere=False,
        useHalton=True,
        useLength=False,
        use_orient_bias=False,
        use_rotation_axis=True,
        walkingMode="sphere",
        weight=0.2,
    ):
        # TODO: need to fix multi_bounds and radii settings
        super().__init__(
            multi_bounds=[[], []],
            radii=radii,
            type=type,
            color=color,
            cutoff_surface=cutoff_surface,
            gradient=gradient,
            is_attractor=is_attractor,
            max_jitter=max_jitter,
            molarity=molarity,
            name=name,
            jitter_attempts=jitter_attempts,
            count=count,
            count_options=count_options,
            orient_bias_range=orient_bias_range,
            priority=priority,
            partners=partners,
            perturb_axis_amplitude=perturb_axis_amplitude,
            place_method=place_method,
            principal_vector=principal_vector,
            representations=representations,
            rejection_threshold=rejection_threshold,
            rotation_axis=rotation_axis,
            rotation_range=rotation_range,
            use_orient_bias=use_orient_bias,
            use_rotation_axis=use_rotation_axis,
            weight=weight,
        )
        if name is None:
            name = "%s_%f" % (str(radii), molarity)
        self.name = name
        self.model_type = model_type
        self.collisionLevel = 0
        self.min_radius = self.radii[0][0]
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
        self.uLength = uLength

        if self.positions2 is None:
            if self.uLength == 0:
                self.uLength = self.radii[0][0]
            self.vector = numpy.array(self.principal_vector) * self.uLength / 2.0
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
        self.encapsulating_radius = self.uLength / 2.0
        self.unitNumberF = 0  # number of unit pose so far forward
        self.unitNumberR = 0  # number of unit pose so far reverse
        self.orientation = orientation
        self.seedOnPlus = True  # The filament should continue to grow on its (+) end
        self.seedOnMinus = False  # The filamen should continue to grow on its (-) end.
        #        if self.compartment_id > 0 :
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
        self.use_rbsphere = use_rbsphere
        self.useHalton = useHalton
        self.constraintMarge = constraintMarge
        self.cutoff_boundary = cutoff_boundary
        self.cutoff_surface = cutoff_surface
        # mesh object representing one uLength? or a certain length
        self.unitParent = None
        self.unitParentLength = 0.0
        self.walkingMode = walkingMode  # ["sphere","lattice"]
        self.walkingType = "stepbystep"  # or atonce
        self.compMask = []
        self.prev_v3 = []
        if compMask is not None:
            if type(compMask) is str:
                self.compMask = eval(compMask)
            else:
                self.compMask = compMask
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

        self.alternates_proba = []

        self.alternates_weight = []

        self.prev_alt = None
        self.prev_was_alternate = False
        self.prev_alt_pt = None
        self.mini_interval = 2
        self.alternate_interval = 0
        # keep record of point Id that are bound to alternate and change the
        # representation according.
        self.safetycutoff = 10

    def get_signed_distance(
        self,
        packing_location,
        grid_point_location,
        rotation_matrix,
    ):
        cent1T = self.transformPoints(
            packing_location, rotation_matrix, self.positions[-1]
        )
        cent2T = self.transformPoints(
            packing_location, rotation_matrix, self.positions2[-1]
        )

        for radc, p1, p2 in zip(self.radii[-1], cent1T, cent2T):
            x1, y1, z1 = p1
            x2, y2, z2 = p2
            vx, vy, vz = vector_along_ingredient = (x2 - x1, y2 - y1, z2 - z1)
            lengthsq = vx * vx + vy * vy + vz * vz
            pd = grid_point_location - p1
            pd2 = grid_point_location - p2

            dot_product = numpy.dot(grid_point_location, vector_along_ingredient)
            d2toP1 = numpy.sum(pd * pd)
            dsq = d2toP1 - dot_product * dot_product / lengthsq

            d2toP2 = numpy.sum(pd2 * pd2)
            if dot_product < 0.0:  # outside 1st cap
                signed_distance = d2toP1

            elif dot_product > lengthsq:
                signed_distance = d2toP2
            else:
                signed_distance = dsq - radc
        return signed_distance

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

            pd = (
                numpy.take(gridPointsCoords, pointsInCube, 0) - p1
            )  # vector joining grid point and 1st corner
            dotp = numpy.dot(pd, vect)
            d2toP1 = numpy.sum(pd * pd, 1)
            dsq = (
                d2toP1 - dotp * dotp / lengthsq
            )  # perpendicular distance between grid point and cylinder axis

            pd2 = numpy.take(gridPointsCoords, pointsInCube, 0) - p2
            d2toP2 = numpy.sum(pd2 * pd2, 1)

            for pti, pt in enumerate(pointsInCube):
                if pt in insidePoints:
                    continue

                if dotp[pti] < 0.0:  # outside 1st cap, p1 is closer
                    d = sqrt(d2toP1[pti]) - radc  # add cylindrical cap at ends?
                    if d < distance[pt]:  # point in region of influence
                        if pt in newDistPoints:
                            if d < newDistPoints[pt]:
                                newDistPoints[pt] = d
                        else:
                            newDistPoints[pt] = d
                elif dotp[pti] > lengthsq:  # p2 is closer
                    d = sqrt(d2toP2[pti]) - radc  # add cylindrical cap at ends?
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
        np = numpy.array(self.sphere_points[sp_pt_indice]) * numpy.array(
            self.max_jitter
        )
        return (
            numpy.array(self.vi.unit_vector(np)) * self.uLength
        )  # biased by max_jitter ?

    def mask_sphere_points_boundary(self, pt, boundingBox=None):
        if boundingBox is None:
            boundingBox = self.env.fillBB
        pts = (numpy.array(self.sphere_points) * self.uLength) + pt
        points_mask = numpy.nonzero(self.sphere_points_mask)[0]
        if len(points_mask):
            mask = [self.point_is_available(pt) for pt in pts[points_mask]]
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
            radius = [float(ingr.encapsulating_radius) for ingr in ingrs]
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
                # if distance is >= to ingredient encapsulating_radius we keep the point
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
        pta = self.partners[alternate].get_point(0)
        ptb = self.partners[alternate].get_point(1)
        ptc = self.partners[alternate].get_point(2)
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

    def getNextPtIndCyl(self, jtrans, rotMatj, free_points, histoVol):
        #        print jtrans, rotMatj
        cent2T = self.transformPoints(jtrans, rotMatj, self.positions[-1])
        jx, jy, jz = self.max_jitter
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
        o = self.env.compartments[abs(self.compartment_id) - 1]
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
                closeS = self.far_enough_from_surfaces(v, cutoff=self.cutoff_surface)
                inComp = self.is_point_in_correct_region(v)
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
                closeS = self.far_enough_from_surfaces(v, cutoff=self.cutoff_surface)
                inComp = self.is_point_in_correct_region(v)
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
            )  # *numpy.array(self.max_jitter)
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
                    newPt, dist=self.cutoff_boundary, jitter=self.max_jitter
                )
                closeS = self.far_enough_from_surfaces(
                    newPt, cutoff=self.cutoff_surface
                )
                inComp = self.is_point_in_correct_region(newPt)
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
                    if self.model_type == "Cylinders":
                        # outise is consider as collision...?
                        #                        rotMatj,jtrans=self.getJtransRot(numpy.array(pt2).flatten(),newPt)
                        rot_mat = numpy.identity(4)
                        #                        collision = self.checkSphCollisions([newPt,],[float(self.uLength)*1.,],
                        #                                            [0.,0.,0.], m, 0,
                        #                                            histoVol.grid.masterGridPositions,
                        #                                            distance,
                        #                                            histoVol)
                        collision, _, _ = self.checkCylCollisions(
                            [numpy.array(pt2).flatten()],
                            [newPt],
                            self.radii[-1],
                            [0.0, 0.0, 0.0],
                            rot_mat,
                            histoVol.grid.masterGridPositions,
                            distance,
                            histoVol,
                            dpad,
                        )
                        if not collision:
                            found = True
                            return newPt, True
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
                    return newPt, True
                    #                attempted += 1
            else:
                attempted += 1
                continue
            attempted += 1
        return newPt, True

    def getInterpolatedSphere(self, pt1, pt2):
        v, d = self.vi.measure_distance(pt1, pt2, vec=True)
        #        d=self.uLength
        sps = numpy.arange(0, d, self.min_radius * 2)
        r = []
        p = []
        pt1 = numpy.array(pt1)
        pt2 = numpy.array(pt2)
        vn = numpy.array(v) / numpy.linalg.norm(numpy.array(v))  # normalized
        p.append(pt1)
        r.append(self.min_radius)
        for i, sp in enumerate(sps[1:]):
            r.append(self.min_radius)
            p.append(pt1 + (vn * sp))
        p.append(pt2)
        r.append(self.min_radius)
        return [r, p]

    def pickHalton(self, pt1, pt2):
        p = self.getNextPoint()
        if p is None:
            return None
        p = numpy.array(p)  # *self.uLength
        pt = numpy.array(p)  # *numpy.array(self.max_jitter)#?
        return numpy.array(pt2).flatten() + numpy.array(pt)

    def pickRandomSphere(self, pt1, pt2, marge, v):
        p = self.vi.advance_randpoint_onsphere(
            self.uLength, marge=math.radians(marge), vector=v
        )
        pt = numpy.array(p) * numpy.array(self.max_jitter)
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

    def resetLastPoint(self, listePtCurve):
        self.env.nb_ingredient -= 1
        self.env.rTrans.pop(len(self.env.rTrans) - 1)
        self.env.rRot.pop(len(self.env.rRot) - 1)  # rotMatj
        self.env.rIngr.pop(len(self.env.rIngr) - 1)
        self.env.result.pop(len(self.env.result) - 1)
        # rebuild kdtree
        if len(self.env.rTrans) > 1:
            self.env.close_ingr_bhtree = spatial.cKDTree(
                self.env.packed_objects.get_positions(), leafsize=10
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
        free_points,
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

        counter = 0
        mask = None
        if self.walkingMode == "lattice" and self.compartment_id > 0:
            o = self.env.compartments[abs(self.compartment_id) - 1]
            v = o.surfacePointsCoords
            mask = numpy.ones(len(v), int)
        alternate = False
        if secondPoint is not None:
            previousPoint = startingPoint
            startingPoint = secondPoint

        while not Done:
            # rest the mask
            self.sphere_points_mask = numpy.ones(10000, "i")
            alternate = False
            print("attempt K ", k)
            if k > safetycutoff:
                print("break safetycutoff", k)
                return success, nbFreePoints, free_points
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
                secondPoint, success = self.walkSphere(
                    previousPoint,
                    startingPoint,
                    distance,
                    histoVol,
                    dpad,
                    marge=self.marge,
                    checkcollision=True,
                )
            if self.walkingMode == "lattice" and self.compartment_id > 0:
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
                # secondPoint = numpy.array(previousPoint)
                # startingPoint = previousPoint_store
                k += 1
                continue

            if len(secondPoint) == 2:
                alternate = True
                startingPoint = secondPoint[0]
                secondPoint = secondPoint[1]
            v, d = self.vi.measure_distance(startingPoint, secondPoint, vec=True)
            startingPoint = get_reflected_point(self, startingPoint)
            secondPoint = get_reflected_point(self, secondPoint)
            rotMatj, jtrans = self.getJtransRot(startingPoint, secondPoint)
            if r:
                # reverse mode
                rotMatj, jtrans = self.getJtransRot(secondPoint, startingPoint)
            cent1T = self.transformPoints(jtrans, rotMatj, self.positions[-1])
            cent2T = self.transformPoints(jtrans, rotMatj, self.positions2[-1])
            print(
                "here is output of walk",
                startingPoint,
                secondPoint,
                d,
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
                    # rbnode = histoVol.callFunction(histoVol.addRB,(self, numpy.array(jtrans), numpy.array(rotMatj),),{"rtype":self.type},)#cylinder
                    # histoVol.callFunction(histoVol.moveRBnode,(rbnode, jtrans, rotMatj,))
                    insidePoints, newDistPoints = self.get_new_distance_values(
                        jtrans=jtrans,
                        rotMatj=rotMatj,
                        gridPointsCoords=gridPointsCoords,
                        distance=distance,
                        dpad=dpad,
                        centT=cent1T,
                    )

                    nbFreePoints = BaseGrid.updateDistances(
                        insidePoints,
                        newDistPoints,
                        free_points,
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
                        + str(self.left_to_place),
                    )
                else:
                    autopack.helper.progressBar(
                        progress=int((self.currentLength / self.length) * 100),
                        label=self.name
                        + str(self.currentLength / self.length)
                        + " "
                        + str(self.nbCurve)
                        + "/"
                        + str(self.left_to_place),
                    )

                    # Start Graham on 5/16/12 This progress bar doesn't work properly... compare with my version in HistoVol
                if self.currentLength >= self.length:
                    Done = True
                    self.counter = counter + 1

                previousPoint = startingPoint
                startingPoint = secondPoint
            else:
                secondPoint = startingPoint
                break
        return success, nbFreePoints, free_points

    def updateGrid(
        self,
        rg,
        histoVol,
        dpad,
        free_points,
        nbFreePoints,
        distance,
        gridPointsCoords,
    ):
        insidePoints = {}
        newDistPoints = {}
        for i in range(rg):  # len(self.results)):
            jtrans, rotMatj = self.results[-i]
            cent1T = self.transformPoints(jtrans, rotMatj, self.positions[-1])
            new_inside_pts, new_dist_points = self.get_new_distance_values(
                jtrans=jtrans,
                rotMatj=rotMatj,
                gridPointsCoords=gridPointsCoords,
                distance=distance,
                dpad=dpad,
                centT=cent1T,
            )
            insidePoints = self.merge_place_results(new_inside_pts, insidePoints)
            newDistPoints = self.merge_place_results(new_dist_points, newDistPoints)
            # update free points
            nbFreePoints = BaseGrid.updateDistances(
                new_inside_pts, new_dist_points, free_points, nbFreePoints, distance
            )
        return insidePoints, newDistPoints, nbFreePoints, free_points

    def getFirstPoint(self, ptInd, seed=0):
        if (
            self.compartment_id > 0
        ):  # surfacegrowing: first point is aling to the normal:
            v2 = self.env.compartments[
                abs(self.compartment_id) - 1
            ].surfacePointsNormals[ptInd]
            secondPoint = (
                numpy.array(self.startingpoint) + numpy.array(v2) * self.uLength
            )
        else:
            # randomize the orientation in the hemisphere following the direction.
            v = self.vi.rotate_about_axis(
                numpy.array(self.orientation),
                random() * math.radians(self.marge),  # or marge ?
                # axis=list(self.orientation).index(0),
                axis=2,  # TODO: revert to original implementation for 3D packing
            )
            self.vector = (
                numpy.array(v).flatten() * self.uLength * self.max_jitter
            )  # = (1,0,0)self.vector.flatten()
            secondPoint = self.startingpoint + self.vector
            # seed="F"
            if seed:
                seed = "R"
                secondPoint = self.startingpoint - self.vector
            else:
                seed = "F"
            inside = self.env.grid.checkPointInside(
                secondPoint, dist=self.cutoff_boundary, jitter=self.max_jitter
            )
            closeS = False
            if inside and self.compartment_id <= 0:
                # only if not surface ingredient
                closeS = self.far_enough_from_surfaces(
                    secondPoint, cutoff=self.cutoff_surface
                )
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
                    pt = numpy.array(p) * numpy.array(self.max_jitter)
                    secondPoint = self.startingpoint + numpy.array(pt)
                    inside = self.env.grid.checkPointInside(
                        secondPoint, dist=self.cutoff_boundary, jitter=self.max_jitter
                    )
                    if self.compartment_id <= 0:
                        closeS = self.far_enough_from_surfaces(
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

    def grow_place(
        self,
        env,
        ptInd,
        free_points,
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
        if self.compartment_id > 0:
            normal = env.compartments[
                abs(self.compartment_id) - 1
            ].surfacePointsNormals[ptInd]
        self.startingpoint = previousPoint = startingPoint = self.jitterPosition(
            numpy.array(env.grid.masterGridPositions[ptInd]),
            env.smallestProteinSize,
            normal=normal,
        )
        v, u = self.vi.measure_distance(self.positions, self.positions2, vec=True)
        self.vector = numpy.array(self.orientation) * self.uLength

        # if u != self.uLength:
        #     self.positions2 = [[self.vector]]
        if self.compartment_id == 0:
            compartment = self.env
        else:
            compartment = self.env.compartments[abs(self.compartment_id) - 1]
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

        # reflect points back in-plane (useful for 2D packing)
        previousPoint = get_reflected_point(self, previousPoint)
        startingPoint = get_reflected_point(self, startingPoint)
        secondPoint = get_reflected_point(self, secondPoint)

        rotMatj, jtrans = self.getJtransRot(startingPoint, secondPoint)
        # test for collision
        # return success, nbFreePoints
        self.results.append([jtrans, rotMatj])

        # rebuild kdtree
        if len(self.env.rTrans) > 1:
            self.env.close_ingr_bhtree = spatial.cKDTree(
                self.env.packed_objects.get_positions(), leafsize=10
            )

        self.currentLength = 0.0
        #        self.Ptis=[ptInd,histoVol.grid.getPointFrom3D(secondPoint)]
        dist, pid = env.grid.getClosestGridPoint(secondPoint)
        self.Ptis = [ptInd, pid]
        listePtCurve = [jtrans]
        listePtLinear = [startingPoint, secondPoint]
        # grow until reach self.currentLength >= self.length
        # or attempt > safety
        success, nbFreePoints, free_points = self.grow(
            previousPoint,
            startingPoint,
            secondPoint,
            listePtCurve,
            listePtLinear,
            env,
            ptInd,
            free_points,
            nbFreePoints,
            distance,
            dpad,
            stepByStep=False,
            usePP=usePP,
        )
        insidePoints, newDistPoints, nbFreePoints, free_points = self.updateGrid(
            2,
            env,
            dpad,
            free_points,
            nbFreePoints,
            distance,
            gridPointsCoords,
        )
        if self.seedOnMinus:
            success, nbFreePoints, free_points = self.grow(
                previousPoint,
                listePtLinear[1],
                listePtLinear[0],
                listePtCurve,
                listePtLinear,
                env,
                ptInd,
                free_points,
                nbFreePoints,
                distance,
                dpad,
                stepByStep=False,
                r=True,
            )
            insidePoints, newDistPoints, nbFreePoints, free_points = self.updateGrid(
                2,
                env,
                dpad,
                free_points,
                nbFreePoints,
                distance,
                gridPointsCoords,
            )
        # store result in molecule
        self.log.info("res %d", len(self.results))
        for i in range(len(self.results)):
            jtrans, rotMatj = self.results[-i]
            dist, ptInd = env.grid.getClosestGridPoint(jtrans)
            compartment.molecules.append([jtrans, rotMatj, self, ptInd, self.radius])
            # reset the result ?
        self.results = []
        #        print ("After :",listePtLinear)
        self.listePtCurve.append(listePtCurve)
        self.listePtLinear.append(listePtLinear)
        self.nbCurve += 1
        self.completion = float(self.nbCurve) / float(self.left_to_place)
        self.log.info(
            "completion %r %r %r", self.completion, self.nbCurve, self.left_to_place
        )
        return success, jtrans, rotMatj, insidePoints, newDistPoints

    def prepare_alternates(
        self,
    ):
        if len(self.partners.all_partners):
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
        length = self.partners[alternate].length
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
        ptb = self.partners[alternate].get_point(1)
        ptc = self.partners[alternate].get_point(2)
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
        length = self.partners[alternate].length
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
        length = self.partners[alternate].length
        rotMatj, jtrans = self.getJtransRot_r(
            numpy.array(pt1).flatten(), numpy.array(pt2).flatten(), length=length
        )
        # jtrans is the position between pt1 and pt2
        prevMat = numpy.array(rotMatj)
        prevMat[3, :3] = numpy.array(pt1)  # jtrans
        newv = numpy.array(pt2) - numpy.array(pt1)
        ptb = self.partners[alternate].get_point(1)
        ptc = self.partners[alternate].get_point(2)
        ptd = self.partners[alternate].get_point(3)
        toalign = numpy.array(ptc) - numpy.array(ptb)
        m = numpy.array(rotVectToVect(toalign, newv)).transpose()
        m[3, :3] = numpy.array(pt1)  # jtrans
        pts = autopack.helper.ApplyMatrix([ptb], m.transpose())  # transpose ?
        v = numpy.array(pt1) - pts[0]
        m[3, :3] = numpy.array(pt1) + v
        newPts = autopack.helper.ApplyMatrix([ptc, ptd], m.transpose())  # transpose ?
        return numpy.array(newPts[1]) - numpy.array(newPts[0])

    def place_alternate(self, alternate, alti, v, pt1, pt2):
        pta = self.partners[alternate].get_point(0)
        ptb = self.partners[alternate].get_point(1)
        ptc = self.partners[alternate].get_point(2)
        ptd = self.partners[alternate].get_point(3)
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
        out1 = p_alternate.get_point(0)
        out2 = p_alternate.get_point(1)
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
        priority=0,
        name=None,
        pdb=None,
        color=None,
        jitter_attempts=5,
        max_jitter=(1, 1, 1),
        perturb_axis_amplitude=0.1,
        length=10.0,
        closed=False,
        modelType="Cylinders",
        biased=1.0,
        type="Actine",
        principal_vector=(1, 0, 0),
        meshFile=None,
        packing=None,
        place_method="jitter",
        marge=35.0,
        influenceRad=100.0,
        meshObject=None,
        orientation=(1, 0, 0),
        count=0,
        **kw
    ):
        GrowIngredient.__init__(
            self,
            molarity,
            radii,
            positions,
            positions2,
            priority,
            name,
            pdb,
            color,
            jitter_attempts,
            max_jitter,
            perturb_axis_amplitude,
            length,
            closed,
            modelType,
            biased,
            principal_vector,
            meshFile,
            packing,
            place_method,
            marge,
            meshObject,
            orientation,
            count,
            type,
            **kw
        )
        if name is None:
            name = "Actine_%s_%f" % (str(radii), molarity)
        self.is_attractor = True
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
        self.principal_vector = [1.0, 0.0, 0.0]
        self.uLength = r
        self.length = 2 * r

import numpy
import math
from math import pi, sqrt
from cellpack.autopack.utils import get_distance

from .Ingredient import Ingredient
import cellpack.autopack as autopack

helper = autopack.helper


class SingleCylinderIngr(Ingredient):
    """
    This Ingredient is represented by a single cylinder specified by
    radii, positions and positions2.
    The principal Vector will be used to align the ingredient
    """

    def __init__(
        self,
        bounds,
        radius,
        available_regions=None,
        type="single_cylinder",
        color=None,
        count=0,
        count_options=None,
        cutoff_boundary=None,
        cutoff_surface=0.0,
        distance_expression=None,
        distance_function=None,
        force_random=False,  # avoid any binding
        gradient="",
        is_attractor=False,
        max_jitter=(1, 1, 1),
        molarity=0.0,
        name=None,
        jitter_attempts=5,
        orient_bias_range=[-pi, pi],
        packing_mode="random",
        priority=0,
        partners=None,
        perturb_axis_amplitude=0.1,
        place_method="jitter",
        principal_vector=(1, 0, 0),
        rotation_axis=[0.0, 0.0, 0.0],
        rotation_range=6.2831,
        rejection_threshold=30,
        u_length=None,
        use_orient_bias=False,
        use_rotation_axis=True,
        weight=0.2,  # use for affinity ie partner.weight
    ):
        super().__init__(
            type=type,
            color=color,
            count=count,
            count_options=count_options,
            cutoff_boundary=cutoff_boundary,
            cutoff_surface=cutoff_surface,
            distance_expression=distance_expression,
            distance_function=distance_function,
            force_random=force_random,  # avoid any binding
            gradient=gradient,
            is_attractor=is_attractor,
            max_jitter=max_jitter,
            molarity=molarity,
            name=name,
            jitter_attempts=jitter_attempts,
            packing_mode=packing_mode,
            priority=priority,
            partners=partners,
            perturb_axis_amplitude=perturb_axis_amplitude,
            place_method=place_method,
            principal_vector=principal_vector,
            rejection_threshold=rejection_threshold,
            rotation_axis=rotation_axis,
            rotation_range=rotation_range,
            use_orient_bias=use_orient_bias,
            use_rotation_axis=use_rotation_axis,
            weight=weight,
        )

        if name is None:
            name = "%s_%f" % (str(radius), molarity)
        self.name = name
        self.model_type = "Cylinders"
        self.collisionLevel = 0
        self.min_radius = self.radius
        self.length = get_distance(bounds[1], bounds[0])
        self.nbCurve = 2
        bottom_cent = numpy.array(bounds[0])
        top_cent = numpy.array(bounds[1])

        self.axis = top_cent - bottom_cent
        self.principal_vector = self.axis / self.length
        self.center = (
            bottom_cent + (top_cent - bottom_cent) / 2
        )  # location of center based on top and bottom

        self.encapsulating_radius = numpy.sqrt(radius**2 + (self.length / 2.0) ** 2)

        self.listePtLinear = [
            bottom_cent,
            bottom_cent + self.axis,
        ]

    def initialize_mesh(self, mesh_store):
        if self.mesh is None and autopack.helper is not None:
            self.mesh = autopack.helper.Cylinder(
                self.name + "_basic",
                radius=self.radii[0][0] * 1.24,
                length=self.length,
                res=5,
                parent="autopackHider",
                axis=self.principal_vector,
            )[0]

    def get_cuttoff_value(self, spacing):
        """Returns the min value a grid point needs to be away from a surfance
        in order for this ingredient to pack. Only needs to be calculated once
        per ingredient once the jitter is set."""
        if self.min_distance > 0:
            return self.min_distance
        radius = self.min_radius
        jitter = self.getMaxJitter(spacing)

        if self.packing_mode == "close":
            cut = self.length - jitter
        #            if ingrmodel_type=='Cube' : #radius iactually the size
        #                cut = min(self.radii[0]/2.)-jitter
        #            elif ingr.cutoff_boundary is not None :
        #                #this mueay work if we have the distance from the border
        #                cut  = radius+ingr.cutoff_boundary-jitter

        else:
            cut = radius - jitter
        self.min_distance = cut
        return cut

    def getBigBB(self):
        # one level for cylinder
        bbs = []
        for radc, p1, p2 in zip(self.radii[0], self.positions[0], self.positions2[0]):
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
        return bb

    def collides_with_compartment(
        self,
        env,
        jtrans,
        rotation_matrix=None,
    ):
        """
        Check cylinders for collision
        """
        level = self.deepest_level
        centers1 = (self.positions[level],)
        centers2 = (self.positions2[level],)
        radii = (self.radii[level],)
        cent1T = self.transformPoints(jtrans, rotation_matrix, centers1)
        cent2T = self.transformPoints(jtrans, rotation_matrix, centers2)

        cylNum = 0
        for radc, p1, p2 in zip(radii, cent1T, cent2T):
            x1, y1, z1 = p1
            x2, y2, z2 = p2
            vx, vy, vz = vect = (x2 - x1, y2 - y1, z2 - z1)
            lengthsq = vx * vx + vy * vy + vz * vz
            length = math.sqrt(lengthsq)
            cx, cy, cz = posc = x1 + vx * 0.5, y1 + vy * 0.5, z1 + vz * 0.5
            radt = length + radc

            bb = self.correctBB(p1, p2, radc)
            pointsInCube = env.grid.getPointsInCube(bb, posc, radt, info=True)

            # check for collisions with cylinder
            pd = numpy.take(env.grid.gridPointsCoords, pointsInCube, 0) - p1
            dotp = numpy.dot(pd, vect)
            #            rad2 = radc*radc
            #            dsq = numpy.sum(pd*pd, 1) - dotp*dotp/lengthsq
            ptsWithinCaps = numpy.nonzero(
                numpy.logical_and(
                    numpy.greater_equal(dotp, 0.0), numpy.less_equal(dotp, lengthsq)
                )
            )

            ptsInSphereId = numpy.take(pointsInCube, ptsWithinCaps[0], 0)
            compIdsSphere = numpy.take(env.grid.compartment_ids, ptsInSphereId, 0)
            if self.compartment_id <= 0:
                wrongPt = [cid for cid in compIdsSphere if cid != self.compartment_id]
                if len(wrongPt):
                    #                        print wrongPt
                    return True
            cylNum += 1
        return False

    def collision_jitter(
        self,
        jtrans,
        rotMat,
        level,
        gridPointsCoords,
        distance,
        histoVol,
        dpad,
    ):
        """
        Check cylinders for collision
        """
        centers1 = self.positions[level]
        centers2 = self.positions2[level]
        radii = self.radii[level]
        return self.checkCylCollisions(
            centers1,
            centers2,
            radii,
            jtrans,
            rotMat,
            gridPointsCoords,
            distance,
            histoVol,
            dpad,
        )

    def checkCylCollisions(
        self,
        centers1,
        centers2,
        radii,
        jtrans,
        rotMat,
        gridPointsCoords,
        distance,
        env,
        dpad,
    ):
        """
        Check cylinders for collision
        """
        cent1T = self.transformPoints(jtrans, rotMat, centers1)
        cent2T = self.transformPoints(jtrans, rotMat, centers2)

        insidePoints = {}
        newDistPoints = {}

        cylNum = 0
        for radc, p1, p2 in zip(radii, cent1T, cent2T):
            if env.runTimeDisplay > 1:
                name = "cyl"
                cyl = self.vi.getObject("cyl")
                if cyl is None:
                    cyl = self.vi.oneCylinder(
                        name, p1, p2, color=(1.0, 1.0, 1.0), radius=radc
                    )
                # self.vi.updateTubeMesh(cyl,cradius=radc)
                else:
                    self.vi.updateOneCylinder(cyl, p1, p2, radius=radc)
                self.vi.changeObjColorMat(cyl, (1.0, 1.0, 1.0))
                name = "sph1"
                sph1 = self.vi.getObject("sph1")
                if sph1 is None:
                    sph1 = self.vi.Sphere(name, radius=radc * 2.0)[0]
                self.vi.setTranslation(sph1, p1)
                name = "sph2"
                sph2 = self.vi.getObject("sph2")
                if sph2 is None:
                    sph2 = self.vi.Sphere(name, radius=radc * 2.0)[0]
                self.vi.setTranslation(sph2, p2)

                self.vi.update()

            x1, y1, z1 = p1
            x2, y2, z2 = p2
            vx, vy, vz = vect = (x2 - x1, y2 - y1, z2 - z1)
            lengthsq = vx * vx + vy * vy + vz * vz
            cx, cy, cz = posc = x1 + vx * 0.5, y1 + vy * 0.5, z1 + vz * 0.5
            radt = sqrt(lengthsq + radc**2)

            bb = self.correctBB(p1, p2, radc)
            #            bb = self.correctBB(posc,posc,radt)
            if env.runTimeDisplay > 1:
                box = self.vi.getObject("collBox")
                if box is None:
                    box = self.vi.Box("collBox", cornerPoints=bb, visible=1)
                else:
                    #                    self.vi.toggleDisplay(box,True)
                    self.vi.updateBox(box, cornerPoints=bb)
                    self.vi.update()
                    #                 sleep(1.0)
            pointsInCube = env.grid.getPointsInCube(bb, posc, radt, info=True)

            # check for collisions with cylinder
            pd = numpy.take(gridPointsCoords, pointsInCube, 0) - p1
            dotp = numpy.dot(pd, vect)
            rad2 = radc * radc
            d2toP1 = numpy.sum(pd * pd, 1)
            dsq = (
                d2toP1 - dotp * dotp / lengthsq
            )  # perpendicular distance to cylinder axis

            ptsWithinCaps = numpy.nonzero(
                numpy.logical_and(
                    numpy.greater_equal(dotp, 0.0), numpy.less_equal(dotp, lengthsq)
                )
            )
            if not len(ptsWithinCaps[0]):
                print("no point inside the geom?")
                return False, insidePoints, newDistPoints
            if self.compareCompartment:
                ptsInSphereId = numpy.take(pointsInCube, ptsWithinCaps[0], 0)
                compIdsSphere = numpy.take(env.grid.compartment_ids, ptsInSphereId, 0)
                #                print "compId",compIdsSphere
                if self.compartment_id <= 0:
                    wrongPt = [
                        cid for cid in compIdsSphere if cid != self.compartment_id
                    ]
                    if len(wrongPt):
                        return True, insidePoints, newDistPoints

            pd2 = numpy.take(gridPointsCoords, pointsInCube, 0) - p2
            d2toP2 = numpy.sum(pd2 * pd2, 1)

            for pti, pt in enumerate(pointsInCube):
                dist = dsq[pti]
                if dist > rad2:
                    continue  # outside radius
                elif distance[pt] < 0:
                    return True, insidePoints, newDistPoints

                if pt in insidePoints:
                    continue

                if dotp[pti] < 0.0:  # outside 1st cap, p1 is closer
                    d = sqrt(d2toP1[pti]) - radc
                    if d < distance[pt]:  # point in region of influence
                        if pt in newDistPoints:
                            if d < newDistPoints[pt]:
                                newDistPoints[pt] = d
                        else:
                            newDistPoints[pt] = d
                elif dotp[pti] > lengthsq:  # p2 is closer
                    d = sqrt(d2toP2[pti]) - radc
                    if d < distance[pt]:  # point in region of influence
                        if pt in newDistPoints:
                            if d < newDistPoints[pt]:
                                newDistPoints[pt] = d
                        else:
                            newDistPoints[pt] = d
                else:
                    d = sqrt(dsq[pti]) - radc
                    if d < 0.0:  # point is inside curved region
                        if pt in insidePoints:
                            if d < insidePoints[pt]:
                                insidePoints[pt] = d
                        else:
                            insidePoints[pt] = d
            cylNum += 1
        return False, insidePoints, newDistPoints

    def get_signed_distance(
        self,
        packing_location,
        grid_point_location,
        rotation_matrix,
    ):
        # returns the distance to 'grid_point_location' from the nearest cylinder surface
        # the cylinder center is located at packing_location
        # a rotation matrix rotation_matrix is applied to the cylinder
        # bottom_cent = center point of cylinder bottom surface (positions)
        # top_cent = center point of cylinder top surface (positions2)
        radius = self.radii[0][0]

        length = self.length

        bottom_cent = numpy.array(self.positions[0][0] - self.axis / 2)
        top_cent = numpy.array(self.positions2[0][0] - self.axis / 2)

        bottom_cent = numpy.array(
            self.transformPoints(packing_location, rotation_matrix, [bottom_cent])[0]
        )
        top_cent = numpy.array(
            self.transformPoints(packing_location, rotation_matrix, [top_cent])[0]
        )

        axis_vect = top_cent - bottom_cent

        # check where point lies relative to cylinder
        bottom_vect = grid_point_location - bottom_cent
        top_vect = grid_point_location - top_cent

        dist_to_bottom = numpy.linalg.norm(bottom_vect)
        dist_to_top = numpy.linalg.norm(top_vect)

        bottom_cos = numpy.dot(bottom_vect, axis_vect) / length / dist_to_bottom
        top_cos = numpy.dot(top_vect, axis_vect) / length / dist_to_top

        bottom_sin = numpy.sqrt(1 - bottom_cos**2)
        perp_dist = (
            dist_to_bottom * bottom_sin
        )  # perpendicular distance to cylinder axis

        if bottom_cos >= 0 and top_cos <= 0:
            # point lies within top and bottom faces
            if perp_dist > radius:
                return perp_dist - radius
            else:
                top_surf_dist = numpy.abs(dist_to_top * top_cos)
                bottom_surf_dist = numpy.abs(dist_to_bottom * bottom_cos)
                curved_surf_dist = numpy.abs(perp_dist - radius)
                return -min(top_surf_dist, bottom_surf_dist, curved_surf_dist)
        elif bottom_cos >= 0 and top_cos >= 0:
            # point lies beyond top face
            if perp_dist <= radius:
                return dist_to_top * top_cos
            else:
                x_dist = dist_to_top * top_cos
                y_dist = perp_dist - radius
                return numpy.sqrt(x_dist**2 + y_dist**2)
        elif bottom_cos <= 0 and top_cos <= 0:
            # point lies beyond bottom face
            if perp_dist <= radius:
                return numpy.abs(dist_to_bottom * bottom_cos)
            else:
                x_dist = dist_to_bottom * bottom_cos
                y_dist = perp_dist - radius
                return numpy.sqrt(x_dist**2 + y_dist**2)

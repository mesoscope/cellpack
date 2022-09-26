import numpy
import math
from math import pi, sqrt
from panda3d.core import Point3, TransformState
from panda3d.bullet import BulletCylinderShape, BulletRigidBodyNode

from cellpack.autopack.utils import get_distance

from .Ingredient import Ingredient
import cellpack.autopack as autopack
from .utils import pandaMatrice

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
        type="single_cylinder",
        color=None,
        count=0,
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
        packing_priority=0,
        partners=None,
        perturb_axis_amplitude=0.1,
        place_type="jitter",
        principal_vector=(1, 0, 0),
        representations=None,
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
            packing_priority=packing_priority,
            partners=partners,
            perturb_axis_amplitude=perturb_axis_amplitude,
            place_type=place_type,
            principal_vector=principal_vector,
            rejection_threshold=rejection_threshold,
            representations=representations,
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
        self.min_radius = radius
        self.nbCurve = 2
        self.bottom_cent = numpy.array(bounds[0])
        self.top_cent = numpy.array(bounds[1])
        self.length = get_distance(self.top_cent, self.bottom_cent)
        self.radius = radius
        self.axis = self.top_cent - self.bottom_cent
        self.principal_vector = self.axis / self.length
        self.center = (
            self.bottom_cent + (self.top_cent - self.bottom_cent) / 2
        )  # location of center based on top and bottom

        self.encapsulating_radius = numpy.sqrt(radius**2 + (self.length / 2.0) ** 2)

        self.listePtLinear = [
            self.bottom_cent,
            self.bottom_cent + self.axis,
        ]

    def initialize_mesh(self, mesh_store):
        if self.mesh is None:
            self.mesh = mesh_store.create_cylinder(
                self.name + "_basic", radius=self.radius, height=self.length,
            )

            self.getData()

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
        jtrans,
        rotMat,
        level,
        gridPointsCoords,
        env,
    ):
        """
        Check cylinders for collision
        """
        centers1 = (self.positions[level],)
        centers2 = (self.positions2[level],)
        radii = (self.radii[level],)
        cent1T = self.transformPoints(jtrans, rotMat, centers1)
        cent2T = self.transformPoints(jtrans, rotMat, centers2)

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
            pd = numpy.take(gridPointsCoords, pointsInCube, 0) - p1
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
            if self.compNum <= 0:
                wrongPt = [cid for cid in compIdsSphere if cid != self.compNum]
                if len(wrongPt):
                    #                        print wrongPt
                    return True
            cylNum += 1
        return False

    def collision_jitter(
        self,
        packing_location,
        rotation_matrix,
        level,
        gridPointsCoords,
        current_grid_distances,
        env,
        dpad,
    ):
        """
        Check cylinders for collision
        positions denotes the center of the cylinder base surface
        positions2 denotes the center of the cylinder top surface
        """
        bottom_cent = numpy.array(
            self.transformPoints(packing_location, rotation_matrix, [self.bottom_cent])[0]
        )
        top_cent = numpy.array(
            self.transformPoints(packing_location, rotation_matrix, [self.top_cent])[0]
        )

        center_trans = (top_cent + bottom_cent) / 2

        insidePoints = {}
        newDistPoints = {}

        search_radius = 2 * self.encapsulating_radius + dpad

        bb = self.correctBB(
            bottom_cent, top_cent, search_radius
        )  # bounding box in world space

        if env.runTimeDisplay:  # > 1:
            box = self.vi.getObject("collBox")
            if box is None:
                box = self.vi.Box(
                    "collBox", cornerPoints=bb, visible=1
                )  # cornerPoints=bb,visible=1)
            else:
                self.vi.updateBox(box, cornerPoints=bb)
            self.vi.update()

        points_to_check = env.grid.getPointsInCube(
            bb, center_trans, search_radius
        )  # indices of all grid points within padded distance from cube center

        grid_point_vectors = numpy.take(gridPointsCoords, points_to_check, 0)

        # signed distances of grid points from the cube surface
        grid_point_distances = []
        for grid_point in grid_point_vectors:
            grid_point_distance = self.get_signed_distance(
                center_trans,
                grid_point,
                rotation_matrix,
            )
            grid_point_distances.append(grid_point_distance)

        for pti in range(len(points_to_check)):
            # pti = point index

            grid_point_index = points_to_check[pti]
            signed_distance_to_cyl_surface = grid_point_distances[pti]

            collision = (
                signed_distance_to_cyl_surface
                + current_grid_distances[grid_point_index]
                <= 0
            )

            if collision:
                self.log.info("grid point already occupied %f", grid_point_index)
                return True, {}, {}

            # check if grid point lies inside the cube
            if signed_distance_to_cyl_surface <= 0:
                if grid_point_index not in insidePoints or abs(
                    signed_distance_to_cyl_surface
                ) < abs(insidePoints[grid_point_index]):
                    insidePoints[grid_point_index] = signed_distance_to_cyl_surface
            elif (
                signed_distance_to_cyl_surface
                <= current_grid_distances[grid_point_index]
            ):
                # update grid distances if no collision was detected
                if grid_point_index in newDistPoints:
                    newDistPoints[grid_point_index] = min(
                        signed_distance_to_cyl_surface, newDistPoints[grid_point_index]
                    )
                else:
                    newDistPoints[grid_point_index] = signed_distance_to_cyl_surface
        self.listePtLinear = self.transformPoints(packing_location, rotation_matrix, self.listePtLinear)
        return False, insidePoints, newDistPoints

    def add_rb_node(self, worldNP):
        inodenp = worldNP.attachNewNode(BulletRigidBodyNode(self.name))
        inodenp.node().setMass(1.0)
        centT1 = self.positions[
            0
        ]  # ingr.transformPoints(jtrans, rotMat, ingr.positions[0])
        centT2 = self.positions2[
            0
        ]  # ingr.transformPoints(jtrans, rotMat, ingr.positions2[0])
        for radc, p1, p2 in zip(self.radii[0], centT1, centT2):
            length, mat = autopack.helper.getTubePropertiesMatrix(p1, p2)
            pMat = pandaMatrice(mat)
            #            d = numpy.array(p1) - numpy.array(p2)
            #            s = numpy.sum(d*d)
            Point3(
                self.principal_vector[0],
                self.principal_vector[1],
                self.principal_vector[2],
            )
            shape = BulletCylinderShape(
                radc, length, 1
            )  # math.sqrt(s), 1)# { XUp = 0, YUp = 1, ZUp = 2 } or LVector3f const half_extents
            inodenp.node().addShape(shape, TransformState.makeMat(pMat))  #
        return inodenp

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
                if self.compNum <= 0:
                    wrongPt = [cid for cid in compIdsSphere if cid != self.compNum]
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
        radius = self.radius

        length = self.length 

        bottom_cent = numpy.array(
            self.transformPoints(packing_location, rotation_matrix, [self.bottom_cent])[0]
        )
        top_cent = numpy.array(
            self.transformPoints(packing_location, rotation_matrix, [self.top_cent])[0]
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

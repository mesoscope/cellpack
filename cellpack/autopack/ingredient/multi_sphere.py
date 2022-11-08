from panda3d.core import Point3, TransformState
from panda3d.bullet import BulletSphereShape, BulletRigidBodyNode
from math import pi
import numpy

from .Ingredient import Ingredient
import cellpack.autopack as autopack

helper = autopack.helper


class MultiSphereIngr(Ingredient):
    """
    This Ingredient is represented by a collection of spheres specified by radii
    and positions. The principal Vector will be used to align the ingredient
    """

    def __init__(
        self,
        representations,  # required because the representations.packing dictionary will have the spheres
        available_regions=None,
        color=None,
        count=0,
        cutoff_boundary=None,
        cutoff_surface=None,
        gradient=None,
        is_attractor=False,
        max_jitter=(1, 1, 1),
        molarity=0.0,
        name=None,
        jitter_attempts=5,
        offset=[0, 0, 0],
        orient_bias_range=[-pi, pi],
        overwrite_distance_function=True,  # overWrite
        packing_mode="random",
        packing=0,
        partners=None,
        perturb_axis_amplitude=0.1,
        place_method="jitter",
        principal_vector=(1, 0, 0),
        priority=0,
        rejection_threshold=30,
        rotation_axis=[0.0, 0.0, 0.0],
        rotation_range=0,
        type="MultiSphere",
        use_orient_bias=False,
        use_rotation_axis=True,
        weight=0.2,  # use for affinity ie partner.weight
    ):
        super().__init__(
            color=color,
            cutoff_boundary=cutoff_boundary,
            count=count,
            cutoff_surface=cutoff_surface,
            gradient=gradient,
            is_attractor=is_attractor,
            max_jitter=max_jitter,
            molarity=molarity,
            name=name,
            jitter_attempts=jitter_attempts,
            offset=offset,
            orient_bias_range=orient_bias_range,
            packing_mode=packing_mode,
            priority=priority,
            partners=partners,
            perturb_axis_amplitude=perturb_axis_amplitude,
            place_method=place_method,
            principal_vector=principal_vector,
            representations=representations,
            rotation_axis=rotation_axis,
            rotation_range=rotation_range,
            type=type,
            use_orient_bias=use_orient_bias,
            use_rotation_axis=use_rotation_axis,
            weight=weight,
        )
        self.name = name

        self.radii = self.representations.get_radii()
        self.positions = self.representations.get_positions()
        self.deepest_level = self.representations.get_deepest_level()
        (
            self.min_radius,
            self.encapsulating_radius,
        ) = self.representations.get_min_max_radius()
        if name is None:
            name = "%s_%f" % (str(self.radii), molarity)

    def collision_jitter(
        self,
        jtrans,
        rotMat,
        level,
        gridPointsCoords,
        current_grid_distances,
        env,
        dpad,
    ):
        """
        Check spheres for collision
        """
        centers = self.positions[level]
        radii = self.radii[level]
        # should we also check for outside the main grid ?
        # wouldnt be faster to do sphere-sphere distance test ? than points/points from the grid
        centT = self.transformPoints(jtrans, rotMat, centers)  # centers)
        # sphNum = 0  # which sphere in the sphere tree we're checking
        # self.distances_temp = []
        insidePoints = {}
        newDistPoints = {}
        at_max_level = level == self.deepest_level and (level + 1) == len(
            self.positions
        )
        for radius_of_ing_being_packed, posc in zip(radii, centT):
            x, y, z = posc
            radius_of_area_to_check = (
                radius_of_ing_being_packed + dpad
            )  # extends the packing ingredient's bounding box to be large enough to include masked gridpoints of the largest possible ingrdient in the receipe
            #  TODO: add realtime render here that shows all the points being checked by the collision

            pointsToCheck = env.grid.getPointsInSphere(
                posc, radius_of_area_to_check
            )  # indices
            # check for collisions by looking at grid points in the sphere of radius radc
            delta = numpy.take(gridPointsCoords, pointsToCheck, 0) - posc
            delta *= delta
            distA = numpy.sqrt(delta.sum(1))

            for pti in range(len(pointsToCheck)):
                grid_point_index = pointsToCheck[
                    pti
                ]  # index of master grid point that is inside the sphere
                distance_to_packing_location = distA[
                    pti
                ]  # is that point's distance from the center of the sphere (packing location)
                # distance is an array of distance of closest contact to anything currently in the grid
                collision = (
                    current_grid_distances[grid_point_index]
                    + distance_to_packing_location
                    <= radius_of_ing_being_packed
                )

                if collision:
                    # an object is too close to the sphere at this level
                    if not at_max_level:
                        # if we haven't made it all the way down the sphere tree,
                        # check a level down
                        new_level = level + 1
                        # NOTE: currently with sphere trees, no children seem present
                        # get sphere that are children of this one
                        # ccenters = []
                        # cradii = []
                        # for sphInd in self.children[level][sphNum]:
                        #     ccenters.append(nxtLevelSpheres[sphInd])
                        #     cradii.append(nxtLevelRadii[sphInd])
                        return self.collision_jitter(
                            jtrans,
                            rotMat,
                            new_level,
                            gridPointsCoords,
                            current_grid_distances,
                            env,
                            dpad,
                        )
                    else:
                        self.log.info(
                            "grid point already occupied %f",
                            current_grid_distances[grid_point_index],
                        )
                        return True, {}, {}
                if not at_max_level:
                    # we don't want to calculate new distances if we are not
                    # at the highest geo
                    # but getting here means there was no collision detected
                    # so the loop can continue
                    continue
                signed_distance_to_sphere_surface = (
                    distance_to_packing_location - radius_of_ing_being_packed
                )

                (
                    insidePoints,
                    newDistPoints,
                ) = self.get_new_distances_and_inside_points(
                    env,
                    jtrans,
                    rotMat,
                    grid_point_index,
                    current_grid_distances,
                    newDistPoints,
                    insidePoints,
                    signed_distance_to_sphere_surface,
                )

            if not at_max_level:
                # we didn't find any colisions with the this level, but we still want
                # the inside points to be based on the most detailed geom
                new_level = self.deepest_level
                return self.collision_jitter(
                    jtrans,
                    rotMat,
                    new_level,
                    gridPointsCoords,
                    current_grid_distances,
                    env,
                    dpad,
                )
        return False, insidePoints, newDistPoints

    def add_rb_node(self, worldNP):
        inodenp = worldNP.attachNewNode(BulletRigidBodyNode(self.name))
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

    def get_signed_distance(
        self,
        packing_location,
        grid_point_location,
        rotation_matrix=None,
    ):
        level = self.deepest_level
        centers = self.positions[level]
        radii = self.radii[level]
        centers_trans = self.transformPoints(
            packing_location, rotation_matrix, centers
        )  # centers)

        closest_distance = numpy.inf
        for current_radius, center_position in zip(radii, centers_trans):
            distance_to_packing_location = numpy.linalg.norm(
                center_position - grid_point_location
            )
            signed_distance_to_surface = distance_to_packing_location - current_radius
            if signed_distance_to_surface < closest_distance:
                closest_distance = signed_distance_to_surface

        return closest_distance

    def pack_at_grid_pt_location(
        self,
        env,
        jtrans,
        rotMatj,
        dpad,
        grid_point_distances,
        inside_points,
        new_dist_points,
    ):
        level = self.deepest_level
        centers = self.positions[level]
        radii = self.radii[level]
        centT = self.transformPoints(jtrans, rotMatj, centers)  # centers)
        gridPointsCoords = env.grid.masterGridPositions
        for radius_of_sphere_in_tree, pos_of_sphere in zip(radii, centT):
            radius_of_area_to_check = (
                radius_of_sphere_in_tree + dpad
            )  # extends the packing ingredient's bounding box to be large enough to include masked gridpoints of the largest possible ingrdient in the receipe

            pointsToCheck = env.grid.getPointsInSphere(
                pos_of_sphere, radius_of_area_to_check
            )  # indices
            # check for collisions by looking at grid points in the sphere of radius radc
            delta = numpy.take(gridPointsCoords, pointsToCheck, 0) - pos_of_sphere
            delta *= delta
            distA = numpy.sqrt(delta.sum(1))

            for pti in range(len(pointsToCheck)):
                grid_point_index = pointsToCheck[
                    pti
                ]  # index of master grid point that is inside the sphere
                distance_to_packing_location = distA[
                    pti
                ]  # is that point's distance from the center of the sphere (packing location)
                # distance is an array of distance of closest contact to anything currently in the grid

                signed_distance_to_sphere_surface = (
                    distance_to_packing_location - radius_of_sphere_in_tree
                )
                (
                    inside_points,
                    new_dist_points,
                ) = self.get_new_distances_and_inside_points(
                    env,
                    jtrans,
                    rotMatj,
                    grid_point_index,
                    grid_point_distances,
                    new_dist_points,
                    inside_points,
                    signed_distance_to_sphere_surface,
                )

        return inside_points, new_dist_points

    def collides_with_compartment(
        self,
        env,
        jtrans,
        rotation_matrix,
    ):
        """
        Check spheres for collision
        TODO improve the testwhen grid stepSize is larger that size of the ingredient
        """
        level = self.deepest_level
        centers = self.positions[level]
        radii = (self.radii[level],)
        centT = self.transformPoints(jtrans, rotation_matrix, centers)
        for radc, posc in zip(radii, centT):
            ptsInSphere = env.grid.getPointsInSphere(posc, radc[0])  # indices
            compIdsSphere = numpy.take(env.grid.compartment_ids, ptsInSphere, 0)
            wrongPt = [cid for cid in compIdsSphere if cid != self.compNum]
            if len(wrongPt):
                return True
        return False

    def calculate_distance(
        self,
        sphere_position,
        gridPointsCoords,
        distance,
        dpad,
        radius,
        inside_points,
        new_dist_points,
    ):
        padded_sphere = radius + dpad
        ptsInSphere = self.env.grid.getPointsInSphere(sphere_position, padded_sphere)
        delta = numpy.take(gridPointsCoords, ptsInSphere, 0) - sphere_position
        delta *= delta
        distA = numpy.sqrt(delta.sum(1))
        for pti in range(len(ptsInSphere)):
            pt = ptsInSphere[pti]
            dist = distA[pti]
            d = dist - radius
            if d <= 0:  # point is inside dropped sphere
                if pt in inside_points:
                    if abs(d) < abs(inside_points[pt]):
                        inside_points[pt] = d
                else:
                    inside_points[pt] = d
            elif d < distance[pt]:  # point in region of influence
                if pt in new_dist_points:
                    if d < new_dist_points[pt]:
                        new_dist_points[pt] = d
                else:
                    new_dist_points[pt] = d
        return inside_points, new_dist_points

    def get_new_distance_values(
        self, jtrans, rotation_matrix, grid_points_coords, distance, dpad, level=0
    ):
        level = self.deepest_level
        centers = self.positions[level]
        radii = self.radii[level]
        transformed_centers = self.transformPoints(jtrans, rotation_matrix, centers)
        inside_points = {}
        new_dist_points = {}
        for sphere_radius, sphere_position in zip(radii, transformed_centers):
            # grid_points_to_update = self.env.grid.getPointsInSphere(
            #     posc, radius_of_area_to_check
            # )
            # # check for collisions by looking at grid points in the sphere of radius radc
            # delta = numpy.take(grid_points_coords, grid_points_to_update, 0) - posc
            # delta *= delta
            # distA = numpy.sqrt(delta.sum(1))

            # for pti in range(len(grid_points_to_update)):
            #     grid_point_index = grid_points_to_update[
            #         pti
            #     ]  # index of master grid point that is inside the sphere
            #     distance_to_packing_location = distA[
            #         pti
            #     ]  # is that point's distance from the center of the sphere (packing location)
            # distance is an array of distance of closest contact to anything currently in the grid
            inside_points, new_dist_points = self.calculate_distance(
                sphere_position,
                grid_points_coords,
                distance,
                dpad,
                sphere_radius,
                inside_points,
                new_dist_points,
            )
        return inside_points, new_dist_points

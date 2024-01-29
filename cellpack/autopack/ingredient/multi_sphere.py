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
        count_options=None,
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
        object_name=None,
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
            count_options=count_options,
            cutoff_surface=cutoff_surface,
            gradient=gradient,
            is_attractor=is_attractor,
            max_jitter=max_jitter,
            molarity=molarity,
            name=name,
            jitter_attempts=jitter_attempts,
            object_name=object_name,
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

    def get_radius(self):
        return self.encapsulating_radius

    def get_new_distance_values(
        self,
        packed_position,
        packed_rotation,
        gridPointsCoords,
        distance,
        dpad,
        level,
    ):
        inside_points = {}
        new_dist_points = {}
        padded_sphere = self.radius + dpad
        ptsInSphere = self.env.grid.getPointsInSphere(packed_position, padded_sphere)
        delta = numpy.take(gridPointsCoords, ptsInSphere, 0) - packed_position
        delta *= delta
        distA = numpy.sqrt(delta.sum(1))
        for pti in range(len(ptsInSphere)):
            pt = ptsInSphere[pti]
            dist = distA[pti]
            d = dist - self.radius
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
        transformed_centers = self.transformPoints(jtrans, rotMat, centers)  # centers)
        # sphNum = 0  # which sphere in the sphere tree we're checking
        # self.distances_temp = []
        insidePoints = {}
        newDistPoints = {}
        at_max_level = level == self.deepest_level and (level + 1) == len(
            self.positions
        )
        for radius_of_ing_being_packed, posc in zip(radii, transformed_centers):
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
        rotation_matrix,
        dpad,
        grid_point_distances,
        inside_points,
        new_dist_points,
        pt_index,
    ):
        level = self.deepest_level
        centers = self.positions[level]
        radii = self.radii[level]
        transformed_centers = self.transformPoints(
            jtrans, rotation_matrix, centers
        )  # centers)
        grid_points_coords = env.grid.masterGridPositions
        self.store_packed_object(jtrans, rotation_matrix, pt_index)
        for radius_of_sphere_in_tree, pos_of_sphere in zip(radii, transformed_centers):
            radius_of_area_to_check = (
                radius_of_sphere_in_tree + dpad
            )  # extends the packing ingredient's bounding box to be large enough to include masked grid points of the largest possible ingredient in the recipe

            points_to_check = env.grid.getPointsInSphere(
                pos_of_sphere, radius_of_area_to_check
            )  # indices
            # check for collisions by looking at grid points in the sphere of radius radc
            delta = numpy.take(grid_points_coords, points_to_check, 0) - pos_of_sphere
            delta *= delta
            distA = numpy.sqrt(delta.sum(1))

            for pti in range(len(points_to_check)):
                grid_point_index = points_to_check[
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
                    rotation_matrix,
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
        TODO improve the test when grid stepSize is larger that size of the ingredient
        """
        level = self.deepest_level
        centers = self.positions[level]
        radii = (self.radii[level],)
        transformed_centers = self.transformPoints(jtrans, rotation_matrix, centers)
        for radc, posc in zip(radii, transformed_centers):
            ptsInSphere = env.grid.getPointsInSphere(posc, radc[0])  # indices
            compIdsSphere = numpy.take(env.grid.compartment_ids, ptsInSphere, 0)
            wrongPt = [cid for cid in compIdsSphere if cid != self.compartment_id]
            if len(wrongPt):
                return True
        return False

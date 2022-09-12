from panda3d.core import Point3, TransformState
from panda3d.bullet import BulletSphereShape, BulletRigidBodyNode
from math import pi, sqrt
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
        color=None,
        coordsystem="right",
        count=0,
        cutoff_boundary=None,
        cutoff_surface=None,
        excluded_partners_name=None,
        gradient="",
        is_attractor=False,
        max_jitter=(1, 1, 1),
        meshFile=None,
        meshName="",
        meshObject=None,
        meshType="file",
        molarity=0.0,
        name=None,
        jitter_attempts=5,
        offset=None,
        orient_bias_range=[-pi, pi],
        overwrite_distance_function=True,  # overWrite
        packing=None,
        packing_priority=0,
        partners_name=None,
        partners_position=None,
        pdb=None,
        perturb_axis_amplitude=0.1,
        place_type="jitter",
        principal_vector=(1, 0, 0),
        proba_binding=0.5,
        proba_not_binding=0.5,
        properties=None,
        representations=None,
        rejection_threshold=30,
        rotation_axis=[0.0, 0.0, 0.0],
        rotation_range=0,
        source=None,
        type="MultiSphere",
        use_orient_bias=False,
        use_rotation_axis=True,
        weight=0.2,  # use for affinity ie partner.weight
    ):
        super().__init__(
            color=color,
            cutoff_boundary=cutoff_boundary,
            coordsystem=coordsystem,
            count=count,
            cutoff_surface=cutoff_surface,
            excluded_partners_name=excluded_partners_name,
            gradient=gradient,
            is_attractor=is_attractor,
            max_jitter=max_jitter,
            meshFile=meshFile,
            meshName=meshName,
            meshObject=meshObject,
            meshType=meshType,
            molarity=molarity,
            name=name,
            jitter_attempts=jitter_attempts,
            offset=offset,
            orient_bias_range=orient_bias_range,
            packing_priority=packing_priority,
            partners_name=partners_name,
            partners_position=partners_position,
            pdb=pdb,
            perturb_axis_amplitude=perturb_axis_amplitude,
            place_type=place_type,
            principal_vector=principal_vector,
            proba_binding=proba_binding,
            proba_not_binding=proba_not_binding,  # chance to actually not bind
            properties=properties,
            rotation_axis=rotation_axis,
            rotation_range=rotation_range,
            source=source,
            type=type,
            use_orient_bias=use_orient_bias,
            use_rotation_axis=use_rotation_axis,
            weight=weight,
        )
        self.name = name

        positions, radii = self.representations.get_spheres()
        self.set_sphere_positions(positions, radii)
        if name is None:
            name = "%s_%f" % (str(radii), molarity)

    def set_sphere_positions(self, positions, radii):
        # positions and radii are passed to the constructor
        # check the format old nested array, new array of dictionary
        nLOD = 0
        if positions is not None:
            nLOD = len(positions)
        if positions is not None and isinstance(positions[0], dict):
            for i in range(nLOD):
                c = numpy.array(positions[i]["coords"])
                n = int(len(c) / 3)
                self.positions.append(c.reshape((n, 3)).tolist())
                self.radii.append(radii[i]["radii"])
            if len(self.radii) == 0:
                self.radii = [[10]]  # some default value ?
                self.positions = [[[0, 0, 0]]]
            self.deepest_level = len(radii) - 1
        else:  # regular nested
            if radii is not None:
                delta = numpy.array(positions[0])
                rM = sqrt(max(numpy.sum(delta * delta, 1)))
                self.encapsulating_radius = max(rM, self.encapsulating_radius)
            if radii is not None:
                self.deepest_level = len(radii) - 1
            self.radii = radii
            self.positions = positions
        self.min_radius = min(min(self.radii))
        if self.encapsulating_radius <= 0.0 or self.encapsulating_radius < max(
            self.radii[0]
        ):
            self.encapsulating_radius = max(self.radii[0])  #

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
        self, env, jtrans, rotMatj, dpad, grid_point_distances
    ):
        level = self.deepest_level
        centers = self.positions[level]
        radii = self.radii[level]
        centT = self.transformPoints(jtrans, rotMatj, centers)  # centers)
        insidePoints = {}
        newDistPoints = {}
        gridPointsCoords = env.masterGridPositions
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
                    insidePoints,
                    newDistPoints,
                ) = self.get_new_distances_and_inside_points(
                    env,
                    jtrans,
                    rotMatj,
                    grid_point_index,
                    grid_point_distances,
                    newDistPoints,
                    insidePoints,
                    signed_distance_to_sphere_surface,
                )

        return insidePoints, newDistPoints

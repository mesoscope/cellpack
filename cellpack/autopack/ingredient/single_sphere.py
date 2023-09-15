import numpy
from math import pi
from panda3d.bullet import BulletRigidBodyNode, BulletSphereShape
from panda3d.core import Point3, TransformState, Vec3
from panda3d.ode import OdeBody, OdeMass, OdeSphereGeom

import cellpack.autopack as autopack

from .Ingredient import Ingredient

helper = autopack.helper


class SingleSphereIngr(Ingredient):
    """
    This Ingredient is represented by a single sphere
    and either a single radius, or a list of radii and offset vectors
    for each sphere representing the ingredient
    """

    def __init__(
        self,
        radius,
        available_regions=None,
        type="single_sphere",
        color=None,
        count=0,
        count_options=None,
        cutoff_boundary=None,
        cutoff_surface=0.0,
        distance_expression=None,
        distance_function=None,
        force_random=False,  # avoid any binding
        gradient=None,
        is_attractor=False,
        max_jitter=(1, 1, 1),
        molarity=0.0,
        name=None,
        jitter_attempts=5,
        object_name=None,
        offset=None,
        orient_bias_range=[-pi, pi],
        overwrite_distance_function=True,  # overWrite
        packing_mode="random",
        priority=0,
        partners=None,
        perturb_axis_amplitude=0.1,
        place_method="jitter",
        principal_vector=(1, 0, 0),
        representations=None,
        rejection_threshold=30,
        resolution_dictionary=None,
        rotation_axis=[0.0, 0.0, 0.0],
        rotation_range=0,
        size_options=None,
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
            force_random=force_random,
            gradient=gradient,
            is_attractor=is_attractor,
            max_jitter=max_jitter,
            molarity=molarity,
            name=name,
            jitter_attempts=jitter_attempts,
            object_name=object_name,
            overwrite_distance_function=overwrite_distance_function,
            packing_mode=packing_mode,
            priority=priority,
            partners=partners,
            perturb_axis_amplitude=perturb_axis_amplitude,
            place_method=place_method,
            principal_vector=principal_vector,
            representations=representations,
            rotation_axis=rotation_axis,
            rotation_range=rotation_range,
            size_options=size_options,
            use_rotation_axis=use_rotation_axis,
            weight=weight,
        )
        self.model_type = "Spheres"
        if name is None:
            name = "%5.2f_%f" % (radius, molarity)
        self.name = name
        self.mesh = None
        # min and max radius for a single sphere should be the same
        self.radius = radius
        self.encapsulating_radius = radius
        self.min_radius = radius

    @staticmethod
    def create_voxelization(
        self, image_data, bounding_box, voxel_size, image_size, position, rotation, radius, hollow=None, mesh_store=None,
    ):
        """
        Creates a voxelization for the sphere
        """
        relative_position = position - bounding_box[0]
        voxelized_position = (relative_position / voxel_size).astype(int)
        mask = self.create_circular_mask(
            *image_size,
            center=voxelized_position,
            radius=radius,
            voxel_size=voxel_size
        )
        image_data[mask] = 255

        return image_data
    
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

        insidePoints = {}
        newDistPoints = {}

        radius_of_ing_being_packed = self.radius
        position = jtrans
        radius_of_area_to_check = (
            radius_of_ing_being_packed + dpad
        )  # extends the packing ingredient's bounding box to be large enough to include masked gridpoints of the largest possible ingrdient in the receipe
        #  TODO: add realtime render here that shows all the points being checked by the collision

        pointsToCheck = env.grid.getPointsInSphere(
            position, radius_of_area_to_check
        )  # indices
        # check for collisions by looking at grid points in the sphere of radius radc
        distance_to_grid_points = numpy.linalg.norm(
            gridPointsCoords[pointsToCheck] - position, axis=1
        )

        for pti, grid_point_index in enumerate(pointsToCheck):
            distance_to_packing_location = distance_to_grid_points[
                pti
            ]  # is that point's distance from the center of the sphere (packing location)
            # distance is an array of distance of closest contact to anything currently in the grid

            collision = (
                current_grid_distances[grid_point_index] + distance_to_packing_location
                <= radius_of_ing_being_packed
            )

            if collision:
                # an object is too close to the sphere at this level
                self.log.info(
                    "grid point already occupied %f",
                    current_grid_distances[grid_point_index],
                )
                return True, {}, {}

            signed_distance_to_sphere_surface = (
                distance_to_packing_location - radius_of_ing_being_packed
            )

            (insidePoints, newDistPoints,) = self.get_new_distances_and_inside_points(
                env,
                jtrans,
                rotMat,
                grid_point_index,
                current_grid_distances,
                newDistPoints,
                insidePoints,
                signed_distance_to_sphere_surface,
            )
        return False, insidePoints, newDistPoints

    def collides_with_compartment(
        self,
        env,
        jtrans,
        rotation_matrix=None,
    ):
        """
        Check spheres for collision
        TODO improve the testwhen grid stepSize is larger that size of the ingredient
        """
        ptsInSphere = env.grid.getPointsInSphere(jtrans, self.radius)  # indices
        compIdsSphere = numpy.take(env.grid.compartment_ids, ptsInSphere, 0)
        if self.compNum <= 0:
            wrongPt = [cid for cid in compIdsSphere if cid != self.compNum]
            if len(wrongPt):
                return True
        return False

    def get_signed_distance(
        self,
        packing_location,
        grid_point_location,
        rotation_matrix=None,
    ):
        radius = self.radius
        distance_to_packing_location = numpy.linalg.norm(
            packing_location - grid_point_location
        )
        signed_distance_to_surface = distance_to_packing_location - radius
        return signed_distance_to_surface

    def get_new_distance_values(
        self, jtrans, rotMatj, gridPointsCoords, distance, dpad, level=0
    ):
        insidePoints = {}
        newDistPoints = {}
        padded_sphere = self.radius + dpad
        ptsInSphere = self.env.grid.getPointsInSphere(jtrans, padded_sphere)
        delta = numpy.take(gridPointsCoords, ptsInSphere, 0) - jtrans
        delta *= delta
        distA = numpy.sqrt(delta.sum(1))
        for pti in range(len(ptsInSphere)):
            pt = ptsInSphere[pti]
            dist = distA[pti]
            d = dist - self.radius
            if d <= 0:  # point is inside dropped sphere
                if pt in insidePoints:
                    if abs(d) < abs(insidePoints[pt]):
                        insidePoints[pt] = d
                else:
                    insidePoints[pt] = d
            elif d < distance[pt]:  # point in region of influence
                if pt in newDistPoints:
                    if d < newDistPoints[pt]:
                        newDistPoints[pt] = d
                else:
                    newDistPoints[pt] = d
        return insidePoints, newDistPoints

    def add_rb_node(self, worldNP):
        shape = BulletSphereShape(self.encapsulating_radius)
        inodenp = worldNP.attachNewNode(BulletRigidBodyNode(self.name))
        inodenp.node().setMass(1.0)
        #        inodenp.node().addShape(shape)
        inodenp.node().addShape(
            shape, TransformState.makePos(Point3(0, 0, 0))
        )  # rotation ?
        #        spherenp.setPos(-2, 0, 4)
        return inodenp

    def add_rb_node_ode(self, world, jtrans, pMat):
        body = OdeBody(world)
        M = OdeMass()
        M.setSphereTotal(1.0, self.encapsulating_radius)
        body.setMass(M)
        body.setPosition(Vec3(jtrans[0], jtrans[1], jtrans[2]))
        body.setRotation(pMat)
        # the geometry for the collision ?
        geom = OdeSphereGeom(self.ode_space, self.encapsulating_radius)
        geom.setBody(body)
        return geom

    def initialize_mesh(self, mesh_store):
        if self.mesh is None:
            self.mesh = mesh_store.create_sphere(
                self.name + "_basic", 5, radius=self.radius
            )

            self.getData()

    @staticmethod
    def create_circular_mask(
        x_width, y_width, z_width, center=None, radius=None, voxel_size=None
    ):
        """
        Creates a circular mask of the given shape with the specified center
        and radius
        """
        if center is None:  # use the middle of the image
            center = (int(x_width / 2), int(y_width / 2), int(z_width / 2))
        if (
            radius is None
        ):  # use the smallest distance between the center and image walls
            radius = min(
                center[0],
                center[1],
                center[2],
                x_width - center[0],
                y_width - center[1],
                z_width - center[2],
            )

        if voxel_size is None:
            voxel_size = numpy.array([1, 1, 1], dtype=int)

        X, Y, Z = numpy.ogrid[:x_width, :y_width, :z_width]
        dist_from_center = numpy.sqrt(
            ((X - center[0]) * voxel_size[0]) ** 2
            + ((Y - center[1]) * voxel_size[1]) ** 2
            + ((Z - center[2]) * voxel_size[2]) ** 2
        )

        mask = dist_from_center <= radius
        return mask



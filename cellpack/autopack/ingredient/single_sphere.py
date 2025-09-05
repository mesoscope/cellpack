from __future__ import annotations
from typing import List, Tuple, Optional, Dict, Any
import numpy
from math import pi
import numpy as np
import cellpack.autopack as autopack
from .Ingredient import Ingredient

helper = autopack.helper


class SingleSphereIngr(Ingredient):
    """
    This Ingredient is represented by a single sphere
    """

    def __init__(
        self,
        radius: float,
        available_regions: Optional[Any] = None,
        type: str = "single_sphere",
        color: Optional[Any] = None,
        count: int = 0,
        count_options: Optional[Any] = None,
        cutoff_boundary: Optional[Any] = None,
        cutoff_surface: float = 0.0,
        distance_expression: Optional[Any] = None,
        distance_function: Optional[Any] = None,
        force_random: bool = False,
        gradient: Optional[Any] = None,
        gradient_weights: Optional[Any] = None,
        is_attractor: bool = False,
        max_jitter: Tuple[float, float, float] = (1, 1, 1),
        molarity: float = 0.0,
        name: Optional[str] = None,
        jitter_attempts: int = 5,
        object_name: Optional[str] = None,
        offset: Optional[Any] = None,
        orient_bias_range: List[float] = [-pi, pi],
        overwrite_distance_function: bool = True,
        packing_mode: str = "random",
        priority: int = 0,
        partners: Optional[Any] = None,
        perturb_axis_amplitude: float = 0.1,
        place_method: str = "jitter",
        principal_vector: List[float] = [1, 0, 0],
        representations: Optional[Any] = None,
        rejection_threshold: int = 30,
        resolution_dictionary: Optional[Any] = None,
        rotation_axis: List[float] = [0.0, 0.0, 0.0],
        rotation_range: float = 0,
        size_options: Optional[Any] = None,
        use_orient_bias: bool = False,
        use_rotation_axis: bool = True,
        weight: float = 0.2,
    ):
        """
        Initialize a SingleSphereIngr instance.

        Parameters
        ----------
        radius
            The radius of the sphere.
        available_regions
            The available regions for the ingredient.
        type
            The type of the ingredient.
        color
            The color of the ingredient.
        count
            The count of the ingredient.
        count_options
            The count options for the ingredient.
        cutoff_boundary
            The cutoff boundary for the ingredient.
        cutoff_surface
            The cutoff surface for the ingredient.
        distance_expression
            The distance expression for the ingredient.
        distance_function
            The distance function for the ingredient.
        force_random
            Whether to force random placement.
        gradient
            The gradient for the ingredient.
        gradient_weights
            The gradient weights for the ingredient.
        is_attractor
            Whether the ingredient is an attractor.
        max_jitter
            The maximum jitter for the ingredient.
        molarity
            The molarity of the ingredient.
        name
            The name of the ingredient.
        jitter_attempts
            The number of jitter attempts.
        object_name
            The object name of the ingredient.
        offset
            The offset for the ingredient.
        orient_bias_range
            The orientation bias range.
        overwrite_distance_function
            Whether to overwrite the distance function.
        packing_mode
            The packing mode.
        priority
            The priority of the ingredient.
        partners
            The partners of the ingredient.
        perturb_axis_amplitude
            The perturb axis amplitude.
        place_method
            The placement method.
        principal_vector
            The principal vector.
        representations
            The representations of the ingredient.
        rejection_threshold
            The rejection threshold.
        resolution_dictionary
            The resolution dictionary.
        rotation_axis
            The rotation axis.
        rotation_range
            The rotation range.
        size_options
            The size options.
        use_orient_bias
            Whether to use orientation bias.
        use_rotation_axis
            Whether to use rotation axis.
        weight
            The weight of the ingredient.
        """
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
        self.radius = radius
        self.encapsulating_radius = radius
        self.min_radius = radius

    @staticmethod
    def create_circular_mask(
        x_width: int,
        y_width: int,
        z_width: int,
        center: Optional[Tuple[int, int, int]] = None,
        radius: Optional[float] = None,
        voxel_size: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Create a circular mask of the given shape with the specified center and radius.

        Parameters
        ----------
        x_width
            The width of the mask in the x dimension.
        y_width
            The width of the mask in the y dimension.
        z_width
            The width of the mask in the z dimension.
        center
            The center of the mask.
        radius
            The radius of the mask.
        voxel_size
            The size of the voxels.

        Returns
        -------
        :
            A boolean mask array with the same shape as the input dimensions, where the sphere region is marked as True.
        """
        if center is None:
            center = (int(x_width / 2), int(y_width / 2), int(z_width / 2))
        if radius is None:
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

    def get_radius(self) -> float:
        """
        Return the radius of the sphere.

        Returns
        -------
        :
            The radius of the sphere.
        """
        return self.radius

    def collision_jitter(
        self,
        jtrans: np.ndarray,
        rotMat: np.ndarray,
        _: None,
        gridPointsCoords: List[int],
        current_grid_distances: List[float],
        env: "autopack.Environment",
        dpad: float,
    ) -> Tuple[bool, Dict[int, float], Dict[int, float]]:
        """
        Check spheres for collision using the jitter algorithm.

        Parameters
        ----------
        jtrans
            The randomly jittered translation vector, which is close to the selected grid point.
        rotMat
            The randomly jittered rotation matrix.
        _
            Unused parameter.
        gridPointsCoords
            The coordinates of the grid points.
        current_grid_distances
            The current distances of the grid points to the nearest surface.
        env
            The environment object.
        dpad
            The padding distance.

        Returns
        -------
        :
            A tuple containing a bool (True if a collision is detected, False otherwise), a dictionary of points inside the sphere, and a dictionary of new distance points.
        """
        insidePoints: dict = {}
        newDistPoints: dict = {}

        radius_of_ing_being_packed = self.radius
        position = jtrans
        radius_of_area_to_check = radius_of_ing_being_packed + dpad
        pointsToCheck = env.grid.getPointsInSphere(position, radius_of_area_to_check)
        distance_to_grid_points = numpy.linalg.norm(
            gridPointsCoords[pointsToCheck] - position, axis=1
        )

        for pti, grid_point_index in enumerate(pointsToCheck):
            distance_to_packing_location = distance_to_grid_points[pti]
            collision = (
                current_grid_distances[grid_point_index] + distance_to_packing_location
                <= radius_of_ing_being_packed
            )

            if collision:
                self.log.info(
                    "grid point already occupied %f",
                    current_grid_distances[grid_point_index],
                )
                return True, {}, {}

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
        return False, insidePoints, newDistPoints

    def collides_with_compartment(
        self,
        env: "autopack.Environment",
        jtrans: np.ndarray,
        _: Any,
    ) -> bool:
        """
        Check spheres for collision with compartment boundaries.

        Parameters
        ----------
        env
            The environment object.
        jtrans
            The transformed position of the ingredient.
        _
            Unused parameter.

        Returns
        -------
        :
            True if the ingredient collides with the compartment boundaries.
        """
        ptsInSphere = env.grid.getPointsInSphere(jtrans, self.radius)
        compIdsSphere = numpy.take(env.grid.compartment_ids, ptsInSphere, 0)
        if self.compartment_id <= 0:
            wrongPt = [cid for cid in compIdsSphere if cid != self.compartment_id]
            if len(wrongPt):
                return True
        return False

    def get_signed_distance(
        self,
        packing_location: np.ndarray,
        grid_point_location: np.ndarray,
        _: Any,
    ) -> float:
        """
        Compute the signed distance from the packing location to the grid point.

        Parameters
        ----------
        packing_location
            The packing location of the ingredient.
        grid_point_location
            The location of the grid point.
        _
            Unused parameter.

        Returns
        -------
        :
            The signed distance from the packing location to the grid point.
        """
        radius = self.radius
        distance_to_packing_location = numpy.linalg.norm(
            packing_location - grid_point_location
        )
        signed_distance_to_surface = distance_to_packing_location - radius
        return signed_distance_to_surface

    def get_new_distance_values(
        self,
        jtrans: List[float],
        _: Any,
        gridPointsCoords: np.ndarray,
        distance: np.ndarray,
        dpad: float,
        level: int = 0,
    ) -> Tuple[Dict[int, float], Dict[int, float]]:
        """
        Get new distance values for the sphere.

        Parameters
        ----------
        jtrans
            The transformed position of the ingredient.
        _
            Unused parameter.
        gridPointsCoords
            The coordinates of the grid points.
        distance
            The current distance values for the grid points.
        dpad
            The padding distance for the sphere.
        level
            The level of the hierarchy.

        Returns
        -------
        :
            A dictionary of points inside the ingredient and a dictionary of new distance points.
        """
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
            if d <= 0:
                if pt in insidePoints:
                    if abs(d) < abs(insidePoints[pt]):
                        insidePoints[pt] = d
                else:
                    insidePoints[pt] = d
            elif d < distance[pt]:
                if pt in newDistPoints:
                    if d < newDistPoints[pt]:
                        newDistPoints[pt] = d
                else:
                    newDistPoints[pt] = d
        return insidePoints, newDistPoints

    def initialize_mesh(self, mesh_store: Any) -> None:
        """
        Initialize the mesh for the sphere.

        Parameters
        ----------
        mesh_store
            The mesh store to use for creating the sphere mesh.
        """
        if self.mesh is None:
            self.mesh = mesh_store.create_sphere(
                self.name + "_basic", 5, radius=self.radius
            )
            self.getData()

    def create_voxelization(
        self,
        image_data: np.ndarray,
        bounding_box: np.ndarray,
        voxel_size: float,
        image_size: Tuple[int, int, int],
        position: np.ndarray,
        **kwargs,
    ) -> np.ndarray:
        """
        Create a voxelization for the sphere.

        Parameters
        ----------
        image_data
            The image data to voxelize.
        bounding_box
            The bounding box of the sphere.
        voxel_size
            The size of the voxels.
        image_size
            The size of the image.
        position
            The position of the sphere.
        **kwargs
            Additional arguments to pass to the voxelization function.

        Returns
        -------
        :
            The voxelized image data.
        """
        relative_position = position - bounding_box[0]
        voxelized_position = (relative_position / voxel_size).astype(int)
        mask = self.create_circular_mask(
            *image_size,
            center=voxelized_position,
            radius=self.radius,
            voxel_size=voxel_size,
        )
        image_data[mask] = 255

        return image_data

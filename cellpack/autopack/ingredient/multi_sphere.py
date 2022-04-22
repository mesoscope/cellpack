from panda3d.core import Point3, TransformState
from panda3d.bullet import BulletSphereShape, BulletRigidBodyNode
from math import pi

from cellpack.autopack.ingredient.single_sphere import SingleSphereIngr
import cellpack.autopack as autopack
import numpy

helper = autopack.helper


class MultiSphereIngr(SingleSphereIngr):
    """
    This Ingredient is represented by a collection of spheres specified by radii
    and positions. The principal Vector will be used to align the ingredient
    """

    def __init__(
        self,
        color=None,
        coordsystem="right",
        cutoff_boundary=None,
        cutoff_surface=None,
        encapsulatingRadius=0,
        excluded_partners_name=None,
        gradient="",
        isAttractor=False,
        jitterMax=(1, 1, 1),
        meshFile=None,
        meshObject=None,
        molarity=0.0,
        name=None,
        nbJitter=5,
        nbMol=0,
        orientBiasRotRangeMax=-pi,
        orientBiasRotRangeMin=-pi,
        overwrite_distFunc=True,  # overWrite
        overwrite_nbMol_value=None,
        packingMode="random",
        packingPriority=0,
        partners_name=None,
        partners_position=None,
        pdb=None,
        perturbAxisAmplitude=0.1,
        placeType="jitter",
        positions=None,
        positions2=None,
        principalVector=(1, 0, 0),
        proba_binding=0.5,
        proba_not_binding=0.5,  # chance to actually not bind
        properties=None,
        radii=None,
        rejectionThreshold=30,
        rotAxis=[0.0, 0.0, 0.0],
        rotRange=0,
        sphereFile=None,
        Type="MultiSphere",
        useOrientBias=False,
        use_mesh_rb=False,
        useRotAxis=True,
        weight=0.2,  # use for affinity ie partner.weight
    ):
        super().__init__(
            color=color,
            cutoff_surface=cutoff_surface,
            encapsulatingRadius=encapsulatingRadius,
            jitterMax=jitterMax,
            meshFile=meshFile,
            meshObject=meshObject,
            molarity=molarity,
            name=name,
            nbJitter=nbJitter,
            nbMol=nbMol,
            packingMode=packingMode,
            packingPriority=packingPriority,
            pdb=pdb,
            perturbAxisAmplitude=perturbAxisAmplitude,
            placeType=placeType,
            positions=positions,  # positions2=None,
            principalVector=principalVector,
            radii=radii,
            rotAxis=rotAxis,
            rotRange=rotRange,
            sphereFile=sphereFile,
            Type=Type,
        )
        min_radius = encapsulatingRadius
        for level in self.radii:
            if min(level) < min_radius:
                min_radius = min(level)
        self.minRadius = min_radius
        if name is None:
            name = "%s_%f" % (str(radii), molarity)
        self.name = name
        self.singleSphere = False

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

    def get_new_distances_and_inside_points(
        self,
        env,
        packing_location,
        rotation_matrix,
        grid_point_index,
        grid_distance_values,
        new_dist_points,
        inside_points,
        signed_distance_to_surface=None,
    ):
        if signed_distance_to_surface is None:
            grid_point_location = env.grid.masterGridPositions[grid_point_index]
            signed_distance_to_surface = self.get_signed_distance(
                packing_location,
                grid_point_location,
                rotation_matrix,
            )

        if signed_distance_to_surface <= 0:  # point is inside dropped sphere
            if (
                env.grid.gridPtId[grid_point_index] != self.compNum
                and self.compNum <= 0
            ):  # did this jitter outside of it's compartment
                # in wrong compartment, reject this packing position
                self.log.warning("checked pt that is not in container")
                return True, {}, {}
            if grid_point_index in inside_points:
                if abs(signed_distance_to_surface) < abs(
                    inside_points[grid_point_index]
                ):
                    inside_points[grid_point_index] = signed_distance_to_surface
            else:
                inside_points[grid_point_index] = signed_distance_to_surface
        elif (
            signed_distance_to_surface < grid_distance_values[grid_point_index]
        ):  # point in region of influence
            # need to update the distances of the master grid with new smaller distance
            if grid_point_index in new_dist_points:
                new_dist_points[grid_point_index] = min(
                    signed_distance_to_surface, new_dist_points[grid_point_index]
                )
            else:
                new_dist_points[grid_point_index] = signed_distance_to_surface
        return inside_points, new_dist_points

from panda3d.core import Point3, TransformState
from panda3d.bullet import BulletSphereShape, BulletRigidBodyNode
from math import pi
import numpy

from cellpack.autopack.ingredient.single_sphere import SingleSphereIngr
import cellpack.autopack as autopack

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
        count=0,
        cutoff_boundary=None,
        cutoff_surface=None,
        encapsulating_radius=0,
        excluded_partners_name=None,
        gradient="",
        isAttractor=False,
        jitter_max=(1, 1, 1),
        meshFile=None,
        meshName="",
        meshObject=None,
        meshType="file",
        molarity=0.0,
        name=None,
        jitter_attempts=5,
        nbMol=0,
        offset=None,
        orient_bias_range=[-pi, pi],
        overwrite_distFunc=True,  # overWrite
        packing=None,
        packingPriority=0,
        partners_name=None,
        partners_position=None,
        pdb=None,
        perturb_axis_amplitude=0.1,
        place_type="jitter",
        positions=None,
        positions2=None,
        principal_vector=(1, 0, 0),
        proba_binding=0.5,
        proba_not_binding=0.5,
        properties=None,
        radii=None,
        rejection_threshold=30,
        rotation_axis=[0.0, 0.0, 0.0],
        rotation_range=0,
        source=None,
        sphereFile=None,
        type="MultiSphere",
        useOrientBias=False,
        useRotAxis=True,
        weight=0.2,  # use for affinity ie partner.weight
    ):
        super().__init__(
            color=color,
            coordsystem=coordsystem,
            count=count,
            cutoff_surface=cutoff_surface,
            encapsulating_radius=encapsulating_radius,
            excluded_partners_name=excluded_partners_name,
            gradient=gradient,
            isAttractor=isAttractor,
            jitter_max=jitter_max,
            meshFile=meshFile,
            meshName=meshName,
            meshObject=meshObject,
            meshType=meshType,
            molarity=molarity,
            name=name,
            jitter_attempts=jitter_attempts,
            nbMol=nbMol,
            offset=offset,
            orient_bias_range=orient_bias_range,
            packing=packing,
            packingPriority=packingPriority,
            partners_name=partners_name,
            partners_position=partners_position,
            pdb=pdb,
            perturb_axis_amplitude=perturb_axis_amplitude,
            place_type=place_type,
            positions=positions,
            principal_vector=principal_vector,
            proba_binding=proba_binding,
            proba_not_binding=proba_not_binding,  # chance to actually not bind
            properties=properties,
            radii=radii,
            rotation_axis=rotation_axis,
            rotation_range=rotation_range,
            source=source,
            sphereFile=sphereFile,
            type=type,
            useOrientBias=useOrientBias,
            useRotAxis=useRotAxis,
            weight=weight,
        )
        min_radius = encapsulating_radius
        if radii is not None:
            for level in radii:
                if isinstance(level, dict):
                    if min(level["radii"]) < min_radius:
                        min_radius = min(level["radii"])
                else:
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

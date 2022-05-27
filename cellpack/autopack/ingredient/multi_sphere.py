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
        cutoff_boundary=None,
        cutoff_surface=None,
        encapsulatingRadius=0,
        excluded_partners_name=None,
        gradient="",
        isAttractor=False,
        jitterMax=(1, 1, 1),
        meshFile=None,
        meshType="file",
        meshObject=None,
        molarity=0.0,
        name=None,
        nbJitter=5,
        nbMol=0,
        offset=None,
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
        source=None,
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
            meshType=meshType,
            molarity=molarity,
            name=name,
            nbJitter=nbJitter,
            nbMol=nbMol,
            offset=offset,
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
            source=source,
            sphereFile=sphereFile,
            Type=Type,
        )
        min_radius = encapsulatingRadius
        for level in radii:
            if min(level["radii"]) < min_radius:
                min_radius = min(level["radii"])
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

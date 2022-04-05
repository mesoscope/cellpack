from panda3d.core import Point3, TransformState
from panda3d.bullet import BulletSphereShape, BulletRigidBodyNode
from math import pi

from cellpack.autopack.ingredient.single_sphere import SingleSphereIngr
from .Ingredient import Ingredient
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
        coordsystem='right',
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
        rotAxis=[0.0,0.0,0.0],
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
        for level in radii:
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

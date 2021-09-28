
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
        molarity=0.0,
        radii=None,
        positions=None,
        sphereFile=None,
        packingPriority=0,
        name=None,
        pdb=None,
        color=None,
        nbJitter=5,
        jitterMax=(1, 1, 1),
        perturbAxisAmplitude=0.1,
        Type="MultiSphere",
        principalVector=(1, 0, 0),
        meshFile=None,
        packingMode="random",
        placeType="jitter",
        meshObject=None,
        nbMol=0,
        **kw
    ):
        Ingredient.__init__(
            self,
            molarity=molarity,
            radii=radii,
            positions=positions,  # positions2=None,
            sphereFile=sphereFile,
            packingPriority=packingPriority,
            name=name,
            pdb=pdb,
            color=color,
            nbJitter=nbJitter,
            jitterMax=jitterMax,
            perturbAxisAmplitude=perturbAxisAmplitude,
            principalVector=principalVector,
            meshFile=meshFile,
            packingMode=packingMode,
            placeType=placeType,
            meshObject=meshObject,
            nbMol=nbMol,
            Type=Type,
            **kw
        )

        if name is None:
            name = "%s_%f" % (str(radii), molarity)
        self.name = name
        self.singleSphere = False

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
        meshName="",
        meshObject=None,
        meshType="file",
        molarity=0.0,
        name=None,
        nbJitter=5,
        nbMol=0,
        offset=[0.0, 0.0, 0.0],
        orientBiasRotRangeMax=-pi,
        orientBiasRotRangeMin=-pi,
        overwrite_distFunc=True,  # overWrite
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
        proba_not_binding=0.5,
        properties=None,
        radii=None,
        rejectionThreshold=30,
        rotAxis=[0.0, 0.0, 0.0],
        rotRange=0,
        source=None,
        sphereFile=None,
        Type="MultiSphere",
        useOrientBias=False,
        useRotAxis=True,
        weight=0.2,  # use for affinity ie partner.weight
    ):
        super().__init__(
            color=color,
            coordsystem=coordsystem,
            cutoff_surface=cutoff_surface,
            encapsulatingRadius=encapsulatingRadius,
            excluded_partners_name=excluded_partners_name,
            gradient=gradient,
            isAttractor=isAttractor,
            jitterMax=jitterMax,
            meshFile=meshFile,
            meshName=meshName,
            meshObject=meshObject,
            meshType=meshType,
            molarity=molarity,
            name=name,
            nbJitter=nbJitter,
            nbMol=nbMol,
            offset=offset,
            orientBiasRotRangeMax=orientBiasRotRangeMax,
            orientBiasRotRangeMin=orientBiasRotRangeMin,
            packingMode=packingMode,
            packingPriority=packingPriority,
            partners_name=partners_name,
            partners_position=partners_position,
            pdb=pdb,
            perturbAxisAmplitude=perturbAxisAmplitude,
            placeType=placeType,
            positions=positions,
            principalVector=principalVector,
            proba_binding=proba_binding,
            proba_not_binding=proba_not_binding,  # chance to actually not bind
            properties=properties,
            radii=radii,
            rotAxis=rotAxis,
            rotRange=rotRange,
            source=source,
            sphereFile=sphereFile,
            Type=Type,
            useOrientBias=useOrientBias,
            useRotAxis=useRotAxis,
            weight=weight,
        )
        min_radius = encapsulatingRadius
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

    def pack_at_grid_pt_location(
        self,
        env,
        jtrans,
        rotMatj,
        dpad,
        grid_point_distances
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


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
        Type="SingleSphere",
        color=None,
        coordsystem="right",
        cutoff_boundary=None,
        cutoff_surface=None,
        distExpression=None,
        distFunction=None,
        encapsulatingRadius=0,
        excluded_partners_name=None,
        force_random=False,  # avoid any binding
        gradient="",
        isAttractor=False,
        jitterMax=(1, 1, 1),
        meshType="file",
        molarity=0.0,
        name=None,
        nbJitter=5,
        nbMol=0,
        offset=None,
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
        positions=[[[0, 0, 0]]],
        positions2=None,
        principalVector=(1, 0, 0),
        proba_binding=0.5,
        proba_not_binding=0.5,  # chance to actually not bind
        properties=None,
        radii=None,
        radius=None,
        rejectionThreshold=30,
        resolution_dictionary=None,
        position=None,
        sphereFile=None,
        meshFile=None,
        meshName=None,
        meshObject=None,
        rotAxis=[0.0, 0.0, 0.0],
        rotRange=0,
        source=None,
        useOrientBias=False,
        useRotAxis=True,
        weight=0.2,  # use for affinity ie partner.weight
    ):
        # called through inheritance
        if radii is None and radius is not None:
            radii = [[radius]]
        if positions is None and position is not None:
            positions = [[position]]
        super().__init__(
            Type=Type,
            color=color,
            coordsystem=coordsystem,
            cutoff_boundary=cutoff_boundary,
            cutoff_surface=cutoff_surface,
            distExpression=distExpression,
            distFunction=distFunction,
            excluded_partners_name=excluded_partners_name,
            force_random=force_random,
            gradient=gradient,
            isAttractor=isAttractor,
            jitterMax=jitterMax,
            meshName=meshName,
            meshType=meshType,
            meshObject=meshObject,
            molarity=molarity,
            name=name,
            nbJitter=nbJitter,
            nbMol=nbMol,
            overwrite_distFunc=overwrite_distFunc,
            packingMode=packingMode,
            packingPriority=packingPriority,
            partners_name=partners_name,
            partners_position=partners_position,
            pdb=pdb,
            sphereFile=sphereFile,
            perturbAxisAmplitude=perturbAxisAmplitude,
            meshFile=meshFile,
            placeType=placeType,
            positions=positions,  # positions2=None,
            principalVector=principalVector,
            proba_binding=proba_binding,
            proba_not_binding=proba_not_binding,
            properties=properties,
            radii=radii,
            rotAxis=rotAxis,
            rotRange=rotRange,
            useRotAxis=useRotAxis,
            weight=weight,
        )
        self.modelType = "Spheres"
        if name is None:
            name = "%5.2f_%f" % (radius, molarity)
        self.name = name
        self.singleSphere = True
        self.mesh = None
        # min and max radius for a single sphere should be the same
        self.encapsulatingRadius = encapsulatingRadius or radius

    def collides_with_compartment(
        self,
        jtrans,
        rotMat,
        level,
        gridPointsCoords,
        env,
    ):
        """
        Check spheres for collision
        TODO improve the testwhen grid stepSize is larger that size of the ingredient
        """
        centers = self.positions[level]
        radii = (self.radii[level],)
        centT = self.transformPoints(jtrans, rotMat, centers)  # this should be jtrans
        for radc, posc in zip(radii, centT):
            ptsInSphere = env.grid.getPointsInSphere(posc, radc[0])  # indices
            compIdsSphere = numpy.take(env.grid.compartment_ids, ptsInSphere, 0)
            if self.compNum <= 0:
                wrongPt = [cid for cid in compIdsSphere if cid != self.compNum]
                if len(wrongPt):
                    print("OK false compartment", len(wrongPt))
                    return True
        return False

    def get_signed_distance(
        self,
        packing_location,
        grid_point_location,
        rotation_matrix=None,
    ):
        radius = self.radii[0][0]
        distance_to_packing_location = numpy.linalg.norm(
            packing_location - grid_point_location
        )
        signed_distance_to_surface = distance_to_packing_location - radius
        return signed_distance_to_surface

    def get_new_distance_values(
        self, jtrans, rotMatj, gridPointsCoords, distance, dpad, level=0
    ):
        self.centT = centT = self.transformPoints(
            jtrans, rotMatj, self.positions[level]
        )
        centT = self.centT  # self.transformPoints(jtrans, rotMatj, self.positions[-1])
        insidePoints = {}
        newDistPoints = {}
        for radc, posc in zip(self.radii[-1], centT):
            rad = radc + dpad
            ptsInSphere = self.env.grid.getPointsInSphere(posc, rad)
            delta = numpy.take(gridPointsCoords, ptsInSphere, 0) - posc
            delta *= delta
            distA = numpy.sqrt(delta.sum(1))
            for pti in range(len(ptsInSphere)):
                pt = ptsInSphere[pti]
                dist = distA[pti]
                d = dist - radc
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
        shape = BulletSphereShape(self.encapsulatingRadius)
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
        M.setSphereTotal(1.0, self.encapsulatingRadius)
        body.setMass(M)
        body.setPosition(Vec3(jtrans[0], jtrans[1], jtrans[2]))
        body.setRotation(pMat)
        # the geometry for the collision ?
        geom = OdeSphereGeom(self.ode_space, self.encapsulatingRadius)
        geom.setBody(body)
        return geom

    def initialize_mesh(self, mesh_store):
        if self.mesh is None:
            self.mesh = mesh_store.create_sphere(
                self.name + "_basic", 5, radius=self.radii[0][0]
            )

            self.getData()
        # should do that for all ingredient type
        # if self.representation is None and not hasattr(
        #     self.mesh, "getFaces"
        # ):  # this is not working with dejavu
        #     # and should go in the graphics.
        #     self.representation = autopack.helper.Icosahedron(
        #         self.name + "_rep", radius=self.radii[0][0]
        #     )[0]

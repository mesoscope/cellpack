import numpy
from panda3d.core import Point3, TransformState, Vec3
from panda3d.bullet import BulletSphereShape, BulletRigidBodyNode
from panda3d.ode import OdeBody, OdeMass, OdeSphereGeom

from .Ingredient import Ingredient
import cellpack.autopack as autopack

helper = autopack.helper


class SingleSphereIngr(Ingredient):
    """
    This Ingredient is represented by a single sphere
    and either a single radius, or a list of radii and offset vectors
    for each sphere representing the ingredient
    """

    def __init__(
        self,
        molarity=0.0,
        radius=None,
        position=None,
        sphereFile=None,
        packingPriority=0,
        name=None,
        pdb=None,
        color=None,
        nbJitter=5,
        jitterMax=(1, 1, 1),
        perturbAxisAmplitude=0.1,
        principalVector=(1, 0, 0),
        meshFile=None,
        packingMode="random",
        placeType="jitter",
        Type="SingleSphere",
        meshObject=None,
        nbMol=0,
        **kw
    ):

        Ingredient.__init__(
            self,
            molarity=molarity,
            radii=[[radius]],
            positions=[[position]],  # positions2=None,
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
        self.modelType = "Spheres"

        if name is None:
            name = "%5.2f_%f" % (radius, molarity)
        self.name = name
        self.singleSphere = True
        # min and max radius for a single sphere should be the same
        self.minRadius = radius
        self.encapsulatingRadius = radius
        # make a sphere ?->rapid ?
        if self.mesh is None and autopack.helper is not None:
            if not autopack.helper.nogui:
                #            if not autopack.helper.nogui :
                # build a cylinder and make it length uLength, radius radii[0]
                # this mesh is used bu RAPID for collision
                p = autopack.helper.getObject("autopackHider")
                if p is None:
                    p = autopack.helper.newEmpty("autopackHider")
                    if autopack.helper.host.find("blender") == -1:
                        autopack.helper.toggleDisplay(p, False)
                self.mesh = autopack.helper.Sphere(
                    self.name + "_basic",
                    radius=self.radii[0][0],
                    color=self.color,
                    parent=p,
                    res=24,
                )[0]
            else:
                self.mesh = autopack.helper.unitSphere(
                    self.name + "_basic", 5, radius=self.radii[0][0]
                )[0]
                self.getData()
        # should do that for all ingredient type
        if self.representation is None and not hasattr(
            self.mesh, "getFaces"
        ):  # this is not working with dejavu
            # and should go in the graphics.
            if not autopack.helper.nogui:
                self.representation = autopack.helper.Sphere(
                    self.name + "_rep",
                    radius=self.radii[0][0],
                    color=self.color,
                    parent=self.mesh,
                    res=24,
                )[0]
            else:
                self.representation = autopack.helper.Icosahedron(
                    self.name + "_rep", radius=self.radii[0][0]
                )[0]

    def collides_with_compartment(
        self,
        jtrans,
        rotMat,
        level,
        gridPointsCoords,
        histoVol,
    ):
        """
        Check spheres for collision
        TODO improve the testwhen grid stepSize is larger that size of the ingredient
        """
        centers = self.positions[level]
        radii = (self.radii[level],)
        centT = self.transformPoints(jtrans, rotMat, centers)  # this should be jtrans
        for radc, posc in zip(radii, centT):
            ptsInSphere = histoVol.grid.getPointsInSphere(posc, radc[0])  # indices
            compIdsSphere = numpy.take(histoVol.grid.gridPtId, ptsInSphere, 0)
            if self.compNum <= 0:
                wrongPt = [cid for cid in compIdsSphere if cid != self.compNum]
                if len(wrongPt):
                    print("OK false compartment", len(wrongPt))
                    return True
        return False

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

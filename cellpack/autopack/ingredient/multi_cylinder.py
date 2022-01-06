import numpy
import math
from math import sqrt
import panda3d
from panda3d.core import Mat4, Point3, TransformState
from panda3d.bullet import BulletCylinderShape, BulletRigidBodyNode

from .Ingredient import Ingredient
import cellpack.autopack as autopack

helper = autopack.helper


# TODO : move somewhere in a more apropriate place ?
def pandaMatrice(mat):
    if panda3d is None:
        return
    mat = mat.transpose().reshape((16,))
    #        print mat,len(mat),mat.shape
    pMat = Mat4(
        mat[0],
        mat[1],
        mat[2],
        mat[3],
        mat[4],
        mat[5],
        mat[6],
        mat[7],
        mat[8],
        mat[9],
        mat[10],
        mat[11],
        mat[12],
        mat[13],
        mat[14],
        mat[15],
    )
    return pMat


class MultiCylindersIngr(Ingredient):
    """
    This Ingredient is represented by a collection of cylinder specified by
    radii, positions and positions2.
    The principal Vector will be used to align the ingredient
    """

    def __init__(
        self,
        molarity=0.0,
        radii=None,
        positions=None,
        positions2=None,
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
        Type="MultiCylinder",
        meshObject=None,
        nbMol=0,
        **kw
    ):

        Ingredient.__init__(
            self,
            molarity=molarity,
            radii=radii,
            positions=positions,
            positions2=positions2,
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
        self.modelType = "Cylinders"
        self.collisionLevel = 0
        self.minRadius = self.radii[0][0]
        #        self.encapsulatingRadius = radii[0][0]  #Graham worry: 9/8/11 This is incorrect... shoudl be max(radii[0]) or radii[0][1]
        #        self.encapsulatingRadius = radii[0][0]#nope should be  half length ?
        self.length = 1.0
        self.useLength = False
        if "useLength" in kw:
            self.useLength = kw["useLength"]
        if self.positions2 is not None and self.positions is not None:
            # shoulde the overall length of the object from bottom to top
            bb = self.getBigBB()
            d = numpy.array(bb[1]) - numpy.array(bb[0])
            s = numpy.sum(d * d)
            self.length = math.sqrt(s)  # diagonal
        # if self.mesh is None and autopack.helper is not None :
        #            #build a cylinder and make it length uLength, radius radii[0]
        #            self.mesh = autopack.helper.Cylinder(self.name+"_basic",radius=self.radii[0][0],
        #                                       length=self.uLength,parent="autopackHider")[0]
        if self.mesh is None and autopack.helper is not None:
            p = None
            if not autopack.helper.nogui:
                # build a cylinder and make it length uLength, radius radii[0]
                # this mesh is used bu RAPID for collision
                p = autopack.helper.getObject("autopackHider")
                if p is None:
                    p = autopack.helper.newEmpty("autopackHider")
                    if autopack.helper.host.find("blender") == -1:
                        autopack.helper.toggleDisplay(p, False)
                        #                self.mesh = autopack.helper.Cylinder(self.name+"_basic",
                        #                                radius=self.radii[0][0]*1.24, length=self.uLength,
                        #                                res= 5, parent="autopackHider",axis="+X")[0]
            length = 1
            if self.positions2 is not None and self.positions is not None:
                d = numpy.array(self.positions2[0][0]) - numpy.array(
                    self.positions[0][0]
                )
                s = numpy.sum(d * d)
                length = math.sqrt(s)  # diagonal
            self.mesh = autopack.helper.Cylinder(
                self.name + "_basic",
                radius=self.radii[0][0] * 1.24,
                length=length,
                res=5,
                parent="autopackHider",
                axis=self.principalVector,
            )[0]
        # self.mesh = autopack.helper.oneCylinder(self.name+"_basic",
        #                                self.positions[0][0],self.positions2[0][0],
        #                                radius=self.radii[0][0]*1.24,
        #                                parent = p,color=self.color)
        #            self.getData()

        self.KWDS["useLength"] = {}

    def getBigBB(self):
        # one level for cylinder
        bbs = []
        for radc, p1, p2 in zip(self.radii[0], self.positions[0], self.positions2[0]):
            bb = self.correctBB(p1, p2, radc)
            bbs.append(bb)
        # get min and max from all bbs
        maxBB = [0, 0, 0]
        minBB = [9999, 9999, 9999]
        for bb in bbs:
            for i in range(3):
                if bb[0][i] < minBB[i]:
                    minBB[i] = bb[0][i]
                if bb[1][i] > maxBB[i]:
                    maxBB[i] = bb[1][i]
                if bb[1][i] < minBB[i]:
                    minBB[i] = bb[1][i]
                if bb[0][i] > maxBB[i]:
                    maxBB[i] = bb[0][i]
        bb = [minBB, maxBB]
        return bb

    def collides_with_compartment(
        self,
        jtrans,
        rotMat,
        level,
        gridPointsCoords,
        histoVol,
    ):
        """
        Check cylinders for collision
        """
        centers1 = (self.positions[level],)
        centers2 = (self.positions2[level],)
        radii = (self.radii[level],)
        cent1T = self.transformPoints(jtrans, rotMat, centers1)
        cent2T = self.transformPoints(jtrans, rotMat, centers2)

        cylNum = 0
        for radc, p1, p2 in zip(radii, cent1T, cent2T):
            x1, y1, z1 = p1
            x2, y2, z2 = p2
            vx, vy, vz = vect = (x2 - x1, y2 - y1, z2 - z1)
            lengthsq = vx * vx + vy * vy + vz * vz
            length = math.sqrt(lengthsq)
            cx, cy, cz = posc = x1 + vx * 0.5, y1 + vy * 0.5, z1 + vz * 0.5
            radt = length + radc

            bb = self.correctBB(p1, p2, radc)
            pointsInCube = histoVol.grid.getPointsInCube(bb, posc, radt, info=True)

            # check for collisions with cylinder
            pd = numpy.take(gridPointsCoords, pointsInCube, 0) - p1
            dotp = numpy.dot(pd, vect)
            #            rad2 = radc*radc
            #            dsq = numpy.sum(pd*pd, 1) - dotp*dotp/lengthsq
            ptsWithinCaps = numpy.nonzero(
                numpy.logical_and(
                    numpy.greater_equal(dotp, 0.0), numpy.less_equal(dotp, lengthsq)
                )
            )

            ptsInSphereId = numpy.take(pointsInCube, ptsWithinCaps[0], 0)
            compIdsSphere = numpy.take(histoVol.grid.gridPtId, ptsInSphereId, 0)
            if self.compNum <= 0:
                wrongPt = [cid for cid in compIdsSphere if cid != self.compNum]
                if len(wrongPt):
                    #                        print wrongPt
                    return True
            cylNum += 1
        return False

    def collision_jitter(
        self,
        jtrans,
        rotMat,
        level,
        gridPointsCoords,
        distance,
        histoVol,
        dpad,
    ):
        """
        Check cylinders for collision
        """
        centers1 = self.positions[level]
        centers2 = self.positions2[level]
        radii = self.radii[level]
        return self.checkCylCollisions(
            centers1,
            centers2,
            radii,
            jtrans,
            rotMat,
            gridPointsCoords,
            distance,
            histoVol,
            dpad,
        )

    def add_rb_node(self, worldNP):
        inodenp = worldNP.attachNewNode(BulletRigidBodyNode(self.name))
        inodenp.node().setMass(1.0)
        centT1 = self.positions[
            0
        ]  # ingr.transformPoints(jtrans, rotMat, ingr.positions[0])
        centT2 = self.positions2[
            0
        ]  # ingr.transformPoints(jtrans, rotMat, ingr.positions2[0])
        for radc, p1, p2 in zip(self.radii[0], centT1, centT2):
            length, mat = autopack.helper.getTubePropertiesMatrix(p1, p2)
            pMat = pandaMatrice(mat)
            #            d = numpy.array(p1) - numpy.array(p2)
            #            s = numpy.sum(d*d)
            Point3(
                self.principalVector[0],
                self.principalVector[1],
                self.principalVector[2],
            )
            shape = BulletCylinderShape(
                radc, length, 1
            )  # math.sqrt(s), 1)# { XUp = 0, YUp = 1, ZUp = 2 } or LVector3f const half_extents
            inodenp.node().addShape(shape, TransformState.makeMat(pMat))  #
        return inodenp

    def checkCylCollisions(
        self,
        centers1,
        centers2,
        radii,
        jtrans,
        rotMat,
        gridPointsCoords,
        distance,
        histoVol,
        dpad,
    ):
        """
        Check cylinders for collision
        """
        cent1T = self.transformPoints(jtrans, rotMat, centers1)
        cent2T = self.transformPoints(jtrans, rotMat, centers2)

        insidePoints = {}
        newDistPoints = {}

        cylNum = 0
        for radc, p1, p2 in zip(radii, cent1T, cent2T):
            if histoVol.runTimeDisplay > 1:
                name = "cyl"
                cyl = self.vi.getObject("cyl")
                if cyl is None:
                    cyl = self.vi.oneCylinder(
                        name, p1, p2, color=(1.0, 1.0, 1.0), radius=radc
                    )
                # self.vi.updateTubeMesh(cyl,cradius=radc)
                else:
                    self.vi.updateOneCylinder(cyl, p1, p2, radius=radc)
                self.vi.changeObjColorMat(cyl, (1.0, 1.0, 1.0))
                name = "sph1"
                sph1 = self.vi.getObject("sph1")
                if sph1 is None:
                    sph1 = self.vi.Sphere(name, radius=radc * 2.0)[0]
                self.vi.setTranslation(sph1, p1)
                name = "sph2"
                sph2 = self.vi.getObject("sph2")
                if sph2 is None:
                    sph2 = self.vi.Sphere(name, radius=radc * 2.0)[0]
                self.vi.setTranslation(sph2, p2)

                self.vi.update()
            x1, y1, z1 = p1
            x2, y2, z2 = p2
            vx, vy, vz = vect = (x2 - x1, y2 - y1, z2 - z1)
            lengthsq = vx * vx + vy * vy + vz * vz
            length = sqrt(lengthsq)
            cx, cy, cz = posc = x1 + vx * 0.5, y1 + vy * 0.5, z1 + vz * 0.5
            radt = length + radc

            bb = self.correctBB(p1, p2, radc)
            #            bb = self.correctBB(posc,posc,radt)
            if histoVol.runTimeDisplay > 1:
                box = self.vi.getObject("collBox")
                if box is None:
                    box = self.vi.Box("collBox", cornerPoints=bb, visible=1)
                else:
                    #                    self.vi.toggleDisplay(box,True)
                    self.vi.updateBox(box, cornerPoints=bb)
                    self.vi.update()
                    #                 sleep(1.0)
            pointsInCube = histoVol.grid.getPointsInCube(bb, posc, radt, info=True)

            # check for collisions with cylinder
            pd = numpy.take(gridPointsCoords, pointsInCube, 0) - p1
            dotp = numpy.dot(pd, vect)
            rad2 = radc * radc
            dsq = numpy.sum(pd * pd, 1) - dotp * dotp / lengthsq

            ptsWithinCaps = numpy.nonzero(
                numpy.logical_and(
                    numpy.greater_equal(dotp, 0.0), numpy.less_equal(dotp, lengthsq)
                )
            )
            if not len(ptsWithinCaps[0]):
                print("no point inside the geom?")
                return False, insidePoints, newDistPoints
            if self.compareCompartment:
                ptsInSphereId = numpy.take(pointsInCube, ptsWithinCaps[0], 0)
                compIdsSphere = numpy.take(histoVol.grid.gridPtId, ptsInSphereId, 0)
                #                print "compId",compIdsSphere
                if self.compNum <= 0:
                    wrongPt = [cid for cid in compIdsSphere if cid != self.compNum]
                    if len(wrongPt):
                        return True, insidePoints, newDistPoints
            # for pti in ptsWithinCaps[0]:
            #     pt = pointsInCube[pti]
            #     dist = dsq[pti]
            #     if dist > rad2:
            #         continue  # outside radius
            #     elif distance[pt] < -0.0001:  # or trigger: # pt is inside cylinder
            #         # changeObjColorMat
            #         if histoVol.runTimeDisplay > 1:
            #             self.vi.changeObjColorMat(cyl, (1., 0., 0.))
            #             self.vi.update()
            #         #                        sleep(1.0)
            #         # reject
            #         return True
            d2toP1 = numpy.sum(pd * pd, 1)
            dsq = d2toP1 - dotp * dotp / lengthsq
            pd2 = numpy.take(gridPointsCoords, pointsInCube, 0) - p2
            d2toP2 = numpy.sum(pd2 * pd2, 1)

            for pti, pt in enumerate(pointsInCube):
                dist = dsq[pti]
                if dist > rad2:
                    continue  # outside radius
                elif distance[pt] < -0.0001:
                    return True, insidePoints, newDistPoints
                if pt in insidePoints:
                    continue
                if dotp[pti] < 0.0:  # outside 1st cap
                    d = sqrt(d2toP1[pti])
                    if d < distance[pt]:  # point in region of influence
                        if pt in newDistPoints:
                            if d < newDistPoints[pt]:
                                newDistPoints[pt] = d
                        else:
                            newDistPoints[pt] = d
                elif dotp[pti] > lengthsq:
                    d = sqrt(d2toP2[pti])
                    if d < distance[pt]:  # point in region of influence
                        if pt in newDistPoints:
                            if d < newDistPoints[pt]:
                                newDistPoints[pt] = d
                        else:
                            newDistPoints[pt] = d
                else:
                    d = sqrt(dsq[pti]) - radc
                    if d < 0.0:  # point is inside dropped sphere
                        if pt in insidePoints:
                            if d < insidePoints[pt]:
                                insidePoints[pt] = d
                        else:
                            insidePoints[pt] = d
            cylNum += 1
        return False, insidePoints, newDistPoints

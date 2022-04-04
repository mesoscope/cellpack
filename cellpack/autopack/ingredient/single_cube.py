from math import sqrt, pi
import numpy
from panda3d.core import Point3, TransformState, Vec3
from panda3d.bullet import BulletBoxShape, BulletRigidBodyNode

from .Ingredient import Ingredient
from .utils import ApplyMatrix
import cellpack.autopack as autopack

helper = autopack.helper


class SingleCubeIngr(Ingredient):
    """
    This Ingredient is represented by a single cube
    """

    def __init__(
        self,
        Type="SingleCube",
        color=None,
        coordsystem='right',
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
        # meshFile=None,
        # meshName=None,
        # meshObject=None,
        # meshType='file',
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
        positions2=[[[0, 0, 0]]],
        positions=[[[0, 0, 0]]],
        principalVector=(1, 0, 0),
        proba_binding=0.5,
        proba_not_binding=0.5,  # chance to actually not bind
        properties=None,
        radii=None,
        rejectionThreshold=30,
        resolution_dictionary=None,
        rotAxis=None,
        rotRange=6.2831,
        source=None,
        # sphereFile=None,
        useOrientBias=False,
        useRotAxis=False,
        weight=0.2,  # use for affinity ie partner.weight
    ):
        super().__init__(
            Type=Type,
            color=color,
            cutoff_boundary=cutoff_boundary,
            cutoff_surface=cutoff_surface,
            distExpression=distExpression,
            distFunction=distFunction,
            excluded_partners_name=excluded_partners_name,
            force_random=force_random,
            gradient=gradient,
            isAttractor=isAttractor,
            jitterMax=jitterMax,
            # meshFile=meshFile,
            # meshObject=meshObject,
            molarity=molarity,
            name=name,
            nbJitter=nbJitter,
            nbMol=nbMol,
            overwrite_distFunc=overwrite_distFunc,
            overwrite_nbMol_value=overwrite_nbMol_value,
            packingMode=packingMode,
            packingPriority=packingPriority,
            partners_name=partners_name,
            partners_position=partners_position,
            pdb=pdb,
            perturbAxisAmplitude=perturbAxisAmplitude,
            placeType=placeType,
            positions2=positions2,
            positions=positions,
            principalVector=principalVector,
            proba_binding=proba_binding,
            proba_not_binding=proba_not_binding,
            properties=properties,
            radii=radii,
            rotRange=rotRange,
            # sphereFile=sphereFile,
            weight=weight,
        )
        print("MAKING CUBE", positions2)
        if name is None:
            name = "%5.2f_%f" % (radii[0][0], molarity)
        self.name = name
        self.singleSphere = False
        self.modelType = "Cube"
        self.collisionLevel = 0
        radii = numpy.array(radii)
        
        self.minRadius = min(
             radii[0] / 2.0
         )  # should have three radii sizex,sizey,sizez
        self.maxRadius = self.encapsulatingRadius = numpy.linalg.norm(radii[0]/2) # calculate encapsulating radius based on side length
        self.bb = [-radii[0] / 2.0, radii[0] / 2.0]
        
        self.positions = positions # bottom left corner of cuboid
        self.positions2 = positions2 # top right corner of cuboid
        positions_ar = numpy.array(self.positions[0][0])
        positions2_ar = numpy.array(self.positions2[0][0])
        
        self.center = positions_ar+(positions2_ar-positions_ar)/2 #location of center based on corner points
        
        self.radii = radii

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
        Check cube for collision
        centers1 and centers2 should be the cornerPoints, so we can do parrallelpiped
        can also use the center plus size (radii), or the position/position2
        """
        centers1 = self.positions[0]
        centers2 = self.positions2[0]
        cent1T = self.transformPoints(jtrans, rotMat, centers1)[0]  # bb1
        cent2T = self.transformPoints(jtrans, rotMat, centers2)[0]  # bb2
        center = self.transformPoints(
            jtrans,
            rotMat,
            [self.center],
        )[0]

        insidePoints = {}
        newDistPoints = {}

        x1, y1, z1 = cent1T #coordinates of 1st corner point in world space
        x2, y2, z2 = cent2T #coordinates of 2nd corner point in world space
        vx, vy, vz = (x2 - x1, y2 - y1, z2 - z1) #vector connecting corner points
        lengthsq = vx * vx + vy * vy + vz * vz #length^2 of diagonal
        length = sqrt(lengthsq) # length of diagonal
        posc = center  # x1+vx*.5, y1+vy*.5, z1+vz*.5  # position of center in world space
        radt = length / 2.0 + self.encapsulatingRadius + dpad 
        x, y, z = posc
        bb = ([x - radt, y - radt, z - radt], [x + radt, y + radt, z + radt]) #recalculated bounding box in world space

        if histoVol.runTimeDisplay:  # > 1:
            box = self.vi.getObject("collBox")
            if box is None:
                box = self.vi.Box(
                    "collBox", cornerPoints=bb, visible=1
                )  # cornerPoints=bb,visible=1)
            else:
                self.vi.updateBox(box, cornerPoints=bb)
            self.vi.update()

        pointsInCube = histoVol.grid.getPointsInCube(bb, posc, radt)
        pd = numpy.take(gridPointsCoords, pointsInCube, 0) - center  # center them ?
        delta = pd.copy()
        delta *= delta
        distA = numpy.sqrt(delta.sum(1))

        # m = numpy.matrix(numpy.array(rotMat).reshape(4, 4))  #
        # mat = m.I
        # need to apply inverse mat to pd
        # rpd = ApplyMatrix(pd, mat)
        # need to check if these point are inside the cube using the dimension of the cube
        ptinside_mask = [histoVol.grid.test_points_in_bb(bb, gi) for gi in pd]
        print(len(ptinside_mask))
        ptinside = numpy.nonzero(ptinside_mask)[0]
        # res = numpy.less_equal(numpy.fabs(rpd), numpy.array(radii[0]) / 2.)
        # if len(res):
        #     c = numpy.average(res, 1)  # .astype(int)
        #     d = numpy.equal(c, 1.)
        #     ptinside = numpy.nonzero(d)[0]
        if not len(ptinside):
            print("something is wrong no grid points inside cube", len(pointsInCube))
            return True, insidePoints, newDistPoints
        if self.compareCompartment:
            ptinsideId = numpy.take(pointsInCube, ptinside, 0)
            compIdsSphere = numpy.take(histoVol.grid.gridPtId, ptinsideId, 0)
            if self.compNum <= 0:
                wrongPt = [cid for cid in compIdsSphere if cid != self.compNum]
                if len(wrongPt):
                    return True, insidePoints, newDistPoints
        for pti in range(len(pointsInCube)):
            # ptinsideCube:#inside point but have been already computed during the check collision...?
            pt = pointsInCube[pti]
            if pti in ptinside:
                if distance[pt] < -0.0001:  # or trigger : # pt is inside cylinder
                    return True, insidePoints, newDistPoints
            if pt in insidePoints:
                continue
            dist = distA[pti]
            d = dist - self.encapsulatingRadius
            # should be distance to the cube, but will use approximation
            if pti in ptinside:
                if pt in insidePoints:
                    if d < insidePoints[pt]:
                        insidePoints[pt] = d
                else:
                    insidePoints[pt] = d
            elif d < distance[pt]:  # point in region of influence
                if pt in newDistPoints:
                    if d < newDistPoints[pt]:
                        newDistPoints[pt] = d
                else:
                    newDistPoints[pt] = d
        return False, insidePoints, newDistPoints

    def collides_with_compartment(
        self,
        jtrans,
        rotMat,
        gridPointsCoords,
        histoVol,
    ):
        """
        Check cube for collision
        centers1 and centers2 should be the cornerPoints ?
        can also use the center plus size (radii), or the position/position2
        """
        centers1 = self.positions[0]
        centers2 = self.positions2[0]
        radii = self.radii
        cent1T = self.transformPoints(jtrans, rotMat, centers1)[0]  # bb1
        cent2T = self.transformPoints(jtrans, rotMat, centers2)[0]  # bb2
        center = self.transformPoints(jtrans, rotMat, [self.center])[0]

        #        for radc, p1, p2 in zip(radii, cent1T, cent2T):
        x1, y1, z1 = cent1T
        x2, y2, z2 = cent2T
        vx, vy, vz = (x2 - x1, y2 - y1, z2 - z1)
        lengthsq = vx * vx + vy * vy + vz * vz
        length = sqrt(lengthsq)
        cx, cy, cz = posc = center  # x1+vx*.5, y1+vy*.5, z1+vz*.5
        radt = length / 2.0 + self.encapsulatingRadius
        x, y, z = posc
        bb = ([x - radt, y - radt, z - radt], [x + radt, y + radt, z + radt])

        pointsInCube = histoVol.grid.getPointsInCube(bb, posc, radt)

        pd = numpy.take(gridPointsCoords, pointsInCube, 0) - center
        m = numpy.matrix(numpy.array(rotMat).reshape(4, 4))  #
        mat = m.I
        rpd = ApplyMatrix(pd, mat)
        res = numpy.less_equal(numpy.fabs(rpd), numpy.array(radii[0]) / 2.0)
        c = numpy.average(res, 1)  # .astype(int)
        d = numpy.equal(c, 1.0)
        ptinside = numpy.nonzero(d)[0]
        ptinsideId = numpy.take(pointsInCube, ptinside, 0)
        compIdsSphere = numpy.take(histoVol.grid.gridPtId, ptinsideId, 0)
        #        print "compId",compIdsSphere
        if self.compNum <= 0:
            wrongPt = [cid for cid in compIdsSphere if cid != self.compNum]
            if len(wrongPt):
                #                print wrongPt
                return True
        return False

    def get_new_distance_values(
        self, jtrans, rotMat, gridPointsCoords, distance, dpad, level=0
    ):
        radii = self.radii
        insidePoints = {}
        newDistPoints = {}
        cent1T = self.transformPoints(jtrans, rotMat, self.positions[0])[0]  # bb1
        cent2T = self.transformPoints(jtrans, rotMat, self.positions2[0])[0]  # bb2
        center = self.transformPoints(
            jtrans,
            rotMat,
            [self.center],
        )[0]
        #        cylNum = 0
        #        for radc, p1, p2 in zip(radii, cent1T, cent2T):
        x1, y1, z1 = cent1T
        x2, y2, z2 = cent2T
        vx, vy, vz = (x2 - x1, y2 - y1, z2 - z1)
        lengthsq = vx * vx + vy * vy + vz * vz
        length = sqrt(lengthsq)
        cx, cy, cz = posc = center  # x1+vx*.5, y1+vy*.5, z1+vz*.5
        radt = length / 2.0 + self.encapsulatingRadius

        bb = [cent2T, cent1T]  # self.correctBB(p1,p2,radc)
        x, y, z = posc
        bb = ([x - radt, y - radt, z - radt], [x + radt, y + radt, z + radt])
        #        print ("pointsInCube",bb,posc,radt)
        pointsInGridCube = self.env.grid.getPointsInCube(bb, posc, radt)

        # check for collisions with cylinder
        pd = numpy.take(gridPointsCoords, pointsInGridCube, 0) - center

        delta = pd.copy()
        delta *= delta
        distA = numpy.sqrt(delta.sum(1))

        m = numpy.matrix(numpy.array(rotMat).reshape(4, 4))  #
        mat = m.I
        # need to apply inverse mat to pd
        rpd = ApplyMatrix(pd, mat)
        # need to check if these point are inside the cube using the dimension of the cube
        # numpy.fabs
        res = numpy.less_equal(numpy.fabs(rpd), numpy.array(radii[0]) / 2.0)
        if len(res):
            c = numpy.average(res, 1)  # .astype(int)
            d = numpy.equal(c, 1.0)
            ptinsideCube = numpy.nonzero(d)[0]
        else:
            ptinsideCube = []
        for pti in range(len(pointsInGridCube)):
            # ptinsideCube:#inside point but have been already computed during the check collision...?
            pt = pointsInGridCube[pti]
            if pt in insidePoints:
                continue
            dist = distA[pti]
            d = dist - self.encapsulatingRadius
            # should be distance to the cube, but will use approximation
            if pti in ptinsideCube:
                # dist < radt:  # point is inside dropped sphere
                if pt in insidePoints:
                    if d < insidePoints[pt]:
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
        halfextents = self.bb[1]
        shape = BulletBoxShape(
            Vec3(halfextents[0], halfextents[1], halfextents[2])
        )  # halfExtents
        inodenp = worldNP.attachNewNode(BulletRigidBodyNode(self.name))
        inodenp.node().setMass(1.0)
        #        inodenp.node().addShape(shape)
        inodenp.node().addShape(
            shape, TransformState.makePos(Point3(0, 0, 0))
        )  # , pMat)#TransformState.makePos(Point3(jtrans[0],jtrans[1],jtrans[2])))#rotation ?
        #        spherenp.setPos(-2, 0, 4)
        return inodenp

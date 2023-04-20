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
    This Ingredient is represented by a single cube. Required attribute:
    bounds, in the form of [lower bounds, upper bounds]. Each an x, y, z point.
    """

    def __init__(
        self,
        bounds,
        available_regions=None,
        type="single_cube",
        color=None,
        count=0,
        cutoff_boundary=None,
        cutoff_surface=0.0,
        distance_expression=None,
        distance_function=None,
        force_random=False,  # avoid any binding
        gradient=None,
        is_attractor=False,
        max_jitter=(1, 1, 1),
        molarity=0.0,
        name=None,
        jitter_attempts=5,
        offset=None,
        orient_bias_range=[-pi, pi],
        overwrite_distance_function=True,  # overWrite
        priority=0,
        partners=None,
        perturb_axis_amplitude=0.1,
        place_method="jitter",
        principal_vector=(1, 0, 0),
        representations=None,
        rejection_threshold=30,
        resolution_dictionary=None,
        rotation_axis=[0.0, 0.0, 0.0],
        rotation_range=0,
        use_orient_bias=False,
        use_rotation_axis=True,
        weight=0.2,  # use for affinity ie partner.weight
    ):
        super().__init__(
            type=type,
            color=color,
            count=count,
            cutoff_boundary=cutoff_boundary,
            cutoff_surface=cutoff_surface,
            distance_expression=distance_expression,
            distance_function=distance_function,
            force_random=force_random,
            gradient=gradient,
            is_attractor=is_attractor,
            max_jitter=max_jitter,
            molarity=molarity,
            name=name,
            jitter_attempts=jitter_attempts,
            overwrite_distance_function=overwrite_distance_function,
            priority=priority,
            partners=partners,
            perturb_axis_amplitude=perturb_axis_amplitude,
            place_method=place_method,
            principal_vector=principal_vector,
            representations=representations,
            rotation_axis=rotation_axis,
            rotation_range=rotation_range,
            use_rotation_axis=use_rotation_axis,
            weight=weight,
        )

        if name is None:
            name = "%5.2f_%f" % (bounds[0][0], molarity)
        self.name = name
        self.model_type = "Cube"
        self.collisionLevel = 0

        self.bb = bounds

        self.lower_bound = bounds[0]  # bottom left corner of cuboid
        self.upper_bound = bounds[1]  # top right corner of cuboid
        lower_bound = numpy.array(self.lower_bound)
        upper_bound = numpy.array(self.upper_bound)
        self.edges = numpy.array([upper_bound[i] - lower_bound[i] for i in range(3)])
        self.min_radius = min(self.edges) / 2  # sizex,sizey,sizez
        self.encapsulating_radius = numpy.linalg.norm(
            self.edges / 2
        )  # calculate encapsulating radius based on side length
        self.center = (
            lower_bound + (upper_bound - lower_bound) / 2
        )  # location of center based on corner points

        d = self.edges / 2.0

        self.vertices = [
            [-d, -d, -d],  # [x0, y0, z0],
            [d, -d, -d],  # [x1, y0, z0],
            [d, d, -d],  # [x1, y1, z0],
            [-d, d, -d],  # [x0, y1, z0],
            [-d, d, d],  # [x0, y1, z1],
            [d, d, d],  # [x1, y1, z1],
            [d, -d, d],  # [x1, y0, z1],
            [-d, -d, d],  # [x0, y0, z1],
        ]

    def collision_jitter(
        self,
        jtrans,
        rotMat,
        level,
        gridPointsCoords,
        current_grid_distances,
        histoVol,
        dpad,
    ):
        """
        Check cube for collision
        centers1 and centers2 should be the cornerPoints, so we can do parrallelpiped
        can also use the center plus size (edges), or the position/position2
        """
        corner1 = self.lower_bound
        corner2 = self.upper_bound
        corner1_trans = self.transformPoints(jtrans, rotMat, corner1)[0]  # bb1
        corner2_trans = self.transformPoints(jtrans, rotMat, corner2)[0]  # bb2
        center_trans = self.transformPoints(jtrans, rotMat, [self.center])[0]

        insidePoints = {}
        newDistPoints = {}

        diag_length = numpy.linalg.norm(corner2_trans - corner1_trans)

        search_radius = diag_length / 2.0 + self.encapsulating_radius + dpad

        bb = (
            center_trans - search_radius,
            center_trans + search_radius,
        )  # bounding box in world space

        if histoVol.runTimeDisplay:  # > 1:
            box = self.vi.getObject("collBox")
            if box is None:
                box = self.vi.Box(
                    "collBox", cornerPoints=bb, visible=1
                )  # cornerPoints=bb,visible=1)
            else:
                self.vi.updateBox(box, cornerPoints=bb)
            self.vi.update()

        points_to_check = histoVol.grid.getPointsInCube(
            bb, center_trans, search_radius
        )  # indices of all grid points within padded distance from cube center

        grid_point_vectors = numpy.take(gridPointsCoords, points_to_check, 0)

        # signed distances of grid points from the cube surface
        grid_point_distances = []
        for grid_point in grid_point_vectors:
            grid_point_distance = self.get_signed_distance(
                center_trans, grid_point, rotMat,
            )
            grid_point_distances.append(grid_point_distance)

        for pti in range(len(points_to_check)):
            # pti = point index

            grid_point_index = points_to_check[pti]
            signed_distance_to_cube_surface = grid_point_distances[pti]

            collision = (
                signed_distance_to_cube_surface
                + current_grid_distances[grid_point_index]
                <= 0
            )

            if collision:
                self.log.info("grid point already occupied %f", grid_point_index)
                return True, {}, {}

            # check if grid point lies inside the cube
            if signed_distance_to_cube_surface <= 0:
                if grid_point_index not in insidePoints or abs(
                    signed_distance_to_cube_surface
                ) < abs(insidePoints[grid_point_index]):
                    insidePoints[grid_point_index] = signed_distance_to_cube_surface
            elif (
                signed_distance_to_cube_surface
                <= current_grid_distances[grid_point_index]
            ):
                # update grid distances if no collision was detected
                if grid_point_index in newDistPoints:
                    newDistPoints[grid_point_index] = min(
                        signed_distance_to_cube_surface, newDistPoints[grid_point_index]
                    )
                else:
                    newDistPoints[grid_point_index] = signed_distance_to_cube_surface

        return False, insidePoints, newDistPoints

    def collides_with_compartment(
        self, env, jtrans, rotation_matrix,
    ):
        """
        Check cube for collision
        centers1 and centers2 should be the cornerPoints ?
        can also use the center plus size (edges), or the position/position2
        """
        centers1 = self.lower_bound
        centers2 = self.upper_bound
        edges = self.edges
        cent1T = self.transformPoints(jtrans, rotation_matrix, centers1)[0]  # bb1
        cent2T = self.transformPoints(jtrans, rotation_matrix, centers2)[0]  # bb2
        center = self.transformPoints(jtrans, rotation_matrix, [self.center])[0]

        x1, y1, z1 = cent1T
        x2, y2, z2 = cent2T
        vx, vy, vz = (x2 - x1, y2 - y1, z2 - z1)
        lengthsq = vx * vx + vy * vy + vz * vz
        length = sqrt(lengthsq)
        cx, cy, cz = posc = center  # x1+vx*.5, y1+vy*.5, z1+vz*.5
        radt = length / 2.0 + self.encapsulating_radius
        x, y, z = posc
        bb = ([x - radt, y - radt, z - radt], [x + radt, y + radt, z + radt])

        pointsInCube = env.grid.getPointsInCube(bb, posc, radt)

        pd = numpy.take(env.grid.gridPointsCoords, pointsInCube, 0) - center
        m = numpy.matrix(numpy.array(rotation_matrix).reshape(4, 4))  #
        mat = m.I
        rpd = ApplyMatrix(pd, mat)
        res = numpy.less_equal(numpy.fabs(rpd), edges / 2.0)
        c = numpy.average(res, 1)  # .astype(int)
        d = numpy.equal(c, 1.0)
        ptinside = numpy.nonzero(d)[0]
        ptinsideId = numpy.take(pointsInCube, ptinside, 0)
        compIdsSphere = numpy.take(env.grid.compartment_ids, ptinsideId, 0)
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
        edges = self.edges
        insidePoints = {}
        newDistPoints = {}
        cent1T = self.transformPoints(jtrans, rotMat, self.lower_bound)[0]  # bb1
        cent2T = self.transformPoints(jtrans, rotMat, self.upper_bound)[0]  # bb2
        center = self.transformPoints(jtrans, rotMat, [self.center],)[0]
        #        cylNum = 0
        #        for radc, p1, p2 in zip(edges, cent1T, cent2T):
        x1, y1, z1 = cent1T
        x2, y2, z2 = cent2T
        vx, vy, vz = (x2 - x1, y2 - y1, z2 - z1)
        lengthsq = vx * vx + vy * vy + vz * vz
        length = sqrt(lengthsq)
        posc = center  # x1+vx*.5, y1+vy*.5, z1+vz*.5
        radt = length / 2.0 + self.encapsulating_radius

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
        res = numpy.less_equal(numpy.fabs(rpd), edges / 2.0)
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
            d = dist - self.encapsulating_radius
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

    def cube_surface_distance(
        self, point,
    ):
        # returns the distance to the closest cube surface from point
        side_lengths = numpy.abs(self.edges) / 2.0

        dist_x, dist_y, dist_z = numpy.abs(point) - side_lengths

        if dist_x <= 0:
            if dist_y <= 0:
                if dist_z <= 0:
                    # point is inside the cube
                    current_distance = -numpy.min(numpy.abs([dist_x, dist_y, dist_z]))
                else:
                    # z plane is the closest
                    current_distance = dist_z
            else:
                if dist_z <= 0:
                    # y plane is the closest
                    current_distance = dist_y
                else:
                    # yz edge is the closest
                    current_distance = numpy.sqrt(dist_y ** 2 + dist_z ** 2)
        else:
            if dist_y <= 0:
                if dist_z <= 0:
                    # x plane is closest
                    current_distance = dist_x
                else:
                    # xz edge is the closest
                    current_distance = numpy.sqrt(dist_x ** 2 + dist_z ** 2)
            else:
                if dist_z <= 0:
                    # xy edge is the closest
                    current_distance = numpy.sqrt(dist_x ** 2 + dist_y ** 2)
                else:
                    # vertex is the closest
                    current_distance = numpy.sqrt(
                        dist_x ** 2 + dist_y ** 2 + dist_z ** 2
                    )
        return current_distance

    def get_signed_distance(
        self, packing_location, grid_point_location, rotation_matrix,
    ):
        # returns the distance to 'grid_point_location' from the nearest cube surface
        # the cube center is located at packing_location
        # a rotation matrix rotation_matrix is applied to the cube
        signed_distance_to_surface = []
        inv_rotation_matrix = numpy.linalg.inv(rotation_matrix)

        transformed_point = [
            (grid_point_location - packing_location)
        ]  # translate points to cube center
        transformed_point = self.transformPoints(
            self.center, inv_rotation_matrix, transformed_point
        )  # rotate points to align with cube axis
        # run distance checks on transformed points
        signed_distance_to_surface = self.cube_surface_distance(transformed_point[0])

        return signed_distance_to_surface

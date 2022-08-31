import os
from panda3d.core import Point3, TransformState
from panda3d.bullet import BulletSphereShape, BulletRigidBodyNode
from math import pi, sqrt
import numpy

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
        color=None,
        coordsystem="right",
        count=0,
        cutoff_boundary=None,
        cutoff_surface=None,
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
            cutoff_boundary=cutoff_boundary,
            coordsystem=coordsystem,
            count=count,
            cutoff_surface=cutoff_surface,
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
        min_radius = 999
        if radii is not None:
            for level in radii:
                if isinstance(level, dict):
                    if min(level["radii"]) < min_radius:
                        min_radius = min(level["radii"])
                else:
                    if min(level) < min_radius:
                        min_radius = min(level)
        self.min_radius = min_radius
        if name is None:
            name = "%s_%f" % (str(radii), molarity)
        self.name = name
        self.singleSphere = False
        self.sphereFile = sphereFile
        print("sphereFile", sphereFile)
        if sphereFile is not None and str(sphereFile) != "None":
            sphereFileo = autopack.retrieveFile(sphereFile, cache="collisionTrees")
            fileName, fileExtension = os.path.splitext(sphereFile)
            self.log.info("sphereTree %r", sphereFileo)

            if sphereFileo is not None and os.path.isfile(sphereFileo):
                self.sphereFile = sphereFile
                sphereFile = sphereFileo
                if fileExtension == ".mstr":  # BD_BOX format
                    data = numpy.loadtxt(sphereFileo, converters={0: lambda s: 0})
                    positions = data[:, 1:4]
                    radii = data[:, 4]
                    self.min_radius = min(radii)
                    # np.apply_along_axis(np.linalg.norm, 1, c)
                    self.encapsulating_radius = max(
                        numpy.sqrt(numpy.einsum("ij,ij->i", positions, positions))
                    )  # shoud be max distance
                    self.min_radius = self.encapsulating_radius
                    positions = [positions]
                    radii = [radii]
                elif fileExtension == ".sph":
                    min_radius, rM, positions, radii, children = self.getSpheres(
                        sphereFileo
                    )
                    # if a user didn't set this properly before
                    if not len(radii):
                        self.min_radius = 1.0
                        self.encapsulating_radius = 1.0
                    else:
                        # min_radius is used to compute grid spacing. It represents the
                        # smallest radius around the anchor point(i.e.
                        # the point where the
                        # ingredient is dropped that needs to be free
                        self.min_radius = min_radius
                        # encapsulating_radius is the radius of the sphere
                        # centered at 0,0,0
                        # and encapsulate the ingredient
                        self.encapsulating_radius = rM
                else:
                    self.log.info(
                        "sphere file extension not recognized %r", fileExtension
                    )
        self.set_sphere_positions(positions, radii)
    
    def getSpheres(self, sphereFile):
        """
        get spherical approximation of shape
        """
        # file format is space separated
        # float:Rmin float:Rmax
        # int:number of levels
        # int: number of spheres in first level
        # x y z r i j k ...# first sphere in first level and 0-based indices
        # of spheres in next level covererd by this sphere
        # ...
        # int: number of spheres in second level
        f = open(sphereFile)
        datao = f.readlines()
        f.close()

        # strip comments
        data = [x for x in datao if x[0] != "#" and len(x) > 1 and x[0] != "\r"]

        rmin, rmax = list(map(float, data[0].split()))
        nblevels = int(data[1])
        radii = []
        centers = []
        children = []
        line = 2
        for level in range(nblevels):
            rl = []
            cl = []
            ch = []
            nbs = int(data[line])
            line += 1
            for n in range(nbs):
                w = data[line].split()
                x, y, z, r = list(map(float, w[:4]))
                if level < nblevels - 1:  # get sub spheres indices
                    ch.append(list(map(int, w[4:])))
                cl.append((x, y, z))
                rl.append(r)
                line += 1
            centers.append(cl)
            radii.append(rl)
            children.append(ch)
        # we ignore the hierarchy for now
        return rmin, rmax, centers, radii, children

    def set_sphere_positions(self, positions, radii):
        # positions and radii are passed to the constructor
        # check the format old nested array, new array of dictionary
        nLOD = 0
        if positions is not None:
            nLOD = len(positions)

        self.positions = []
        self.radii = []
        if positions is not None and isinstance(positions[0], dict):
            for i in range(nLOD):
                c = numpy.array(positions[i]["coords"])
                n = int(len(c) / 3)
                self.positions.append(c.reshape((n, 3)).tolist())
                self.radii.append(radii[i]["radii"])
            if len(self.radii) == 0:
                self.radii = [[10]]  # some default value ?
                self.positions = [[[0, 0, 0]]]
            self.deepest_level = len(radii) - 1
        else:  # regular nested
            if (
                positions is None or positions[0] is None or positions[0][0] is None
            ):  # [0][0]
                positions = [[[0, 0, 0]]]

            else:
                if radii is not None:
                    delta = numpy.array(positions[0])
                    rM = sqrt(max(numpy.sum(delta * delta, 1)))
                    self.encapsulating_radius = max(rM, self.encapsulating_radius)
            # if radii is not None and positions is not None:
            # for r, c in zip(radii, positions):
            #     assert len(r) == len(c)
            if radii is not None:
                self.deepest_level = len(radii) - 1
            if radii is None:
                radii = [[0]]
            self.radii = radii
            self.positions = positions
        if self.min_radius == 0:
            self.min_radius = min(min(self.radii))
        if self.encapsulating_radius <= 0.0 or self.encapsulating_radius < max(
            self.radii[0]
        ):
            self.encapsulating_radius = max(self.radii[0])  #

    def collision_jitter(
        self,
        jtrans,
        rotMat,
        level,
        gridPointsCoords,
        current_grid_distances,
        env,
        dpad,
    ):
        """
        Check spheres for collision
        """
        centers = self.positions[level]
        radii = self.radii[level]
        # should we also check for outside the main grid ?
        # wouldnt be faster to do sphere-sphere distance test ? than points/points from the grid
        centT = self.transformPoints(jtrans, rotMat, centers)  # centers)
        # sphNum = 0  # which sphere in the sphere tree we're checking
        # self.distances_temp = []
        insidePoints = {}
        newDistPoints = {}
        at_max_level = level == self.deepest_level and (level + 1) == len(
            self.positions
        )
        for radius_of_ing_being_packed, posc in zip(radii, centT):
            x, y, z = posc
            radius_of_area_to_check = (
                radius_of_ing_being_packed + dpad
            )  # extends the packing ingredient's bounding box to be large enough to include masked gridpoints of the largest possible ingrdient in the receipe
            #  TODO: add realtime render here that shows all the points being checked by the collision

            pointsToCheck = env.grid.getPointsInSphere(
                posc, radius_of_area_to_check
            )  # indices
            # check for collisions by looking at grid points in the sphere of radius radc
            delta = numpy.take(gridPointsCoords, pointsToCheck, 0) - posc
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
                collision = (
                    current_grid_distances[grid_point_index]
                    + distance_to_packing_location
                    <= radius_of_ing_being_packed
                )

                if collision:
                    # an object is too close to the sphere at this level
                    if not at_max_level:
                        # if we haven't made it all the way down the sphere tree,
                        # check a level down
                        new_level = level + 1
                        # NOTE: currently with sphere trees, no children seem present
                        # get sphere that are children of this one
                        # ccenters = []
                        # cradii = []
                        # for sphInd in self.children[level][sphNum]:
                        #     ccenters.append(nxtLevelSpheres[sphInd])
                        #     cradii.append(nxtLevelRadii[sphInd])
                        return self.collision_jitter(
                            jtrans,
                            rotMat,
                            new_level,
                            gridPointsCoords,
                            current_grid_distances,
                            env,
                            dpad,
                        )
                    else:
                        self.log.info(
                            "grid point already occupied %f",
                            current_grid_distances[grid_point_index],
                        )
                        return True, {}, {}
                if not at_max_level:
                    # we don't want to calculate new distances if we are not
                    # at the highest geo
                    # but getting here means there was no collision detected
                    # so the loop can continue
                    continue
                signed_distance_to_sphere_surface = (
                    distance_to_packing_location - radius_of_ing_being_packed
                )

                (
                    insidePoints,
                    newDistPoints,
                ) = self.get_new_distances_and_inside_points(
                    env,
                    jtrans,
                    rotMat,
                    grid_point_index,
                    current_grid_distances,
                    newDistPoints,
                    insidePoints,
                    signed_distance_to_sphere_surface,
                )

            if not at_max_level:
                # we didn't find any colisions with the this level, but we still want
                # the inside points to be based on the most detailed geom
                new_level = self.deepest_level
                return self.collision_jitter(
                    jtrans,
                    rotMat,
                    new_level,
                    gridPointsCoords,
                    current_grid_distances,
                    env,
                    dpad,
                )
        return False, insidePoints, newDistPoints

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

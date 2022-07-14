import math
import os
import numpy
import trimesh
from cellpack import autopack


class MeshStore:
    def __init__(self):
        self.scene = trimesh.scene.Scene()

    @staticmethod
    def get_collada_material(geom, col):
        # get the bound geometries
        mat = None
        boundg = list(col.scene.objects("geometry"))
        for bg in boundg:
            if bg.original == geom:
                m = bg.materialnodebysymbol.values()
                if len(m):
                    k0 = [*bg.materialnodebysymbol][0]
                    mat = bg.materialnodebysymbol[k0].target
        return mat

    @staticmethod
    def normalize_v3(arr):
        """Normalize a numpy array of 3 component vectors shape=(n,3)"""
        #        return self.unit_vector(arr,axis=1)
        #        lens = numpy.linalg.norm(arr,axis=1)
        lens = numpy.sqrt(arr[:, 0] ** 2 + arr[:, 1] ** 2 + arr[:, 2] ** 2)
        arr[:, 0] /= lens
        arr[:, 1] /= lens
        arr[:, 2] /= lens
        return arr

    @staticmethod
    def normal_array(vertices, faces):
        vertices = numpy.array(vertices)
        faces = numpy.array(faces)
        # Create a zeroed array with the same type and shape as our vertices i.e., per vertex normal
        norm = numpy.zeros(vertices.shape, dtype=vertices.dtype)
        # Create an indexed view into the vertex array using the array of three indices for triangles
        tris = vertices[faces]
        # Calculate the normal for all the triangles, by taking the cross product of the vectors v1-v0, and v2-v0 in each triangle
        n = numpy.cross(tris[::, 1] - tris[::, 0], tris[::, 2] - tris[::, 0])
        # n is now an array of normals per triangle. The length of each normal is dependent the vertices, # we need to normalize these, so that our next step weights each normal equally.normalize_v3(n)
        # now we have a normalized array of normals, one per triangle, i.e., per triangle normals.
        # But instead of one per triangle (i.e., flat shading), we add to each vertex in that triangle,
        # the triangles' normal. Multiple triangles would then contribute to every vertex, so we need to normalize again afterwards.
        # The cool part, we can actually add the normals through an indexed view of our (zeroed) per vertex normal array
        norm[faces[:, 0]] += n
        norm[faces[:, 1]] += n
        norm[faces[:, 2]] += n
        return MeshStore.normalize_v3(norm)

    @staticmethod
    def get_midpoint(p1, p2):
        return [(p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0, (p1[2] + p2[2]) / 2.0]

    @staticmethod
    def norm(a, b, c):
        """
        return the norm of the vector [a,b,c]

        >>> result = helper.norm(a,b,c) #a,b,c being double

        @type a: float
        @param a:  first value of the vector
        @type b: float
        @param b:  second value of the vector
        @type c: float
        @param c:  third value of the vector

        @rtype: float
        @return: the norm of the vector

        """
        return math.sqrt(a * a + b * b + c * c)

    @staticmethod
    def normalize(A):
        """
        return the normalized vector A [x,y,z]

        >>> a = [1.0,3.0,5.0]
        >>> a_normalized = helper.normalize(a)

        @type A: vector
        @param A:  the 3d vector
        @rtype: vector
        @return: the normalized 3d vecor
        """
        norm = MeshStore.norm(A[0], A[1], A[2])
        if norm == 0.0:
            return A
        else:
            return [A[0] / norm, A[1] / norm, A[2] / norm]

    @staticmethod
    def get_mesh_filepath_and_extension(filename):
        name = filename.split("/")[-1]
        fileName, fileExtension = os.path.splitext(name)
        if fileExtension == "":
            tmpFileName1 = autopack.retrieveFile(
                filename + ".indpolface", cache="geometries"
            )
            filename = os.path.splitext(tmpFileName1)[0]
        else:
            filename = autopack.retrieveFile(filename, cache="geometries")
        if filename is None:
            return None
        if not os.path.isfile(filename) and fileExtension != "":
            return None
        file_name, file_extension = os.path.splitext(filename)
        return file_name, file_extension

    def add_mesh_to_scene(self, mesh, name):
        self.scene.add_geometry(mesh, geom_name=name)

    def read_mesh_file(self, filename):
        file_name, file_extension = MeshStore.get_mesh_filepath_and_extension(filename)
        data = trimesh.exchange.load.load(
            f"{file_name}{file_extension}"
        )  # , ignore=[collada.DaeUnsupportedError,
        if type(data) == trimesh.base.Trimesh:
            return data
        for key in data.geometry:
            return data.geometry[key]

    def create_mesh(
        self,
        name,
        vertices,
        vnormals,
        faces,
    ):
        """
        This is the main function that create a polygonal mesh.

        @type  name: string
        @param name: name of the pointCloud
        @type  vertices: array
        @param vertices: list of x,y,z vertices points
        @type  vnormals: array
        @param vnormals: list of x,y,z vertex normals vector
        @type  faces: array
        @param faces: list of i,j,k indice of vertex by face
        @return:  the polygon object
        """
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        self.add_mesh_to_scene(mesh, name)
        return mesh

    def create_sphere_data(self, iterations):
        """from http://paulbourke.net/geometry/circlesphere/csource2.c"""
        i = 0
        j = 0
        n = 0
        nstart = 0
        vertices = []
        p1 = MeshStore.normalize((1.0, 1.0, 1.0))
        p2 = MeshStore.normalize((-1.0, -1.0, 1.0))
        p3 = MeshStore.normalize((1.0, -1.0, -1.0))
        p4 = MeshStore.normalize((-1.0, 1.0, -1.0))
        vertices.extend([p1, p2, p3, p4])
        allfacets = int(math.pow(4, iterations))
        facets = numpy.zeros((allfacets, 3), "int")
        facets[0] = [0, 1, 2]  # p1; facets[0].p2 = p2; facets[0].p3 = p3;
        facets[1] = [0, 1, 3]  # .p1 = p2; facets[1].p2 = p1; facets[1].p3 = p4;
        facets[2] = [1, 3, 2]  # .p1 = p2; facets[2].p2 = p4; facets[2].p3 = p3;
        facets[3] = [0, 2, 3]  # .p1 = p1; facets[3].p2 = p3; facets[3].p3 = p4;

        n = 4
        for i in range(1, iterations):  # (i=1;i<iterations;i++) {
            nstart = n
            for j in range(nstart):  # (j=0;j<nstart;j++) {
                # /* Create initially copies for the new facets */
                facets[n] = facets[j]
                facets[n + 1] = facets[j]
                facets[n + 2] = facets[j]

                # /* Calculate the midpoints */
                p1 = MeshStore.get_midpoint(
                    vertices[facets[j][0]], vertices[facets[j][1]]
                )
                p2 = MeshStore.get_midpoint(
                    vertices[facets[j][1]], vertices[facets[j][2]]
                )
                p3 = MeshStore.get_midpoint(
                    vertices[facets[j][2]], vertices[facets[j][0]]
                )
                vertices.extend([p1, p2, p3])
                ip1 = len(vertices) - 3
                ip2 = len(vertices) - 2
                ip3 = len(vertices) - 1
                # /* Replace the current facet */
                facets[j][1] = ip1
                facets[j][2] = ip3
                # /* Create the changed vertices in the new facets */
                facets[n][0] = ip1
                facets[n][2] = ip2
                facets[n + 1][0] = ip3
                facets[n + 1][1] = ip2
                facets[n + 2][0] = ip1
                facets[n + 2][1] = ip2
                facets[n + 2][2] = ip3
                n += 3
        vertices = [MeshStore.normalize(v) for v in vertices]
        return vertices, facets

    def get_nsphere(self, geomname):
        mesh = self.get_object(geomname)
        if mesh is not None:
            return trimesh.nsphere.minimum_nsphere(mesh)

    def create_sphere(self, name, iterations, radius):
        """
        Create the mesh data and the mesh object of a Sphere of a given radius

        @type  name: string
        @param name: name for the sphere
        @type  iterations: int
        @param iterations: resolution
        @type  radius: float
        @param radius: radius of the sphere

        @rtype:   Object, Mesh
        @return:  Sphere Object and Mesh
        """
        v, f = self.create_sphere_data(iterations)
        mesh = self.create_mesh(name, numpy.array(v) * radius, None, f)
        return mesh

    def contains_point(self, geomname, point):
        mesh = self.get_object(geomname)
        if mesh is not None:
            intersector = trimesh.ray.ray_triangle.RayMeshIntersector(mesh)
            return intersector.contains_points([point])[0]
        return False

    def contains_points(self, geomname, points):
        mesh = self.get_object(geomname)
        if mesh is not None:
            intersector = trimesh.ray.ray_pyembree.RayMeshIntersector(mesh)
            return intersector.contains_points(points)
        return [False]

    def contains_points_slow(self, geomname, points):
        mesh = self.get_object(geomname)
        if mesh is not None:
            intersector = trimesh.ray.ray_triangle.RayMeshIntersector(mesh)
            return intersector.contains_points(points)
        return [False]

    def get_smallest_radius(self, geomname, center):
        mesh = self.get_object(geomname)
        if mesh is not None:
            query = trimesh.proximity.ProximityQuery(mesh)
            (closet_point, distance, triangle_id) = query.on_surface([center])
            return distance[0]

    def get_normal(self, geomname, point_pos):
        mesh = self.get_object(geomname)
        if mesh is not None:
            query = trimesh.proximity.ProximityQuery(mesh)
            (distance, triangle_ids) = query.vertex([point_pos])
            triangle_id = triangle_ids[0]
            return mesh.vertex_normals[triangle_id]

    def get_centroid(self, geomname):
        mesh = self.get_object(geomname)
        if mesh is not None:
            return mesh.centroid
        return None

    def get_object(self, geomname):
        return self.scene.geometry.get(geomname)

    def build_mesh(self, data, geomname):
        """
        Create a polygon mesh object from a dictionary verts,faces,normals
        """
        nv = int(len(data["verts"]) / 3)
        nf = int(len(data["faces"]) / 3)
        vertices = numpy.array(data["verts"]).reshape((nv, 3))
        faces = numpy.array(data["faces"]).reshape((nf, 3))
        vnormals = numpy.array(data["normals"]).reshape((nv, 3))
        geom = self.create_mesh(geomname, vertices, None, faces)[0]

        autopack.helper.saveDejaVuMesh(
            autopack.cache_geoms + os.sep + geomname, self.vertices, self.faces
        )
        autopack.helper.saveObjMesh(
            autopack.cache_geoms + os.sep + geomname + ".obj", self.vertices, self.faces
        )
        # self.saveObjMesh(autopack.cache_geoms + os.sep + geomname + ".obj")
        return geom, vertices, faces, vnormals

    def get_mesh(self, mesh_name, file_path=None):
        geometry = self.get_object(mesh_name)
        if geometry is None and file_path is not None:
            geometry = self.read_mesh_file(file_path)
            self.add_mesh_to_scene(geometry, mesh_name)
        return geometry

    def decompose_mesh(self, poly, edit=True, copy=True, tri=True, transform=True):
        if not isinstance(poly, trimesh.Trimesh):
            return [], [], []
        return poly.faces, poly.vertices, poly.vertex_normals

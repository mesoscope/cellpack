import cellpack.autopack as autopack


class Representations:
    DATABASE = "https://raw.githubusercontent.com/mesoscope/cellPACK_data/master/cellPACK_database_1.1.0"

    def __init__(self, mesh=None, atomic=None, packing=None):
        """
        This object holds the different representation types for an ingredient
        ----------
        mesh : OBJ file info
        atomic : PDB or ciff file info
        packing: Sphere tree file or sphere tree data
        """
        self.mesh = mesh
        self.atomic = atomic
        self.packing = packing

    @staticmethod
    def _read_sphere_file(file):
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
        f = open(file)
        sphere_data = f.readlines()
        f.close()

        # strip comments
        data = [x for x in sphere_data if x[0] != "#" and len(x) > 1 and x[0] != "\r"]

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
        return centers, radii

    def get_spheres(self):
        if "path" in self.packing:
            sphere_file = f"{self.packing['path']}/{self.packing['name']}"
            sphere_file_path = autopack.retrieveFile(
                sphere_file, cache="collisionTrees"
            )
            (
                positions,
                radii,
            ) = Representations._read_sphere_file(sphere_file_path)
            self.packing["positions"] = positions
            self.packing["radii"] = radii
        positions = self.packing["positions"]
        radii = self.packing["radii"]
        if positions is None or positions[0] is None or positions[0][0] is None:
            positions = [[[0, 0, 0]]]

        if radii is None:
            radii = [[0]]
        return positions, radii

    def has_pdb(self):
        return self.atomic is not None

    def get_pdb_path(self):
        if "path" in self.atomic:
            if self.atomic["path"] == "default":
                return f"{self.DATABASE}/other/{self.atomic['name']}"
            return f"{self.atomic['path']}{self.atomic['name']}"
        else:
            return self.atomic["id"]

    def has_mesh(self):
        return self.mesh is not None

    def get_mesh_name(self):
        if not self.has_mesh():
            return None
        else:
            self.mesh["name"]

    def get_mesh_path(self):
        if not self.has_mesh():
            return None
        else:
            if self.mesh["path"] == "default":
                return f"{self.DATABASE}/geometries/{self.mesh['name']}"
            return f"{self.mesh['path']}{self.mesh['name']}"

    def get_mesh_format(self):
        if not self.has_mesh():
            return None
        else:
            return self.mesh["format"]

    
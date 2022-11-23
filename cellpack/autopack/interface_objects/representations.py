from math import sqrt
import cellpack.autopack as autopack
import numpy as np


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
        self.active = None
        if self.packing is not None:
            # self.packing = {
            #     "radii": [[r]],
            #     "positions": [[x, y, x]],
            # }
            self.set_sphere_positions()

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
        print(file)
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

    def _get_spheres(self):
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
        # can be passed in directly, or they were just read from a file
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
            return self.mesh["name"]

    def get_mesh_path(self):
        if not self.has_mesh():
            return None
        else:
            if self.mesh["path"] == "default":
                return f"{self.DATABASE}/geometries/{self.mesh['name']}"
            return f"{self.mesh['path']}/{self.mesh['name']}"

    def get_mesh_format(self):
        if not self.has_mesh():
            return None
        else:
            return self.mesh["format"]

    def set_active(self, type="atomic"):
        self.active = type

    def get_active(self):
        return self.active

    def get_active_data(self):
        if self.active is None:
            return {}
        return getattr(self, self.active)

    def get_adjusted_position(self, position, rotation):
        active_data = self.get_active_data()
        if "transform" in active_data:
            offset = np.array(active_data["transform"]["translate"])
        else:
            offset = np.array([0, 0, 0])
        rot_mat = np.array(rotation[0:3, 0:3])
        adj_offset = np.matmul(rot_mat, offset)
        return position - adj_offset

    def set_sphere_positions(self):
        positions, radii = self._get_spheres()
        packing = self.packing
        packing["radii"] = radii
        packing["positions"] = positions

    def get_radii(self):
        if "radii" not in self.packing:
            raise ValueError("expected to have radii")
        return self.packing["radii"]

    def get_positions(self):
        if "positions" not in self.packing:
            raise ValueError("expected to have positions")
        return self.packing["positions"]

    def get_deepest_level(self):
        radii = self.get_radii()
        return len(radii) - 1

    def get_min_max_radius(self):
        radii = self.get_radii()
        r_max_level_zero = max(radii[0])
        positions = self.get_positions()
        delta = np.array(positions[0])
        r_max = sqrt(max(np.sum(delta * delta, 1)))
        r_max = max(r_max, r_max_level_zero)
        r_min = min(min(radii))
        return r_min, r_max

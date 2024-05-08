import collections
import copy
import pickle

import numpy


def get_distance(pt1, pt2):
    return numpy.linalg.norm(pt2 - pt1)


def get_distances_from_point(np_array_of_pts, pt):
    return numpy.linalg.norm(np_array_of_pts - pt, axis=1)


def ingredient_compare1(x, y):
    """
    sort ingredients using decreasing priority and decreasing radii for
    priority ties and decreasing completion for radii ties
    for priority > 0
    """
    p1 = x.priority
    p2 = y.priority
    if p1 < p2:  # p1 > p2
        return 1
    elif p1 == p2:  # p1 == p1
        r1 = x.min_radius
        r2 = y.min_radius
        if r1 > r2:  # r1 < r2
            return 1
        elif r1 == r2:  # r1 == r2
            c1 = x.completion
            c2 = y.completion
            if c1 > c2:  # c1 > c2
                return 1
            elif c1 == c2:
                return 0
            else:
                return -1
        else:
            return -1
    else:
        return -1


def ingredient_compare0(x, y):
    """
    sort ingredients using decreasing priority and decreasing radii for
    priority ties and decreasing completion for radii ties
    for priority < 0
    """
    p1 = x.priority
    p2 = y.priority
    if p1 > p2:  # p1 > p2
        return 1
    elif p1 == p2:  # p1 == p1
        r1 = x.min_radius
        r2 = y.min_radius
        if r1 > r2:  # r1 < r2
            return 1
        elif r1 == r2:  # r1 == r2
            c1 = x.completion
            c2 = y.completion
            if c1 > c2:  # c1 > c2
                return 1
            elif c1 == c2:
                return 0
            else:
                return -1
        else:
            return -1
    else:
        return -1


def ingredient_compare2(x, y):
    """
    sort ingredients using decreasing radii and decresing completion
    for radii matches:
    priority = 0
    """
    c1 = x.min_radius
    c2 = y.min_radius
    if c1 < c2:
        return 1
    elif c1 == c2:
        r1 = x.completion
        r2 = y.completion
        if r1 > r2:
            return 1
        elif r1 == r2:
            return 0
        else:
            return -1
    else:  # x < y
        return -1


def cmp_to_key(mycmp):
    "Convert a cmp= function into a key= function"

    class K:
        def __init__(self, obj, *args):
            self.obj = obj

        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0

        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0

        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0

        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0

        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0

        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0

    return K


def deep_merge(dct, merge_dct):
    """Recursive dict merge

    This mutates dct - the contents of merge_dct are added to dct (which is also returned).
    If you want to keep dct you could call it like deep_merge(copy.deepcopy(dct), merge_dct)
    """
    if dct is None:
        dct = {}
    if merge_dct is None:
        merge_dct = {}
    for k, v in merge_dct.items():
        if (
            k in dct
            and isinstance(dct[k], dict)
            and isinstance(merge_dct[k], collections.abc.Mapping)
        ):
            deep_merge(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]
    return dct


def expand_object_using_key(current_object, expand_on, lookup_dict):
    object_key = current_object[expand_on]
    base_object = lookup_dict[object_key]
    new_object = deep_merge(copy.deepcopy(base_object), current_object)
    del new_object[expand_on]
    return new_object


def check_paired_key(val_dict, key1=None, key2=None):
    """
    Checks if the key pair exists in dict
    """
    for key in val_dict:
        if (key1 in key) and (key2 in key):
            return True
    return False


def get_paired_key(val_dict, key1=None, key2=None):
    """
    Get the combined key from dict
    """
    for key in val_dict:
        if (key1 in key) and (key2 in key):
            return key


def load_object_from_pickle(pickle_file_object):
    """
    Update an object from a pickle file
    """
    try:
        output_object = pickle.load(pickle_file_object)
    except Exception as e:
        raise ValueError(f"Error loading saved object: {e}")
    return output_object


def get_min_value_from_distribution(distribution_options, return_int=False):
    """
    Returns a low bound on the value from a distribution
    """
    value = None
    if distribution_options.get("distribution") == "uniform":
        value = distribution_options.get("min", 1)

    if distribution_options.get("distribution") == "normal":
        value = distribution_options.get("mean", 0) - 2 * distribution_options.get(
            "std", 1
        )

    if distribution_options.get("distribution") == "list":
        value = numpy.nanmin(distribution_options.get("list_values", None))

    if return_int and value is not None:
        value = int(numpy.rint(value))

    return value


def get_max_value_from_distribution(distribution_options, return_int=False):
    """
    Returns a high bound on the value from a distribution
    """
    value = None
    if distribution_options.get("distribution") == "uniform":
        value = distribution_options.get("max", 1)

    if distribution_options.get("distribution") == "normal":
        value = distribution_options.get("mean", 0) + 2 * distribution_options.get(
            "std", 1
        )

    if distribution_options.get("distribution") == "list":
        value = numpy.nanmax(distribution_options.get("list_values", None))

    if return_int and value is not None:
        value = int(numpy.rint(value))

    return value


def get_value_from_distribution(distribution_options, return_int=False):
    """
    Returns a value from the distribution options
    """
    if distribution_options.get("distribution") == "uniform":
        if return_int:
            return int(
                numpy.random.randint(
                    distribution_options.get("min", 0),
                    distribution_options.get("max", 1),
                )
            )
        else:
            return numpy.random.uniform(
                distribution_options.get("min", 0),
                distribution_options.get("max", 1),
            )
    if distribution_options.get("distribution") == "normal":
        value = numpy.random.normal(
            distribution_options.get("mean", 0), distribution_options.get("std", 1)
        )
    elif distribution_options.get("distribution") == "list":
        value = numpy.random.choice(distribution_options.get("list_values", None))
    else:
        value = None

    if return_int and value is not None:
        value = int(numpy.rint(value))

    return value


def get_seed_list(packing_config_data, recipe_data):
    # Returns a list of seeds to use for packing
    if packing_config_data["randomness_seed"] is not None:
        seed_list = packing_config_data["randomness_seed"]
    elif recipe_data.get("randomness_seed") is not None:
        seed_list = recipe_data["randomness_seed"]
    else:
        seed_list = None

    if isinstance(seed_list, int):
        seed_list = [seed_list]

    if (seed_list is not None) and (
        len(seed_list) != packing_config_data["number_of_packings"]
    ):
        base_seed = int(seed_list[0])
        seed_list = [
            base_seed + i for i in range(packing_config_data["number_of_packings"])
        ]

    return seed_list


# These functions have been moved over from Analysis.py
"""
Created on Mon May  6 22:58:44 2013

@author: ludo
"""

import csv
import json
import math
import os

import numpy as np
import pandas as pd
import seaborn as sns
import trimesh
from matplotlib import pyplot as plt
from matplotlib.patches import Circle, Patch
from PIL import Image
from scipy import stats
from scipy.cluster import hierarchy
from scipy.spatial import distance
from sklearn.metrics import matthews_corrcoef
from tqdm import tqdm

import cellpack.autopack as autopack
from cellpack.autopack.GeometryTools import Rectangle
from cellpack.autopack.MeshStore import MeshStore
from cellpack.autopack.upy import colors as col
from cellpack.autopack.upy.colors import map_colors


def get_xyz_dict_from_all_pos_dict(all_pos_dict):
    """
    returns array of x, y, and z positions for each seed for runs
    in all_pos_dict
    """
    all_objs = {}
    for seed, object_dict in all_pos_dict.items():
        for obj, positions in object_dict.items():
            positions = np.array(positions)
            if obj not in all_objs:
                all_objs[obj] = {}
            if seed not in all_objs[obj]:
                all_objs[obj][seed] = {}
            for ct, dim in enumerate(["x", "y", "z"]):
                all_objs[obj][seed][dim] = positions[:, ct]
    return all_objs


def save_array_to_file(array_to_save, file_path, seed_index):
    f_handle = open(file_path, "a" if seed_index else "w")
    np.savetxt(
        f_handle,
        array_to_save,
        delimiter=",",
    )
    f_handle.close()


def getPositionsFromResFile(self):
    # could actually restore file using histoVol.
    # or not
    # need to parse apr file here anyway
    return []


def getPositionsFromObject(self, parents):
    positions = []
    for parent in parents:
        obparent = self.helper.getObject(parent)
        children = self.helper.getChilds(obparent)
        for ch in children:
            ingr_name = self.helper.getName(ch)
            meshp = self.helper.getObject("Meshs_" + ingr_name.split("_")[0])
            if meshp is None:
                c = self.helper.getChilds(ch)
                if not len(c):
                    continue
                meshp_children = self.helper.getChilds(
                    c[0]
                )  # continue #should get sphere/cylnder parent ?
            else:
                meshp_children = self.helper.getChilds(meshp)
            for cc in meshp_children:
                pos = self.helper.ToVec(self.helper.getTranslation(cc))
                positions.append(pos)
    return positions


def getDistanceFrom(self, target, parents=None, **options):
    """
    target : name or host object target or target position
    parent : name of host parent object for the list of object to measure distance from
    objects : list of object or list of points
    """
    # get distance from object to the target.
    # all object are in env.packed_objects
    # get options

    if isinstance(target, (list, tuple)):
        targetPos = target
    elif isinstance(target, str):
        o = self.helper.getObject(target)
        if o is not None:
            targetPos = self.helper.ToVec(self.helper.getTranslation(o))
    else:
        o = self.helper.getObject(target)
        if o is not None:
            targetPos = self.helper.ToVec(self.helper.getTranslation(o))
    listCenters = []
    if self.result_file is None:
        if parents is None and self.result_file is None:
            listeParent = [self.env.name + "_cytoplasm"]
            for o in self.env.compartments:
                listeParent.append(o.name + "_Matrix")
                listeParent.append(o.name + "_surface")
        elif parents is not None and self.result_file is None:
            listeParent = parents
        listCenters = self.getPositionsFromObject(listeParent)

    delta = np.array(listCenters) - np.array(targetPos)
    delta *= delta
    distA = np.sqrt(delta.sum(1))
    return distA


def getClosestDistance(self, parents=None, **options):
    if self.result_file is None:
        if parents is None and self.result_file is None:
            listeParent = [self.env.name + "_cytoplasm"]
            for o in self.env.compartments:
                listeParent.append(o.name + "_Matrix")
                listeParent.append(o.name + "_surface")
        elif parents is not None and self.result_file is None:
            listeParent = parents
        listeCenters = self.getPositionsFromObject(listeParent)
    else:
        # use data from file
        # TODO: currently getPositionsFromResFile returns an empty list
        # listeCenters = self.getPositionsFromResFile(listeParent)
        listeCenters = []
    # is the distance in the result array ?
    listeDistance = np.zeros(len(listeCenters)) + 99999
    for i in range(len(listeCenters)):
        for j in range(i + 1, len(listeCenters)):
            # should use point
            d = self.helper.measure_distance(listeCenters[i], listeCenters[j])
            if d < listeDistance[i]:
                listeDistance[i] = d
    return listeDistance


def displayDistance(
    self,
    ramp_color1=[1, 0, 0],
    ramp_color2=[0, 0, 1],
    ramp_color3=None,
    cutoff=60.0,
):
    distances = np.array(self.env.grid.distToClosestSurf[:])
    mask = distances > cutoff
    ind = np.nonzero(mask)[0]
    distances[ind] = cutoff
    mask = distances < 0  # -cutoff
    ind = np.nonzero(mask)[0]
    distances[ind] = 0  # cutoff
    base = self.helper.getObject(self.env.name + "distances_base")
    if base is None:
        base = self.helper.Sphere(self.env.name + "distances_base")[0]
    p = self.helper.getObject(self.env.name + "distances")
    if p is not None:
        self.helper.deleteObject(p)  # recursif?
    p = self.helper.newEmpty(self.env.name + "distances")
    # can use cube also


def displayDistanceCube(
    self,
    ramp_color1=[1, 0, 0],
    ramp_color2=[0, 0, 1],
    ramp_color3=None,
    cutoff=60.0,
):
    distances = np.array(self.env.grid.distToClosestSurf[:])
    mask = distances > cutoff
    ind = np.nonzero(mask)[0]
    distances[ind] = cutoff
    mask = distances < 0  # -cutoff
    ind = np.nonzero(mask)[0]
    distances[ind] = 0  # cutoff
    base = self.helper.getObject(self.env.name + "distances_base_cube")
    if base is None:
        #            base=self.helper.Sphere(self.env.name+"distances_base")[0]
        size = self.env.grid.gridSpacing
        base = self.helper.box(
            self.env.name + "distances_base_cube",
            center=[0.0, 0.0, 0.0],
            size=[size, size, size],
        )[0]
    parent_cube = self.helper.getObject(self.env.name + "distances_cubes")
    if parent_cube is not None:
        self.helper.deleteObject(parent_cube)  # recursif?
    parent_cube = self.helper.newEmpty(self.env.name + "distances_cubes")


def displayDistancePlane(
    self,
    ramp_color1=[1, 0, 0],
    ramp_color2=[0, 0, 1],
    ramp_color3=None,
    cutoff=60.0,
):
    # which axis ?
    distances = np.array(self.env.grid.distToClosestSurf[:])

    ramp = col.getRamp([ramp_color1, ramp_color2], size=255)  # color
    mask = distances > cutoff
    ind = np.nonzero(mask)[0]
    distances[ind] = cutoff
    mask = distances < 0  # -cutoff
    ind = np.nonzero(mask)[0]
    distances[ind] = 0  # cutoff
    newd = np.append(distances, cutoff)
    colors = map_colors(newd, ramp)[:-1]  # 1D array of the grid x,y,1
    autopack._colors = colors
    p = self.helper.getObject(self.env.name + "distances")
    if p is not None:
        self.helper.deleteObject(p)  # recursif?
    p = self.helper.newEmpty(self.env.name + "distances_p")

    d = np.array(self.env.grid.boundingBox[0]) - np.array(self.env.grid.boundingBox[1])
    p, mpl = self.helper.plane(
        self.env.name + "distances_plane",
        center=self.env.grid.getCenter(),
        size=[math.fabs(d[0]), math.fabs(d[1])],
        parent=p,
    )
    self.helper.rotateObj(p, [0, 0, -math.pi / 2.0])
    filename = (
        autopack.cache_results + os.sep + self.env.name + "distances_plane_texture.png"
    )
    c = colors.reshape(
        (
            self.env.grid.nbGridPoints[0],
            self.env.grid.nbGridPoints[1],
            self.env.grid.nbGridPoints[2],
            3,
        )
    )

    im = Image.fromstring(
        "RGB", (c.shape[0], c.shape[1]), np.uint8(c * 255.0).tostring()
    )
    im.save(str(filename))
    mat = self.helper.createTexturedMaterial(self.env.name + "planeMat", str(filename))
    # assign the material to the plane
    self.helper.assignMaterial(p, mat, texture=True)


def grabResultFromJSON(self, n):
    ingrrot = {}
    ingrpos = {}
    for i in range(n):
        with open("results_seed_" + str(i) + ".json") as data_file:
            data = json.load(data_file)
        for recipe in data:
            for ingrname in data[recipe]:
                for k in range(len(data[recipe][ingrname]["results"])):
                    if ingrname not in ingrrot:
                        ingrrot[ingrname] = []
                        ingrpos[ingrname] = []
                    ingrrot[ingrname].append(data[recipe][ingrname]["results"][k][1])
                    ingrpos[ingrname].append(data[recipe][ingrname]["results"][k][0])
    return ingrpos, ingrrot


def grabResultFromTXT(self, n, doanalyze=False):
    from autopack import transformation as t

    ingrrot = {}
    ingrpos = {}
    for i in range(1000):
        files = open("results_seed_" + str(i) + ".txt", "r")
        lines = files.readlines()
        files.close()
        for line in lines:
            line = line.replace("<", " ").replace(">", " ")
            elem = line.split()
            ingrname = elem[-5]
            if ingrname not in ingrrot:
                ingrrot[ingrname] = []
                ingrpos[ingrname] = []
            ingrrot[ingrname].append(eval(elem[2]))
            ingrpos[ingrname].append(eval(elem[0]))
    for ingrname in ingrrot:
        ingrrot[ingrname] = [np.array(m).reshape((4, 4)) for m in ingrrot[ingrname]]
    if doanalyze:
        for ingrname in ingrrot:
            eulers3 = [t.euler_from_matrix(m, "rxyz") for m in ingrrot[ingrname]]
            e3 = np.degrees(np.array(eulers3)).transpose()
            np.savetxt(
                ingrname + "_euler_X.csv",
                np.array(e3[0]),
                delimiter=",",
            )
            np.savetxt(
                ingrname + "_euler_Y.csv",
                np.array(e3[1]),
                delimiter=",",
            )
            np.savetxt(
                ingrname + "_euler_Z.csv",
                np.array(e3[2]),
                delimiter=",",
            )
            self.histogram(e3[0], ingrname + "_euler_X.png")
            self.histogram(e3[1], ingrname + "_euler_Y.png")
            self.histogram(e3[2], ingrname + "_euler_Z.png")
    return ingrpos, ingrrot


# should take any type of list...
def save_csv(self, data, filename=None):
    if filename is None:
        filename = "output.csv"
    resultFile = open(filename, "wb")
    wr = csv.writer(resultFile, dialect="excel")
    # wr.writerows(data) list of list ?
    # resultFile.close()
    for item in data:
        wr.writerow([item])
    resultFile.close()


def rectangle_circle_area(self, bbox, center, radius):
    # http://www.eex-dev.net/index.php?id=100
    # [[0.,0,0],[1000,1000,1]]
    # top,bottom, right, left
    #        rect=Rectangle(bbox[0][0],bbox[1][0],bbox[0][1],bbox[1][1])#top,bottom, right, left
    rect = Rectangle(
        bbox[1][1], bbox[0][1], bbox[1][0], bbox[0][0]
    )  # top,bottom, right, left
    m = [center[0], center[1]]
    r = radius
    area = math.pi * r**2
    chs = self.g.check_sphere_inside(rect, m, r)
    if chs:  # sph not completly inside
        ch = self.g.check_rectangle_oustide(rect, m, r)
        if ch:  # rectangle not outside
            leftBound, rightBound = self.g.getBoundary(rect, m, r)
            area = self.g.get_rectangle_cercle_area(rect, m, r, leftBound, rightBound)
        else:
            area = bbox[0][1] ** 2
    return area


def getVolumeShell(self, bbox, radii, center):
    # rectangle_circle_area
    volumes = []
    box_size0 = bbox[1][0] - bbox[0][0]
    for i in range(len(radii) - 1):
        r1 = radii[i]
        r2 = radii[i + 1]
        v1 = self.g.calc_volume(r1, box_size0 / 2.0)
        v2 = self.g.calc_volume(r2, box_size0 / 2.0)
        volumes.append(v2 - v1)
    return volumes


def rdf_3d(self, ingr):
    # see for intersection volume here http://crowsandcats.blogspot.com/2013/04/cube-sphere-intersection-volume.html
    # and here http://crowsandcats.blogspot.com/2013/05/extending-radial-distributions.html
    # will require scipy...worth it ?
    # should be pairewise distance ? or not ?
    distances = np.array(self.env.distances[ingr.name])
    basename = self.env.basename
    np.savetxt(
        basename + ingr.name + "_pos.csv",
        np.array(self.env.ingredient_positions[ingr.name]),
        delimiter=",",
    )
    self.histogram(distances, basename + ingr.name + "_histo.png")
    np.savetxt(
        basename + ingr.name + "_distances.csv",
        np.array(distances),
        delimiter=",",
    )
    # the bin should be not less than the biggest ingredient radius
    # b=int(distances.max()/self.largest)
    b = 100
    # bin_edges = np.arange(0, min(box_size) / 2, bin_width)
    new_rdf, edges = np.histogramdd(
        distances, bins=b, range=[(distances.min(), distances.max())]
    )
    radii = edges[0]
    # from http://isaacs.sourceforge.net/phys/rdfs.html
    dnr = new_rdf
    N = len(distances)
    V = (
        self.env.grid.nbGridPoints[0]
        * self.env.grid.nbGridPoints[1]
        * self.env.grid.nbGridPoints[2]
        * self.env.grid.gridSpacing**3
    )
    Vshell = np.array(self.getVolumeShell(self.bbox, radii, self.center))
    gr = (dnr * V) / (N * Vshell)
    np.savetxt(basename + ingr.name + "_rdf.csv", np.array(gr), delimiter=",")
    self.plot(gr, radii[:-1], basename + ingr.name + "_rdf.png")


def getAreaShell(self, bbox, radii, center):
    # rectangle_circle_area
    areas = []
    for i in range(len(radii) - 1):
        r1 = radii[i]
        r2 = radii[i + 1]
        area1 = self.rectangle_circle_area(bbox, center, r1)
        area2 = self.rectangle_circle_area(bbox, center, r2)
        if area1 == 0 or area2 == 0:
            areas.append(np.pi * (np.power(r2, 2) - np.power(r1, 2)))
        else:
            areas.append(area2 - area1)
    return areas


def ripley(self, positions, dr=25, rMax=None):
    # K(t) = A*SUM(wij*I(i,j)/n**2)
    # lambda = n/A A is the area of the region containing all points
    # I indicator function 1 if its operand is true, 0 otherwise
    # t is the search radius
    # if homogenous K(s) = pi*s**2
    # L(t) = (K(t)/pi)**1/2
    # A common plot is a graph of t - \hat{L}(t) against t
    # which will approximately follow the horizontal zero-axis with constant
    # dispersion if the data follow a homogeneous Poisson process.
    N = len(positions)
    V = 1000**2
    diag = np.sqrt(1000**2 + 1000**2)
    dr = dr  # all_distance.min()
    if rMax is None:
        rMax = diag
    edges = np.arange(dr, rMax + 1.1 * dr, dr)
    k = np.zeros((N, len(edges)))
    for i, p in enumerate(positions):
        di = distance.cdist(
            positions,
            [p],
            "euclidean",
        )
        # dV = np.array(analyse.getAreaShell(analyse.bbox,edges,p))
        for j, e in enumerate(edges):
            area0 = math.pi * e**2  # complete circle
            area1 = self.rectangle_circle_area(self.bbox, p, e)
            w = area1 / area0
            k[i, j] = w * len(np.nonzero(di < e)[0]) / N**2
    Kt = V * np.sum(k, axis=0)
    Lt = (Kt / np.pi) ** 0.5
    return Kt, Lt


def rdf(self, positions, dr=10, rMax=None):
    N = len(positions)
    V = 1000**2
    diag = np.sqrt(1000**2 + 1000**2)
    dr = dr  # all_distance.min()
    if rMax is None:
        rMax = diag
    edges = np.arange(0.0, rMax + 1.1 * dr, dr)
    g = np.zeros((N, len(edges) - 1))
    dv = []
    density = float(N) / float(V)
    for i, p in enumerate(positions):
        di = distance.cdist(
            positions,
            [p],
            "euclidean",
        )
        dN, bins = np.histogram(di, bins=edges)
        dV = np.array(self.getAreaShell(self.bbox, edges, p))
        dv.append(dV)
        g[i] = dN / (dV * density)
    avg = np.average(g, axis=0)  # /np.array(dv)
    return avg


def rdf_2d(self, ingr):
    # dN/N / dV/V = dN/dV * V/N
    distances = np.array(self.env.distances[ingr.name])
    basename = self.env.basename
    np.savetxt(
        basename + ingr.name + "_pos.csv",
        np.array(self.env.ingredient_positions[ingr.name]),
        delimiter=",",
    )
    self.histogram(distances, basename + ingr.name + "_histo.png")
    np.savetxt(
        basename + ingr.name + "_distances.csv",
        np.array(distances),
        delimiter=",",
    )
    # the bin should be not less than the biggest ingredient radius
    #        b=int(distances.max()/self.largest)
    new_rdf, edges = np.histogramdd(
        distances
    )  # , bins=b, range=[(distances.min(), distances.max())],normed=0)
    radii = edges[0]
    #        r=radii.tolist()
    #        r.insert(0,0.0)
    #        radii = np.array(r)
    #        rdf= new_rdf.tolist()
    #        rdf.insert(0,0)
    #        new_rdf = np.array(rdf)
    # from http://isaacs.sourceforge.net/phys/rdfs.html
    dnr = new_rdf[:]
    N = len(distances)
    V = (
        self.env.grid.nbGridPoints[0]
        * self.env.grid.nbGridPoints[1]
        * self.env.grid.gridSpacing**2
    )
    Vshell = np.array(self.getAreaShell(self.bbox, radii, self.center))
    #        print Vshell
    #        Vshell1 = np.pi*density*(np.power(radii[1:],2)-np.power(radii[:-1], 2))
    #        print Vshell1
    #        print radii
    gr = (dnr * V) / (N * Vshell)
    np.savetxt(basename + ingr.name + "_rdf.csv", np.array(gr), delimiter=",")
    self.plot(gr, radii[:-1], basename + ingr.name + "_rdf.png")
    # simpl approach Ni/Areai
    G = dnr / Vshell
    np.savetxt(
        basename + ingr.name + "_rdf_simple.csv",
        np.array(G),
        delimiter=",",
    )
    self.plot(
        np.array(G),
        radii[:-1],
        basename + ingr.name + "_rdf_simple.png",
    )


def correlation(self, ingr):
    basename = self.env.basename
    posxyz = np.array(self.env.ingredient_positions[ingr.name]).transpose()
    g_average, radii, x, y, z = self.PairCorrelationFunction_3D(posxyz, 1000, 900, 100)
    self.plot(g_average, radii, basename + ingr.name + "_corr.png")


def PairCorrelationFunction_3D(self, data, S, rMax, dr):
    """Compute the three-dimensional pair correlation function for a set of
    spherical particles contained in a cube with side length S. This simple
    function finds reference particles such that a sphere of radius rMax drawn
    around the particle will fit entirely within the cube, eliminating the need
    to compensate for edge effects. If no such particles exist, an error is
    returned. Try a smaller rMax...or write some code to handle edge effects! ;)
    Arguments:
    x an array of x positions of centers of particles
    y an array of y positions of centers of particles
    z an array of z positions of centers of particles
    S length of each side of the cube in space
    rMax outer diameter of largest spherical shell
    dr increment for increasing radius of spherical shell

    Returns a tuple: (g, radii, interior_x, interior_y, interior_z)
    g(r) a np array containing the correlation function g(r)
    radii a np array containing the radii of the
    spherical shells used to compute g(r)
    interior_x x coordinates of reference particles
    interior_y y coordinates of reference particles
    interior_z z coordinates of reference particles
    """
    x = data[0]
    y = data[1]
    z = data[2]
    # Find particles which are close enough to the cube center that a sphere of radius
    # rMax will not cross any face of the cube
    bools1 = x > rMax
    bools2 = x < (S - rMax)
    bools3 = y > rMax
    bools4 = y < (S - rMax)
    bools5 = z > rMax
    bools6 = z < (S - rMax)

    (interior_indices,) = np.where(bools1 * bools2 * bools3 * bools4 * bools5 * bools6)
    num_interior_particles = len(interior_indices)

    if num_interior_particles < 1:
        raise RuntimeError(
            "No particles found for which a sphere of radius rMax\
will lie entirely within a cube of side length S. Decrease rMax\
or increase the size of the cube."
        )

    edges = np.arange(0.0, rMax + 1.1 * dr, dr)
    num_increments = len(edges) - 1
    g = np.zeros([num_interior_particles, num_increments])
    radii = np.zeros(num_increments)
    numberDensity = len(x) / S**3

    # Compute pairwise correlation for each interior particle
    for p in range(num_interior_particles):
        index = interior_indices[p]
        d = np.sqrt((x[index] - x) ** 2 + (y[index] - y) ** 2 + (z[index] - z) ** 2)
        d[index] = 2 * rMax

        (result, bins) = np.histogram(d, bins=edges, normed=False)
        g[p, :] = result / numberDensity

    # Average g(r) for all interior particles and compute radii
    g_average = np.zeros(num_increments)
    for i in range(num_increments):
        radii[i] = (edges[i] + edges[i + 1]) / 2.0
        rOuter = edges[i + 1]
        rInner = edges[i]
        g_average[i] = np.average(g[:, i]) / (
            4.0 / 3.0 * np.pi * (rOuter**3 - rInner**3)
        )

    return (
        g_average,
        radii,
        x[interior_indices],
        y[interior_indices],
        z[interior_indices],
    )
    # Number of particles in shell/total number of particles/volume of shell/number density
    # shell volume = 4/3*pi(r_outer**3-r_inner**3)


def PairCorrelationFunction_2D(self, x, y, S, rMax, dr):
    """Compute the two-dimensional pair correlation function, also known
    as the radial distribution function, for a set of circular particles
    contained in a square region of a plane.  This simple function finds
    reference particles such that a circle of radius rMax drawn around the
    particle will fit entirely within the square, eliminating the need to
    compensate for edge effects.  If no such particles exist, an error is
    returned. Try a smaller rMax...or write some code to handle edge effects! ;)

    Arguments:
        x               an array of x positions of centers of particles
        y               an array of y positions of centers of particles
        S               length of each side of the square region of the plane
        rMax            outer diameter of largest annulus
        dr              increment for increasing radius of annulus

    Returns a tuple: (g, radii, interior_x, interior_y)
        g(r)            a np array containing the correlation function g(r)
        radii           a np array containing the radii of the
                        annuli used to compute g(r)
        interior_x      x coordinates of reference particles
        interior_y      y coordinates of reference particles
    """
    # Number of particles in ring/area of ring/number of reference particles/number density
    # area of ring = pi*(r_outer**2 - r_inner**2)
    # Find particles which are close enough to the box center that a circle of radius
    # rMax will not cross any edge of the box
    bools1 = x > 1.1 * rMax
    bools2 = x < (S - 1.1 * rMax)
    bools3 = y > rMax * 1.1
    bools4 = y < (S - rMax * 1.1)
    (interior_indices,) = np.where(bools1 * bools2 * bools3 * bools4)
    num_interior_particles = len(interior_indices)

    if num_interior_particles < 1:
        raise RuntimeError(
            "No particles found for which a circle of radius rMax\
                will lie entirely within a square of side length S.  Decrease rMax\
                or increase the size of the square."
        )

    edges = np.arange(0.0, rMax + 1.1 * dr, dr)
    num_increments = len(edges) - 1
    g = np.zeros([num_interior_particles, num_increments])
    radii = np.zeros(num_increments)
    numberDensity = len(x) / S**2

    # Compute pairwise correlation for each interior particle
    for p in range(num_interior_particles):
        index = interior_indices[p]
        d = np.sqrt((x[index] - x) ** 2 + (y[index] - y) ** 2)
        d[index] = 2 * rMax

        (result, bins) = np.histogram(d, bins=edges, normed=False)
        g[p, :] = result / numberDensity

    # Average g(r) for all interior particles and compute radii
    g_average = np.zeros(num_increments)
    for i in range(num_increments):
        radii[i] = (edges[i] + edges[i + 1]) / 2.0
        rOuter = edges[i + 1]
        rInner = edges[i]
        # divide by the area of sphere cut by sqyare
        g_average[i] = np.average(g[:, i]) / (np.pi * (rOuter**2 - rInner**2))

    return (g_average, radii, interior_indices)


def normalize_similarity_df(self, similarity_df):
    """
    Normalizes the similarity dataframe
    """
    dims_to_normalize = self.get_list_of_dims() + ["pairwise_distance"]
    for dim in dims_to_normalize:
        values = similarity_df.loc[:, dim].values
        normalized_values = (values - np.min(values)) / (
            np.max(values) - np.min(values)
        )
        normalized_values[np.isnan(normalized_values)] = 0
        similarity_df.loc[:, dim] = normalized_values
    return similarity_df


def calc_avg_similarity_values_for_dim(self, similarity_vals_for_dim):
    packing_inds = np.cumsum(
        np.hstack([0, self.num_seeds_per_packing])
    )  # returns the indices where packings start and end
    avg_similarity_values = -np.ones((self.num_packings, self.num_packings))

    for p1_id in range(self.num_packings):
        for p2_id in range(self.num_packings):
            if avg_similarity_values[p1_id, p2_id] >= 0:
                continue
            p1_inds = np.arange(
                packing_inds[p1_id], packing_inds[p1_id + 1]
            )  # indices corresponding to packing p1_id
            p2_inds = np.arange(packing_inds[p2_id], packing_inds[p2_id + 1])
            avg_similarity_values[p1_id, p2_id] = np.mean(
                similarity_vals_for_dim[p1_inds, p2_inds]
            )
            avg_similarity_values[p2_id, p1_id] = avg_similarity_values[p1_id, p2_id]
    return avg_similarity_values


def calc_similarity_df(self, all_objs, ingredient_key, save_path=None):
    """
    Calculates a dataframe of similarity values between packings
    """
    key_list = list(all_objs[ingredient_key].keys())
    similarity_df = pd.DataFrame(
        index=key_list,
        columns=pd.MultiIndex.from_product([self.get_list_of_dims(), key_list]),
        dtype=float,
    )
    similarity_df["packing_id"] = 0
    dims_to_calc = self.get_list_of_dims() + ["pairwise_distance"]
    for seed1, pos_dict1 in tqdm(all_objs[ingredient_key].items()):
        similarity_df.loc[seed1, "packing_id"] = seed1.split("_")[-1]
        for seed2, pos_dict2 in all_objs[ingredient_key].items():
            for dim in dims_to_calc:
                if dim == "pairwise_distance":
                    pos1 = np.array([pos_dict1["x"], pos_dict1["y"], pos_dict1["z"]])
                    pos2 = np.array([pos_dict2["x"], pos_dict2["y"], pos_dict2["z"]])
                    arr1 = distance.pdist(pos1.T)
                    arr2 = distance.pdist(pos2.T)
                else:
                    arr1 = pos_dict1[dim]
                    arr2 = pos_dict2[dim]

                min_dim = np.min([arr1.ravel(), arr2.ravel()])
                max_dim = np.max([arr1.ravel(), arr2.ravel()])
                arr1 = (arr1 - min_dim) / max_dim
                arr2 = (arr2 - min_dim) / max_dim

                if len(arr1) == 1 or len(arr2) == 1:
                    # cannot determine similarity when only one instance is packed
                    similarity_score = 0
                elif len(np.unique(arr1)) == 1 or len(np.unique(arr2)) == 1:
                    # if there is only one unique value, compare the value
                    if len(np.unique(arr1)) == 1 and len(np.unique(arr2)) == 1:
                        # both packings have only one unique value, compare the value
                        similarity_score = (
                            1 if np.unique(arr1) == np.unique(arr2) else 0
                        )
                    else:
                        # one of the packings has more than one unique value, cannot compare
                        similarity_score = 0
                else:
                    # anderson-darling test
                    # ad_stat = stats.anderson_ksamp([arr1, arr2])
                    # similarity_score = (ad_stat.significance_level - 0.001) / (
                    #     0.25 - 0.001
                    # )
                    # similarity_score = 1 - ad_stat.statistic

                    # 2 sample ks
                    ks_stat = stats.ks_2samp(arr1, arr2)
                    similarity_score = 1 - ks_stat.statistic
                    # similarity_score = ks_stat.pvalue

                    # histograms for bhattacharyya and jensen-shannon distances
                    # hist1, bin_edges1 = np.histogram(arr1, bins="auto", density=True)
                    # hist2, bin_edges2 = np.histogram(arr2, bins=bin_edges1, density=True)

                    # bhattacharyya distance
                    # similarity_score = np.sqrt(np.sum(np.sqrt(hist1 * hist2)))

                    # jensen-shannon distance
                    # similarity_score = 1 - distance.jensenshannon(arr1, arr2)

                similarity_df.loc[seed1, (dim, seed2)] = similarity_score

    similarity_df = self.normalize_similarity_df(similarity_df)
    if save_path is not None:
        dfpath = save_path / f"similarity_df_{ingredient_key}.csv"
        print(f"Saving similarity df to {dfpath}")
        similarity_df.to_csv(dfpath)

    return similarity_df


def plot_and_save_similarity_heatmaps(self, similarity_df, ingredient_key):
    """
    Plots heatmaps with hierarchical clustering using similarity scores
    """
    # accounting for changes when reading from csv
    if similarity_df["packing_id"].ndim > 1:
        packing_ids = similarity_df["packing_id"].iloc[:, 0]
    else:
        packing_ids = similarity_df["packing_id"]
    lut = dict(zip(packing_ids.unique(), sns.color_palette()))
    row_colors = packing_ids.map(lut)
    row_colors.rename("Packing ID", inplace=True)
    figdir = self.figures_path / "clustering"
    figdir.mkdir(parents=True, exist_ok=True)

    dims_to_calc = self.get_list_of_dims() + ["pairwise_distance"]
    for dim in dims_to_calc:
        avg_similarity_values = self.calc_avg_similarity_values_for_dim(
            similarity_df[dim].values
        )
        np.savetxt(
            figdir / f"avg_similarity_{ingredient_key}_{dim}.txt",
            avg_similarity_values,
        )

        row_linkage = hierarchy.linkage(
            1 - distance.squareform(similarity_df[dim], checks=False),
            method="ward",
            optimal_ordering=True,
        )

        g = sns.clustermap(
            similarity_df[dim],
            row_colors=row_colors,
            row_linkage=row_linkage,
            col_linkage=row_linkage,
            cbar_kws={"label": "similarity score"},
        )
        handles = [Patch(facecolor=lut[name]) for name in lut]
        plt.legend(
            handles,
            lut,
            title="Packing IDs",
            bbox_to_anchor=(1, 1),
            bbox_transform=plt.gcf().transFigure,
            loc="upper right",
        )
        g.ax_col_dendrogram.set_visible(False)
        g.ax_row_dendrogram.set_visible(False)
        g.ax_heatmap.set_xlabel(f"{ingredient_key}_{dim}")
        g.savefig(figdir / f"clustermap_{ingredient_key}_{dim}", dpi=300)


def run_similarity_analysis(
    self,
    all_objs,
    ingredient_key,
    save_heatmaps=False,
    recalculate=False,
):
    """
    TODO: add docs
    """
    print("Running similarity analysis...")

    if ingredient_key not in all_objs:
        raise ValueError(f"Missing ingredient: {ingredient_key}")

    dfpath = self.output_path / f"similarity_df_{ingredient_key}.csv"
    if dfpath.is_file() and not recalculate:
        print(f"Loading similarity values from {dfpath}")
        similarity_df = pd.read_csv(dfpath, header=[0, 1])
    else:
        similarity_df = self.calc_similarity_df(
            all_objs,
            ingredient_key=ingredient_key,
            save_path=self.output_path,
        )

    if save_heatmaps:
        self.plot_and_save_similarity_heatmaps(
            similarity_df,
            ingredient_key=ingredient_key,
        )

    return similarity_df


def calc_and_save_correlations(
    self,
    all_spilr_scaled,
    ingredient_key,
):
    key_list = [
        f"{pc}_{sc}"
        for pc in range(self.num_packings)
        for sc in range(self.num_seeds_per_packing[pc])
    ]
    corr_df = pd.DataFrame(
        index=key_list,
        columns=key_list,
        dtype=float,
    )
    corr_df["packing_id"] = np.nan
    for pc1 in range(self.num_packings):
        for sc1 in tqdm(range(self.num_seeds_per_packing[pc1])):
            for pc2 in range(self.num_packings):
                for sc2 in range(self.num_seeds_per_packing[pc2]):
                    corr_df.loc[f"{pc1}_{sc1}", "packing_id"] = pc1
                    # do not calculate if:
                    # a) already calculated
                    # b) calculating for same packing
                    if (not np.isnan(corr_df.loc[f"{pc1}_{sc1}", f"{pc2}_{sc2}"])) or (
                        (pc1 == pc2) and (sc1 == sc2)
                    ):
                        continue
                    corr_df.loc[f"{pc1}_{sc1}", f"{pc2}_{sc2}"] = matthews_corrcoef(
                        all_spilr_scaled[pc1, sc1].flatten(),
                        all_spilr_scaled[pc2, sc2].flatten(),
                    )
                    corr_df.loc[f"{pc2}_{sc2}", f"{pc1}_{sc1}"] = corr_df.loc[
                        f"{pc1}_{sc1}", f"{pc2}_{sc2}"
                    ]
    df_packing = corr_df.pop("packing_id")
    lut = dict(zip(df_packing.unique(), sns.color_palette()))
    row_colors = df_packing.map(lut)
    corr_df.fillna(0, inplace=True)
    g = sns.clustermap(
        corr_df,
        row_colors=row_colors,
        cbar_kws={"label": "spilr correlation"},
    )
    g.savefig(self.figures_path / f"spilr_correlation_{ingredient_key}.png", dpi=300)


def save_spilr_heatmap(self, input_dict, file_path, label_str=None):
    fig, ax = plt.subplots()
    g = sns.heatmap(
        input_dict,
        cbar=False,
        xticklabels=False,
        yticklabels=False,
        ax=ax,
    )
    g.set_xlabel("Angular coordinates")
    g.set_ylabel(label_str)
    g.invert_yaxis()

    fig.savefig(
        file_path,
        dpi=300,
    )
    plt.close()


def get_parametrized_representation(
    self,
    all_pos_list,
    ingredient_key=None,
    mesh_paths={},
    num_angular_points=64,
    save_plots=False,
    max_plots_to_save=1,
    get_correlations=False,
):
    print("creating parametrized representations...")

    if "inner" not in mesh_paths or "outer" not in mesh_paths:
        raise ValueError(
            "Missing mesh paths required to generate parametrized representations"
        )

    inner_mesh = trimesh.load_mesh(mesh_paths.get("inner"))
    outer_mesh = trimesh.load_mesh(mesh_paths.get("outer"))

    theta_vals = np.linspace(0, np.pi, 1 + num_angular_points)
    phi_vals = np.linspace(0, 2 * np.pi, 1 + 2 * num_angular_points)
    rad_vals = np.linspace(0, 1, 1 + num_angular_points)

    all_spilr = {}
    for scaled_val in ["raw", "scaled"]:
        all_spilr[scaled_val] = np.full(
            (
                self.num_packings,
                np.max(self.num_seeds_per_packing),
                len(rad_vals),
                len(theta_vals) * len(phi_vals),
            ),
            np.nan,
        )

    if save_plots:
        save_dir = self.figures_path / "spilr_heatmaps"
        os.makedirs(save_dir, exist_ok=True)

    for pc, (packing_id, packing_dict) in enumerate(
        zip(self.packing_id_dict.values(), all_pos_list)
    ):
        num_saved_plots = 0
        for sc, (_, pos_dict) in enumerate(packing_dict.items()):
            pos_list = np.array(pos_dict[ingredient_key])
            sph_pts = self.cartesian_to_sph(pos_list)

            (
                scaled_rad,
                distance_between_surfaces,
                inner_surface_distances,
            ) = MeshStore.calc_scaled_distances_for_positions(
                pos_list, inner_mesh, outer_mesh
            )

            trial_spilr = {}
            for scaled_val in ["raw", "scaled"]:
                rad_array = (
                    np.linspace(0, distance_between_surfaces.max(), len(rad_vals))
                    if scaled_val == "raw"
                    else rad_vals
                )

                trial_spilr[scaled_val] = np.zeros(
                    (len(rad_array), len(theta_vals), len(phi_vals))
                )

                max_rad = distance_between_surfaces.max() if scaled_val == "raw" else 1

                if np.any(rad_array > max_rad) or np.any(rad_array < 0):
                    raise ValueError("Check ray-mesh intersections!")

                rad_pos = inner_surface_distances if scaled_val == "raw" else scaled_rad
                rad_inds = np.digitize(rad_pos, rad_array) - 1
                theta_inds = np.digitize(sph_pts[:, 1], theta_vals) - 1
                phi_inds = np.digitize(sph_pts[:, 2], phi_vals) - 1

                trial_spilr[scaled_val][rad_inds, theta_inds, phi_inds] = 1

                all_spilr[scaled_val][pc, sc] = trial_spilr[scaled_val].reshape(
                    (len(rad_array), -1)
                )

                if save_plots and (num_saved_plots <= max_plots_to_save):
                    label_str = f"Distance from Nuclear Surface, {packing_id}_{sc}, {scaled_val}"
                    file_path = (
                        save_dir
                        / f"heatmap_{scaled_val}_{packing_id}_{sc}_{ingredient_key}"
                    )
                    self.save_spilr_heatmap(
                        all_spilr[scaled_val][pc, sc], file_path, label_str
                    )
                    num_saved_plots += 1

    if get_correlations:
        print("calculating correlations...")
        self.calc_and_save_correlations(
            all_spilr["scaled"],
            ingredient_key=ingredient_key,
        )

    if save_plots:
        for scaled_val in ["raw", "scaled"]:
            average_spilr = np.nanmean(all_spilr[scaled_val], axis=1)
            for pc, packing_id in enumerate(self.packing_id_dict.values()):
                label_str = (
                    f"Distance from Nuclear Surface, avg {packing_id}, {scaled_val}"
                )
                file_path = (
                    save_dir / f"avg_heatmap_{scaled_val}_{packing_id}_{ingredient_key}"
                )
                self.save_spilr_heatmap(average_spilr[pc], file_path, label_str)

    return all_spilr


def calcDistanceMatrixFastEuclidean2(self, nDimPoints):
    nDimPoints = np.array(nDimPoints)
    n, m = nDimPoints.shape
    delta = np.zeros((n, n), "d")
    for d in range(m):
        data = nDimPoints[:, d]
        delta += (data - data[:, np.newaxis]) ** 2
    return np.sqrt(delta)


def flush(self):
    import gc
    import pprint

    for i in range(2):
        print("Collecting %d ..." % i)
        n = gc.collect()
        print("Unreachable objects:", n)
        print("Remaining Garbage:")
        pprint.pprint(gc.garbage)
        del gc.garbage[:]


def merge(self, d1, d2, merge=lambda x, y: y):
    result = dict(d1)
    for k, v in d2.items():
        if k in result:
            result[k].extend(v)
        else:
            result[k] = v
    return result


def plotNResult2D(self, n, bbox=[[0.0, 0, 0.0], [1000.0, 1000.0, 1000.0]]):
    for i in range(n):
        f = "results_seed_" + str(i) + ".json"
        self.plot_one_result_2d(filename=f, bbox=bbox)


def plot_one_result_2d(
    self,
    data=None,
    filename=None,
    bbox=[[0.0, 0, 0.0], [1000.0, 1000.0, 1000.0]],
):
    if data is None and filename is None:
        return
    elif data is None and filename is not None:
        with open(filename) as data_file:
            data = json.load(data_file)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    radius = {}
    ingrrot = {}
    ingrpos = {}
    for recipe in data:
        for ingrname in data[recipe]:
            for k in range(len(data[recipe][ingrname]["results"])):
                if ingrname not in ingrrot:
                    ingrrot[ingrname] = []
                    ingrpos[ingrname] = []
                    radius[ingrname] = data[recipe][ingrname]["encapsulating_radius"]
                ingrrot[ingrname].append(data[recipe][ingrname]["results"][k][1])
                ingrpos[ingrname].append(data[recipe][ingrname]["results"][k][0])
    for ingr in ingrpos:
        for i, p in enumerate(ingrpos[ingr]):
            ax.add_patch(
                Circle(
                    (p[0], p[1]),
                    radius[ingr],
                    edgecolor="black",
                    facecolor="red",
                )
            )
        ax.set_aspect(1.0)
        plt.axhline(y=bbox[0][1], color="k")
        plt.axhline(y=bbox[1][1], color="k")
        plt.axvline(x=bbox[0][0], color="k")
        plt.axvline(x=bbox[1][0], color="k")
        plt.axis([bbox[0][0], bbox[1][0], bbox[0][1], bbox[1][1]])
        plt.savefig("plot" + ingr + ".png")
        plt.close()  # closes the current figure
    return


def one_exp(self, seed, output_path, eid=0, nmol=1, periodicity=True, dim=2):
    output = output_path + str(nmol)
    if periodicity:
        self.env.use_periodicity = True
        autopack.testPeriodicity = True
    else:
        self.env.use_periodicity = False
        autopack.testPeriodicity = False
    if dim == 3:
        autopack.biasedPeriodicity = [1, 1, 1]
    else:
        autopack.biasedPeriodicity = [1, 1, 0]
    if not os.path.exists(output):
        os.makedirs(output)

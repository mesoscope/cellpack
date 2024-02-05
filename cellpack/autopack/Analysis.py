# -*- coding: utf-8 -*-
"""
Created on Mon May  6 22:58:44 2013

@author: ludo
"""
import csv
import json
import math
import os
from pathlib import Path
from time import time

import matplotlib
import numpy
import pandas as pd
import seaborn as sns
import trimesh
from matplotlib import pyplot as plt
from matplotlib.patches import Circle, Patch
from mdutils.mdutils import MdUtils
from PIL import Image
from scipy import stats
from scipy.cluster import hierarchy
from scipy.spatial import distance
from sklearn.metrics import matthews_corrcoef
from tqdm import tqdm

import cellpack.autopack as autopack
from cellpack.autopack.GeometryTools import GeometryTools, Rectangle
from cellpack.autopack.ldSequence import halton
from cellpack.autopack.MeshStore import MeshStore
from cellpack.autopack.plotly_result import PlotlyAnalysis
from cellpack.autopack.upy import colors as col
from cellpack.autopack.upy.colors import map_colors
from cellpack.autopack.utils import check_paired_key, get_paired_key
from cellpack.autopack.writers import Writer
from cellpack.autopack.writers.ImageWriter import ImageWriter
import concurrent.futures
import multiprocessing


class Analysis:
    def __init__(
        self,
        env=None,
        viewer=None,
        result_file=None,
        packing_results_path=None,
        output_path=None,
    ):
        self.env = None
        self.smallest = 99999.0
        self.largest = 0.0
        if env:
            self.env = env
            self.smallest = env.smallestProteinSize
            self.largest = env.largestProteinSize
        self.afviewer = viewer
        self.helper = None
        if viewer:
            self.helper = self.afviewer.vi
        self.result_file = result_file
        self.center = [0, 0, 0]
        self.bbox = [[0, 0, 0], [1, 1, 1]]
        self.g = GeometryTools()
        self.g.Resolution = 1.0  # or grid step?
        self.current_pos = None
        self.current_distance = None
        self.plotly = PlotlyAnalysis()

        if packing_results_path is not None:
            self.packing_results_path = Path(packing_results_path)
        elif self.env is not None:
            self.packing_results_path = Path(self.env.out_folder)
        else:
            self.packing_results_path = Path()

        if output_path is not None:
            self.output_path = Path(output_path)
        elif self.env is not None:
            self.output_path = Path(self.env.out_folder)
        else:
            self.output_path = Path("out/")

        self.figures_path = self.output_path / "figures"
        self.figures_path.mkdir(parents=True, exist_ok=True)
        self.seed_to_results = {}
        autopack._colors = None

    @staticmethod
    def get_xyz_dict_from_all_pos_dict(all_pos_dict):
        """
        returns array of x, y, and z positions for each seed for runs
        in all_pos_dict
        """
        all_objs = {}
        for seed, object_dict in all_pos_dict.items():
            for obj, positions in object_dict.items():
                positions = numpy.array(positions)
                if obj not in all_objs:
                    all_objs[obj] = {}
                if seed not in all_objs[obj]:
                    all_objs[obj][seed] = {}
                for ct, dim in enumerate(["x", "y", "z"]):
                    all_objs[obj][seed][dim] = positions[:, ct]
        return all_objs

    @staticmethod
    def cartesian_to_sph(xyz, center=None):
        """
        Converts cartesian to spherical coordinates
        """
        if center is None:
            center = numpy.zeros(3)
        xyz = xyz - center
        sph_pts = numpy.zeros(xyz.shape)
        xy = xyz[:, 0] ** 2 + xyz[:, 1] ** 2
        sph_pts[:, 0] = numpy.sqrt(xy + xyz[:, 2] ** 2)
        sph_pts[:, 1] = numpy.arctan2(numpy.sqrt(xy), xyz[:, 2])
        sph_pts[:, 2] = numpy.arctan2(xyz[:, 1], xyz[:, 0])

        return sph_pts

    @staticmethod
    def get_list_of_dims():
        return ["x", "y", "z", "r", "theta", "phi"]

    @staticmethod
    def save_array_to_file(array_to_save, file_path, seed_index):
        f_handle = open(file_path, "a" if seed_index else "w")
        numpy.savetxt(
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

        if type(target) == list or type(target) == tuple:
            targetPos = target
        elif type(target) == str:
            o = self.helper.getObject(target)
            if o is not None:
                targetPos = self.helper.ToVec(self.helper.getTranslation(o))  # hostForm
        else:
            o = self.helper.getObject(target)
            if o is not None:
                targetPos = self.helper.ToVec(self.helper.getTranslation(o))  # hostForm
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

        delta = numpy.array(listCenters) - numpy.array(targetPos)
        delta *= delta
        distA = numpy.sqrt(delta.sum(1))
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
        listeDistance = numpy.zeros(len(listeCenters)) + 99999
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
        distances = numpy.array(self.env.grid.distToClosestSurf[:])
        mask = distances > cutoff
        ind = numpy.nonzero(mask)[0]
        distances[ind] = cutoff
        mask = distances < 0  # -cutoff
        ind = numpy.nonzero(mask)[0]
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
        distances = numpy.array(self.env.grid.distToClosestSurf[:])
        mask = distances > cutoff
        ind = numpy.nonzero(mask)[0]
        distances[ind] = cutoff
        mask = distances < 0  # -cutoff
        ind = numpy.nonzero(mask)[0]
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
        distances = numpy.array(self.env.grid.distToClosestSurf[:])

        ramp = col.getRamp([ramp_color1, ramp_color2], size=255)  # color
        mask = distances > cutoff
        ind = numpy.nonzero(mask)[0]
        distances[ind] = cutoff
        mask = distances < 0  # -cutoff
        ind = numpy.nonzero(mask)[0]
        distances[ind] = 0  # cutoff
        newd = numpy.append(distances, cutoff)
        colors = map_colors(newd, ramp)[:-1]  # 1D array of the grid x,y,1
        autopack._colors = colors
        p = self.helper.getObject(self.env.name + "distances")
        if p is not None:
            self.helper.deleteObject(p)  # recursif?
        p = self.helper.newEmpty(self.env.name + "distances_p")

        d = numpy.array(self.env.grid.boundingBox[0]) - numpy.array(
            self.env.grid.boundingBox[1]
        )
        p, mpl = self.helper.plane(
            self.env.name + "distances_plane",
            center=self.env.grid.getCenter(),
            size=[math.fabs(d[0]), math.fabs(d[1])],
            parent=p,
        )
        self.helper.rotateObj(p, [0, 0, -math.pi / 2.0])
        filename = (
            autopack.cache_results
            + os.sep
            + self.env.name
            + "distances_plane_texture.png"
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
            "RGB", (c.shape[0], c.shape[1]), numpy.uint8(c * 255.0).tostring()
        )
        im.save(str(filename))
        mat = self.helper.createTexturedMaterial(
            self.env.name + "planeMat", str(filename)
        )
        # assign the material to the plane
        self.helper.assignMaterial(p, mat, texture=True)

    def writeJSON(self, filename, data):
        with open(filename, "w") as fp:  # doesnt work with symbol link ?
            json.dump(
                data, fp, indent=4, separators=(",", ": ")
            )  # ,indent=4, separators=(',', ': ')

    def loadJSON(self, filename):
        with open(filename) as data_file:
            data = json.load(data_file)
        return data

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
                        ingrrot[ingrname].append(
                            data[recipe][ingrname]["results"][k][1]
                        )
                        ingrpos[ingrname].append(
                            data[recipe][ingrname]["results"][k][0]
                        )
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
            ingrrot[ingrname] = [
                numpy.array(m).reshape((4, 4)) for m in ingrrot[ingrname]
            ]
        if doanalyze:
            for ingrname in ingrrot:
                eulers3 = [t.euler_from_matrix(m, "rxyz") for m in ingrrot[ingrname]]
                e3 = numpy.degrees(numpy.array(eulers3)).transpose()
                numpy.savetxt(
                    ingrname + "_euler_X.csv",
                    numpy.array(e3[0]),
                    delimiter=",",
                )
                numpy.savetxt(
                    ingrname + "_euler_Y.csv",
                    numpy.array(e3[1]),
                    delimiter=",",
                )
                numpy.savetxt(
                    ingrname + "_euler_Z.csv",
                    numpy.array(e3[2]),
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
                area = self.g.get_rectangle_cercle_area(
                    rect, m, r, leftBound, rightBound
                )
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
        distances = numpy.array(self.env.distances[ingr.name])
        basename = self.env.basename
        numpy.savetxt(
            basename + ingr.name + "_pos.csv",
            numpy.array(self.env.ingredient_positions[ingr.name]),
            delimiter=",",
        )
        self.histogram(distances, basename + ingr.name + "_histo.png")
        numpy.savetxt(
            basename + ingr.name + "_distances.csv",
            numpy.array(distances),
            delimiter=",",
        )
        # the bin should be not less than the biggest ingredient radius
        # b=int(distances.max()/self.largest)
        b = 100
        # bin_edges = numpy.arange(0, min(box_size) / 2, bin_width)
        new_rdf, edges = numpy.histogramdd(
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
        Vshell = numpy.array(self.getVolumeShell(self.bbox, radii, self.center))
        gr = (dnr * V) / (N * Vshell)
        numpy.savetxt(basename + ingr.name + "_rdf.csv", numpy.array(gr), delimiter=",")
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
                areas.append(numpy.pi * (numpy.power(r2, 2) - numpy.power(r1, 2)))
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
        diag = numpy.sqrt(1000**2 + 1000**2)
        dr = dr  # all_distance.min()
        if rMax is None:
            rMax = diag
        edges = numpy.arange(dr, rMax + 1.1 * dr, dr)
        k = numpy.zeros((N, len(edges)))
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
                k[i, j] = w * len(numpy.nonzero(di < e)[0]) / N**2
        Kt = V * numpy.sum(k, axis=0)
        Lt = (Kt / numpy.pi) ** 0.5
        return Kt, Lt

    def rdf(self, positions, dr=10, rMax=None):
        N = len(positions)
        V = 1000**2
        diag = numpy.sqrt(1000**2 + 1000**2)
        dr = dr  # all_distance.min()
        if rMax is None:
            rMax = diag
        edges = numpy.arange(0.0, rMax + 1.1 * dr, dr)
        g = numpy.zeros((N, len(edges) - 1))
        dv = []
        density = float(N) / float(V)
        for i, p in enumerate(positions):
            di = distance.cdist(
                positions,
                [p],
                "euclidean",
            )
            dN, bins = numpy.histogram(di, bins=edges)
            dV = numpy.array(self.getAreaShell(self.bbox, edges, p))
            dv.append(dV)
            g[i] = dN / (dV * density)
        avg = numpy.average(g, axis=0)  # /np.array(dv)
        return avg

    def rdf_2d(self, ingr):
        # dN/N / dV/V = dN/dV * V/N
        distances = numpy.array(self.env.distances[ingr.name])
        basename = self.env.basename
        numpy.savetxt(
            basename + ingr.name + "_pos.csv",
            numpy.array(self.env.ingredient_positions[ingr.name]),
            delimiter=",",
        )
        self.histogram(distances, basename + ingr.name + "_histo.png")
        numpy.savetxt(
            basename + ingr.name + "_distances.csv",
            numpy.array(distances),
            delimiter=",",
        )
        # the bin should be not less than the biggest ingredient radius
        #        b=int(distances.max()/self.largest)
        new_rdf, edges = numpy.histogramdd(
            distances
        )  # , bins=b, range=[(distances.min(), distances.max())],normed=0)
        radii = edges[0]
        #        r=radii.tolist()
        #        r.insert(0,0.0)
        #        radii = numpy.array(r)
        #        rdf= new_rdf.tolist()
        #        rdf.insert(0,0)
        #        new_rdf = numpy.array(rdf)
        # from http://isaacs.sourceforge.net/phys/rdfs.html
        dnr = new_rdf[:]
        N = len(distances)
        V = (
            self.env.grid.nbGridPoints[0]
            * self.env.grid.nbGridPoints[1]
            * self.env.grid.gridSpacing**2
        )
        Vshell = numpy.array(self.getAreaShell(self.bbox, radii, self.center))
        #        print Vshell
        #        Vshell1 = numpy.pi*density*(numpy.power(radii[1:],2)-numpy.power(radii[:-1], 2))
        #        print Vshell1
        #        print radii
        gr = (dnr * V) / (N * Vshell)
        numpy.savetxt(basename + ingr.name + "_rdf.csv", numpy.array(gr), delimiter=",")
        self.plot(gr, radii[:-1], basename + ingr.name + "_rdf.png")
        # simpl approach Ni/Areai
        G = dnr / Vshell
        numpy.savetxt(
            basename + ingr.name + "_rdf_simple.csv",
            numpy.array(G),
            delimiter=",",
        )
        self.plot(
            numpy.array(G),
            radii[:-1],
            basename + ingr.name + "_rdf_simple.png",
        )

    def plot_position_distribution_total(self, all_positions):
        pos_xyz = numpy.array(all_positions)
        if pos_xyz.shape[0] <= 1:
            return
        pos_sph = self.cartesian_to_sph(pos_xyz)
        all_pos = numpy.hstack([pos_xyz, pos_sph])
        for ind, dim in enumerate(self.get_list_of_dims()):
            self.histogram(
                all_pos[:, ind],
                self.figures_path
                / f"all_ingredient_histo_{dim}_{self.env.basename}.png",
                title_str="all_ingredients",
                x_label=dim,
                y_label="count",
            )

    def plot_position_distribution(self, ingr):
        pos_xyz = numpy.array(self.env.ingredient_positions[ingr.name])
        if pos_xyz.shape[0] <= 1:
            return
        pos_sph = self.cartesian_to_sph(pos_xyz)
        all_pos = numpy.hstack([pos_xyz, pos_sph])
        for ind, dim in enumerate(self.get_list_of_dims()):
            self.histogram(
                all_pos[:, ind],
                self.figures_path / f"{ingr.name}_histo_{dim}_{self.env.basename}.png",
                title_str=ingr.name,
                x_label=dim,
                y_label="count",
            )

    def plot_occurence_distribution(self, ingr):
        occ = self.env.occurences[ingr.name]
        if len(occ) <= 1:
            return
        self.simpleplot(
            range(len(occ)),
            occ,
            self.figures_path
            / f"{ingr.name}_occurrence_{self.env.basename}_lineplot.png",
            title_str=ingr.name,
            x_label="seed",
            y_label="occurrences",
        )
        self.histogram(
            distances=numpy.array(occ),
            filename=self.figures_path
            / f"{ingr.name}_occurrence_{self.env.basename}_histo.png",
            title_str=ingr.name,
            x_label="occurrences",
            y_label="count",
        )

    def plot_distance_distribution(self, all_ingredient_distances):
        """
        Plots the distribution of distances for ingredient and pairs of ingredients
        """
        for ingr_key, distances in all_ingredient_distances.items():
            if len(distances) <= 1:
                continue
            self.histogram(
                distances=numpy.array(distances),
                filename=self.figures_path
                / f"{ingr_key}_pairwise_distances_{self.env.basename}.png",
                title_str=ingr_key,
                x_label="pairwise distance",
                y_label="count",
            )

    def correlation(self, ingr):
        basename = self.env.basename
        posxyz = numpy.array(self.env.ingredient_positions[ingr.name]).transpose()
        g_average, radii, x, y, z = self.PairCorrelationFunction_3D(
            posxyz, 1000, 900, 100
        )
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
        g(r) a numpy array containing the correlation function g(r)
        radii a numpy array containing the radii of the
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

        (interior_indices,) = numpy.where(
            bools1 * bools2 * bools3 * bools4 * bools5 * bools6
        )
        num_interior_particles = len(interior_indices)

        if num_interior_particles < 1:
            raise RuntimeError(
                "No particles found for which a sphere of radius rMax\
    will lie entirely within a cube of side length S. Decrease rMax\
    or increase the size of the cube."
            )

        edges = numpy.arange(0.0, rMax + 1.1 * dr, dr)
        num_increments = len(edges) - 1
        g = numpy.zeros([num_interior_particles, num_increments])
        radii = numpy.zeros(num_increments)
        numberDensity = len(x) / S**3

        # Compute pairwise correlation for each interior particle
        for p in range(num_interior_particles):
            index = interior_indices[p]
            d = numpy.sqrt(
                (x[index] - x) ** 2 + (y[index] - y) ** 2 + (z[index] - z) ** 2
            )
            d[index] = 2 * rMax

            (result, bins) = numpy.histogram(d, bins=edges, normed=False)
            g[p, :] = result / numberDensity

        # Average g(r) for all interior particles and compute radii
        g_average = numpy.zeros(num_increments)
        for i in range(num_increments):
            radii[i] = (edges[i] + edges[i + 1]) / 2.0
            rOuter = edges[i + 1]
            rInner = edges[i]
            g_average[i] = numpy.average(g[:, i]) / (
                4.0 / 3.0 * numpy.pi * (rOuter**3 - rInner**3)
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
            g(r)            a numpy array containing the correlation function g(r)
            radii           a numpy array containing the radii of the
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
        (interior_indices,) = numpy.where(bools1 * bools2 * bools3 * bools4)
        num_interior_particles = len(interior_indices)

        if num_interior_particles < 1:
            raise RuntimeError(
                "No particles found for which a circle of radius rMax\
                    will lie entirely within a square of side length S.  Decrease rMax\
                    or increase the size of the square."
            )

        edges = numpy.arange(0.0, rMax + 1.1 * dr, dr)
        num_increments = len(edges) - 1
        g = numpy.zeros([num_interior_particles, num_increments])
        radii = numpy.zeros(num_increments)
        numberDensity = len(x) / S**2

        # Compute pairwise correlation for each interior particle
        for p in range(num_interior_particles):
            index = interior_indices[p]
            d = numpy.sqrt((x[index] - x) ** 2 + (y[index] - y) ** 2)
            d[index] = 2 * rMax

            (result, bins) = numpy.histogram(d, bins=edges, normed=False)
            g[p, :] = result / numberDensity

        # Average g(r) for all interior particles and compute radii
        g_average = numpy.zeros(num_increments)
        for i in range(num_increments):
            radii[i] = (edges[i] + edges[i + 1]) / 2.0
            rOuter = edges[i + 1]
            rInner = edges[i]
            # divide by the area of sphere cut by sqyare
            g_average[i] = numpy.average(g[:, i]) / (
                numpy.pi * (rOuter**2 - rInner**2)
            )

        return (g_average, radii, interior_indices)

    def get_obj_dict(self, packing_results_path):
        """
        Returns the object dictionary from the input path folder.
        TODO: add description of object dictionary
        """
        file_list = Path(packing_results_path).glob("positions_*.json")
        all_pos_list = []
        packing_id_dict = {}
        for packing_index, file_path in enumerate(file_list):
            packing_id_dict[packing_index] = str(file_path).split("_")[-1].split(".")[0]
            with open(file_path, "r") as j:
                all_pos_list.append(json.loads(j.read()))

        all_objs = {}
        for packing_id, all_pos in zip(packing_id_dict.values(), all_pos_list):
            for seed, object_dict in all_pos.items():
                for obj, positions in object_dict.items():
                    positions = numpy.array(positions)
                    if obj not in all_objs:
                        all_objs[obj] = {}
                    seed_key = f"{seed}_{packing_id}"
                    if seed_key not in all_objs[obj]:
                        all_objs[obj][seed_key] = {}
                    for ct, dim in enumerate(["x", "y", "z"]):
                        all_objs[obj][seed_key][dim] = positions[:, ct]
                    sph_pts = self.cartesian_to_sph(positions)
                    for ct, dim in enumerate(["r", "theta", "phi"]):
                        all_objs[obj][seed_key][dim] = sph_pts[:, ct]
        self.all_objs = all_objs
        self.all_pos_list = all_pos_list
        self.packing_id_dict = packing_id_dict
        return all_objs, all_pos_list

    def get_minimum_expected_distance_from_recipe(self, recipe_data):
        """
        Returns 2x the smallest radius of objects in the recipe
        """
        return 2 * min(
            [val for val in self.get_ingredient_radii(recipe_data=recipe_data).values()]
        )

    def get_packed_minimum_distance(self, pairwise_distance_dict):
        """
        Returns the minimum distance between packed objects
        """
        return min(
            self.combine_results_from_ingredients(
                self.combine_results_from_seeds(pairwise_distance_dict)
            )
        )

    def get_number_of_ingredients_packed(
        self,
        ingredient_keys=None,
    ):
        """
        Returns the number of ingredients packed

        Parameters
        ----------
        ingredient_key: str
            ingredient key in self.all_pos_list
        """
        avg_num_packed = {}
        for ingr_key in ingredient_keys:
            ingredient_packing_dict = self.all_objs.get(ingr_key)
            if not ingredient_packing_dict:
                val = 0
            else:
                ingredients_packed = 0
                for packing_dict in ingredient_packing_dict.values():
                    ingredients_packed += len(packing_dict["r"])
                val = ingredients_packed / self.num_packings
            avg_num_packed[ingr_key] = val

        return avg_num_packed

    def get_ingredient_radii(
        self,
        recipe_data,
    ):
        """
        Returns the radii of ingredients packed

        Parameters
        ----------
        ingredient_key: str
            ingredient key in self.all_pos_list
        """
        ingredient_radii = {}
        for object_key, object_values in recipe_data.get("objects").items():
            if "radius" in object_values:
                ingredient_radii[object_key] = object_values["radius"]
        return ingredient_radii

    def get_dict_from_glob(
        self,
        glob_str,
    ):
        glob_to_distance_file = self.packing_results_path.glob(glob_str)
        for path_to_distance_file in glob_to_distance_file:
            if path_to_distance_file.is_file() and (
                path_to_distance_file.suffix == ".json"
            ):
                return self.loadJSON(path_to_distance_file)

    def run_distance_analysis(
        self,
        report_md,
        recipe_data,
        pairwise_distance_dict,
        figure_path,
        output_image_location,
    ):
        """
        Runs distance analysis on the given packing and adds it to
        the analysis report
        """
        expected_minimum_distance = self.get_minimum_expected_distance_from_recipe(
            recipe_data
        )
        if pairwise_distance_dict is not None:
            all_pairwise_distances = self.combine_results_from_seeds(
                pairwise_distance_dict
            )

            packed_minimum_distance = self.get_packed_minimum_distance(
                pairwise_distance_dict
            )

            report_md.new_header(level=1, title="Distance analysis")
            report_md.new_line(
                f"Expected minimum distance: {expected_minimum_distance:.2f}"
            )
            report_md.new_line(
                f"Actual minimum distance: {packed_minimum_distance:.2f}\n"
            )

            if expected_minimum_distance > packed_minimum_distance:
                report_md.new_header(
                    level=2, title="Possible errors", add_table_of_contents="n"
                )
                report_md.new_list(
                    [
                        f"Packed minimum distance {packed_minimum_distance:.2f}"
                        " is less than the "
                        f"expected minimum distance {expected_minimum_distance:.2f}\n"
                    ]
                )

            num_keys = len(all_pairwise_distances.keys())
            img_list = []
            for ingr_key in all_pairwise_distances:
                ingr_distance_histo_path = figure_path.glob(
                    f"{ingr_key}_pairwise_distances_*.png"
                )
                for img_path in ingr_distance_histo_path:
                    img_list.append(
                        report_md.new_inline_image(
                            text=f"Distance distribution {ingr_key}",
                            path=f"{output_image_location}/{img_path.name}",
                        )
                    )
            text_list = [
                "Ingredient key",
                "Pairwise distance distribution",
                *[
                    val
                    for pair in zip(all_pairwise_distances.keys(), img_list)
                    for val in pair
                ],
            ]

            report_md.new_table(
                columns=2, rows=(num_keys + 1), text=text_list, text_align="center"
            )

    def get_ingredient_key_from_object_or_comp_name(
        self, search_name, ingredient_key_dict
    ):
        """
        Returns the ingredient key if object or composition name is given
        """
        for ingredient_key, name_mappings in ingredient_key_dict.items():
            if search_name in name_mappings.values():
                return ingredient_key

    def get_partner_pair_dict(
        self,
        recipe_data,
        combined_pairwise_distance_dict,
        ingredient_radii,
        avg_num_packed,
    ):
        """
        Creates a partner pair dictionary as follows:
        {
            key_from_pairwise_distance_dict: {
                "binding_probability": value,
                "touching_radius": value,
            },
            ...
        }
        """
        partner_pair_dict = {}
        for ingredient_key, name_mappings in self.ingredient_key_dict.items():
            object_name = name_mappings["object_name"]
            if "partners" in recipe_data["objects"][object_name]:
                partner_list = recipe_data["objects"][object_name]["partners"]
                ingredient_radius = recipe_data["objects"][object_name]["radius"]
                for partner in partner_list.all_partners:
                    partner_object_name = partner.name
                    binding_probability = partner.binding_probability
                    partner_radius = recipe_data["objects"][partner_object_name][
                        "radius"
                    ]
                    partner_ingr_key = self.get_ingredient_key_from_object_or_comp_name(
                        partner_object_name, self.ingredient_key_dict
                    )
                    paired_key = get_paired_key(
                        combined_pairwise_distance_dict,
                        ingredient_key,
                        partner_ingr_key,
                    )
                    if paired_key not in partner_pair_dict:
                        partner_pair_dict[paired_key] = {
                            "binding_probability": binding_probability,
                            "touching_radius": ingredient_radius + partner_radius,
                            "num_packed": avg_num_packed[ingredient_key],
                        }

        return partner_pair_dict

    def run_partner_analysis(
        self,
        report_md,
        recipe_data,
        combined_pairwise_distance_dict,
        ingredient_radii,
        avg_num_packed,
    ):
        """
        runs an analysis of partner packings
        """
        partner_pair_dict = self.get_partner_pair_dict(
            recipe_data,
            combined_pairwise_distance_dict,
            ingredient_radii,
            avg_num_packed,
        )
        if len(partner_pair_dict):
            report_md.new_header(level=1, title="Partner Analysis")

            val_list = []
            for paired_key, partner_values in partner_pair_dict.items():
                pairwise_distances = numpy.array(
                    combined_pairwise_distance_dict[paired_key]
                )
                padded_radius = 1.2 * partner_values["touching_radius"]
                close_fraction = (
                    numpy.count_nonzero(pairwise_distances < padded_radius)
                    / partner_values["num_packed"]
                )
                val_list.extend(
                    [
                        paired_key,
                        partner_values["touching_radius"],
                        partner_values["binding_probability"],
                        close_fraction,
                    ]
                )

            text_list = [
                "Partner pair",
                "Touching radius",
                "Binding probability",
                "Close packed fraction",
                *val_list,
            ]
            report_md.new_table(
                columns=4,
                rows=(len(partner_pair_dict) + 1),
                text=text_list,
                text_align="center",
            )

    def create_report(
        self,
        recipe_data,
        ingredient_keys=None,
        report_output_path=None,
        output_image_location=None,
        run_distance_analysis=True,
        run_partner_analysis=True,
    ):
        """
        Creates a markdown file with various analyses included

        Parameters
        ----------
        self: AnalyseAP
            instance of AnalyseAP class
        recipe_data: dict
            dictionary containing recipe data for the packing being analyzed
        ingredient_keys: List[str]
            list of ingredient keys to analyze
        output_image_location: Path
            this is the path to look for output images for the markdown file
        run_*_analysis: bool
            whether to run specific analysis
        """
        if report_output_path is None:
            report_output_path = self.output_path
        report_output_path = Path(report_output_path)

        report_md = MdUtils(
            file_name=f"{report_output_path}/analysis_report",
            title="Packing analysis report",
        )
        report_md.new_header(
            level=2,
            title=f"Analysis for packing results located at {self.packing_results_path}",
            add_table_of_contents="n",
        )

        if not hasattr(self, "ingredient_key_dict"):
            self.ingredient_key_dict = self.get_dict_from_glob("ingredient_keys_*")

        if ingredient_keys is None:
            ingredient_keys = list(self.ingredient_key_dict.keys())

        avg_num_packed = self.get_number_of_ingredients_packed(
            ingredient_keys=ingredient_keys
        )
        ingredient_radii = self.get_ingredient_radii(recipe_data=recipe_data)

        if not hasattr(self, "pairwise_distance_dict"):
            self.pairwise_distance_dict = self.get_dict_from_glob(
                "pairwise_distances_*.json"
            )

        combined_pairwise_distance_dict = self.combine_results_from_seeds(
            self.pairwise_distance_dict
        )

        val_list = []
        for key, radius, num_packed in zip(
            ingredient_keys, ingredient_radii.values(), avg_num_packed.values()
        ):
            val_list.extend([key, radius, num_packed])
        text_list = [
            "Ingredient name",
            "Encapsulating radius",
            "Average number packed",
            *val_list,
        ]
        report_md.new_table(
            columns=3,
            rows=(len(ingredient_keys) + 1),
            text=text_list,
            text_align="center",
        )

        # path to save report and other outputs
        if output_image_location is None:
            output_image_location = self.output_path

        # path where packing results are stored
        packing_results_path = self.packing_results_path
        figure_path = packing_results_path / "figures"

        report_md.new_header(level=1, title="Packing image")
        glob_to_packing_image = figure_path.glob("packing_image_*.png")
        for img_path in glob_to_packing_image:
            report_md.new_line(
                report_md.new_inline_image(
                    text="Packing image",
                    path=f"{output_image_location}/{img_path.name}",
                )
            )
        report_md.new_line("")

        if run_distance_analysis:
            # TODO: take packing distance dict as direct input for live mode
            self.run_distance_analysis(
                report_md,
                recipe_data,
                self.pairwise_distance_dict,
                figure_path,
                output_image_location,
            )

        if run_partner_analysis:
            self.run_partner_analysis(
                report_md,
                recipe_data,
                combined_pairwise_distance_dict,
                ingredient_radii,
                avg_num_packed,
            )

        report_md.create_md_file()

    def run_analysis_workflow(
        self,
        analysis_config: dict,
        recipe_data: dict,
    ):
        all_objs, all_pos_list = self.get_obj_dict(self.packing_results_path)

        self.num_packings = len(all_pos_list)
        self.num_seeds_per_packing = numpy.array(
            [len(packing_dict) for packing_dict in all_pos_list]
        )

        print("Starting analysis workflow...")

        if analysis_config.get("similarity_analysis"):
            self.run_similarity_analysis(
                all_objs, **analysis_config["similarity_analysis"]
            )

        if analysis_config.get("parametrized_representation"):
            self.get_parametrized_representation(
                all_pos_list=all_pos_list,
                **analysis_config["parametrized_representation"],
            )

        if analysis_config.get("create_report"):
            self.create_report(
                recipe_data=recipe_data,
                **analysis_config["create_report"],
            )

    def normalize_similarity_df(self, similarity_df):
        """
        Normalizes the similarity dataframe
        """
        dims_to_normalize = self.get_list_of_dims() + ["pairwise_distance"]
        for dim in dims_to_normalize:
            values = similarity_df.loc[:, dim].values
            normalized_values = (values - numpy.min(values)) / (
                numpy.max(values) - numpy.min(values)
            )
            normalized_values[numpy.isnan(normalized_values)] = 0
            similarity_df.loc[:, dim] = normalized_values
        return similarity_df

    def calc_avg_similarity_values_for_dim(self, similarity_vals_for_dim):
        packing_inds = numpy.cumsum(
            numpy.hstack([0, self.num_seeds_per_packing])
        )  # returns the indices where packings start and end
        avg_similarity_values = -numpy.ones((self.num_packings, self.num_packings))

        for p1_id in range(self.num_packings):
            for p2_id in range(self.num_packings):
                if avg_similarity_values[p1_id, p2_id] >= 0:
                    continue
                p1_inds = numpy.arange(
                    packing_inds[p1_id], packing_inds[p1_id + 1]
                )  # indices corresponding to packing p1_id
                p2_inds = numpy.arange(packing_inds[p2_id], packing_inds[p2_id + 1])
                avg_similarity_values[p1_id, p2_id] = numpy.mean(
                    similarity_vals_for_dim[p1_inds, p2_inds]
                )
                avg_similarity_values[p2_id, p1_id] = avg_similarity_values[
                    p1_id, p2_id
                ]
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
                        pos1 = numpy.array(
                            [pos_dict1["x"], pos_dict1["y"], pos_dict1["z"]]
                        )
                        pos2 = numpy.array(
                            [pos_dict2["x"], pos_dict2["y"], pos_dict2["z"]]
                        )
                        arr1 = distance.pdist(pos1.T)
                        arr2 = distance.pdist(pos2.T)
                    else:
                        arr1 = pos_dict1[dim]
                        arr2 = pos_dict2[dim]

                    min_dim = numpy.min([arr1.ravel(), arr2.ravel()])
                    max_dim = numpy.max([arr1.ravel(), arr2.ravel()])
                    arr1 = (arr1 - min_dim) / max_dim
                    arr2 = (arr2 - min_dim) / max_dim

                    if len(arr1) == 1 or len(arr2) == 1:
                        # cannot determine similarity when only one instance is packed
                        similarity_score = 0
                    elif len(numpy.unique(arr1)) == 1 or len(numpy.unique(arr2)) == 1:
                        # if there is only one unique value, compare the value
                        if (
                            len(numpy.unique(arr1)) == 1
                            and len(numpy.unique(arr2)) == 1
                        ):
                            # both packings have only one unique value, compare the value
                            similarity_score = (
                                1 if numpy.unique(arr1) == numpy.unique(arr2) else 0
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
                        # hist1, bin_edges1 = numpy.histogram(arr1, bins="auto", density=True)
                        # hist2, bin_edges2 = numpy.histogram(arr2, bins=bin_edges1, density=True)

                        # bhattacharyya distance
                        # similarity_score = numpy.sqrt(numpy.sum(numpy.sqrt(hist1 * hist2)))

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
            numpy.savetxt(
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
        corr_df["packing_id"] = numpy.nan
        for pc1 in range(self.num_packings):
            for sc1 in tqdm(range(self.num_seeds_per_packing[pc1])):
                for pc2 in range(self.num_packings):
                    for sc2 in range(self.num_seeds_per_packing[pc2]):
                        corr_df.loc[f"{pc1}_{sc1}", "packing_id"] = pc1
                        # do not calculate if:
                        # a) already calculated
                        # b) calculating for same packing
                        if (
                            not numpy.isnan(corr_df.loc[f"{pc1}_{sc1}", f"{pc2}_{sc2}"])
                        ) or ((pc1 == pc2) and (sc1 == sc2)):
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
        g.savefig(
            self.figures_path / f"spilr_correlation_{ingredient_key}.png", dpi=300
        )

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

        theta_vals = numpy.linspace(0, numpy.pi, 1 + num_angular_points)
        phi_vals = numpy.linspace(0, 2 * numpy.pi, 1 + 2 * num_angular_points)
        rad_vals = numpy.linspace(0, 1, 1 + num_angular_points)

        all_spilr = {}
        for scaled_val in ["raw", "scaled"]:
            all_spilr[scaled_val] = numpy.full(
                (
                    self.num_packings,
                    numpy.max(self.num_seeds_per_packing),
                    len(rad_vals),
                    len(theta_vals) * len(phi_vals),
                ),
                numpy.nan,
            )

        if save_plots:
            save_dir = self.figures_path / "spilr_heatmaps"
            os.makedirs(save_dir, exist_ok=True)

        for pc, (packing_id, packing_dict) in enumerate(
            zip(self.packing_id_dict.values(), all_pos_list)
        ):
            num_saved_plots = 0
            for sc, (_, pos_dict) in enumerate(packing_dict.items()):
                pos_list = numpy.array(pos_dict[ingredient_key])
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
                        numpy.linspace(
                            0, distance_between_surfaces.max(), len(rad_vals)
                        )
                        if scaled_val == "raw"
                        else rad_vals
                    )

                    trial_spilr[scaled_val] = numpy.zeros(
                        (len(rad_array), len(theta_vals), len(phi_vals))
                    )

                    max_rad = (
                        distance_between_surfaces.max() if scaled_val == "raw" else 1
                    )

                    if numpy.any(rad_array > max_rad) or numpy.any(rad_array < 0):
                        raise ValueError("Check ray-mesh intersections!")

                    rad_pos = (
                        inner_surface_distances if scaled_val == "raw" else scaled_rad
                    )
                    rad_inds = numpy.digitize(rad_pos, rad_array) - 1
                    theta_inds = numpy.digitize(sph_pts[:, 1], theta_vals) - 1
                    phi_inds = numpy.digitize(sph_pts[:, 2], phi_vals) - 1

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
                average_spilr = numpy.nanmean(all_spilr[scaled_val], axis=1)
                for pc, packing_id in enumerate(self.packing_id_dict.values()):
                    label_str = (
                        f"Distance from Nuclear Surface, avg {packing_id}, {scaled_val}"
                    )
                    file_path = (
                        save_dir
                        / f"avg_heatmap_{scaled_val}_{packing_id}_{ingredient_key}"
                    )
                    self.save_spilr_heatmap(average_spilr[pc], file_path, label_str)

        return all_spilr

    def histogram(self, distances, filename, title_str="", x_label="", y_label=""):
        plt.clf()
        # calculate histogram
        nbins = int(numpy.sqrt(len(distances)))
        if nbins < 2:
            return
        y, bin_edges = numpy.histogram(distances, bins=nbins)
        bincenters = 0.5 * (bin_edges[1:] + bin_edges[:-1])

        # calculate standard error for values in each bin
        bin_inds = numpy.digitize(distances, bin_edges)
        x_err_vals = numpy.zeros(y.shape)
        for bc in range(nbins):
            dist_vals = distances[bin_inds == (bc + 1)]
            if len(dist_vals) > 1:
                x_err_vals[bc] = numpy.std(dist_vals)
            else:
                x_err_vals[bc] = 0
        y_err_vals = numpy.sqrt(y * (1 - y / numpy.sum(y)))
        # set bin width
        dbin = 0.9 * (bincenters[1] - bincenters[0])
        plt.bar(bincenters, y, width=dbin, color="r", xerr=x_err_vals, yerr=y_err_vals)
        plt.title(title_str)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.savefig(filename)
        plt.close()

    def plot(self, rdf, radii, file_name):
        plt.clf()
        matplotlib.rc("font", size=14)
        matplotlib.rc("figure", figsize=(5, 4))
        #        plt.clf()
        plt.plot(radii, rdf, linewidth=3)
        plt.xlabel(r"distance $r$ in $\AA$")
        plt.ylabel(r"radial distribution function $g(r)$")
        plt.savefig(file_name)

    def simpleplot(self, X, Y, filename, w=3, title_str="", x_label="", y_label=""):
        plt.clf()
        plt.plot(X, Y, linewidth=w)
        plt.title(title_str)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.savefig(filename)

    def build_grid(
        self,
    ):
        t1 = time()
        self.env.buildGrid()
        t2 = time()
        gridTime = t2 - t1
        print(f"time to build grid: {gridTime:0.2f}")

    def pack(
        self,
        seed=20,
        show_plotly_plot=True,
    ):
        if show_plotly_plot:
            self.plotly.update_title(self.env.place_method)

        t1 = time()
        results = self.env.pack_grid(seedNum=seed)
        self.seed_to_results[seed] = results
        t2 = time()
        run_time = t2 - t1
        print(f"time to run pack_grid for {self.env.place_method}: {run_time:0.2f}")
        print(f"num placed: {len(self.env.packed_objects.get_ingredients())}")
        if show_plotly_plot:
            min_bound, max_bound = self.env.get_bounding_box_limits()
            width = max_bound - min_bound
            self.plotly.plot["data"] = []
            self.plotly.plot.layout.shapes = ()
            self.plotly.plot.update_xaxes(
                range=[min_bound[0] - 0.2 * width[0], max_bound[0] + 0.2 * width[0]]
            )
            self.plotly.plot.update_yaxes(
                range=[min_bound[1] - 0.2 * width[1], max_bound[1] + 0.2 * width[1]]
            )
            self.plotly.update_title(
                f"{self.env.place_method} took {str(round(t2 - t1, 2))}s, packed {len(self.env.packed_objects.get_ingredients())}"
            )
            self.plotly.make_grid_heatmap(self.env)
            self.plotly.add_ingredient_positions(self.env)
            self.plotly.show()

    def calcDistanceMatrixFastEuclidean2(self, nDimPoints):
        nDimPoints = numpy.array(nDimPoints)
        n, m = nDimPoints.shape
        delta = numpy.zeros((n, n), "d")
        for d in range(m):
            data = nDimPoints[:, d]
            delta += (data - data[:, numpy.newaxis]) ** 2
        return numpy.sqrt(delta)

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
                        radius[ingrname] = data[recipe][ingrname][
                            "encapsulating_radius"
                        ]
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
        return ingrpos

    def set_ingredient_color(self, ingr):
        """
        Sets the color of an ingredient
        """
        color = None

        if ingr.color is not None:
            color = (
                ingr.color
                if all([x <= 1 for x in ingr.color])
                else numpy.array(ingr.color) / 255
            )

        return color

    def add_ingredient_positions_to_plot(
        self, ax, ingr, color, seed_index, ingredient_position_dict, width
    ):
        """
        Adds 2D images of ingredient positions to axis
        """
        seed_ingredient_positions = ingredient_position_dict[seed_index][ingr.name]
        for i, pos in enumerate(seed_ingredient_positions):
            ax.add_patch(
                Circle(
                    (pos[0], pos[1]),
                    ingr.encapsulating_radius,
                    edgecolor="black",
                    facecolor=color,
                )
            )

            #  Plot "image" particles to verify that periodic boundary conditions are working
            radius = ingr.encapsulating_radius
            if autopack.testPeriodicity:
                if pos[0] < radius:
                    ax.add_patch(
                        Circle(
                            (pos[0] + width[0], pos[1]),
                            radius,
                            facecolor=color,
                        )
                    )
                elif pos[0] > (width[0] - radius):
                    ax.add_patch(
                        Circle(
                            (pos[0] - width[0], pos[1]),
                            radius,
                            facecolor=color,
                        )
                    )
                if pos[1] < radius:
                    ax.add_patch(
                        Circle(
                            (pos[0], pos[1] + width[1]),
                            radius,
                            facecolor=color,
                        )
                    )
                elif pos[1] > (width[1] - radius):
                    ax.add_patch(
                        Circle(
                            (pos[0], pos[1] - width[1]),
                            radius,
                            facecolor=color,
                        )
                    )

            if i == 0:  # len(ingrpos)-1:
                continue

            if ingr.type == "Grow":
                plt.plot(
                    [
                        seed_ingredient_positions[-i][0],
                        seed_ingredient_positions[-i - 1][0],
                    ],
                    [
                        seed_ingredient_positions[-i][1],
                        seed_ingredient_positions[-i - 1][1],
                    ],
                    "k-",
                    lw=2,
                )
                # plot the sphere
                if ingr.use_rbsphere:
                    (ext_recipe, pts,) = ingr.getInterpolatedSphere(
                        seed_ingredient_positions[-i - 1],
                        seed_ingredient_positions[-i],
                    )
                    for pt in pts:
                        ax.add_patch(
                            Circle(
                                (pt[0], pt[1]),
                                ingr.min_radius,
                                edgecolor="black",
                                facecolor=color,
                            )
                        )
        return ax

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

    def getHaltonUnique(self, n):
        seeds_f = numpy.array(halton(int(n * 1.5))) * int(n * 1.5)
        seeds_int = numpy.array(numpy.round(seeds_f), "int")
        _, indices_u = numpy.unique(seeds_int, return_index=True)
        seeds_i = numpy.array(seeds_int[numpy.sort(indices_u)])[:n]
        return seeds_i

    def update_distance_distribution_dictionaries(
        self,
        ingr,
        center_distance_dict,
        pairwise_distance_dict,
        ingredient_position_dict,
        ingredient_angle_dict,
        ingredient_occurence_dict,
        seed_index,
        center,
    ):
        """
        Update dictionaries that store distance and angle information
        """
        if ingr.name not in center_distance_dict[seed_index]:
            center_distance_dict[seed_index][ingr.name] = []
            pairwise_distance_dict[seed_index][ingr.name] = []
            ingredient_position_dict[seed_index][ingr.name] = []
            ingredient_angle_dict[seed_index][ingr.name] = []
            ingredient_occurence_dict[seed_index][ingr.name] = []

        get_angles = False
        if ingr.packing_mode == "gradient" and self.env.use_gradient:
            self.center = center = self.env.gradients[ingr.gradient].mode_settings.get(
                "center", center
            )
            get_angles = True

        # get angles wrt gradient
        (
            seed_ingredient_positions,
            seed_distances_from_center,
            seed_distances_between_ingredients,
            seed_angles,
        ) = self.env.get_distances_and_angles(ingr.name, center, get_angles=get_angles)

        center_distance_dict[seed_index][
            ingr.name
        ] = seed_distances_from_center.tolist()
        pairwise_distance_dict[seed_index][
            ingr.name
        ] = seed_distances_between_ingredients.tolist()
        ingredient_position_dict[seed_index][
            ingr.name
        ] = seed_ingredient_positions.tolist()
        ingredient_angle_dict[seed_index][ingr.name] = seed_angles.tolist()
        ingredient_occurence_dict[seed_index][ingr.name].append(
            len(seed_ingredient_positions)
        )

        return (
            center_distance_dict,
            pairwise_distance_dict,
            ingredient_position_dict,
            ingredient_angle_dict,
            ingredient_occurence_dict,
        )

    def update_crosswise_distances(
        self, ingr, recipe, pairwise_distance_dict, seed_index
    ):
        """
        Adds cross-ingredient distances for pairwise distance dictionary
        """
        for ingr2 in recipe.ingredients:
            if ingr2.name == ingr.name:
                continue
            if not check_paired_key(
                pairwise_distance_dict[seed_index],
                ingr.name,
                ingr2.name,
            ):
                pairwise_distance_dict[seed_index][
                    f"{ingr.name}_{ingr2.name}"
                ] = self.env.calc_pairwise_distances(ingr.name, ingr2.name).tolist()

        return pairwise_distance_dict

    def process_ingredients_in_recipe(
        self,
        recipe,
        center_distance_dict,
        pairwise_distance_dict,
        ingredient_position_dict,
        ingredient_angle_dict,
        ingredient_occurence_dict,
        ingredient_key_dict,
        seed_index,
        center,
        ax,
        plot_figures,
        two_d,
        width,
    ):
        """
        Updates distance/angle dictionaries and creates plots for ingredients in recipe
        """
        for ingr in recipe.ingredients:
            # set ingredient color
            color = self.set_ingredient_color(ingr)

            if ingr.name not in ingredient_key_dict:
                ingredient_key_dict[ingr.name] = {}
                ingredient_key_dict[ingr.name][
                    "composition_name"
                ] = ingr.composition_name
                ingredient_key_dict[ingr.name]["object_name"] = ingr.object_name

            # calculate distances and angles for ingredient
            (
                center_distance_dict,
                pairwise_distance_dict,
                ingredient_position_dict,
                ingredient_angle_dict,
                ingredient_occurence_dict,
            ) = self.update_distance_distribution_dictionaries(
                ingr,
                center_distance_dict,
                pairwise_distance_dict,
                ingredient_position_dict,
                ingredient_angle_dict,
                ingredient_occurence_dict,
                seed_index,
                center,
            )

            # calculate cross ingredient_distances
            pairwise_distance_dict = self.update_crosswise_distances(
                ingr, recipe, pairwise_distance_dict, seed_index
            )

            if plot_figures and two_d:
                ax = self.add_ingredient_positions_to_plot(
                    ax,
                    ingr,
                    color,
                    seed_index,
                    ingredient_position_dict,
                    width,
                )

        return (
            center_distance_dict,
            pairwise_distance_dict,
            ingredient_position_dict,
            ingredient_angle_dict,
            ingredient_occurence_dict,
            ingredient_key_dict,
            ax,
        )

    def combine_results_from_seeds(self, input_dict):
        """
        Combines results from multiple seeds into one dictionary
        Dictionary keys are ingredient names
        """
        output_dict = {}
        for seed_index, ingr_dict in input_dict.items():
            for ingr_name, value_list in ingr_dict.items():
                if ingr_name not in output_dict:
                    output_dict[ingr_name] = []
                output_dict[ingr_name].extend(value_list)

        return output_dict

    def combine_results_from_ingredients(self, input_dict):
        """
        Combines results from multiple ingredients into one list
        """
        output_list = []
        for ingr_name, value_list in input_dict.items():
            output_list.extend(value_list)
        return output_list

    def pack_one_seed(
        self,
        seed_index,
        seed_list,
        bounding_box,
        center_distance_dict=None,
        pairwise_distance_dict=None,
        ingredient_position_dict=None,
        ingredient_angle_dict=None,
        ingredient_occurence_dict=None,
        ingredient_key_dict=None,
        get_distance_distribution=False,
        image_export_options=None,
        show_grid=False,
        plot_figures=False,
        save_gradient_data_as_image=False,
    ):
        """
        Packs one seed of a recipe and returns the recipe object
        """
        seed = int(seed_list[seed_index])
        seed_basename = self.env.add_seed_number_to_base_name(seed)
        # Clear
        if self.afviewer:
            self.afviewer.clearFill("Test_Spheres2D")
        else:
            self.env.reset()
        self.env.saveResult = True
        numpy.random.seed(seed)
        self.build_grid()
        two_d = self.env.is_two_d()
        use_simularium = False
        self.pack(
            seed=seed,
            # TODO: fix this to disable plotly if using simularium
            show_plotly_plot=(show_grid and two_d) and not use_simularium,
        )

        self.center = self.env.grid.getCenter()

        ax = None
        width = 0
        if plot_figures and two_d:
            width = self.env.get_size_of_bounding_box()
            fig = plt.figure()
            ax = fig.add_subplot(111)

        if get_distance_distribution:
            center_distance_dict[seed_index] = {}
            pairwise_distance_dict[seed_index] = {}
            ingredient_position_dict[seed_index] = {}
            ingredient_angle_dict[seed_index] = {}
            ingredient_occurence_dict[seed_index] = {}

            if hasattr(self, "center"):
                center = self.center
            else:
                center = self.env.grid.getCenter()  # center of the grid

            ext_recipe = self.env.exteriorRecipe
            if ext_recipe:
                (
                    center_distance_dict,
                    pairwise_distance_dict,
                    ingredient_position_dict,
                    ingredient_angle_dict,
                    ingredient_occurence_dict,
                    ingredient_key_dict,
                    ax,
                ) = self.process_ingredients_in_recipe(
                    recipe=ext_recipe,
                    center_distance_dict=center_distance_dict,
                    pairwise_distance_dict=pairwise_distance_dict,
                    ingredient_position_dict=ingredient_position_dict,
                    ingredient_angle_dict=ingredient_angle_dict,
                    ingredient_occurence_dict=ingredient_occurence_dict,
                    ingredient_key_dict=ingredient_key_dict,
                    seed_index=seed_index,
                    center=center,
                    ax=ax,
                    plot_figures=plot_figures,
                    two_d=two_d,
                    width=width,
                )

            for comparment in self.env.compartments:
                surface_recipe = comparment.surfaceRecipe
                if surface_recipe:
                    (
                        center_distance_dict,
                        pairwise_distance_dict,
                        ingredient_position_dict,
                        ingredient_angle_dict,
                        ingredient_occurence_dict,
                        ingredient_key_dict,
                        ax,
                    ) = self.process_ingredients_in_recipe(
                        recipe=surface_recipe,
                        center_distance_dict=center_distance_dict,
                        pairwise_distance_dict=pairwise_distance_dict,
                        ingredient_position_dict=ingredient_position_dict,
                        ingredient_angle_dict=ingredient_angle_dict,
                        ingredient_occurence_dict=ingredient_occurence_dict,
                        ingredient_key_dict=ingredient_key_dict,
                        seed_index=seed_index,
                        center=center,
                        ax=ax,
                        plot_figures=plot_figures,
                        two_d=two_d,
                        width=width,
                    )

                inner_recipe = comparment.innerRecipe
                if inner_recipe:
                    (
                        center_distance_dict,
                        pairwise_distance_dict,
                        ingredient_position_dict,
                        ingredient_angle_dict,
                        ingredient_occurence_dict,
                        ingredient_key_dict,
                        ax,
                    ) = self.process_ingredients_in_recipe(
                        recipe=inner_recipe,
                        center_distance_dict=center_distance_dict,
                        pairwise_distance_dict=pairwise_distance_dict,
                        ingredient_position_dict=ingredient_position_dict,
                        ingredient_angle_dict=ingredient_angle_dict,
                        ingredient_occurence_dict=ingredient_occurence_dict,
                        ingredient_key_dict=ingredient_key_dict,
                        seed_index=seed_index,
                        center=center,
                        ax=ax,
                        plot_figures=plot_figures,
                        two_d=two_d,
                        width=width,
                    )

            if plot_figures and two_d:
                ax.set_aspect(1.0)
                plt.axhline(y=bounding_box[0][1], color="k")
                plt.axhline(y=bounding_box[1][1], color="k")
                plt.axvline(x=bounding_box[0][0], color="k")
                plt.axvline(x=bounding_box[1][0], color="k")
                plt.axis(
                    [
                        bounding_box[0][0],
                        bounding_box[1][0],
                        bounding_box[0][1],
                        bounding_box[1][1],
                    ]
                )
                plt.savefig(self.figures_path / f"packing_image_{seed_basename}.png")
                plt.close()  # closes the current figure

        if image_export_options is not None:
            env_image_writer = ImageWriter(
                env=self.env,
                name=seed_basename,
                output_path=self.figures_path,
                **image_export_options,
            )
            env_image_writer = self.env.create_voxelization(env_image_writer)
            env_image_writer.export_image()

        if save_gradient_data_as_image:
            gradient_data_figure_path = self.figures_path / "gradient_data_figures"
            gradient_data_figure_path.mkdir(exist_ok=True)
            for _, gradient in self.env.gradients.items():
                grid_image_writer = ImageWriter(
                    env=self.env,
                    name=f"{seed_basename}_grid_data",
                    output_path=gradient_data_figure_path,
                )
                grid_image_writer = gradient.create_voxelization(grid_image_writer)
                grid_image_writer.export_image()

        return (
            center_distance_dict,
            pairwise_distance_dict,
            ingredient_position_dict,
            ingredient_angle_dict,
            ingredient_occurence_dict,
            ingredient_key_dict,
        )

    def doloop(
        self,
        number_of_packings,
        bounding_box,
        get_distance_distribution=True,
        plot_figures=True,
        show_grid=True,
        seed_list=None,
        config_name="default",
        recipe_version="1.0.0",
        image_export_options=None,
        parallel=False,
        save_gradient_data_as_image=False,
    ):
        """
        Runs multiple packings of the same recipe in a loop. This workflow
        also runs various analyses and saves the output figures and data at
        the location set by the environment. The output data is also stored
        as an attribute on the environment object and on the Analysis class
        instance.

        Parameters
        ----------
        number_of_packing : int
            Number of repeats of a packing. Default: 1
        bounding_box : np.ndarray
            bounding box from the environment
        get_distance_distribution: bool
            specify whether to calculate distance distributions
        render: bool
            ???
        plot_figures: bool
            specify whether to save figures generated by the analyses
        show_grid: bool
            specify whether to display packing grid in browser
        fbox_bb: ???
            ???
        seed_list: List
            list of seeds to use for the packing (for reproducibility)
        config_name: string
            name of the configuration used for the packing
        recipe_version: string
            version of the recipe used for the packing

        Outputs
        -------
        {}_distance_dict: dict
            Dictionaries with various ingredient distances stored
        images: png
            packing image, histograms of distance, angle, and occurence
            distributions as applicable for each seed, and a combined image
            across seeds
        """
        if seed_list is None:
            seed_list = self.getHaltonUnique(number_of_packings)
        packing_basename = self.env.base_name
        numpy.savetxt(
            self.env.out_folder / f"seeds_{packing_basename}.txt",
            seed_list,
            delimiter=",",
        )

        center_distance_file = (
            self.env.out_folder / f"center_distances_{packing_basename}.json"
        )
        pairwise_distance_file = (
            self.env.out_folder / f"pairwise_distances_{packing_basename}.json"
        )
        ingredient_position_file = (
            self.env.out_folder / f"positions_{packing_basename}.json"
        )
        ingredient_angle_file = self.env.out_folder / f"angles_{packing_basename}.json"
        ingredient_occurences_file = (
            self.env.out_folder / f"occurences_{packing_basename}.json"
        )
        ingredient_key_file = (
            self.env.out_folder / f"ingredient_keys_{packing_basename}.json"
        )

        center_distance_dict = {}
        pairwise_distance_dict = {}
        ingredient_position_dict = {}
        ingredient_angle_dict = {}
        ingredient_occurence_dict = {}
        ingredient_key_dict = {}

        if parallel:
            num_processes = numpy.min(
                [
                    int(numpy.floor(0.8 * multiprocessing.cpu_count())),
                    number_of_packings,
                ]
            )
            with concurrent.futures.ProcessPoolExecutor(
                max_workers=num_processes
            ) as executor:
                futures = []
                for seed_index in range(number_of_packings):
                    futures.append(
                        executor.submit(
                            self.pack_one_seed,
                            seed_index=seed_index,
                            seed_list=seed_list,
                            bounding_box=bounding_box,
                            center_distance_dict=center_distance_dict,
                            pairwise_distance_dict=pairwise_distance_dict,
                            ingredient_position_dict=ingredient_position_dict,
                            ingredient_angle_dict=ingredient_angle_dict,
                            ingredient_occurence_dict=ingredient_occurence_dict,
                            ingredient_key_dict=ingredient_key_dict,
                            get_distance_distribution=get_distance_distribution,
                            image_export_options=image_export_options,
                            save_gradient_data_as_image=save_gradient_data_as_image,
                        )
                    )
                for future in concurrent.futures.as_completed(futures):
                    (
                        seed_center_distance_dict,
                        seed_pairwise_distance_dict,
                        seed_ingredient_position_dict,
                        seed_ingredient_angle_dict,
                        seed_ingredient_occurence_dict,
                        seed_ingredient_key_dict,
                    ) = future.result()
                    center_distance_dict.update(seed_center_distance_dict)
                    pairwise_distance_dict.update(seed_pairwise_distance_dict)
                    ingredient_position_dict.update(seed_ingredient_position_dict)
                    ingredient_angle_dict.update(seed_ingredient_angle_dict)
                    ingredient_occurence_dict.update(seed_ingredient_occurence_dict)
                    ingredient_key_dict.update(seed_ingredient_key_dict)

        else:
            for seed_index in range(number_of_packings):
                (
                    center_distance_dict,
                    pairwise_distance_dict,
                    ingredient_position_dict,
                    ingredient_angle_dict,
                    ingredient_occurence_dict,
                    ingredient_key_dict,
                ) = self.pack_one_seed(
                    seed_index=seed_index,
                    seed_list=seed_list,
                    bounding_box=bounding_box,
                    center_distance_dict=center_distance_dict,
                    pairwise_distance_dict=pairwise_distance_dict,
                    ingredient_position_dict=ingredient_position_dict,
                    ingredient_angle_dict=ingredient_angle_dict,
                    ingredient_occurence_dict=ingredient_occurence_dict,
                    ingredient_key_dict=ingredient_key_dict,
                    get_distance_distribution=get_distance_distribution,
                    image_export_options=image_export_options,
                    show_grid=show_grid,
                    plot_figures=plot_figures,
                    save_gradient_data_as_image=save_gradient_data_as_image,
                )

        self.writeJSON(center_distance_file, center_distance_dict)
        self.writeJSON(pairwise_distance_file, pairwise_distance_dict)
        self.writeJSON(ingredient_position_file, ingredient_position_dict)
        self.writeJSON(ingredient_angle_file, ingredient_angle_dict)
        self.writeJSON(ingredient_occurences_file, ingredient_occurence_dict)
        self.writeJSON(ingredient_key_file, ingredient_key_dict)

        if number_of_packings > 1:
            Writer().save_as_simularium(self.env, self.seed_to_results)

        all_ingredient_positions = self.combine_results_from_seeds(
            ingredient_position_dict
        )
        all_center_distances = self.combine_results_from_seeds(center_distance_dict)
        all_ingredient_distances = self.combine_results_from_seeds(
            pairwise_distance_dict
        )
        all_ingredient_occurences = self.combine_results_from_seeds(
            ingredient_occurence_dict
        )
        all_ingredient_angles = self.combine_results_from_seeds(ingredient_angle_dict)

        all_center_distance_array = numpy.array(
            self.combine_results_from_ingredients(all_center_distances)
        )
        all_pairwise_distance_array = numpy.array(
            self.combine_results_from_ingredients(all_ingredient_distances)
        )
        all_ingredient_position_array = numpy.array(
            self.combine_results_from_ingredients(all_ingredient_positions)
        )
        all_ingredient_angle_array = numpy.array(
            self.combine_results_from_ingredients(all_ingredient_angles)
        )

        self.env.ingredient_positions = all_ingredient_positions
        self.env.distances = all_ingredient_distances
        self.env.basename = packing_basename
        self.env.occurences = all_ingredient_occurences
        self.env.angles = all_ingredient_angles

        self.center_distance_dict = center_distance_dict
        self.pairwise_distance_dict = pairwise_distance_dict
        self.ingredient_position_dict = ingredient_position_dict
        self.ingredient_angle_dict = ingredient_angle_dict
        self.ingredient_occurence_dict = ingredient_occurence_dict
        self.ingredient_key_dict = ingredient_key_dict

        if plot_figures:
            self.env.loopThroughIngr(self.plot_position_distribution)
            self.env.loopThroughIngr(self.plot_occurence_distribution)

            # plot pairwise distance histograms
            self.plot_distance_distribution(all_ingredient_distances)

            # plot distribution of positions for all combined seeds and ingredients
            self.plot_position_distribution_total(all_ingredient_position_array)

            # plot histograms for all combined distances
            if len(all_center_distance_array) > 1:
                self.histogram(
                    all_center_distance_array,
                    self.figures_path
                    / f"all_ingredient_center_distances_{self.env.basename}.png",
                    title_str="all_ingredients",
                    x_label="center distance",
                    y_label="count",
                )

            if len(all_center_distance_array) > 1:
                self.histogram(
                    all_pairwise_distance_array,
                    self.figures_path
                    / f"all_ingredient_pairwise_distances_{self.env.basename}.png",
                    title_str="all_ingredients",
                    x_label="pairwise distances",
                    y_label="count",
                )

            # plot the angle
            if len(all_ingredient_angle_array) > 1:
                self.histogram(
                    all_ingredient_angle_array[0],
                    self.figures_path / f"all_angles_X_{self.env.basename}.png",
                    title_str="all_ingredients",
                    x_label="angles X",
                    y_label="count",
                )
                self.histogram(
                    all_ingredient_angle_array[1],
                    self.figures_path / f"all_angles_Y_{self.env.basename}.png",
                    title_str="all_ingredients",
                    x_label="angles Y",
                    y_label="count",
                )
                self.histogram(
                    all_ingredient_angle_array[2],
                    self.figures_path / f"all_angles_Z_{self.env.basename}.png",
                    title_str="all_ingredients",
                    x_label="angles Z",
                    y_label="count",
                )

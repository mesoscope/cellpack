# -*- coding: utf-8 -*-
"""
Created on Mon May  6 22:58:44 2013

@author: ludo
"""
import os
import math

import numpy
import scipy
import csv
import json
from time import time
from PIL import Image

import matplotlib
from matplotlib import pylab
from matplotlib import pyplot
from matplotlib.patches import Circle
from matplotlib import pyplot as plt

from cellpack.autopack.upy import colors as col
import cellpack.autopack as autopack
from cellpack.autopack.transformation import signed_angle_between_vectors
from cellpack.autopack.ldSequence import halton

from cellpack.autopack.GeometryTools import GeometryTools, Rectangle
from cellpack.autopack.upy.colors import map_colors
from cellpack.autopack.plotly_result import PlotlyAnalysis


def autolabel(rects, ax):
    # from http://matplotlib.org/examples/api/barchart_demo.html
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(
            rect.get_x() + rect.get_width() / 2.0,
            height / 2.0,
            "%d" % int(height),
            ha="center",
            va="bottom",
        )


def autolabelyerr(ax, rects, err=None):
    # attach some text labels
    for i, rect in enumerate(rects):
        height = rect.get_height()
        v = "%.2f" % height
        y = 0.5 * height
        if err is not None:
            v = "%.2f" % err[i]
            y = 1.05 * height
        ax.text(rect.get_x() + rect.get_width() / 2.0, y, v, ha="center", va="bottom")


def autolabels(loci1, loci2, loci3, ax, yerr1, yerr2, yerr3):
    # from http://matplotlib.org/examples/api/barchart_demo.html
    # attach some text labels
    for i in range(len(loci1)):  # rects:
        rect1 = loci1[i]
        rect2 = loci2[i]
        rect3 = loci3[i]
        height1 = rect1.get_height()
        height2 = rect2.get_height()
        height3 = rect3.get_height()
        ax.text(
            rect1.get_x() + rect1.get_width() / 2.0,
            height1 / 2.0,
            "%2.1f" % (height1 * 100.0),
            ha="center",
            va="bottom",
            color="black",
        )
        ax.text(
            rect2.get_x() + rect2.get_width() / 2.0,
            height2 / 2.0 + height1,
            "%2.1f" % (height2 * 100.0),
            ha="center",
            va="bottom",
            color="black",
        )
        ax.text(
            rect3.get_x() + rect2.get_width() / 2.0,
            height3 / 2.0 + height1 + height2,
            "%2.1f" % (height3 * 100.0),
            ha="center",
            va="bottom",
            color="white",
        )
        ax.text(
            rect1.get_x() + rect1.get_width() / 2.0,
            1.01 * height1,
            "%2.1f" % (yerr1[i] * 100.0),
            ha="center",
            va="bottom",
            color="black",
        )
        ax.text(
            rect2.get_x() + rect2.get_width() / 2.0,
            1.01 * (height2 + height1),
            "%2.1f" % (yerr2[i] * 100.0),
            ha="center",
            va="bottom",
            color="white",
        )
        ax.text(
            rect3.get_x() + rect2.get_width() / 2.0,
            1.01 * (height3 + height1 + height2),
            "%2.1f" % (yerr3[i] * 100.0),
            ha="center",
            va="bottom",
            color="black",
        )


def getRndWeighted(listPts, weight, yerr):
    w = [yerr[i] * numpy.random.random() + weight[i] for i in range(len(weight))]
    t = numpy.cumsum(w)
    s = numpy.sum(w)
    i = numpy.searchsorted(t, numpy.random.rand(1) * s)[0]
    return listPts[i]


class AnalyseAP:
    def __init__(self, env=None, viewer=None, result_file=None):
        self.env = None
        self.smallest = 99999.0
        self.largest = 0.0
        if env:
            self.env = env
            self.smallest, self.largest = self.getMinMaxProteinSize()
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

        autopack._colors = None

    def getMinMaxProteinSize(self):
        smallest = 999999.0
        largest = 0.0
        for organelle in self.env.compartments:
            mini, maxi = organelle.getMinMaxProteinSize()
            if mini < smallest:
                smallest = mini
            if maxi > largest:
                largest = maxi

        if self.env.exteriorRecipe:
            mini, maxi = self.env.exteriorRecipe.getMinMaxProteinSize()
            if mini < smallest:
                smallest = mini
            if maxi > largest:
                largest = maxi
        return smallest, largest

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
        # all object are in h.molecules and orga.molecules
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
                    ingrname + "_euler_X.csv", numpy.array(e3[0]), delimiter=","
                )
                numpy.savetxt(
                    ingrname + "_euler_Y.csv", numpy.array(e3[1]), delimiter=","
                )
                numpy.savetxt(
                    ingrname + "_euler_Z.csv", numpy.array(e3[2]), delimiter=","
                )
                self.histo(e3[0], ingrname + "_euler_X.png", bins=12, size=max(e3[0]))
                self.histo(e3[1], ingrname + "_euler_Y.png", bins=12, size=max(e3[1]))
                self.histo(e3[2], ingrname + "_euler_Z.png", bins=12, size=max(e3[2]))
        #                ingrpositions,distA,angles3=self.getDistanceAngle(ingrpos3, ingrrot3)
        #                numpy.savetxt(ingrname+"_angle_X.csv", numpy.array(angles3[1]), delimiter=",")
        #                numpy.savetxt(ingrname+"_angle_Y.csv", numpy.array(angles3[2]), delimiter=",")
        #                numpy.savetxt(ingrname+"_angle_Z.csv", numpy.array(angles3[3]), delimiter=",")
        #                self.histo(angles3[1],ingrname+"_angle_X.png",bins=12,size=max(angles3[1]))
        #                self.histo(angles3[2],ingrname+"_angle_Y.png",bins=12,size=max(angles3[2]))
        #                self.histo(angles3[3],ingrname+"_angle_Z.png",bins=12,size=max(angles3[3]))
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
            #                print area,leftBound,rightBound
            else:
                area = bbox[0][1] ** 2
        return area

    def getAxeValue(self, ingrname, axe=0):
        ingrpositions = [
            self.env.molecules[i][0][axe]
            for i in range(len(self.env.molecules))
            if self.env.molecules[i][2].name == ingrname
        ]
        return ingrpositions

    def getAxesValues(self, positions):
        pp = numpy.array(positions).transpose()
        if len(positions) == 0:
            return 1, 1, 1
        px = pp[0]
        py = pp[1]
        pz = pp[2]
        return px, py, pz

    def getDistance(self, ingrname, center):
        distA = []
        ingrpositions = [
            self.env.molecules[i][0]
            for i in range(len(self.env.molecules))
            if self.env.molecules[i][2].name == ingrname
        ]
        ingrpositions = numpy.array(ingrpositions)
        if len(ingrpositions):
            delta = numpy.array(ingrpositions) - numpy.array(center)
            delta *= delta
            distA = numpy.sqrt(delta.sum(1)).tolist()
        return ingrpositions, distA

    def getDistanceAngle(self, ingr, center):
        # need matrix to euler? then access and plot them?
        # also check the measure angle one
        angles = []
        distA = []
        ingr_positions = [
            self.env.molecules[i][0]
            for i in range(len(self.env.molecules))
            if self.env.molecules[i][2].name == ingr.name
        ]
        ingr_positions = numpy.array(ingr_positions)
        ingr_rotation = [
            self.env.molecules[i][1]
            for i in range(len(self.env.molecules))
            if self.env.molecules[i][2].name == ingr.name
        ]
        ingr_rotation = numpy.array(ingr_rotation)
        if len(ingr_positions):
            delta = numpy.array(ingr_positions) - numpy.array(center)
            # lets do it on X,Y,Z and also per positions ?
            anglesX = numpy.array(
                signed_angle_between_vectors(
                    [[0, 0, 1]] * len(ingr_positions),
                    ingr_rotation[:, 0, :3],
                    -delta,
                    directed=False,
                    axis=1,
                )
            )
            anglesY = numpy.array(
                signed_angle_between_vectors(
                    [[0, 1, 0]] * len(ingr_positions),
                    ingr_rotation[:, 1, :3],
                    -delta,
                    directed=False,
                    axis=1,
                )
            )
            anglesZ = numpy.array(
                signed_angle_between_vectors(
                    [[1, 0, 0]] * len(ingr_positions),
                    ingr_rotation[:, 2, :3],
                    -delta,
                    directed=False,
                    axis=1,
                )
            )
            delta *= delta
            distA = numpy.sqrt(delta.sum(1)).tolist()
            angles = numpy.array([distA, anglesX, anglesY, anglesZ])
        return ingr_positions, distA, numpy.degrees(angles)

    def getVolumeShell(self, bbox, radii, center):
        # rectangle_circle_area
        volumes = []
        box_size0 = bbox[1][0] - bbox[0][0]
        for i in range(len(radii) - 1):
            r1 = radii[i]
            r2 = radii[i + 1]
            v1 = self.g.calc_volume(r1, box_size0 / 2.0)
            v2 = self.g.calc_volume(r2, box_size0 / 2.0)
            #            if v1 == 0 or v2 == 0 :
            #                volumes.append((4./3.)*numpy.pi*(numpy.power(r2,3)-numpy.power(r1, 3)))
            #            else :
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
            numpy.array(self.env.ingrpositions[ingr.name]),
            delimiter=",",
        )
        self.histo(distances, basename + ingr.name + "_histo.png")
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
            di = scipy.spatial.distance.cdist(
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

    #        pos=numpy.array(self.env.ingrpositions[ingr.name])#np.array([np.array(p[0]) for p in h.molecules])
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
            di = scipy.spatial.distance.cdist(
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
            numpy.array(self.env.ingrpositions[ingr.name]),
            delimiter=",",
        )
        self.histo(distances, basename + ingr.name + "_histo.png")
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
            basename + ingr.name + "_rdf_simple.csv", numpy.array(G), delimiter=","
        )
        self.plot(numpy.array(G), radii[:-1], basename + ingr.name + "_rdf_simple.png")

    def axis_distribution_total(self, all_positions):
        basename = self.env.basename
        numpy.savetxt(
            basename + "total_pos.csv", numpy.array(all_positions), delimiter=","
        )
        px, py, pz = self.getAxesValues(all_positions)
        #        m1=numpy.nonzero( numpy.logical_and(
        #               numpy.greater_equal(px, 0.), numpy.less_equal(px, 1000.0)))
        #        m2=numpy.nonzero( numpy.logical_and(
        #               numpy.greater_equal(py, 0.), numpy.less_equal(py, 1000.0)))
        self.histo(px, basename + "total_histo_X.png", bins=10)
        self.histo(py, basename + "total_histo_Y.png", bins=10)
        self.histo(pz, basename + "total_histo_Z.png", bins=10)

    def axis_distribution(self, ingr):
        basename = self.env.basename
        px, py, pz = self.getAxesValues(self.env.ingrpositions[ingr.name])
        self.histo(px, basename + ingr.name + "_histo_X.png", bins=10)
        self.histo(py, basename + ingr.name + "_histo_Y.png", bins=10)
        self.histo(pz, basename + ingr.name + "_histo_Z.png", bins=10)
        # do it for all ingredient cumulate?

    def occurence_distribution(self, ingr):
        basename = self.env.basename
        occ = self.env.occurences[ingr.name]
        self.simpleplot(range(len(occ)), occ, basename + ingr.name + "_occurence.png")

    def correlation(self, ingr):
        basename = self.env.basename
        posxyz = numpy.array(self.env.ingrpositions[ingr.name]).transpose()
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
        from numpy import zeros, sqrt, where, pi, average, arange, histogram

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

        (interior_indices,) = where(bools1 * bools2 * bools3 * bools4 * bools5 * bools6)
        num_interior_particles = len(interior_indices)

        if num_interior_particles < 1:
            raise RuntimeError(
                "No particles found for which a sphere of radius rMax\
    will lie entirely within a cube of side length S. Decrease rMax\
    or increase the size of the cube."
            )

        edges = arange(0.0, rMax + 1.1 * dr, dr)
        num_increments = len(edges) - 1
        g = zeros([num_interior_particles, num_increments])
        radii = zeros(num_increments)
        numberDensity = len(x) / S**3

        # Compute pairwise correlation for each interior particle
        for p in range(num_interior_particles):
            index = interior_indices[p]
            d = sqrt((x[index] - x) ** 2 + (y[index] - y) ** 2 + (z[index] - z) ** 2)
            d[index] = 2 * rMax

            (result, bins) = histogram(d, bins=edges, normed=False)
            g[p, :] = result / numberDensity

        # Average g(r) for all interior particles and compute radii
        g_average = zeros(num_increments)
        for i in range(num_increments):
            radii[i] = (edges[i] + edges[i + 1]) / 2.0
            rOuter = edges[i + 1]
            rInner = edges[i]
            g_average[i] = average(g[:, i]) / (
                4.0 / 3.0 * pi * (rOuter**3 - rInner**3)
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
        from numpy import zeros, sqrt, where, pi, average, arange, histogram

        # Number of particles in ring/area of ring/number of reference particles/number density
        # area of ring = pi*(r_outer**2 - r_inner**2)

        # Find particles which are close enough to the box center that a circle of radius
        # rMax will not cross any edge of the box
        bools1 = x > 1.1 * rMax
        bools2 = x < (S - 1.1 * rMax)
        bools3 = y > rMax * 1.1
        bools4 = y < (S - rMax * 1.1)
        (interior_indices,) = where(bools1 * bools2 * bools3 * bools4)
        num_interior_particles = len(interior_indices)

        if num_interior_particles < 1:
            raise RuntimeError(
                "No particles found for which a circle of radius rMax\
                    will lie entirely within a square of side length S.  Decrease rMax\
                    or increase the size of the square."
            )

        edges = arange(0.0, rMax + 1.1 * dr, dr)
        num_increments = len(edges) - 1
        g = zeros([num_interior_particles, num_increments])
        radii = zeros(num_increments)
        numberDensity = len(x) / S**2

        # Compute pairwise correlation for each interior particle
        for p in range(num_interior_particles):
            index = interior_indices[p]
            d = sqrt((x[index] - x) ** 2 + (y[index] - y) ** 2)
            d[index] = 2 * rMax

            (result, bins) = histogram(d, bins=edges, normed=False)
            g[p, :] = result / numberDensity

        # Average g(r) for all interior particles and compute radii
        g_average = zeros(num_increments)
        for i in range(num_increments):
            radii[i] = (edges[i] + edges[i + 1]) / 2.0
            rOuter = edges[i + 1]
            rInner = edges[i]
            # divide by the area of sphere cut by sqyare
            g_average[i] = average(g[:, i]) / (pi * (rOuter**2 - rInner**2))

        return (g_average, radii, interior_indices)

    def histo(self, distances, filename, bins=100, size=1000.0):
        pylab.clf()
        numpy.mean(distances), numpy.std(distances)
        # the histogram of the data
        #        b=numpy.arange(distances.min(), distances.max(), 2)
        #        n, bins, patches = pyplot.hist(distances, bins=bins, normed=1, facecolor='green')#, alpha=0.75)
        y, binEdges = numpy.histogram(distances, bins=bins)
        bincenters = 0.5 * (binEdges[1:] + binEdges[:-1])
        menStd = numpy.sqrt(y)  # or sigma?
        width = bins
        pyplot.bar(bincenters, y, width=width, color="r", yerr=menStd)
        # add a 'best fit' line?
        #        y = mlab.normpdf( bins, mu, sigma)#should be the excepted distribution
        #        l = pyplot.plot(bins, y, 'r--', linewidth=3)
        pyplot.savefig(filename)

    #        pylab.close()     # closes the current figure

    def plot(self, rdf, radii, file_name):
        pylab.clf()
        matplotlib.rc("font", size=14)
        matplotlib.rc("figure", figsize=(5, 4))
        #        pylab.clf()
        pylab.plot(radii, rdf, linewidth=3)
        pylab.xlabel(r"distance $r$ in $\AA$")
        pylab.ylabel(r"radial distribution function $g(r)$")
        pylab.savefig(file_name)

    def simpleplot(self, X, Y, filenameme, w=3):
        pylab.clf()
        pylab.plot(X, Y, linewidth=w)
        pylab.savefig(filenameme)

    def build_grid(
        self,
        bb,
        forceBuild=True,
    ):
        t1 = time()
        gridFileIn = None
        gridFileOut = None
        self.env.buildGrid(
            boundingBox=bb,
            gridFileIn=gridFileIn,
            rebuild=forceBuild,
            gridFileOut=gridFileOut,
            previousFill=False,
        )

        t2 = time()
        gridTime = t2 - t1
        print("time to Build Grid", gridTime)

    def pack(
        self, seed=20, vTestid=3, vAnalysis=0, fbox_bb=None, show_plotly_plot=True
    ):
        if show_plotly_plot:
            self.plotly.update_title(self.env.placeMethod)

        t1 = time()
        self.env.pack_grid(
            seedNum=seed, vTestid=vTestid, vAnalysis=vAnalysis, fbox=fbox_bb
        )
        t2 = time()
        print("time to run pack_grid", self.env.placeMethod, t2 - t1)
        print("num placed", len(self.env.molecules))
        if show_plotly_plot:
            self.plotly.update_title(
                f"{self.env.placeMethod} took {str(round(t2 - t1, 2))}s, packed {len(self.env.molecules)}"
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
            print

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
        self, data=None, filename=None, bbox=[[0.0, 0, 0.0], [1000.0, 1000.0, 1000.0]]
    ):
        if data is None and filename is None:
            return
        elif data is None and filename is not None:
            with open(filename) as data_file:
                data = json.load(data_file)
        fig = pyplot.figure()
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
                        radius[ingrname] = data[recipe][ingrname]["encapsulatingRadius"]
                    ingrrot[ingrname].append(data[recipe][ingrname]["results"][k][1])
                    ingrpos[ingrname].append(data[recipe][ingrname]["results"][k][0])
        for ingr in ingrpos:
            for i, p in enumerate(ingrpos[ingr]):
                ax.add_patch(
                    Circle(
                        (p[0], p[1]), radius[ingr], edgecolor="black", facecolor="red"
                    )
                )
            ax.set_aspect(1.0)
            pyplot.axhline(y=bbox[0][1], color="k")
            pyplot.axhline(y=bbox[1][1], color="k")
            pyplot.axvline(x=bbox[0][0], color="k")
            pyplot.axvline(x=bbox[1][0], color="k")
            pyplot.axis([bbox[0][0], bbox[1][0], bbox[0][1], bbox[1][1]])
            pyplot.savefig("plot" + ingr + ".png")
            pylab.close()  # closes the current figure
        return ingrpos

    #        res=plotOneResult(None,filename="results_seed_8.json")

    def plot_one_result_3D(self, filename, width=1000.0):
        plt.close("all")  # closes the current figure
        pos = []
        s = []
        c = []
        for i in range(len(self.env.molecules)):
            m = self.env.molecules[i]
            pos.append(numpy.array(m[0]).tolist())
            s.append(m[2].encapsulatingRadius ** 2)
            c.append(m[2].color)
        fig = plt.figure()
        ax = fig.gca(projection="3d")
        x, y, z = numpy.array(pos).transpose()
        ax.scatter(x, y, z, s=s, c=c)
        ax.legend()
        ax.set_xlim3d(0, width)
        ax.set_ylim3d(0, width)
        ax.set_zlim3d(0, width)
        plt.savefig(filename)
        return x, y, z, s, c

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

    def doloop(
        self,
        n,
        bbox,
        output,
        rdf=True,
        render=False,
        plot=True,
        show_plotly_plot=True,
        twod=True,
        fbox_bb=None,
        use_file=True,
        seeds_i=None,
    ):
        # doLoop automatically produces result files, images, and documents from the recipe while adjusting parameters
        # To run doLoop, 1) in your host's python console type:
        # execfile(pathothis recipe) # for example, on my computer:
        # " execfile("/Users/grahamold/Dev/autoFillSVN/autofillSVNversions/trunk/AutoFillClean/autoFillRecipeScripts/2DsphereFill/2DSpheres_setup_recipe.py")
        # 2) prepare your scene for the rendering->render output should be 640,480 but you can change the size in the script at then end.  Set up textures lights, and effects as you wish
        #    Results will appear in the result folder of your recipe path
        # where n is the number of loop, seed = i
        # analyse.doloop(n)
        if seeds_i is None:
            seeds_i = self.getHaltonUnique(n)
        numpy.savetxt(output + os.sep + "seeds", seeds_i, delimiter=",")
        angle_file = output + os.sep + "angle"
        position_file = output + os.sep + "pos"
        distance_file = output + os.sep + "dist"
        occurences_file = output + os.sep + "occurence"
        rangeseed = range(n)
        distances = {}
        ingrpositions = {}
        anglesingr = {}
        occurences = {}
        total_positions = []
        total_distances = []
        total_angles = []
        self.bbox = bbox
        angles = None
        rebuild = True
        for seed_index in range(n):
            basename = output + os.sep + "results_seed_" + str(seed_index)
            # Clear
            if self.afviewer:
                self.afviewer.clearFill("Test_Spheres2D")
            else:
                self.env.reset()
            self.env.saveResult = True
            self.env.resultfile = basename
            seed = seeds_i[seed_index]  # int(time())
            self.build_grid(
                bbox,
                forceBuild=rebuild,
            )
            self.pack(
                seed=seed,
                vTestid=seed_index,
                vAnalysis=1,
                fbox_bb=fbox_bb,
                show_plotly_plot=show_plotly_plot,
            )
            self.center = self.env.grid.getCenter()
            if render:
                # render/save scene if hosted otherwise nothing
                self.helper.render(basename + ".jpg", 640, 480)
                self.helper.write(basename + ".c4d", [])
            if rdf:
                if plot and twod:
                    width = 1000.0  # should be the boundary here ?
                    fig = pyplot.figure()
                    ax = fig.add_subplot(111)
                center = self.env.grid.getCenter()  # [500,500,0.5]#center of the grid
                r = self.env.exteriorRecipe
                d = {}
                if r:
                    for ingr in r.ingredients:
                        if ingr.name not in distances:
                            distances[ingr.name] = []
                            ingrpositions[ingr.name] = []
                            anglesingr[ingr.name] = []
                            occurences[ingr.name] = []
                        if ingr.packingMode == "gradient" and self.env.use_gradient:
                            self.center = center = self.env.gradients[
                                ingr.gradient
                            ].direction
                            # also mesure the angle pos>center pcpalVector
                            ingrpos, d, angles = self.getDistanceAngle(ingr, center)
                            if use_file:
                                f_handle = open(angle_file, "a")
                                numpy.savetxt(f_handle, angles, delimiter=",")
                                f_handle.close()
                            else:
                                anglesingr[ingr.name].extend(angles)
                                total_angles.extend(angles)
                        else:
                            ingrpos, d = self.getDistance(ingr.name, center)
                        occurences[ingr.name].append(len(ingrpos))
                        if use_file:
                            f_handle = open(position_file, "a")
                            numpy.savetxt(f_handle, ingrpos, delimiter=",")
                            f_handle.close()
                            f_handle = open(distance_file, "a")
                            numpy.savetxt(f_handle, d, delimiter=",")
                            f_handle.close()
                            distances[ingr.name] = d
                            ingrpositions[ingr.name] = ingrpos.tolist()
                        else:
                            distances[ingr.name].extend(d)
                            ingrpositions[ingr.name].extend(ingrpos)
                            total_positions.extend(ingrpos)
                            total_distances.extend(d)

                        if plot and twod:
                            for i, p in enumerate(ingrpos):
                                ax.add_patch(
                                    Circle(
                                        (p[0], p[1]),
                                        ingr.encapsulatingRadius,
                                        edgecolor="black",
                                        facecolor=ingr.color,
                                    )
                                )
                                #  Plot "image" particles to verify that periodic boundary conditions are working
                                r = ingr.encapsulatingRadius
                                if autopack.testPeriodicity:
                                    if p[0] < r:
                                        ax.add_patch(
                                            Circle(
                                                (p[0] + width, p[1]),
                                                r,
                                                facecolor=ingr.color,
                                            )
                                        )
                                    elif p[0] > (width - r):
                                        ax.add_patch(
                                            Circle(
                                                (p[0] - width, p[1]),
                                                r,
                                                facecolor=ingr.color,
                                            )
                                        )
                                    if p[1] < r:
                                        ax.add_patch(
                                            Circle(
                                                (p[0], p[1] + width),
                                                r,
                                                facecolor=ingr.color,
                                            )
                                        )
                                    elif p[1] > (width - r):
                                        ax.add_patch(
                                            Circle(
                                                (p[0], p[1] - width),
                                                r,
                                                facecolor=ingr.color,
                                            )
                                        )
                                if i == 0:  # len(ingrpos)-1:
                                    continue
                                if ingr.Type == "Grow":
                                    pyplot.plot(
                                        [ingrpos[-i][0], ingrpos[-i - 1][0]],
                                        [ingrpos[-i][1], ingrpos[-i - 1][1]],
                                        "k-",
                                        lw=2,
                                    )
                                    # plot the sphere
                                    if ingr.use_rbsphere:
                                        r, pts = ingr.getInterpolatedSphere(
                                            ingrpos[-i - 1], ingrpos[-i]
                                        )
                                        for pt in pts:
                                            ax.add_patch(
                                                Circle(
                                                    (pt[0], pt[1]),
                                                    ingr.minRadius,
                                                    edgecolor="black",
                                                    facecolor=ingr.color,
                                                )
                                            )
                for o in self.env.compartments:
                    rs = o.surfaceRecipe
                    if rs:
                        for ingr in rs.ingredients:
                            if ingr.name not in distances:
                                distances[ingr.name] = []
                                ingrpositions[ingr.name] = []
                                occurences[ingr.name] = []
                            if ingr.packingMode == "gradient" and self.env.use_gradient:
                                center = self.env.gradients[ingr.gradient].direction
                            ingrpos, d = self.getDistance(ingr.name, center)
                            occurences[ingr.name].append(len(ingrpos))
                            if use_file:
                                f_handle = open(position_file, "a")
                                numpy.savetxt(f_handle, ingrpos, delimiter=",")
                                f_handle.close()
                                f_handle = open(distance_file, "a")
                                numpy.savetxt(f_handle, d, delimiter=",")
                                f_handle.close()
                                distances[ingr.name] = d
                                ingrpositions[ingr.name] = ingrpos.tolist()
                            else:
                                distances[ingr.name].extend(d)
                                ingrpositions[ingr.name].extend(ingrpos)
                                total_positions.extend(ingrpos)
                                total_distances.extend(d)
                            if plot and twod:
                                for p in ingrpos:
                                    ax.add_patch(
                                        Circle(
                                            (p[0], p[1]),
                                            ingr.encapsulatingRadius,
                                            edgecolor="black",
                                            facecolor=ingr.color,
                                        )
                                    )
                    ri = o.innerRecipe
                    if ri:
                        for ingr in ri.ingredients:
                            if ingr.name not in distances:
                                distances[ingr.name] = []
                                ingrpositions[ingr.name] = []
                                occurences[ingr.name] = []
                            if ingr.packingMode == "gradient" and self.env.use_gradient:
                                center = self.env.gradients[ingr.gradient].direction
                            ingrpos, d = self.getDistance(ingr.name, center)
                            occurences[ingr.name].append(len(ingrpos))
                            if use_file:
                                f_handle = open(position_file, "a")
                                numpy.savetxt(f_handle, ingrpos, delimiter=",")
                                f_handle.close()
                                f_handle = open(distance_file, "a")
                                numpy.savetxt(f_handle, d, delimiter=",")
                                f_handle.close()
                                distances[ingr.name] = d
                                ingrpositions[ingr.name] = ingrpos.tolist()
                            else:
                                distances[ingr.name].extend(d)
                                ingrpositions[ingr.name].extend(ingrpos)
                                total_positions.extend(ingrpos)
                                total_distances.extend(d)
                            if plot and twod:
                                for p in ingrpos:
                                    ax.add_patch(
                                        Circle(
                                            (p[0], p[1]),
                                            ingr.encapsulatingRadius,
                                            edgecolor="black",
                                            facecolor=ingr.color,
                                        )
                                    )
                # write
                if use_file:
                    self.writeJSON(
                        output + os.sep + "_posIngr_" + str(seed_index) + ".json",
                        ingrpositions,
                    )
                    self.writeJSON(
                        output + os.sep + "_dIngr_" + str(seed_index) + ".json",
                        distances,
                    )
                    self.writeJSON(
                        output + os.sep + "_angleIngr_" + str(seed_index) + ".json",
                        anglesingr,
                    )
                if plot and twod:
                    ax.set_aspect(1.0)
                    pyplot.axhline(y=bbox[0][1], color="k")
                    pyplot.axhline(y=bbox[1][1], color="k")
                    pyplot.axvline(x=bbox[0][0], color="k")
                    pyplot.axvline(x=bbox[1][0], color="k")
                    pyplot.axis([bbox[0][0], bbox[1][0], bbox[0][1], bbox[1][1]])
                    pyplot.savefig(basename + ".png")
                    pylab.close()  # closes the current figure

        numpy.savetxt(output + os.sep + "seeds", seeds_i, delimiter=",")
        if use_file:
            total_positions = numpy.genfromtxt(position_file, delimiter=",")
            try:
                total_angles = numpy.genfromtxt(angle_file, delimiter=",")
            except Exception:
                total_angles = []
            # gatherall result
            ingrpositions = {}
            distances = {}
            anglesingr = {}
            for i in rangeseed:
                dict1 = self.loadJSON(output + os.sep + "_posIngr_" + str(i) + ".json")
                ingrpositions = dict(self.merge(ingrpositions, dict1))
                dict1 = self.loadJSON(output + os.sep + "_dIngr_" + str(i) + ".json")
                distances = dict(self.merge(distances, dict1))
                dict1 = self.loadJSON(
                    output + os.sep + "_angleIngr_" + str(i) + ".json"
                )
                anglesingr = dict(self.merge(anglesingr, dict1))
        self.writeJSON(occurences_file, occurences)
        self.env.ingrpositions = ingrpositions
        self.env.distances = distances
        self.env.basename = basename
        self.env.occurences = occurences
        self.env.angles = total_angles
        if plot and twod:
            self.env.loopThroughIngr(self.axis_distribution)
            self.env.loopThroughIngr(self.occurence_distribution)
            self.axis_distribution_total(total_positions)
        # plot the angle
        if len(total_angles):
            self.histo(
                total_angles[1],
                output + os.sep + "_anglesX.png",
                bins=12,
                size=max(total_angles[2]),
            )
            self.histo(
                total_angles[2],
                output + os.sep + "_anglesY.png",
                bins=12,
                size=max(total_angles[2]),
            )
            self.histo(
                total_angles[3],
                output + os.sep + "_anglesZ.png",
                bins=12,
                size=max(total_angles[2]),
            )

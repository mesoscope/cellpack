from math import sqrt
import cellpack.autopack as autopack
import numpy as np
import sys



class Partner:
    def __init__(self, ingredient, weight=0.0, properties=None):
        if type(ingredient) is str:
            self.name = ingredient
        else:
            self.name = ingredient.name
        self.ingr = ingredient
        self.weight = weight
        self.properties = {}
        self.distance_expression = None
        if properties is not None:
            self.properties = properties

    # def setup(
    #     self,
    # ):
    # QUESTION: why is this commented out?
    # # setup the marge according the pt properties
    # pt1 = numpy.array(self.getProperties("pt1"))
    # pt2 = numpy.array(self.getProperties("pt2"))
    # pt3 = numpy.array(self.getProperties("pt3"))
    # pt4 = numpy.array(self.getProperties("pt4"))

    # # length = autopack.helper.measure_distance(pt2,pt3)#length
    # margein = math.degrees(
    #     autopack.helper.angle_between_vectors(pt2 - pt1, pt3 - pt2)
    # )  # 4
    # margeout = math.degrees(
    #     autopack.helper.angle_between_vectors(pt3 - pt2, pt4 - pt3)
    # )  # 113
    # dihedral = math.degrees(
    #     autopack.helper.angle_between_vectors(pt2 - pt1, pt4 - pt2)
    # )  # 79
    # dihedral = autopack.helper.dihedral(pt1, pt2, pt3, pt4)
    # self.properties["marge_in"] = [margein - 1, margein + 1]
    # self.properties["marge_out"] = [margeout - 1, margeout + 1]
    # self.properties["diehdral"] = [dihedral - 1, dihedral + 1]

    def addProperties(self, name, value):
        self.properties[name] = value

    def getProperties(self, name):
        if name in self.properties:
            # if name == "pt1":
            #    return [0,0,0]
            # if name == "pt2":
            #    return [0,0,0]
            return self.properties[name]
        else:
            return None

    def distanceFunction(self, d, expression=None, function=None):
        # default function that can be overwrite or
        # can provide an experssion which 1/d or 1/d^2 or d^2etc.w*expression
        # can provide directly a function that take as
        # arguments the w and the distance
        if expression is not None:
            val = self.weight * expression(d)
        elif function is not None:
            val = function(self.weight, d)
        else:
            val = self.weight * 1.0 / d
        return val

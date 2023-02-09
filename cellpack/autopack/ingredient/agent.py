import numpy
import math

from cellpack.autopack.ingredient.partner import Partner

class Agent:
    def __init__(
        self,
        name,
        concentration,
        distance_expression=None,
        distance_function=None,
        force_random=False,  # avoid any binding
        gradient="",
        is_attractor=False,
        overwrite_distance_function=True,  # overWrite
        packing_mode="random",
        partners=None,
        place_method="jitter",
    ):
        self.name = name
        self.concentration = concentration
        self.partners = partners
        self.packing_mode = packing_mode

        assert self.packing_mode in [
            "random",
            "close",
            "closePartner",
            "randomPartner",
            "gradient",
            "hexatile",
            "squaretile",
            "triangletile",
        ]
        self.place_method = place_method
        self.mesh_3d = None
        self.is_attractor = is_attractor
        self.force_random = force_random
        self.distance_function = distance_function
        self.distance_expression = distance_expression
        self.overwrite_distance_function = overwrite_distance_function
        self.overwrite_distance_function = True
        self.gradient = gradient
        self.cb = None
        self.radii = None
        self.recipe = None  # weak ref to recipe
        self.tilling = None

    def getPartner(self, name):
        if name in self.partners:
            return self.partners[name]
        else:
            return None

    def addExcludedPartner(self, name, properties=None):
        self.excluded_partners[name] = Partner(name, properties=properties)

    def weightListByDistance(self, listePartner):
        probaArray = []
        w = 0.0
        for i, part, dist in listePartner:
            # print ("i",part,dist,w,part.weight)
            if self.overwrite_distance_function:
                wd = part.weight
            else:
                wd = part.distanceFunction(dist, expression=part.distance_expression)
            # print "calc ",dist, wd
            probaArray.append(wd)
            w = w + wd
        # probaArray.append(self.proba_not_binding)
        # w=w+self.proba_not_binding
        return probaArray, w

    def getProbaArray(self, weightD, total):
        probaArray = []
        final = 0.0
        for w in weightD:
            p = w / total
            #            print "norma ",w,total,p
            final = final + p
            probaArray.append(final)
        probaArray[-1] = 1.0
        return probaArray

    def getSubWeighted(self, weights):
        """
        From http://eli.thegreenplace.net/2010/01/22/weighted-random-generation-in-python/
        This method is about twice as fast as the binary-search technique,
        although it has the same complexity overall. Building the temporary
        list of totals turns out to be a major part of the functions runtime.
        This approach has another interesting property. If we manage to sort
        the weights in descending order before passing them to
        weighted_choice_sub, it will run even faster since the random
        call returns a uniformly distributed value and larger chunks of
        the total weight will be skipped in the beginning.
        """
        rnd = numpy.random.random() * sum(weights)
        if sum(weights) == 0:
            return None, None
        for i, w in enumerate(weights):
            rnd -= w
            if rnd < 0:
                return i, rnd
        return None, None

    def pickPartner(self, mingrs, listePartner, currentPos=[0, 0, 0]):
        # listePartner is (i,partner,d)
        # wieght using the distance function
        #        print "len",len(listePartner)
        targetPoint = None
        weightD, total = self.weightListByDistance(listePartner)
        self.log.info("w %r %d", weightD, total)
        i, b = self.getSubWeighted(weightD)
        if i is None:
            return None, None
        # probaArray = self.getProbaArray(weightD,total)
        #        print "p",probaArray
        #        probaArray=numpy.array(probaArray)
        #        #where is random in probaArray->index->ingr
        #        b = random()
        #        test = b < probaArray
        #        i = test.tolist().index(True)
        #        print "proba",i,test,(len(probaArray)-1)
        #        if i == (len(probaArray)-1) :
        #            #no binding due to proba not binding....
        #            print ("no binding due to proba")
        #            return None,b

        ing_indice = listePartner[i][0]  # i,part,dist
        ing = mingrs[2][ing_indice]  # [2]
        self.log.info("binding to %s" + ing.name)
        targetPoint = mingrs[0][ing_indice]  # [0]
        if self.compNum > 0:
            #            organelle = self.env.compartments[abs(self.compNum)-1]
            #            dist,ind = organelle.OGsrfPtsBht.query(targetPoint)
            #            organelle.ogsurfacePoints[]
            targetPoint = self.env.grid.getClosestFreeGridPoint(
                targetPoint,
                compId=self.compNum,
                ball=(ing.encapsulating_radius + self.encapsulating_radius),
                distance=self.encapsulating_radius * 2.0,
            )
            self.log.info(
                "target point free tree is %r %r %r",
                targetPoint,
                self.encapsulating_radius,
                ing.encapsulating_radius,
            )
        else:
            # get closestFreePoint using freePoint and masterGridPosition
            # if self.place_method == "rigid-body" or self.place_method == "jitter":
            # the new point is actually tPt -normalise(tPt-current)*radius
            self.log.info(
                "tP %r %s %r %d", ing_indice, ing.name, targetPoint, ing.radii[0][0]
            )
            # what I need it the closest free point from the target ingredient
            v = numpy.array(targetPoint) - numpy.array(currentPos)
            s = numpy.sum(v * v)
            factor = (v / math.sqrt(s)) * (
                ing.encapsulating_radius + self.encapsulating_radius
            )  # encapsulating radus ?
            targetPoint = numpy.array(targetPoint) - factor

        return targetPoint, b

    def pickPartnerInstance(self, bindingIngr, mingrs, currentPos=None):
        # bindingIngr is ingr,(weight,(instances indices))
        #        print "bindingIngr ",bindingIngr,bindingIngr[1]
        if currentPos is None:  # random mode
            picked_I = numpy.random() * len(bindingIngr[1][1])
            i = bindingIngr[1][1][picked_I]
        else:  # pick closest one
            mind = 99999999.9
            i = 0
            for ind in bindingIngr[1][1]:
                v = numpy.array(mingrs[ind][0]) - numpy.array(currentPos)
                d = numpy.sum(v * v)
                if d < mind:
                    mind = d
                    i = ind
        return i

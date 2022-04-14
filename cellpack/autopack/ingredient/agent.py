import numpy
import math


class Partner:
    def __init__(self, ingr, weight=0.0, properties=None):
        if type(ingr) is str:
            self.name = ingr
        else:
            self.name = ingr.name
        self.ingr = ingr
        self.weight = weight
        self.properties = {}
        self.distExpression = None
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


class Agent:
    def __init__(
        self,
        name,
        concentration,
        distExpression=None,
        distFunction=None,
        excluded_partners_name=None,
        force_random=False,  # avoid any binding
        gradient="",
        isAttractor=False,
        overwrite_distFunc=True,  # overWrite
        packingMode="close",
        partners_name=None,
        partners_position=None,
        placeType="jitter",
        proba_binding=0.5,
        proba_not_binding=0.5,  # chance to actually not bind
        properties=None,
        weight=0.2,  # use for affinity ie partner.weight
    ):
        self.name = name
        self.concentration = concentration
        self.partners = {}
        self.excluded_partners = {}
        # the partner position is the local position
        self.partners_position = partners_position or []
        self.partners_name = partners_name or []
        self.properties = properties
        if not self.partners_position:
            for i in self.partners_name:
                self.partners_position.append([numpy.identity(4)])
        excluded_partners_name = []
        self.excluded_partners_name = excluded_partners_name
        assert packingMode in [
            "random",
            "close",
            "closePartner",
            "randomPartner",
            "gradient",
            "hexatile",
            "squaretile",
            "triangletile",
        ]
        self.packingMode = packingMode
        partners_weight = 0
        self.partners_weight = partners_weight
        # assert placeType in ['jitter', 'spring','rigid-body']
        self.placeType = placeType
        self.mesh_3d = None
        self.isAttractor = isAttractor
        self.weight = weight
        self.proba_not_binding = proba_not_binding
        self.proba_binding = proba_binding
        self.force_random = force_random
        self.distFunction = distFunction
        self.distExpression = distExpression
        self.overwrite_distFunc = overwrite_distFunc
        self.overwrite_distFunc = True
        # chance to actually bind to any partner
        self.gradient = gradient
        self.cb = None
        self.radii = None
        self.recipe = None  # weak ref to recipe
        self.tilling = None

    def getProbaBinding(self, val=None):
        # get a value between 0.0 and 1.0and return the weight and success ?
        if val is None:
            val = numpy.random()
        if self.cb is not None:
            return self.cb(val)
        if val <= self.weight:
            return True, val
        else:
            return False, val

    def getPartnerweight(self, name):
        print("Deprecated use self.weight")
        partner = self.getPartner(name)
        w = partner.getProperties("weight")
        if w is not None:
            return w

    def getPartnersName(self):
        return list(self.partners.keys())

    def getPartner(self, name):
        if name in self.partners:
            return self.partners[name]
        else:
            return None

    def addPartner(self, ingr, weight=0.0, properties=None):
        if ingr.name not in self.partners:
            self.partners[ingr.name] = Partner(
                ingr, weight=weight, properties=properties
            )
        else:
            self.partners[ingr.name].weight = weight
            self.partners[ingr.name].properties = properties
        return self.partners[ingr.name]

    def getExcludedPartnersName(self):
        return list(self.excluded_partners.keys())

    def getExcludedPartner(self, name):
        if name in self.excluded_partners:
            return self.excluded_partners[name]
        else:
            return None

    def addExcludedPartner(self, name, properties=None):
        self.excluded_partners[name] = Partner(name, properties=properties)

    def sortPartner(self, listeP=None):
        if listeP is None:
            listeP = []
            for i, ingr in list(self.partners.keys()):
                listeP.append([i, ingr])
        # extract ing name unic
        listeIngrInstance = {}
        for i, ingr in listeP:
            if ingr.name not in listeIngrInstance:
                listeIngrInstance[ingr.name] = [ingr.weight, []]
            listeIngrInstance[ingr.name][1].append(i)
        # sort according ingredient binding weight (proba to bind)
        sortedListe = sorted(
            list(listeIngrInstance.items()), key=lambda elem: elem[1][0]
        )
        # sortedListe is [ingr,(weight,(instances indices))]
        # sort by weight/min->max
        # wIngrList = []
        # for i,ingr in listeP:
        # need to sort by ingr.weight
        #    wIngrList.append([i,ingr,ingr.weight])
        # sortedListe = sorted(wIngrList, key=lambda elem: elem[2])   # sort by weight/min->max
        #        print sortedListe
        return sortedListe

    def weightListByDistance(self, listePartner):
        probaArray = []
        w = 0.0
        for i, part, dist in listePartner:
            # print ("i",part,dist,w,part.weight)
            if self.overwrite_distFunc:
                wd = part.weight
            else:
                wd = part.distanceFunction(dist, expression=part.distExpression)
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
                ball=(ing.encapsulatingRadius + self.encapsulatingRadius),
                distance=self.encapsulatingRadius * 2.0,
            )
            self.log.info(
                "target point free tree is %r %r %r",
                targetPoint,
                self.encapsulatingRadius,
                ing.encapsulatingRadius,
            )
        else:
            # get closestFreePoint using freePoint and masterGridPosition
            # if self.placeType == "rigid-body" or self.placeType == "jitter":
            # the new point is actually tPt -normalise(tPt-current)*radius
            self.log.info(
                "tP %r %s %r %d", ing_indice, ing.name, targetPoint, ing.radii[0][0]
            )
            # what I need it the closest free point from the target ingredient
            v = numpy.array(targetPoint) - numpy.array(currentPos)
            s = numpy.sum(v * v)
            factor = (v / math.sqrt(s)) * (
                ing.encapsulatingRadius + self.encapsulatingRadius
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

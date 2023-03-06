import numpy
import math


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
        weight=0.2,
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
        self.gradient = gradient
        self.cb = None
        self.radii = None
        self.recipe = None  # weak ref to recipe
        self.tilling = None
        self.weight = weight

    def get_weights_by_distance(self, placed_partners):
        weights = []
        total = 0.0
        for _, partner, dist in placed_partners:
            if self.overwrite_distance_function:
                wd = partner.weight

            else:
                wd = partner.distanceFunction(
                    dist, expression=partner.distance_expression
                )
            weights.append(wd)
            total = total + wd
        # probaArray.append(self.proba_not_binding)
        # w=w+self.proba_not_binding
        return weights, total

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
            return None
        for i, w in enumerate(weights):
            rnd -= w
            if rnd < 0:
                return i
        return None

    def pick_partner_grid_index(
        self, near_by_ingredients, placed_partners, currentPos=[0, 0, 0]
    ):
        # placed_partners is (i,partner,d)
        # weight using the distance function
        targetPoint = None
        weightD, total = self.get_weights_by_distance(placed_partners)
        self.log.info(f"w {placed_partners} {total}")
        i = self.getSubWeighted(weightD)
        if i is None:
            return None, None
        partner_index = placed_partners[i][0]  # i,part,dist
        partner_ingredient = near_by_ingredients[2][partner_index]
        self.log.info(f"binding to {partner_ingredient.name}")
        targetPoint = near_by_ingredients[0][partner_index]
        if self.compNum > 0:
            #            organelle = self.env.compartments[abs(self.compNum)-1]
            #            dist,ind = organelle.OGsrfPtsBht.query(targetPoint)
            #            organelle.ogsurfacePoints[]
            targetPoint = self.env.grid.getClosestFreeGridPoint(
                targetPoint,
                compId=self.compNum,
                ball=(
                    partner_ingredient.encapsulating_radius + self.encapsulating_radius
                ),
                distance=self.encapsulating_radius * 2.0,
            )
            self.log.info(
                f"target point free tree is {targetPoint} {self.encapsulating_radius} {partner_ingredient.encapsulating_radius}"
            )
        else:
            # get closestFreePoint using freePoint and masterGridPosition
            # if self.place_method == "rigid-body" or self.place_method == "jitter":
            # the new point is actually tPt -normalise(tPt-current)*radius
            # what I need it the closest free point from the target ingredient
            v = numpy.array(targetPoint) - numpy.array(currentPos)
            s = numpy.sum(v * v)
            factor = (v / math.sqrt(s)) * (
                partner_ingredient.encapsulating_radius + self.encapsulating_radius
            )
            targetPoint = numpy.array(targetPoint) - factor

        return targetPoint

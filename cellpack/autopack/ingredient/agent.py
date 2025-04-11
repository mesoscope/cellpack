from random import random
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
        gradient=None,
        gradient_weights=None,
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

        # assert self.packing_mode in [
        #     "random",
        #     "close",
        #     "closePartner",
        #     "randomPartner",
        #     "gradient",
        #     "hexatile",
        #     "squaretile",
        #     "triangletile",
        # ]
        self.place_method = place_method
        self.mesh_3d = None
        self.is_attractor = is_attractor
        self.force_random = force_random
        self.distance_function = distance_function
        self.distance_expression = distance_expression
        self.overwrite_distance_function = overwrite_distance_function
        self.gradient = gradient
        self.gradient_weights = gradient_weights
        self.cb = None
        self.radii = None
        self.recipe = None  # weak ref to recipe
        self.tilling = None
        self.weight = weight

    def get_weights_by_distance(self, placed_partners):
        weights = []
        for _, partner, dist in placed_partners:
            if self.overwrite_distance_function:
                wd = partner.weight

            else:
                wd = partner.distanceFunction(
                    dist, expression=partner.distance_expression
                )
            weights.append(wd)
        return weights

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
        self, near_by_ingredients, placed_partners, current_packing_position=[0, 0, 0]
    ):
        # near_by_ingredient is [
        #   PackedObject
        #   distance[]
        # ]
        # placed_partners is (index,placed_partner_ingredient,distance_from_current_point)
        # weight using the distance function
        packing_position = None
        weightD = self.get_weights_by_distance(placed_partners)
        i = self.getSubWeighted(weightD)
        if i is None:
            return None
        partner_index = placed_partners[i][0]  # i,part,dist
        partner = placed_partners[i][1]
        partner_ingredient = near_by_ingredients[partner_index][0].ingredient
        self.log.info(f"binding to {partner_ingredient.name}")

        if self.compartment_id > 0:
            packing_position = self.env.grid.getClosestFreeGridPoint(
                packing_position,
                compId=self.compartment_id,
                ball=(
                    partner_ingredient.encapsulating_radius + self.encapsulating_radius
                ),
                distance=self.encapsulating_radius * 2.0,
            )
            return packing_position
        else:
            binding_probability = partner.binding_probability
            bind = True
            chance = random()
            if binding_probability > 0:
                bind = chance <= binding_probability
                if bind:
                    partner_position = near_by_ingredients[partner_index][0].position

                    # get closestFreePoint using freePoint and masterGridPosition
                    # if self.place_method == "rigid-body" or self.place_method == "jitter":
                    # the new point is actually tPt -normalise(tPt-current)*radius
                    # what I need it the closest free point from the target ingredient
                    v = numpy.array(partner_position) - numpy.array(
                        current_packing_position
                    )
                    s = numpy.sum(v * v)
                    factor = (v / math.sqrt(s)) * (
                        partner_ingredient.encapsulating_radius
                        + self.encapsulating_radius
                    )
                    packing_position = numpy.array(partner_position) - factor
                    return packing_position
                else:
                    return current_packing_position
            elif binding_probability < 0:
                for partner in placed_partners:
                    binding_probability = partner[1].binding_probability
                    repelled = chance <= abs(binding_probability)
                    if repelled:
                        partner_ingr = partner[1].ingredient
                        needed_distance = (
                            partner_ingr.encapsulating_radius
                            + self.encapsulating_radius
                        )
                        distance = partner[2][0]
                        if distance <= needed_distance:
                            return None
                return current_packing_position
            else:
                return current_packing_position

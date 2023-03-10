class Partner:
    def __init__(self, name, position, weight, binding_probability):
        self.name = name
        self.position = position
        self.weight = weight
        self.binding_probability = binding_probability
        # replaces self.properties
        # used in grow ingredient
        self.points = []
        self.margin_in = 0
        self.margin_out = 0
        self.dihedral = 0
        self.length = 0

    def set_ingredient(self, ingredient):
        self.ingredient = ingredient
        self.weight = ingredient.weight

    def get_point(self, index):
        if index >= len(self.points):
            return None
        return self.points[index]

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


class Partners:
    def __init__(self, partners):
        """
        This object holds the partner data
        ----------

        """
        # ONE PARTNER: {
        #     name:
        #     position
        #     weight
        #     binding_probably (negative value means repelled)
        # }
        self.all_partners = []
        #c copied this code in, not sure what exactly these weights 
        # are for or why they're distributed this way
        total = len(partners)
        weight_initial = 0.2
        weight = weight_initial
        for partner in partners:

            weight += ((1 - weight_initial) / (total)) - weight_initial
            partner = Partner(
                partner["name"],
                partner["position"] if "position" in partner else [0, 0, 0],
                partner["weight"] if "weight" in partner else weight,
                partner["binding_probability"]
                if "binding_probability" in partner
                else 1.0,
            )
            self.all_partners.append(partner)

    def add_partner(self, ingredient, probability_binding=0.5):
        partner = Partner(
            ingredient.name, [0, 0, 0], ingredient.weight, probability_binding
        )
        partner.set_ingredient(ingredient)
        self.all_partners.append(partner)

    def is_partner(self, full_ingredient_name):
        for partner in self.all_partners:
            if partner.name in full_ingredient_name:
                return True
        else:
            return False

    def get_partner_by_ingr_name(self, name):
        for partner in self.all_partners:
            if partner.ingredient and partner.ingredient.name == name:
                return partner
        else:
            return None

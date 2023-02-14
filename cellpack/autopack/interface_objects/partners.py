import numpy

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

class Partners:
    def __init__(
        self,
        settings
    ):
        """
        This object holds the partner data
        ----------

        """
        self.names = settings.get("names", [])
        self.positions = settings.get("positions", [])
        self.weight = settings.get("weight", 0)
        self.excluded_names = settings.get("excluded_names", [])
        self.probability_binding = settings.get("probability_binding", [])
        self.probability_repelled = settings.get("probability_repelled", [])
        self.excluded_ingredients = {}
        self.ingredients = {}

        # partner = {
        #     name:
        #     position
        #     weight
        #     probability_binding (negative value means repelled)
        # }

        if len(self.positions) == 0 :
            for i in self.names:
                self.positions.append([numpy.identity(4)])

    def set_partner(self, partner_ingredient):
        if partner_ingredient is None:
            return 
        if len(self.names) > 0:
            weight_initial = self.weight
            total = len(self.names) 
            w = float(weight_initial)
            if len(self.names) == 1:
                w = 1.0
                total = 2
                weight_initial = 1
                i = self.get_partner_index(partner_ingredient.name)
                if i < 0:
                    import ipdb; ipdb.set_trace()
                if i < len(self.positions):
                    partner = self.add_partner(
                        partner_ingredient,
                        weight=w,
                        properties={"position": self.positions[i]},
                    )
                else:
                    partner = self.add_partner(partner_ingredient, weight=w, properties={})
                # for p in partner_ingredient.properties:
                #     partner.addProperties(p, partner_ingredient.properties[p])
                w += ((1 - weight_initial) / (total - 1)) - weight_initial
    
    def is_partner(self, full_ingredient_name):
        return self.get_partner_index(full_ingredient_name) >= 0

    def get_partner_index(self, full_ingredient_name):
        for index, base_name in enumerate(self.names):
            if base_name in full_ingredient_name:
                return index
        else:
            return -1
    
    def get_partner_by_name(self, name):
        if name in self.ingredients:
            return self.ingredients[name]
        else:
            return None

    def add_partner(self, ingredient, weight=0.0, properties=None):
        if ingredient.name not in self.ingredients:
            self.ingredients[ingredient.name] = Partner(
                ingredient, weight=weight, properties=properties
            )
        else:
            self.ingredients[ingredient.name].weight = weight
            self.ingredients[ingredient.name].properties = properties
        return self.ingredients[ingredient.name]
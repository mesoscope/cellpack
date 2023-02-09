import numpy

from cellpack.autopack.ingredient.partner import Partner

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

        if len(self.positions) == 0 :
            for i in self.names:
                self.partners_position.append([numpy.identity(4)])

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
                if i < len(self.positions):
                    partner = self.add_partner(
                        partner_ingredient,
                        weight=w,
                        properties={"position": self.positions[i]},
                    )
                else:
                    partner = self.add_partner(partner_ingredient, weight=w, properties={})
                for p in partner_ingredient.properties:
                    partner.addProperties(p, partner_ingredient.properties[p])
                w += ((1 - weight_initial) / (total - 1)) - weight_initial
    
    def get_partner_index(self, name):
        if name in self.names:
            return self.names.index(name)
        else:
            return None     

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
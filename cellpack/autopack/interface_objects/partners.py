import numpy

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
        self.excluded_partners = {}

        if len(self.positions) == 0 :
            for i in self.names:
                self.partners_position.append([numpy.identity(4)])

    def get_probability_of_binding(self, val=None):
        # get a value between 0.0 and 1.0and return the weight and success ?
        if val is None:
            val = numpy.random()
        if self.cb is not None:
            return self.cb(val)
        if val <= self.weight:
            return True, val
        else:
            return False, val
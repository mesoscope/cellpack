from enum import Enum

"""
GradientData provides a class to pass sanitized arguments to create gradients
"""


class GradientOptions(Enum):
    # TODO: add option to reverse direction of gradient
    MODES = ["X", "Y", "Z", "direction", "radial", "surface"]


class GradientData:
    def __init__(self, gradient_options):
        """
        Takes in gradient_options dictionary from the recipe file to create a
        GradientData instance
        """
        pass

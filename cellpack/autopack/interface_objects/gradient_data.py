import copy
from cellpack.autopack.utils import deep_merge
from .meta_enum import MetaEnum
from .default_values import DEFAULT_GRADIENT_MODE_SETTINGS

"""
GradientData provides a class to pass sanitized arguments to create gradients
"""


class GradientModes(MetaEnum):
    """
    All available gradient modes
    """

    X = "X"
    Y = "Y"
    Z = "Z"
    VECTOR = "vector"
    RADIAL = "radial"
    SURFACE = "surface"


class WeightModes(MetaEnum):
    """
    All available weight modes
    """

    LINEAR = "linear"
    SQUARE = "square"
    CUBE = "cube"


class PickModes(MetaEnum):
    """
    All available pick modes
    """

    MAX = "max"
    MIN = "min"
    RND = "rnd"
    LINEAR = "linear"
    BINARY = "binary"
    SUB = "sub"
    REG = "reg"


class ModeOptions(MetaEnum):
    """
    All available options for individual modes
    """

    direction = "direction"
    center = "center"
    radius = "radius"
    gblob = "gblob"
    object = "object"
    scale_distance_between = "scale_distance_between"


REQUIRED_MODE_OPTIONS = {
    GradientModes.VECTOR: [ModeOptions.direction],
    GradientModes.RADIAL: [ModeOptions.center, ModeOptions.radius],
    GradientModes.SURFACE: [ModeOptions.object],
}

DIRECTION_MAP = {
    GradientModes.X: [1, 0, 0],
    GradientModes.Y: [0, 1, 0],
    GradientModes.Z: [0, 0, 1],
}


class GradientData:

    default_values = DEFAULT_GRADIENT_MODE_SETTINGS.copy()

    def __init__(self, gradient_options, gradient_name="default"):
        """
        Takes in gradient dictionary from the recipe file to create a
        GradientData instance
        """
        gradient_data = copy.deepcopy(GradientData.default_values)
        gradient_data["name"] = gradient_name
        gradient_data = deep_merge(gradient_data, gradient_options)
        self.validate_gradient_data(gradient_data)
        self.set_mode_properties(gradient_data)
        self.data = gradient_data

    def validate_gradient_data(self, gradient_data):

        if not GradientModes.is_member(gradient_data.get("mode")):
            raise ValueError(f"Invalid gradient mode: {gradient_data.get('mode')}")
        if not WeightModes.is_member(gradient_data.get("weight_mode")):
            raise ValueError(
                f"Invalid gradient weight mode: {gradient_data.get('weight_mode')}"
            )
        if not PickModes.is_member(gradient_data.get("pick_mode")):
            raise ValueError(
                f"Invalid gradient pick mode: {gradient_data.get('pick_mode')}"
            )
        self.validate_mode_settings(
            gradient_data["mode"], gradient_data.get("mode_settings")
        )

    def validate_mode_settings(self, mode_name, mode_settings_dict):

        required_options = REQUIRED_MODE_OPTIONS.get(mode_name)

        if required_options is None:
            return

        if not mode_settings_dict:
            raise ValueError(f"Missing mode settings for {mode_name}")

        for option in required_options:
            if option not in mode_settings_dict:
                raise ValueError(
                    f"Missing required mode setting {option} for {mode_name}"
                )

    def set_mode_properties(self, gradient_data):

        if not gradient_data.get("mode_settings"):
            gradient_data["mode_settings"] = {}

        if gradient_data["mode"] in [GradientModes.X, GradientModes.Y, GradientModes.Z]:

            direction_vector = DIRECTION_MAP[gradient_data["mode"]]

            if gradient_data.get("reversed"):
                direction_vector = [-1 * vec for vec in direction_vector]

            gradient_data["mode_settings"]["direction"] = direction_vector

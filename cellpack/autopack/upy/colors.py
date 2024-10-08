"""
    Copyright (C) <2010>  Autin L. TSRI

    This file git_upy/colors.py is part of upy.

    upy is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    upy is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with upy.  If not, see <http://www.gnu.org/licenses/gpl-3.0.html>.
"""

import numpy
from math import floor

IPRECISION = numpy.int32

color_names = [
    "aliceblue",
    "antiquewhite",
    "aqua",
    "aquamarine",
    "azure",
    "beige",
    "bisque",
    "black",
    "blanchedalmond",
    "blue",
    "blueviolet",
    "brown",
    "burlywood",
    "cadetblue",
    "chartreuse",
    "chocolate",
    "coral",
    "cornflowerblue",
    "cornsilk",
    "crimson",
    "cyan",
    "darkblue",
    "darkcyan",
    "darkgoldenrod",
    "darkgray",
    "darkgreen",
    "darkgrey",
    "darkkhaki",
    "darkmagenta",
    "darkolivegreen",
    "darkorange",
    "darkorchid",
    "darkred",
    "darksalmon",
    "darkseagreen",
    "darkslateblue",
    "darkslategray",
    "darkslategrey",
    "darkturquoise",
    "darkviolet",
    "deeppink",
    "deepskyblue",
    "dimgray",
    "dimgrey",
    "dodgerblue",
    "firebrick",
    "floralwhite",
    "forestgreen",
    "fuchsia",
    "gainsboro",
    "ghostwhite",
    "gold",
    "goldenrod",
    "gray",
    "green",
    "greenyellow",
    "grey",
    "honeydew",
    "hotpink",
    "indianred",
    "indigo",
    "ivory",
    "khaki",
    "lavender",
    "lavenderblush",
    "lawngreen",
    "lemonchiffon",
    "lightblue",
    "lightcoral",
    "lightcyan",
    "lightgoldenrodyellow",
    "lightgreen",
    "lightgrey",
    "lightpink",
    "lightsalmon",
    "lightseagreen",
    "lightskyblue",
    "lightslategray",
    "lightslategrey",
    "lightsteelblue",
    "lightyellow",
    "lime",
    "limegreen",
    "linen",
    "magenta",
    "maroon",
    "mediumaquamarine",
    "mediumblue",
    "mediumorchid",
    "mediumpurple",
    "mediumseagreen",
    "mediumslateblue",
    "mediumspringgreen",
    "mediumturquoise",
    "mediumvioletred",
    "midnightblue",
    "mintcream",
    "mistyrose",
    "moccasin",
    "navajowhite",
    "navy",
    "oldlace",
    "olive",
    "olivedrab",
    "orange",
    "orangered",
    "orchid",
    "palegoldenrod",
    "palegreen",
    "palevioletred",
    "papayawhip",
    "peachpuff",
    "peru",
    "pink",
    "plum",
    "powderblue",
    "purple",
    "red",
    "rosybrown",
    "royalblue",
    "saddlebrown",
    "salmon",
    "sandybrown",
    "seagreen",
    "seashell",
    "sienna",
    "silver",
    "skyblue",
    "slateblue",
    "slategray",
    "slategrey",
    "snow",
    "springgreen",
    "steelblue",
    "tan",
    "teal",
    "thistle",
    "tomato",
    "turquoise",
    "violet",
    "wheat",
    "white",
    "whitesmoke",
    "yellow",
    "yellowgreen",
]

indigo = (0.294, 0.000, 0.510)
gold = (1.000, 0.843, 0.000)
firebrick = (0.698, 0.133, 0.133)
indianred = (0.804, 0.361, 0.361)
yellow = (1.000, 1.000, 0.000)
darkolivegreen = (0.333, 0.420, 0.184)
darkseagreen = (0.561, 0.737, 0.561)
slategrey = (0.439, 0.502, 0.565)
darkslategrey = (0.184, 0.310, 0.310)
mediumvioletred = (0.780, 0.082, 0.522)
mediumorchid = (0.729, 0.333, 0.827)
chartreuse = (0.498, 1.000, 0.000)
mediumslateblue = (0.482, 0.408, 0.933)
black = (0.000, 0.000, 0.000)
springgreen = (0.000, 1.000, 0.498)
crimson = (0.863, 0.078, 0.235)
lightsalmon = (1.000, 0.627, 0.478)
brown = (0.647, 0.165, 0.165)
turquoise = (0.251, 0.878, 0.816)
olivedrab = (0.420, 0.557, 0.137)
cyan = (0.000, 1.000, 1.000)
silver = (0.753, 0.753, 0.753)
skyblue = (0.529, 0.808, 0.922)
gray = (0.502, 0.502, 0.502)
darkturquoise = (0.000, 0.808, 0.820)
goldenrod = (0.855, 0.647, 0.125)
darkgreen = (0.000, 0.392, 0.000)
darkviolet = (0.580, 0.000, 0.827)
darkgray = (0.663, 0.663, 0.663)
lightpink = (1.000, 0.714, 0.757)
teal = (0.000, 0.502, 0.502)
darkmagenta = (0.545, 0.000, 0.545)
lightgoldenrodyellow = (0.980, 0.980, 0.824)
lavender = (0.902, 0.902, 0.980)
yellowgreen = (0.604, 0.804, 0.196)
thistle = (0.847, 0.749, 0.847)
violet = (0.933, 0.510, 0.933)
navy = (0.000, 0.000, 0.502)
dimgrey = (0.412, 0.412, 0.412)
orchid = (0.855, 0.439, 0.839)
blue = (0.000, 0.000, 1.000)
ghostwhite = (0.973, 0.973, 1.000)
honeydew = (0.941, 1.000, 0.941)
cornflowerblue = (0.392, 0.584, 0.929)
darkblue = (0.000, 0.000, 0.545)
darkkhaki = (0.741, 0.718, 0.420)
mediumpurple = (0.576, 0.439, 0.859)
cornsilk = (1.000, 0.973, 0.863)
red = (1.000, 0.000, 0.000)
bisque = (1.000, 0.894, 0.769)
slategray = (0.439, 0.502, 0.565)
darkcyan = (0.000, 0.545, 0.545)
khaki = (0.941, 0.902, 0.549)
wheat = (0.961, 0.871, 0.702)
deepskyblue = (0.000, 0.749, 1.000)
darkred = (0.545, 0.000, 0.000)
steelblue = (0.275, 0.510, 0.706)
aliceblue = (0.941, 0.973, 1.000)
lightslategrey = (0.467, 0.533, 0.600)
gainsboro = (0.863, 0.863, 0.863)
mediumturquoise = (0.282, 0.820, 0.800)
floralwhite = (1.000, 0.980, 0.941)
coral = (1.000, 0.498, 0.314)
purple = (0.502, 0.000, 0.502)
lightgrey = (0.827, 0.827, 0.827)
lightcyan = (0.878, 1.000, 1.000)
darksalmon = (0.914, 0.588, 0.478)
beige = (0.961, 0.961, 0.863)
azure = (0.941, 1.000, 1.000)
lightsteelblue = (0.690, 0.769, 0.871)
oldlace = (0.992, 0.961, 0.902)
greenyellow = (0.678, 1.000, 0.184)
royalblue = (0.255, 0.412, 0.882)
lightseagreen = (0.125, 0.698, 0.667)
mistyrose = (1.000, 0.894, 0.882)
sienna = (0.627, 0.322, 0.176)
lightcoral = (0.941, 0.502, 0.502)
orangered = (1.000, 0.271, 0.000)
navajowhite = (1.000, 0.871, 0.678)
lime = (0.000, 1.000, 0.000)
palegreen = (0.596, 0.984, 0.596)
burlywood = (0.871, 0.722, 0.529)
seashell = (1.000, 0.961, 0.933)
mediumspringgreen = (0.000, 0.980, 0.604)
fuchsia = (1.000, 0.000, 1.000)
papayawhip = (1.000, 0.937, 0.835)
blanchedalmond = (1.000, 0.922, 0.804)
peru = (0.804, 0.522, 0.247)
aquamarine = (0.498, 1.000, 0.831)
white = (1.000, 1.000, 1.000)
darkslategray = (0.184, 0.310, 0.310)
ivory = (1.000, 1.000, 0.941)
dodgerblue = (0.118, 0.565, 1.000)
lemonchiffon = (1.000, 0.980, 0.804)
chocolate = (0.824, 0.412, 0.118)
orange = (1.000, 0.647, 0.000)
forestgreen = (0.133, 0.545, 0.133)
slateblue = (0.416, 0.353, 0.804)
olive = (0.502, 0.502, 0.000)
mintcream = (0.961, 1.000, 0.980)
antiquewhite = (0.980, 0.922, 0.843)
darkorange = (1.000, 0.549, 0.000)
cadetblue = (0.373, 0.620, 0.627)
moccasin = (1.000, 0.894, 0.710)
limegreen = (0.196, 0.804, 0.196)
saddlebrown = (0.545, 0.271, 0.075)
grey = (0.502, 0.502, 0.502)
darkslateblue = (0.282, 0.239, 0.545)
lightskyblue = (0.529, 0.808, 0.980)
deeppink = (1.000, 0.078, 0.576)
plum = (0.867, 0.627, 0.867)
aqua = (0.000, 1.000, 1.000)
darkgoldenrod = (0.722, 0.525, 0.043)
maroon = (0.502, 0.000, 0.000)
sandybrown = (0.980, 0.643, 0.376)
magenta = (1.000, 0.000, 1.000)
tan = (0.824, 0.706, 0.549)
rosybrown = (0.737, 0.561, 0.561)
pink = (1.000, 0.753, 0.796)
lightblue = (0.678, 0.847, 0.902)
palevioletred = (0.686, 0.933, 0.933)
mediumseagreen = (0.235, 0.702, 0.443)
dimgray = (0.412, 0.412, 0.412)
powderblue = (0.690, 0.878, 0.902)
seagreen = (0.180, 0.545, 0.341)
snow = (1.000, 0.980, 0.980)
mediumblue = (0.000, 0.000, 0.804)
midnightblue = (0.098, 0.098, 0.439)
palegoldenrod = (0.933, 0.910, 0.667)
whitesmoke = (0.961, 0.961, 0.961)
darkorchid = (0.600, 0.196, 0.800)
salmon = (0.980, 0.502, 0.447)
lightslategray = (0.467, 0.533, 0.600)
lawngreen = (0.486, 0.988, 0.000)
lightgreen = (0.565, 0.933, 0.565)
tomato = (1.000, 0.388, 0.278)
hotpink = (1.000, 0.412, 0.706)
lightyellow = (1.000, 1.000, 0.878)
lavenderblush = (1.000, 0.941, 0.961)
linen = (0.980, 0.941, 0.902)
mediumaquamarine = (0.400, 0.804, 0.667)
green = (0.000, 0.502, 0.000)
blueviolet = (0.541, 0.169, 0.886)
peachpuff = (1.000, 0.855, 0.725)
darkgrey = (0.663, 0.663, 0.663)


def RedWhiteBlueRamp(size=256):
    ramp = numpy.ones((size, 3), "f")
    mid = int(size / 2)
    incr = 1.0 / (mid - 1)
    for i in range(mid):
        ramp[i][1] = i * incr
        ramp[i][2] = i * incr
    for i in range(mid):
        ramp[mid + i][0] = 1.0 - (i * incr)
        ramp[mid + i][1] = 1.0 - (i * incr)
    return ramp


def getRamp(colors, size=256):
    if len(colors) == 2:
        ramp = TwoColorRamp(col1=colors[0], col2=colors[1], size=size)
    elif len(colors) == 3:
        ramp = ThreeColorRamp(col1=colors[0], col2=colors[1], col3=colors[2], size=size)
    else:
        ramp = None
    return ramp


def TwoColorRamp(col1=red, col2=white, size=256, alpha=False):
    n = 3
    if alpha:
        n = 4
    col1 = numpy.array(col1)
    col2 = numpy.array(col2)
    ramp = numpy.ones((size, n), "d")
    # interpolate from col1 to col2 along size
    for i in range(int(size)):
        ramp[i] = col1 + float(i) / float(size - 1) * (col2 - col1)
    # ramp = ramp/float(size-1)
    return ramp.astype("f")


def ThreeColorRamp(col1=blue, col2=white, col3=red, size=256, alpha=False):
    n = 3
    if alpha:
        n = 4
    col1 = numpy.array(col1)
    col2 = numpy.array(col2)
    col3 = numpy.array(col3)
    ramp = numpy.ones((size, n), "d")
    mid = int(size / 2)
    # interpolate from col1 to col2, then col2 to col3 along size
    for i in range(int(mid)):
        ramp[i] = col1 + float(i) / float(mid - 1) * (col2 - col1)
    for i in range(int(mid)):
        ramp[mid + i] = col2 + float(i) / float(mid - 1) * (col3 - col2)
    return ramp.astype("f")


def hexToRgb(c):
    split = (c[0:2], c[2:4], c[4:6])
    return [int(x, 16) for x in split]


def map_colors(values, colorMap, mini=None, maxi=None):
    """Get colors corresponding to values in a colormap"""

    values = numpy.array(values)
    if len(values.shape) == 2 and values.shape[1] == 1:
        values.shape = (values.shape[0],)
    elif len(values.shape) > 1:
        print("ERROR: values array has bad shape")
        return None

    cmap = numpy.array(colorMap)
    if len(cmap.shape) != 2 or cmap.shape[1] not in (3, 4):
        print("ERROR: colorMap array has bad shape")
        return None

    if mini is None:
        mini = min(values)
    else:
        values = numpy.maximum(values, mini)
    if maxi is None:
        maxi = max(values)
    else:
        values = numpy.minimum(values, maxi)
    valrange = maxi - mini
    if valrange < 0.0001:
        ind = numpy.ones(values.shape)
    else:
        colrange = cmap.shape[0] - 1
        ind = ((values - mini) * colrange) / valrange
    col = numpy.take(colorMap, ind.astype(IPRECISION))
    return col


def create_divergent_color_map_with_scaled_values(min_value, max_value, color_list):
    """
    Use case: you want a divergent scale centered at 0, but with drastically different
    negative scale and positive scale. Ie, min number is -20, and max is 2000.
    @param min_value: float value that is the min of the data
    @param max_value: float value max of the data
    @param color_list: array of color strings, either "red" or "rgb(222, 0, 0)"
    returns: a mapping from 0 to 1 with the appropriate step size for negative and positive values
    in the form [[0.0, 'rgb(222, 0, 0)'], ...]
    """
    middle_index = floor(
        len(color_list) / 2
    )  # the index of the color that will be mapped to 0
    # init map with all the same color
    color_map = [
        [i / (len(color_list) - 1), color_list[len(color_list) - 1]]
        for i in range(len(color_list))
    ]
    if min_value == max_value:
        return color_map
    zero_point = -min_value / (
        max_value - min_value
    )  # The value between 0 and 1 that maps to 0, ie the y intercept
    inside_step = (
        zero_point / middle_index
    )  # the spacing between points between min and zero point
    outside_step = (
        1 - zero_point
    ) / middle_index  # the spacing between points from zero point to max
    for i in range(len(color_list)):
        if i == len(color_list) - 1:
            # last value, fix any rounding issues
            color_map[i] = [1.0, color_list[i]]
        elif i < middle_index:
            color_map[i] = [i * inside_step, color_list[i]]
        elif i > middle_index:
            counter = i - middle_index
            color_map[i] = [zero_point + counter * outside_step, color_list[i]]
        else:
            color_map[i] = [zero_point, color_list[i]]
    return color_map

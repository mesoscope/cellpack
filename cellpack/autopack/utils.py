import collections
import copy

import numpy


def get_distance(pt1, pt2):
    return numpy.linalg.norm(pt2 - pt1)


def get_distances_from_point(np_array_of_pts, pt):
    return numpy.linalg.norm(np_array_of_pts - pt, axis=1)


def ingredient_compare1(x, y):
    """
    sort ingredients using decreasing priority and decreasing radii for
    priority ties and decreasing completion for radii ties
    for priority > 0
    """
    p1 = x.priority
    p2 = y.priority
    if p1 < p2:  # p1 > p2
        return 1
    elif p1 == p2:  # p1 == p1
        r1 = x.min_radius
        r2 = y.min_radius
        if r1 > r2:  # r1 < r2
            return 1
        elif r1 == r2:  # r1 == r2
            c1 = x.completion
            c2 = y.completion
            if c1 > c2:  # c1 > c2
                return 1
            elif c1 == c2:
                return 0
            else:
                return -1
        else:
            return -1
    else:
        return -1


def ingredient_compare0(x, y):
    """
    sort ingredients using decreasing priority and decreasing radii for
    priority ties and decreasing completion for radii ties
    for priority < 0
    """
    p1 = x.priority
    p2 = y.priority
    if p1 > p2:  # p1 > p2
        return 1
    elif p1 == p2:  # p1 == p1
        r1 = x.min_radius
        r2 = y.min_radius
        if r1 > r2:  # r1 < r2
            return 1
        elif r1 == r2:  # r1 == r2
            c1 = x.completion
            c2 = y.completion
            if c1 > c2:  # c1 > c2
                return 1
            elif c1 == c2:
                return 0
            else:
                return -1
        else:
            return -1
    else:
        return -1


def ingredient_compare2(x, y):
    """
    sort ingredients using decreasing radii and decresing completion
    for radii matches:
    priority = 0
    """
    c1 = x.min_radius
    c2 = y.min_radius
    if c1 < c2:
        return 1
    elif c1 == c2:
        r1 = x.completion
        r2 = y.completion
        if r1 > r2:
            return 1
        elif r1 == r2:
            return 0
        else:
            return -1
    else:  # x < y
        return -1


def cmp_to_key(mycmp):
    "Convert a cmp= function into a key= function"

    class K:
        def __init__(self, obj, *args):
            self.obj = obj

        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0

        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0

        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0

        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0

        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0

        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0

    return K


def deep_merge(dct, merge_dct):
    """Recursive dict merge

    This mutates dct - the contents of merge_dct are added to dct (which is also returned).
    If you want to keep dct you could call it like deep_merge(copy.deepcopy(dct), merge_dct)
    """
    if dct is None:
        dct = {}
    if merge_dct is None:
        merge_dct = {}
    for k, v in merge_dct.items():
        if (
            k in dct
            and isinstance(dct[k], dict)
            and isinstance(merge_dct[k], collections.abc.Mapping)
        ):
            deep_merge(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]
    return dct


def expand_object_using_key(current_object, expand_on, lookup_dict):
    object_key = current_object[expand_on]
    base_object = lookup_dict[object_key]
    new_object = deep_merge(copy.deepcopy(base_object), current_object)
    del new_object[expand_on]
    return new_object


def check_paired_key(val_dict, key1=None, key2=None):
    """
    Checks if the key pair exists in dict
    """
    for key in val_dict:
        if (key1 in key) and (key2 in key):
            return True
    return False


def get_paired_key(val_dict, key1=None, key2=None):
    """
    Get the combined key from dict
    """
    for key in val_dict:
        if (key1 in key) and (key2 in key):
            return key


def get_min_value_from_distribution(distribution_options, return_int=False):
    """
    Returns a low bound on the value from a distribution
    """
    value = None
    if distribution_options.get("distribution") == "uniform":
        value = distribution_options.get("min", 1)

    if distribution_options.get("distribution") == "normal":
        value = distribution_options.get("mean", 0) - 2 * distribution_options.get(
            "std", 1
        )

    if distribution_options.get("distribution") == "list":
        value = numpy.nanmin(distribution_options.get("list_values", None))

    if return_int and value is not None:
        value = int(numpy.rint(value))

    return value


def get_max_value_from_distribution(distribution_options, return_int=False):
    """
    Returns a high bound on the value from a distribution
    """
    value = None
    if distribution_options.get("distribution") == "uniform":
        value = distribution_options.get("max", 1)

    if distribution_options.get("distribution") == "normal":
        value = distribution_options.get("mean", 0) + 2 * distribution_options.get(
            "std", 1
        )

    if distribution_options.get("distribution") == "list":
        value = numpy.nanmax(distribution_options.get("list_values", None))

    if return_int and value is not None:
        value = int(numpy.rint(value))

    return value


def get_value_from_distribution(distribution_options, return_int=False):
    """
    Returns a value from the distribution options
    """
    if distribution_options.get("distribution") == "uniform":
        if return_int:
            return int(
                numpy.random.randint(
                    distribution_options.get("min", 0),
                    distribution_options.get("max", 1),
                )
            )
        else:
            return numpy.random.uniform(
                distribution_options.get("min", 0),
                distribution_options.get("max", 1),
            )
    if distribution_options.get("distribution") == "normal":
        value = numpy.random.normal(
            distribution_options.get("mean", 0), distribution_options.get("std", 1)
        )
    elif distribution_options.get("distribution") == "list":
        value = numpy.random.choice(distribution_options.get("list_values", None))
    else:
        value = None

    if return_int and value is not None:
        value = int(numpy.rint(value))

    return value


def get_seed_list(packing_config_data, recipe_data):
    # Returns a list of seeds to use for packing
    if packing_config_data["randomness_seed"] is not None:
        seed_list = packing_config_data["randomness_seed"]
    elif recipe_data.get("randomness_seed") is not None:
        seed_list = recipe_data["randomness_seed"]
    else:
        seed_list = None

    if isinstance(seed_list, int):
        seed_list = [seed_list]

    if (seed_list is not None) and (
        len(seed_list) != packing_config_data["number_of_packings"]
    ):
        base_seed = int(seed_list[0])
        seed_list = [
            base_seed + i for i in range(packing_config_data["number_of_packings"])
        ]

    return seed_list

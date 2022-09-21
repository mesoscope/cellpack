import collections
import numpy


def get_distance(pt1, pt2):
    return numpy.linalg.norm(pt2 - pt1)


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

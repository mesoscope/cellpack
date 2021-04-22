## Automatically adapted for numpy.oldnumeric Jul 30, 2007 by

import sys
from mglutil.regression import testplus
import numpy.oldnumeric as Numeric

points = None


def setUpSuite():
    from bhtree import bhtreelib

    print(("bhtreelib imported from: ", bhtreelib.__file__))


def test_buildTreeForSpheres():
    print("#### test_buildTreeForSpheres ###")
    # 1 - build a fixed size BHtree for a set of spheres (points with radii)
    #   radii come into play when calling closePointsPairs
    # 2 - retrieve points within 10.0 from (0.0, 0.0, 0.0)

    from bhtree import bhtreelib

    # load a bunch of 3D points
    from .crn_crd_and_rad import pts

    # build a BHTree for 3D points (xyz), radii
    # granularity=10
    #     granularity specifies the maximum number of points per leaf node
    rad = [x[3] for x in pts]
    xyz = [x[:3] for x in pts]
    bht = bhtreelib.BHtree(xyz, rad, 10)

    # allocate an array for results of query
    # the array has to be long enough to hold the indices of all points
    # found.
    result = Numeric.zeros((len(pts),)).astype("i")

    # find all points in pts within 10.0 deom (0.,0.,0.)
    # nb will be the number of points, result[:nb] will hold the indices
    nb = bht.closePoints((0.0, 0.0, 0.0), 10.0, result)

    assert nb == 53

    # delete the tree
    del bht


def test_badPoints():
    # 1 - build a fixed size BHtree for a set of spheres (points with radii)
    #   radii come into play when calling closePointsPairs
    # 2 - retrieve points within 10.0 from (0.0, 0.0, 0.0)

    print("#### test_badPoints ####")
    from bhtree import bhtreelib

    from .crn_crd_and_rad import pts

    rad = [x[3] for x in pts]
    # pass an Nx4 array for points .. this has to raise a ValueError
    try:
        bht = bhtreelib.BHtree(pts, rad, 10)
        assert 0, "failed to raise ValueError for bad first argument"
    except ValueError:
        pass


def test_badNumberOfRadii():
    print("#### test_badNumberOfRadii ####")
    from bhtree import bhtreelib

    from .crn_crd_and_rad import pts

    rad = [x[3] for x in pts]
    # pass a number of radii that does not match the number of points
    try:
        bht = bhtreelib.BHtree(pts, rad[:10], 10)
        assert 0, "failed to raise ValueError for bad set of radii"
    except ValueError:
        pass


def test_noRadii():
    print("#### test_noRadii ####")
    from bhtree import bhtreelib

    from .crn_crd_and_rad import pts

    xyz = [x[:3] for x in pts]
    bht = bhtreelib.BHtree(xyz, None, 10)

    # delete the tree
    del bht


def test_findAllCloseWithRadii():
    print("#### test_findAllCloseWithRadii ####")
    from bhtree import bhtreelib

    # load a bunch of 3D points
    from .crn_crd_and_rad import pts

    # build a BHTree for the points, their ids
    # granularity=10
    #     granularity specifies the maximum number of points per leaf node
    rad = [x[3] for x in pts]
    xyz = [x[:3] for x in pts]
    bht = bhtreelib.BHtree(xyz, rad, 10)

    # find all pairs of atoms for which the distance is less than 1.1
    # times the sum of the radii
    pairs = bht.closePointsPairsInTree(1.1)
    assert len(pairs) == 337

    # delete the tree
    del bht


def test_findAllCloseNoRadii():
    print("#### test_findAllCloseNoRadii ####")
    from bhtree import bhtreelib

    # load a bunch of 3D points
    from .crn_crd_and_rad import pts

    # build a BHTree for the points, their ids
    # granularity=10
    #     granularity specifies the maximum number of points per leaf node
    xyz = [x[:3] for x in pts]
    bht = bhtreelib.BHtree(xyz, None, 10)

    # find all pairs of atoms for which the distance is less than 1.1
    # times the sum of the radii
    pairs = bht.closePointsPairsInTree(1.1)

    assert len(pairs) == 0

    # delete the tree
    del bht


def test_findClosePairsWithSecondSetOfPoints():
    print("#### test_findClosePairsWithSecondSetOfPoints ####")
    # no radii, we should find no pairs
    from bhtree import bhtreelib

    # load a bunch of 3D points
    from .crn_crd_and_rad import pts

    pts1 = pts
    from .cv_crd_and_rad import pts

    pts2 = pts

    # build a BHTree for the points, their ids
    # granularity=10
    #     granularity specifies the maximum number of points per leaf node
    xyz = [x[:3] for x in pts1]
    bht = bhtreelib.BHtree(xyz, None, 10)

    # find all pairs of atoms (pi,pj) for which the distance is less than 1.1
    # times the sum of the radii. Pi belongs to pts2 ant pj is a point from
    # the bhtree
    xyz = [x[:3] for x in pts2]
    pairs = bht.closePointsPairs(xyz, None, 1.0)
    assert len(pairs) == 0

    # delete the tree
    del bht


def test_findClosePairsWithSecondSetOfSpheres():
    print("#### test_findClosePairsWithSecondSetOfSpheres ####")
    # we use radii, we should find pairs that are close
    from bhtree import bhtreelib

    # load a bunch of 3D points
    from .crn_crd_and_rad import pts

    pts1 = pts
    from .cv_crd_and_rad import pts

    pts2 = pts

    # build a BHTree for the points, their ids
    # granularity=10
    #     granularity specifies the maximum number of points per leaf node
    xyz = [x[:3] for x in pts1]
    rad = [x[3] for x in pts1]
    bht = bhtreelib.BHtree(xyz, rad, 10)

    # find all pairs of atoms (pi,pj) for which the distance is less than 1.1
    # times the sum of the radii. Pi belongs to pts2 ant pj is a point from
    # the bhtree
    xyz = [x[:3] for x in pts2]
    rad = [x[3] for x in pts2]
    pairs = bht.closePointsPairs(xyz, rad, 1.1)
    assert len(pairs) == 4

    # delete the tree
    del bht


def test_closestPointsArray():
    print("#### test_closestPointsArray ####")
    from bhtree import bhtreelib

    # load a bunch of 3D points
    from .crn_crd_and_rad import pts

    pts1 = [x[:3] for x in pts]
    from .cv_crd_and_rad import pts

    pts2 = [x[:3] for x in pts]

    # build a BHTree for pts1
    bht = bhtreelib.BHtree(pts1, None, 10)
    points = bht.closestPointsArray(pts2, 10)
    check_points = [
        133,
        133,
        108,
        133,
        133,
        133,
        133,
        98,
        98,
        97,
        109,
        109,
        109,
        133,
        127,
        108,
        108,
        108,
        108,
        108,
        108,
        108,
        108,
        211,
        133,
        133,
        133,
        108,
        108,
        108,
        108,
        108,
        108,
        108,
        211,
        211,
        108,
        133,
        109,
        108,
        133,
        133,
        133,
        109,
        133,
        133,
        133,
        133,
        141,
        108,
        133,
        106,
        98,
        99,
        109,
        109,
        133,
        109,
        108,
        127,
    ]
    assert points.tolist() == check_points


def test_closestPointsArrayDist2():
    print("#### test_closestPointsArrayDist2 ####")
    from bhtree import bhtreelib

    # load a bunch of 3D points
    from .crn_crd_and_rad import pts

    pts1 = [x[:3] for x in pts]
    from .cv_crd_and_rad import pts

    pts2 = [x[:3] for x in pts]

    # build a BHTree for pts1
    bht = bhtreelib.BHtree(pts1, None, 10)
    points, dist = bht.closestPointsArrayDist2(pts2, 10)
    check_points = [
        133,
        133,
        108,
        133,
        133,
        133,
        133,
        98,
        98,
        97,
        109,
        109,
        109,
        133,
        127,
        108,
        108,
        108,
        108,
        108,
        108,
        108,
        108,
        211,
        133,
        133,
        133,
        108,
        108,
        108,
        108,
        108,
        108,
        108,
        211,
        211,
        108,
        133,
        109,
        108,
        133,
        133,
        133,
        109,
        133,
        133,
        133,
        133,
        141,
        108,
        133,
        106,
        98,
        99,
        109,
        109,
        133,
        109,
        108,
        127,
    ]
    assert points.tolist() == check_points
    # print "DISTANSES:"
    # print dist
    assert dist.shape == (len(points),)


def test_tbhtree_ClosePoints():
    print("#### test_tbhtree_ClosePoints####")
    # 1 - build a TBHtree (points can be added and moved, NOT deleted)
    # 2 - retrieve points within 10.0 from (0.0, 0.0, 0.0)

    from bhtree import bhtreelib

    # load a bunch of 3D points
    from .crn_crd import pts

    # create an array of IDs for these points
    ids = Numeric.arrayrange(len(pts)).astype("i")
    # build a TBHTree for the points, their ids
    # granularity=10
    #     granularity specifies the maximum number of points per leaf node
    # LeafPadding=10
    #     Padding added to the array of points in each leaf;
    #     The number of new points that can be added to each box
    #     through the move and insert commands
    # SpacePadding=9999.0
    #      SpacePadding is the amount of void "padding" space stored around
    #      the tree to allow inserts and moves outside of the original
    #      boundaries of the tree
    #

    bht = bhtreelib.TBHTree(pts, ids, 10, 10, 9999.0)

    # allocate an array for results of query
    # the array has to be long enough to hold the indices of all points
    # found.
    result = Numeric.zeros((len(pts),)).astype("i")

    # find all points in pts within 10.0 deom (0.,0.,0.)
    # nb will be the number of points, result[:nb] will hold the indices
    nb = bht.ClosePoints((0.0, 0.0, 0.0), 10.0, result)

    assert nb == 53

    # delete the tree
    del bht


def test_refCount():
    """tests a function that takes Numeric array  arguments. Checks that there is no
    memory leak by counting reference of the Numeric array objects."""

    print("#### test_refCount ####")
    from bhtree import bhtreelib
    from .crn_crd_and_rad import pts

    xyz = [x[:3] for x in pts]
    bht = bhtreelib.BHtree(xyz, None, 10)
    i = 0
    while i < 10:
        indices = Numeric.zeros((len(xyz),)).astype("i")
        dist = Numeric.zeros((len(xyz),)).astype("f")
        nb = bht.closePointsDist2((0.0, 0.0, 0.0), 10.0, indices, dist)
        i += 1
    assert sys.getrefcount(indices) == 2
    assert sys.getrefcount(dist) == 2

    # delete the tree
    del bht


if __name__ == "__main__":
    testplus.chdir()
    harness = testplus.TestHarness(
        __name__,
        connect=(setUpSuite, (), {}),
        funs=testplus.testcollect(globals()),
    )
    print(harness)
    sys.exit(len(harness))

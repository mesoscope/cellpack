## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by

import sys, os, math, types, string
from Tkinter import Menubutton
import unittest
from math import sqrt
import numpy.oldnumeric as Numeric
from DejaVu.Viewer import Viewer
from DejaVu.Ellipsoids import Ellipsoids
from string import split
import Image


class Ellipsoids__init__Tests(unittest.TestCase):
    """
    tests for init: default values supplied for shape, slices, stacks, radius
    NB: if quality is supplied, it overrides default slices and stacks
    """

    def test_defaults(self):
        """
        test init with no parameters
        """
        g = Ellipsoids()
        self.assertEqual(isinstance(g, Ellipsoids), True)

    def test_centers(self):
        """
        test init with centers
        """
        g = Ellipsoids(centers=[[1, 1, 1], [5, 5, 5]])
        self.assertEqual(isinstance(g, Ellipsoids), True)

    def test_shape(self):
        """
        test init with shape
        """
        g = Ellipsoids(shape=(0, 2))
        self.assertEqual(isinstance(g, Ellipsoids), True)

    def test_quality(self):
        """
        test init with quality
        """
        g = Ellipsoids(quality=15)
        self.assertEqual(isinstance(g, Ellipsoids), True)


class Ellipsoids_Set_Tests(unittest.TestCase):
    """
    tests for Set:
    """

    def setUp(self):
        """
        setup Ellipsoid Geom
        """
        rotcrn = Numeric.array(
            [
                [0.62831, -0.67899, -0.37974, 0],
                [0.36979, 0.69011, -0.62210, 0],
                [0.68446, 0.25045, 0.68468, 0],
                [0, 0, 0, 1],
            ],
            "f",
        )
        transcrn = [9.26883, 9.78728, 6.96709]
        scalecrn = [8.0957, 11.7227, 16.2550]
        rotcv = Numeric.identity(4, "f")
        transcv = [0.0, 0.0, 0.0]
        scalecv = [7.8895, 5.5336, 3.3147]
        self.geom = Ellipsoids(
            "ellipsoids1",
            centers=[transcv, transcrn],
            scaling=[scalecv, scalecrn],
            orientation=[rotcv, rotcrn],
            materials=[[1, 0, 0], [0, 1, 0]],
            inheritMaterial=0,
            quality=30,
        )

    def tearDown(self):
        """
        clean-up
        """
        try:
            del self.geom
        except:
            pass

    # centers
    def test_Set_centers(self):
        """tests valid input for center"""
        self.geom.Set(centers=[[1, 1, 1], [5, 5, 5]])
        self.assertEqual(
            split(str(self.geom.vertexSet.vertices.array), "\n"),
            ["[[ 1.  1.  1.]", " [ 5.  5.  5.]]"],
        )

    def test_ellipsoids_center_invalid(self):
        """tests invalid input for center"""
        # self.assertRaises(AttributeError, self.geom.Set,centers ='hai')
        self.assertRaises(ValueError, self.geom.Set, centers="hai")

    # quality AND
    # slices ???

    def test_Set_quality(self):
        """
        test Set with quality changes stacks
        """
        val = 10
        self.geom.Set(quality=val)
        self.assertEqual(self.geom.stacks, val)

    def test_ellipsoids_quality_slices(self):
        """tests valid input for quality"""
        self.geom.Set(quality=10)
        self.assertEqual(self.geom.slices, 10)

    def xtest_ellipsoids_quality_invalid(self):
        """tests invalid input for quality
        ###### it seems that we have always been accepting this invalid data ####
        """
        self.geom.Set(quality="hai")
        self.assertNotEqual(self.geom.slices, "hai")
        self.assertNotEqual(self.geom.stacks, "hai")

    # scaling
    def test_ellipsoids_scaling(self):
        """tests valid input for scaling"""
        self.geom.Set(scaling=[[8, 8, 8], [7.5, 7.5, 7.5]])
        self.assertEqual(
            split(str(self.geom.scaling), "\n"),
            ["[[ 8.   8.   8. ]", " [ 7.5  7.5  7.5]]"],
        )

    def test_ellipsoids_scaling_invalid(self):
        """tests invalid input for scaling"""
        #        self.geom.Set(scaling ='hai')
        #        self.assertNotEqual(self.geom.scaling, 'hai')
        self.assertRaises(ValueError, self.geom.Set, scaling="hai")

    ##orientation
    #    def test_ellipsoids_orientation(self):
    #        """tests valid input for orientation
    #        """
    #        a = Numeric.array( [[0.52831, -0.57899, -0.57974, 0],[0.56979,  0.89011, -0.42210, 0],[0.48446,  0.15045,  0.97, 0],[0, 0, 0, 1]], 'f')
    #        b = Numeric.identity(4, 'f')
    #        self.geom.Set(orientation = [b,a])
    #        result = [[[ 1.        ,  0.        ,  0.        ,  0.        ],
    #        [ 0.        ,  1.        ,  0.        ,  0.        ],
    #        [ 0.        ,  0.        ,  1.        ,  0.        ],
    #        [ 0.        ,  0.        ,  0.        ,  1.        ]],
    #       [[ 0.52831   , -0.57898998, -0.57973999,  0.        ],
    #        [ 0.56979001,  0.89011002, -0.42210001,  0.        ],
    #        [ 0.48446   ,  0.15045001,  0.97000003,  0.        ],
    #        [ 0.        ,  0.        ,  0.        ,  1.        ]]]
    #        self.assertTrue(numpy.alltrue(self.geom.orientation==result))

    def test_ellipsoids_orientation_invalid(self):
        """tests invalid input for orientation"""
        self.assertRaises(ValueError, self.geom.Set, orientation="hai")

    # stacks
    def test_ellipsoids_stacks(self):
        """tests valid input for stacks"""
        self.geom.Set(stacks=25)
        self.assertEqual(self.geom.stacks, 25)

    def xtest_ellipsoids_stacks_invalid(self):
        """tests invalid input for stacks
        ###### it seems that we have always been accepting this invalid data ####
        """
        self.geom.Set(stacks="hai")
        self.assertNotEqual(self.geom.stacks, "hai")


class Ellipsoids_Viewer_Tests(unittest.TestCase):
    """
    setUp + tearDown form a fixture: working environment for the testing code
    """

    def setUp(self):
        """
        start Viewer
        """
        self.vi = Viewer(verbose=0)
        rotcrn = Numeric.array(
            [
                [0.62831, -0.67899, -0.37974, 0],
                [0.36979, 0.69011, -0.62210, 0],
                [0.68446, 0.25045, 0.68468, 0],
                [0, 0, 0, 1],
            ],
            "f",
        )
        transcrn = [9.26883, 9.78728, 6.96709]
        scalecrn = [8.0957, 11.7227, 16.2550]
        rotcv = Numeric.identity(4, "f")
        transcv = [0.0, 0.0, 0.0]
        scalecv = [7.8895, 5.5336, 3.3147]
        self.geom = Ellipsoids(
            "ellipsoids",
            centers=[transcv, transcrn],
            scaling=[scalecv, scalecrn],
            orientation=[rotcv, rotcrn],
            materials=((1, 0, 0),),
            inheritMaterial=0,
            quality=30,
        )
        self.vi.AddObject(self.geom)
        self.vi.update()
        self.vi.currentCamera.DoPick(0.0, 0.0)
        self.vi.SetCurrentObject(self.geom)

    def tearDown(self):
        """
        clean-up
        """
        try:
            self.vi.Exit()
        except:
            pass

    # one test of setting properties via DejaVuGui...
    def test_Ellipsoids_inheritMaterial(self):
        """valid changing material by toggling inheritMaterial"""
        """ NOTE toggling is done by invoking a button in dejaVuGUI
this test checks pixel in the middle of the scene when the object does not
inheritMaterial and is colored RED vs after inheritMaterial is restored when
the object is white (well grayish)
"""
        cam = self.vi.currentCamera
        cam.Set(height=200, width=200)
        self.vi.OneRedraw()
        self.vi.update()
        buff = cam.GrabFrontBufferAsArray()
        total_pixels = len(buff) / 3
        effective_height = int(sqrt(total_pixels))
        midpt = int(effective_height / 2)
        buff.shape = (effective_height, effective_height, 3)
        buff_255 = buff / 255.0
        # print "1:midpt=", buff_255[midpt][midpt]
        self.assertEqual(round(buff_255[midpt + 1][midpt + 1][1], 1) <= 0.1, True)
        self.vi.OneRedraw()
        self.vi.update()
        for c in self.vi.GUI.inheritF.children.values():
            if c.__class__ == Menubutton and c.configure("text")[-1] == (
                "Current",
                "geom",
                "properties",
            ):
                self.inheritF_menu = c.menu
        inheritMaterial_index = self.inheritF_menu.index("inheritMaterial")
        self.inheritF_menu.invoke(inheritMaterial_index)
        newstate = self.geom.getState()["inheritMaterial"]
        # print "now self.geom.inheritMaterial=", newstate
        self.assertEqual(newstate, 1)
        self.vi.OneRedraw()
        buff = cam.GrabFrontBufferAsArray()
        total_pixels = len(buff) / 3
        effective_height = int(sqrt(total_pixels))
        midpt = int(effective_height / 2)
        buff.shape = (effective_height, effective_height, 3)
        buff_255 = buff / 255.0
        # print "midpt=", buff_255[midpt][midpt]
        self.assertEqual(round(buff_255[midpt][midpt][0], 1) >= 0.4, True)

    def test_ellipsoids_image(self):
        """valid image..checked by writing/reading a tif file"""

        cam = self.vi.currentCamera
        cam.Set(height=200, width=200)
        self.vi.OneRedraw()
        self.vi.update()
        buff = cam.GrabFrontBufferAsArray()
        total_pixels = len(buff) / 3
        effective_height = int(sqrt(total_pixels))
        midpt = int(effective_height / 2)
        buff.shape = (effective_height, effective_height, 3)
        buff_255 = buff / 255.0
        # print "pixel at midpoint of buffer=", buff_255[midpt][midpt]
        # check that the pixel is not black
        self.assertEqual(round(buff_255[midpt][midpt][0], 1) > 0.1, True)
        buff_255_sum = Numeric.add.reduce(buff_255)
        cam.SaveImage("./saveimageel.tif")
        im = Image.open("./saveimageel.tif")
        im = im.tostring()
        narray = Numeric.fromstring(im, "B")
        # print narray.shape
        narray.shape = (effective_height, effective_height, 3)
        narray_255 = narray / 255.0
        narray_255_sum = Numeric.add.reduce(narray_255)
        # print sum
        d = buff_255_sum - narray_255_sum
        # self.assertEqual(d,0)
        for v in d:
            self.assertTrue(v[0] < 1.0e-9)
            self.assertTrue(v[1] < 1.0e-9)
            self.assertTrue(v[2] < 1.0e-9)


if __name__ == "__main__":
    test_cases = [
        "Ellipsoids__init__Tests",
        "Ellipsoids_Set_Tests",
        "Ellipsoids_Viewer_Tests",
    ]

    unittest.main(
        argv=(
            [
                __name__,
            ]
            + test_cases
        )
    )
    # unittest.main()

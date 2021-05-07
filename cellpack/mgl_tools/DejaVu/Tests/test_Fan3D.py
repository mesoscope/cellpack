## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by

#
#
# $Id: test_Fan3D.py,v 1.16 2009/04/20 22:17:25 vareille Exp $
#
#

import sys, os, math, types
import numpy
from Tkinter import Menubutton
import unittest, numpy.oldnumeric as Numeric
from DejaVu.Viewer import Viewer
from time import sleep
import Image
from math import sqrt
from DejaVu.Arcs3D import Fan3D


class Fan3D__init__Tests(unittest.TestCase):
    """test keywords for __init__:
    keywords = ['radii',
                'angles',
                'vectors']

    all other keywords are handled by Geom.__init__ method"""

    # defaults
    def test_Fan3D_defaults(self):
        """defaults for radii, angles, vectors"""
        g = Fan3D()
        self.assertEqual(isinstance(g, Fan3D), True)

    # radii
    def test_Fan3D_radii(self):
        """radii 2 (default radii is 0.2)"""
        g = Fan3D(radii=2.0)
        self.assertEqual(isinstance(g, Fan3D), True)

    # angles
    def test_Fan3D_angles(self):
        """angles 180., (default angles = (360.0,))"""
        g = Fan3D(angles=180.0)
        self.assertEqual(isinstance(g, Fan3D), True)

    # vectors
    def test_Fan3D_angles(self):
        """vectors (.5,0,0) (default vectors is ((1.,0,0),))"""
        g = Fan3D(vectors=(0.5, 0.0, 0.0))
        self.assertEqual(isinstance(g, Fan3D), True)


class Fan3D_Set_Tests(unittest.TestCase):
    """
    # doesnot override Geom.Set so just one test that baseclass Set is called"""

    def setUp(self):
        """
        create geom
        """
        self.geom = Fan3D(name="test", angles=(30.0))

    def tearDown(self):
        """
        clean-up
        """
        try:
            del self.geom
        except:
            pass

    def test_Fan3D_Set_angles(self):
        """
        Set angles by call to Set
        """
        self.geom.Set(angles=180.0)
        self.assertEqual(self.geom.angles, [180.0])

    def test_Fan3D_Set_radii(self):
        """
        Set radii by call to Set
        """
        self.geom.Set(radii=3.0)
        self.assertEqual(self.geom.radii, [3.0])

    def test_Fan3D_Set_vectors(self):
        """
        Set vectors by call to Set
        """
        self.geom.Set(vectors=(1.0, 1.0, 0.0))
        self.assertEqual(self.geom.vectors, [(1.0, 1.0, 0.0)])

    def test_Fan3D_Set_name(self):
        """
        test Setting name
        """
        val = "new_name"
        self.geom.Set(name=val)
        self.assertEqual(self.geom.name, val)

    # INVALID INPUTS

    def test_Fan3D_Set_angles_invalid(self):
        """
        Set inavlid angles by call to Set
        """
        self.assertRaises(ValueError, self.geom.Set, angles="a")

    def test_Fan3D_Set_radii_invalid(self):
        """
        Set invalid radii by call to Set
        """
        self.assertRaises(ValueError, self.geom.Set, radii="a")

    def test_Fan3D_Set_vectors_invalid(self):
        """
        Set invalid vectors by call to Set
        """
        self.assertRaises(TypeError, self.geom.Set, vectors=1)

    def test_Fan3D_Set_vectors_string_invalid_input(self):
        """
        Set invalid string vector input for Set
        """
        self.assertRaises(AssertionError, self.geom.Set, vectors="a")

    # SETTING LIST OF INPUTS

    def test_Fan3D_Set_list_of_angles(self):
        """
        Set list of angles by call to Set
        """
        self.geom.Set(vertices=((0, 0, 0), (5.0, 0.0, 0.0), (-5, 0.0, 0.0)))
        self.geom.Set(angles=(180.0, 360.0, 270.0))
        self.assertEqual(self.geom.angles, [180.0, 360.0, 270.0])

    def test_Fan3D_Set_list_of_radii(self):
        """
        Set list of angles by call to Set
        """
        self.geom.Set(vertices=((0, 0, 0), (5.0, 0.0, 0.0), (-5, 0.0, 0.0)))
        self.geom.Set(radii=(3.0, 2.0, 5.0))
        self.assertEqual(self.geom.radii, [3.0, 2.0, 5.0])

    def test_Fan3D_Set_list_of_vectors(self):
        """
        Set list of angles by call to Set
        """
        self.geom.Set(vertices=((0, 0, 0), (5.0, 0.0, 0.0), (-5, 0.0, 0.0)))
        self.geom.Set(vectors=((1.0, 1.0, 0.0), (0.0, 1.0, 0.0), (0.0, 1.0, 1.0)))
        self.assertEqual(
            self.geom.vectors, [((1.0, 1.0, 0.0), (0.0, 1.0, 0.0), (0.0, 1.0, 1.0))]
        )


class Fan3D_Viewer_Tests(unittest.TestCase):
    """
    tests for Fan3D in DejaVu.Viewer
    """

    def setUp(self):
        """
        start Viewer
        """
        self.vi = Viewer(verbose=0)
        self.geom = Fan3D(
            "arcs",
            vertices=((0, 0, 0), (5.0, 0.0, 0.0)),
            vnormals=((0, 0, -1), (0, 1.0, 0)),
            materials=((0.5, 0, 0),),
            radii=(1.0, 2.0),
            angles=(360, 180),
            vectors=((1, 1, 0), (1, 0, 0)),
            inheritLineWidth=0,
            lineWidth=10,
            inheritMaterial=False,
        )
        self.geom.Set(inheritCulling=0)
        self.geom.Set(culling=0)
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

    # one test of setting properties via DejaVuGuiFan3D
    def test_Fan3D_inheritMaterial(self):
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
        self.assertEqual(round(buff_255[midpt][midpt][1], 1) <= 0.1, True)
        self.vi.OneRedraw()
        self.vi.update()
        # sleep(5)
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
        # sleep(5)
        self.assertEqual(round(buff_255[midpt][midpt][0], 1) >= 0.4, True)

    # Arcs 3D image
    def test_Fan3D_image(self):
        """valid image..checked by writing/reading a tif file"""
        cam = self.vi.currentCamera
        cam.Set(height=200, width=200)
        self.vi.OneRedraw()
        self.vi.update()
        buff = cam.GrabFrontBufferAsArray()
        # print "max pixel= ", max(buff.ravel())
        # sum_array=Numeric.add.reduce(buff)
        # on sgi, viewer is not 500x500 but 509 or 516 or? square
        total_pixels = len(buff) / 3
        effective_height = int(sqrt(total_pixels))
        midpt = int(effective_height / 2)
        buff.shape = (effective_height, effective_height, 3)
        buff_255 = buff / 255.0
        # print "pixel at midpoint of buffer=", buff_255[midpt][midpt]
        # sleep(5)
        # check that the pixel is not black
        self.assertEqual(round(buff_255[midpt][midpt][0], 1) >= 0.1, True)
        buff_255_sum = Numeric.add.reduce(buff_255)
        cam.SaveImage("./saveimageFan3D.tif")
        im = Image.open("./saveimageFan3D.tif")
        im = im.tostring()
        narray = Numeric.fromstring(im, "B")
        # print narray.shape
        narray.shape = (effective_height, effective_height, 3)
        narray_255 = narray / 255.0
        narray_255_sum = Numeric.add.reduce(narray_255)
        # print sum
        d = buff_255_sum - narray_255_sum
        for v in d:
            self.assertTrue(max(v) < 1e-15)


if __name__ == "__main__":
    test_cases = [
        "Fan3D__init__Tests",
        "Fan3D_Set_Tests",
        "Fan3D_Viewer_Tests",
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

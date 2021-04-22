## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by

#
#
# $Id: test_Arrows.py,v 1.11 2007/07/24 17:30:42 vareille Exp $
#
#

import unittest
import sys, os, math
from Tkinter import Menubutton
import numpy.oldnumeric as Numeric, types
from math import sqrt
from DejaVu.Viewer import Viewer
from DejaVu.Arrows import Arrows
import Image


class Arrows__init__Tests(unittest.TestCase):
    """
    'Arrows__init__Tests',
    """

    # defaults
    def test_Arrows_defaults(self):
        """defaults for shape, etc"""
        g = Arrows()
        self.assertEqual(isinstance(g, Arrows), True)

    # shape
    def test_Arrows_shape(self):
        """shape (0,2), (default shape is (0,3))"""
        g = Arrows(shape=(0, 2))
        self.assertEqual(isinstance(g, Arrows), True)


class Arrows_Set_Tests(unittest.TestCase):
    """
    # doesnot override Geom.Set so just one test that baseclass Set is called"""

    def setUp(self):
        """
        create geom
        """
        self.geom = Arrows(name="test")

    def tearDown(self):
        """
        clean-up
        """
        try:
            del self.geom
        except:
            pass

    def test_Arrows_Set_name(self):
        """
        test Setting name
        """
        val = "new_name"
        self.geom.Set(name=val)
        self.assertEqual(self.geom.name, val)


class Arrows_Viewer_Tests(unittest.TestCase):
    """
    tests for Arrows in DejaVu.Viewer
    """

    def setUp(self):
        """
        start Viewer
        """
        self.vi = Viewer(verbose=0)

    def tearDown(self):
        """
        clean-up
        """
        try:
            self.vi.Exit()
        except:
            pass

    # one test of setting properties via DejaVuGui...
    def test_Arrows_inheritMaterial(self):
        """test image and changing its material by toggling inheritMaterial"""
        """ NOTE toggling is done by invoking a button in dejaVuGUI
this test checks pixel in the middle of the scene when the object does not
inheritMaterial and is colored RED vs after inheritMaterial is restored when
the object is white (well grayish)
        """
        cam = self.vi.currentCamera
        cam.Set(height=200, width=200)
        arrows = Arrows(
            "arrows",
            vertices=[[0, 0, 0], [10, 0, 0], [0, 8, 0]],
            faces=((0, 1), (0, 2)),
            materials=((1, 0, 0),),
            inheritLineWidth=0,
            inheritMaterial=0,
            lineWidth=10,
        )
        self.vi.AddObject(arrows)
        self.vi.SetCurrentObject(arrows)
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
        for c in self.vi.GUI.inheritF.children.values():
            if c.__class__ == Menubutton and c.configure("text")[-1] == (
                "Current",
                "geom",
                "properties",
            ):
                self.inheritF_menu = c.menu
        inheritMaterial_index = self.inheritF_menu.index("inheritMaterial")
        self.inheritF_menu.invoke(inheritMaterial_index)
        newstate = arrows.getState()["inheritMaterial"]
        # print "now arrows.inheritMaterial=", newstate
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

    # Arcs 3D image
    def test_arrow_image(self):
        """test creation of valid image by writing/reading a tif file"""
        cam = self.vi.currentCamera
        arrows = Arrows(
            "myarrows",
            vertices=[[0, 0, 0], [10, 0, 0], [0, 8, 0]],
            faces=((0, 1), (0, 2)),
            inheritLineWidth=False,
            lineWidth=10,
        )
        self.vi.AddObject(arrows)
        self.vi.OneRedraw()
        self.vi.update()
        buff = cam.GrabFrontBufferAsArray()
        # print "max pixel= ", max(buff.ravel())
        # sum_array=Numeric.add.reduce(buff)
        # on sgi, viewer is not 500x500 but 509 or 516 or? square
        total_pixels = len(buff) / 3
        effective_height = sqrt(total_pixels)
        midpt = int(effective_height / 2)
        buff.shape = (effective_height, effective_height, 3)
        buff_255 = buff / 255.0
        # print "pixel at midpoint of buffer=", buff_255[midpt][midpt]
        # check that the pixel is not black
        ##print "buff_255[midpt][midpt][0]=", buff_255[midpt][midpt][0]

        #        if sys.platform == 'win32':
        #            self.assertEqual(buff_255[midpt][midpt+2][0]>0.1, True)
        #        else:

        self.assertEqual(buff_255[midpt][midpt][0] > 0.1, True)

        buff_255_sum = Numeric.add.reduce(buff_255)
        cam.SaveImage("./saveimagearrows.tif")
        im = Image.open("./saveimagearrows.tif")
        im = im.tostring()
        narray = Numeric.fromstring(im, "B")
        # print narray.shape
        narray.shape = (effective_height, effective_height, 3)
        narray_255 = narray / 255.0
        narray_255_sum = Numeric.add.reduce(narray_255)
        # print sum
        d = buff_255_sum - narray_255_sum
        # self.assertEqual(d,0)
        # self.assertTrue(numpy.alltrue(d==[0.,0.,0.]))
        for v in d:
            self.assertTrue(v[0] < 1.0e-9)
            self.assertTrue(v[1] < 1.0e-9)
            self.assertTrue(v[2] < 1.0e-9)


if __name__ == "__main__":

    test_cases = [
        "Arrows__init__Tests",
        "Arrows_Set_Tests",
        "Arrows_Viewer_Tests",
    ]
    unittest.main(
        argv=(
            [
                __name__,
            ]
            + test_cases
        )
    )
    # unittest.main( argv=([__name__ , '-v'] + test_cases) )
    # unittest.main()

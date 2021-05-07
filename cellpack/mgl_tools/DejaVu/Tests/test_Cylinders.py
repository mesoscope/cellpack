## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by

#
#
# $Id: test_Cylinders.py,v 1.21 2009/04/20 19:34:34 vareille Exp $
#
#
import sys, os, math, types
import numpy
from math import sqrt
from Tkinter import Tk, Toplevel, Menubutton
import unittest, numpy.oldnumeric as Numeric
from DejaVu.Viewer import Viewer
from time import sleep
from DejaVu.Cylinders import Cylinders
import Image


class Cylinders__init__Tests(unittest.TestCase):
    """test keywords for __init__:
    keywords = [ 'radii',
                'quality']
    all other keywords are handled by Geom.__init__ method"""

    # defaults
    def test_Cylinders_defaults(self):
        """defaults for  radii, quality etc"""
        g = Cylinders()
        self.assertEqual(isinstance(g, Cylinders), True)

    # radii
    def test_Cylinders_radii(self):
        """radii 2 (default radii is 0.2)"""
        g = Cylinders(radii=(2,))
        self.assertEqual(isinstance(g, Cylinders), True)

    # quality
    def test_Cylinders_quality(self):
        """quality 15 (default quality is 3)"""
        g = Cylinders(quality=4)
        self.assertEqual(isinstance(g, Cylinders), True)


class Cylinders_Set_Tests(unittest.TestCase):
    """
    tests for Cylinders.Set method
    """

    def setUp(self):
        """
        create Cylinders geometry
        """
        v = [[1.0, 0, 0], [2.0, 0, 0], [3.0, 0, 0]]
        f = [[0, 1, 2]]
        self.geom = Cylinders("cyl", vertices=v, faces=f)

    def tearDown(self):
        """
        clean-up
        """
        try:
            del self.geom
        except:
            pass

    def test_Cylinders_quality(self):
        """checks setting quality of cylinders"""
        self.geom.Set(quality=4)
        self.assertEqual(self.geom.quality, 4)

    #    def test_Cylinders_quality_invalid(self):
    #        """invalid input for quality of cylinders
    #        """
    #        self.assertRaises(TypeError,self.geom.Set, quality='hai')
    #
    #
    #    def test_Cylinders_quality_bad_input(self):
    #        """bad input for quality of cylinders
    #        """
    #        self.assertRaises(TypeError,self.geom.Set, quality=[1,1])

    def test_Cylinders_radii_asFloat(self):
        """checks setting radius of cylinders
        ???THIS APPARENTLY HAS NO EFFECT???
        value remains the default!!!
        """
        self.geom.Set(radii=3.0)
        self.assertEqual(self.geom.vertexSet.radii.array[0], 3.0)
        self.assertEqual(len(self.geom.vertexSet.radii.array), 1)

    def test_Cylinders_radii_asList(self):
        """checks setting radius of cylinders
        ???THIS APPARENTLY HAS NO EFFECT???
        value remains the default!!!
        """
        self.geom.Set(radii=[3.0])
        self.assertEqual(self.geom.vertexSet.radii.array[0], 3.0)
        self.assertEqual(len(self.geom.vertexSet.radii.array), 1)

    def test_Cylinders_radii(self):
        """checks setting radii of cylinders"""
        self.geom.Set(radii=(3.0,))
        self.assertEqual(self.geom.vertexSet.radii.array, (3.0,))

    def xtest_Cylinders_radii_invalid(self):
        """invalid input for radii of cylinders
        ###### it seems that we have always been accepting this invalid data ####
        """
        self.geom.Set(radii=(-10,))
        self.assertNotEqual(self.geom.vertexSet.radii.array, (-10,))

    def test_Cylinders_radii_invalid_too_much_float(self):
        """bad input, for radii of cylinders"""
        self.assertRaises(TypeError, self.geom.Set, radii="hai")


class Cylinders_Viewer_Tests(unittest.TestCase):
    """
    tests for Cylinders in Viewer
    """

    def setUp(self):
        """
        start Viewer
        """
        self.vi = Viewer(height=200, width=200, verbose=0)
        v = [[-2.0, 0, 0], [2.0, 0, 0]]
        f = [[0, 1]]
        self.geom = Cylinders(
            "cyl",
            vertices=v,
            faces=f,
            materials=((0.5, 0, 0),),
            quality=4,
            inheritLineWidth=0,
            lineWidth=10,
            inheritMaterial=False,
        )
        # should be done vis geom.Set(radii=5.0) (ms)
        self.geom.Set(radii=5.0)
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
    def test_Cylinders_inheritMaterial(self):
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
        # sleep(5)
        buff = cam.GrabFrontBufferAsArray()
        total_pixels = len(buff) / 3
        effective_height = int(sqrt(total_pixels))
        midpt = int(effective_height / 2)
        buff.shape = (effective_height, effective_height, 3)
        buff_255 = buff / 255.0
        # print "1:midpt=", buff_255[midpt][midpt]
        self.assertEqual(round(buff_255[midpt][midpt][1], 1) <= 0.2, True)
        self.vi.OneRedraw()
        self.vi.update()
        for c in self.vi.GUI.inheritF.children.values():
            if c.__class__ == Menubutton and c.configure("text")[-1] == (
                "Current",
                "geom",
                "properties",
            ):
                self.inheritF_menu = c.menu
        # import pdb;pdb.set_trace()
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
        self.assertEqual(round(buff_255[midpt][midpt][0], 1) >= 0.4, True)

    def test_Cylinders_Images(self):
        """tests storing and reading an image"""
        cam = self.vi.currentCamera
        cam.Set(height=200, width=200)
        self.vi.OneRedraw()
        self.vi.update()
        buff = cam.GrabFrontBufferAsArray()
        # sum_array=Numeric.add.reduce(buff)
        # on sgi, viewer is not 500x500 but 509 or 516 or? square
        total_pixels = len(buff) / 3
        effective_height = int(sqrt(total_pixels))
        midpt = int(effective_height / 2)
        buff.shape = (effective_height, effective_height, 3)
        buff_255 = buff / 255.0
        # check that the pixel is not black
        self.assertEqual(buff_255[midpt][midpt][0] > 0.1, True)
        buff_255_sum = Numeric.add.reduce(buff_255)
        # sleep(5)
        cam.SaveImage("./saveimagescyl.tif")
        im = Image.open("./saveimagescyl.tif")
        im = im.tostring()
        narray = Numeric.fromstring(im, "B")
        narray.shape = (effective_height, effective_height, 3)
        narray_255 = narray / 255.0
        narray_255_sum = Numeric.add.reduce(narray_255)
        d = buff_255_sum - narray_255_sum
        # self.assertEqual(d,0)
        # self.assertTrue(numpy.alltrue(d==[0.,0.,0.]))
        for v in d:
            self.assertTrue(v[0] < 1.0e-9)
            self.assertTrue(v[1] < 1.0e-9)
            self.assertTrue(v[2] < 1.0e-9)


if __name__ == "__main__":
    test_cases = [
        "Cylinders__init__Tests",
        "Cylinders_Set_Tests",
        "Cylinders_Viewer_Tests",
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

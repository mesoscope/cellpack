## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by

#
#
# $Id: test_Spheres.py,v 1.26 2009/07/09 00:29:45 vareille Exp $
#
#
import sys, os, math, types
import numpy
from Tkinter import Menubutton
import unittest, numpy.oldnumeric as Numeric
from math import sqrt
from opengltk.OpenGL import GL
from DejaVu.Viewer import Viewer
from DejaVu.Spheres import Spheres, TriangulateIcos, TriangulateIcosByEdgeCenterPoint
from time import sleep
from DejaVu import viewerConst
import Image


class Spheres__init__Tests(unittest.TestCase):
    """test keywords for __init__:
    keywords = ['centers',
                'quality',
                'radii',
                'slices',
                'shapes']
    all other keywords are handled by Geom.__init__ method"""

    # defaults
    def test_Spheres_defaults(self):
        """defaults"""
        g = Spheres()
        self.assertEqual(isinstance(g, Spheres), True)

    # centers
    def test_Spheres_centers(self):
        """centers"""
        g = Spheres(centers=((0, 0, 0), (1, 1, 1)))
        self.assertEqual(isinstance(g, Spheres), True)

    # quality
    def test_Spheres_quality(self):
        """quality"""
        g = Spheres(quality=17)
        self.assertEqual(isinstance(g, Spheres), True)

    # radii
    def test_Spheres_radii(self):
        """radii 2"""
        g = Spheres(radii=2.0)
        self.assertEqual(isinstance(g, Spheres), True)

    # slices
    def test_Spheres_slices(self):
        """slices"""
        g = Spheres(slices=5)
        self.assertEqual(isinstance(g, Spheres), True)

    # stacks
    def test_Spheres_stacks(self):
        """stacks"""
        g = Spheres(stacks=5)
        self.assertEqual(isinstance(g, Spheres), True)


class Spheres_Set_Tests(unittest.TestCase):
    """
    # doesnot override Geom.Set so just one test that baseclass Set is called"""

    def setUp(self):
        """
        create geom
        """
        self.geom = Spheres(name="test")

    def tearDown(self):
        """
        clean-up
        """
        try:
            del self.geom
        except:
            pass

    def test_Spheres_Set_radii(self):
        """
        test Setting radii
        """
        self.geom.Set(
            centers=((1, 1, 1), (2, 2, 2), (3, 3, 3)),
            radii=(
                1,
                1,
                1,
            ),
        )
        self.assertEqual(self.geom.vertexSet.vertices.array[0][0], 1)

    def test_Spheres_Set_name(self):
        """
        test Setting name
        """
        val = "new_name"
        self.geom.Set(name=val)
        self.assertEqual(self.geom.name, val)

    def test_Spheres_centers(self):
        """checks setting center of spheres"""
        self.geom.Set(centers=((3, 0, 0),))
        # self.assertEqual(self.geom.vertexSet.vertices.array[0],((3,0,0),))
        self.assertTrue(
            numpy.alltrue(self.geom.vertexSet.vertices.array[0] == [3.0, 0.0, 0.0])
        )

    def test_Spheres_centers_invalid(self):
        """invalid center of spheres"""
        self.assertRaises(
            AttributeError,
            self.geom.Set,
            centers=(
                0,
                0,
            ),
        )

    def test_Spheres_quality(self):
        """checks setting quality of spheres"""
        self.geom.Set(quality=5)
        self.assertEqual(self.geom.quality, 5)

    def test_Spheres_quality_invalid(self):
        """invalid input for slices"""
        self.geom.Set(quality=-100)
        self.assertNotEqual(self.geom.quality, -100)
        # self.assertRaises(AssertionError,sph.Set,slices= -100)

    def test_Spheres_radii(self):
        """checks setting radii of spheres"""
        self.geom.Set(radii=3.0)
        self.assertEqual(self.geom.radius, 3.0)


class Spheres_Viewer_Tests(unittest.TestCase):
    """
    tests for Spheres in DejaVu.Viewer
    """

    def setUp(self):
        """
        start Viewer
        """
        self.vi = Viewer(verbose=0)
        self.geom = Spheres(
            "spheres",
            vertices=((0, 0, 0), (5.0, 0.0, 0.0)),
            materials=((0.5, 0, 0),),
            radii=(5.0,),
            inheritLineWidth=0,
            lineWidth=10,
            inheritMaterial=False,
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

    # one test of setting properties via DejaVuGuiSpheres
    def test_Spheres_inheritMaterial(self):
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
        self.assertEqual(round(buff_255[midpt][midpt][1], 1) <= 0.25, True)
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

    # Arcs 3D image
    def test_Spheres_image(self):
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
        # check that the pixel is not black
        self.assertEqual(round(buff_255[midpt][midpt][0], 1) >= 0.1, True)
        buff_255_sum = Numeric.add.reduce(buff_255)
        cam.SaveImage("./saveimageSpheres.tif")
        im = Image.open("./saveimageSpheres.tif")
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
            self.assertTrue(v[0] < 1.0e-9 and v[0] > -1.0e-9)
            self.assertTrue(v[1] < 1.0e-9 and v[1] > -1.0e-9)
            self.assertTrue(v[2] < 1.0e-9 and v[2] > -1.0e-9)


if __name__ == "__main__":
    test_cases = [
        "Spheres__init__Tests",
        "Spheres_Set_Tests",
        "Spheres_Viewer_Tests",
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

## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by

#
#
# $Id: test_Arcs3D.py,v 1.19 2010/01/28 23:58:32 annao Exp $
#
#

import sys, os, math, types
import numpy
from Tkinter import Tk, Toplevel, Menubutton
import unittest, numpy.oldnumeric as Numeric
from opengltk.OpenGL import GL
from DejaVu.Camera import Camera
from DejaVu.Viewer import Viewer
from DejaVu.Spheres import Spheres
from opengltk.extent.utillib import glCleanRotMat
from time import sleep
from DejaVu.IndexedPolygons import IndexedPolygons
from DejaVu.IndexedPolylines import IndexedPolylines
from DejaVu.ViewerGUI import ViewerGUI
from DejaVu import viewerConst, datamodel
import Image
from math import sqrt
from DejaVu.Points import Points, CrossSet
from DejaVu.Arcs3D import Arcs3D


class Arcs3D__init__Tests(unittest.TestCase):
    """test keywords for __init__:
    keywords = [ 'shape',
                'radii',
                'angles']
    all other keywords are handled by Geom.__init__ method"""

    # defaults
    def test_Arcs3D_defaults(self):
        """defaults for shape, radii, angles"""
        g = Arcs3D()
        self.assertEqual(isinstance(g, Arcs3D), True)

    # shape
    def test_Arcs3D_shape(self):
        """shape (0,2), (default shape is (0,3))"""
        g = Arcs3D(shape=(0, 2))
        self.assertEqual(isinstance(g, Arcs3D), True)

    # radii
    def test_Arcs3D_radii(self):
        """radii 2 (default radii is 0.2)"""
        g = Arcs3D(radii=2.0)
        self.assertEqual(isinstance(g, Arcs3D), True)

    # angles
    def test_Arcs3D_angles(self):
        """angles 180 (default angles is (360,))"""
        g = Arcs3D(angles=180)
        self.assertEqual(isinstance(g, Arcs3D), True)


class Arcs3D_Set_Tests(unittest.TestCase):
    """
    # doesnot override Geom.Set so just one test that baseclass Set is called"""

    def setUp(self):
        """
        create geom
        """
        self.geom = Arcs3D(name="test")

    def tearDown(self):
        """
        clean-up
        """
        try:
            del self.geom
        except:
            pass

    def test_Arcs3D_Set_angles(self):
        """
        test Setting angles
        """
        self.geom.Set(angles=360)
        self.assertEqual(self.geom.angles[0], 360)

    def test_Arcs3D_Set_radii(self):
        """
        Set radii by call to Set
        """
        self.geom.Set(radii=3.0)
        self.assertEqual(self.geom.radii, [3.0])

    def test_Arcs3D_Set_name(self):
        """
        test Setting name
        """
        val = "new_name"
        self.geom.Set(name=val)
        self.assertEqual(self.geom.name, val)

    # INVALID INPUT
    def test_Arcs3D_Set_angles_invalid(self):
        """
        Set inavlid angles by call to Set
        """
        self.assertRaises(ValueError, self.geom.Set, angles="a")

    def test_Arcs3D_Set_radii_invalid(self):
        """
        Set invalid radii by call to Set
        """
        self.assertRaises(ValueError, self.geom.Set, radii="a")

    # SETTING LIST OF INPUTS

    def test_Arcs3D_Set_list_of_angles(self):
        """
        Set list of angles by call to Set
        """
        self.geom.Set(vertices=((0, 0, 0), (5.0, 0.0, 0.0), (-5, 0.0, 0.0)))
        self.geom.Set(angles=(180.0, 360.0, 270.0))
        self.assertEqual(self.geom.angles, [180.0, 360.0, 270.0])

    def test_Arcs3D_Set_list_of_radii(self):
        """
        Set list of radii by call to Set
        """
        self.geom.Set(vertices=((0, 0, 0), (5.0, 0.0, 0.0), (-5, 0.0, 0.0)))
        self.geom.Set(radii=(3.0, 2.0, 5.0))
        self.assertEqual(self.geom.radii, [3.0, 2.0, 5.0])


class Arcs3D_Viewer_Tests(unittest.TestCase):
    """
    tests for Arcs3D in DejaVu.Viewer
    """

    def setUp(self):
        """
        start Viewer
        """
        self.vi = Viewer(verbose=0)
        self.geom = arc = Arcs3D(
            "arcs",
            vertices=((0, 0, 0), (5.0, 0.0, 0.0)),
            vnormals=((1.0, 0, 0), (0, 1.0, 0)),
            materials=((0.5, 0, 0),),
            radii=(1.0, 2.0),
            angles=(360, 180),
            inheritLineWidth=0,
            lineWidth=10,
            inheritMaterial=False,
        )
        self.vi.AddObject(arc)
        self.vi.update()
        self.vi.currentCamera.DoPick(0.0, 0.0)
        self.vi.SetCurrentObject(arc)

    def tearDown(self):
        """
        clean-up
        """
        try:
            self.vi.Exit()
        except:
            pass

    # one test of setting properties via DejaVuGui...
    def test_Arcs3D_inheritMaterial(self):
        """valid changing material by toggling inheritMaterial"""
        """ NOTE toggling is done by invoking a button in dejaVuGUI
this test checks pixel in the middle of the scene when the object does not
inheritMaterial and is colored RED vs after inheritMaterial is restored when
the object is white (well grayish)
        """
        cam = self.vi.currentCamera
        cam.Set(height=200, width=200)
        arc = self.geom
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
        newstate = arc.getState()["inheritMaterial"]
        # print "now arc.inheritMaterial=", newstate
        self.assertEqual(newstate, 1)

        self.vi.OneRedraw()
        buff = cam.GrabFrontBufferAsArray()
        total_pixels = len(buff) / 3
        effective_height = int(sqrt(total_pixels))
        midpt = int(effective_height / 2)
        buff.shape = (effective_height, effective_height, 3)
        buff_255 = buff / 255.0
        # print "midpt=", buff_255[midpt][midpt]

        if sys.platform == "irix6":
            self.assertEqual(
                (round(buff_255[midpt - 1][midpt - 1][0], 1) >= 0.4)
                or (round(buff_255[midpt][midpt][0], 1) >= 0.4),
                True,
            )

        else:
            self.assertEqual(round(buff_255[midpt][midpt][0], 1) >= 0.4, True)

    # Arcs 3D image
    def test_Arcs3D_image(self):
        """valid image..checked by writing/reading a tif file"""
        arc = self.geom
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
        if sys.platform == "irix6":
            self.assertEqual(
                (round(buff_255[midpt - 1][midpt - 1][0], 1) >= 0.1)
                or (round(buff_255[midpt][midpt][0], 1) >= 0.1),
                True,
            )
        else:
            self.assertEqual(round(buff_255[midpt][midpt][0], 1) >= 0.1, True)

        buff_255_sum = Numeric.add.reduce(buff_255)
        cam.SaveImage("./saveimagearc.tif")
        im = Image.open("./saveimagearc.tif")
        im = im.tostring()
        narray = Numeric.fromstring(im, "B")
        # print narray.shape
        narray.shape = (effective_height, effective_height, 3)
        narray_255 = narray / 255.0
        narray_255_sum = Numeric.add.reduce(narray_255)
        # print sum
        d = buff_255_sum - narray_255_sum
        self.assertTrue(d.ravel().max() < 1.0e-9)
        # self.assertTrue(numpy.alltrue(d==[0.,0.,0.]))
        # for v in d:
        #    self.assertTrue(v[0]<1.e-9)
        #    self.assertTrue(v[1]<1.e-9)
        #    self.assertTrue(v[2]<1.e-9)


if __name__ == "__main__":
    test_cases = [
        "Arcs3D__init__Tests",
        "Arcs3D_Set_Tests",
        "Arcs3D_Viewer_Tests",
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

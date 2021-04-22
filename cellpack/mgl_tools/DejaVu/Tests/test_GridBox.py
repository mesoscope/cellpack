## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by

#
#
# $Id: test_GridBox.py,v 1.12 2007/07/24 17:30:42 vareille Exp $
#
#
import unittest
import sys, os, math
import numpy.oldnumeric as Numeric

from opengltk.OpenGL import GL

# import Materials, viewerConst, datamodel, Clip
from DejaVu.Viewer import Viewer
from math import sqrt
from DejaVu.Box import GridBox
import Image
from time import sleep
from Tkinter import Menubutton

# Grid Box


class GridBox__init__Tests(unittest.TestCase):
    """test keywords for __init__:
    keywords = [ 'npts',
                 'xnpts',
                 'ynpts',
                 'znpts',
                 'spacing',
                 'xspacing',
                 'yspacing',
                 'zspacing',
                ]
    all other keywords are handled by Geom.__init__ method"""

    # defaults
    def test_GridBox_defaults(self):
        """defaults"""
        g = GridBox()
        self.assertEqual(isinstance(g, GridBox), True)

    # npts
    def test_GridBox_shape(self):
        """npts default is 40"""
        g = GridBox(npts=20)
        self.assertEqual(isinstance(g, GridBox), True)

    # xnpts
    def test_GridBox_shape(self):
        """xnpts default is 40"""
        g = GridBox(xnpts=20)
        self.assertEqual(isinstance(g, GridBox), True)

    # ynpts
    def test_GridBox_shape(self):
        """ynpts default is 40"""
        g = GridBox(ynpts=20)
        self.assertEqual(isinstance(g, GridBox), True)

    # znpts
    def test_GridBox_shape(self):
        """znpts default is 40"""
        g = GridBox(znpts=20)
        self.assertEqual(isinstance(g, GridBox), True)

    # spacing
    def test_GridBox_shape(self):
        """spacing default is .375"""
        g = GridBox(spacing=0.20)
        self.assertEqual(isinstance(g, GridBox), True)

    # xspacing
    def test_GridBox_shape(self):
        """xspacing default is .375"""
        g = GridBox(xspacing=0.20)
        self.assertEqual(isinstance(g, GridBox), True)

    # yspacing
    def test_GridBox_shape(self):
        """yspacing default is .375"""
        g = GridBox(yspacing=0.20)
        self.assertEqual(isinstance(g, GridBox), True)

    # zspacing
    def test_GridBox_shape(self):
        """zspacing default is .375"""
        g = GridBox(zspacing=0.20)
        self.assertEqual(isinstance(g, GridBox), True)


class GridBox_Set_Tests(unittest.TestCase):
    """
    # does override Geom.Set ???? one test that baseclass Set is called"""

    def setUp(self):
        """
        create geom
        """
        self.geom = GridBox(name="test")

    def tearDown(self):
        """
        clean-up
        """
        try:
            del self.geom
        except:
            pass

    def test_GridBox_Set_spacing(self):
        """
        test Setting angles
        """
        self.geom.Set(spacing=(0.5, 0.375, 0.1))
        self.assertEqual(self.geom.xspacing, 0.5)

    def test_GridBox_Set_name(self):
        """
        test Setting name
        """
        val = "new_name"
        self.geom.Set(name=val)
        self.assertEqual(self.geom.name, val)


class GridBox_Viewer_Tests(unittest.TestCase):
    """
    tests for GridBox in DejaVu.Viewer
    """

    def setUp(self):
        """
        start Viewer
        """
        self.vi = Viewer(verbose=0)
        # put box with one corner on origin...
        self.geom = GridBox(
            "gridbox",
            origin=(0, 0, 0),
            inheritLineWidth=0,
            lineWidth=10,
            inheritMaterial=False,
        )
        self.geom.frontPolyMode = GL.GL_LINE

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

    # one test of setting properties via DejaVuGuiGridBox
    def test_GridBox_inheritMaterial(self):
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
        self.assertEqual(round(buff_255[midpt][midpt][0], 1) >= 0.4, True)

    # Arcs 3D image
    def test_GridBox_image(self):
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

        # import pdb;pdb.set_trace()

        self.assertEqual(round(buff_255[midpt][midpt][0], 1) >= 0.1, True)
        # sleep(5)
        buff_255_sum = Numeric.add.reduce(buff_255)
        cam.SaveImage("./saveimageGridBox.tif")
        im = Image.open("./saveimageGridBox.tif")
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
        "GridBox__init__Tests",
        "GridBox_Set_Tests",
        "GridBox_Viewer_Tests",
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

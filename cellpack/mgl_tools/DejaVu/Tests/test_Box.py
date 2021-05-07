## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by

#
#
# $Id: test_Box.py,v 1.14 2009/07/13 19:02:52 vareille Exp $
#
#
import unittest
import sys, os
import numpy
import numpy.oldnumeric as Numeric
import Image

from math import sqrt
from Tkinter import Menubutton

from opengltk.OpenGL import GL

from DejaVu.Viewer import Viewer
from DejaVu.Box import Box


# Box
class Box__init__Tests(unittest.TestCase):
    """
    'Box__init__Tests',
    NOTE: cannot create box without any arguments!
    """

    # defaults
    def test_Box_defaults(self):
        """can create box with defaults values"""
        g = Box()
        self.assertEqual(isinstance(g, Box), True)

    # origin
    def test_Box_origin(self):
        """origin (2,2,2), (default origin is (0,0,0))
        box=Box("mybox",cornerPoints=((0,0,0),(5,5,0)), materials=((0,1,0),))
        """
        g = Box(origin=(2, 2, 2))
        self.assertEqual(isinstance(g, Box), True)


class Box_Set_Tests(unittest.TestCase):
    """
    # doesnot override Geom.Set so just one test that baseclass Set is called
    adds these keywords to IndexedPolygon.keywords
    maxCube
    minCube
    vertices
    side
    xside
    yside
    zside
    center
    origin
    cornerPoints"""

    def setUp(self):
        """
        create geom
        """
        self.geom = Box(name="test", origin=(0, 0, 0))

    def tearDown(self):
        """
        clean-up
        """
        try:
            del self.geom
        except:
            pass

    def test_Box_Set_name(self):
        """
        test Setting name
        """
        val = "new_name"
        self.geom.Set(name=val)
        self.assertEqual(self.geom.name, val)

    # maxCube
    def test_Box_Set_maxCube(self):
        """
        test Setting maxCube
        """
        val = 3
        self.geom.Set(maxCube=val)
        self.assertEqual(self.geom.maxCube, val)

    # minCube
    def test_Box_Set_minCube(self):
        """
        test Setting minCube
        """
        val = 3
        self.geom.Set(minCube=val)
        self.assertEqual(self.geom.minCube, val)

    # vertices
    def test_Box_Set_vertices(self):
        """
        test Setting vertices
        """
        val = (
            (2.0, 2.0, 0.0),
            (0.0, 2.0, 0.0),
            (0.0, 0.0, 0.0),
            (2.0, 0.0, 0.0),
            (2.0, 2.0, 2.0),
            (0.0, 2.0, 2.0),
            (0.0, 0.0, 2.0),
            (2.0, 0.0, 2.0),
        )
        self.geom.Set(vertices=val)
        # self.assertEqual(self.geom.vertexSet.vertices.array[0], val[0])
        self.assertTrue(numpy.alltrue(self.geom.vertexSet.vertices.array[0] == val[0]))

    # side
    def test_Box_Set_side(self):
        """
        test Setting side
        """
        val = 3
        self.geom.Set(side=val)
        # side sets all 2 dimensions
        self.assertEqual(self.geom.xside, val)

    # xside
    def test_Box_Set_xside(self):
        """
        test Setting xside
        """
        val = 4
        self.geom.Set(xside=val)
        self.assertEqual(self.geom.xside, val)

    # yside
    def test_Box_Set_yside(self):
        """
        test Setting yside
        """
        val = 5
        self.geom.Set(yside=val)
        self.assertEqual(self.geom.yside, val)

    # zside
    def test_Box_Set_zside(self):
        """
        test Setting zside
        """
        val = 6
        self.geom.Set(zside=val)
        self.assertEqual(self.geom.zside, val)

    # center
    def test_Box_Set_center(self):
        """
        test Setting center
        """
        val = (2, 4, 6)
        self.geom.Set(center=val)
        self.assertEqual(self.geom.center, val)

    # origin
    def test_Box_Set_origin(self):
        """
        test Setting origin ONLY WORKS IF CENTER SPECIFIED (??)
        """
        val = (-2, -2, -2)
        center = (0, 0, 0)
        self.geom.Set(origin=val, center=center)
        self.assertEqual(self.geom.vertexSet.vertices.array[0][0], -val[0])

    # cornerPoints
    def test_Box_Set_cornerPoints(self):
        """
        test Setting cornerPoints
        """
        val = ((0, 0, 0), (10, 10, 10))
        self.geom.Set(cornerPoints=val)
        self.assertEqual(self.geom.xside, 10)


class Box_Viewer_Tests(unittest.TestCase):
    """
    tests for Box in DejaVu.Viewer
    """

    def setUp(self):
        """
        start Viewer
        """
        self.vi = Viewer(verbose=0)
        self.geom = box = Box(
            "box",
            cornerPoints=((0, 0, 0), (5, 5, 0)),
            materials=((0, 1, 0),),
            inheritLineWidth=0,
            inheritMaterial=0,
            lineWidth=10,
        )
        self.geom.frontPolyMode = GL.GL_LINE

        self.vi.AddObject(box)
        self.vi.update()
        self.vi.currentCamera.DoPick(0.0, 0.0)
        self.vi.SetCurrentObject(box)
        # self.vi.OneRedraw()

    def tearDown(self):
        """
        clean-up
        """
        try:
            self.vi.Exit()
        except:
            pass

    # one test of setting properties via DejaVuGui...
    def test_Box_inheritMaterial(self):
        """tests changing box material by toggling inheritMaterial"""
        """ NOTE toggling is done by invoking a button in dejaVuGUI
this test checks pixel in the middle of the scene when the object does not
inheritMaterial and is colored RED vs after inheritMaterial is restored when
the object is white (well grayish)
        """
        cam = self.vi.currentCamera
        cam.Set(height=200, width=200)
        box = self.geom
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
        newstate = box.getState()["inheritMaterial"]
        # print "now box.inheritMaterial=", newstate
        self.assertEqual(newstate, 1)
        self.vi.OneRedraw()
        buff = cam.GrabFrontBufferAsArray()
        total_pixels = len(buff) / 3
        effective_height = int(sqrt(total_pixels))
        midpt = int(effective_height / 2)
        buff.shape = (effective_height, effective_height, 3)
        buff_255 = buff / 255.0
        # print "2:midpt=", buff_255[midpt][midpt]
        self.assertEqual(round(buff_255[midpt][midpt][0], 1) >= 0.4, True)

    def test_Box_image(self):
        """test image: changing its material by toggling inheritMaterial"""
        cam = self.vi.currentCamera
        cam.Set(height=200, width=200)
        box = self.geom
        self.vi.OneRedraw()
        self.vi.update()
        buff = cam.GrabFrontBufferAsArray()
        self.vi.startAutoRedraw()
        # print "max pixel= ", max(buff.ravel())
        # sum_array=Numeric.add.reduce(buff)
        # on sgi, viewer is not 500x500 but 509 or 516 or? square
        total_pixels = len(buff) / 3
        effective_height = sqrt(total_pixels)
        midpt = int(effective_height / 2)
        buff.shape = (effective_height, effective_height, 3)
        buff_255 = buff  # /255.
        # print "pixel at midpoint of buffer=", buff_255[midpt][midpt]
        # check that the pixel is not black
        self.assertEqual(buff_255[midpt][midpt][0] > 0.1, True)
        buff_255_sum = Numeric.add.reduce(buff_255)
        cam.SaveImage("./saveimagebox.tif")
        im = Image.open("./saveimagebox.tif")
        im = im.tostring()
        narray = Numeric.fromstring(im, "B")
        # print narray.shape
        narray.shape = (effective_height, effective_height, 3)
        narray_255 = narray  # /255.
        narray_255_sum = Numeric.add.reduce(narray_255)
        # print sum
        d = buff_255_sum - narray_255_sum
        # self.assertEqual(d,0)
        self.assertTrue(numpy.alltrue(d == [0.0, 0.0, 0.0]))


# End Box

if __name__ == "__main__":

    test_cases = [
        "Box__init__Tests",
        "Box_Set_Tests",
        "Box_Viewer_Tests",
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

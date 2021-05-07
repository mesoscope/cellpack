## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by

import numpy
import sys, os, math, types
from Tkinter import Menubutton
import unittest, numpy.oldnumeric as Numeric
from DejaVu.Viewer import Viewer
from DejaVu.triangle_strip import Triangle_strip
from time import sleep

import Image
from math import sqrt


vert = [
    (0, 0, 0),
    (1, 0, 1),
    (1, 1, 0),
    (2, 0, -1),
    (2, 1, 0),
    (3, 0, 1),
    (3, 1, 0),
    (4, 0, -1),
    (4, 1, 0),
    (5, 0, 1),
    (5, 3, 0),
    (6, -2, 1),
]
v1 = Numeric.array(vert)
v2 = v1 + 3.0
v3 = Numeric.concatenate((v1, v2))
colors = [
    (0, 0, 1),
    (1, 0, 0),
    (0, 1, 0),
    (0, 0, 1),
    (1, 0, 0),
    (0, 1, 0),
    (0, 0, 1),
    (1, 0, 0),
    (0, 1, 0),
    (0, 0, 1),
    (1, 0, 0),
    (0, 1, 0),
]
v4 = v2 + 3.0
v5 = Numeric.concatenate((v3, v4))


class Triangle_strip__init__Tests(unittest.TestCase):
    """test keywords for __init__:
    keywords = ['stripBegin',
                'stripEnd',
                'fnormals']
    all other keywords are handled by Geom.__init__ method"""

    # defaults
    def test_Triangle_strip_defaults(self):
        """defaults"""
        g = Triangle_strip()
        self.assertEqual(isinstance(g, Triangle_strip), True)

    # vertices
    def test_Triangle_strip_vertices(self):
        """vertices"""
        g = Triangle_strip(vertices=v1)
        self.assertEqual(isinstance(g, Triangle_strip), True)

    # stripBegin
    def test_Triangle_strip_stripBegin(self):
        """stripBegin"""

        g = Triangle_strip(vertices=v5, stripBegin=[0, 12])
        self.assertEqual(isinstance(g, Triangle_strip), True)

    # materials and colors
    def test_Triangle_strip_materials(self):
        """materials"""
        g = Triangle_strip(
            vertices=v3, stripBegin=[0, 12, 24], materials=colors + colors[0:8]
        )

        self.assertEqual(isinstance(g, Triangle_strip), True)


class Triangle_strip_Set_Tests(unittest.TestCase):
    """
    # doesnot override Geom.Set so just one test that baseclass Set is called"""

    def setUp(self):
        """
        create geom
        """
        self.geom = Triangle_strip(name="test")

    def tearDown(self):
        """
        clean-up
        """
        try:
            del self.geom
        except:
            pass

    def test_Triangle_strip_Set_vertices(self):
        """
        test Setting angles
        """
        self.geom.Set(vertices=v3, stripBegin=[0, 12, 24])
        # self.assertEqual(self.geom.vertexSet.vertices.array[0], 0)
        self.assertTrue(
            numpy.alltrue(self.geom.vertexSet.vertices.array[0] == [0.0, 0.0, 0.0])
        )

    def test_Triangle_strip_Set_name(self):
        """
        test Setting name
        """
        val = "new_name"
        self.geom.Set(name=val)
        self.assertEqual(self.geom.name, val)


class Triangle_strip_Viewer_Tests(unittest.TestCase):
    """
    tests for Triangle_strip in DejaVu.Viewer
    """

    def setUp(self):
        """
        start Viewer
        """
        self.vi = Viewer(verbose=0)
        v = ((-1, 1, 0), (-1, -1, 0), (1, 1, 0), (1, -1, 0))
        self.geom = Triangle_strip(
            "triangle_strip",
            vertices=v,
            stripBegin=[0, 4],
            materials=((1.0, 0, 0),),
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

    # one test of setting properties via DejaVuGuiTriangle_strip
    def test_Triangle_strip_inheritMaterial(self):
        """valid changing material by toggling inheritMaterial"""
        """ NOTE toggling is done by invoking a button in dejaVuGUI
this test checks pixel in the middle of the scene when the object does not
inheritMaterial and is colored RED vs after inheritMaterial is restored when
the object is white (well grayish)
        """
        cam = self.vi.currentCamera

        width = height = 200
        cam.Set(height=height, width=width)

        # turn lighting off so colors are pure
        # self.geom.Set(lighting=0)
        self.vi.OverAllLightingIsOn.set(0)
        self.vi.deleteOpenglListAndCallRedrawAndCallDisableGlLighting()
        self.vi.OneRedraw()
        self.vi.update()
        buff = cam.GrabFrontBufferAsArray()
        buff.shape = (height, width, 3)
        midx = width / 2
        midy = height / 2

        # assert middle picel is red
        self.assertEqual(buff[midy][midx][0], 255)
        self.assertEqual(buff[midy][midx][1], 0)
        self.assertEqual(buff[midy][midx][2], 0)

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
        buff.shape = (height, width, 3)
        self.assertEqual(buff[midy][midx][0] == 255, True)
        self.assertEqual(buff[midy][midx][1] == 255, True)
        self.assertEqual(buff[midy][midx][2] == 255, True)
        # sleep(5)

    # Arcs 3D image
    def test_Triangle_strip_image(self):
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
        # sleep(5)
        # print "pixel at midpoint of buffer=", buff_255[midpt][midpt]
        # check that the pixel is not black
        # midpt+1 (instead of midpt)
        # because this was not working properly on some old sgi OGL card
        self.assertEqual(round(buff_255[midpt][midpt + 1][0], 1) >= 0.1, True)
        buff_255_sum = Numeric.add.reduce(buff_255)
        cam.SaveImage("./saveimageTriangle_strip.tif")
        im = Image.open("./saveimageTriangle_strip.tif")
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
            self.assertTrue(v[0] > -1.0e-9)
            self.assertTrue(v[1] > -1.0e-9)
            self.assertTrue(v[2] > -1.0e-9)


if __name__ == "__main__":
    test_cases = [
        "Triangle_strip__init__Tests",
        "Triangle_strip_Set_Tests",
        "Triangle_strip_Viewer_Tests",
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

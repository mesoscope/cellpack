## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by

#
#
# Id$
#
#
import unittest
import sys, os
from math import sqrt
from Tkinter import Menubutton
from opengltk.OpenGL import GL
from geomutils.geomalgorithms import TriangleNormals
import numpy.oldnumeric as Numeric
from DejaVu.Viewer import Viewer
from DejaVu.IndexedPolygons import IndexedPolygons
import Image


class IndexedPolygons__init__Tests(unittest.TestCase):
    """test keywords for __init__:
    no special keywords for this geometry
    all keywords are handled by Geom.__init__ method"""

    # defaults
    def test_IndexedPolygons_defaults(self):
        """defaults for vertices, faces etc"""
        g = IndexedPolygons()
        self.assertEqual(isinstance(g, IndexedPolygons), True)

    # vertices
    def test_IndexedPolygons_vertices(self):
        """vertices ((0,0,0,),(1,0,0))"""
        g = IndexedPolygons(
            vertices=(
                (
                    0,
                    0,
                    0,
                ),
                (1, 0, 0),
            )
        )
        self.assertEqual(isinstance(g, IndexedPolygons), True)

    # faces without vertices
    def test_IndexedPolygons_faces_only(self):
        """faces alone won't do..."""
        self.assertRaises(ValueError, IndexedPolygons, faces=((0, 1),))

    # vertices and faces
    def test_IndexedPolygons_vertices_and_faces(self):
        """vertices and faces"""
        g = IndexedPolygons(
            vertices=(
                (
                    0,
                    0,
                    0,
                ),
                (1, 0, 0),
            ),
            faces=((0, 1),),
        )
        self.assertEqual(isinstance(g, IndexedPolygons), True)

    # materials
    def test_IndexedPolygons_materials(self):
        """materials ((1,0,0),)"""
        g = IndexedPolygons(materials=((1, 0, 0),))
        self.assertEqual(isinstance(g, IndexedPolygons), True)


class IndexedPolygons_Set_Tests(unittest.TestCase):
    """
    # doesnot override Geom.Set so just one test that baseclass Set is called"""

    def setUp(self):
        """
        create geom
        """
        self.geom = IndexedPolygons(name="test")

    def tearDown(self):
        """
        clean-up
        """
        try:
            del self.geom
        except:
            pass

    def test_IndexedPolygons_Set_name(self):
        """
        test Setting name
        """
        val = "new_name"
        self.geom.Set(name=val)
        self.assertEqual(self.geom.name, val)

    def test_Indexedpolygon_fnormals(self):
        """checks number of fnormals????"""
        points = [
            [-1, 1, 1],
            [-1, -1, 1],
            [1, 1, 1],
            [1, -1, 1],
            [1, 1, -1],
            [1, -1, -1],
            [-1, 1, -1],
            [-1, -1, -1],
        ]

        indices = [
            [0, 1, 3, 2],
            [4, 5, 7, 6],
            [6, 7, 1, 0],
            [2, 3, 5, 4],
            [6, 0, 2, 4],
            [1, 7, 5, 3],
        ]
        polygon = IndexedPolygons("box", vertices=points, faces=indices, visible=1)
        self.assertEqual(len(polygon.faceSet.normals.GetProperty()), 6)


class IndexedPolygons_Viewer_Tests2(unittest.TestCase):
    """
    check IndexedPolygons in Viewer
    """

    def setUp(self):
        self.vi = Viewer(verbose=0)
        points = [
            [-1, 1, 1],
            [-1, -1, 1],
            [1, 1, 1],
            [1, -1, 1],
            [1, 1, -1],
            [1, -1, -1],
            [-1, 1, -1],
            [-1, -1, -1],
        ]
        indices = [
            [0, 1, 3, 2],
            [4, 5, 7, 6],
            [6, 7, 1, 0],
            [2, 3, 5, 4],
            [6, 0, 2, 4],
            [1, 7, 5, 3],
        ]
        self.geom = IndexedPolygons("box", vertices=points, faces=indices, visible=1)
        self.vi.AddObject(self.geom)
        self.vi.update()
        self.vi.currentCamera.DoPick(0.0, 0.0)
        self.vi.Redraw()

    def tearDown(self):
        """
        clean-up
        """
        try:
            self.vi.Exit()
        except:
            pass

    def test_Indexedpolygon_fnormals(self):
        """checks number of fnormals"""
        points = [
            [-1, 1, 1],
            [-1, -1, 1],
            [1, 1, 1],
            [1, -1, 1],
            [1, 1, -1],
            [1, -1, -1],
            [-1, 1, -1],
            [-1, -1, -1],
        ]

        indices = [
            [0, 1, 3, 2],
            [4, 5, 7, 6],
            [6, 7, 1, 0],
            [2, 3, 5, 4],
            [6, 0, 2, 4],
            [1, 7, 5, 3],
        ]
        polygon = IndexedPolygons(
            "box", vertices=points, faces=indices, visible=1, replace=True
        )
        self.vi.AddObject(polygon)
        # self.vi.stopAutoRedraw()
        self.vi.Redraw()
        self.assertEqual(len(polygon.faceSet.normals.GetProperty()), 6)


class IndexedPolygons_Viewer_Tests(unittest.TestCase):
    """
    tests for IndexedPolygons in DejaVu.Viewer
    """

    def setUp(self):
        """
        start Viewer
        """
        self.vi = Viewer(verbose=0)

        # guillaume: the faces are not correct here, but the test is usefull
        # because it detects if the normal provided are really used
        # (if it tries to calculate ---> it fails because the faces are not correct)
        self.geom = IndexedPolygons(
            "poly",
            vertices=((0, 0, 0), (5.0, 0.0, 0.0), (7, 2.5, 0.0), (5, 5, 0), (0, 5, 0)),
            vnormals=((1.0, 0, 0), (0, 1.0, 0), (1.0, 0, 0), (0, 1.0, 0), (1.0, 0, 0)),
            faces=((0, 1), (1, 2), (2, 3), (3, 4), (4, 0)),
            materials=((0.5, 0, 0),),
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

    # one test of setting properties via DejaVuGuiIndexedPolygons
    def test_IndexedPolygons_inheritMaterial(self):
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
    def test_IndexedPolygons_image(self):
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
        cam.SaveImage("./saveimageIndexedPolygons.tif")
        im = Image.open("./saveimageIndexedPolygons.tif")
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
        "IndexedPolygons__init__Tests",
        "IndexedPolygons_Set_Tests",
        "IndexedPolygons_Viewer_Tests2",
        "IndexedPolygons_Viewer_Tests",
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

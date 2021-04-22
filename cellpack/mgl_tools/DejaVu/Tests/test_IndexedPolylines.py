## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by

#
#
# $Id: test_IndexedPolylines.py,v 1.14 2007/08/10 14:07:03 vareille Exp $
#
#
import unittest
import numpy
import sys, os
from math import sqrt
from Tkinter import Menubutton
from opengltk.OpenGL import GL
from geomutils.geomalgorithms import TriangleNormals
import numpy.oldnumeric as Numeric, types
from DejaVu.Viewer import Viewer
from DejaVu.IndexedPolylines import IndexedPolylines
import Image


class IndexedPolylines__init__Tests(unittest.TestCase):
    """tests for IndexedPolylines.__init__"""

    def setUp(self):
        """
        create geom
        """
        self.geom = IndexedPolylines(name="basic")

    def tearDown(self):
        """
        clean-up
        """
        try:
            del self.geom
        except:
            pass

    def test_basic(self):
        """sanity check"""
        self.assertEqual(1, 1)

    def test_basic_init(self):
        """check object is created"""
        self.assertEqual(isinstance(self.geom, IndexedPolylines), True)


class IndexedPolylines_Set_Tests(unittest.TestCase):
    """tests for Set, Add methods"""

    def setUp(self):
        """
        #create geom
        """
        self.geom = IndexedPolylines(
            "geom",
            materials=((0, 1, 0),),
            vertices=((0, 0, 0), (1, 0, 0), (0, 1, 0)),
            faces=((0, 1), (1, 2)),
        )

    def tearDown(self):
        """
        clean-up
        """
        try:
            del self.geom
        except:
            pass

    def test_IndexedPolylines_faces(self):
        """check len(faces)"""
        self.assertEqual(len(self.geom.faceSet.faces.array), 2)

    def test_IndexedPolylines_faces_invalid_not_sequence(self):
        """invalid input for faces, faces should be list of lists of integers"""
        self.assertRaises(TypeError, self.geom.Set, faces=20)

    def test_IndexedPolylines_faces_invalid(self):
        """invalid input for faces, -20 not a good index"""
        self.assertRaises(ValueError, self.geom.Set, faces=[[-20, 3, 4]])

    def test_IndexedPolylines_faceSet_normals(self):
        """check len(faceSet.normals)"""
        self.assertEqual(len(self.geom.faceSet.normals), 0)

    def test_IndexedPolylines_primitiveType_GL_LINES(self):
        """check primitiveType, GL_LINES"""
        self.assertEqual(self.geom.primitiveType, GL.GL_LINES)

    def test_IndexedPolylines_linewidth(self):
        """valid input for lineWidth"""
        val = 3
        self.geom.Set(lineWidth=val)
        newstate = self.geom.getState()["lineWidth"]
        self.assertEqual(self.geom.getState()["lineWidth"], val)

    def test_Add_vertices(self):
        """valid input for Add vertices"""
        old_len = len(self.geom.vertexSet.vertices.array)
        self.geom.Add(vertices=((2, 0, 0), (4, 0, 0), (6, 0, 0)))
        self.assertEqual(len(self.geom.vertexSet.vertices.array), old_len + 3)


class IndexedPolylines_Viewer_Tests(unittest.TestCase):
    """
    tests for IndexedPolylines in DejaVu.Viewer
    """

    def setUp(self):
        """
        start Viewer
        """
        self.vi = Viewer(verbose=0)
        self.geom = IndexedPolylines(
            "test",
            vertices=((-1, 0, 0), (5.0, 0.0, 0.0)),
            faces=((0, 1),),
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

    # IndexedPolylines test of setting properties via DejaVuGui...
    def test_IndexedPolylines_inheritMaterial(self):
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

    # IndexedPolylines 3D image
    def test_IndexedPolylines_image(self):
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
        cam.SaveImage("./saveimage....tif")
        im = Image.open("./saveimage....tif")
        im = im.tostring()
        narray = Numeric.fromstring(im, "B")
        # print narray.shape
        narray.shape = (effective_height, effective_height, 3)
        narray_255 = narray / 255.0
        narray_255_sum = Numeric.add.reduce(narray_255)
        # print sum
        d = buff_255_sum - narray_255_sum
        # self.assertEqual(d,0)
        self.assertTrue(numpy.alltrue(d == [0.0, 0.0, 0.0]))


#        for v in d:
#            self.assertTrue(v[0]<1.e-9 and v[0]>-1.e-9)
#            self.assertTrue(v[1]<1.e-9 and v[1]>-1.e-9)
#            self.assertTrue(v[2]<1.e-9 and v[2]>-1.e-9)


if __name__ == "__main__":

    test_cases = [
        "IndexedPolylines__init__Tests",
        "IndexedPolylines_Set_Tests",
        "IndexedPolylines_Viewer_Tests",
    ]

    unittest.main(
        argv=(
            [
                __name__,
            ]
            + test_cases
        )
    )
    # remove the -v flag to make output cleaner
    # unittest.main( argv=([__name__ ,'-v'] + test_cases) )
    # unittest.main()

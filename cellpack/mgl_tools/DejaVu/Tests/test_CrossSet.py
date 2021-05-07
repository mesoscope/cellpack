## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by

#
#
# $Id: test_CrossSet.py,v 1.12 2009/07/13 19:15:22 vareille Exp $
#
#

from Tkinter import Menubutton
import unittest
import numpy
import numpy.oldnumeric as Numeric
from DejaVu.Viewer import Viewer
from time import sleep
import Image
from math import sqrt
from DejaVu.Points import CrossSet


class CrossSet__init__Tests(unittest.TestCase):
    """test keywords for __init__:
    keywords = [ 'offset' ]
    all other keywords are handled by Geom.__init__ method"""

    # defaults
    def test_CrossSet_defaults(self):
        """defaults for shape, radius, angles"""
        g = CrossSet()
        self.assertEqual(isinstance(g, CrossSet), True)

    # offset
    def test_CrossSet_offset(self):
        """offset 1 (default offset is  0.3))"""
        g = CrossSet(offset=1)
        self.assertEqual(isinstance(g, CrossSet), True)

    # vertices
    def test_CrossSet_radius(self):
        """vertices"""
        g = CrossSet(vertices=((0, 0, 0), (1, 1, 1)))
        self.assertEqual(isinstance(g, CrossSet), True)


class CrossSet_Set_Tests(unittest.TestCase):
    """
    # does override Geom.Set ??? one test that baseclass Set is called"""

    def setUp(self):
        """
        create geom
        """
        self.geom = CrossSet(name="test")

    def tearDown(self):
        """
        clean-up
        """
        try:
            del self.geom
        except:
            pass

    def test_CrossSet_Set_vertices(self):
        """
        test Setting vertices
        """
        self.geom.Set(centers=((2, 0, 2), (0, 2, 2)))
        # self.assertEqual(self.geom.vertexSet.vertices.array[0],((2,0,2),(0,2,2)))
        self.assertTrue(
            numpy.alltrue(self.geom.vertexSet.vertices.array[0] == (2, 0, 2))
        )

    def test_CrossSet_Set_name(self):
        """
        test Setting name
        """
        val = "new_name"
        self.geom.Set(name=val)
        self.assertEqual(self.geom.name, val)


class CrossSet_Viewer_Tests(unittest.TestCase):
    """
    tests for CrossSet in DejaVu.Viewer
    """

    def setUp(self):
        """
        start Viewer
        """
        self.vi = Viewer(verbose=0)
        self.geom = CrossSet(
            "crossset",
            vertices=((0, 0, 0), (1.0, 0.0, 0.0)),
            materials=((0.5, 0, 0),),
            offset=3.0,
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

    # one test of setting properties via DejaVuGuiCrossSet
    def test_CrossSet_inheritMaterial(self):
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
        # print "2:midpt=", buff_255[midpt][midpt]
        self.assertEqual(round(buff_255[midpt][midpt][0], 1) >= 0.4, True)

    # Arcs 3D image
    def test_CrossSet_image(self):
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
        # sleep(5)
        self.assertEqual(round(buff_255[midpt][midpt][0], 1) >= 0.1, True)
        buff_255_sum = Numeric.add.reduce(buff_255)
        cam.SaveImage("./saveimageCrossSet.tif")
        im = Image.open("./saveimageCrossSet.tif")
        im = im.tostring()
        narray = Numeric.fromstring(im, "B")
        # print narray.shape
        narray.shape = (effective_height, effective_height, 3)
        narray_255 = narray / 255.0
        narray_255_sum = Numeric.add.reduce(narray_255)
        # print sum
        d = buff_255_sum - narray_255_sum
        # self.assertEqual(d,0)
        # import pdb;pdb.set_trace()
        # self.assertTrue(numpy.alltrue(d==[0.,0.,0.]))
        for v in d:
            self.assertTrue(v[0] < 1.0e-9 and v[0] > -1.0e-9)
            self.assertTrue(v[1] < 1.0e-9 and v[1] > -1.0e-9)
            self.assertTrue(v[2] < 1.0e-9 and v[2] > -1.0e-9)


if __name__ == "__main__":
    test_cases = [
        "CrossSet__init__Tests",
        "CrossSet_Set_Tests",
        "CrossSet_Viewer_Tests",
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

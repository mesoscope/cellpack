import unittest
import sys, os, math
from Tkinter import Menubutton
import numpy
import numpy.oldnumeric as Numeric, types
from math import sqrt
from DejaVu.Viewer import Viewer
from DejaVu.Arrows import Axis
import Image
from time import sleep


class AxisTests(unittest.TestCase):
    def setUp(self):
        """
        start Viewer
        """
        self.vi = Viewer(verbose=0)
        self.vi.cameras[0].Set(height=300, width=300)
        self.vi.Redraw()

    def tearDown(self):
        """
        clean-up
        """
        try:
            self.vi.Exit()
        except:
            pass

    def test_Set_name(self):
        """
        test Setting name
        """
        val = "axis1"
        ax = Axis(
            "axis", point=[0, 0, 0], unitVector=[1, 0, 0], length=20.0, radius=0.3
        )
        ax.Set(name=val)
        self.assertEqual(ax.name, val)

    def test_Set_length(self):
        ax = Axis(
            "axis", point=[0, 0, 0], unitVector=[1, 0, 0], length=20.0, radius=0.3
        )
        self.vi.AddObject(ax)
        self.vi.Redraw()
        # sleep(5)
        val = 10
        arr1 = ax.vertexSet.vertices.array
        ax.Set(length=val)
        self.vi.OneRedraw()
        self.assertEqual(ax.length, val)
        arr2 = ax.vertexSet.vertices.array
        self.assertEqual(numpy.alltrue(numpy.equal(arr1, arr2)), False)

    def test_Set_points(self):
        ax = Axis(
            "axis", point=[0, 0, 0], unitVector=[1, 0, 0], length=20.0, radius=0.3
        )
        self.vi.AddObject(ax)
        self.vi.Redraw()
        # sleep(5)
        arr1 = ax.vertexSet.vertices.array
        ax.Set(point1=[1, 1, 1])
        arr2 = ax.vertexSet.vertices.array
        self.assertEqual(numpy.alltrue(numpy.equal(arr1, arr2)), False)
        ax.Set(point2=[5, 5, 5])
        self.vi.OneRedraw()
        arr3 = ax.vertexSet.vertices.array
        self.assertEqual(numpy.alltrue(numpy.equal(arr3, arr2)), False)

    def test_Set_materials(self):
        ax = Axis(
            "axis",
            point=[0, 0, 0],
            unitVector=[0, 1, 0],
            length=20.0,
            radius=0.3,
            color="green",
        )
        self.vi.AddObject(ax)
        self.vi.Redraw()
        # sleep(5)
        mat1 = numpy.array(
            [
                [1, 0, 0, 1],
            ],
            "f",
        )
        ax.Set(materials=mat1, inheritMaterial=0)
        mat2 = ax.materials[1028].prop[1]
        self.assertEqual(numpy.alltrue(numpy.equal(mat1, mat2)), True)
        self.vi.OneRedraw()
        ax.Set(color="blue", inheritMaterial=0)
        mat3 = numpy.array([[0.0, 0.0, 1.0, 1.0]], "f")
        self.assertEqual(
            numpy.alltrue(numpy.equal(mat3, ax.materials[1028].prop[1])), True
        )
        self.vi.OneRedraw()

    def test_Set_radius(self):
        ax = Axis(
            "axis",
            point=[0, 0, 0],
            unitVector=[0, 0, 1],
            length=20.0,
            radius=0.3,
            color="magenta",
        )
        self.vi.AddObject(ax)
        self.vi.Redraw()
        # sleep(5)
        val = 0.1
        ax.Set(radius=val)
        self.vi.OneRedraw()
        self.assertEqual(abs(ax.vertexSet.radii.array[1] - val) < 0.001, True)

    def test_image(self):
        """test creation of valid image by writing/reading a tif file"""
        cam = self.vi.currentCamera
        ax = Axis(
            "axis",
            point=[0, 0, 0],
            unitVector=[1, 1, 1],
            length=20.0,
            radius=1,
            color="white",
        )
        self.vi.AddObject(ax)
        self.vi.Redraw()
        from time import sleep

        # sleep(5)
        self.vi.update()
        ax.Set(radius=0.5)
        self.vi.OneRedraw()
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
        # print "buff_255[midpt][midpt][0]=", buff_255[midpt][midpt][0]
        # sleep(5)

        #        if sys.platform == 'win32':
        #            self.assertEqual(buff_255[midpt][midpt+2][0]>0.1, True)
        #        else:

        self.assertEqual(buff_255[midpt][midpt][0] > 0.1, True)

        buff_255_sum = Numeric.add.reduce(buff_255)
        cam.SaveImage("./saveimageax.tif")
        im = Image.open("./saveimageax.tif")
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
        "test_Set_name",
        "test_Set_length",
        "test_Set_points",
        "test_Set_materials",
        "test_Set_radius",
        "test_image",
    ]
    unittest.main(
        argv=(
            [
                __name__,
            ]
            + test_cases
        )
    )

## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#
#
# $Id: test_Labels.py,v 1.21 2008/10/28 23:10:52 vareille Exp $
#
#
import sys, os,math,types
from Tkinter import Menubutton
import unittest,numpy.oldnumeric as Numeric
from math import sqrt
from opengltk.OpenGL import GL
from DejaVu.Viewer import Viewer
from time import sleep
from DejaVu import viewerConst
import Image
from DejaVu.glfLabels import GlfLabels


class Labels__init__Tests(unittest.TestCase):
    """test keywords for __init__:
    keywords = [ 'labels',
                'font', 
                'offset']
    all other keywords are handled by Geom.__init__ method
"""

#defaults
    def test_Labels_defaults(self):
        """defaults for shape, radius, angles
        """
        g = GlfLabels()
        self.assertEqual(isinstance(g, GlfLabels), True)

  
#labels
    def test_Labels_labels(self):
        """labels ['TEST1']
        """
        g = GlfLabels(labels=("TEST",))
        self.assertEqual(isinstance(g, GlfLabels), True)

  
#font
    def test_Labels_radius(self):
        """font "glut9by15"
        """
        g = GlfLabels(font="arial1.glf")
        self.assertEqual(isinstance(g, GlfLabels), True)

  
#offset
    def test_Labels_offset(self):
        """offset 
        """
        g = GlfLabels(fontTranslation=(.1,.1,.1))
        self.assertEqual(isinstance(g, GlfLabels), True)

  

class Labels_Set_Tests(unittest.TestCase):
    """
# does not override Geom.Set so just one test that baseclass Set is called
"""

    def setUp(self):
        """
        create geom
        """
        self.geom = GlfLabels(name='test')


    def tearDown(self):
        """
        clean-up
        """
        try:
            del(self.geom)
        except:
            pass


    def test_Labels_Set_font(self):
        """
        test Setting font
        """
        val = "arial1.glf"
        self.geom.Set(font=val)
        self.assertEqual(self.geom.font, val)


    def test_Labels_Set_name(self):
        """
        test Setting name
        """
        val = 'new_name'
        self.geom.Set(name=val)
        self.assertEqual(self.geom.name, val)



class Labels_Viewer_Tests(unittest.TestCase):
    """
tests for Labels in DejaVu.Viewer
    """

    def setUp(self):
        """
        start Viewer
        """
        self.vi = Viewer(verbose = 0)
        cam = self.cam = self.vi.currentCamera
        cam.Set(height=200,width=200)
        self.vertices=((-3.7,0,0,),)
        #self.vertices=((-10,0,0,),)
        self.geom = GlfLabels(name='labels', shape=(0,3),
                       inheritMaterial=0, materials = ((1,0,0),),
                       visible=1,
                       labels = ["XXXXX",],
                       vertices=self.vertices,
                       font="arial1.glf") 
        self.vi.AddObject(self.geom)
        self.vi.update()
        self.cam.DoPick(0.,0.)
        self.vi.SetCurrentObject(self.geom)
        self.vi.OneRedraw()
            

    def tearDown(self):
        """
        clean-up
        """
        try:
            self.vi.Exit()
        except:
            pass
                   

    def test_Labels_sanity(self):
        """ sanity check"""
        #print 4
        cam = self.vi.currentCamera
        self.assertEqual(1,1)

                   

#one test of setting properties via DejaVuGuiLabels
    def test_Labels_inheritMaterial(self):
        """valid changing material by toggling inheritMaterial
        """
        """ NOTE toggling is done by invoking a button in dejaVuGUI
this test checks pixel in the middle of the scene when the object does not
inheritMaterial and is colored RED vs after inheritMaterial is restored when
the object is white (well grayish)
        """
        #print 3
        cam = self.vi.currentCamera
        self.vi.OneRedraw()
        self.vi.update()

        buff = cam.GrabFrontBufferAsArray()
        total_pixels = len(buff)/3
        effective_height = int(sqrt(total_pixels))
        midpt = int(effective_height/2)
        buff.shape = (effective_height,effective_height,3)
        buff_255 = buff/255.
        #print "1:midpt=", buff_255[midpt][midpt]
        #this is trying to checkthat the label is red
        #self.assertEqual(round(buff_255[midpt][midpt][0],1)>=0.1, True)
        self.assertEqual(round(buff_255[midpt][midpt][0],1)>=0.1, True)
        self.vi.OneRedraw()
        self.vi.update()
        for c in self.vi.GUI.inheritF.children.values():
            if   c.__class__ == Menubutton \
              and c.configure('text')[-1] == ('Current', 'geom', 'properties'):
                self.inheritF_menu = c.menu
        inheritMaterial_index = self.inheritF_menu.index('inheritMaterial')
        self.inheritF_menu.invoke(inheritMaterial_index)
        newstate = self.geom.getState()['inheritMaterial']
        #print "now self.geom.inheritMaterial=", newstate
        self.assertEqual(newstate, 1)
        self.vi.OneRedraw()
        buff = cam.GrabFrontBufferAsArray()
        total_pixels = len(buff)/3
        effective_height = int(sqrt(total_pixels))
        midpt = int(effective_height/2)
        buff.shape = (effective_height,effective_height,3)
        buff_255 = buff/255.
        #print "2:midpt=", buff_255[midpt][midpt]
        self.assertEqual(round(buff_255[midpt][midpt][0],1)>=0.4, True)


#Labels Image7
    def test_Labels_image(self):
        """valid image..checked by writing/reading a tif file
        """
        #print 2
        cam = self.vi.currentCamera
        self.vi.update()
        #self.cam.DoPick(0.,0.)
        self.vi.OneRedraw()
        buff = cam.GrabFrontBufferAsArray()
        #print "max pixel= ", max(buff.ravel())
        #on sgi, viewer is not 500x500 but 509 or 516 or? square
        total_pixels = len(buff)/3
        #print "total_pixels=", total_pixels
        effective_height = int(sqrt(total_pixels))
        #print "effective_height=", effective_height
        midpt = int(effective_height/2)
        #print "midpt=", midpt
        buff.shape = (effective_height,effective_height,3)
        buff_255 = buff/255.
        #print "pixel at midpoint of buffer=", buff_255[midpt][midpt]
        #print " buff_255[midpt][midpt]=", buff_255[midpt][midpt]
        #check that the pixel is not black
        self.assertEqual(round(buff_255[midpt][midpt][0],1)>=0.1, True)
        buff_255_sum = Numeric.add.reduce(buff_255)
        cam.SaveImage("./saveimageLabels.tif")
        im = Image.open("./saveimageLabels.tif")
        im = im.tostring()
        narray = Numeric.fromstring(im,'B')
        #print narray.shape
        narray.shape = (effective_height,effective_height,3)
        narray_255 = narray/255.
        narray_255_sum = Numeric.add.reduce(narray_255)
        #print sum
        d = buff_255_sum-narray_255_sum
        #self.assertEqual(d,0)
        #self.assertTrue(numpy.alltrue(d==[0.,0.,0.]))
        for v in d:
            self.assertTrue(v[0]<1.e-9)
            self.assertTrue(v[1]<1.e-9)
            self.assertTrue(v[2]<1.e-9)


    def test_Labels_Set(self):
        """valid image..checked by writing/reading a tif file
"""
        #print 1
        cam = self.vi.currentCamera
        try:
            self.geom.Set( 
                  inheritMaterial=0,
                  materials = ((1,0,0),),
                  visible=1,
                  labels = ["lili", ],
                  vertices=( (3.8, 0.2, 0.4), (3.8, 0.2, 0.4)),
                  font="arial1.glf") 
            self.vi.OneRedraw()
        except Exception, e:
            print "Exception", e
            self.assertEqual(1,0)


if __name__ == '__main__':
    test_cases = [
        'Labels__init__Tests',
        'Labels_Set_Tests',
        'Labels_Viewer_Tests',
        ]

    unittest.main( argv=([__name__ ,] + test_cases) )
    #unittest.main( argv=([__name__ , '-v'] + test_cases) )

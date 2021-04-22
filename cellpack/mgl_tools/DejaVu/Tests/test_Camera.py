## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#
# 
# $Id: test_Camera.py,v 1.55 2010/11/22 21:23:36 annao Exp $
# 
#

import sys, os, math, types
import numpy
from Tkinter import Tk, Toplevel
import unittest,numpy.oldnumeric as Numeric
from opengltk.OpenGL import GL
from DejaVu.Camera import Camera
from DejaVu.Viewer import Viewer
from DejaVu.Spheres import Spheres
from opengltk.extent.utillib import glCleanRotMat
from time import sleep
from DejaVu.IndexedPolygons import IndexedPolygons
from DejaVu.ViewerGUI import ViewerGUI
from DejaVu import viewerConst,datamodel
import Image
from math import sqrt
from mglutil.math.rotax import rotax

class Camera_BaseTests(unittest.TestCase):
    """
    setUp + tearDown form a fixture: working environment for the testing code
    """

    def setUp(self):
        """
        start Viewer
        """ 
        if not hasattr(self, 'vi'):
            self.vi = Viewer(verbose=0)
            self.vi.currentCamera.Set(height=500, width=500)


    def tearDown(self):
        """
        clean-up
        """
        try:
            self.vi.Exit()
        except:
            pass


    def test_SaveImage(self):
        """test save image
        """
        cmd = "rm -f ./saveImage.tif"
        os.system(cmd)
        s1 = Spheres('sph', vertices = [[0,0,0], [3,0,0], [0,3,0], [0,0,3]])
        self.vi.AddObject(s1)
        cam = self.vi.currentCamera
        cam.SaveImage("./saveImage.tif")
        self.vi.Exit()
        self.assertEqual( os.path.exists("./saveImage.tif"), True)


    def test_setCamera_width(self):
        """test camera width
        """
        cam = self.vi.currentCamera
        # set the camera width
        cam.Set(width=150)
        self.assertEqual(cam.width, 150)
        # ask for the window size
        x,y,w,h = cam.getGeometry()
        # make sure the window actually has the right size
        self.assertEqual(w, 150)
        self.assertEqual(cam.__class__, Camera)
        # make sure the camera's state reflects the change
        newstate = cam.getState()
        self.assertEqual(newstate['width'], 150)
        self.vi.Exit()
            

    def test_setCamera_width_invalid_input(self):
        """test camera width negative input
        """
        cam = self.vi.currentCamera
        self.assertRaises(AttributeError,cam.Set,width=-15)
            

    def test_setCamera_width_invalid_inputFloat(self):
        """test camera width float input
        """
        cam = self.vi.currentCamera
        self.assertRaises(AssertionError,cam.Set,width=450.)

   
    def test_setCamera_fov(self):
        """fov has to be <180,>0
        """
        cam = self.vi.currentCamera
        cam.Set(fov=120)
        newstate = cam.getState()
        self.vi.Exit()            
        self.assertEqual(newstate['fov'], 120)


    def test_setCamera_fov_invalid_input(self):
        """fov >180, invalid input
        """
        cam = self.vi.currentCamera
        self.assertRaises(AttributeError,cam.Set,fov=190)
             
    def test_setCamera_rootx(self):
        """test camera rootx
        """
        cam = self.vi.currentCamera
        cam.Set(rootx=220)
        newstate = cam.getState()
        self.vi.Exit()
        self.assertEqual(newstate['rootx'], 220)
        
    def test_setCamera_rootx_negative(self):
        """test camera rootx invalid input
        """
        cam = self.vi.currentCamera
        cam.Set(rootx=-100)
        self.assertEqual(cam.rootx, 0)
       
    def test_setCamera_height(self):
        """test camera height
        """
        cam = self.vi.currentCamera
        # set the camera height
        cam.Set(height=150)
        self.assertEqual(cam.height, 150)
        # ask for the window size
        x,y,w,h = cam.getGeometry()
        # make sure the window actually has the right size
        self.assertEqual(h, 150)
        self.assertEqual(cam.__class__, Camera)
        # make sure the camera's state reflects the change
        newstate = cam.getState()
        self.assertEqual(newstate['height'], 150)
        self.vi.Exit()
        

    def test_setCamera_height_invalid_input(self):
        """test camera height invalid input
        """
        cam = self.vi.currentCamera
        self.assertRaises(AttributeError,cam.Set,height=-400)
           

    def test_setCamera_height_invalid_inputFloat(self):
        """test camera height float input
        """
        cam = self.vi.currentCamera
        self.assertRaises(AssertionError,cam.Set,height=450.)


    def test_setCamera_rooty(self):
        """ test camera rooty
        """
        cam = self.vi.currentCamera
        cam.Set(rooty=320)
        newstate = cam.getState()
        self.vi.Exit()
        self.assertEqual(newstate['rooty'], 320)
        
    def test_setCamera_rooty_negative(self):
        """test camera rooty invalid input
        """
        cam = self.vi.currentCamera
        cam.Set(rooty=-100)
        self.assertEqual(cam.rooty, 0)
              
    def test_setCamera_near(self):
        """test camera near
        """
        cam = self.vi.currentCamera
        cam.Set(near=10)
        newstate = cam.getState()
        self.vi.Exit()
        self.assertEqual(newstate['near'], 10)
        

    def test_setCamera_near_invalid_input(self):
        """ test near should be less than far
        """
        cam = self.vi.currentCamera
        cam.Set(far=20)
        self.assertRaises(AttributeError,cam.Set,near = 40)
       
    def test_setCamera_far(self):
        """test camera far
        """
        cam = self.vi.currentCamera
        cam.Set(far=20)
        newstate = cam.getState()
        self.vi.Exit()
        self.assertEqual(newstate['far'], 20)

    
    def test_setCamera_far_invalid_input(self):
        """test far should be larger than near
        """
        cam = self.vi.currentCamera
        cam.Set(near=10)
        self.assertRaises(AttributeError,cam.Set,far = 5) 
       
       
    def test_setCamera_color(self):
        """ test camera color
        """
        cam = self.vi.currentCamera
        cam.Set(color=(1.0,1.0,1.0,1.0))
        newstate = cam.getState()
        self.vi.Exit()
        self.assertEqual(newstate['color'],(1.0,1.0,1.0,1.0))


    def test_setCamera_color_invalid(self):
        """ test camera color invalid input 
        """
        cam = self.vi.currentCamera
        rval = cam.Set(color = (1.0,1.0,1.0))
        self.assertEqual(rval,None)
        

    def test_setCamera_antialiased(self):
        """test antialiased
        """
        cam = self.vi.currentCamera
        cam.Set(antialiased=0)
        newstate = cam.getState()
        self.vi.Exit()
        self.assertEqual(newstate['antialiased'],0)


    def test_setCamera_antialiased_invalid_input(self):
        """test antialiased invalid input
        """
        cam = self.vi.currentCamera
        self.assertRaises(ValueError,cam.Set,antialiased='hai')
       
    def test_setCamera_boundingbox_NO(self):
        """test camera bounding box 
        """
        cam = self.vi.currentCamera
        cam.Set(boundingbox=0)
        newstate = cam.getState()
        self.vi.Exit()
        self.assertEqual(newstate['boundingbox'],0)
        

    def test_setCamera_boundingbox_invalid_input(self):
        """test camera bounding box invalid input
        """
        cam = self.vi.currentCamera
        self.assertRaises(ValueError,cam.Set,boundingbox='hai')
          
    def test_setCamera_projection_type(self):
        """test camera projection type
        """
        cam = self.vi.currentCamera
        cam.Set(projectionType=1)
        newstate = cam.getState()
        self.vi.Exit()
        self.assertEqual(newstate['projectionType'],1)
   

    def test_setCamera_projection_type_invalid(self):
        """test camera projection type invalid
        """
        cam = self.vi.currentCamera
        rval = cam.Set(projectionType='hai')
        self.assertEqual(rval,None)
       
    def test_setCamera_contours(self):
        """test camera contours
        """
        cam = self.vi.currentCamera
        cam.Set(contours=True)
        newstate = cam.getState()
        self.vi.Exit()
        self.assertEqual(newstate['contours'], True, msg="Expecting cam.contours to be set to True")
         

    def test_setCamera_stereo_mode_side_by_side(self):
        """test camera stereoMode
        """
        cam = self.vi.currentCamera
        cam.Set(stereoMode='SIDE_BY_SIDE_CROSS')
        newstate = cam.getState()
        self.vi.Exit()
        self.assertEqual(newstate['stereoMode'],'SIDE_BY_SIDE_CROSS')


    def test_setCamera_stereo_mode_side_by_side_invalid(self):
        """test camera stereoMode
        """
        cam = self.vi.currentCamera
        self.assertRaises(AssertionError,cam.Set,stereoMode='hai')

    def test_setCamera_side_by_side_rot_angle(self):
        """test camera sideBySideRotAngle
        """
        cam = self.vi.currentCamera
        cam.Set(sideBySideRotAngle=5.)
        newstate = cam.getState()
        self.vi.Exit()
        self.assertEqual(newstate['sideBySideRotAngle'],5.)


    def test_setCamera_side_by_side_rot_angle_invalid(self):
        """test camera sideBySideRotAngle,invalid input
        """
        cam = self.vi.currentCamera 
        self.assertRaises(AssertionError,cam.Set,sideBySideRotAngle='hai')
        
    def test_setCamera_side_by_side_translation(self):
        """test camera sideBySideTranslation
        """
        cam = self.vi.currentCamera
        cam.Set(sideBySideTranslation=3.)
        newstate = cam.getState()
        self.vi.Exit()
        self.assertEqual(newstate['sideBySideTranslation'],3.)
    

    def test_setCamera_side_by_side_translation_invalid(self):
        """test camera sideBySideTranslation,invalid input
        """
        cam = self.vi.currentCamera
        self.assertRaises(AssertionError,cam.Set,sideBySideTranslation='hai')
        
    def test_setCamera_pivot(self):
        """test camera pivot
        """
        
        cam = self.vi.currentCamera
        mat = Numeric.reshape(Numeric.array(Numeric.ones( (3,), 'f')), (3,)).astype('f')
        cam.SetPivot(mat)
        newstate = cam.getState()
        self.vi.Exit()
        self.assertEqual(newstate['pivot'],[1.0,1.0,1.0])
            

    def test_setCamera_pivot_invalid(self):
        """test camera pivot,invalid input
        """
        cam = self.vi.currentCamera
        self.assertRaises(ValueError,cam.SetPivot,[1.0,1.0])
               

    def test_setCamera_scale(self):
        """test camera scale
        """
        cam = self.vi.currentCamera
        mat = Numeric.ones( (3,), 'f')
        cam.SetScale(mat)
        newstate = cam.getState()
        self.vi.Exit()
        self.assertEqual(newstate['scale'],[1.0,1.0,1.0])
    

    def test_setCamera_scale(self):
        """test camera scale
        """
        cam = self.vi.currentCamera
        self.assertRaises(AssertionError,cam.SetScale,([1.0,1.0]))


    def test_setCamera_rotation(self):
        """test camera rotation
        """
        cam = self.vi.currentCamera
        from DejaVu.IndexedPolylines import IndexedPolylines
        lines=IndexedPolylines('mylines',materials=((0,1,0),))
        self.vi.AddObject(lines)
        lines.Set(vertices =[[0,0,0],[1,0,0]],faces=((0,1),))
##         from mglutil.math.rotax import rotax
##         import math
##         matRot = rotax( (0,0,0), (0,0,1), math.pi/2.)
##         cam.Set(rotation=matRot)
##         self.vi.Redraw()
##         newstate = cam.getState()
##         self.vi.Exit()
##         lTestedValues = [0, -1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
##         for i in range(16):
##             self.assertTrue( newstate['rotation'][i] < lTestedValues[i] + 1.e9)
##             self.assertTrue( newstate['rotation'][i] > lTestedValues[i] - 1.e9)
        lf1 = numpy.array([-20, 20, 0],'f')
        cam.Set(lookFrom = lf1)
        self.vi.Redraw()
        lf2 = cam.lookFrom
        self.assertTrue(numpy.alltrue(lf1==lf2), True)
        self.vi.Exit()
            

##     def test_setCamera_rotation_invalid_input(self):
##         """test camera rotation,invalid input
##         """
##         cam = self.vi.currentCamera
##         from DejaVu.IndexedPolylines import IndexedPolylines
##         lines=IndexedPolylines('mylines',materials=((0,1,0),))
##         self.vi.AddObject(lines)
##         lines.Set(vertices =[[0,0,0],[1,0,0]],faces=((0,1),))
##         self.assertRaises(ValueError,cam.Set,rotation=[1.0,1.0])
             

    def test_setCamera_lookat(self):
        """test camera look at
        """
        cam = self.vi.currentCamera
        mat = Numeric.reshape(Numeric.array(Numeric.ones(3)), (3,)).astype('f')
        cam.Set(lookAt=mat)
        #self.assertEqual(cam.lookAt,mat)
        self.assertTrue(numpy.alltrue(cam.lookAt == mat))
        self.vi.Exit()


    def test_setCamera_lookat_invalid(self):
        """test camera look at,invalid input
        """
        cam = self.vi.currentCamera
        self.assertRaises(AssertionError,cam.Set,lookAt = [1.0,1.0])
               
    def test_setCamera_lookFrom(self):
        """test camera look from
        """
        cam = self.vi.currentCamera
        mat = Numeric.reshape(Numeric.array(Numeric.ones(3)), (3,)).astype('f')
        cam.Set(lookFrom=mat)
        #self.assertEqual(cam.lookFrom,mat)
        self.assertTrue(numpy.alltrue(cam.lookFrom == mat))
        self.vi.Exit()


    def test_setCamera_lookFrom_invalid(self):
        """test camera look from,invalid input
        """
        cam = self.vi.currentCamera
        self.assertRaises(AssertionError,cam.Set,lookFrom = [1.0,1.0])
               
    def test_setCamera_direction(self):
        """test camera direction
        """
        cam = self.vi.currentCamera
        mat = Numeric.reshape(Numeric.array(Numeric.ones(3)), (3,)).astype('f')
        mat1 = Numeric.reshape(Numeric.array(Numeric.zeros(3)), (3,)).astype('f')
        cam.Set(lookAt=mat,lookFrom=mat1)
        #self.assertEqual(cam.direction,cam.lookAt - cam.lookFrom)
        self.assertTrue(numpy.alltrue(cam.direction == (cam.lookAt - cam.lookFrom)))
        self.vi.Exit()
    

    def test_setCamera_direction_invalid(self):
        """test camera direction,invalid input
        """
        cam = self.vi.currentCamera
        self.assertRaises(ValueError,cam.Set,direction = [1.0,1.0])
       
    def test_setCamera_translation(self):
        """test setCamera_translation
        """
        cam = self.vi.currentCamera
        from DejaVu.IndexedPolylines import IndexedPolylines
        lines=IndexedPolylines('mylines',materials=((0,1,0),))
        self.vi.AddObject(lines)
        lines.Set(vertices =[[1,0,1],[1,1,1]],faces=((0,1),))
        #cam.Set(translation=Numeric.ones(3, 'f'))
        cam.SetTranslation(Numeric.ones(3, 'f'))
        self.vi.OneRedraw()
        self.vi.update()
        newstate = cam.getState()
        self.vi.Exit()
        #self.assertEqual(newstate['translation'],Numeric.ones(3))
        for v in newstate['translation']:
            self.assertTrue(v < 1. + 1.e-9)
            self.assertTrue(v > 1. - 1.e-9)


    def test_setCamera_translation_invalid(self):
        """test camera translation,invalid input
        """
        cam = self.vi.currentCamera
        from DejaVu.IndexedPolylines import IndexedPolylines
        lines=IndexedPolylines('mylines',materials=((0,1,0),))
        self.vi.AddObject(lines)
        lines.Set(vertices =[[1,0,1],[1,1,1]],faces=((0,1),))
        self.assertRaises(AttributeError,cam.SetTranslation,[1.0,1.0])


    def test_setCamera_rotation_lines(self):
        """test camera set rotation
"""
        #apply(self.vi.AddCamera, (self.master, None, Camera,), {})
        cam = self.vi.currentCamera
        from DejaVu.IndexedPolylines import IndexedPolylines
        lines=IndexedPolylines('mylines',materials=((0,1,0),))
        self.vi.AddObject(lines)
        lines.Set(vertices =[[0,0,0],[1,0,0]],faces=((0,1),))
        self.vi.OneRedraw()
        array1=cam.GrabFrontBufferAsArray()
##         matRot = rotax( (0,0,0), (0,0,1), math.pi*.5)
##         cam.Set(rotation=matRot)
        
        cam.Set(lookFrom = numpy.array([-20, 20, 0],'f'))
        self.vi.OneRedraw()
        array2=cam.GrabFrontBufferAsArray()
        
        array1.shape = (500, 500, 3)
        array2.shape = (500, 500, 3)
        #print "array1[249][250]", array1[249][250]
        #print "array1[250][251]", array1[250][251]
        #print "array2[249][250]", array2[249][250]
        #print "array2[250][251]", array2[250][251]
        
        d=array1-array2
        error=Numeric.add.reduce(d)
        self.vi.Exit()
        #self.assertEqual(error!=0, True)
        self.assertEqual(error.max()>1.e-9, True)
       



    def test_setCamera_image(self):
        """test setCamera_image
        """
        cam = self.vi.currentCamera
        from DejaVu.IndexedPolylines import IndexedPolylines
        lines=IndexedPolylines('mylines',materials=((0,1,0),))
        self.vi.AddObject(lines)
        lines.Set(vertices =[[0,0,0],[1,0,0]],faces=((0,1),))
        self.vi.OneRedraw()
        cam.SaveImage("./saveimage1.tif")
        #matRot = rotax( (0,0,0), (0,0,1), math.pi*.5)
        #cam.Set(rotation=matRot)
        cam.Set(lookFrom = [-20, 20, 0])
        self.vi.OneRedraw()
        cam.SaveImage("./saveimage2.tif")
        fptr=open("./saveimage1.tif")
        alllines=fptr.readlines()
        fptr1=open("./saveimage2.tif")
        alllines1=fptr1.readlines()
        self.vi.Exit()
        self.assertEqual(alllines==alllines1,False)




#methods

    def test_orthogonal_to_perspective(self):
        """test_orthogonal_to_perspective
        """
        cam = self.vi.currentCamera
        points = [
        [-1, 1, 1], [-1, -1, 1], [1, 1, 1], [1, -1, 1],
        [1, 1, -1], [1, -1, -1], [-1, 1, -1], [-1, -1, -1]
        ]

        indices = [
        [0, 1, 3, 2], [4, 5, 7, 6], [6, 7, 1, 0],
        [2, 3, 5, 4], [6, 0, 2, 4], [1, 7, 5, 3]
        ]
        geomBox = IndexedPolygons("box", vertices=points, faces=indices, visible=1)
        self.vi.AddObject(geomBox)
        self.vi.OneRedraw()
        self.vi.update()
        #sleep(5)
        array1 = cam.GrabFrontBufferAsArray()
        sum1 = Numeric.add.reduce(array1)
        #print sum1
        cam.Set(projectionType=1)
        #cam.OrthogonalToPerspective()
        self.vi.OneRedraw()
        self.vi.update()
        array2 = cam.GrabFrontBufferAsArray()
        sum2 = Numeric.add.reduce(array2)
        #print sum2
        cam.Set(projectionType=0)
        #cam.PerspectiveToOrthogonal()
        self.vi.OneRedraw()
        self.vi.update()
        array3 = cam.GrabFrontBufferAsArray()
        sum3 = Numeric.add.reduce(array3)
        #print sum3
        self.vi.Exit()
        self.assertEqual(sum1,sum3)


    def test_SaveImage(self):
        """test_Images
"""
        cam = self.vi.currentCamera
        sph = Spheres("sp", centers=( (0,0,0),),
                  radii = (1,),)
        self.vi.AddObject(sph)
        self.vi.OneRedraw()
        self.vi.update()
        import time
        time.sleep(1)
        buff = cam.GrabFrontBufferAsArray()
        #print "max pixel= ", max(buff.ravel())
        #sum_array=Numeric.add.reduce(buff)
        #on sgi, viewer is not 500x500 but 509 or 516 or? square
        total_pixels = len(buff)/3
        effective_height = sqrt(total_pixels)
        midpt = int(effective_height/2)
        buff.shape = (effective_height,effective_height,3)
        buff_255 = buff/255.
        #print "pixel at midpoint of buffer=", buff_255[midpt][midpt]
        #check that the pixel is not black
        self.assertEqual(buff_255[midpt][midpt][0]>0.1, True)
        buff_255_sum=Numeric.add.reduce(buff_255)
        cam.SaveImage("./saveimagesph.tif")
        im = Image.open("./saveimagesph.tif")
        im = im.tostring()
        narray = Numeric.fromstring(im,'B')
        #print narray.shape
        narray.shape = (effective_height,effective_height,3)
        narray_255 = narray/255.
        narray_255_sum=Numeric.add.reduce(narray_255)
        #print sum
        d=buff_255_sum-narray_255_sum
        self.vi.Exit()
        #self.assertEqual(d,0)
        #self.assertTrue(numpy.alltrue(d==[0.,0.,0.]))
        for v in d:
            self.assertTrue(v[0]<1.e-9)
            self.assertTrue(v[1]<1.e-9)
            self.assertTrue(v[2]<1.e-9)


    def test_DoPick(self):
        cam = self.vi.currentCamera
        cam.Redraw()
        sph = Spheres("sp", centers=( (0,0,0),),
                  radii = (10,),)
        self.vi.AddObject(sph)
        pick  = cam.DoPick(250,250)
        self.assertEqual(str(pick.hits),'{<DejaVu.Spheres.GLUSpheres> sp with 1 vertices: [(0, [0, 0])]}')


#    def DrawPickingSphere(self):
#        cam = self.vi.currentCamera
#        from DejaVu.IndexedPolylines import IndexedPolylines
#        lines=IndexedPolylines('mylines',materials=((0,1,0),))
#        self.vi.AddObject(lines)
#        lines.Set(vertices =[[0,0,0],[1,0,0]],faces=((0,1),))
#        p = cam.DoPick(250,250)
#        cam.DrawPickingSphere(p)
#        self.assertEqual(len(self.vi.pickVerticesSpheres.vertexSet),1)


    def test_CameraSize(self):
        import numpy.oldnumeric as Numeric
        from opengltk.OpenGL import GL
        from DejaVu import Viewer
        from DejaVu.Cylinders import CylinderArrows
        coordSyst = CylinderArrows('coordSystem',
                vertices=([0,0,0], [10,0,0],[0,10,0],[0,0,10]),
                faces = ([0,1], [0,2], [0,3]),
                materials = ((1.,0,0), (0,1,0), (0,0,1)),
                radii = 0.6, inheritMaterial=False,
                inheritCulling=False,
                backPolyMode=GL.GL_FILL,
                inheritBackPolyMode=False,
                quality=10)
        coordSyst.Set(culling=GL.GL_NONE)
        self.vi.AddObject(coordSyst, parent=self.vi.FindObjectByName('root'))
        c1 = self.vi.AddCamera()
        c0 = self.vi.cameras[0]
        c0.Activate()
        m0 = Numeric.array(GL.glGetDoublev(GL.GL_PROJECTION_MATRIX)).astype('f')
        c1.Activate()
        self.vi.update()
        m1 = Numeric.array(GL.glGetDoublev(GL.GL_PROJECTION_MATRIX)).astype('f')
        c1.Set(width=600)
        c1.Redraw()
        c1.Activate()
        self.vi.update()
        m11 = Numeric.array(GL.glGetDoublev(GL.GL_PROJECTION_MATRIX)).astype('f')
        c0.Activate()
        self.vi.update()
        #self.vi.DeleteCamera(c1)
        assert Numeric.sum(m1-m11)>0.0001


    def test_CameraNpr(self):
        from opengltk.OpenGL import GL
        from DejaVu.Cylinders import CylinderArrows
        coordSyst = CylinderArrows('coordSystem',
                vertices=([0,0,0], [10,0,0],[0,10,0],[0,0,10]),
                faces = ([0,1], [0,2], [0,3]),
                materials = ((1.,0,0), (0,1,0), (0,0,1)),
                radii = 0.6, inheritMaterial=False,
                inheritCulling=False,
                backPolyMode=GL.GL_FILL,
                inheritBackPolyMode=False,
                quality=10)
        coordSyst.Set(culling=GL.GL_NONE)
        self.vi.AddObject(coordSyst, parent=self.vi.FindObjectByName('root'))
        self.vi.GUI.contourTk.set(True)
        self.vi.currentCamera.Set(contours=True, tagModified=False)
        self.vi.currentCamera.Redraw()
        self.vi.update()
        lArray=self.vi.currentCamera.GrabFrontBufferAsArray()
        lSum = numpy.add.reduce(lArray)
        print "lSum:", lSum
        lSumDict = {}
        lSumDict['levi'] = 179429081
        lSumDict['jacob'] = 180898722
        lSumDict['mslaptop4'] = 180898731 #179429399
        lSumDict['rapa'] =  180897551 #179428587
        lSumDict['austral'] = 175905763 #174520068
        lSumDict['anaa'] = 180875930 #179402096
        lSumDict['mslaptop1'] = 174525533
        self.assertTrue( lSum in lSumDict.values(),
                         msg='test_CameraNpr lSum: %d'%lSum)


if __name__ == '__main__':
    unittest.main()


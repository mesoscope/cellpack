from DejaVu import Viewer
from DejaVu.Spheres import Spheres
from DejaVu.IndexedPolylines import IndexedPolylines
from DejaVu.Materials import propertyNum
from time import sleep
import unittest
import sys

#declare the 'showwarning'  variable that is used in the code returned by maa.getSourceCode()
showwarning = False

class CustomAnimations_Tests(unittest.TestCase):

    def setUp(self):
        """Create DejaVu Viewer
        """
        #if not hasattr(self, "vi"):
        self.vi = Viewer()

    def tearDown(self):
        """
        clean-up
        """
        try:
            self.vi.Exit()
        except:
            pass

    
    def test_flyin(self):
        """Tests:
           - creation of FlyInObjectMAA with different options (number
             of keyframes, direction)
           - playing different frames of maa . """

        vi = self.vi
        sph = Spheres( 'sph', centers=[ (0,0,0), (5, 0,0), (0,5,0), (0, 0,5) ],
                       materials = [ (1,1,1),  (1,0,0),  (0,1,0),  (0,0,1) ],
                       inheritMaterial=False) 
        vi.AddObject(sph)

        from DejaVu.scenarioInterface.animations import FlyInObjectMAA
        # fly in from left
        maa1 = FlyInObjectMAA(sph, objectName=None, direction='left', kfpos=[0, 30])
        actors = maa1.actors
        self.assertEqual(len(actors), 3)
        vi.OneRedraw()
        sph.Set(translation=[0,0,0])
        # check that the position (translation) of the object changes from left to center
        # of the viewer at frames 0 - 15 - 30
        maa1.setValuesAt(0)
        t1 = sph.translation[0]
        vi.OneRedraw()
        self.assertEqual(t1 < 0, True)
        maa1.setValuesAt(15)
        t2 = sph.translation[0]    
        self.assertEqual( int(t1/2), int(t2))
        vi.OneRedraw()
        maa1.setValuesAt(30)
        t3 = sph.translation[0]    
        self.assertEqual(t3, 0)
        vi.OneRedraw()

        # fly in from right
        maa2 = FlyInObjectMAA(sph, objectName=None, direction='right', kfpos=[0, 60])
        actors = maa2.actors
        self.assertEqual(len(actors), 3)
        sph.Set(translation=[0,0,0])
        # check that the position (translation) of the object changes from right to center
        # of the viewer at frames 0 - 30- 60
        maa2.setValuesAt(0)
        vi.OneRedraw()
        t1 = sph.translation[0]
        self.assertEqual(t1 > 0, True)
        maa2.setValuesAt(30)
        vi.OneRedraw()
        t2 = sph.translation[0]    
        self.assertEqual(int(t1/2), int(t2))
        maa2.setValuesAt(60)
        vi.OneRedraw()
        t3 = sph.translation[0]    
        self.assertEqual(t3, 0)

        # fly in from top
        maa3 = FlyInObjectMAA(sph, objectName=None, direction='top', kfpos=[0, 30])
        actors = maa3.actors
        self.assertEqual(len(actors), 3)
        sph.Set(translation=[0,0,0])
        # check that the position (translation) of the object changes from top to center
        # of the viewer at frames 0 - 15 - 30
        maa3.setValuesAt(0)
        vi.OneRedraw()
        t1 = sph.translation[1]
        self.assertEqual(t1 > 0, True)
        maa3.setValuesAt(15)
        vi.OneRedraw()
        t2 = sph.translation[1]    
        self.assertEqual(int(t1/2), int(t2))
        maa3.setValuesAt(30)
        vi.OneRedraw()
        t3 = sph.translation[1]    
        self.assertEqual(t3, 0)

        # fly in from bottom
        
        maa4 = FlyInObjectMAA(sph, objectName=None, direction='bottom', kfpos=[0, 60])
        actors = maa4.actors
        self.assertEqual(len(actors),3)
        sph.Set(translation=[0,0,0])
        sph.Set(visible = 0)
        # check that the position (translation) of the object changes from bottom to center
        # of the viewer at frames 0 - 30 - 60
        maa4.setValuesAt(0)
        vi.OneRedraw()
        # check that the "visible" maa's actor sets the sph.visible attribute to 1
        self.assertEqual(sph.visible, 1)
        t1 = sph.translation[1]
        self.assertEqual( t1 <  0, True)
        maa4.setValuesAt(30)
        vi.OneRedraw()
        t2 = sph.translation[1]    
        self.assertEqual( int(t1/2), int(t2))
        maa4.setValuesAt(60)
        vi.OneRedraw()
        t3 = sph.translation[1]    
        self.assertEqual(t3, 0)

        #run maa 
        maa1.run()
        maa2.run()
        maa3.run()
        self.assertEqual(sph.visible, 1)

        maa4.run()

        #check we can reproduce the maa from it's sourcecode:
        maa5 = None
        maasrc = maa4.getSourceCode("maa5")
        viewer = vi
        exec(maasrc)
        assert maa5 != None
        self.assertEqual(len(maa5.actors),3)
        sph.Set(translation=[0,0,0])
        # check that the position (translation) of the object changes from bottom to center
        # of the viewer at frames 0 - 30 - 60
        maa5.setValuesAt(0)
        vi.OneRedraw()
        # check that the "visible" maa's actor sets the sph.visible attribute to 1
        self.assertEqual(sph.visible, 1)
        t1 = sph.translation[1]
        self.assertEqual( t1 <  0, True)
        maa5.setValuesAt(30)
        vi.OneRedraw()
        t2 = sph.translation[1]    
        self.assertEqual( int(t1/2), int(t2))
        maa5.setValuesAt(60)
        vi.OneRedraw()
        t3 = sph.translation[1]    
        self.assertEqual(t3, 0)
        


    def test_flyout(self):
        """Test creation of FlyOutObjectMAA with different options (number of keyframes, direction); playing different frames of maa ."""

        vi = self.vi
        sph = Spheres( 'sph', centers=[ (0,0,0), (5, 0,0), (0,5,0), (0, 0,5) ],
                       materials = [ (1,1,1),  (1,0,0),  (0,1,0),  (0,0,1) ],
                       inheritMaterial=False) 
        vi.AddObject(sph)

        from DejaVu.scenarioInterface.animations import FlyOutObjectMAA
        # direction: left
        sph.Set(translation=[0,0,0])
        maa1 = FlyOutObjectMAA(sph, objectName=None, direction='left', kfpos=[0, 30])
        actors = maa1.actors
        self.assertEqual (len(actors), 3)
        vi.OneRedraw()
        sph.Set(translation=[5,-5,5])
        # check that the position (translation) of the object changes from center to left side
        # of the viewer at frames 0 - 15 - 30
        maa1.setValuesAt(0)
        t1 = sph.translation
        vi.OneRedraw()
        self.assertEqual ([t1[0], t1[1], t1[2]] , [0, 0, 0])
        maa1.setValuesAt(15)
        t2 = sph.translation[0]
        self.assertEqual(t2 < 0, True)
        vi.OneRedraw()
        maa1.setValuesAt(30)
        t3 = sph.translation[0]
        self.assertEqual(int(t3/2), int(t2))
        vi.OneRedraw()

        # direction: right
        sph.Set(translation=[0,0,0])
        maa2 = FlyOutObjectMAA(sph, objectName=None, direction='right', kfpos=[0, 60])
        actors = maa2.actors
        self.assertEqual(len(actors), 3)
        vi.OneRedraw()
        sph.Set(translation=[5,5,5])
        # check that the position (translation) of the object changes from center to right side
        # of the viewer at frames 0 - 30 - 60
        maa2.setValuesAt(0)
        t1 = sph.translation
        vi.OneRedraw()
        self.assertEqual([t1[0], t1[1], t1[2]] , [0, 0, 0])
        
        maa2.setValuesAt(30)
        t2 = sph.translation[0]
        self.assertEqual(t2 > 0, True)
        vi.OneRedraw()
        maa2.setValuesAt(60)
        t3 = sph.translation[0]
        self.assertEqual(int(t3/2), int(t2))
        vi.OneRedraw()

        # direction: top
        sph.Set(translation=[0,0,0])
        maa3 = FlyOutObjectMAA(sph, objectName=None, direction='top', kfpos=[0, 30])
        actors = maa3.actors
        self.assertEqual (len(actors), 3)
        vi.OneRedraw()
        sph.Set(translation=[-5,5,5])                  

        # check that the position (translation) of the object changes from center to top side
        # of the viewer at frames 0 - 15 - 30
        maa3.setValuesAt(0)
        t1 = sph.translation
        vi.OneRedraw()
        self.assertEqual([t1[0], t1[1], t1[2]] , [0, 0, 0])
        maa3.setValuesAt(15)
        t2 = sph.translation[1]
        self.assertEqual(t2 > 0, True)
        vi.OneRedraw()
        maa3.setValuesAt(30)
        t3 = sph.translation[1]
        self.assertEqual(int(t3/2), int(t2))
        vi.OneRedraw()

        # direction: bottom
        sph.Set(translation=[0,0,0])
        maa4 = FlyOutObjectMAA(sph, objectName=None, direction='bottom', kfpos=[0, 60])
        actors = maa4.actors
        self.assertEqual (len(actors), 3)
        sph.Set(visible = 0)
        vi.OneRedraw()
        sph.Set(translation=[5,5,5])
        # check that the position (translation) of the object changes from center to top side
        # of the viewer at frames 0 - 30 - 60
        maa4.setValuesAt(0)
        t1 = sph.translation
        vi.OneRedraw()
        self.assertEqual([t1[0], t1[1], t1[2]] , [0, 0, 0])
        # check that the "visible" maa's actor sets the sph.visible attribute to 1
        self.assertEqual(sph.visible, 1)
        maa4.setValuesAt(30)
        t2 = sph.translation[1]
        self.assertEqual(t2 < 0, True)
        vi.OneRedraw()
        maa4.setValuesAt(60)
        t3 = sph.translation[1]
        self.assertEqual(int(t3/2), int(t2))
        vi.OneRedraw()
        #run maas
        maa1.run()
        maa2.run()
        maa3.run()
        self.assertEqual(sph.visible, 1)
        maa4.run()

        #check we can reproduce the maa from it's sourcecode:
        maa5 = None
        maasrc = maa4.getSourceCode("maa5")
        viewer = vi
        exec(maasrc)
        assert maa5 != None
        self.assertEqual (len(maa5.actors), 3)
        sph.Set(translation=[5,5,5])
        vi.OneRedraw()
        # check that the position (translation) of the object changes from center to top side
        # of the viewer at frames 0 - 30 - 60
##         maa5.setValuesAt(0)
##         t1 = sph.translation
##         vi.OneRedraw()
##         self.assertEqual([t1[0], t1[1], t1[2]] , [0, 0, 0])
##         # check that the "visible" maa's actor sets the sph.visible attribute to 1
##         self.assertEqual(sph.visible, 1)
##         maa5.setValuesAt(30)
##         t2 = sph.translation[1]
##         self.assertEqual(t2 < 0, True)
##         vi.OneRedraw()
##         maa5.setValuesAt(60)
##         t3 = sph.translation[1]
##         self.assertEqual(int(t3/2), int(t2))
        maa5.run()
        
    def check_fadevals(self, maa, obj, vi):
        # check that the opacity  of the object changes from 0 to 1 
        # at frames 0 - 15 - 30
        maa.setValuesAt(0)
        val1 = obj.materials[1028].prop[propertyNum['opacity']]
        self.assertEqual(len(val1), 1)
        self.assertEqual (val1[0] , 0)
        self.assertEqual(obj.visible, 1)
        vi.OneRedraw()
        maa.setValuesAt(15)
        val2 = obj.materials[1028].prop[propertyNum['opacity']]
        self.assertEqual(len(val1), 1)
        self.assertEqual (val2[0] , 0.5)
        vi.OneRedraw()
        maa.setValuesAt(30)
        val3 = obj.materials[1028].prop[propertyNum['opacity']]
        self.assertEqual(len(val1), 1)
        self.assertEqual(val3[0], 1)
        vi.OneRedraw()

    def test_fadein(self):
        """Test creation of FadeInObjectMAA and playing different frames of maa ."""

        vi = viewer = self.vi
        sph = Spheres( 'sph', centers=[ (0,0,0), (5, 0,0), (0,5,0), (0, 0,5) ],
                       materials = [ (1,1,1),  (1,0,0),  (0,1,0),  (0,0,1) ],
                       inheritMaterial=False) 
        viewer.AddObject(sph)

        from DejaVu.scenarioInterface.animations import FadeInObjectMAA
        maa1 = FadeInObjectMAA(sph, objectName=None, kfpos=[0, 30])
        #check we can reproduce the maa from it's sourcecode:
        maa2 =  None
        maasrc = maa1.getSourceCode("maa2")
        #viewer = vi
        exec(maasrc)
        assert maa2 != None
        sph.Set(visible = 0)
        for maa in [maa1, maa2]:
            actors = maa.actors
            self.assertEqual (len(actors), 3)
            viewer.OneRedraw()
            # check that the opacity  of the object changes from 0 to 1 
            # at frames 0 - 15 - 30
            maa.setValuesAt(0)
            val1 = sph.materials[1028].prop[propertyNum['opacity']]
            self.assertEqual(len(val1), 1)
            self.assertEqual (val1[0] , 0)
            self.assertEqual(sph.visible, 1)
            vi.OneRedraw()
            maa.setValuesAt(15)
            val2 = sph.materials[1028].prop[propertyNum['opacity']]
            self.assertEqual(len(val1), 1)
            self.assertEqual (val2[0] , 0.5)
            vi.OneRedraw()
            maa.setValuesAt(30)
            val3 = sph.materials[1028].prop[propertyNum['opacity']]
            self.assertEqual(len(val1), 1)
            self.assertEqual(val3[0], 1)
            vi.OneRedraw()
            # run maa
            maa.run()
        

    def test_fadeout(self):
        """Test creation of FadeInObjectMAA and playing different frames of maa ."""

        vi = self.vi
        sph = Spheres( 'sph', centers=[ (0,0,0), (5, 0,0), (0,5,0), (0, 0,5) ],
                       materials = [ (1,1,1),  (1,0,0),  (0,1,0),  (0,0,1) ],
                       inheritMaterial=False) 
        vi.AddObject(sph)
        sph.Set(opacity = 0.8)
        from DejaVu.scenarioInterface.animations import FadeOutObjectMAA
        #from DejaVu.Materials import propertyNum

        # create an instance of FadeOutObjectMAA object 
        maa1 = FadeOutObjectMAA(sph, objectName=None, kfpos=[0, 60])

        #check we can reproduce the maa from it's sourcecode:
        maa2 =  None
        maasrc = maa1.getSourceCode("maa2")
        viewer = vi
        print maasrc
        exec(maasrc)
        
        assert maa2 != None

        # check the maas
        for maa in [maa1,  maa2]:
            actors = maa.actors
            self.assertEqual (len(actors), 3)
            vi.OneRedraw()

            # check that the opacity  of the object changes from 0 to 1 
            # at frames 0 - 30 - 60
            maa.setValuesAt(0)
            val1 = sph.materials[1028].prop[propertyNum['opacity']]
            self.assertEqual(len(val1), 1)
            self.assertEqual ("%.2f"%val1[0] , "0.80")
            vi.OneRedraw()
            maa.setValuesAt(30)
            val2 = sph.materials[1028].prop[propertyNum['opacity']]
            self.assertEqual(len(val1), 1)
            self.assertEqual ("%.2f"%val2[0] , "0.40")
            vi.OneRedraw()
            maa.setValuesAt(60)
            val3 = sph.materials[1028].prop[propertyNum['opacity']]
            self.assertEqual(len(val1), 1)
            self.assertEqual(val3[0], 0)
            vi.OneRedraw()
            maa.run()
            maa.afterAnimation_cb()
            # check that the last maa's afterAnimation method sets the opacity 
            # to it's original value
            val = sph.materials[1028].prop[propertyNum['opacity']][0]
            self.assertEqual("%.2f"%val, "0.80")

            

    def test_partialFade(self):
        """Test creation of PartialFadeMAA, and playing different frames of maa ."""
        
        vi = self.vi
        sph = Spheres( 'sph', centers=[ (0,0,0), (5, 0,0), (0,5,0), (0, 0,5) ],
                       materials = [ (1,1,1),  (1,0,0),  (0,1,0),  (0,0,1) ],
                       inheritMaterial=False) 
        vi.AddObject(sph)
        
        from DejaVu.scenarioInterface.animations import PartialFadeMAA
        #from DejaVu.Materials import propertyNum
        import numpy
        
        initVal = {sph: [0.80, 1.0, 0.80, 1.0]}
        finalVal = {sph: numpy.array([0.0,1.0, 0.0, 1.0], 'f')}
        
        maa1 = PartialFadeMAA(sph, initVal, finalVal,  kfpos=[0, 100])
        #check we can reproduce the maa from it's sourcecode:
        maa2 =  None
        maasrc = maa1.getSourceCode("maa2")
        viewer = vi
        exec(maasrc)
        assert maa2 != None
        sph.Set(visible = 0)
        for maa in [maa1, maa2]:
            actors = maa.actors
            self.assertEqual (len(actors), 3)
            # test that the opacity of the object is changing from initVal to finalVal when maa is set to frames 0 - 50 -100
            maa.setValuesAt(0)
            self.assertEqual(sph.visible , 1)
            val =  sph.materials[1028].prop[1][:,3]
            #print "val:" , val
            testval = numpy.array(initVal[sph], "f")
            self.assertEqual(numpy.alltrue(numpy.equal(val, testval)), True)
            vi.OneRedraw()

            maa.setValuesAt(50)
            val =  sph.materials[1028].prop[1][:,3]
            #print "val:" , val
            testval = numpy.array([0.40, 1., 0.40, 1.], "f")
            self.assertEqual(numpy.alltrue(numpy.equal(val, testval)), True)
            vi.OneRedraw()

            maa.setValuesAt(100)
            val =  sph.materials[1028].prop[1][:,3]
            testval = numpy.array(finalVal[sph], "f")
            self.assertEqual(numpy.alltrue(numpy.equal(val, testval)), True)
            #print "val:" , val
            vi.OneRedraw()

            maa.run()
            maa.afterAnimation_cb()
            #check that the afterAnimation method sets the opacity attribute
            # of the object  to its original value
            val =  sph.materials[1028].prop[1][:,3]
            #print "val:" , val
            testval = numpy.array([1., 1., 1., 1.], "f")
            self.assertEqual(numpy.alltrue(numpy.equal(val, testval)), True)



    def test_visible(self):
        """Test creation of VisibleObjectMAA """
        vi = self.vi
        sph = Spheres( 'sph', centers=[ (0,0,0), (5, 0,0), (0,5,0), (0, 0,5) ],
                       materials = [ (1,1,1),  (1,0,0),  (0,1,0),  (0,0,1) ],
                       inheritMaterial=False) 
        vi.AddObject(sph)
        
        from DejaVu.scenarioInterface.animations import VisibleObjectMAA
        # create maa that sets "visible" attribute of the object to False
        maa1 = VisibleObjectMAA(sph, visible=0)
        self.assertEqual (len(maa1.actors), 2)
        maa1.setValuesAt(0)
        self.assertEqual(sph.visible , 0)

        maa1.run()
        maa1.afterAnimation_cb()
        # afterAnimation_cb() should set the attribute to it's original value
        self.assertEqual(sph.visible , 1)
        
        # create maa that sets "visible" attribute of the object to True
        maa2 = VisibleObjectMAA(sph, visible=1)

        #check we can reproduce the maa from it's sourcecode:
        maa3 =  None
        maasrc = maa2.getSourceCode("maa3")
        viewer = vi
        exec(maasrc)
        assert maa3 != None
        for maa in [maa2, maa3]:
            self.assertEqual (len(maa.actors), 2)
            sph.Set(visible = 0)
            maa.setValuesAt(0)
            self.assertEqual(sph.visible , 1)
            maa.run()


    def test_colors(self):
        """Test creation of ColorObjectMAA and setting the maa to different frames """

        vi = self.vi
        sph = Spheres( 'sph', centers=[ (0,0,0), (5, 0,0), (0,5,0), (0, 0,5) ],
                       materials = [ (1,1,1),  (1,1,1),  (1,1,1),  (1,1,1) ],
                       inheritMaterial=False)
        lines = IndexedPolylines('lines' ,materials=((0,1,0),), 
                        vertices=((0,0,0), (5, 0,0), (0,5,0), (0, 0,5)), faces=((0,1),(1,2),(2,3),(3,0)),
                                 inheritMaterial = False)
        vi.AddObject(sph)
        vi.AddObject(lines)
        from DejaVu.scenarioInterface.animations import ColorObjectMAA
        import numpy
        initColors =  {sph: [ (1,1,1),  (1,1,1),  (1,1,1),  (1,1,1)], lines: [(0,1,0),]}
        finalColors = {sph: [ (1,0,1),  (0,0,1),  (1,0,0),  (0,1,0) ], lines: [(1,0,0)]}
        root = vi.rootObject
        lines.Set(visible = 0 )
##         maa =  ColorObjectMAA(sph, initColors[sph], finalColors[sph], nbFrames = 200)
##         maa1 = ColorObjectMAA(lines, initColors[lines], finalColors[lines], nbFrames = 200)
##         maa.addMultipleActorsActionsAt(maa1)
        
        maa1 =  ColorObjectMAA([sph, lines], initColors, finalColors, nbFrames = 200)
        #check we can reproduce the maa from it's sourcecode:
        maa2 =  None
        maasrc = maa1.getSourceCode("maa2")
        viewer = vi
        exec(maasrc)
        assert maa2 != None
        for maa in [maa1, maa2]:
            self.assertEqual(len(maa.actors), 5)
            self.assertEqual(len(maa.origValues), 4)
            maa.setValuesAt(0)
            val1 = sph.materials[1028].prop[1][:, :3]
            #print "1:", val1
            val2 = lines.materials[1028].prop[1][:, :3]
            #print "2", val2
            vi.OneRedraw()
            self.assertEqual(numpy.alltrue(numpy.equal(val1, numpy.array(initColors[sph], "f"))), True)
            self.assertEqual(numpy.alltrue(numpy.equal(val2, numpy.array(initColors[lines], "f"))), True)
            self.assertEqual(lines.visible , 1)
            maa.setValuesAt(100)
            val1 = sph.materials[1028].prop[1][:, :3]
            testval1 = numpy.array([[ 1., 0.5, 1. ], [0.5,0.5, 1.], [1., 0.5, 0.5], [0.5, 1., 0.5]],'f')
            #print "1:", val1
            val2 = lines.materials[1028].prop[1][:, :3]
            #print "2:", val2
            testval2 = numpy.array([[ 0.5, 0.5,  0. ]],'f')
            vi.OneRedraw()
            self.assertEqual(numpy.alltrue(numpy.equal(val1, testval1)), True)
            self.assertEqual(numpy.alltrue(numpy.equal(val2, testval2)), True)

            maa.setValuesAt(200)
            val1 = sph.materials[1028].prop[1][:, :3]
            #print "1:", val1
            val2 = lines.materials[1028].prop[1][:, :3]
            #print "2:", val2
            vi.OneRedraw()
            self.assertEqual(numpy.alltrue(numpy.equal(val1, numpy.array(finalColors[sph], "f"))), True)
            self.assertEqual(numpy.alltrue(numpy.equal(val2, numpy.array(finalColors[lines], "f"))), True)

            sph.Set(materials = [ (0,0,1),  (0.5,0,1),  (0,0,1),  (05,1,1)], inheritMaterial = 0)
            lines.Set(materials = [ (1,1,1),], inheritMaterial = 0)

            # check that the original values are set to the geometries after the maa run.
            maa.run()
            maa.afterAnimation_cb()
            val1 = sph.materials[1028].prop[1][:, :3]
            val2 = lines.materials[1028].prop[1][:, :3]
            self.assertEqual(numpy.alltrue(numpy.equal(val1, numpy.array(initColors[sph], "f"))), True)
            self.assertEqual(numpy.alltrue(numpy.equal(val2, numpy.array(initColors[lines], "f"))), True)
            self.assertEqual(lines.visible , 0)
            vi.OneRedraw()


    def test_rotationMAA(self):
        
        from DejaVu.scenarioInterface.animations import RotationMAA
        import numpy
        vi = self.vi
        sph = Spheres( 'sph', centers=[ (0,0,0), (5, 0,0), (0,5,0), (0, 0,5) ],
                       materials = [ (1,1,1),  (1,1,1),  (1,1,1),  (1,1,1) ],
                       inheritMaterial=False)

        vi.AddObject(sph)
        root = vi.rootObject
        origRot = root.rotation.copy()
        maa1 = RotationMAA(root, angle = 120, nbFrames= 90 )
        maa2 =  None
        maasrc = maa1.getSourceCode("maa2")
        viewer = vi
        exec(maasrc)
        assert maa2 != None
        for maa in [maa1, maa2]:
            for i in range(30):
                maa.setValuesAt(i)
                vi.OneRedraw()
            rots = [origRot, root.rotation.copy()]
            assert  numpy.alltrue(numpy.equal(rots[0], rots[1])) == False

            for i in range(30, 60):
                maa.setValuesAt(i)
                vi.OneRedraw()
            for rr in rots:
                assert  numpy.alltrue(numpy.equal(rr, root.rotation)) == False
            rots.append(root.rotation.copy())

            for i in range(60, 90):
                maa.setValuesAt(i)
                vi.OneRedraw()
            for rr in rots:
                assert  numpy.alltrue(numpy.equal(rr, root.rotation)) == False
            # check that afterAnimation() sets the object to it's orig. value
            maa.run()
            #assert  numpy.alltrue(numpy.equal(origRot, root.rotation)) == True
            #print "rotation after run", root.rotation

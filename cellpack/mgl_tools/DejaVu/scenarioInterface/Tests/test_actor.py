## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by

###############################################################################
##
##
## Author: Sowjanya Karnati
##
##
###############################################################################

# $Id: test_actor.py,v 1.4 2009/03/11 21:46:56 annao Exp $

# Contents Tested
# ActionWithRedraw
# RedrawActor
# DejaVuActor
# DejaVuFogActor
# DejaVuClipZActor
# DejaVuScissorActor
# DejaVuSpheresRadiiActor
# getDejaVuActor

import unittest
from DejaVu.scenarioInterface.actor import *
from Scenario2.interpolators import *
from Scenario2.actor import *
from DejaVu.Viewer import Viewer
from DejaVu.Spheres import Spheres
from Scenario2.director import *
from DejaVu.IndexedPolylines import IndexedPolylines
from numpy.oldnumeric import array


class ActionWithRedrawBaseTest(unittest.TestCase):
    def test_action_defaultargs(self):
        """testing Action with default args"""
        myaction = ActionWithRedraw()
        self.assertEqual(myaction.startFrame, None)
        self.assertEqual(myaction.endFrame, None)
        self.assertEqual(myaction.interpolator, None)
        self.assertEqual(myaction.isFullRange(), True)
        self.assertEqual(myaction.getFirstFrame(), 0)
        self.assertEqual(myaction.preStep_cb, None)
        self.assertEqual(str(myaction.postStep_cb) != None, True)

    def test_action_with_args(self):
        """testing Action with args"""
        myaction = ActionWithRedraw(
            startFrame=0, endFrame=2, interpolator=KeyFrameInterpolator([10, 20])
        )
        self.assertEqual(myaction.startFrame, 0)
        self.assertEqual(myaction.endFrame, 2)
        self.assertEqual(isinstance(myaction.interpolator, KeyFrameInterpolator), True)
        self.assertEqual(myaction.isFullRange(), False)
        self.assertEqual(myaction.getFirstFrame(), 0)
        self.assertEqual(myaction.preStep_cb, None)
        self.assertEqual(str(myaction.postStep_cb) != None, True)

    # RedrawActorBaseTest(unittest.TestCase):
    def test_RedrawActor_1(self):
        """testing calling RedrawActor"""
        vi = Viewer()
        myactor = RedrawActor(vi)
        self.assertEqual(myactor.name, "redraw")
        self.assertEqual(myactor.object, vi)
        self.assertEqual(len(myactor.actions), 1)
        self.assertEqual(isinstance(myactor.actions[0], Action), True)
        vi.Exit()


class DejaVuActorBaseTest(unittest.TestCase):
    # DejaVuActor
    def test_DejaVuActor_1(self):
        """tests interpolating radii ,calling DejaVuActor with args setName and getName"""
        vi = Viewer()
        sph = Spheres(
            "spheres",
            vertices=((0, 0, 0), (5.0, 0.0, 0.0)),
            materials=((0.5, 0, 0),),
            radii=2.0,
            quality=30,
        )
        vi.AddObject(sph)
        mydirector = Director()
        # RedrawActor
        myactor1 = RedrawActor(vi)
        mydirector.addActor(myactor1)
        # DejaVuActor
        myactor = DejaVuActor("radii", sph, setName="radii", getName="radius")
        myaction = ActionWithRedraw(
            startFrame=0, endFrame=20, interpolator=KeyFrameInterpFloat((0.6, 3.5))
        )
        myactor.addAction(myaction)
        mydirector.addActor(myactor)
        mydirector.run()
        self.assertEqual(myactor.setName, "radii")
        self.assertEqual(myactor.getName, "radius")
        self.assertEqual(myactor.hasGetFunction, True)
        self.assertEqual(myactor.initialValue, 2.0)
        vi.Exit()

    def test_DejaVuActor_2(self):
        """tests interpolating quality calling DejaVuActor with args setName and getName"""
        vi = Viewer()
        sph = Spheres(
            "spheres",
            vertices=((0, 0, 0), (5.0, 0.0, 0.0)),
            materials=((0.5, 0, 0),),
            radii=2.0,
            quality=30,
        )
        vi.AddObject(sph)
        vi.update()
        mydirector = Director()
        # RedrawActor
        myactor1 = RedrawActor(vi)
        mydirector.addActor(myactor1)
        # DejaVuActor
        myactor = DejaVuActor("quality", sph, setName="quality", getName="stacks")
        myaction = ActionWithRedraw(
            startFrame=0, endFrame=20, interpolator=KeyFrameInterpFloat((10, 40))
        )
        myactor.addAction(myaction)
        mydirector.addActor(myactor)
        mydirector.run()
        self.assertEqual(myactor.setName, "quality")
        self.assertEqual(myactor.getName, "stacks")
        self.assertEqual(myactor.hasGetFunction, True)
        self.assertEqual(myactor.initialValue, 30)
        vi.Exit()

    def test_DejaVuActor_3(self):
        """tests interpolating scale"""
        vi = Viewer()
        sph = Spheres(
            "spheres",
            vertices=((0, 0, 0), (5.0, 0.0, 0.0)),
            materials=((0.5, 0, 0),),
            radii=2.0,
            quality=30,
        )
        vi.AddObject(sph)
        vi.update()
        mydirector = Director()
        # RedrawActor
        myactor1 = RedrawActor(vi)
        mydirector.addActor(myactor1)
        # DejaVuActor
        myactor = DejaVuActor("scale", sph)
        myaction = ActionWithRedraw(
            startFrame=0,
            endFrame=100,
            interpolator=ScaleInterpolator([(1.0, 1.0, 1.0), (5.0, 5.0, 5.0)]),
        )
        myactor.addAction(myaction)
        mydirector.addActor(myactor)
        mydirector.run()
        self.assertEqual(myactor.setName, "scale")
        self.assertEqual(myactor.getName, "scale")
        self.assertEqual(myactor.hasGetFunction, True)
        self.assertEqual(myactor.initialValue, [1.0, 1.0, 1.0])
        vi.Exit()

    def test_DejaVuActor_4(self):
        """tests interpolating rotation"""
        vi = Viewer()
        points = ((0, 0, 0), (5, 0, 0), (0, 5, 0))
        indices = ((0, 1), (0, 2))
        polylines = IndexedPolylines("box", vertices=points, faces=indices, visible=1)
        vi.AddObject(polylines)
        lines_set_rotation = lambda actor, value: actor.object.Set(rotation=value)
        start_mat = Numeric.identity(4, "f")
        z = [[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
        mat = array(z)
        s = Numeric.reshape(start_mat, (16,))
        e = Numeric.reshape(mat, (16,))
        mydirector = Director()
        # RedrawActor
        myactor1 = RedrawActor(vi)
        mydirector.addActor(myactor1)
        # DejaVuActor
        myactor = DejaVuActor("rotation", polylines)
        myaction = ActionWithRedraw(
            startFrame=0, endFrame=100, interpolator=RotationInterpolator(values=[s, e])
        )
        myactor.addAction(myaction)
        mydirector.addActor(myactor)
        mydirector.run()
        self.assertEqual(myactor.setName, "rotation")
        self.assertEqual(myactor.getName, "rotation")
        self.assertEqual(myactor.hasGetFunction, True)
        self.assertEqual(
            myactor.initialValue,
            array(
                [
                    1.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    1.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    1.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    1.0,
                ],
                "f",
            ),
        )
        vi.Exit()

    def test_DejaVuActor_translation(self):
        """tests interpolating translation"""
        mydirector = Director()
        vi = Viewer()
        sph = Spheres(
            "spheres",
            vertices=((0, 0, 0), (5.0, 0.0, 0.0)),
            materials=((0.5, 0, 0),),
            radii=2.0,
            quality=30,
            inheritLineWidth=0,
            inheritMaterial=False,
        )
        vi.AddObject(sph)
        # RedrawActor
        myactor1 = RedrawActor(vi)
        mydirector.addActor(myactor1)
        # DejaVuActor
        starts = Numeric.zeros(3, "f")
        ends = Numeric.array([1, 1, 1], "f")
        myactor = DejaVuActor("translation", sph)
        myaction = ActionWithRedraw(
            startFrame=0,
            endFrame=200,
            interpolator=TranslationInterpolator(values=[starts, ends]),
        )
        myactor.addAction(myaction)
        mydirector.addActor(myactor)
        mydirector.run()
        self.assertEqual(myactor.setName, "translation")
        self.assertEqual(myactor.getName, "translation")
        self.assertEqual(myactor.hasGetFunction, True)
        self.assertEqual(myactor.initialValue, [0.0, 0.0, 0.0])
        vi.Exit()

    def test_DejaVuActor_pivot(self):
        """tests interpolating pivot"""
        mydirector = Director()
        vi = Viewer()
        sph = Spheres(
            "spheres",
            vertices=((0, 0, 0), (5.0, 0.0, 0.0)),
            materials=((0.5, 0, 0),),
            radii=2.0,
            quality=30,
            inheritLineWidth=0,
            inheritMaterial=False,
        )
        vi.AddObject(sph)
        # RedrawActor
        myactor1 = RedrawActor(vi)
        mydirector.addActor(myactor1)
        # DejaVuActor
        starts = Numeric.zeros(3, "f")
        ends = Numeric.array([1, 1, 1], "f")
        myactor = DejaVuActor("pivot", sph)
        myaction = ActionWithRedraw(
            startFrame=0,
            endFrame=200,
            interpolator=TranslationInterpolator(values=[starts, ends]),
        )
        myactor.addAction(myaction)
        mydirector.addActor(myactor)
        mydirector.run()
        self.assertEqual(myactor.setName, "pivot")
        self.assertEqual(myactor.getName, "pivot")
        self.assertEqual(myactor.hasGetFunction, True)
        self.assertEqual(myactor.initialValue, [0.0, 0.0, 0.0])
        vi.Exit()


class DejaVuFogActorBaseTest(unittest.TestCase):
    def test_DejaVuFogActor_1(self):
        """tests calling DejaVuFogActor"""
        mydirector = Director()
        vi = Viewer()
        sph = Spheres(
            "spheres",
            vertices=((0, 0, 0), (5.0, 0.0, 0.0)),
            materials=((0.5, 0, 0),),
            radii=2.0,
            quality=30,
            inheritLineWidth=0,
            inheritMaterial=False,
        )
        vi.AddObject(sph)
        # RedrawActor
        myactor1 = RedrawActor(vi)
        mydirector.addActor(myactor1)
        # DejaVuFogActor
        myactor = DejaVuFogActor("fog", vi.currentCamera)
        myaction = ActionWithRedraw(
            startFrame=0,
            endFrame=10,
            interpolator=SequenceLinearInterpolator([[0.1, 50.0], [45.0, 50.0]]),
        )
        myactor.addAction(myaction)
        mydirector.addActor(myactor)
        mydirector.run()
        vi.Exit()


class DejaVuClipZActorBaseTest(unittest.TestCase):
    def test_DejaVuClipZActor_1(self):
        """tests calling DejaVuClipZActor"""
        mydirector = Director()
        vi = Viewer()
        sph = Spheres(
            "spheres",
            vertices=((0, 0, 0), (5.0, 0.0, 0.0)),
            materials=((0.5, 0, 0),),
            radii=2.0,
            quality=30,
            inheritLineWidth=0,
            inheritMaterial=False,
        )
        vi.AddObject(sph)
        # RedrawActor
        myactor1 = RedrawActor(vi)
        mydirector.addActor(myactor1)
        # DejaVuClipZActor
        myactor = DejaVuClipZActor("clipZ", vi.currentCamera)
        myaction = ActionWithRedraw(
            startFrame=0,
            endFrame=10,
            interpolator=SequenceLinearInterpolator([[0.1, 50.0], [45.0, 50.0]]),
        )
        myactor.addAction(myaction)
        mydirector.addActor(myactor)
        mydirector.run()
        vi.Exit()


class DejaVuSperesRadiiActorBaseTest(unittest.TestCase):
    def test_DejaVuSperesRadiiActor_1(self):
        """tests calling DejaVuSperesRadiiActor"""
        mydirector = Director()
        vi = Viewer()
        sph = Spheres(
            "spheres",
            vertices=((0, 0, 0), (5.0, 0.0, 0.0)),
            materials=((0.5, 0, 0),),
            radii=2.0,
            quality=30,
            inheritLineWidth=0,
            inheritMaterial=False,
        )
        vi.AddObject(sph)
        # RedrawActor
        myactor1 = RedrawActor(vi)
        mydirector.addActor(myactor1)
        # DejaVuSperesRadiiActor
        vi.update()
        myactor = DejaVuSperesRadiiActor("radii", sph)
        myaction = ActionWithRedraw(
            startFrame=0,
            endFrame=200,
            interpolator=listNFloatInterpolator([[1.0, 4.0], [4.0, 1.0]]),
        )
        myactor.addAction(myaction)
        mydirector.addActor(myactor)
        mydirector.run()
        vi.Exit()


class DejaVuScissorActorBaseTest(unittest.TestCase):
    def test_DejaVuScissorActor_1(self):
        """tests calling DejaVuScissorActor"""
        mydirector = Director()
        vi = Viewer()
        sph = Spheres(
            "spheres",
            vertices=((0, 0, 0), (5.0, 0.0, 0.0)),
            materials=((0.5, 0, 0),),
            radii=2.0,
            quality=30,
            inheritLineWidth=0,
            inheritMaterial=False,
        )
        vi.AddObject(sph)
        sph.Set(scissor=1)
        # RedrawActor
        myactor1 = RedrawActor(vi)
        mydirector.addActor(myactor1)
        # DejaVuScissorActor
        myactor = DejaVuScissorActor("scissor", sph)
        myaction = ActionWithRedraw(
            startFrame=0,
            endFrame=200,
            interpolator=KeyFrameInterp4Float(
                [[2.0, 3.0, 4.0, 5.0], [120.0, 130.0, 140.0, 150.0]]
            ),
        )
        myactor.addAction(myaction)
        mydirector.addActor(myactor)
        mydirector.run()
        self.assertEqual(sph.getState()["scissorH"], 120.0)
        self.assertEqual(sph.getState()["scissorW"], 130.0)
        self.assertEqual(sph.getState()["scissorX"], 140.0)
        self.assertEqual(sph.getState()["scissorY"], 150.0)
        vi.Exit()

    # getDejaVuActor
    def test_getDejaVuActor_1(self):
        """tests calling getDejaVuActor"""
        mydirector = Director()
        vi = Viewer()
        sph = Spheres(
            "spheres",
            vertices=((0, 0, 0), (5.0, 0.0, 0.0)),
            materials=((0.5, 0, 0),),
            radii=2.0,
            quality=30,
            inheritLineWidth=0,
            inheritMaterial=False,
        )
        vi.AddObject(sph)
        # RedrawActor
        myactor1 = RedrawActor(vi)
        mydirector.addActor(myactor1)
        # DejaVuScissorActor
        myactor = getDejaVuActor(sph, "radii")
        myaction = ActionWithRedraw(
            startFrame=0,
            endFrame=200,
            interpolator=listNFloatInterpolator([[1.0, 1.0], [4.0, 4.0], [1.0, 1.0]]),
        )
        myactor.addAction(myaction)
        mydirector.addActor(myactor)
        mydirector.run()
        vi.Exit()


if __name__ == "__main__":
    unittest.main()

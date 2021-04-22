#
#
#  $Id: test_Fog.py,v 1.6 2005/12/08 20:34:15 annao Exp $
#
#

import unittest
from opengltk.OpenGL import GL
from DejaVu import Viewer


class Fog_BaseTests(unittest.TestCase):
    """
    setUp + tearDown form a fixture: working environment for the testing code
    """

    def setUp(self):
        """
        start Viewer
        """
        if not hasattr(self, "vi"):
            self.vi = Viewer(verbose=False)
            # self.vi.cameras[0].master.master.withdraw()
            self.fog = self.vi.currentCamera.fog
            self.orig_state = self.fog.getState()

    def tearDown(self):
        """
        clean-up
        """
        # print 'in fog tearDown'
        # apply(self.fog.Set, (), self.orig_state)
        try:
            self.vi.Exit()
        except:
            pass
        # self.vi.__del__()

    def test_SetColor_attr(self):
        """Set color changes fog's color attribute"""
        self.fog.Set(color=(1, 0, 0))
        col = self.fog.color
        self.assertEqual(col[0], 1.0)
        self.assertEqual(col[1], 0.0)
        self.assertEqual(col[2], 0.0)

    def test_SetColor_GL(self):
        """Set color changes GL_FOG_COLOR"""
        self.fog.Set(color=(1, 0, 0))
        col = GL.glGetFloat(GL.GL_FOG_COLOR)
        self.assertEqual(col[0], 1.0)
        self.assertEqual(col[1], 0.0)
        self.assertEqual(col[2], 0.0)

    def test_SetColor_state(self):
        """Set color changes fog's state['color']"""
        self.fog.Set(color=(1, 0, 0))
        state = self.fog.getState()
        col = state["color"]
        self.assertEqual(col[0], 1.0)
        self.assertEqual(col[1], 0.0)
        self.assertEqual(col[2], 0.0)

    def test_SetColor_bad_input(self):
        """ValueError raised on bad input to Set color"""
        self.assertRaises(ValueError, self.fog.Set, color=(1, 0))

    def test_SetColor_empty_input(self):
        """ValueError raised on empty input to Set color"""
        self.assertRaises(ValueError, self.fog.Set, color=())

    def test_SetColor_too_much_input(self):
        """ValueError raised on too_much input to Set color"""
        self.assertRaises(ValueError, self.fog.Set, color=(1, 0, 0, 1, 1))

    def test_SetStart_attr(self):
        """Set start changes fog's start attribute"""
        val = 15
        self.fog.Set(start=val)
        self.assertEqual(self.fog.start, val)

    def test_SetStart_GL(self):
        """Set start changes GL_FOG_START"""
        val = 15
        self.fog.Set(start=val)
        start = GL.glGetFloat(GL.GL_FOG_START)
        self.assertEqual(start, val)

    def test_SetStart_state(self):
        """Set start changes fog's state['start']"""
        val = 15
        self.fog.Set(start=val)
        state = self.fog.getState()
        start = state["start"]
        self.assertEqual(start, val)

    def test_SetStart_bad_input(self):
        """ValueError raised on bad input to Set start"""
        self.assertRaises(AttributeError, self.fog.Set, start=100)

    def test_SetStart_empty_input(self):
        """ValueError raised on empty input to Set start"""
        self.assertRaises(AttributeError, self.fog.Set, start="")

    def test_SetStart_too_much_input(self):
        """ValueError raised on too_much input to Set start"""
        self.assertRaises(AttributeError, self.fog.Set, start=[1.0, 2.0, 3.0, 4.0])

    def test_SetEnd_attr(self):
        """Set end changes fog's end attribute"""
        val = 30
        self.fog.Set(end=val)
        self.assertEqual(self.fog.end, val)

    def test_SetEnd_GL(self):
        """Set end changes GL_FOG_END"""
        val = 30
        self.fog.Set(end=val)
        end = GL.glGetFloat(GL.GL_FOG_END)
        self.assertEqual(end, val)

    def test_SetEnd_state(self):
        """Set end changes fog's state['end']"""
        val = 30
        self.fog.Set(end=val)
        state = self.fog.getState()
        end = state["end"]
        self.assertEqual(end, val)

    def xtest_SetEnd_bad_input(self):
        """ValueError raised on bad input to Set end"""
        self.assertRaises(AttributeError, self.fog.Set, end=10)

    def xtest_SetEnd_empty_input(self):
        """ValueError raised on empty input to Set end"""
        self.assertRaises(AttributeError, self.fog.Set, end="")

    def xtest_SetEnd_too_much_input(self):
        """ValueError raised on too_much input to Set end"""
        self.assertRaises(AttributeError, self.fog.Set, end=[1.0, 2.0, 3.0, 4.0])

    def test_SetDensity_attr(self):
        """Set density changes fog's density attribute"""
        val = 0.5
        self.fog.Set(density=val)
        self.assertEqual(self.fog.density, val)

    def test_SetDensity_GL(self):
        """Set density changes GL_FOG_DENSITY"""
        val = 0.5
        self.fog.Set(density=val)
        density = GL.glGetFloat(GL.GL_FOG_DENSITY)
        self.assertEqual(density, val)

    def test_SetDensity_state(self):
        """Set density changes fog's state['density']"""
        val = 0.5
        self.fog.Set(density=val)
        state = self.fog.getState()
        density = state["density"]
        self.assertEqual(density, val)

    def test_SetDensity_bad_input(self):
        """AttributeError raised on bad input to Set density"""
        self.assertRaises(AttributeError, self.fog.Set, density=10)

    def test_SetDensity_empty_input(self):
        """AttributeError raised on empty input to Set density"""
        self.assertRaises(AttributeError, self.fog.Set, density="")

    def test_SetDensity_too_much_input(self):
        """AttributeError raised on too_much input to Set density"""
        self.assertRaises(AttributeError, self.fog.Set, density=[1.0, 2.0, 3.0, 4.0])

    # MODE
    # GL_EXP
    def test_EXP_SetMode_attr(self):
        """Set mode GL_EXP changes fog's mode attribute"""
        val = GL.GL_EXP
        self.fog.Set(mode=val)
        self.assertEqual(self.fog.mode, val)

    def test_EXP_SetMode_GL(self):
        """Set mode GL_EXP changes GL_FOG_MODE"""
        val = GL.GL_EXP
        self.fog.Set(mode=val)
        mode = GL.glGetInteger(GL.GL_FOG_MODE)
        self.assertEqual(mode, val)

    def test_EXP_SetMode_state(self):
        """ Set mode GL_EXP changes fog's state['mode']
======================================================================
FAIL: Set mode changes fog's state['mode']
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test_Fog.py", line 261, in test_EXP_SetMode_state
    self.assertEqual(mode, val)
  File "/mgl/python/share//lib/python2.3/unittest.py", line 302, in failUnlessEqual
    raise self.failureException, \
AssertionError: 'GL_EXP' != 2048
        """
        val = GL.GL_EXP
        self.fog.Set(mode=val)
        state = self.fog.getState()
        mode = state["mode"]
        self.assertEqual(mode, "GL_EXP")

    # GL_EXP2
    def test_EXP2_SetMode_attr(self):
        """Set mode GL_EXP2 changes fog's mode attribute"""
        val = GL.GL_EXP2
        self.fog.Set(mode=val)
        self.assertEqual(self.fog.mode, val)

    def test_EXP2_SetMode_GL(self):
        """Set mode GL_EXP2 changes GL_FOG_MODE"""
        val = GL.GL_EXP2
        self.fog.Set(mode=val)
        mode = GL.glGetInteger(GL.GL_FOG_MODE)
        self.assertEqual(mode, val)

    def test_EXP2_SetMode_state(self):
        """ Set mode GL_EXP2 changes fog's state['mode']
======================================================================
FAIL: Set mode changes fog's state['mode']
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test_Fog.py", line 288, in test_EXP2_SetMode_state
    self.assertEqual(mode, val)
  File "/mgl/python/share//lib/python2.3/unittest.py", line 302, in failUnlessEqual
    raise self.failureException, \
AssertionError: 'GL_EXP2' != 2049
        """
        val = GL.GL_EXP2
        self.fog.Set(mode=val)
        state = self.fog.getState()
        mode = state["mode"]
        self.assertEqual(mode, "GL_EXP2")

    # GL_LINEAR
    def test_LINEAR_SetMode_attr(self):
        """Set mode GL_LINEAR changes fog's mode attribute"""
        val = GL.GL_LINEAR
        self.fog.Set(mode=val)
        self.assertEqual(self.fog.mode, val)

    def test_LINEAR_SetMode_GL(self):
        """Set mode GL_LINEAR changes GL_FOG_MODE"""
        val = GL.GL_LINEAR
        self.fog.Set(mode=val)
        mode = GL.glGetInteger(GL.GL_FOG_MODE)
        self.assertEqual(mode, val)

    def test_LINEAR_SetMode_state(self):
        """ Set mode GL_LINEAR changes fog's state['mode']
======================================================================
NB: all of these could be a bit better
FAIL: Set mode changes fog's state['mode']
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test_Fog.py", line 316, in test_LINEAR_SetMode_state
    self.assertEqual(mode, val)
  File "/mgl/python/share//lib/python2.3/unittest.py", line 302, in failUnlessEqual
    raise self.failureException, \
AssertionError: 'GL_LINEAR' != 9729

        """
        val = GL.GL_LINEAR
        self.fog.Set(mode=val)
        state = self.fog.getState()
        mode = state["mode"]
        self.assertEqual(mode, "GL_LINEAR")

    def test_SetMode_bad_input(self):
        """AttributeError raised on bad input to Set mode"""
        self.assertRaises(AttributeError, self.fog.Set, mode="INVALID")

    def test_SetMode_empty_input(self):
        """AttributeError raised on empty input to Set mode"""
        self.assertRaises(AttributeError, self.fog.Set, mode="")

    def test_SetMode_too_much_input(self):
        """AttributeError raised on too_much input to Set mode"""
        self.assertRaises(AttributeError, self.fog.Set, mode=["INV", "ALID"])

    # ENABLE
    def test_SetEnabled_attr(self):
        """Set enabled changes fog's enabled attribute"""
        val = 0
        self.fog.Set(enabled=val)
        self.assertEqual(self.fog.enabled, val)

    def test_SetEnabled_GL(self):
        """Set enabled changes GL_FOG"""
        val = 0
        self.fog.Set(enabled=val)
        enabled = GL.glGetInteger(GL.GL_FOG)
        self.assertEqual(enabled, val)

    def test_SetEnabled_state(self):
        """Set enabled changes fog's state['enabled']"""
        val = 0
        self.fog.Set(enabled=val)
        state = self.fog.getState()
        enabled = state["enabled"]
        self.assertEqual(enabled, 0)

    def test_SetEnabled_bad_input(self):
        """ValueError raised on bad input to Set enabled"""
        self.assertRaises(ValueError, self.fog.Set, enabled=2)

    def test_SetEnabled_empty_input(self):
        """ValueError raised on empty input to Set enabled"""
        self.assertRaises(ValueError, self.fog.Set, enabled="")


if __name__ == "__main__":
    unittest.main()

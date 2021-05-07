## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by

#
#
#  $Id: test_Clip.py,v 1.26 2010/11/20 00:55:42 sanner Exp $
#
#

import unittest
import numpy.oldnumeric as Numeric
import math
import warnings
import sys

from mglutil.math.rotax import rotax
from opengltk.OpenGL import GL
from DejaVu import Viewer
from DejaVu.Spheres import Spheres


class Clip_BaseTests(unittest.TestCase):
    """
    setUp + tearDown form a fixture: working environment for the testing code
    """

    def setUp(self):
        """
        start Viewer
        """
        if not hasattr(self, "vi"):
            self.vi = Viewer(verbose=False)
            self.vi.GUI.top.master.withdraw()
            # this is good also:
            # self.vi.cameras[0].master.master.lift()
            self.clip = self.vi.currentClip
            self.orig_state = self.clip.getState()

    def tearDown(self):
        """
        clean-up
        """
        # print 'in clip tearDown'
        # apply(self.clip.Set, (), self.orig_state)
        try:
            self.vi.Exit()
        except:
            pass
        # self.vi.__del__()

    # Name
    def test_Name(self):
        """Name is ClipPlane0"""
        self.assertEqual(self.clip.name, "ClipPlane0")

    # end Name

    # COLOR
    def test_SetColor_attr(self):
        """Set color changes clip's color attribute"""
        self.clip.Set(color=(1, 0, 0))
        col = self.clip.color
        self.assertEqual(col[0], 1.0)
        self.assertEqual(col[1], 0.0)
        self.assertEqual(col[2], 0.0)

    def test_SetColor_state(self):
        """Set color changes clip's state['color']"""
        self.clip.Set(color=(1, 0, 0))
        state = self.clip.getState()
        col = state["color"]
        self.assertEqual(col[0], 1.0)
        self.assertEqual(col[1], 0.0)
        self.assertEqual(col[2], 0.0)

    def test_SetColor_bad_input(self):
        """ValueError raised on bad input to Set color"""
        self.assertRaises(ValueError, self.clip.Set, color=(1, 0))

    def test_SetColor_empty_input(self):
        """ValueError raised on empty input to Set color"""
        self.assertRaises(ValueError, self.clip.Set, color=())

    def test_SetColor_too_much_input(self):
        """ValueError raised on too_much input to Set color"""
        self.assertRaises(ValueError, self.clip.Set, color=(1, 0, 0, 1, 1))

    # end COLOR

    # ENABLE
    def test_Enabled_attr(self):
        """Test clip's enabled attribute is False"""
        self.assertEqual(self.clip.enabled, False)

    def test_Enabled_GL_CLIP_PLANE0(self):
        """Test enabled GL_CLIP_PLANE0"""
        self.assertEqual(GL.glIsEnabled(GL.GL_CLIP_PLANE0), False)

    def test_SetEnabled_attr(self):
        """Set enabled changes clip's enabled attribute"""
        val = True
        self.clip.Set(enabled=val)
        self.assertEqual(self.clip.enabled, val)

    def test_SetEnabled_state(self):
        """Set enabled changes clip's state['enabled']"""
        val = True
        self.clip.Set(enabled=val)
        state = self.clip.getState()
        enabled = state["enabled"]
        self.assertEqual(enabled, val)

    def test_SetEnabled_changes_GL_CLIP_PLANE0(self):
        """Set enabled changes GL_CLIP_PLANE0"""
        val = True
        self.clip.Set(enabled=val)
        self.assertEqual(GL.glIsEnabled(GL.GL_CLIP_PLANE0), val)

    def test_SetEnabled_bad_input(self):
        """AttributeError raised on bad input to Set enabled"""
        self.assertRaises(AttributeError, self.clip.Set, enabled=2)

    def test_SetEnabled_empty_input(self):
        """AttributeError raised on empty input to Set enabled"""
        self.assertRaises(AttributeError, self.clip.Set, enabled="")

    # end ENABLED

    # VISIBLE
    def test_Visible_attr(self):
        """Test clip's visible attribute is False"""
        self.assertEqual(self.clip.visible, False)

    def test_SetVisible_attr(self):
        """Set visible changes clip's visible attribute"""
        val = True
        self.clip.Set(visible=val)
        self.assertEqual(self.clip.visible, val)

    def test_SetVisible_state(self):
        """Set visible changes clip's state['visible']"""
        val = True
        self.clip.Set(visible=val)
        state = self.clip.getState()
        visible = state["visible"]
        self.assertEqual(visible, val)

    def test_SetVisible_bad_input(self):
        """AttributeError raised on bad input to Set visible"""
        self.assertRaises(AttributeError, self.clip.Set, visible=2)

    def test_SetVisible_empty_input(self):
        """AttributeError raised on empty input to Set visible"""
        self.assertRaises(AttributeError, self.clip.Set, visible="")

    # end VISIBLE

    # LINEWIDTH
    def test_LineWidth_attr(self):
        """Test clip's lineWidth attribute is 2.0"""
        self.assertEqual(self.clip.lineWidth, 2)

    def test_SetLineWidth_attr(self):
        """Set lineWidth changes clip's lineWidth attribute"""
        val = 4
        self.clip.Set(lineWidth=val)
        self.assertEqual(self.clip.lineWidth, val)

    def test_SetLineWidth_state(self):
        """Set lineWidth changes clip's state['lineWidth']"""
        val = 4
        self.clip.Set(lineWidth=val)
        state = self.clip.getState()
        lineWidth = state["lineWidth"]
        self.assertEqual(lineWidth, val)

    # FIX THESE BY CHECKING INPUT IN CLIP.PY
    def test_SetLineWidth_bad_input(self):
        """ValueError raised on bad input to Set lineWidth"""
        self.assertRaises(ValueError, self.clip.Set, lineWidth=-1)

    def test_SetLineWidth_bad_input2(self):
        """ValueError raised on stringinput to Set lineWidth"""
        self.assertRaises(ValueError, self.clip.Set, lineWidth="a")

    def test_SetLineWidth_string_float_input(self):
        """No ValueError raised on stringinput of a float to Set lineWidth"""
        # import pdb;pdb.set_trace()
        val = "1"
        self.clip.Set(lineWidth=val)
        self.assertEqual(self.clip.lineWidth, 1)
        # self.assertRaises(ValueError, self.clip.Set, lineWidth='-1.0')

    def test_SetLineWidth_empty_input(self):
        """ValueError raised on empty input to Set lineWidth"""
        self.assertRaises(ValueError, self.clip.Set, lineWidth="")

    # end LINEWIDTH

    # INITIAL COEFFICIENTS
    def test_InitialCoefficients(self):
        """Test clip's InitialCoefficients are (0,0,0,0)"""
        expectedVal = (0.0, 0.0, 0.0, 0)
        coefs = GL.glGetClipPlane(GL.GL_CLIP_PLANE0)
        for c, v in zip(coefs, expectedVal):
            self.assertEqual(c, v)


# end INITIAL COEFFICIENTS


class Clip_ObjectTests(unittest.TestCase):
    """
    setUp + tearDown form a fixture: working environment for the testing code
    """

    def setUp(self):
        """
        start Viewer
        """
        if not hasattr(self, "vi"):
            self.vi = Viewer(verbose=False)
            # self.vi.GUI.top.master.withdraw()
            self.camera = self.vi.cameras[0]
            self.camera.master.master.lift()
            self.spheres = Spheres(
                "test",
                centers=(
                    (-2.5, 0, 0),
                    (4.5, 0, 0),
                ),
                quality=15,
                radii=(2, 4),
            )
            self.vi.AddObject(self.spheres)
            self.vi.Normalize_cb()
            self.vi.master.update()
            # self.vi.stopAutoRedraw()
            self.clip = self.vi.clipP[0]
            self.clip.Set(enabled=False)
            # self.spheres.AddClipPlane(self.clip)
            self.camera.Set(projectionType=self.vi.cameras[0].ORTHOGRAPHIC)
            self.camera.master.master.lift()
            self.vi.OneRedraw()

    def tearDown(self):
        """
        clean-up
        """
        # print 'in clip tearDown'
        # apply(self.clip.Set, (), self.orig_state)
        try:
            self.vi.Exit()
            delattr(self, "vi")
        except:
            pass
        # self.vi.__del__()

    def test_setup_spheres_clips_right_sphere(self):
        """
        check setup of spheres clip plane is working via zbuffer min
        NB: on sgi this may break if there are other windows open which
        overlap the camera's window"""
        width = self.camera.width
        height = self.camera.height
        zbuf = self.camera.GrabZBufferAsArray()  # lock=False)
        zbuf.shape = (width, height)
        self.camera.master.master.lift()
        self.vi.OneRedraw()
        # check that something is in the right half
        midway = int(self.camera.width / 2.0)
        # self.assertEqual(round(zbuf[:,midway:].min(),1)< .5, True)
        self.assertEqual(zbuf[:, midway:].min() < 0.6, True)

        self.spheres.AddClipPlane(self.clip)
        self.clip.Set(enabled=True)
        self.camera.master.master.lift()
        self.vi.OneRedraw()
        zbuf2 = self.camera.GrabZBufferAsArray()  # lock=False)
        zbuf2.shape = (width, height)
        # self.assertEqual(round(min(min(zbuf2[:,midway:]))), 1.0)
        self.assertEqual(round(zbuf2[:, midway:].min()), 1.0)

    def test_translating_clip_removes_half_left_sphere(self):
        """
        check translating clip plane is working via zbuffer min
        NB: on sgi this may break if there are other windows open which
        overlap the camera's window"""
        # self.clip.Set(translation=(-5, 0, 0))
        self.spheres.AddClipPlane(self.clip)
        self.clip.Set(enabled=True)
        self.clip.Set(translation=(-2.5, 0, 0))
        self.camera.master.master.lift()
        self.vi.update()
        midway = int(self.camera.width / 2.0)
        self.vi.OneRedraw()
        zbuf = self.camera.GrabZBufferAsArray()  # lock=False)
        zbuf.shape = (self.camera.width, self.camera.height)
        # self.assertEqual(round(min(min(zbuf[:,midway:]))), 1.0)
        self.assertEqual(round(zbuf[:, midway:].min()), 1.0)

    def test_rotating_clip_removes_top_half(self):
        """
        check rotating clip plane is working via zbuffer min
        NB: on sgi this may break if there are other windows open which
        overlap the camera's window"""
        mat = rotax((0, 0, 0), (0, 0, 1), math.pi / 2.0)
        self.spheres.AddClipPlane(self.clip)
        self.clip.Set(enabled=True)
        self.clip.Set(rotation=mat)
        self.camera.master.master.lift()
        self.vi.OneRedraw()
        zbuf = self.camera.GrabZBufferAsArray()  # lock=False)
        zbuf.shape = (self.camera.width, self.camera.height)
        # the array is flipped vertically compared tot he image
        # so we check the top half of the image by testing the
        # lower half of the array i.e. [midway:, :]
        midway = int(self.camera.height / 2.0)
        # self.assertEqual(round(min(min(zbuf[midway:, :]))), 1.0)
        self.assertEqual(round(zbuf[midway:, :].min()), 1.0)

    def test_translating_clip_removes_everything(self):
        """
        check translating clip plane removes everything
        NB: on sgi this may break if there are other windows open which
        overlap the camera's window
        """
        self.spheres.AddClipPlane(self.clip)
        self.clip.Set(enabled=True)
        self.clip.Set(translation=(-5, 0, 0))
        self.camera.master.master.lift()
        self.vi.OneRedraw()
        zbuf = self.camera.GrabZBufferAsArray()  # lock=False)
        zbuf.shape = (self.camera.width, self.camera.height)
        if sys.platform == "irix6":
            # on SGI octane 2 the opengl card has a bug:
            # the clipping plane doesn't affect the Z buffer !!!
            # so we just set a warning to pass the test anyway
            if min(min(zbuf)) != max(max(zbuf)):
                warnings.warn("clipping plane doesn't affect Z buffer")
        else:
            # self.assertEqual(min(min(zbuf)), max(max(zbuf)))
            self.assertEqual(zbuf.min(), zbuf.max())


if __name__ == "__main__":
    test_cases = [
        "Clip_BaseTests",
        "Clip_ObjectTests",
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

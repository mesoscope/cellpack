########################################################################
#
# Date: October 2006 Authors: Guillaume Vareille, Michel Sanner
#
#    vareille@scripps.edu
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Guillaume Vareille, Michel Sanner and TSRI
#
#########################################################################
#
# $Header$
#
# $Id$
#

import os
import Image
from copy import deepcopy

from opengltk.extent import _gllib
from opengltk.OpenGL import GL
from DejaVu.Insert2d import Insert2d


class StickerImage(Insert2d):

    keywords = Insert2d.keywords + [
        "image",
    ]

    def __init__(self, name="StickerImage", check=1, **kw):
        # print "StickerImage.__init__"

        self.image = None

        Insert2d.__init__(*(self, name, check), **kw)

        self.needsRedoDpyListOnResize = True

    def Set(self, check=1, redo=1, updateOwnGui=True, **kw):
        """set data for this object:
        check=1 : verify that all the keywords present can be handle by this func
        redo=1 : append self to viewer.objectsNeedingRedo
        updateOwnGui=True : allow to update owngui at the end this func"""
        # print "StickerImage.Set"
        redoFlags = Insert2d.Set(*(self, check, 0), **kw)

        image = kw.get("image")
        if image is not None:
            kw.pop("image")
            self.image = image
            self.size[0] = self.image.size[0]
            self.size[1] = self.image.size[1]
            redoFlags |= self._redoFlags["redoDisplayListFlag"]

        return self.redoNow(redo, updateOwnGui, redoFlags)

    def Draw(self):
        # print "StickerImage.Draw", self

        if self.image is None:
            return

        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        Insert2d.Draw(self)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glLoadIdentity()

        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glDisable(GL.GL_LIGHTING)

        width = self.size[0]
        height = self.size[1]

        fullWidth = self.viewer.currentCamera.width
        fullHeight = self.viewer.currentCamera.height

        # we want the anchor of the image to be at the given position
        posxFromLeft = self.position[0] * fullWidth - self.anchor[0] * width
        posyFrombottom = (1.0 - self.position[1]) * fullHeight - (
            1.0 - self.anchor[1]
        ) * height
        # print "posxFromLeft, posyFrombottom", posxFromLeft, posyFrombottom

        # used for picking
        self.polygonContour = [
            (posxFromLeft, posyFrombottom),
            (posxFromLeft + width, posyFrombottom),
            (posxFromLeft + width, posyFrombottom + height),
            (posxFromLeft, posyFrombottom + height),
        ]

        # this accept negative values were GL.glRasterPos2f(x,y) doesn't
        GL.glRasterPos2f(0, 0)
        _gllib.glBitmap(0, 0, 0, 0, posxFromLeft, posyFrombottom, 0)

        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        if self.image.mode == "RGBA":
            _gllib.glDrawPixels(
                self.image.size[0],
                self.image.size[1],
                GL.GL_RGBA,
                GL.GL_UNSIGNED_BYTE,
                self.image.tostring(),
            )
        elif self.image.mode == "RGB":
            _gllib.glDrawPixels(
                self.image.size[0],
                self.image.size[1],
                GL.GL_RGB,
                GL.GL_UNSIGNED_BYTE,
                self.image.tostring(),
            )
        elif self.image.mode == "L":
            _gllib.glDrawPixels(
                self.image.size[0],
                self.image.size[1],
                GL.GL_LUMINANCE,
                GL.GL_UNSIGNED_BYTE,
                self.image.tostring(),
            )

        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPopMatrix()

        return 1

    def setSize(self, event, redo=1):
        """the trackball transmit the translation info"""
        pass

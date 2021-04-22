#########################################################################
#
# Date: May 2003 Authors: Ruth Huey,  Michel Sanner
#
#    rhuey@scripps.edu
#    sanner@scripps.edu
#
# Copyright:  Michel Sanner, Ruth Huey, and TSRI
#
#########################################################################

#
#
# $Header: /opt/cvs/python/packages/share1.5/DejaVu/Tests/test_ColorMap.py,v 1.15 2006/10/27 20:52:48 vareille Exp $
#
# $Id: test_ColorMap.py,v 1.15 2006/10/27 20:52:48 vareille Exp $
#
#
#
#


import sys, Tkinter
import unittest
from mglutil.regression import testplus
from DejaVu.colorTool import RGBRamp, RedWhiteBlueRamp
from DejaVu.colorMapLegend import ColorMapLegend
from DejaVu.colorMap import ColorMap
from DejaVu.ColormapGui import ColorMapGUI
from DejaVu.Viewer import Viewer
from time import sleep

# add methods to test configure + write methods when updated
class ColorMapTest(unittest.TestCase):
    def setUp(self):
        self.root = Tkinter.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_constructor(self):
        # test if we can build a colormap with a ramp
        cmapgui = ColorMapGUI(name="test", ramp=RGBRamp(), mini=0, maxi=255)
        self.assertEqual(cmapgui.name, "test")
        self.assertEqual(len(cmapgui.ramp), 256)
        self.assertEqual(cmapgui.mini, 0.0)
        self.assertEqual(cmapgui.maxi, 255)
        self.assertEqual(len(cmapgui.history), 1)
        self.assertEqual(cmapgui.currentOnStack, True)

    def test_constructorFromFile(self):
        # test if we can build basic cmap from file
        cmapgui = ColorMapGUI(name="second", filename="./Data/test_map.py")
        self.assertEqual(len(cmapgui.ramp), 5)
        self.assertEqual(cmapgui.mini, 0.0)
        self.assertEqual(cmapgui.maxi, 10.0)
        self.assertEqual(cmapgui.name, "second")
        self.assertEqual(len(cmapgui.history), 1)
        self.assertEqual(cmapgui.currentOnStack, True)

    def test_configureCmap(self):
        cmapgui = ColorMapGUI(name="test", ramp=RGBRamp())
        cmapgui.configure(name="newRamp", mini=7, maxi=53, geoms={"g1": 1})
        self.assertEqual(cmapgui.mini, 7)
        self.assertEqual(cmapgui.maxi, 53)
        self.assertEqual(len(cmapgui.geoms), 1)
        self.assertEqual(len(cmapgui.history), 1)

        cmapgui.configure(ramp=RedWhiteBlueRamp())
        self.assertEqual(len(cmapgui.history), 2)
        self.assertEqual(cmapgui.currentOnStack, True)
        self.assertEqual(cmapgui.mini, 7)
        self.assertEqual(cmapgui.maxi, 53)

    def test_pushRamp(self):

        # import pdb;pdb.set_trace()

        # test if we can build a very basic cmap and push the ramp
        cmapgui = ColorMapGUI(name="test", ramp=RGBRamp())
        cmapgui.pushRamp()
        # Cannot push the ramp when already on the history stack
        self.assertEqual(len(cmapgui.history), 1)
        newRamp = RedWhiteBlueRamp()
        cmapgui.configure(ramp=newRamp, pushRamp=False)
        self.assertEqual(len(cmapgui.history), 1)
        self.assertEqual(cmapgui.currentOnStack, False)
        cmapgui.pushRamp()
        self.assertEqual(len(cmapgui.history), 2)
        self.assertEqual(cmapgui.currentOnStack, True)

    def test_popRamp(self):
        # Create an cmap with no ramp
        cmapgui = ColorMapGUI(name="test", ramp=None)
        self.assertEqual(len(cmapgui.history), 1)
        # call popRamp when len(history) is equal to 0
        cmapgui.popRamp()
        self.assertEqual(len(cmapgui.history), 1)

        # fill in the history stack with 4 more entries:
        newRamp = RGBRamp()
        for x in xrange(4):
            cmapgui.configure(ramp=newRamp)
        self.assertEqual(len(cmapgui.history), 5)

        # Call popRamp with the default argument index=-1
        cmapgui.popRamp()
        self.assertEqual(len(cmapgui.history), 4)
        self.assertEqual(cmapgui.currentOnStack, False)

        # Pop all the ramp from the history stack
        for x in xrange(4):
            cmapgui.popRamp()
        # The first entry of the history stack is never removed.
        self.assertEqual(len(cmapgui.history), 1)
        self.assertEqual(cmapgui.currentOnStack, True)

        # Test popRamp with various index
        # 1- (-len(cmap.history))
        # fill in the history stack with 5 entries:
        for x in xrange(5):
            cmapgui.configure(ramp=newRamp)
        # 5 new entries plus the first entry
        self.assertEqual(len(cmapgui.history), 6)
        cmapgui.popRamp(-len(cmapgui.history))
        self.assertEqual(len(cmapgui.history), 1)
        self.assertEqual(cmapgui.currentOnStack, True)

        # 2- negative index which doesn't exists
        # fill in the history stack with 5 entries:
        for x in xrange(5):
            cmapgui.configure(ramp=newRamp)
        # 5 new entries plus the first entry
        self.assertEqual(len(cmapgui.history), 6)
        cmapgui.popRamp(-len(cmapgui.history) - 2)
        self.assertEqual(len(cmapgui.history), 1)
        self.assertEqual(cmapgui.currentOnStack, True)

        # 3- negative index in the list
        # fill in the history stack with 5 entries:
        for x in xrange(5):
            cmapgui.configure(ramp=newRamp)
        # 5 new entries plus the first entry
        self.assertEqual(len(cmapgui.history), 6)
        cmapgui.popRamp(-3)
        self.assertEqual(len(cmapgui.history), 3)
        # When popping a ramp from the history the new ramp
        # is not pushed back on the list except the first entry which
        # always stays on the history stack
        self.assertEqual(cmapgui.currentOnStack, False)

    def test_CmapWithLegend(self):
        cmapGui = ColorMapGUI(name="test", ramp=RGBRamp())
        cmapGui.legend.Set(
            width=10,
            height=1,
            interp=1,
        )

        cmapGui.configure(name="newRamp", mini=7, maxi=53, geoms={"g1": 1})
        self.assertEqual(cmapGui.mini, 7)
        self.assertEqual(cmapGui.maxi, 53)
        self.assertEqual(len(cmapGui.geoms), 1)
        self.assertEqual(cmapGui.legend.mini, 7)
        self.assertEqual(cmapGui.legend.maxi, 53)

    def test_asHSV(self):
        cmapGui = ColorMapGUI(name="test", ramp=RGBRamp())
        hsv = cmapGui.asHSV()
        self.assertEqual(len(hsv), len(cmapGui.ramp))
        # check that hsv[0]==ToHSV(cmap.ramp[0])??

    def test_reset(self):
        rgbramp = RGBRamp()
        cmapGui = ColorMapGUI(name="rgb", ramp=rgbramp)
        self.assertEqual(cmapGui.history[0], cmapGui.ramp)
        self.assertEqual(len(cmapGui.history), 1)
        self.assertEqual(cmapGui.currentOnStack, True)

        rwbramp = RedWhiteBlueRamp()
        cmapGui.configure(name="rwb", ramp=rwbramp)
        self.assertEqual(len(cmapGui.history), 2)
        self.assertEqual(cmapGui.currentOnStack, True)
        self.failUnless(cmapGui.history[0] != cmapGui.ramp)

        cmapGui.reset()
        rgb = map(lambda x: x[:3], cmapGui.ramp)
        self.assertEqual(rgb, rgbramp.tolist())
        self.assertEqual(cmapGui.currentOnStack, True)
        self.assertEqual(len(cmapGui.history), 1)

    #    def test_resetComp(self):
    #
    #        import pdb;pdb.set_trace()
    #
    #        cmapgui = ColorMapGUI(name='rgb10', filename="Data/rgb10_map.py")
    #        rgb10 = cmapgui.ramp[:]
    #        c2 = ColorMap(name='rgb10T', filename='Data/rgb10_transparent_map.py')
    #        rgb10T = c2.ramp[:]
    #        cmapgui.configure(ramp=c2.ramp[:])
    #        self.assertEqual(len(cmapgui.history),2)
    #        self.assertEqual(cmapgui.currentOnStack, True)
    #        # reset the 'Hue' component
    #        cmapgui.resetComp('Hue')
    #        # allways keep the first entry
    #        self.assertEqual(len(cmapgui.history),2)
    #        self.assertEqual(cmapgui.currentOnStack, True)
    #
    #        self.assertEqual(cmapgui.ramp, rgb10T)
    #
    #        # reset the "Opa" component of the rgb10T
    #        cmapgui.resetComp('Opa')
    #        self.assertEqual(cmapgui.ramp, rgb10)
    #        self.assertEqual(len(cmapgui.history),2)
    #        self.assertEqual(cmapgui.currentOnStack, True)

    def test_getDescr(self):
        rgb = RGBRamp()
        cmap = ColorMap(name="test", ramp=rgb, mini=0, maxi=255)
        cfg = cmap.getDescr()
        self.assertEqual(cfg["name"], "test")
        self.assertEqual(cfg["mini"], 0.0)
        self.assertEqual(cfg["maxi"], 255.0)
        self.assertEqual(cfg["ramp"], cmap.ramp)

    def test_read(self):

        rgb = RGBRamp()
        cmapgui = ColorMapGUI(name="test", ramp=rgb)
        r = map(lambda x: x[:3], cmapgui.ramp)
        self.assertEqual(r, rgb.tolist())
        self.assertEqual(cmapgui.name, "test")
        self.assertEqual(len(cmapgui.history), 1)

        # import pdb;pdb.set_trace()

        cmapgui.read("Data/rgb10_map.py")
        self.assertEqual(cmapgui.name, "rgb10")
        self.failUnless(cmapgui.ramp != rgb.tolist())

        self.assertEqual(len(cmapgui.history), 2)

    #        self.assertEqual(len(cmapgui.history), 1)
    #        self.assertEqual(cmapgui.ramp, cmapgui.history[0])

    def test_write(self):
        cmap = ColorMap(name="test", ramp=RGBRamp())
        cmap.write("/tmp/output_map.py")
        cmap2 = ColorMap(name="test", filename="/tmp/output_map.py")
        self.assertEqual(cmap2.ramp, cmap.ramp)
        self.assertEqual(cmap2.name, cmap.name)
        import os

        os.system("rm -f /tmp/output_map.py")


## harness = testplus.TestHarness( __name__,
##                                 connect = setUp,
##                                 funs = testplus.testcollect( globals()),
##                                 disconnect = tearDown
##                                 )

if __name__ == "__main__":
    unittest.main()
##     testplus.chdir()
##     print harness
##     sys.exit( len( harness))

## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by

import sys
from time import sleep

import sys, os, math, types
import unittest, numpy.oldnumeric as Numeric
from DejaVu.Viewer import Viewer
from time import sleep
from Tkinter import Tk, Frame, Toplevel
from DejaVu.Spheres import Spheres


class basics_Tkinter_Viewer_Tests(unittest.TestCase):
    """
    tests for Tkinter basics in DejaVu.Viewer
    """

    def setUp(self):
        self.root = Tk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except:
            pass

    def test_01_constructViewerWhenTkDefaultRootExists(self):
        """check creating viewer when Tkinter.root already exists"""
        # this test would fail if DejaVu.Viewer would try to create independent Tk
        # instances, because Pmw cannot handle several instances
        vi = Viewer(verbose=0)
        vi.Exit()
        self.assertEqual(1, 1)

    def test_ViewerWithMaster(self):
        """create a viewer for a given master and destroy it"""
        master = Frame(self.root)
        master.pack()
        vi = Viewer(verbose=0, master=master)
        self.assertEqual(vi.master, master)
        vi.Exit()

    def test_ViewerWithFrameGuiMaster(self):
        """create a viewer with a frame to pack the GUI and destroy it"""
        master = Frame(self.root)
        master.pack()
        vi = Viewer(verbose=0, guiMaster=master)
        self.assertEqual(vi.master.master, self.root)
        self.assertEqual(vi.GUI.root, master)
        vi.Exit()

    def test_ViewerWithToplevelGuiMaster(self):
        """create a viewer with a frame to pack the GUI and destroy it"""
        master = Toplevel(self.root)
        vi = Viewer(verbose=0, guiMaster=master)
        self.assertEqual(vi.master.master.master, self.root)
        self.assertEqual(vi.GUI.root, master)
        vi.Exit()


class basics_Viewer_Tests(unittest.TestCase):
    """
    tests for basics in DejaVu.Viewer
    """

    def setUp(self):
        """
        start Viewer
        """
        self.vi = Viewer(verbose=0)

    def tearDown(self):
        """
        clean-up
        """
        try:
            self.vi.Exit()
        except:
            pass

    def test_deleteCamera(self):
        """check viewer.deleteCamera"""
        self.vi.DeleteCamera(self.vi.cameras[0])
        self.assertEqual(1, 1)

    def test_deleteCamera2(self):
        """check viewer.deleteCamera"""
        self.vi.AddCamera()
        self.vi.DeleteCamera(self.vi.cameras[1])
        self.assertEqual(1, 1)

    def test_TwoViewers1(self):
        """create 2 viewers and destroy them"""
        # this test makes sure that the GUI has different roots
        vi2 = Viewer(verbose=0)
        self.assertNotEqual(self.vi.master, vi2.master)
        # vi2.Exit()

    def test_2cameras(self):
        """display 4 spheres in 2 different cameras"""

        s1 = Spheres("sph", vertices=[[0, 0, 0], [3, 0, 0], [0, 3, 0], [0, 0, 3]])
        self.vi.AddObject(s1)
        ## add a second camera
        self.vi.AddCamera()
        self.assertEqual(1, 1)

    def test_multipleViewers(self):
        """create 3 independent viewers"""

        s1 = Spheres(
            "sph",
            vertices=[[0, 0, 0], [3, 0, 0], [0, 5, 0], [0, 0, 3]],
            materials=((1, 0, 0),),
            inheritMaterial=0,
        )
        self.vi.AddObject(s1)
        vi2 = Viewer(verbose=0)
        s2 = Spheres(
            "sph",
            vertices=[[0, 0, 0], [3, 0, 0], [0, 3, 0], [0, 0, 3]],
            materials=((0, 1, 0),),
            inheritMaterial=0,
        )
        vi2.AddObject(s2)
        vi3 = Viewer(verbose=0)
        s3 = Spheres(
            "sph",
            vertices=[[0, 0, 0], [3, 0, 0], [0, 3, 0], [0, 0, 3]],
            materials=((0, 0, 1),),
            inheritMaterial=0,
        )
        vi3.AddObject(s3)
        vi2.Exit()
        vi3.Exit()

        if sys.platform == "darwin":
            self.vi.currentCamera.Activate()  # needed on our ppcdarwin7

        self.assertEqual(1, 1)


if __name__ == "__main__":
    test_cases = [
        "basics_Tkinter_Viewer_Tests",
        "basics_Viewer_Tests",
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

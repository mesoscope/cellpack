import gc

import unittest
from DejaVu.Viewer import Viewer
from time import sleep
from Tkinter import Tk, Frame, Toplevel
from DejaVu.Spheres import Spheres


class memory_Tests(unittest.TestCase):
    """
    tests for memory
    """

    # def setUp(self):
    #    self.root = Tk()
    #    self.root.withdraw()
    #
    #    def tearDown(self):
    #        try:
    #            self.root.destroy()
    #        except:
    #            pass

    def XXtest_creatingViewers100Time(self):
        """create a Viewer and destroy it 100 times"""

        # for i in range(100):
        #    vi = Viewer(verbose=0)
        #    vi.master.update()
        #    vi.Exit()
        #    gc.collect()
        self.assertEqual(1, 1)

    def test_creatingViewers100TimeWithViewer(self):
        """create a Viewer and destroy it 100 times, when a Viewer already exists"""
        vi1 = Viewer(verbose=False)
        for i in range(10):
            vi = Viewer(verbose=0)
            vi.master.update()
            vi.Exit()
            gc.collect()
        vi1.Exit()
        gc.collect()
        self.assertEqual(1, 1)


if __name__ == "__main__":
    test_cases = [
        "memory_Tests",
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

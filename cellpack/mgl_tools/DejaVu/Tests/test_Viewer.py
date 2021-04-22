import sys
from mglutil.regression import testplus
import unittest
from DejaVu.Geom import Geom
from DejaVu.Points import Points
from DejaVu.Viewer import Viewer
from DejaVu.Polylines import Polylines


class TestViewer(unittest.TestCase):
    def setUp(self):
        self.vi = Viewer(verbose=0)

    def tearDown(self):
        self.vi.Exit()

    def test_AddObject(self):
        # MasterGeom1
        mg = Geom("mol1", shape=(0, 0), visible=1)
        wire = Geom("lines", shape=(0, 0), visible=1)
        # lines: Bonded atoms are represented by IndexedPolyLines
        lcoords = [
            [
                [17.0, 14.0, 4.0],
                [17.0, 13.0, 4.0],
                [16.0, 13.0, 5.0],
                [15.0, 14.0, 6.0],
                [18.0, 13.0, 5.0],
                [19.0, 13.0, 4.0],
                [18.0, 12.0, 6.0],
                [15.0, 12.0, 5.0],
                [14.0, 11.0, 6.0],
                [14.0, 11.0, 7.0],
                [15.0, 10.0, 7.0],
                [13.0, 11.0, 5.0],
                [13.0, 9.0, 5.0],
                [12.0, 11.0, 4.0],
                [13.0, 11.0, 8.0],
                [14.0, 11.0, 10.0],
                [12.0, 10.0, 10.0],
                [11.0, 11.0, 10.0],
                [14.0, 12.0, 11.0],
                [16.0, 12.0, 10.0],
                [12.0, 9.0, 11.0],
                [11.0, 9.0, 11.0],
            ]
        ]
        l = Polylines(
            "bonded",
            vertices=lcoords,
            visible=1,
            pickableVertices=1,
            lineWidth=3,
            inheritMaterial=0,
            inheritLineWidth=0,
        )
        # nobnds : Non Bonded atoms are represented by Points
        pcoords = [
            [11.0, 9.0, 13.0],
            [12.0, 8.0, 13.0],
            [10.0, 8.0, 11.0],
            [10.0, 8.0, 9.0],
            [10.0, 9.0, 14.0],
            [9.0, 9.0, 15.0],
            [9.0, 8.0, 16.0],
            [9.0, 8.0, 17.0],
            [8.0, 10.0, 15.0],
            [7.0, 10.0, 14.0],
            [8.0, 10.0, 13.0],
        ]
        p = Points(
            "nobnds",
            shape=(0, 3),
            pointWidth=6,
            visible=1,
            vertices=pcoords,
            inheritMaterial=0,
        )
        # bondorder : Bond Order are represented by Indexed PolyLines
        b = Polylines("bondorder", visible=1, lineWidth=3, inheritMaterial=0)
        # MasterGeom2
        mg2 = Geom("mol2", shape=(0, 0), visible=1)
        wire2 = Geom("lines", shape=(0, 0), visible=1)
        # lines: Bonded atoms are represented by IndexedPolyLines
        l2coords = [
            [
                [18.0, 14.0, 4.0],
                [18.0, 13.0, 4.0],
                [17.0, 13.0, 5.0],
                [16.0, 14.0, 6.0],
                [19.0, 13.0, 5.0],
                [20.0, 13.0, 4.0],
                [19.0, 12.0, 6.0],
                [16.0, 12.0, 5.0],
                [15.0, 11.0, 6.0],
                [15.0, 11.0, 7.0],
                [16.0, 10.0, 7.0],
                [14.0, 11.0, 5.0],
                [14.0, 9.0, 5.0],
                [13.0, 11.0, 4.0],
                [14.0, 11.0, 8.0],
                [15.0, 11.0, 10.0],
                [13.0, 10.0, 10.0],
                [12.0, 11.0, 10.0],
                [15.0, 12.0, 11.0],
                [17.0, 12.0, 10.0],
                [13.0, 9.0, 11.0],
                [12.0, 9.0, 11.0],
            ]
        ]
        l2 = Polylines(
            "bonded",
            vertices=l2coords,
            visible=1,
            pickableVertices=1,
            lineWidth=3,
            inheritMaterial=0,
            inheritLineWidth=0,
        )
        # nobnds : Non Bonded atoms are represented by Points
        p2coords = [
            [12.0, 9.0, 13.0],
            [13.0, 8.0, 13.0],
            [11.0, 8.0, 11.0],
            [11.0, 8.0, 9.0],
            [11.0, 9.0, 14.0],
            [10.0, 9.0, 15.0],
            [10.0, 8.0, 16.0],
            [10.0, 8.0, 17.0],
            [9.0, 10.0, 15.0],
            [8.0, 10.0, 14.0],
            [9.0, 10.0, 13.0],
        ]
        p2 = Points(
            "nobnds",
            shape=(0, 3),
            pointWidth=6,
            visible=1,
            vertices=p2coords,
            inheritMaterial=0,
        )
        # bondorder : Bond Order are represented by Indexed PolyLines
        b2 = Polylines("bondorder", visible=1, lineWidth=3, inheritMaterial=0)

        # Create a hierarchy of geometries.
        self.vi.AddObject(mg)
        wire.replace = True
        self.vi.AddObject(wire, parent=mg, redo=0)

        l.replace = True
        self.vi.AddObject(l, parent=wire, redo=0)
        p.replace = True
        self.vi.AddObject(p, parent=wire, redo=0)
        b.replace = True
        self.vi.AddObject(b, parent=wire, redo=0)

        self.vi.AddObject(mg2)
        wire2.replace = True
        self.vi.AddObject(wire2, parent=mg2, redo=0)

        l2.replace = True
        self.vi.AddObject(l2, parent=wire2, redo=0)
        p2.replace = True
        self.vi.AddObject(p2, parent=wire2, redo=0)
        b2.replace = True
        self.vi.AddObject(b2, parent=wire2, redo=0)

        # Make sure that each entry has been added to its proper place in the
        # object listbox.

    def test_DeleteObject(self):
        # MasterGeom1
        mg = Geom("mol1", shape=(0, 0), visible=1)
        wire = Geom("lines", shape=(0, 0), visible=1)
        # lines: Bonded atoms are represented by IndexedPolyLines
        lcoords = [
            [
                [17.0, 14.0, 4.0],
                [17.0, 13.0, 4.0],
                [16.0, 13.0, 5.0],
                [15.0, 14.0, 6.0],
                [18.0, 13.0, 5.0],
                [19.0, 13.0, 4.0],
                [18.0, 12.0, 6.0],
                [15.0, 12.0, 5.0],
                [14.0, 11.0, 6.0],
                [14.0, 11.0, 7.0],
                [15.0, 10.0, 7.0],
                [13.0, 11.0, 5.0],
                [13.0, 9.0, 5.0],
                [12.0, 11.0, 4.0],
                [13.0, 11.0, 8.0],
                [14.0, 11.0, 10.0],
                [12.0, 10.0, 10.0],
                [11.0, 11.0, 10.0],
                [14.0, 12.0, 11.0],
                [16.0, 12.0, 10.0],
                [12.0, 9.0, 11.0],
                [11.0, 9.0, 11.0],
            ]
        ]
        l = Polylines(
            "bonded",
            vertices=lcoords,
            visible=1,
            pickableVertices=1,
            lineWidth=3,
            inheritMaterial=0,
            inheritLineWidth=0,
        )
        # nobnds : Non Bonded atoms are represented by Points
        pcoords = [
            [11.0, 9.0, 13.0],
            [12.0, 8.0, 13.0],
            [10.0, 8.0, 11.0],
            [10.0, 8.0, 9.0],
            [10.0, 9.0, 14.0],
            [9.0, 9.0, 15.0],
            [9.0, 8.0, 16.0],
            [9.0, 8.0, 17.0],
            [8.0, 10.0, 15.0],
            [7.0, 10.0, 14.0],
            [8.0, 10.0, 13.0],
        ]
        p = Points(
            "nobnds",
            shape=(0, 3),
            pointWidth=6,
            visible=1,
            vertices=pcoords,
            inheritMaterial=0,
        )
        # bondorder : Bond Order are represented by Indexed PolyLines
        b = Polylines("bondorder", visible=1, lineWidth=3, inheritMaterial=0)
        # MasterGeom2
        mg2 = Geom("mol2", shape=(0, 0), visible=1)
        wire2 = Geom("lines", shape=(0, 0), visible=1)
        # lines: Bonded atoms are represented by IndexedPolyLines
        l2coords = [
            [
                [18.0, 14.0, 4.0],
                [18.0, 13.0, 4.0],
                [17.0, 13.0, 5.0],
                [16.0, 14.0, 6.0],
                [19.0, 13.0, 5.0],
                [20.0, 13.0, 4.0],
                [19.0, 12.0, 6.0],
                [16.0, 12.0, 5.0],
                [15.0, 11.0, 6.0],
                [15.0, 11.0, 7.0],
                [16.0, 10.0, 7.0],
                [14.0, 11.0, 5.0],
                [14.0, 9.0, 5.0],
                [13.0, 11.0, 4.0],
                [14.0, 11.0, 8.0],
                [15.0, 11.0, 10.0],
                [13.0, 10.0, 10.0],
                [12.0, 11.0, 10.0],
                [15.0, 12.0, 11.0],
                [17.0, 12.0, 10.0],
                [13.0, 9.0, 11.0],
                [12.0, 9.0, 11.0],
            ]
        ]
        l2 = Polylines(
            "bonded",
            vertices=l2coords,
            visible=1,
            pickableVertices=1,
            lineWidth=3,
            inheritMaterial=0,
            inheritLineWidth=0,
        )
        # nobnds : Non Bonded atoms are represented by Points
        p2coords = [
            [12.0, 9.0, 13.0],
            [13.0, 8.0, 13.0],
            [11.0, 8.0, 11.0],
            [11.0, 8.0, 9.0],
            [11.0, 9.0, 14.0],
            [10.0, 9.0, 15.0],
            [10.0, 8.0, 16.0],
            [10.0, 8.0, 17.0],
            [9.0, 10.0, 15.0],
            [8.0, 10.0, 14.0],
            [9.0, 10.0, 13.0],
        ]
        p2 = Points(
            "nobnds",
            shape=(0, 3),
            pointWidth=6,
            visible=1,
            vertices=p2coords,
            inheritMaterial=0,
        )
        # bondorder : Bond Order are represented by Indexed PolyLines
        b2 = Polylines("bondorder", visible=1, lineWidth=3, inheritMaterial=0)

        # Create a hierarchy of geometries.
        self.vi.AddObject(mg)
        wire.replace = True
        self.vi.AddObject(wire, parent=mg, redo=0)

        l.replace = True
        self.vi.AddObject(l, parent=wire, redo=0)
        p.replace = True
        self.vi.AddObject(p, parent=wire, redo=0)
        b.replace = True
        self.vi.AddObject(b, parent=wire, redo=0)

        self.vi.AddObject(mg2)
        wire2.replace = True
        self.vi.AddObject(wire2, parent=mg2, redo=0)

        l2.replace = True
        self.vi.AddObject(l2, parent=wire2, redo=0)
        p2.replace = True
        self.vi.AddObject(p2, parent=wire2, redo=0)
        b2.replace = True
        self.vi.AddObject(b2, parent=wire2, redo=0)

        # Make sure that each entry has been added to its proper place in the
        # object listbox.

    def test_AddObjectWhenExistsObjectWithSameName(self):
        from DejaVu import Viewer

        vi = Viewer()
        from DejaVu.IndexedPolygons import IndexedPolygons

        p1 = IndexedPolygons("foo", protected=True)
        vi.AddObject(p1)
        p2 = IndexedPolygons("foo", protected=True)
        try:
            vi.AddObject(p2)
        except RuntimeError:
            return

        raise RuntimeError(
            "second geom with same name should not be \
                            added, a ValueError should have been raised"
        )


## harness = testplus.TestHarness( __name__,
##                                 connect = setUp,
##                                 funs = testplus.testcollect( globals()),
##                                 disconnect = tearDown
##                                 )

## if __name__ == '__main__':
##     testplus.chdir()
##     print harness
##     sys.exit( len( harness))

M_PI = 3.14159265358979323846
from RAPID import RAPIDlib
import numpy.oldnumeric as Numeric
import math
import unittest, sys


class RapidTests(unittest.TestCase):
    def setUp(self):
        """
        start Viewer
        """
        try:
            from DejaVu.Viewer import Viewer

            self.vi = Viewer()
        except:
            print("Could not import Viewer.")
            self.vi = None

    def tearDown(self):
        """
        clean-up
        """
        try:
            if self.vi:
                self.vi.Exit()
        except:
            pass

    def test_Collide(self):
        # first, get a couple of boxes in which to put our models

        b1 = RAPIDlib.RAPID_model()
        b2 = RAPIDlib.RAPID_model()

        # then, load the boxes with triangles.  The following loads each
        # with a torus of 2*n1*n2 triangles.

        a = 1.0  # major radius of the tori
        b = 0.2  # minor radius of the tori

        n1 = 50  # tori will have n1*n2*2 triangles each
        n2 = 50

        count = 0

        p = Numeric.zeros((n1 * n1 * 4, 3), Numeric.Float64)

        trs = []
        for uc in range(n1):
            for vc in range(n2):
                u1 = (2.0 * M_PI * uc) / n1
                u2 = (2.0 * M_PI * (uc + 1)) / n1
                v1 = (2.0 * M_PI * vc) / n2
                v2 = (2.0 * M_PI * (vc + 1)) / n2
                p1 = [0, 0, 0]
                p2 = [0, 0, 0]
                p3 = [0, 0, 0]
                p4 = [0, 0, 0]
                c = count * 4
                p[c][0] = (a - b * math.cos(v1)) * math.cos(u1)
                p[c + 1][0] = (a - b * math.cos(v1)) * math.cos(u2)
                p[c + 2][0] = (a - b * math.cos(v2)) * math.cos(u1)
                p[c + 3][0] = (a - b * math.cos(v2)) * math.cos(u2)
                p[c][1] = (a - b * math.cos(v1)) * math.sin(u1)
                p[c + 1][1] = (a - b * math.cos(v1)) * math.sin(u2)
                p[c + 2][1] = (a - b * math.cos(v2)) * math.sin(u1)
                p[c + 3][1] = (a - b * math.cos(v2)) * math.sin(u2)
                p[c][2] = b * math.sin(v1)
                p[c + 1][2] = b * math.sin(v1)
                p[c + 2][2] = b * math.sin(v2)
                p[c + 3][2] = b * math.sin(v2)
                trs.append([c, c + 1, c + 2])
                trs.append([c + 3, c + 1, c + 2])
                count = count + 1
        trs_arr = Numeric.array(trs, "i")
        if True:
            R1 = Numeric.zeros((3, 3), "f")
            R2 = Numeric.zeros((3, 3), "f")
            T1 = Numeric.zeros((3), "f")
            T2 = Numeric.zeros((3), "f")
            R1[0][0] = R1[1][1] = R1[2][2] = 1.0
            R1[0][1] = R1[1][0] = R1[2][0] = 0.0
            R1[0][2] = R1[1][2] = R1[2][1] = 0.0
            R2[0][0] = R2[1][1] = R2[2][2] = 1.0
            R2[0][1] = R2[1][0] = R2[2][0] = 0.0
            R2[0][2] = R2[1][2] = R2[2][1] = 0.0
            T1[0] = 1.0
            T1[1] = 0.0
            T1[2] = 0.0
            T2[0] = 0.0
            T2[1] = 0.0
            T2[2] = 0.0
            print("adding triangles...")
            b1.addTriangles(p, trs_arr)
            b2.addTriangles(p, trs_arr)
            print("done")
        if self.vi:
            from DejaVu.IndexedPolygons import IndexedPolygons

            obj1 = IndexedPolygons("obj1", vertices=p, faces=trs_arr, inheritMaterial=0)
            col2 = Numeric.array(((0, 1, 0, 1),), "f")
            obj2 = IndexedPolygons(
                "obj2", vertices=p, faces=trs_arr, inheritMaterial=0, materials=col2
            )

            print("Tori have %d triangles each." % (count * 2))
            # now we are free to call the interference detect routine.
            # but first, construct the transformations which define the placement
            # of our two hierarchies in world space:
            # this placement causes them to overlap a large amount.
            self.vi.AddObject(obj1)
            obj1.SetTranslation(T1)
            self.vi.AddObject(obj2)
            self.vi.OneRedraw()
            self.vi.update()
            from time import sleep

            sleep(2)

        # now we can perform a collision query:

        RAPIDlib.RAPID_Collide_scaled(
            R1, T1, 1.0, b1, R2, T2, 1.0, b2, RAPIDlib.cvar.RAPID_ALL_CONTACTS
        )
        # RAPIDlib.RAPID_Collide(R1, T1, b1, R2, T2, b2, 1)
        # looking at the report, we can see where all the contacts were, and
        # also how many tests were necessary:

        # print "All contacts between overlapping tori:"

        print("Num box tests: %d" % RAPIDlib.cvar.RAPID_num_box_tests)
        print("Num contact pairs: %d" % RAPIDlib.cvar.RAPID_num_contacts)
        data1 = RAPIDlib.RAPID_Get_All_Pairs()
        # print "data1 type:", type(data1)

        # Notice the RAPID_ALL_CONTACTS flag we used in the call to collide().
        # The alternative is to use the FIRST_CONTACT flag, instead.
        # the result is that the collide routine searches for any contact,
        # but not all of them.  It takes many many fewer tests to locate a single
        # contact.

        RAPIDlib.RAPID_Collide_scaled(
            R1, T1, 1.0, b1, R2, T2, 1.0, b2, RAPIDlib.cvar.RAPID_FIRST_CONTACT
        )
        print("First contact between overlapping tori:")

        print("Num box tests: %d" % RAPIDlib.cvar.RAPID_num_box_tests)
        print("Num contact pairs: %d" % RAPIDlib.cvar.RAPID_num_contacts)
        data2 = RAPIDlib.RAPID_Get_All_Pairs()
        # print "data2 type:", type(data2)

        # by rotating one of them around the x-axis 90 degrees, they
        # are now interlocked, but not quite touching.

        R1[0][0] = 1.0
        R1[0][1] = 0.0
        R1[0][2] = 0.0
        R1[1][0] = 0.0
        R1[1][1] = 0.0
        R1[1][2] = -1.0
        R1[2][0] = 0.0
        R1[2][1] = 1.0
        R1[2][2] = 0.0

        RAPIDlib.RAPID_Collide_scaled(
            R1, T1, 1.0, b1, R2, T2, 1.0, b2, RAPIDlib.cvar.RAPID_FIRST_CONTACT
        )

        print("No contact between interlocked but nontouching tori:")

        print("Num box tests: %d" % RAPIDlib.cvar.RAPID_num_box_tests)
        print("Num contact pairs: %d" % RAPIDlib.cvar.RAPID_num_contacts)
        data3 = RAPIDlib.RAPID_Get_All_Pairs()
        print("data3 type:", type(data3))


if __name__ == "__main__":
    unittest.main()

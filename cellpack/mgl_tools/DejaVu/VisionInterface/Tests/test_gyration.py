#########################################################################
#
# Date: DEc 2005  Authors: Guillaume Vareille, Michel Sanner
#
#       vareille@scripps.edu
#       sanner@scripps.edu
#
# Copyright: Guillaume Vareille, Michel Sanner, and TSRI
#
#############################################################################
#
# $Header$
#
# $Id$
#

import sys

ed = None


def setUp():
    global ed
    from Vision.VPE import VisualProgramingEnvironment

    ed = VisualProgramingEnvironment(
        name="Vision",
        withShell=0,
    )
    from DejaVu.VisionInterface.DejaVuNodes import vizlib

    ed.addLibraryInstance(vizlib, "DejaVu.VisionInterface.DejaVuNodes", "vizlib")
    ed.root.update_idletasks()
    ed.configure(withThreads=0)


def tearDown():
    ed.exit_cb()
    import gc

    gc.collect()


##########################
## Helper methods
##########################


def pause(sleepTime=0.4):
    from time import sleep

    ed.master.update()
    sleep(sleepTime)


##########################
## Tests
##########################

# ===============================================================================
# this concerns the rethinking of IndexedPolygonsNE
# =============================================================================
def test_01_different_input_for_sphere_center():
    # test if Spheres accept:
    # - single point
    # - single point in list
    # - list of points
    # it is also a test for gyration sphere
    from DejaVu.Geom import Geom

    ed.loadNetwork("Data/gyration_net.py")
    net = ed.currentNetwork
    net.runOnNewData.value = True
    net.run()

    # the nodes
    PointsListNode = net.nodes[1]
    PointListNode = net.nodes[4]
    GyrationNode = net.getNodeByName("Gyration Sphere")[0]
    SphereNode = net.getNodeByName("spheres")[0]
    ViewerNode = net.getNodeByName("Viewer")[0]

    # the sphere geom
    data = SphereNode.outputPorts[0].data

    # is this a Spheres geom?
    assert data is not None, "Expected data, got %s" % data
    assert isinstance(data, Geom), "Expected %s, got %s" % (Geom, data.__class__)
    # is the radius set correctly?
    assert data.radius == 2.0, "Expected 2.0, got %s" % data.radius
    # how many spheres ?
    assert len(data.vertexSet.vertices) == 1, "expected %s got %s" % (
        1,
        len(data.vertexSet.vertices),
    )
    # is the center set correctly?
    array = data.vertexSet.vertices.array[0]
    assert (
        array[0] == array[1] == 1 and array[2] == 0
    ), "Expected 1 1 0 got array0: %s, array1: %s, array2: %s" % (
        array[0],
        array[1],
        array[2],
    )
    # was it correctly added to the viewer?
    assert (
        data in ViewerNode.vi.rootObject.children
    ), "data is: %s\nchildren are: %s" % (data, ViewerNode.vi.rootObject.children)
    # does it have a parent?
    assert data.parent is not None, "data.parent is: %s" % data.parent
    # does it know about the viewer?
    assert data.viewer is not None, "data.viewer is: %s" % data.viewer
    # is it visible?
    assert data.visible == True, "Expected True, got %s" % data.visible

    # delete connection from gyration: [3 3 0]
    net.deleteConnection(GyrationNode, "center", SphereNode, "coords")
    # connect to eval: [[-3 -3 -3]]
    net.connectNodes(PointListNode, SphereNode, portNode2="coords")
    data = SphereNode.outputPorts[0].data

    # is this a Spheres geom?
    assert data is not None, "Expected data, got %s" % data

    assert isinstance(data, Geom), "Expected %s, got %s" % (Geom, data.__class__)

    # is the radius set correctly?
    assert data.radius == 2.0, "Expected 2.0, got %s" % data.radius
    # how many spheres ?
    assert len(data.vertexSet.vertices) == 1, "expected %s got %s" % (
        1,
        len(data.vertexSet.vertices),
    )
    # is the center set correctly?
    array = data.vertexSet.vertices.array[0]
    assert (
        array[0] == array[1] == array[2] == -3
    ), "Expected -3 -3 -3 got array0: %s, array1: %s, array2: %s" % (
        array[0],
        array[1],
        array[2],
    )
    # was it correctly added to the viewer?
    assert (
        data in ViewerNode.vi.rootObject.children
    ), "data is: %s\nchildren are: %s" % (data, ViewerNode.vi.rootObject.children)
    # does it have a parent?
    assert data.parent is not None, "data.parent is: %s" % data.parent
    # does it know about the viewer?
    assert data.viewer is not None, "data.viewer is: %s" % data.viewer
    # is it visible?
    assert data.visible == True, "Expected True, got %s" % data.visible

    # delete connection from eval: [[-3 -3 -3]]
    net.deleteConnection(PointListNode, "result", SphereNode, "coords")
    # connect to eval: [[0,0,0],[3,0,0],[0,3,0.]]
    net.connectNodes(PointsListNode, SphereNode, portNode2="coords")
    data = SphereNode.outputPorts[0].data

    # is this a Spheres geom?
    assert data is not None, "Expected data, got %s" % data
    assert isinstance(data, Geom), "Expected %s, got %s" % (Geom, data.__class__)
    # how many spheres ?
    assert len(data.vertexSet.vertices) == 3, "expected %s got %s" % (
        3,
        len(data.vertexSet.vertices),
    )
    # is the radius set correctly?
    assert data.radius == 2.0, "Expected 2.0, got %s" % data.radius
    # is the center set correctly?
    array = data.vertexSet.vertices.array[0]
    assert (
        array[0] == array[1] == array[2] == 0
    ), "Expected 0 0 0 got array0: %s, array1: %s, array2: %s" % (
        array[0],
        array[1],
        array[2],
    )
    # was it correctly added to the viewer?
    assert (
        data in ViewerNode.vi.rootObject.children
    ), "data is: %s\nchildren are: %s" % (data, ViewerNode.vi.rootObject.children)
    # does it have a parent?
    assert data.parent is not None, "data.parent is: %s" % data.parent
    # does it know about the viewer?
    assert data.viewer is not None, "data.viewer is: %s" % data.viewer
    # is it visible?
    assert data.visible == True, "Expected True, got %s" % data.visible

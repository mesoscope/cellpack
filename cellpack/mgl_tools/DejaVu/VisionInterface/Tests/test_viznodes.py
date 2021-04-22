#########################################################################
#
# Date: Aug 2004  Authors: Daniel Stoffler
#
#       stoffler@scripps.edu
#
# Copyright: Daniel Stoffler, and TSRI
#
#########################################################################

import sys
from time import sleep
from Vision.VPE import VisualProgramingEnvironment

from DejaVu.VisionInterface.DejaVuNodes import vizlib, Spheres, Viewer

ed = None


def setUp():
    global ed
    ed = VisualProgramingEnvironment(
        name="test 3-D Visualization nodes",
        withShell=0,
        visibleWidth=400,
        visibleHeight=300,
    )
    ed.root.update()
    ed.configure(withThreads=0)
    ed.addLibraryInstance(vizlib, "DejaVu.VisionInterface.DejaVuNodes", "vizlib")
    ed.root.update()


def tearDown():
    ed.exit_cb()
    import gc

    gc.collect()


##########################
## Helper methods
##########################


def pause(sleepTime=0.1):
    from time import sleep

    ed.master.update()
    sleep(sleepTime)


##########################
## Tests
##########################


def test_01_SphereNode():
    """Test the Spheres node: create a sphere geom, add it to a viewer"""
    from Vision.StandardNodes import stdlib

    masterNet = ed.currentNetwork
    ed.addLibraryInstance(stdlib, "Vision.StandardNodes", "stdlib")
    ed.root.update()
    ## adding node Eval to generate 1 center for a sphere
    from Vision.StandardNodes import Eval

    node1 = Eval(constrkw={}, name="Sphere Center", library=stdlib)
    masterNet.addNode(node1, 233, 10)
    node1.inputPorts[0].widget.set("[(0.,0,0)]", 0)
    apply(node1.configure, (), {"expanded": True})
    ## adding node Sphere
    node2 = Spheres(constrkw={}, name="Sphere", library=vizlib)
    masterNet.addNode(node2, 29, 100)
    node2.inputPortByName["radius"].widget.set(9.5, 0)  # sphere radius
    node2.inputPortByName["quality"].widget.set(5, 0)  # sphere quality
    node2.inputPortByName["name"].widget.set("testSphere")  # sphere name
    apply(node2.configure, (), {"expanded": True})
    ## adding a node Viewer
    node3 = Viewer(constrkw={}, name="Viewer", library=vizlib)
    masterNet.addNode(node3, 264, 262)
    ## now connect the nodes
    masterNet.connectNodes(node1, node2, "result", "coords", blocking=True)
    masterNet.connectNodes(node2, node3, "spheres", "geometries", blocking=True)
    ## now run the network
    pause()
    masterNet.run()
    pause()
    ## finally, do some tests
    data = node2.outputPorts[0].data  # the sphere geom
    # is this a Spheres geom?
    assert data is not None, "Expected data, got %s" % data
    from DejaVu.Geom import Geom

    assert isinstance(data, Geom), "Expected %s, got %s" % (Geom, data.__class__)
    # is its name 'testSphere'?
    assert data.name == "testSphere", "Expected 'testSphere', got '%s'" % data.name
    # is the radius set correctly?
    assert data.radius == 9.5, "Expected 9.5, got %s" % data.radius
    # does it have oneRadius set to True?
    assert data.oneRadius == True, "Expected True, got %s" % data.oneRadius
    # is the quality set correctly?
    assert data.quality == 5, "Expected 5, got %s" % data.quality
    # was the center set correctly?
    array = data.vertexSet.vertices.array[0]
    assert (
        array[0] == array[1] == array[2] == 0.0
    ), "Expected 0.0, arry0: %s, arry1: %s, arr2: %s" % (array[0], array[1], array[2])
    # was it correctly added to the viewer?
    assert data in node3.vi.rootObject.children, "data is: %s\nchildren are: %s" % (
        data,
        node3.vi.rootObject.children,
    )
    # does it have a parent?
    assert data.parent is not None, "data.parent is: %s" % data.parent
    # does it know about the viewer?
    assert data.viewer is not None, "data.viewer is: %s" % data.viewer
    # is it visible?
    assert data.visible == True, "Expected True, got %s" % data.visible

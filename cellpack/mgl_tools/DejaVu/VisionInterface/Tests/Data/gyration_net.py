########################################################################
#
#    Vision Network - Python source code - file generated by vision
#    Tuesday 20 December 2005 14:00:56 
#    
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Daniel Stoffler, Michel Sanner and TSRI
#   
# revision: Guillaume Vareille
#  
#########################################################################
#
# $Header$
#
# $Id$
#

from traceback import print_exc

## loading libraries ##
from Vision.StandardNodes import stdlib
masterNet.getEditor().addLibraryInstance(stdlib,"Vision.StandardNodes", "stdlib")

from DejaVu.VisionInterface.DejaVuNodes import vizlib
masterNet.getEditor().addLibraryInstance(vizlib,"DejaVu.VisionInterface.DejaVuNodes", "vizlib")

try:

    ## saving node Viewer ##
    from DejaVu.VisionInterface.DejaVuNodes import Viewer
    Viewer_0 = Viewer(constrkw = {}, name='Viewer', library=vizlib)
    masterNet.addNode(Viewer_0,29,279)
except:
    print "WARNING: failed to restore Viewer named Viewer in network masterNet"
    print_exc()
    node0=None
try:

    ## saving node [[0,0,0],[1,0,0... ##
    from Vision.StandardNodes import Eval
    __0_0_0___1_0_0____1 = Eval(constrkw = {}, name='[[0,0,0],[3,0,0...', library=stdlib)
    masterNet.addNode(__0_0_0___1_0_0____1,15,8)
    __0_0_0___1_0_0____1.getInputPortByName("command").widget.set("[[0,0,0],[3,0,0],[0,3,0.]]")
    apply(__0_0_0___1_0_0____1.configure, (), {'expanded': True})
except:
    print "WARNING: failed to restore Eval named [[0,0,0],[3,0,0... in network masterNet"
    print_exc()
    node1=None
try:

    ## saving node Spheres ##
    from DejaVu.VisionInterface.GeometryNodes import Spheres
    Spheres_2 = Spheres(constrkw = {}, name='spheres', library=vizlib)
    masterNet.addNode(Spheres_2,73,174)
    Spheres_2.getInputPortByName('radius').unbindWidget()
    apply(Spheres_2.configure, (), {'expanded': True})
except:
    print "WARNING: failed to restore Spheres named Spheres in network masterNet"
    print_exc()
    node2=None
try:

    ## saving node Gyration Sphere ##
    from DejaVu.VisionInterface.DejaVuNodes import GyrationSphere
    Gyration_Sphere_3 = GyrationSphere(constrkw = {}, name='Gyration Sphere', library=vizlib)
    masterNet.addNode(Gyration_Sphere_3,91,84)
except:
    print "WARNING: failed to restore GyrationSphere named Gyration Sphere in network masterNet"
    print_exc()
    node3=None
try:

    ## saving node [[3,3,3]] ##
    from Vision.StandardNodes import Eval
    __3_3_3___4 = Eval(constrkw = {}, name='[[-3,-3,-3]]', library=stdlib)
    masterNet.addNode(__3_3_3___4,281,52)
    __3_3_3___4.getInputPortByName("command").widget.set("[[-3,-3,-3]]")
    apply(__3_3_3___4.configure, (), {'expanded': True})
except:
    print "WARNING: failed to restore Eval named [[-3,-3,-3]] in network masterNet"
    print_exc()
    node4=None
masterNet.freeze()

## saving connections for network gyration ##
if Gyration_Sphere_3 is not None and Spheres_2 is not None:
    masterNet.connectNodes(
        Gyration_Sphere_3, Spheres_2, "center", "coords", blocking=True)
if Gyration_Sphere_3 is not None and Spheres_2 is not None:
    masterNet.connectNodes(
        Gyration_Sphere_3, Spheres_2, "radius", "radius", blocking=True)
if __0_0_0___1_0_0____1 is not None and Gyration_Sphere_3 is not None:
    masterNet.connectNodes(
        __0_0_0___1_0_0____1, Gyration_Sphere_3, "result", "coords", blocking=True)
if Spheres_2 is not None and Viewer_0 is not None:
    masterNet.connectNodes(
        Spheres_2, Viewer_0, "spheres", "geometries", blocking=True)
masterNet.unfreeze()

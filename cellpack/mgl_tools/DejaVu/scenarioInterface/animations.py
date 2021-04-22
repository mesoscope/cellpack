"""
This module provide objects building DejaVu animation in the form of
MultipleActorsActions objects
"""

import math, numpy, copy

from Scenario2.multipleActorsActions import MultipleActorsActions, MAAGroup
from Scenario2.keyframes import KFValueFromFunction, KFAutoCurrentValue, \
     Interval, KF
from Scenario2.interpolators import matToQuaternion

from DejaVu import Viewer
from DejaVu.scenarioInterface import getActor
from DejaVu.scenarioInterface.actor import RedrawActor
from DejaVu.scenarioInterface.actor import DejaVuAxisConcatRotationActor
from DejaVu.states import getRendering, getOrientation, setRendering

from mglutil.math.rotax import rotax
from mglutil.util.callback import CallbackFunction
import types


## For an MAA object ot be editable the folllowing conditions must be met:
## 1 - the MAA has a .editorClass set to the class of the editor for this MAA
## 2 - the folloing method have to work
##     MAA.getValues()
##     MAAEditor.setValues(**kw)
##     MAAEditor.getValues() 
##     MAAEditor.execute(self, name) has to configure self.maa 
##        with the current parameters (MAAEditor.getValues() )


def expandGeoms(geoms):
    newgeoms = []
    try:
        len(geoms)
    except:
        geoms = [geoms]
    for g in geoms:
        allObjects = g.AllObjects()
        if len(allObjects) == 1 and len(allObjects[0].getVertices())>0 :
            newgeoms.append(allObjects[0])
        else:
            for child in allObjects:
                if len(child.getVertices())>0 and child.visible:
                    newgeoms.append( child )
    return newgeoms

def getObjectName(objects):
    """Create a string representing the objects name.
    objects - list of one or more DejaVu geom. objects"""
    name = ""
    for object in objects:
        try:
            objectName = object.fullName
            if objectName.split("|")[-1] != 'root':
                if objectName.find('root') == 0:
                    if not len(name):
                        name = objectName[5:]
                    else:
                        name = name + ";" + objectName[5:]
                    break
        except:
            pass
    return name


def getObjectFromString(objects):
    objectFromString = None
    try:
        objectFromString = "["
        for object in objects:
            objectFromString =  objectFromString + "viewer.FindObjectByName('%s'), " % object.fullName
        objectFromString = objectFromString + "]"
    except:
        objectFromString = None
    return objectFromString


def numarr2str(val):
    """Returns a string representing the input numeric array"""
    assert type(val) == numpy.ndarray
    dims = val.shape
    if len(dims) == 1:
        _valstr = "%.4f,"*dims[0] % tuple(val)
        valstr = "array([" + _valstr + "], '%s')" % val.dtype.char
    elif len(dims) == 2:
         _valstr = ("[" + "%.4f," * dims[1] +"],") * dims[0] % tuple(val.flatten())
         valstr = "array([" + _valstr + "], '%s')" % val.dtype.char
    else:
        threshold = numpy.get_printoptions()["threshold"]
        numpy.set_printoptions(threshold=val.size)
        valstr = "array(" + numpy.array2string(val, precision =4, separator =",") + ", '%s')"%val.dtype.char
        #valstr.replace("\n", "\n\t")
        numpy.set_printoptions(threshold=threshold)
    return valstr


def comparefloats(a, b, precision = 0.0001 ):
    """Compare two float scalars or arrays"""

    aa = numpy.ravel(numpy.array(a))
    bb = numpy.ravel(numpy.array(b))
    if len(aa) == len(bb) == 0: return True
    if len(aa) != len(bb): return False
    diff = numpy.abs(aa-bb)
    if diff.max() > precision: return False
##     mask0 = aa == 0
##     masknz = aa != 0.
##     if numpy.any(mask0):
##         if diff[mask0].max()> 0.:
##             return False
##     if numpy.any(masknz):
##         if (diff[masknz]/aa[masknz]).max() > precision:
##             return False
    return True


##
##  MAA building classes
##
from DejaVu.Spheres import Spheres
from DejaVu.Cylinders import Cylinders
from DejaVu.IndexedGeom import IndexedGeom
from time import time
class RenderingTransitionMAA(MultipleActorsActions):
    """
    MMA containing a RedrawActor for a DejaVu Viewer and actors to
    morph between representations
    """

    def __init__(self, viewer, rendering = None, kfpos=[0,30], name='morphRepr',
                 startFlag='after previous', saveAtomProp=True):
        """
        constructor

        MAA <- RenderingTransitionMAA(viewer, name='morphRepr',
                                      startFlag='after previous')

        viewer is a DejaVu Viewer Object
        name is a string used to name this RedrawMAA
        startFlag - flag used in a sequence animator for computing time
                    position of the maa .
        the MultipleActorsActions (MAA) is built with a RedrawActor for the
        viewer. The name of the RedrawActor name is 'redraw'+viewer.uniqID.
        """
        assert isinstance(viewer, Viewer)
        MultipleActorsActions.__init__(self, name=name, startFlag=startFlag)
        redrawActor = RedrawActor(viewer)
        self.viewer = viewer
        self.redrawActor = self.addActor(redrawActor)
        self.forceRendering = False
        self.rendering = rendering
        self.sortPoly = 'Never'
        self.editorClass = None
        self.kfpos = kfpos
        self.firstPosition = kfpos[0]
        self.lastPosition = kfpos[1]
        self._maaGroup = None # will be a weakref to MAAGroup
        self.atomSets = {}
        self.msmsPtrs = {}
        self._animNB = None
        if saveAtomProp:
            try:
                self.saveGeomAtomProp()
            except:
                pass



    def makeMAA(self, rendering, kfpos):

        self.kfpos = kfpos
        if not self.rendering:
            return
        # build list of differences
        r1 = rendering
        r2 = self.rendering
        viewer = self.viewer

        if kfpos[-1] - kfpos[0] == 1:
            from DejaVu.scenarioInterface.actor import DejaVuActor
            actor = DejaVuActor("viewer.rendering", viewer.rootObject,
                                setFunction=lambda actor, val:setRendering(actor.object.viewer, val) )
            #kf1 = KF(self.kfpos[-1], r2)
            kf1 = KF(self.kfpos[0], r2)
            actor.actions.addKeyframe(kf1)
            
            self.AddActions( actor, actor.actions )
            return
        
        modDict = {}
        appear = []
        disappear = []
        
        for g in viewer.rootObject.AllObjects():
            #print 'IIIIIIIIIIIIII', g.name
            r1g = r1.get(g.fullName, None)
            r2g = r2.get(g.fullName, None)
            if r1g is None and r2g is None:
                continue

            if r1g is not None and r2g is not None and \
                   r1g['visible']==0 and r2g['visible']==0:
                continue

            elif r1g is None:
                #print "1111, add to appear", g.name
                appear.append(g)
            elif r1g['visible'] == 0:
                if r2g is not None : # g appears
                    mod = self.compareGeomState(r1g,r2g)
                    if mod.has_key('vertices') or mod.has_key('faces'):
                        modDict[g] = mod
                    else:
                        #print "2222, add to appear",  g.name
                        appear.append(g)
            elif r2g is None:
                ff = r1g.get('faces', None)
                if ff is not None:
                    if len(ff) != 0:
                        #print "3333 add to disappear", g.name
                        disappear.append(g)
                else:
                    vv = r1g.get('vertices', None)
                    if vv is not None and len(vv) != 0:
                        #print "4444 add to disappear", g.name
                        disappear.append(g)
            elif r2g['visible']==0: # g disappears
                #print "5555 add to disappear", g.name
                disappear.append(g)

            else:
                mod = self.compareGeomState(r1g,r2g)
                if len(mod):
                    modDict[g] = mod

        # create actors for objects that appear
        for obj in appear:
            #print 'APPEAR', obj.name
            self.appear(obj)
                
        # create actors for objects that disappear
        for obj in disappear:
            #print 'DISAPPEAR', obj.name
            self.disappear(obj)
        
        # loop over geometries and their modes:
        for g,mod in modDict.items():
            scissorvals = {}
            keys = mod.keys()
            gname = g.fullName
            #print 'JJJJJJJJJJJJJJJJJ', gname, keys
            if mod.has_key('vertices'):
                #print "VERTICES"
                # create actors for "Spheres" or "Indexed Geoms" objects that  have different vertex sets
                # in rendering 1 and 2
                if (isinstance(g, Spheres) or isinstance(g, IndexedGeom)):
                    visibleactor = getActor(g, 'visible')
                    kf1 = KF(self.kfpos[0], 1)
                    visibleactor.actions.addKeyframe(kf1)
                    self.AddActions( visibleactor, visibleactor.actions )
                    
                    # we are going to create 3 keyframes.
                    # first keyframe sets the vertex union of both renderings(and corresponding values for colors, opacity, radii and faces)
                    #second keyframe sets opacity and colors .
                    #The opacity and colors are interpolated between two first frames ,
                    #so that the object in rendering 1 is fading out while the object in rendering 2
                    # is fading in .
                    # Last keyframe sets the vertices (and faces) of the second (destination) rendering.
                    
                    val1 = {} # first keyframe values
                    val3 = {} #last (third) keyframe values

                    vv1 = mod['vertices'][1]  # vertices of the first rendering
                    vv2 = mod['vertices'][2]  # vertices of the second rendering
                    nvert1 = len(vv1)
                    nvert2 = len(vv2)
                    # 'radii'
                    radiiactor = None
                    rad1 = rad2 = None
                    if r1[gname].has_key("radii"):
                        radiiactor = getActor(g, "radii")
                        rad1 = r1[gname]["radii"]
                        rad2 = r2[gname]["radii"]
                        val3['radii'] =  rad2
                    # 'colors'
                    col1 = numpy.array(r1[gname]["rawMaterialF"]["diffuse"], numpy.float32)[:,:3]
                    ncol1 = len(col1)
                    if ncol1 == 1 or ncol1 != nvert1:
                        col1 = numpy.array([col1[0]] *nvert1 ,'f')
                    col2 = numpy.array(r2[gname]["rawMaterialF"]["diffuse"], numpy.float32)[:,:3]
                    ncol2 = len(col2)
                    if ncol2 == 1 or ncol2 != nvert2:
                        col2 = numpy.array([col2[0]] *nvert2 ,'f')
                    #'opacity'
                    #op1 = numpy.array(r1[gname]["rawMaterialF"]['opacity'], "f")
                    op1 = numpy.array(r1[gname]["rawMaterialF"]['diffuse'], "f")[:,3]
                    if len(op1) != nvert1:
                            op1 = numpy.ones(nvert1).astype('f')
                    if len(op1) == 1:
                        n = op1[0]
                        op1 = numpy.ones(nvert1).astype('f')*n
                    #op2 = numpy.array(r2[gname]["rawMaterialF"]['opacity'], "f")
                    op2 = numpy.array(r2[gname]["rawMaterialF"]['diffuse'], "f")[:,3]
                    if len(op2) != nvert2:
                            op2 = numpy.ones(nvert2).astype('f')
                    if len(op2) == 1:
                        n = op2[0]
                        op2 = numpy.ones(nvert2).astype('f')*n
                    vis1 = r1[gname].get('visible')
                    
                    #get values for the first two keyframes
                    if  isinstance(g, Spheres):
                        # get arrays of vertices, faces, radii, opacities , colors for
                        # the first keyframe  and arrays of opacities and colors for
                        # the second keyframe 
                        verts1, radii, opacity1, opacity2, colors1, colors2 =\
                                self.getSpheresTransitionValues(g, vv1, vv2, op1, op2,
                                                                col1, col2, rad1, rad2,
                                                                visible1 = vis1)
                    else: # IndexedGeom
                        f1 = numpy.array(r1[gname]["faces"], 'f')
                        f2 = numpy.array(r2[gname]["faces"], 'f')
                        if len(f1) and len(f2):
                            # get arrays of vertices, faces, radii, opacities , colors for
                            # the first keyframe  and arrays of opacities and colors for
                            # the second keyframe 
                            verts1, faces1, radii, opacity1, opacity2, colors1, colors2 = \
                                    self.getIndGeomsTransitionValues(g, vv1, vv2, op1, op2,
                                                                      col1, col2, f1, f2,
                                                                      rad1, rad2, visible1 = vis1)
                            val3['faces'] = f2
                        elif len(f1) == 0:
                            verts1 = vv2; faces1 = f2
                            radii = rad2
                            colors1 = col2; colors2 = None
                            opacity1 = [0]; opacity2 = op2
                            val3 = None
                        elif len(f2) == 0:
                            verts1 = vv1; faces1 =  f1
                            radii = rad1
                            colors1 = col1; colors2 = None
                            opacity1 = op1; opacity2 = [0]
                            val1['faces'] = f1
                        val1['faces'] = faces1
                        
                    #keyframe values for Spheres and Indexed Geoms:
                    
                    val1['vertices'] = verts1
                    if radii is not None:
                        val1['radii'] = radii
                    if colors2 is None:
                        val1["materials"] = colors1
                    matkw = {"redo":1, "tagModified":False, "transparent": 'implicit', "inheritMaterial":0}
                    val1.update(matkw)
                    if val3 is not None:
                        val3['vertices'] =  vv2
                        val3["materials"] = col2
                        val3.update(matkw)

                        
                    ### ACTORS: ######    
                    # create actor that calls g.Set() method to set vertices, faces,
                    # radii and colors of the geometry:
                    from DejaVu.scenarioInterface.actor import DejaVuActor
                    setactor = DejaVuActor("%s.setactor"% (g.fullName,) , g,
                             setFunction=lambda actor, val: actor.object.Set(**val) )             

                    kf0 = KF(self.kfpos[0], val1)
                    setactor.actions.addKeyframe(kf0)
                    if val3:
                        kf1 = KF(self.kfpos[1], val3)
                        setactor.actions.addKeyframe(kf1)
                    self.AddActions( setactor, setactor.actions )
                    
                    # opacity actor 
                    opacactor = getActor(g, 'opacity')
                    kf1 = KF(self.kfpos[0], opacity1)
                    kf2 = KF(self.kfpos[1]-1, opacity2)
                    i1 = Interval( kf1, kf2, generator=opacactor.behaviorList)
                    opacactor.addIntervals( [i1] )
                    kf3 = KF(self.kfpos[1], op2)
                    opacactor.actions.addKeyframe(kf3)
                    self.AddActions( opacactor, opacactor.actions )
                    if colors2 is not None:
                        
                        # add color actor:
                        coloractor = getActor(g, 'colors')
                        kf1 = KF(self.kfpos[0], colors1)
                        kf2 = KF(self.kfpos[1]-1, colors2)
                        i1 = Interval( kf1, kf2, generator=coloractor.behaviorList)
                        coloractor.addIntervals( [i1] )
                        self.AddActions( coloractor, coloractor.actions )
                        
                    # depthMask actor
                    depthactor = getActor(g, 'depthMask')
                    kf0 = KF(self.kfpos[0], 0)
                    kf1 = KF(self.kfpos[1], depthactor.getValueFromObject())
                    depthactor.actions.addKeyframe(kf0)
                    depthactor.actions.addKeyframe(kf1)
                    self.AddActions( depthactor, depthactor.actions )
                    
                    if self.msmsPtrs.has_key(g.fullName):
                        self.msmsPtrs[g.fullName][1] = True

            elif mod.has_key("faces"):
                # create actors for objects that appear through faces
                #print "FACES"
                v1 = mod["faces"][1]
                v2 = mod["faces"][2]
                #print "JJJJJJJ1 faces"
                if len(v1)==0:
                    #print 'APPEAR1', g.name
                    if  len(r1[gname].get('vertices',[])) > 0:
                        facesactor = getActor(g, 'faces')
                        kf0 = KF(self.kfpos[0], v2)
                        facesactor.actions.addKeyframe(kf0)
                        self.AddActions( facesactor, facesactor.actions )
                    self.appear(g)

                elif len(v2)==0:
                    #print 'DISAPPEAR1', g.name
                    facesactor = getActor(g, 'faces')
                    kf0 = KF(self.kfpos[0], v1)
                    facesactor.actions.addKeyframe(kf0)
                    self.AddActions( facesactor, facesactor.actions )
                    self.disappear(g)
                else:
                    vv1 = r1[gname].get('vertices',[])
                    vv2 = r2[gname].get('vertices',[])
                    nvert1 = len(vv1)
                    nvert2 = len(vv2)
                    if nvert1 == 0 or nvert2 == 0: continue
                    visibleactor = getActor(g, 'visible')
                    kf1 = KF(self.kfpos[0], 1)
                    visibleactor.actions.addKeyframe(kf1)
                    self.AddActions( visibleactor, visibleactor.actions )
                    #origop1 = r1[gname]["rawMaterialF"]['opacity']
                    origop1 = numpy.array(r1[gname]["rawMaterialF"]['diffuse'], "f")[:,3]
                    if len(origop1) == 1:
                        n = origop1[0]
                        origop1 = numpy.ones(nvert1).astype('f')*n
                    elif len(origop1) != nvert1:
                        origop1 = numpy.ones(nvert1).astype('f')

                    #origop2 = r2[gname]["rawMaterialF"]['opacity']
                    origop2 = numpy.array(r2[gname]["rawMaterialF"]['diffuse'], "f")[:,3]
                    if len(origop2) == 1:
                        n = origop2[0]
                        origop2 = numpy.ones(nvert1).astype('f')*n

                    elif len(origop2) != nvert2:
                        origop2 = numpy.ones(nvert2).astype('f')

                    op1 = numpy.zeros(nvert1).astype('f')
                    op2 = numpy.zeros(nvert1).astype('f')

                    # create fast lookup for vertices in v2
                    v2key = {}.fromkeys(v2.flatten().tolist())
                        

                    if r1[gname].get('visible') == 1:
                        # create fast lookup for vertices in v1
                        v1key = {}.fromkeys(v1.flatten().tolist())
                        for i in xrange(nvert1):
                            if v1key.has_key(i):
                                op1[i] = origop1[i]
                            if v2key.has_key(i):
                                op2[i] = origop2[i]
                    else:
                        for i in range(nvert1):
                            if v2key.has_key(i):
                                op2[i] = origop2[i]

                    facesactor = getActor(g, 'faces')
                    kf0 = KF(self.kfpos[0], numpy.concatenate((v1, v2)) )
                    facesactor.actions.addKeyframe(kf0)
                    kf1 = KF(self.kfpos[1], v2)
                    facesactor.actions.addKeyframe(kf1)
                    self.AddActions( facesactor, facesactor.actions )
                    
                    opacactor = getActor(g, 'opacity')
                    kf1 = KF(self.kfpos[0], op1)
                    kf2 = KF(self.kfpos[1], op2)
                    i1 = Interval( kf1, kf2, generator=opacactor.behaviorList)
                    opacactor.addIntervals( [i1] )
                    self.AddActions( opacactor, opacactor.actions )
                    # the following color setting is done if the geometry
                    # has one color. In this case setting opacity per vertex does not work
                    # properly_> create array of color - same color per vertex.
                    # 
                    # destination color
                    col2 = r2[gname]["rawMaterialF"]["diffuse"]
                    if len(col2)==1:
                        _col2 = numpy.ones(nvert1*4, 'f').reshape(nvert1, 4)
                        _col2 = _col2 * col2[0]
                        r2[gname]["rawMaterialF"]["diffuse"] = _col2.tolist()
                    # get current color of the object:
                    col1 = g.materials[1028].prop[1][:, :3]
                    if len(col1):
                        _col1 = numpy.ones(nvert1*3, 'f').reshape(nvert1, 3)
                        _col1 = _col1 * col1[0]
                        g.Set(materials=_col1, tagModified=False, transparent='implicit',
                              inheritMaterial=0)
                    
            # actors for other parameters     
            from DejaVu.scenarioInterface.actor import getActorName
            for k, _mod in mod.items():
                typ, v1, v2 = _mod
                if k in ["rawMaterialF", "rawMaterialB"]:
                    if mod.has_key('vertices'): continue
                    col1 = numpy.array(v1["diffuse"], numpy.float32)[:,:3]
                    col2 = numpy.array(v2["diffuse"], numpy.float32)[:,:3]
                    l1 = len(col1)
                    l2 = len(col2)
                    if (l1 == l2 and comparefloats(col1,col2) == False) or (l1 == 1 and l2 != 1) or (l2 == 1 and l1 != 1):
                        aname = "colors"
                        if k == "rawMaterialB": aname = "colorsB"
                        coloractor = self.createActor(g, aname, col1, col2)
                        if not self.findActor(coloractor):
                            self.AddActions( coloractor, coloractor.actions )
                    mater1 = [v1['ambient'], v1['emission'], v1['specular'], v1['shininess']]
                    mater2 = [v2['ambient'], v2['emission'], v2['specular'], v2['shininess']]
                    materialactor = getActor(g, "material")
                    if materialactor is not None:
                        if materialactor.compareValues(mater1, mater2) == False:
                            if k == "rawMaterialB": materialactor.mode = "back"
                            kf1 = KF(self.kfpos[0], mater1)
                            kf2 = KF(self.kfpos[1], mater2)
                            i1 = Interval( kf1, kf2, generator = materialactor.behaviorList)
                            materialactor.addIntervals( [i1] )
                            self.AddActions( materialactor, materialactor.actions )
                    
                    if not self.findActor(getActorName(g,'opacity')):
                        opac1 = v1['opacity']
                        opac2 = v2['opacity']
                        if not comparefloats(opac1, opac2):
                            aname = 'opacityF'
                            if  k == "rawMaterialB": aname = 'opacityB'
                            opacactor = getActor(g, aname)
                            kf1 = KF(self.kfpos[0], opac1)
                            kf2 = KF(self.kfpos[1], opac2)
                            i1 = Interval( kf1, kf2, generator=opacactor.behaviorList)
                            opacactor.addIntervals( [i1] )
                            self.AddActions( opacactor, opacactor.actions )
                elif k in ['scissorH', 'scissorW', 'scissorX', 'scissorY']:
                   scissorvals[k] = [v1, v2]
                elif k in ['pointWidth', 'lineWidth', 'quality']:
                    intactor = self.createActor(g, k, v1, v2)
                    if intactor is not None:
                        self.AddActions(intactor, intactor.actions)
                elif k == "radii":
                    radactor = self.createActor(g, "radii", v1, v2)
                    if not self.findActor(radactor):
                        self.AddActions(radactor, radactor.actions)
                elif k in [
                    'inheritStippleLines', 'stippleLines', 'disableStencil',
                    'immediateRendering', 'inheritLighting',
                    'invertNormals', 'outline', 'inheritPointWidth', 'pickable',
                    'stipplePolygons', 'pickableVertices', 'depthMask',
                    'inheritSharpColorBoundaries', 'lighting', 'inheritCulling',
                    'inheritShading',  'sharpColorBoundaries',
                    'inheritFrontPolyMode', 'inheritStipplePolygons', 'scissor',
                    'inheritBackPolyMode', 'inheritLineWidth', 'inheritMaterial',
                    'inheritXform']: # ,'visible', 'transparent',]:
                    from DejaVu.scenarioInterface.actor import DejaVuActor
                    from Scenario2.interpolators import BooleanInterpolator
                    from Scenario2.datatypes import BoolType
                    if k == "depthMask":
                        if self.findActor(getActorName(g, "depthMask")):
                            continue
                    boolactor =  DejaVuActor(k, g, interp=BooleanInterpolator, datatype=BoolType)
                    kf1 = KF(self.kfpos[0], v1)
                    kf2 = KF(self.kfpos[1], v2)
                    i1 = Interval( kf1, kf2, generator = boolactor.behaviorList)
                    boolactor.addIntervals( [i1] )
                    self.AddActions( boolactor, boolactor.actions )
                # ends  "for" loop
                
            if len(scissorvals):
                scissoractor = getActor(g, 'scissorResize')
                if scissoractor is not None:
                    val1 = scissoractor.getValue()
                    val2 = scissoractor.getValue()
                    for i, var in enumerate (scissoractor.varnames):
                        if scissorvals.has_key(var):
                            val1[i]= scissorvals[var][0]
                            val2[i]= scissorvals[var][1]
                    kf1 = KF(self.kfpos[0], val1)
                    kf2 = KF(self.kfpos[1], val2)
                    i1 = Interval( kf1, kf2, generator = scissoractor.behaviorList)
                    scissoractor.addIntervals( [i1] )
                    self.AddActions(scissoractor, scissoractor.actions)
        cammod = {}
        if r1.has_key('camera') and r2.has_key('camera'):
            cammod = self.compareCameraState(r1['camera'], r2['camera'])
        if len(cammod):
            camera = viewer.cameras[0]
##             if cammod.has_key('near') and cammod.has_key('far'):
##                 val1 = [cammod['near'][1], cammod['far'][1]]
##                 val2 = [cammod['near'][2], cammod['far'][2]]
##                 camclipzactor = self.createActor(camera, 'clipZ',val1, val2)
##                 if camclipzactor is not None:
##                     self.AddActions(camclipzactor,camclipzactor.actions)
##                 cammod.pop('near')
##                 cammod.pop('far')
            for k, val in cammod.items():
                if k == 'color':
                    camcoloractor = self.createActor(camera, 'backgroundColor', val[1], val[2])
                    if camcoloractor is not None:
                        self.AddActions(camcoloractor, camcoloractor.actions)
                elif k in ['height', 'width', 'antialiased', 'boundingbox',
                           'projectionType','drawThumbnail','contours']:
                    camactor = getActor(camera, k)
                    if camactor is not None:
                        kf1 = KF(self.kfpos[0], val[1])
                        kf2 = KF(self.kfpos[1], val[2])
                        camactor.actions.addKeyframe(kf1)
                        camactor.actions.addKeyframe(kf2)
                        self.AddActions( camactor, camactor.actions )
                elif k in ['near', 'far']:
                    camactor = self.createActor(camera, k, val[1], val[2])
                    if camactor is not None:
                        self.AddActions( camactor, camactor.actions )
                        
            #if self._maaGroup is not None:
            #    self._maaGroup().makeActorList()
            

                
                        
    def appear(self, obj):
        #print "APPEAR", obj.name
        # ?? sortPoly can be set in the maa editor.
        # Do we need to make set it here ??
        
        #self.sortPoly = 'Always'
        #if self._maaGroup:
        #    self._maaGroup().sortPoly = 'Always'
        visibleactor = getActor(obj, 'visible')
        kf1 = KF(self.kfpos[0], 1)
        visibleactor.actions.addKeyframe(kf1)

        depthactor = getActor(obj, 'depthMask')
        kf0 = KF(self.kfpos[0], 0)
        kf1 = KF(self.kfpos[1], depthactor.getValueFromObject())
        depthactor.actions.addKeyframe(kf0)
        depthactor.actions.addKeyframe(kf1)
        #actors = [visibleactor, depthactor]
        actors = [depthactor]
        opacityactorF = None
        if len(obj.vertexSet):
            opacityactorF = getActor(obj, 'opacity')
            kf1 = KF(self.kfpos[0], 0.)
            opacF = numpy.array(self.rendering[obj.fullName]["rawMaterialF"]['diffuse'], "f")[:,3]
            kf2 = KF(self.kfpos[1], opacF)
            i1 = Interval( kf1, kf2, generator=opacityactorF.behaviorList)
            opacityactorF.addIntervals( [i1] )
            actors.append( opacityactorF )

##             opacityactorB = getActor(obj, 'opacityB')
##             kf1 = KF(self.kfpos[0], 0.)
##             opacB = numpy.array(self.rendering[obj.fullName]["rawMaterialB"]['diffuse'], "f")[:,3]
##             kf2 = KF(self.kfpos[1], opacB)
##             i1 = Interval( kf1, kf2, generator=opacityactorB.behaviorList)
##             opacityactorB.addIntervals( [i1] )
##             actors.append( opacityactorB )
            
        if self.rendering.has_key(obj.fullName):
            from copy import deepcopy
            r = deepcopy(self.rendering[obj.fullName])
            if opacityactorF and r.has_key("rawMaterialF"):
                r["rawMaterialF"]["opacity"] = [0]
            if r.has_key('inheritMaterial'):
                r['inheritMaterial'] = 0
            if r.has_key("depthMask"):
                r.pop("depthMask")
            ractor =  getActor(obj ,'rendering')
            kf0 = KF(self.kfpos[0], r)
            ractor.actions.addKeyframe(kf0)
            actors.append(ractor)
            
        actors.append(visibleactor)
            
        for actor in actors:
            if actor.actions is not None:
                self.AddActions( actor, actor.actions )

                           
    def disappear(self, obj):
        # ?? sortPoly can be set in the maa editor.
        # Do we need to make set it here ??
        #self.sortPoly = 'Always'
        #if self._maaGroup:
        #    self._maaGroup().sortPoly = 'Always'
        visibleactor = getActor(obj, 'visible')
        kf0 = KF(self.kfpos[0], 1.) # visible at the begining
        kf1 = KF(self.kfpos[1], 0) # not visible at the end
        visibleactor.actions.addKeyframe(kf0)
        visibleactor.actions.addKeyframe(kf1)

        depthactor = getActor(obj, 'depthMask')
        #kf0 = KF((self.kfpos[0]+self.kfpos[1])/2, 0)
        kf0 = KF(self.kfpos[0], 0)
        kf1 = KF(self.kfpos[1], depthactor.getValueFromObject())
        depthactor.actions.addKeyframe(kf0)
        depthactor.actions.addKeyframe(kf1)
        actors = [visibleactor, depthactor]
        #actors = [visibleactor]

        if len(obj.vertexSet):
            opacityactorF = getActor(obj, 'opacity')
            originalOpac = opacityactorF.getValueFromObject()[0]
            kf1 = KF(self.kfpos[0], originalOpac)
            kf2 = KF(self.kfpos[1], 0.)
            i1 = Interval( kf1, kf2, generator=opacityactorF.behaviorList)
            opacityactorF.addIntervals( [i1] )
            #kf3 = KF(self.kfpos[1]+1, originalOpac) # restore opac
            #opacityactor.actions.addKeyframe(kf3)
            actors.append( opacityactorF )

##             opacityactorB = getActor(obj, 'opacityB')
##             originalOpac = opacityactorB.getValueFromObject()[0]
##             kf1 = KF(self.kfpos[0], originalOpac)
##             kf2 = KF(self.kfpos[1], 0.)
##             i1 = Interval( kf1, kf2, generator=opacityactorB.behaviorList)
##             opacityactorB.addIntervals( [i1] )
##             actors.append( opacityactorB )

        for actor in actors:
            if actor.actions is not None:
                self.AddActions( actor, actor.actions )


    def createActor(self, object, actorName, val1, val2):
        actor = getActor(object, actorName)
        if actor is not None:
            kf1 = KF(self.kfpos[0], val1)
            kf2 = KF(self.kfpos[1], val2)
            i1 = Interval( kf1, kf2, generator = actor.behaviorList)
            actor.addIntervals( [i1] )
        return actor

    def setValuesAt(self, frame, off=0, actor=None):
        if frame == off + self.firstPosition:
            if len(self.actors) >1:
                self.removeNonRedrawActors()
            #print self, "setValuesAt, makeMAA"
            self.makeMAA(getRendering(self.viewer, checkAnimatable=True), self.kfpos)
            if self._director is not None:
                self._director().updateEndFrame()
        MultipleActorsActions.setValuesAt(self, frame, off, actor)
        

    def removeNonRedrawActors(self):
        """
        remove all actors except for redraw actors.
        """
        # use by subclasses then they want to rebuild the MAA
        keptActors = []
        for actor in self.actors:
            if isinstance(actor, RedrawActor):
                keptActors.append( actor)
        self.actors = keptActors
        
    def compareGeomState(self, s1, s2):
        mod = {}
        for k in s1.keys():
            # list of states that are skipped
            if k in ['protected', 'replace', 'listed', 'vertexArrayFlag',
                     'needsRedoDpyListOnResize', 'vnormals',  #'vertices',
                     'fnormals', '',]:
                continue
            elif k == "vertices":
                vv1 = s1[k]
                vv2 = s2[k]
                nvert1 = len(vv1)
                nvert2 = len(vv2)
                if nvert1 == 0 or nvert2 == 0: continue
                if nvert1 != nvert2:
                    mod[k] = ('vertices', vv1, vv2) 
                else:
                    #if numpy.alltrue(numpy.equal(vv1, vv2)) != True:
                    if not comparefloats(vv1, vv2): 
                        mod[k] = ('vertices', vv1, vv2)
            elif k in ['faces']:
                if len(s1[k])!=len(s2[k]):
                    mod[k] = ('faces', s1[k], s2[k] )
                elif len(s1[k]) == len(s2[k]) == 0: continue
                else:
                    n = len(s1[k][0])
                    fs = n*"%i,"
                    facedic2 = dict([(fs % tuple(f),None) for f in s2[k]])
                    for f in s1[k]:
                        if not facedic2.has_key(fs % tuple(f)):
                            mod[k] = ("faces", s1[k], s2[k])
                            break

            elif k in [
                'inheritStippleLines', 'stippleLines', 'disableStencil',
                'visible', 'immediateRendering', 'inheritLighting',
                'invertNormals', 'outline', 'inheritPointWidth', 'pickable',
                'stipplePolygons', 'pickableVertices', 'depthMask',
                'inheritSharpColorBoundaries', 'lighting', 'inheritCulling',
                'inheritShading', 'transparent', 'sharpColorBoundaries',
                'inheritFrontPolyMode', 'inheritStipplePolygons', 'scissor',
                'inheritBackPolyMode', 'inheritLineWidth', 'inheritMaterial',
                'inheritXform']:
                if s1[k]!=s2[k]:
                    mod[k]= (bool, s1[k], s2[k] )
                    
            elif k in ['quality', 'scissorH', 'scissorX', 'scissorY',
                       'pointWidth', 'scissorW', 'lineWidth' ]:
                if s1[k]!=s2[k]:
                    mod[k]= (int, s1[k], s2[k])
            elif k in ['scissorAspectRatio']:
                if s1[k]!=s2[k]:
                    mod[k] =(float, s1[k], s2[k] )
            elif k in ['frontPolyMode', 'shading', 'culling', 'backPolyMode']:
                if s1[k]!=s2[k]:
                    mod[k]= (str, s1[k], s2[k]) 
            elif k in ['rawMaterialF', 'rawMaterialB']:
                if s1[k]!=s2[k]:
                    mod[k] = ('material', s1[k], s2[k]) 
            elif k in ['instanceMatricesFromFortran']:
                if s1[k]!=s2[k]:
                    mod[k] = ('instances', s1[k], s2[k]) 
            elif k in ['blendFunctions']:
                if s1[k]!=s2[k]:
                    mod[k] = (tuple, s1[k], s2[k])
            elif k == "radii":
                if type(s1[k])==numpy.ndarray:
                    #if len(s1[k]) != len(s2[k]) or numpy.alltrue(numpy.equal(s1[k], s2[k])) != True:
                    if len(s1[k]) != len(s2[k]) or comparefloats(s1[k], s2[k]) != True:
                        mod[k] = ("radii", s1[k], s2[k])
                else:
                    if s1[k]!=s2[k]:
                        mod[k]= ("radii", s1[k], s2[k])
                        
            #else:
            #    print 'SKIPPED', k
        return mod

    def compareCameraState(self, s1, s2):
        mod = {}
        for k in s1.keys():
            # list of states that are skipped
            if k in ['rotation', 'translation','scale','pivot',
                     'direction','lookAt', 'height', 'width', 'near', 'far']:
                continue
            elif k in ['antialiased', 'boundingbox', 'projectionType',
                       'drawThumbnail','contours']: 
                if s1[k] != s2[k]:
                    mod[k]= (int, s1[k], s2[k])
            elif k == 'color':
                if not comparefloats(s1[k], s2[k]):
                    mod[k]= (tuple, s1[k], s2[k])
        return mod

    def getSourceCode(self, varname, indent=0, saverendering=True):
        """
        Return python code creating this object
        """
        tabs = " "*indent
        lines = tabs + """import tkMessageBox\n"""
        lines += tabs + """from DejaVu.scenarioInterface.animations import RenderingTransitionMAA\n"""
        if saverendering and self.rendering is not None:
            lines += tabs + """from numpy import *\n"""
            #import numpy, types
            # avoid array summarization in the string (ex: "[0, 1, 2, ..., 7, 8, 9]" )
##             oldopts = numpy.get_printoptions()
##             maxlen = oldopts["threshold"]
##             for val in self.rendering.values():
##                 if type(val) == types.DictType:
##                     for val1 in val.values():
##                         if  type(val1) == numpy.ndarray:
##                             maxlen = max(maxlen, len(val1.flat))
##                 elif type(val) == numpy.ndarray:
##                     maxlen = max(maxlen, len(val.flat))
##             numpy.set_printoptions(threshold = maxlen, precision=4)
            #print "maxlen", maxlen
            from numpy import set_string_function, array_repr
            set_string_function(numarr2str)
            lines += tabs + """rendering=%s\n""" % (self.rendering)
            #numpy.set_printoptions(threshold=oldopts["threshold"], precision=oldopts["precision"])
            set_string_function(array_repr) 
        else:
            lines += tabs + """rendering=None\n"""
        newtabs = tabs + 4*" "
        lines += tabs + """try:\n"""
        lines += newtabs + """%s = RenderingTransitionMAA(viewer, rendering = rendering, kfpos=%s, name='%s', startFlag='%s',saveAtomProp=False)\n"""%(varname, self.kfpos, self.name, self.startFlag)
        lines += newtabs + self.saveGeomAtomProp2File(varname)
        lines += tabs + """except:\n"""
        lines += newtabs + """if showwarning: tkMessageBox.showwarning('DejaVu Scenario warning', 'Could not create MAA %s')\n""" % self.name
        lines += newtabs + """print sys.exc_info()[1]\n"""
        return lines


    def getSpheresTransitionValues(self, geom, vv1, vv2, op1, op2, col1, col2, rad1=None, rad2=None, visible1 = 1):
        import numpy.oldnumeric as Numeric
        vdict = {}
        inter1 = []
        inter2 = []
        diff2 = []
        nvert1 = len(vv1)
        nop1 = Numeric.zeros(nvert1, "f")
        ncol1 = col1.astype('f')
        for i,v in enumerate(vv1):
            vdict["%.4f,%.4f,%.4f"%(v[0],v[1],v[2])] = i
        for i, v in enumerate(vv2):
            vkey = "%.4f,%.4f,%.4f"%(v[0],v[1],v[2])
            if vdict.has_key(vkey):
                j = vdict[vkey]
                inter1.append(j)
                inter2.append(i)
                nop1[j] = op2[i]
                ncol1[j] = col2[i]
            else:
                diff2.append(i)
        #print "len vv1:" , len(vv1), "vv2:", len(vv2), "inter:", len(inter1), len(vv1)+len(diff2)
        if len(inter1) > 0:
            nvert2 = len(diff2)

            verts = Numeric.concatenate((vv1, Numeric.take(vv2, diff2)))
            #print "new verts array:", verts.shape
            if rad1 is not None and rad2 is not None:
                radii = Numeric.concatenate((rad1, Numeric.take(rad2, diff2)))
            else:
                radii = None
            if not visible1:
                opacity1 = Numeric.zeros(nvert1+nvert2).astype('f')
            else:
                opacity1 = Numeric.concatenate((op1, Numeric.zeros(nvert2)))
            opacity2 = Numeric.concatenate((nop1,  Numeric.take(op2, diff2)))
            colors1 = Numeric.concatenate((col1, Numeric.take(col2, diff2)))
            colors2 = Numeric.concatenate((ncol1,  Numeric.take(col2, diff2)))
            sverts,  sradii,  scolors1, scolors2, sopac1, sopac2 = self.sortVerts(geom, verts, radii,colors1, colors2, opacity1, opacity2, order=1)

            return sverts, sradii, sopac1, sopac2, scolors1, scolors2
        else:
            verts = Numeric.concatenate((vv1, vv2))
            nvert2 = len(vv2)
            if not visible1:
                opacity1 = Numeric.zeros(nvert1+nvert2).astype('f')
            else:
                opacity1 = Numeric.concatenate((op1, Numeric.zeros(nvert2)))
            opacity2 = Numeric.concatenate((Numeric.zeros(nvert1), op2))

            colors1 = Numeric.concatenate((col1, col2))
            colors2 = None
            if rad1 is not None and rad2 is not None:
                radii = Numeric.concatenate((rad1, rad2))
            else:
                radii = None

            return verts, radii, opacity1, opacity2, colors1, colors2


    def getIndGeomsTransitionValues(self, geom, vv1, vv2, op1, op2, col1, col2, f1, f2, rad1=None, rad2=None, visible1 = 1):
        # checks if the geometries specified by vertices and faces intersect
        # returns "union" arrays of vertices and faces of the two geometries
        # returns opacity an color arrays representing transition between two states.
        import numpy.oldnumeric as Numeric
        inter1 = []
        inter2 = []
        diff2 = []
        ncol1 = col1.astype("f")
        nvert1 = len(vv1)
        nvert2 = len(vv2)
        nop1 = Numeric.zeros(nvert1, 'f')
        fdict = {}
        nv = len(f1[0])
        if nv == 2:
            for i, ff1 in enumerate(f1):
                st1 = "%.4f,%.4f,%.4f,"% tuple(vv1[ff1[0]]) + "%.4f,%.4f,%.4f"% tuple(vv1[ff1[1]])
                fdict[st1] = i
            for j , ff2 in enumerate(f2):
                ind20 = ff2[0]
                ind21 = ff2[1]
                st2 = "%.4f,%.4f,%.4f,"% tuple(vv2[ind20]) + "%.4f,%.4f,%.4f"% tuple(vv2[ind21])
                if fdict.has_key(st2):
                    i = fdict[st2]
                    ind10 = f1[i][0]
                    ind11 = f1[i][1]
                    inter1.append(i)
                    ncol1[ind10] = col2[ind20]
                    ncol1[ind11] = col2[ind21]
                    nop1[ind10] = op2[ind20]
                    nop1[ind11] = op2[ind21]
                else:
                    diff2.append(j) 
        elif nv ==3:
            for i, ff1 in enumerate(f1):
                st1 = "%.4f,%.4f,%.4f,"% tuple(vv1[ff1[0]]) + "%.4f,%.4f,%.4f,"% tuple(vv1[ff1[1]])+ "%.4f,%.4f,%.4f"% tuple(vv1[ff1[2]])
                fdict[st1] = i
            for j , ff2 in enumerate(f2):
                ind20 = ff2[0]
                ind21 = ff2[1]
                ind22 = ff2[2]
                st2 = "%.4f,%.4f,%.4f,"% tuple(vv2[ind20]) + "%.4f,%.4f,%.4f,"% tuple(vv2[ind21])+ "%.4f,%.4f,%.4f"% tuple(vv2[ind22])
                if fdict.has_key(st2):
                    i = fdict[st2]
                    ind10 = f1[i][0]
                    ind11 = f1[i][1]
                    ind12 = f1[i][2]
                    inter1.append(i)
                    ncol1[ind10] = col2[ind20]
                    ncol1[ind11] = col2[ind21]
                    ncol1[ind12] = col2[ind22]
                    nop1[ind10] = op2[ind20]
                    nop1[ind11] = op2[ind21]
                    nop1[ind12] = op2[ind22]
                else:
                    diff2.append(j)
        #print "found intersected faces:", len(inter1)
        #print len(fdict.keys())
        verts = Numeric.concatenate((vv1, vv2))
        radii = None
        if rad1 is not None and rad2 is not None:
            radii = Numeric.concatenate((rad1, rad2))
        colors1 = Numeric.concatenate((col1, col2))
        if not visible1:
            opacity1 = Numeric.zeros(nvert1+nvert2).astype('f')
        else:
            opacity1 = Numeric.concatenate((op1, Numeric.zeros(nvert2)))
        if len(inter1)>0:
            nf2 = Numeric.take(f2, diff2) + (f1.ravel().max()+1)
            #print len(diff2), nf2.shape
            faces = Numeric.concatenate((f1 , nf2 ) )
            colors2 = Numeric.concatenate((ncol1, col2))
            opacity2 = Numeric.concatenate((nop1, op2))
        else:
            faces = Numeric.concatenate((f1 , f2 +(f1.ravel().max()+1)) )
            colors2 = None
            opacity2 = Numeric.concatenate((Numeric.zeros(nvert1), op2))
        sfaces, snorms = self.sortFaces(geom, verts, faces, order=1)
        return verts, sfaces, radii, opacity1, opacity2, colors1, colors2


    def sortFaces(self, geom, verts, faces, normals = None, order=-1):
        """faces, fnormals <- sortFaces(geom, verts, faces, normals = None, order=-1)
        Sorts the geometry polygons according to z values of polygon's
        geomtric centers. Order=-1 sorts by furthest z first, order=1 sorts
        by closest z first"""
        import numpy.oldnumeric as Numeric
        mat = geom.GetMatrix()
        mat = Numeric.reshape(mat, (4,4))
        nv = len(verts)
        verts1 = Numeric.reshape(numpy.ones(nv*4, 'f'), (nv,4))
        verts1[:, :3] = verts
        vt = Numeric.dot(verts1, numpy.transpose(mat))[:, :3]
        triv = Numeric.take(vt, faces.astype('i'))
        nn = faces.shape[1] * 1.
        trig = Numeric.sum(triv,1)/nn
        trigz = trig[:,2]  #triangle's center of gravity z value
        
        ind = Numeric.argsort(trigz) # sorted indices
        
        sfaces = Numeric.take(faces, ind[::order])
        
        if normals is None:
            snormals = None
        else:
            if len(normals)>1:
                snormals = Numeric.take(normals, ind[::order])
            else:
                snormals = normals
                
        return sfaces, snormals


    def sortVerts(self, geom, verts, radii, colors1, colors2, opac1, opac2 = None, order=-1):
        nv = len(verts)
        if len(opac1) != nv or len(colors1)!= nv or len(colors2) != nv or len(radii) != nv:
            return verts, radii, colors1, colors2, opac1, opac2
        import numpy.oldnumeric as Numeric
        mat = geom.GetMatrix()
        mat = Numeric.reshape(mat, (4,4))

        verts1 = Numeric.reshape(numpy.ones(nv*4, 'f'), (nv,4))
        verts1[:, :3] = verts
        
        vt = Numeric.dot(verts1, numpy.transpose(mat))[:, :3]
        ind = Numeric.argsort(vt[:,2])
        sverts = Numeric.take(verts, ind[::order])
        sopac1 = Numeric.take(opac1, ind[::order])
        sopac2 = None
        scolors1 = Numeric.take(colors1, ind[::order])
        scolors2 = Numeric.take(colors2, ind[::order])
        sradii = None
        if radii is not None:
            sradii = Numeric.take(radii, ind[::order])
        if opac2 is not None:
            sopac2 = Numeric.take(opac2, ind[::order])
        return sverts, sradii, scolors1, scolors2, sopac1, sopac2


    def intersects(self, bb1, bb2):
        # find out if two bounding boxes intersect
        return (bb1[0][0] < bb2[1][0]) and (bb1[1][0] > bb2[0][0]) and \
               (bb1[0][1] < bb2[1][1]) and (bb1[1][1] > bb2[0][1]) and \
               (bb1[0][2] < bb2[1][2]) and (bb1[1][2] > bb2[0][2])



    def saveGeomAtomProp(self):
        t1 = time()
        self.atomSets = {}
        self.msmsPtrs = {}
        allobj = self.viewer.rootObject.AllObjects()
        from MolKit.molecule import AtomSet
        for obj in allobj:
            if hasattr(obj, "mol"):
                mol = obj.mol
                set = mol.geomContainer.atoms.get(obj.name, None)
                if set is not None and len(set):
                    #self.atomSets[obj.fullName] = AtomSet(set.data[:])
                    self.atomSets[obj.fullName] = set.__class__(set.data[:])
                gc = mol.geomContainer
                if gc.msms.has_key(obj.name):
                    # save the msms swig pointer
                    
                    self.msmsPtrs[obj.fullName] = [(obj.name, gc.msms[obj.name]), False]
                    # False will be replaced by True if we need to reset the pointer
                    # after animation (in the case when there is transformation
                    # between two same name surfaces with different vertex arrays).
        #print 'time to save prop', time()-t1


    def setGeomAtomProp(self):
        t1 = time()
        if not len(self.atomSets) : return
        #print "setGeomAtomProp"
        for actor in self.actors:
            #if actor.name.find("setactor") > 0 or actor.name.find("faces") > 0:
            if actor.name.split(".")[-1] in ["setactor", "faces", "rendering"]:
                obj = actor.object
                if self.atomSets.has_key(obj.fullName):
                    aset = self.atomSets[obj.fullName]
                    if type(aset) == types.StringType:
                        if self._animNB:
                            pmv = self._animNB().pmv
                            self.viewer.stopAutoRedraw()
                            self.viewer.suspendRedraw = True
                            try:
                                aset = pmv.select(aset).copy()
                                pmv.clearSelection()
                            except:
                                pass
                            self.viewer.suspendRedraw = False
                            self.viewer.startAutoRedraw()
                        else:
                            aset = []
                    if len(aset):
                        obj.mol.geomContainer.atoms[obj.name] = aset
                val = self.msmsPtrs.get(obj.fullName, None)
                if val is not None and val[1] == True:
                    surfname = val[0][0]
                    geomC = obj.mol.geomContainer
                    geomC.msms[surfname] = val[0][1]
                    if hasattr(geomC,'msmsAtoms') and geomC.msmsAtoms.has_key(obj.name):
                        geomC.msmsAtoms[obj.name] = aset
                    #obj.mol.geomContainer.msms.update(val[0])

        #print "time to set atom prop" , time()-t1


    def saveGeomAtomProp2File(self, name):
        ats = {}
        for k, val in self.atomSets.items():
            if type(val) == types.StringType:
                ats[k] = val
            else:
                ats[k] = val.getStringRepr()
        return "%s.atomSets = %s \n" % (name, ats)



    def saveGeomAtomProp0(self):
        t1 = time()
        self.atomSets = {}
        allobj = self.viewer.rootObject.AllObjects()
        from MolKit.molecule import Atom
        from copy import copy
        for obj in allobj:
            if hasattr(obj, "mol"):
                mol = obj.mol
                set = mol.geomContainer.atoms.get(obj.name, None)
                if set is not None and len(set):
                    #print "saving aset for:" , obj.fullName
                    aset = set.findType(Atom)
                    from MolKit.stringSelector import StringSelector
                    selector = StringSelector()
                    g = mol.geomContainer
                    atList = []
                    func = g.geomPickToAtoms.get(obj.name)
                    if func:
                        atList = func(obj, range(len(obj.vertexSet.vertices)))
                    else:
                        allAtoms = g.atoms[obj.name]
                        if hasattr(obj, "vertexSet") and len(allAtoms) == len(obj.vertexSet):
                            atList = allAtoms
                    if len(atList):
                        self.atomSets[obj.fullName] = {'atomset': set.full_name()}
                        self.atomSets[obj.fullName]['atlist'] = atList
        print 'time to save prop', time()-t1


        

    def setGeomAtomProp0(self):
        t1 = time()
        if not len(self.atomSets) : return
        from MolKit.molecule import Atom
        for actor in self.actors:
            if actor.name.find("setactor") > 0 or actor.name.find("faces") > 0:
                obj = actor.object
                if self.atomSets.has_key(obj.fullName):
                    asetstr = self.atomSets[obj.fullName]['atomset']
                    atList = self.atomSets[obj.fullName].get('atlist', None)
                    g = obj.mol.geomContainer
                    from MolKit.stringSelector import StringSelector
                    selector = StringSelector()
                    aset, msg = selector.select(atList, asetstr)
                    if len(aset):
                        #print "setting atoms to:", obj, len(aset)
                        if g.atoms[obj.name].elementType == Atom:
                            g.atoms[obj.name] = aset

        #print 'AAAAAAAAAAa', time()-t1
        t1 = time()
        for actor in self.actors:
            #print actor.name
            prop = None
            if actor.name.find('colors') > 0:
                prop = 'colors'
            elif actor.name.find('opacity') > 0:
                prop = 'opacities'
            if prop:
                obj = actor.object
                if self.atomSets.has_key(obj.fullName):
                    atList = self.atomSets[obj.fullName].get('atlist', None)
                    g = obj.mol.geomContainer
                    if not atList: continue
                    set=obj.mol.geomContainer.atoms.get(obj.name, None)
                    if set is not None and len(set):
                        values = actor.getLastKeyFrame().getValue()
                        if len(values) != 1 and len(values) != len(atList):
                            continue
                        aset = set.findType(Atom)
                        asetstr = aset.full_name(0)
                        oname = None
                        if getattr(aset, prop).has_key(obj.name):
                            oname = obj.name
                        elif getattr(aset, prop).has_key(obj.parent.name):
                            oname = obj.parent.name
                        if not oname: continue
                        #print "setting", prop , "to", oname, len(atList) ,

                        if prop == "colors":
                            if len(values) == 1:
                                for a in atList:
                                    a.colors[oname] = tuple(values[0])
                            else:
                                for i, a in enumerate(atList):
                                    a.colors[oname] = tuple(values[i])

                        elif prop == 'opacities':
                            if len(values) == 1:
                               for a in atList:
                                   a.opacities[oname] = values[0]
                            else:
                                for i, a, in enumerate(atList):
                                    a.opacities[oname] = values[i]

                        from MolKit.stringSelector import StringSelector
                        selector = StringSelector()
                        nset, msg = selector.select(atList, asetstr)
                        g.atoms[obj.name] = nset
                        #print len(self.atomSets[obj.fullName]['atlist'])
        print 'time to restore prop', time()-t1

class RedrawMAA(MultipleActorsActions):
    """
    MMA containin a RedrawActor for a DejaVu Viewer.

    This object always makes sure the RedrawActor is the last one in the list
    of actors.
    """

    def __init__(self, viewer, name='redraw', startFlag='after previous'):
        """
        constructor

        MAA <- RedrawMAA(viewer, name='redraw', startFlag='after previous')

        viewer is a DejaVu Viewer Object
        name is a string used to name this RedrawMAA
        startFlag - flag used in a sequence animator for computing time position of the maa .
        the MultipleActorsActions (MAA) is built with a RedrawActor for the
        viewer. The name of the RedrawActor name is 'redraw'+viewer.uniqID.
        """
        assert isinstance(viewer, Viewer)
        MultipleActorsActions.__init__(self, name=name, startFlag=startFlag)
        redrawActor = RedrawActor(viewer)
        self.redrawActor = self.addActor(redrawActor)
        self.redrawActor.name = 'redraw'
        self.viewer = viewer
        self.origValues = {}
        self.editorClass = None
        self.editorKw = {}
        self.editorArgs = []

        # when True the original orientation (of root object) is set on the first frame
        self.forceOrient = True
        self.orient = None
        
        # when True the original rendering style is set on the first frame
        self.forceRendering = True
        self.rendering = None

         # save the orientation in maa
        self.recordOrient()
        
        # save the representation in maa
        self.recordRendering()
        # Flag to set saved orientation of all parents of self.object
        self.setOrient = False
        self.geomOrients = {}
       

    def configure(self, **kw):
        """
        handle forceOrient, forceRendering parameters
        """
        self.forceOrient = kw.get('forceOrient', self.forceOrient)
        self.forceRendering = kw.get('forceRendering', self.forceRendering)


    def removeNonRedrawActors(self):
        """
        remove all actors except for redraw actors.
        """
        # use by subclasses then they want to rebuild the MAA
        keptActors = []
        for actor in self.actors:
            if isinstance(actor, RedrawActor):
                keptActors.append( actor)
        self.actors = keptActors
        
                
    def addMultipleActorsActionsAt(self, maa, position=None):
        """
        override the base class method to make sure RedrawActor is always last
        in the self.actors list
        """
        val = MultipleActorsActions.addMultipleActorsActionsAt(
            self, maa, position=None)
        if self.redrawActor is not None:
            self.actors.remove(self.redrawActor)
            self.actors.append(self.redrawActor)
        if hasattr(maa, "origValues"):
            if len(maa.origValues):
                if hasattr(self, "origValues"):
                    self.origValues.update(maa.origValues)
                else:
                    self.origValues = maa.origValues
        return val


    def afterAnimation_cb(self):
        # reset maa actors original values
        if hasattr(self, "origValues"):
            for actor in self.actors:
                val = self.origValues.get(actor.name)
                if val is not None:
                    #print "afterAnimation_cb: setting actor %s of object %s"% (actor.name, actor.object.name), val
                    actor.setValue(val)


    def recordOrient(self):
        self.orient = getOrientation(self.viewer.rootObject)

    def recordRendering(self):
        self.rendering = getRendering(self.viewer, checkAnimatable=True)

        

class VisibleObjectMAA(RedrawMAA):
    """
    Create an MAA for making an object visible/invisible
    """
    
    def __init__(self, object, objectName='NoName', kfpos=0, visible=1,
                 objectFromString=None, startFlag="after previous", **kw):
        """
        constructor
        
        MAA <- VisibleObjectMAA( object, objectName=None, name=None, kfpos=0,
                visible = 1, objectFromString=None, startFlag='after previous')

        - object - a list of- or a single DejaVu Transformable object
        - objectName - a short name used to name the MAA
        - kfpos - keyframe position at which object.visible attribute will be set
        - objectFromString is a string  that yields the specified object(s) when evaluated;
        - startFlag - flag used in a sequence animator for computing time position of the maa .        
        """

        if not hasattr(object, "__len__"):
            objects = [object]
        else:
            objects = object

        name = "%s %s"% ({0:"Hide", 1:"Show"}.get(visible), objectName)

        RedrawMAA.__init__(self, objects[0].viewer, name, startFlag)

        self.forceOrient = False
        self.forceRendering = False

        assert visible in (0,1, True, False)
        self.visible = visible

        self.kfpos = kfpos

        self.objectName = objectName

        if objectFromString is None:
            objectFromString = getObjectFromString(objects)
        self.objectFromString = objectFromString

        if visible:
            self.shortName = "Show"
        else:
            self.shortName = "Hide"

        for geom in objects:
            actor = getActor(geom, "visible")
            self.origValues[actor.name] = actor.getValueFromObject()
            kf1 = KF(kfpos, visible)
            actor.actions.addKeyframe(kf1)
            self.AddActions( actor, actor.actions )


    def getSourceCode(self, varname, indent=0):
        """
        Return python code creating this object
        """
        if not self.objectFromString:
            return ""
        tabs = " "*indent
        lines = tabs + """import tkMessageBox\n"""
        lines += tabs + """from DejaVu.scenarioInterface.animations import VisibleObjectMAA\n"""
        lines += tabs + """object = %s\n"""%(self.objectFromString)
        newtabs = tabs + 4*" "
        lines += tabs + """try:\n"""
        lines += newtabs + """%s = VisibleObjectMAA(object, objectName='%s', kfpos=%s, visible=%s, objectFromString = "%s", startFlag='%s')\n""" % (varname, self.objectName, self.kfpos, self.visible, self.objectFromString, self.startFlag)
        lines += newtabs + """assert len(%s.actors) > 0 \n""" % (varname,)
        lines += tabs + """except:\n"""
        lines += newtabs + """if showwarning: tkMessageBox.showwarning('DejaVu Scenario warning', 'Could not create MAA %s')\n""" % self.name
        lines += newtabs + """print sys.exc_info()[1]\n"""
        return lines


from DejaVu.Transformable import Transformable

class OrientationMAA(RedrawMAA):
    """
    create a MAA for going from any orientation to the current orientation
    The orientation includes: the object's rotation, translation, scale,
    pivot point, and teh camera field of view is modified to zoom out
    between the 2 first keyframes and zoom back in between the 2 last keyframes
    """

    def __init__(self, object, name, orient, rendering,
                 keyPos=[0, 10, 20, 30],
#                 rotation=None, translation=None, scale=None,
#                 pivot=None, fieldOfView=None, lookFrom=None,
                 objectFromString=None, startFlag="after previous"):
        """
        constructor
        
        MAA <- OrientationMAA( object, name, keyPos=[0, 10, 20, 30],
                               rotation=None, translation=None, scale=None,
                               pivot=None, fieldOfView=None, lookFrom=None,
                               objectFromString=None, startFlag='after previous')

        - object is a DejaVu Transformable object that belongs to a DejaVu Viewer
        - name is the name for the MAA
        - orient is a dictionary with the following keys:
          -- rotation
          -- translation
          -- scale
          -- pivot
          -- fieldOfView
          -- lookFrom
          -- near
          -- far
          -- fogStart
          -- fogEnd
        - rendering is a dictionary storing the state of all geometries;
        - keyPos is a list of 4 positions. Zoom out will happen between the 2
          first keyframes and zoom in between the 2 last.

        
        - objectFromString is a string  that yields the viewer's oject when evaluated.
        - startFlag - flag used in a sequence animator for computing time position of the maa .        
        """
        assert isinstance(object, Transformable)
        assert isinstance(object.viewer, Viewer)

        RedrawMAA.__init__(self, object.viewer, name, startFlag)

        self.forceOrient = False
        self.forceRendering = False

        ## define the class of the editor for this MAA
        ## the presence of the .editorClass attribute will enable the edit
        ## button in the sequence animator
        ## For this to work the folloing method have to work
        ##     self.getValues()
        ##     MAAEditor.setValues(**kw)
        ##     MAAEditor.getValues() 
        ##     MAAEditor.execute(self, name) has to configure self.maa 
        ##        with the current parameters (MAAEditor.getValues() )
        from DejaVu.scenarioInterface.animationGUI import OrientationMAAEditor
        self.editorClass = OrientationMAAEditor
        self.object = object
        if objectFromString is None:
            try:
                objectFromString = "viewer.FindObjectByName('%s')" % object.fullName
            except:
                pass
        self.objectFromString = objectFromString
        self._maaGroup = None # will be a weakref to MAAGroup
        self.orient = {}
        if not orient:
            orient = self.getCurrentOrient()
        self.makeMAA(keyPos, orient, rendering)


    def getCurrentOrient(self):
        orient = {}
        cam = self.object.viewer.currentCamera
        fieldOfView = cam.fovy
        lookFrom = cam.lookFrom.copy()
        
        orient['fieldOfView'] = fieldOfView
        orient['lookFrom'] = lookFrom
        orient['near'] = cam.near
        orient['far'] = cam.far
        orient['fogStart'] = cam.fog.start
        orient['fogEnd'] = cam.fog.end

        for obj in self.object.AllObjects():
            if not obj.animatable: continue
            oname = obj.fullName
            orient[oname] = {'rotation':obj.rotation[:],
                             'translation':obj.translation[:],
                             'scale':obj.scale[:],
                             'pivot':obj.pivot[:]}
        return orient


    def makeMAA(self, keyPos, orient=None, rendering=None):
        # create all actors and their actions and add them to the MAA
        #print "makeMaa:", self.name,  keyPos
        self.keyPos = keyPos
        
        if rendering:
            self.rendering = rendering

        if orient:
            self.orient = orient
        else:
            orient = self.orient
        
        cam = self.object.viewer.currentCamera

        fieldOfView = orient['fieldOfView']
        lookFrom = orient['lookFrom'] 
        near = orient['near']
        far = orient['far']
        fogStart = orient['fogStart']
        fogEnd = orient['fogEnd']
        
        if keyPos[-1] - keyPos[0] == 1:
            p1 = keyPos[0]

            actor = getActor(cam, 'fieldOfView')
            actor.actions.addKeyframe(KF( p1, fieldOfView))
            self.AddActions( actor, actor.actions )

            actor = getActor(cam, 'lookFrom')
            actor.actions.addKeyframe(KF( p1, lookFrom))
            kf2 = KF( keyPos[-1], 'Nothing There')
            actor.actions.addKeyframe(kf2)
            self.AddActions( actor, actor.actions )

            actor = getActor(cam, 'near')
            actor.actions.addKeyframe(KF( p1, near))
            self.AddActions( actor, actor.actions )

            actor = getActor(cam, 'far')
            actor.actions.addKeyframe(KF( p1, far))
            self.AddActions( actor, actor.actions )

            actor = getActor(cam.fog, 'start')
            actor.actions.addKeyframe(KF( p1, fogStart))
            self.AddActions( actor, actor.actions )

            actor = getActor(cam.fog, 'end')
            actor.actions.addKeyframe(KF( p1, fogEnd))
            self.AddActions( actor, actor.actions )
            
        else:
            p1, p2, p3, p4 = keyPos
            actor = getActor(cam, 'fieldOfView')
            k0 = KFAutoCurrentValue( p1, actor)
            #k1 = KF( p2, cam.fovyNeutral)
            #k2 = KF( p3, cam.fovyNeutral)
            k3 = KF( p4, fieldOfView)
            #actor.addIntervals( [ Interval(k0,k1), Interval(k1,k2),
            #                      Interval(k2,k3), Interval(k2,k3) ] )
            actor.addIntervals( [ Interval(k0,k3)] )
            self.AddActions( actor, actor.actions )

            actor = getActor(cam, 'lookFrom')
            kf0 = KFAutoCurrentValue( p1, actor)
            kf1 = KF( p4, lookFrom)
            i = Interval( kf0, kf1)
            actor.addIntervals( [i] )
            self.AddActions( actor, actor.actions )

            actor = getActor(cam, 'near')
            kf0 = KFAutoCurrentValue( p1, actor)
            kf1 = KF( p4, near)
            actor.addIntervals( [Interval(kf0,kf1)] )
            self.AddActions( actor, actor.actions )

            actor = getActor(cam, 'far')
            kf0 = KFAutoCurrentValue( p1, actor)
            kf1 = KF( p4, far)
            actor.addIntervals( [Interval(kf0,kf1)] )
            self.AddActions( actor, actor.actions )

            actor = getActor(cam.fog, 'start')
            kf0 = KFAutoCurrentValue( p1, actor)
            kf1 = KF( p4, fogStart)
            actor.addIntervals( [Interval(kf0,kf1)] )
            self.AddActions( actor, actor.actions )

            actor = getActor(cam.fog, 'end')
            kf0 = KFAutoCurrentValue( p1, actor)
            kf1 = KF( p4, fogEnd)
            actor.addIntervals( [Interval(kf0,kf1)] )
            self.AddActions( actor, actor.actions )
            
        for obj in self.object.AllObjects():
            if not obj.animatable: continue
            oname = obj.fullName
            objorient = orient.get(oname, None)
            if not objorient: continue
            rotation = objorient['rotation']
            translation = objorient['translation']
            scale = objorient['scale']
            pivot = objorient['pivot']
                
            val = [matToQuaternion(rotation), translation, scale, pivot]
            if keyPos[-1] - keyPos[0] == 1:
                #create one key frame with current (at maa creation time) values
                p1 = keyPos[0]
                actor = getActor(obj, 'transformation')
                actor.actions.addKeyframe(KF( p1, val))
                self.AddActions( actor, actor.actions )
##                 actor = getActor(obj, 'rotation')
##                 actor.actions.addKeyframe(KF( p1, matToQuaternion(rotation)) )
##                 self.AddActions( actor, actor.actions )
               
##                 actor = getActor(obj, 'translation')
##                 actor.actions.addKeyframe(KF( p1, translation ) )
##                 self.AddActions( actor, actor.actions )
               
##                 actor = getActor(obj, 'scale')
##                 actor.actions.addKeyframe(KF( p1, scale) )
##                 self.AddActions( actor, actor.actions )

##                 actor = getActor(obj, 'pivot')
##                 actor.actions.addKeyframe(KF( p1, pivot))
##                 self.AddActions( actor, actor.actions )

            else:  # create transition from current at play time to what it is at creation time
                p1, p2, p3, p4 = keyPos
                actor = getActor(obj, 'transformation')
                kf0 = KFAutoCurrentValue( p1 , actor)
                kf1 = KF( p4, val)
                i = Interval( kf0, kf1, generator=actor.behaviorList)
                actor.addIntervals( [i] )
                self.AddActions( actor, actor.actions )

                
##                 actor = getActor(obj, 'rotation')
##                 kf0 = KFAutoCurrentValue( p1 , actor)
##                 kf1 = KF( p4, matToQuaternion(rotation) )
##                 i = Interval( kf0, kf1, generator=actor.behaviorList)
##                 actor.addIntervals( [i] )
##                 self.AddActions( actor, actor.actions )

##                 actor = getActor(obj, 'translation')
##                 kf0 = KFAutoCurrentValue( p1 , actor )
##                 kf1 = KF( p4, translation )
##                 actor.addIntervals( [ (kf0, kf1) ] )
##                 self.AddActions( actor, actor.actions )

##                 actor = getActor(obj, 'scale')
##                 kf0 = KFAutoCurrentValue( p1, actor)
##                 kf1 = KF( p4, scale)
##                 i = Interval( kf0, kf1 )
##                 actor.addIntervals( [i] )
##                 self.AddActions( actor, actor.actions )

##                 actor = getActor(obj, 'pivot')
##                 kf0 = KFAutoCurrentValue( p1, actor)
##                 kf1 = KF( p4, pivot)
##                 i = Interval( kf0, kf1 ) 
##                 actor.addIntervals( [i] )
##                 self.AddActions( actor, actor.actions )


        print self.getStringRepr()[-1]

        
    def setKeyframePositions(self, keyPos):
        """
        change all KF to reflect the positions
        """
        self.removeNonRedrawActors()
        self.makeMAA(keyPos)


    #def configure(self, **kw):
    #    self.setKeyframePositions(kw['keyframes'])


    def getValues(self):
        """
        returns the parameters of this MAA, i.e. 3 keyframes positions
        """
        return {'keyframes': self.keyPos,
                'forceOrient':self.forceOrient,
                'forceRendering':self.forceRendering}

    def orient2string(self):
        """returns a string representation of the stored orientation. Replaces
        numeric arrays by lists"""
        orient = {}
        import numpy, types
        allkeys = self.orient.keys()
        for k in ['lookFrom', 'fieldOfView']:
            val = self.orient[k]
            if type(val) == numpy.ndarray: val =  val.tolist()
            orient[k]=val
            allkeys.remove(k)
        for k in ['fogStart', 'fogEnd', 'far', 'near']:
            orient[k] = self.orient[k]
            allkeys.remove(k)
        for name in allkeys:
            objorient = self.orient[name]
            orient[name] = {}
            for k, val in objorient.items():
                if type(val) == numpy.ndarray: val = val.tolist()
                orient[name][k] = val
        return """%s"""%orient
        
            
        
    def getSourceCode(self, varname, indent=0):
        """
        Return python code creating this object
        """
        if not self.objectFromString:
            return ""
        tabs = " "*indent
        lines = tabs + """import tkMessageBox\n"""
        lines += tabs + """from DejaVu.scenarioInterface.animations import OrientationMAA\n"""
        lines += tabs + """object = %s\n"""%(self.objectFromString)
        lines += tabs + """from numpy import *\n"""
        import numpy, types
        # avoid array summarization in the string (ex: "[0, 1, 2, ..., 7, 8, 9]" )
##         oldopts = numpy.get_printoptions()
##         maxlen = oldopts["threshold"]
##         for val in self.rendering.values():
##             if type(val) == types.DictType:
##                 for val1 in val.values():
##                     if  type(val1) == numpy.ndarray:
##                         maxlen = max(maxlen, len(val1.flat))
##             elif type(val) == numpy.ndarray:
##                 maxlen = max(maxlen, len(val.flat))
##         numpy.set_printoptions(threshold = maxlen, precision=4)
        numpy.set_string_function(numarr2str)
        #print "maxlen", maxlen
        lines += tabs + """rendering=%s\n""" % (self.rendering)
        lines += tabs + """orient=%s\n""" % self.orient2string()
        newtabs = tabs + 4*" "
        lines += tabs + """try:\n"""
        lines += newtabs + """%s = OrientationMAA(object, '%s', orient, rendering, keyPos=%s, objectFromString="%s", startFlag='%s')\n"""%(varname,  self.name, self.keyPos,  self.objectFromString, self.startFlag)
        lines += newtabs + """assert len(%s.actors) > 0 \n""" % (varname,)
        lines += tabs + """except:\n"""
        lines += newtabs + """if showwarning: tkMessageBox.showwarning('DejaVu Scenario warning', 'Could not create MAA %s')\n""" % self.name
        lines += newtabs + """print sys.exc_info()[1]\n"""
        #numpy.set_printoptions(threshold=oldopts["threshold"], precision=oldopts["precision"])
        from numpy import array_repr
        numpy.set_string_function(array_repr)
        
        return lines

from time import time

class SnapshotMAAGroup(MAAGroup):
    """Create an MAA Group consisting of OrientationMAA and RenderingTransitionMAA"""

    def __init__(self,  orientMaa, renderMaa, name='snapshot', startFlag="after previous"):
        """SnapshotMAAGroup constructor
        SnapshotMAAGroup <- SnapshotMAAGroup(orientMaa, renderMaa, name='snapshot', startFlag='after previous')
        """
        assert isinstance(orientMaa, OrientationMAA)
        assert isinstance(renderMaa, RenderingTransitionMAA)
        MAAGroup.__init__(self, name=name, maalist=[orientMaa, renderMaa], startFlag=startFlag)
        self.orientMaa = orientMaa
        self.renderMaa = renderMaa
        self.sortPoly = 'Never'
        from DejaVu.scenarioInterface.animationGUI import SnapshotMAAGroupEditor
        self.editorClass = SnapshotMAAGroupEditor #orientMaa.editorClass

        # if the following attributes are set to False - we will not
        #interpolate orientation or rendering
        self.interpolateOrient = True
        self.interpolateRendering = True
        
        self.forceRendering = False
        self.forceOrient = False
        self.editorKw = {}
        self.editorArgs = []
        self.rendering = orientMaa.rendering
        self.orient = orientMaa.orient
        self.kfpos = renderMaa.kfpos

    def run(self):
##         if self.orientMaa.forceRendering:
##             setRendering(self.orientMaa.viewer, self.orientMaa.rendering)
##             self.orientMaa.run()
        if self.interpolateRendering :
            # modify (morph) rendering
            t1 = time()
            self.renderMaa.setValuesAt(0)
            if self.interpolateOrient:
                self.makeActorList()
            else:
                self.makeActorList([self.renderMaa])
            t2 = time()
            #print 'time to makeActorList', t2-t1
            t1 = t2
            MAAGroup.run(self)
            t2 = time()
            #print 'time to MAAGroup.run', t2-t1
            t1 = t2
            try:
                self.setGeomAtomProp()
                t2 = time()
                #print 'time to setGeomAtomProp', t2-t1
            except:
                pass
        else:
            if self.interpolateOrient:
                self.orientMaa.run()


    def getValues(self):
        """
        returns the parameters of this MAA, i.e. 3 keyframes positions
        """
        return {'keyframes': self.renderMaa.kfpos,
                'interpolateOrient':self.interpolateOrient,
                'interpolateRendering':self.interpolateRendering,
                'sortPoly': self.sortPoly}


    def recordOrient(self):
        #print self.name, "record orient" 
        orient = self.orient = self.orientMaa.getCurrentOrient()
        self.orientMaa.removeNonRedrawActors()
        kf1, kf2 = self.kfpos
        self.orientMaa.makeMAA([kf1, kf2/3, 2*kf2/3, kf2], orient=orient)

    def recordRendering(self):
        #print self.name, "record rendering"
        self.rendering = getRendering(self.orientMaa.viewer, checkAnimatable=True)
        self.orientMaa.rendering = self.rendering
        self.renderMaa.rendering = self.rendering
        try:
            self.renderMaa.saveGeomAtomProp()
        except:
            pass


    def setKeyframePositions(self, keyPos):
        
        #print "Setting keyframePositions:", keyPos
        assert len(keyPos) == 2
        nbframes = keyPos[1]
        self.orientMaa.setKeyframePositions([0, nbframes/3, 2*nbframes/3, nbframes])
        self.kfpos = self.renderMaa.kfpos = keyPos
        self.firstPosition, self.lastPosition = keyPos
        #print "firstPosition:", self.firstPosition, "lastPosition:", self.lastPosition
        self.makeActorList()
        


    def setValuesAt(self, frame, pos=0):
        self.needsRedraw = False
        if self.interpolateRendering:
            self.renderMaa.setValuesAt(frame, pos)
            if self.renderMaa.needsRedraw:
                self.needsRedraw = True
        if self.interpolateOrient:
                self.orientMaa.setValuesAt(frame, pos)
                if self.orientMaa.needsRedraw:
                    self.needsRedraw = True
        if frame == pos + self.lastPosition:
            if self._director and frame == self._director().endFrame-1:
                try:
                    self.setGeomAtomProp()
                except:
                    pass


    def getSourceCode(self, varname, indent = 0):
        """
        Return python code creating this object
        """
        tabs = " "*indent
        newtabs = tabs + 4*" "
        lines = tabs + """from DejaVu.scenarioInterface.animations import SnapshotMAAGroup\n"""
        lines += tabs + """%sorient = None\n""" % (varname,)
        lines += self.orientMaa.getSourceCode("%sorient" % varname, indent=indent)
        lines += tabs + """%srender = None\n""" % (varname,)
        lines += self.renderMaa.getSourceCode("%srender" % varname, indent=indent, saverendering=False)
        lines += tabs + """if %sorient is not None and %srender is not None:\n"""%(varname, varname) 
        lines += newtabs + """%srender.rendering = %sorient.rendering\n"""%(varname, varname)
        lines += newtabs +"""%s = SnapshotMAAGroup(%sorient, %srender, name='%s', startFlag='%s')\n""" %(varname, varname, varname, self.name, self.startFlag)
        lines += newtabs +"""%s.interpolateOrient = %s\n""" % (varname, self.interpolateOrient)
        lines += newtabs +"""%s.interpolateRendering = %s\n""" % (varname, self.interpolateRendering)
        return lines


    def setGeomAtomProp(self):
        self.renderMaa.setGeomAtomProp()


    def copy(self):
        object = self.orientMaa.object
        orient = self.orientMaa.orient
        rendering = self.renderMaa.rendering
        orientMaa = OrientationMAA(object, self.orientMaa.name, orient, rendering,
                                   objectFromString=self.orientMaa.objectFromString,
                                   keyPos=self.orientMaa.keyPos,
                                   startFlag=self.orientMaa.startFlag)
        renderMaa = RenderingTransitionMAA(self.renderMaa.viewer, rendering = rendering,
                                           kfpos=self.renderMaa.kfpos, name=self.renderMaa.name,
                                           startFlag=self.renderMaa.startFlag,
                                           saveAtomProp=False)
        renderMaa.atomSets = self.renderMaa.atomSets
        
        newmaa = self.__class__(orientMaa, renderMaa, self.name)
        return newmaa
        

        
class FlyObjectMAA(RedrawMAA):
    """
    Create an MAA for flying an object in or out of the scene
    """

    def __init__(self, object, objectName=None, kfpos=[0, 30],
                 direction="left", easeInOut='none', objectFromString=None,
                 startFlag="after previous", inViewTranslation=None):
        """
        constructor
        
        MAA <- FlyObjectMAA( object, name, objectName=None, kfpos=0,
                visible = 1, objectFromString=None, startFlag='after previous')

        - object - a DejaVu Transformable object
        - objectName - a short name used to name the MAA
        - kfpos - list of 2 keyframe position defining length of transition
        - direction - can be 'left', 'right', 'top', bottom'
        - easeInOut - can be 'none', 'ease in', 'ease out', 'ease in and out'
        - objectFromString is a string  that yields the specified object(s) when evaluated;
        - startFlag - flag used in a sequence animator for computing time position of the maa
        """
        if not hasattr(object, "__len__"):
            objects = [object]
        else:
            objects = object

        RedrawMAA.__init__(self, objects[0].viewer, None, startFlag)
        
        # set the editor class so this MAA is editable
        from DejaVu.scenarioInterface.animationGUI import SED_MAAEditor
        self.editorClass = SED_MAAEditor
        self.editorKw = {'directions': ['left', 'right', 'top', 'bottom']}
        
        self.setOrient = True
        if objectFromString is None:
            objectFromString = getObjectFromString(objects)
        self.objectFromString = objectFromString

        self.objects = objects
        self.objectName = objectName
        
        self.inViewTranslation = {}
        if inViewTranslation is not None:
            for obj in self.objects:
                if inViewTranslation.has_key(obj.fullName):
                    self.inViewTranslation[obj.fullName] = inViewTranslation[obj.fullName]
                else:
                    self.inViewTranslation[obj.fullName] = self.getInViewTranslation(obj)
        else:
            for obj in self.objects:
                #self.inViewTranslation[obj] = obj.translation.copy()
                self.inViewTranslation[obj.fullName] = self.getInViewTranslation(obj)
        self.geomOrients = {}
        for obj in self.objects:
            current = obj
            while current.parent:
                parent = current.parent
                if not self.geomOrients.has_key(parent):
                    cameraInfo = False
                    if parent == self.viewer.rootObject:
                        cameraInfo = True
                    self.geomOrients[parent] = getOrientation(parent, camera=cameraInfo)
                current = parent
        
        self.makeMAA(kfpos=kfpos, direction=direction, easeInOut=easeInOut)


    def makeMAA(self, kfpos=[0,30], direction='left', easeInOut='none'):

        # save what we need to be able to recreate this object
        assert len(kfpos)==2
        self.kfpos = kfpos

        assert direction in ['left', 'right', 'top', 'bottom']
        self.direction = direction

        assert easeInOut in ['none', 'ease in', 'ease out', 'ease in and out']
        self.easeInOut = easeInOut

        for obj in self.objects:

            # add visible actor
            visibleactor = getActor(obj, 'visible')

            kf1 = KF(self.kfpos[0], 1)
            visibleactor.actions.addKeyframe(kf1)
            self.AddActions( visibleactor, visibleactor.actions )

            # add translation actor
            translationactor = getActor(obj, 'translation')
            translationactor.setEaseInOut(easeInOut)

            self.setActorsActions(translationactor, self.inViewTranslation[obj.fullName])

            if translationactor.actions is not None:
                self.AddActions( translationactor, translationactor.actions )
        self.name = self.getMAAname()

    def getInViewTranslation(self, object):
        """ Get translation of the object when it is in the camera view"""
        vi = object.viewer
        if object != vi.rootObject:
            return numpy.array([0,0,0], 'f')
        # root object
        # the following is based on code from Viewer.NormalizeCurrentObject()
        mini, maxi = object.ComputeBB()
        g = numpy.add.reduce( (mini, maxi) ) * .5
        d = list(-g[:3])+[1.0]
        rot = numpy.reshape( object.R, (4,4) )
        translation = object.translation + object.multMat4pt(rot, d)
        #print "in view translation:", object.name, translation
        return translation
    

    def setActorsActions(self, actor, inViewTranslation ):
        """
        create a keyframes and interval for fly action
        """
        #method overwriden in FlyInObjectMAA and  FlyOutObjectMAA
        pass

    def getMAAname(self):
        """Create name for this MAA """
        #method overwriden in FlyInObjectMAA and  FlyOutObjectMAA
        pass
    
    def getFlyObjectVal(self, actor, direction, inViewTranslation):
        """
        compute a translation that moves the object out of the view.
        """
        actor = self.findActor(actor)
        if not actor:
            return
        obj = actor.object
        vi = obj.viewer
        c = vi.cameras[0]
        Xc , Yc, Zc = c.lookFrom

        Xo , Yo, Zo = obj.getCumulatedTranslation()
        #d =  math.sqrt( (Xc -Xo)*(Xc -Xo) + (Yc -Yo)*(Yc -Yo) + (Zc -Zo)*(Zc -Zo) )
        d =  math.fabs(Zc -Zo)

        tgTetaOver2 = math.tan(.5*c.fovy * math.pi/180.)

        w = c.width
        h = c.height

        tgAlphaOver2 = tgTetaOver2 * w/float(h)

        lx = d * tgAlphaOver2
        ly = d * tgTetaOver2
        #print "getFlyObjectVal: object", obj, "in view transl:",  inViewTranslation
        trans = numpy.array(inViewTranslation)
        minbb, maxbb = obj.ComputeBB()

        if direction == "left":
            d = maxbb[0] - minbb[0]
            trans[0] = -lx - d
        elif direction == "right":
            d = maxbb[0] - minbb[0]
            trans[0] = lx + d
        elif direction == "top":
            d = maxbb[1] - minbb[1]
            trans[1] = ly + d
        else:
            d = maxbb[1] - minbb[1]
            trans[1] = -ly - d
        #print "translation = ", trans

        # to correct the existing rotation of the rootObject
        if obj != vi.rootObject:
            lInvMat = vi.rootObject.GetMatrixInverse()
            lInvMat.shape= (16)
            rot, transl, scale = vi.rootObject.Decompose4x4(lInvMat)
            rot.shape= (4,4)
            ltrans = numpy.array([trans[0],trans[1],trans[2],1.])
            ltrans.shape= (4,1)
            trans = numpy.dot( rot , ltrans )
            trans = [trans[0,0],trans[1,0],trans[2,0]]
        #print "final trans", trans
        return trans


    def getValues(self):
        """
        returns the parameters of this MAA, i.e. 3 keyframes positions
        """
        return {'kfpos': self.kfpos,
                'direction': self.direction,
                'easeInOut': self.easeInOut,
                'forceOrient':self.forceOrient,
                'forceRendering':self.forceRendering}


    def configure(self, **kw):
        """
        set kfpos, direction and easeInOut and rebuild MAA
        """
        self.removeNonRedrawActors()

        # handle forceOrient and force Rendering
        RedrawMAA.configure(self, **kw)
        kw.pop('forceOrient')
        kw.pop('forceRendering')

        # add missing keys to avoid default values to override current values
        if not kw.has_key('direction'):
            kw['direction'] = self.direction

        if not kw.has_key('kfpos'):
            kw['kfpos'] = self.kfpos

        if not kw.has_key('easeInOut'):
            kw['easeInOut'] = self.easeInOut

        self.makeMAA( **kw )



class FlyInObjectMAA(FlyObjectMAA):
    """
    Create an MAA for flying an object in to the camera view.
    The user specifies the direction to fly the object from.
    The direction is one of the following: left, top, right, bottom.
    """
    
    def __init__(self, object, objectName=None, kfpos=[0, 30],
                 direction="left", easeInOut='none',
                 objectFromString=None, startFlag="after previous",
                 inViewTranslation=None):
        """
        constructor
        
        MAA <- FlyInObjectMAA( object, objectName=None, kfpos=[0,30],
                               direction='left', easeInOut='none',
                               objectFromString=None,
                               startFlag='after previous')
                               
        - object - a DejaVu Transformable object
        - objectName - a short name used to name the MAA
        - kfpos - list of 2 keyframe position defining length of transition
        - direction - can be 'left', 'right', 'top', bottom'
        - easeInOut - can be 'none', 'ease in', 'ease out', 'ease in and out'
        - objectFromString is a string  that yields the specified object(s) when evaluated;
        - startFlag - flag used in a sequence animator for computing time position of the maa
        """

        FlyObjectMAA.__init__(
            self, object, objectName=objectName, kfpos=kfpos,
            direction=direction, easeInOut=easeInOut,
            objectFromString=objectFromString, startFlag=startFlag,
            inViewTranslation=inViewTranslation)

        self.editorKw['title'] = 'Fly Out Editor'

        self.shortName = "FlyIn"


    def setActorsActions(self, actor, inViewTranslation):
        """
        Add keyframes and a valuegenerating interval to the actor.

        create a keyframe that computes it's value at run time to move the
        object out of view.
        """
        kf1 = KFValueFromFunction(
            self.kfpos[0], CallbackFunction(
                self.getFlyObjectVal, actor,
                self.direction, inViewTranslation) )
        kf2 = KF(self.kfpos[1], inViewTranslation)
        i1 = Interval( kf1, kf2, generator=actor.behaviorList)
        actor.addIntervals( [i1] )


    def getSourceCode(self, varname, indent=0):
        """
        Return python code creating this object
        """
        if not self.objectFromString:
            return ""
        tabs = " "*indent
        lines = tabs + """import tkMessageBox\n"""
        lines += tabs + """from DejaVu.scenarioInterface.animations import FlyInObjectMAA\n"""
        lines += tabs + """object = %s\n"""%(self.objectFromString)
        newtabs = tabs + 4*" "
        lines += tabs + """try:\n"""
        lines += newtabs + """%s = FlyInObjectMAA(object, objectName='%s',  kfpos=%s, direction='%s', easeInOut='%s', objectFromString="%s", startFlag='%s')\n""" % (varname, self.objectName, self.kfpos, self.direction, self.easeInOut, self.objectFromString, self.startFlag)
        lines += newtabs + """assert len(%s.actors) > 0 \n""" % (varname,)
        lines += tabs + """except:\n"""
        lines += newtabs + """if showwarning: tkMessageBox.showwarning('DejaVu Scenario warning', 'Could not create MAA %s')\n""" % self.name
        lines += newtabs + """print sys.exc_info()[1]\n"""
        return lines


    def getMAAname(self):
        """Create name for this MAA """
        return "fly in %s from %s"% (self.objectName, self.direction)
        



class FlyOutObjectMAA(FlyObjectMAA):
    """
    Create an MAA for flying an object out of the camera view.
    The user specifies the direction to fly the object to.
    The direction is one of the following: left, top, right, bottom.
    """
    
    def __init__(self, object, objectName=None, kfpos=[0,30],
                 direction="left", easeInOut='none',
                 objectFromString=None, startFlag="after previous", inViewTranslation=None):
        """
        constructor
        
        MAA <- FlyOutObjectMAA( object, objectName=None, kfpos=[0,30],
                                direction='left', easeInOut='none',
                                objectFromString=None,
                                startFlag='after previous')
                               
        - object - a DejaVu Transformable object
        - objectName - a short object name used to name the MAA
        - kfpos - list of 2 keyframe position defining length of transition
        - direction - can be 'left', 'right', 'top', bottom'
        - easeInOut - can be 'none', 'ease in', 'ease out', 'ease in and out'
        - objectFromString is a string  that yields the specified object(s) when evaluated;
        - startFlag - flag used in a sequence animator for computing time position of the maa
        """

        FlyObjectMAA.__init__(
            self, object, objectName=objectName, kfpos=kfpos,
            direction=direction, easeInOut=easeInOut,
            objectFromString=objectFromString, startFlag=startFlag,
            inViewTranslation=inViewTranslation)

        self.editorKw['title'] = 'Fly Out Editor'

        self.shortName = "FlyOut"


    def setActorsActions(self, actor, inViewTranslation):
        """
        Add keyframes and a valuegenerating interval to the actor.

        create a keyframe that computes it's value at run time to move the
        object out of view.
        """

        kf1 = KF(self.kfpos[0], inViewTranslation)
        kf2 = KFValueFromFunction(self.kfpos[1], CallbackFunction(
            self.getFlyObjectVal, actor, self.direction, inViewTranslation))
        i1 = Interval( kf1, kf2, generator=actor.behaviorList)
        actor.addIntervals( [i1] )


    def getSourceCode(self, varname, indent=0):
        """
        Return python code creating this object
        """
        if not self.objectFromString:
            return ""
        tabs = " "*indent
        lines = tabs + """import tkMessageBox\n"""
        lines += tabs + """from DejaVu.scenarioInterface.animations import FlyOutObjectMAA\n"""
        lines += tabs + """object = %s\n"""%(self.objectFromString)
        newtabs = tabs + 4*" "
        lines += tabs + """try:\n"""
        lines += newtabs + """%s = FlyOutObjectMAA(object, objectName='%s', kfpos=%s, direction='%s', easeInOut='%s', objectFromString="%s", startFlag='%s')\n""" % (varname, self.objectName, self.kfpos, self.direction, self.easeInOut, self.objectFromString, self.startFlag)
        lines += newtabs + """assert len(%s.actors) > 0 \n""" % (varname,)
        lines += tabs + """except:\n"""
        lines += newtabs + """if showwarning: tkMessageBox.showwarning('DejaVu Scenario warning', 'Could not create MAA %s')\n""" % self.name
        lines += newtabs + """print sys.exc_info()[1]\n"""
        return lines


    def getMAAname(self):
        """Create name for this MAA """
        return "fly out %s %s"% (self.objectName, self.direction)
        



class FadeObjectMAA(RedrawMAA):
    """
    Create an MAA for fading one or more objects in or out
    """

    def __init__(self, objects, name, objectName, kfpos=[0, 30],
                 easeInOut='none',
                 sortPoly='Once', objectFromString=None,
                 startFlag="after previous"):
        """
        constructor
        
        MAA <- FadeObjectMAA( objects, name, objectName, kfpos=[0,30],
                              easeInOut='none', sortPoly='Once',
                              objectFromString=None, startFlag='after previous')

        - object - a DejaVu Transformable object
        - name - maa name
        - objectName - a short name used to name the MAA
        - kfpos - list of 2 keyframe position defining length of transition
        - easeInOut - can be 'none', 'ease in', 'ease out', 'ease in and out'
        - sortPoly - can be 'Once', 'Never', 'Always'
        - objectFromString is a string  that yields the specified object(s) when evaluated;
        - startFlag - flag used in a sequence animator for computing time position of the maa
        """

        vi = objects[0].viewer
        RedrawMAA.__init__(self, vi, name, startFlag)

        from DejaVu.scenarioInterface.animationGUI import SESp_MAAEditor
        self.editorClass = SESp_MAAEditor
        if objectFromString is None:
            objectFromString = getObjectFromString(objects)
        self.objectFromString = objectFromString

        self.objects = objects
        self.objectName = objectName

        self.makeMAA(kfpos=kfpos, easeInOut=easeInOut, sortPoly=sortPoly)


    def makeMAA(self, kfpos=[0,30], easeInOut='none', sortPoly='Once'):

        # save what we need to be able to recreate this object
        self.kfpos = kfpos
        self.easeInOut = easeInOut
        self.sortPoly = sortPoly # can be 'Never', 'Once', or 'Always'
        
        for obj in self.objects:
            # create opacity actor
            opacityactor = getActor(obj, 'opacity')
            self.origValues[opacityactor.name] = opacityactor.getValueFromObject()
            opacityactor.setEaseInOut(easeInOut)

            # create visibility actor
            visibleactor = getActor(obj, 'visible')
            self.origValues[visibleactor.name] = visibleactor.getValueFromObject()
            kf1 = KF(self.kfpos[0], 1)
            visibleactor.actions.addKeyframe(kf1)

            # call method tha creates keyframes and intervals for Fade In or Out
            actors = [opacityactor, visibleactor]
            self.setActorsActions(actors)

            # add actions from visibility and opacity actors to maa
            for actor in actors:
                if actor.actions is not None:
                    self.AddActions( actor, actor.actions )


    def setActorsActions(self, actor):
        """this method should be overwritten be FlyInObjectMAA and  FlyOutObjectMAA classes"""
        pass


    def getValues(self):
        """
        returns the parameters of this MAA, i.e. 3 keyframes positions
        """
        return {'kfpos': self.kfpos,
                'sortPoly': self.sortPoly,
                'easeInOut': self.easeInOut,
                'forceOrient':self.forceOrient,
                'forceRendering':self.forceRendering}


    def configure(self, **kw):
        """
        set kfpos, direction and easeInOut and rebuild MAA
        """
        self.removeNonRedrawActors()

        # handle forceOrient and force Rendering
        RedrawMAA.configure(self, **kw)
        kw.pop('forceOrient')
        kw.pop('forceRendering')
        
        # add missing keys to avoid default values to override current values
        if not kw.has_key('sortPoly'):
            kw['sortPoly'] = self.sortPoly

        if not kw.has_key('kfpos'):
            kw['kfpos'] = self.kfpos

        if not kw.has_key('easeInOut'):
            kw['easeInOut'] = self.easeInOut

        self.makeMAA( **kw )


    def copy(self):
        newmaa = self.__class__(objects, name, objectName, kfpos=[0, 30],
                                easeInOut='none',
                                sortPoly='Once', objectFromString=None,
                                startFlag="after previous")
        newmaa.forceOrient = self.forceOrient
        newmaa.orient = self.orient
        newmaa.forceRendering = self.forceRendering
        newmaa.rendering = self.rendering
        return newmaa



class FadeInObjectMAA(FadeObjectMAA):
    """
    Create an MAA for 'fading in' a geometric object by
    interpolating the opacity of the object from 0 to 1
    """
    
    def __init__(self, objects, name = None, objectName=None, kfpos=[0,30],
                 easeInOut='none', sortPoly='Once', objectFromString=None,
                 startFlag="after previous"):

        """
        constructor
        
        MAA <- FadeInObjectMAA( objects, objectName=None, kfpos=[0,30],
                               easeInOut='none', sortPoly='Once',
                               objectFromString=None,
                               startFlag='after previous')

        - object - one or a list of DejaVu Transformable objects
        - objectName - a short name used to name the MAA
        - kfpos - list of 2 keyframe position defining length of transition
        - easeInOut - can be 'none', 'ease in', 'ease out', 'ease in and out'
        - sortPoly - can be 'Once', 'Never', 'Always'
        - objectFromString is a string  that yields the specified object(s) when evaluated;
        - startFlag - flag used in a sequence animator for computing time position of the maa
        """

        if not hasattr(objects, "__len__"):
            objects = [objects]
        else:
            objects = objects

        geometries = expandGeoms(objects)
        #print "geometries:", geometries
        if not len(geometries):
            self.actors = []
            raise ValueError("No geometry to fade for:" , objects)
        if not name:
            name = "fade in %s"% (objectName)

        if objectFromString is None:
            objectFromString = getObjectFromString(objects)

        FadeObjectMAA.__init__(
            self, geometries, name, objectName, kfpos=kfpos,
            easeInOut=easeInOut, sortPoly=sortPoly,
            objectFromString=objectFromString, startFlag=startFlag)

        self.editorKw['title'] = 'Fade In Editor'

        self.shortName = "FadeIn"


    def setActorsActions(self, actors):
        """
        Add keyframes and a valuegenerating interval to the actor.
        """
        for actor in actors:
            if actor.name.find("opacity") > 0:
                kf1 = KF(self.kfpos[0], 0.)
                kf2 = KFAutoCurrentValue(self.kfpos[1], actor)
                val = kf2.getValue()
                val = actor.initialValue
                if  hasattr(val, "__len__") :
                    if sum(val) == 0:
                        actor.initialValue = [1.] #kf2.getValue([1.])
                elif val == 0:
                    #kf2.setValue(1.)
                    actor.initialValue = 1.0
                i1 = Interval( kf1, kf2, generator = actor.behaviorList)
                actor.addIntervals( [i1] )
            elif actor.name.find("visible") > 0:
                kf1 = KF(self.kfpos[0], 1)
                actor.actions.addKeyframe(kf1)


    def getSourceCode(self, varname, indent=0):
        """
        Return python code creating this object
        """
        if not self.objectFromString:
            return ""
        tabs = " "*indent
        lines = tabs + """import tkMessageBox\n"""
        lines += tabs + """from DejaVu.scenarioInterface.animations import FadeInObjectMAA\n"""
        lines += tabs + """object = %s\n"""%(self.objectFromString)
        newtabs = tabs + 4*" "
        lines += tabs + """try:\n"""
        lines += newtabs + """%s = FadeInObjectMAA(object, objectName='%s', kfpos=%s, easeInOut='%s', objectFromString="%s", startFlag='%s')\n""" % (varname, self.objectName, self.kfpos, self.easeInOut, self.objectFromString, self.startFlag)
        lines += newtabs + """assert len(%s.actors) > 0 \n""" % (varname,)
        lines += tabs + """except:\n"""
        lines += newtabs + """if showwarning: tkMessageBox.showwarning('DejaVu Scenario warning', 'Could not create MAA %s')\n""" % self.name
        lines += newtabs + """print sys.exc_info()[1]\n"""
        return lines                



class FadeOutObjectMAA(FadeObjectMAA):
    """
    Create an MAA for 'fading out' a geometric object by
    interpolating the opacity of the object from 1 to 0
    """
    
    def __init__(self, object, name=None, objectName=None, kfpos=[0,30], easeInOut='none',
                 sortPoly='Once', objectFromString=None,
                 startFlag="after previous"):

        """
        constructor
        
        MAA <- FadeInObjectMAA( object, objectName=None, kfpos=[0,30],
                 easeInOut='none', sortPoly='Once', objectFromString=None,
                 startFlag='after previous')

        - object - one or a list of DejaVu Transformable object
        - objectName - the object's name. If it is not specified, the class
          constructor will try to use 'fullName' attribute of the object.
        - kfpos - list of 2 keyframe position defining length of transition
        - easeInOut - can be 'none', 'ease in', 'ease out', 'ease in and out'
        - sortPoly - can be 'Once', 'Never', 'Always'
        - objectFromString is a string  that yields the specified oject(s) when evaluated.
        - startFlag - flag used in a sequence animator for computing time position of the maa .        
        """

        if not hasattr(object, "__len__"):
            objects = [object]
        else:
            objects = object
        
        geometries = expandGeoms(objects)
        if not len(geometries):
            self.actors = []
            raise ValueError("No geoemtry to fade")

        if not name:
            name = "fade out %s"% (objectName)
            
        if objectFromString is None:
            objectFromString = getObjectFromString(objects)

        FadeObjectMAA.__init__(
            self, geometries, name, objectName, kfpos=kfpos,
            easeInOut=easeInOut, sortPoly=sortPoly,
            objectFromString=objectFromString, startFlag=startFlag)

        self.editorKw['title'] = 'Fade Out Editor'

        self.shortName = "FadeOut"


    def setActorsActions(self, actors):
        """
        Add keyframes and a valuegenerating interval to the actor.
        """
        #print "FadeoutObjectMAA", actor
        for actor in actors:
            if actor.name.find("opacity") > 0:
                kf1 = KFAutoCurrentValue(self.kfpos[0], actor)
                kf2 = KF(self.kfpos[1], 0.)
                i1 = Interval( kf1, kf2, generator = actor.behaviorList)
                actor.addIntervals( [i1] )
            elif actor.name.find("visible") > 0:
                kf1 = KF(self.kfpos[0], 1)
                actor.actions.addKeyframe(kf1)
                #kf2 = KF(self.kfpos[1], 0)
                #actor.actions.addKeyframe(kf2)


    def getSourceCode(self, varname, indent=0):
        """
        Return python code creating this object
        """
        if not self.objectFromString:
            return ""
        tabs = " "*indent
        lines = tabs + """import tkMessageBox\n"""
        lines += tabs + """from DejaVu.scenarioInterface.animations import FadeOutObjectMAA\n"""
        lines += tabs + """object = %s\n"""%(self.objectFromString)
        newtabs = tabs + 4*" "
        lines += tabs + """try:\n"""
        lines += newtabs + """%s = FadeOutObjectMAA(object, objectName='%s', kfpos=%s, easeInOut='%s', objectFromString="%s", startFlag='%s')\n""" % (varname, self.objectName, self.kfpos, self.easeInOut, self.objectFromString, self.startFlag)
        lines += newtabs + """assert len(%s.actors) > 0 \n""" % (varname,)
        lines += tabs + """except:\n"""
        lines += newtabs + """if showwarning: tkMessageBox.showwarning('DejaVu Scenario warning', 'Could not create MAA %s')\n""" % self.name
        lines += newtabs + """print sys.exc_info()[1]\n"""
        return lines                



class RotationMAA(RedrawMAA):
    """
    create an MAA for rotation animation
    """

    def __init__(self, object, objectName=None, angle=360,
                 nbFrames=180, vector=(0,1,0), easeInOut='none', 
                 direction='counter clockwise', objectFromString=None,
                 startFlag="after previous"):
        """
        constructor

        MAA <- RotationMAA(object, objectName=None, angle=360,
                 nbFrames=180, vector=(0,1,0), easeInOut='none', 
                 irection='counter clockwise', objectFromString=None,
                 startFlag='after previous')

        - object is an instance of a DejaVu Geom object
        - objectName - the object's name. If it is not specified, the class
        - angle is the angular amplitude of the rotation in degrees
        - nbFrames is the number of Frames for the animation
        - direction can be either 'clockwise' or 'counter clockwise'
        - easeInOut - can be 'none', 'ease in', 'ease out', 'ease in and out'
        - objectFromString is a string  that yields the specified oject(s) when evaluated.
        - startFlag - flag used in a sequence animator for computing time position of the maa .
        """

        if not hasattr(object, "__len__"):
            objects = [object]
        else:
            objects = object
        for obj in objects:
            assert isinstance(obj, Transformable)
            assert isinstance(obj.viewer, Viewer)
        self.objects = objects
        
        
        RedrawMAA.__init__(self, objects[0].viewer, name=None, startFlag=startFlag)

        from DejaVu.scenarioInterface.animationGUI import Rotation_MAAEditor
        self.editorClass = Rotation_MAAEditor

	if objectFromString is None:
            objectFromString = getObjectFromString(objects)
        self.objectFromString = objectFromString
        self.objectName = objectName
        self.makeMAA( angle=angle, nbFrames=nbFrames, vector=vector,
                      easeInOut=easeInOut, direction=direction)

        self.shortName = "Rot. "


    def makeMAA(self, angle=360, nbFrames=180, vector=(0,1,0),
                easeInOut='none', direction='counter clockwise'):

        self.angle = angle
        self.nbFrames = nbFrames
        self.vector = vector
        self.easeInOut = easeInOut
        self.direction = direction

        # compute rotation increment matrix
        if direction=='counter clockwise':
            angleIncr = float(angle) / nbFrames
        else:
            angleIncr = 0.0-float(angle) / nbFrames

        # 2 keyframes are created. The first is at frame 0 and set the
        # rotation increment matrix. The second one is as nbframes-1 and has
        # the same rotation increment matrix leading to a constant
        # interpolation.
        for obj in self.objects:
            actor = DejaVuAxisConcatRotationActor(
                'axisRotation', obj, axis=vector)
            actor.setEaseInOut(easeInOut)
            kf0 = KF( 0 , angleIncr)
            kf1 = KF( nbFrames-1, angleIncr)
            actor.addKeyframe( kf0 )
            i1 = Interval( kf0, kf1, generator=actor.behaviorList)
            actor.behaviorList.constant = True
            actor.addIntervals( [i1] )
            self.AddActions( actor, actor.actions )
        self.name = '%s %s %s (%s) rotation'% (self.objectName, str(angle),  direction, self.getAxis(vector))


    def getAxis(self, vector):
        """
        return axis name based in (x, y, z) vector
        """
        x,y,z = vector
        if x==1 and y==0 and z==0:
            return 'X'
        elif x==0 and y==1 and z==0:
            return 'Y'
        elif x==0 and y==0 and z==1:
            return 'Z'
        elif x==1 and y==1 and z==0:
            return 'XY'
        elif x==0 and y==1 and z==1:
            return 'YZ'
        elif x==1 and y==0 and z==1:
            return 'XZ'
        elif x==1 and y==1 and z==1:
            return 'XYZ'
        else:
            return str(vector)


    def getValues(self):
        """
        returns the parameters of this MAA, i.e. 3 keyframes positions
        """
        return {'angle': self.angle,
                'nbFrames': self.nbFrames,
                'vector': self.vector,
                'easeInOut': self.easeInOut,
                'direction': self.direction,
                'forceOrient':self.forceOrient,
                'forceRendering':self.forceRendering}


    def configure(self, **kw):
        """
        set angle, nbFrames, vector, easeInOut, direction, forceOrient and
        forceRendering and rebuild MAA
        """
        self.removeNonRedrawActors()

        # handle forceOrient and force Rendering
        RedrawMAA.configure(self, **kw)
        kw.pop('forceOrient')
        kw.pop('forceRendering')
        
        # add missing keys to avoid default values to override current values
        for attr in ['angle', 'nbFrames', 'vector', 'easeInOut', 'direction']:
            if not kw.has_key(attr):
                kw[attr] = self.getattr(attr)

        self.makeMAA( **kw )


    def getSourceCode(self, varname, indent=0):
        """
        Return python code creating this object
        """
        if not self.objectFromString:
            return ""
        tabs = " "*indent
        lines = tabs + """import tkMessageBox\n"""
        lines += tabs + """from DejaVu.scenarioInterface.animations import RotationMAA\n"""
        lines += tabs + """object = %s\n"""%(self.objectFromString)
        newtabs = tabs + 4*" "
        lines += tabs + """try:\n"""
        lines += newtabs + """%s = RotationMAA(object, '%s', nbFrames=%d, angle=%f,"""%(
            varname, self.objectName, self.nbFrames, self.angle)

        if self.vector is not None:
            lines += """ vector=%s,"""%(str(self.vector),)
        lines += """ direction='%s', """%(self.direction,)
        lines += """easeInOut='%s', """%(self.easeInOut,)
        lines += """objectFromString="%s", startFlag='%s')\n""" % (self.objectFromString, self.startFlag)
        lines += newtabs + """assert len(%s.actors) > 0 \n""" % (varname,)
        lines += tabs + """except:\n"""
        lines += newtabs + """if showwarning: tkMessageBox.showwarning('DejaVu Scenario warning', 'Could not create MAA %s')\n""" % self.name
        lines += newtabs + """print sys.exc_info()[1]\n"""
        return lines
    


class RockMAA(RotationMAA):
    """
    create an MAA for rock animation
    """

    def __init__(self, object, objectName=None, angle=60, nbFrames=60,
                 vector=(0,1,0), objectFromString=None,
                 startFlag='after previous'):
        """

        MAA <- RockMAA(object, objectName=None,  nbFrames=180, angle=60,
                       vector=None, objectFromString=None,
                       startFlag='after previous')

        - object is an instance of a DejaVu Geom object
        - objectName - the object's name. If it is not specified, the class
        - angle is the angular amplitude of the rotation in degrees
        - nbFrames is the number of Frames for the animation
        - direction can be either 'clockwise' or 'counter clockwise'
        - easeInOut - can be 'none', 'ease in', 'ease out', 'ease in and out'
        - objectFromString is a string  that yields the specified oject(s) when evaluated.
        - startFlag - flag used in a sequence animator for computing time position of the maa .
        """

        RotationMAA.__init__(self, object, objectName=objectName, angle=angle,
                             nbFrames=nbFrames, vector=vector,
                             objectFromString=objectFromString,
                             startFlag=startFlag)

        from DejaVu.scenarioInterface.animationGUI import Rock_MAAEditor
        self.editorClass = Rock_MAAEditor
        self.shortName = "Rock"

        
    def makeMAA(self, angle=360, nbFrames=180, vector=(0,1,0),
                easeInOut='none', direction='counter clockwise'):

        self.angle = angle
        self.nbFrames = nbFrames
        self.vector = vector
        self.easeInOut = easeInOut
        self.direction = direction

        angleIncr = float(angle) / (nbFrames/4)
        p1 = (0,0,0)
        p2 = vector
        mat0 = rotax(p1, p2, 0)
        mat1 = rotax( p1, p2, angleIncr*math.pi/180.)
        mat2 = rotax( p1, p2, -angleIncr*math.pi/180.)
        quat0 = matToQuaternion(mat0.flatten())
        quat1 = matToQuaternion(mat1.flatten())
        quat2 = matToQuaternion(mat2.flatten())
        for obj in self.objects:
            actor = getActor(obj, 'concatRotation')
            kf0 = KF( 0 , quat1)  # identity matrix at frame 0
            kf1 = KF( nbFrames/4, quat0)
            kf2 = KF( (nbFrames/4)*2, quat2)
            kf3 = KF( (nbFrames*3)/4, quat0)
            kf4 = KF( (nbFrames-1), quat1)
            
            i1 = Interval( kf0, kf1, generator = actor.behaviorList)
            i2 = Interval( kf1, kf2, generator = actor.behaviorList)
            i3 = Interval( kf2, kf3, generator = actor.behaviorList)
            i4 = Interval( kf3, kf4, generator = actor.behaviorList)
            
            actor.addIntervals( [i1] )
            actor.addIntervals( [i2] )
            actor.addIntervals( [i3] )
            actor.addIntervals( [i4] )
            
            self.AddActions( actor, actor.actions )
        self.name = '%s %s %s rock'% (self.objectName, str(angle), str(vector))


    def getSourceCode(self, varname, indent=0):
        """
        Return python code creating this object
        """
        if not self.objectFromString:
            return ""
        tabs = " "*indent
        lines = tabs + """import tkMessageBox\n"""
        lines += tabs + """from DejaVu.scenarioInterface.animations import RockMAA\n"""
        lines += tabs + """object = %s\n"""%(self.objectFromString)
        newtabs = tabs + 4*" "
        lines += tabs + """try:\n"""
        lines += newtabs + """%s = RockMAA(object, '%s', nbFrames=%d, angle=%f,"""%(
            varname, self.objectName, self.nbFrames, self.angle)
        if self.vector is not None:
            lines += """ vector=%s,"""%(str(self.vector),)
        lines += """ name='%s', """%(self.name,)
        lines += """objectFromString="%s", startFlag='%s')\n""" % (self.objectFromString, self.startFlag)
        lines += newtabs + """assert len(%s.actors) > 0 \n""" % (varname,)
        lines += tabs + """except:\n"""
        lines += newtabs + """if showwarning: tkMessageBox.showwarning('DejaVu Scenario warning', 'Could not create MAA %s')\n""" % self.name
        lines += newtabs + """print sys.exc_info()[1]\n"""
        return lines



class PartialFadeMAA(FadeObjectMAA):
    """
    Create an MAA for fading in parts of a geometry using per vertex opacity
    """
    
    def __init__(self, object, initOpac, finalOpac, objectName=None,
                 name=None, nbFrames=None, kfpos=[0,30], easeInOut='none',
                 objectFromString=None, startFlag="after previous"):

        """
        constructor
        
        MAA <- PartialFadeMAA( object, initOpac, finalOpac,
                    objectName=None, name=None, nbFrames=None, kfpos=[0,30],
                     easeInOut='none', objectFromString=None,
                     startFlag='after previous')

        - object - a DejaVu Transformable object (or list of objects)
                 that belong to a DejaVu Viewer;
        - initOpac - a dictionary {object: opacity array at the beginning of animation},
        - finalOpac- a dictionary {object: opacity array at the end of animation},
        - objectName - the object's name. If it is not specified, the class constructor
          will try to use 'fullName' attribute of the object.
        - name   - the MAA name;
        - kfpos - a list of two keyframe positions specifying the start and end times
          of the animation;
        - easeInOut - used to set easeIn and easeOut atributes of all value generators,
        can be one of the following :  'none', 'ease in', 'ease out', 'ease in and out';
        - objectFromString is a string  that yields the specified oject(s) when evaluated;
        - startFlag - flag used in a sequence animator for computing time position of the maa .        
        """
        
        if not hasattr(object, "__len__"):
            objects = [object]
        else:
            objects = object
        nobjects = len(objects)
        assert len(initOpac) == nobjects
        assert len(finalOpac) == nobjects
        self.initOpac = initOpac
        self.finalOpac = finalOpac
        if objectName is None:
            objectName = getObjectName(objects)
        self.objectName = objectName
        if name is None:
            name = "partial fade %s"% (objectName)
        self.shortName = "pFade"
        if objectFromString is None:
            objectFromString = getObjectFromString(objects)
        #print "object name:", objectName, object.fullName
        FadeObjectMAA.__init__(self, objects,  name, objectName, kfpos=kfpos,
                               easeInOut=easeInOut, objectFromString=objectFromString,
                               startFlag=startFlag)
        self.objects = objects


    def setActorsActions(self, actors):
        """Add keyframes and a valuegenerating interval to the actor."""
        #print "PartialFadeinObjectMAA", actor
        for actor in actors:
            if actor.name.find("opacity") > 0:
                obj = actor.object
                kf1 = KF(self.kfpos[0], self.initOpac[obj])
                kf2 = KF(self.kfpos[1], self.finalOpac[obj])
                i1 = Interval( kf1, kf2, generator = actor.behaviorList)
                actor.addIntervals( [i1] )
            elif actor.name.find("visible") > 0:
                kf1 = KF(self.kfpos[0], 1)
                actor.actions.addKeyframe(kf1)

                
    def getSourceCode(self, varname, indent=0):
        """
        Return python code creating this object
        """
        if not self.objectFromString:
            return ""
        tabs = " "*indent
        lines = tabs + """import tkMessageBox\n"""
        lines += tabs + """from numpy import array\n"""
        lines += tabs + """from DejaVu.scenarioInterface.animations import PartialFadeMAA\n"""
        lines += tabs + """object = %s\n"""%(self.objectFromString)
        newtabs = tabs + 4*" "
        initOpac = """initOpac = {"""
        finalOpac = """finalOpac = {"""
        for i, obj in enumerate(self.objects):
            val1 = self.initOpac[obj]
            if type(val1) == numpy.ndarray:
                valstr1 = numarr2str(val1)
            else:
                valstr1 = "%s"%val1
            initOpac += """object[%d]:%s, """%(i, valstr1)
            val2 = self.finalOpac[obj]
            if type(val2) == numpy.ndarray:
                valstr2 = numarr2str(val2)
            else:
                valstr2 = "%s"%val2
            finalOpac += """object[%d]:%s, """%(i, valstr2)
        initOpac += """}\n"""
        finalOpac += """}\n"""
        lines += tabs + initOpac
        lines += tabs + finalOpac
        lines += tabs + """try:\n"""
        lines += newtabs + """%s = PartialFadeMAA(object, initOpac, finalOpac, objectName='%s', name='%s', kfpos=%s, easeInOut='%s', objectFromString="%s", startFlag='%s')\n""" % (varname, self.objectName, self.name, self.kfpos, self.easeInOut, self.objectFromString, self.startFlag)
        lines += newtabs + """assert len(%s.actors) > 0 \n""" % (varname,)
        lines += tabs + """except:\n"""
        lines += newtabs + """if showwarning: tkMessageBox.showwarning('DejaVu Scenario warning', 'Could not create MAA %s')\n""" % self.name
        lines += newtabs + """print sys.exc_info()[1]\n"""
        return lines                



from numpy import copy

class ColorObjectMAA(RedrawMAA):
    """ Create an MAA to color an object.
        ColorObjectMAAobject <- ColorObjectMAA(object,
                   initColors={}, finalColors={},
                   objectName=None, name=None, nbFrames=None,
                   kfpos=[0,30], colortype = 'choose color',
                   objectFromString=None, startFlag='after previous')
       arguments:
         - object -  a geometry object (or list of objects) to color;
         - objectName - the object's name. If it is not specified, the class constructor
                      will try to use 'fullName' attribute of the object.
         - name   - the MAA name;
         - initColors - a dictionary {object: array of (r,g,b) tuples at the beginning of animation},
         - finalColors - a dictionary {object: rray of (r,g,b) tuples at the end of animation};
         - objectFromString is a string  that yields the specified oject(s) when evaluated;
         - startFlag - flag used in a sequence animator for computing time position of the maa .         
         
    """

    def __init__(self, object, initColors, finalColors,
                 objectName=None, name=None, nbFrames=None,
                 kfpos=[0,30], colortype="choose color",
                 objectFromString=None, startFlag="after previous", easeInOut='none',
                 **kw):

        if not hasattr(object, "__len__"):
            objects = [object]
        else:
            objects = object
        nobjects = len(objects)
        assert len(initColors) == nobjects
        assert len(finalColors) == nobjects
        self.actors = []
        self.objects = objects
        vi = objects[0].viewer
        if objectName is None:
            objectName = getObjectName(objects)
        if objectFromString is None:
            objectFromString = getObjectFromString(objects)
        self.objectFromString = objectFromString
        
        RedrawMAA.__init__(self, vi, name, startFlag)
        self.forceOrient = False
        self.forceRendering = False
        self.objectName = objectName
        if name is None:
            name = "%s %s" % (colortype, objectName)
        self.name = name
        if nbFrames:
            kfpos = [0, nbFrames]
        self.initColors = initColors
        self.finalColors = finalColors
        
        from DejaVu.scenarioInterface.animationGUI import SECol_MAAEditor
        self.editorClass = SECol_MAAEditor
        
        self.makeMAA(kfpos=kfpos, easeInOut=easeInOut, colortype=colortype)
        

    def makeMAA(self, kfpos=[0,30], easeInOut='none', colortype="choose color"):
        # create visible actor(s) and color actor(s).
        for object in self.objects:
            visibleactor = getActor(object, 'visible')
            self.origValues[visibleactor.name] =  visibleactor.getValueFromObject()
            kf1 = KF(kfpos[0], 1)
            visibleactor.actions.addKeyframe(kf1)
            self.AddActions( visibleactor, visibleactor.actions )
            # create color actor.
            coloractor = self.getColorActor(object, self.finalColors[object], kfpos)
            self.origValues[coloractor.name] = self.initColors[object]
        self.kfpos = kfpos
        self.easeInOut = easeInOut
        self.colortype = colortype

    def getColorActor(self, object, colors, kfpos):

        actor = getActor(object, 'colors')
        kf1 = KFAutoCurrentValue(kfpos[0], actor)
        kf2 = KF(kfpos[1], colors)
        i1 = Interval( kf1, kf2, generator = actor.behaviorList)
        actor.addIntervals( [i1] )
        #print "adding actions for actor", actor.name
        #print "color:" , type(colors)
        #print col
        self.AddActions(actor, actor.actions )
        return actor

    def getValues(self):
        """
        returns the parameters of this MAA, i.e. 3 keyframes positions
        """
        return {'kfpos': self.kfpos,
                #'sortPoly': self.sortPoly,
                'easeInOut': self.easeInOut,
                'forceOrient':self.forceOrient,
                'forceRendering':self.forceRendering,
                'colortype': self.colortype}


    def configure(self, **kw):
        """
        set kfpos, direction and easeInOut and rebuild MAA
        """
        self.removeNonRedrawActors()

        # handle forceOrient and force Rendering
        RedrawMAA.configure(self, **kw)
        kw.pop('forceOrient')
        kw.pop('forceRendering')
        
        # add missing keys to avoid default values to override current values
##         if not kw.has_key('sortPoly'):
##             kw['sortPoly'] = self.sortPoly

        if not kw.has_key('kfpos'):
            kw['kfpos'] = self.kfpos

        if not kw.has_key('easeInOut'):
            kw['easeInOut'] = self.easeInOut

        self.makeMAA( **kw )


    def getSourceCode(self, varname, indent=0):
        """
        Return python code creating this object
        """
        if not self.objectFromString:
            return ""
        tabs = " "*indent
        lines = tabs + """import tkMessageBox\n"""
        lines += tabs + """from numpy import array\n"""
        lines += tabs + """from DejaVu.scenarioInterface.animations import ColorObjectMAA\n"""
        lines += tabs + """object = %s\n"""%(self.objectFromString)
        newtabs = tabs + 4*" "
        initColors = """initColors = {"""
        finalColors = """finalColors = {"""
        for i, obj in enumerate(self.objects):
            val1 = self.initColors[obj]
            if type(val1) == numpy.ndarray:
                valstr1 = numarr2str(val1)
            else:
                valstr1 = "%s"%val1
            initColors += """object[%d]:%s, """%(i, valstr1)
            val2 = self.finalColors[obj]
            if type(val2) == numpy.ndarray:
                valstr2 = numarr2str(val2)
            else:
                valstr2 = "%s"%val2
            finalColors += """object[%d]:%s, """%(i, valstr2)
        initColors += """}\n"""
        finalColors += """}\n"""
        lines += tabs + initColors
        lines += tabs + finalColors
        lines += tabs + """try:\n"""
        lines += newtabs + """%s = ColorObjectMAA(object, initColors, finalColors, objectName='%s', name='%s', kfpos=%s, colortype='%s', objectFromString="%s", startFlag='%s')\n""" % (varname, self.objectName, self.name, self.kfpos, self.colortype, self.objectFromString, self.startFlag)
        lines += newtabs + """assert len(%s.actors) > 0 \n""" % (varname,)
        lines += tabs + """except:\n"""
        lines += newtabs + """if showwarning: tkMessageBox.showwarning('DejaVu Scenario warning', 'Could not create MAA %s')\n""" % self.name
        lines += newtabs + """print sys.exc_info()[1]\n"""
        return lines                



class FocusMAA(RedrawMAA):
    """
    create an MAA for focucing the camera on the object.
    """

    def __init__(self, object, objectName, name, nbFrames = None,  
                 translation=None, scale=None,
                 pivot=None, fieldOfView=None, lookFrom=None):
        """
        constructor
        
        MAA <- FocusMAA( object, objectName, name, nbFrames = None,
                                translation=None, scale=None,
                               pivot=None, fieldOfView=None, lookFrom=None)

        object is a DejaVu Transformable object that belongs to a DejaVu Viewer
        name ifs the name for the MAA
        kfpos is a list of 2 positions.
        translation
        scale
        pivot
        fieldOfView
        lookFrom
        """
        assert isinstance(object, Transformable)
        assert isinstance(object.viewer, Viewer)
        self.objectName = objectName
        self.nbFrames = nbFrames
        
        RedrawMAA.__init__(self, object.viewer, name)

        # create all actors and their actions and add them to the MAA
        cam = self.camera = object.viewer.currentCamera
        p1, p2 = [0, nbFrames-1]
        # actor look at 
        actor = getActor(cam, "lookAt")
        actor.actions.addKeyframe(KF(p1, numpy.array([0.,0.,0.] ) )) 
        self.AddActions( actor, actor.actions )
        
        # scale actor for root object
        rootObject = self.rootObject=object.viewer.rootObject
        actor = getActor(rootObject, 'scale')
        self.origValues[actor.name] = actor.getValueFromObject()
        actor.actions.addKeyframe(KF(p1, [1.,1.,1.] ))
        self.AddActions( actor, actor.actions )

        # translation actor for rootObject
        actor = getActor(rootObject, 'translation')
        self.origValues[actor.name] = actor.getValueFromObject()
        if translation is None:
            translation = rootObject.translation.copy()
        self.translation = translation
##         kf0 = KFValueFromFunction( p1, self.getRootObjTranslation )
##         kf1 = KFValueFromFunction( p2, self.getRootObjTranslation )
        trans = self.getRootObjTranslation()
        kf0 = KFValueFromFunction( p1, trans)
        kf1 = KFValueFromFunction( p2, trans)
        actor.setFunction = self.concatTranslation
        actor.addIntervals( [ (kf0, kf1) ] )
        self.AddActions( actor, actor.actions )

        # add field of view actor of current camera
        actor = getActor(cam, 'fieldOfView')
        if fieldOfView is None:
            fieldOfView = cam.fovy
        self.fieldOfView = fieldOfView
        diff_fovy =  cam.fovyNeutral - fieldOfView
        k0 = KFAutoCurrentValue( p1, actor)
        k1 = KF( p2, fieldOfView + (self.nbFrames-1)*diff_fovy/self.nbFrames)
        actor.addIntervals( [ Interval(k0,k1), Interval(k1,k2)])
        self.AddActions( actor, actor.actions )

        # actor lookfrom
        actor = getActor(cam, 'lookFrom')
        if lookFrom is None:
            lookFrom = cam.lookFrom.copy()
        self.lookFrom = lookFrom
        
##         lNewDist = lHalfObject / math.tan(self.currentCamera.fovy/2*math.pi/180.0)
##         newDist = self.currentCamera.nearDefault+lNewDist+lHalfObject
##         dist = oldLookFrom*(steps-i-1.)/steps + newDist*(i+1.)/steps
##         self.currentCamera.lookFrom = Numeric.array( ( 0., 0., dist ) )
##         self.currentCamera.direction = self.currentCamera.lookAt - self.currentCamera.lookFrom 


    def getRootObjTranslation(self):
        Rmini, Rmaxi = self.rootObject.ComputeBB()
        Rg = numpy.add.reduce( (Rmini, Rmaxi) ) * .5
        diffVect = -g-self.rootObject.translation
        if not (g-Rg).any():
            diffVect = -Rg
        return diffVect[:3]/float(self.nbFrames)

    def concatTranslation(self, val):
        self.rootObject.ConcatTranslation( val )




    
############################################################################
##
##  GUI stuff
##
############################################################################

import Pmw, Tkinter
from Scenario2 import  _clipboard

class RotationMAAOptionsGUI:

    def __init__(self, master, object, objectName):

        self.object = object
        self.objectName = objectName
        if not master:
            self.parent = parent = Tkinter.Toplevel()
        else:
            self.parent = parent = master
        self.axis = 'Y'
        self.direction = 'clockwise'
        self.maa = None
	self.dialog = Pmw.Dialog(parent,
	    buttons = ('OK', 'Preview', 'Cancel', 'Copy To Clipboard'),
	    defaultbutton = 'Preview',
	    title = 'Full Rotation Options:',
	    command = self.execute)
	self.dialog.withdraw()

        parent = self.dialog.interior()
        
        self.buttonBox = Pmw.ButtonBox(
            parent, labelpos = 'nw', label_text = 'Full Rotation Options:',
            frame_borderwidth = 2, frame_relief = 'groove')

        # animation name
        self.namew = Pmw.EntryField(parent, labelpos = 'w', label_text = 'Name:',
                               value = 'Full Rotation Y',)

        # file name for movie
        self.filenamew = Pmw.EntryField(parent, labelpos = 'w',
                                   label_text = 'Filename:',
                                   value='pmvMovie.mpeg')
        
        self.namew.pack(side='top', fill='x', expand=1, padx=10, pady=5)
        self.filenamew.pack(side='top', fill='x', expand=1, padx=10, pady=5)

        # Create and pack the dropdown ComboBox for axis
        axes = ('X', 'Y', 'Z', 'XY', 'XZ', 'YZ', 'XYZ')
        self.axisDropdownw = Pmw.ComboBox(
            parent, label_text = 'Axis:', labelpos = 'w',
            selectioncommand = self.changeAxis, scrolledlist_items = axes)
        self.axisDropdownw.pack(side = 'top', anchor = 'n',
                                fill = 'x', expand = 1, padx = 8, pady = 8)
        self.axisDropdownw.selectitem(self.axis)

        self.directionw = Pmw.ComboBox(
            parent, label_text = 'direction:', labelpos = 'w',
            selectioncommand = self.changeDirection,
            scrolledlist_items = ['clockwise', 'counter clockwise'])
        self.directionw.pack(side = 'top', anchor = 'n',
                             fill = 'x', expand = 1, padx = 8, pady = 8)
        self.directionw.selectitem(self.direction)

        # frame number
        self.nbframesw = Pmw.Counter(parent,
                                labelpos = 'w',
                                label_text = 'Number of Frames:',
                                entry_width = 6,
                                entryfield_value = 180,
                                entryfield_validate = {'validator' : 'integer',
                                                       'min' : 1 }
                                )
        self.nbframesw.pack(side='top', padx=10, pady=5)

        self.anglew = Pmw.Counter(parent,
                                  labelpos = 'w',
                                  label_text = 'Angle (degrees):',
                                  entry_width = 6,
                                  entryfield_value = 360,
                                  entryfield_validate = {'validator':'integer',
                                                       'min' : 1 }
                                  )
        self.anglew.pack(side='top', padx=10, pady=5)

        # record checkbutton
        self.recordVar = Tkinter.IntVar()

        c = Tkinter.Checkbutton(parent, text="Record", variable=self.recordVar)
        c.pack(side='top', padx=10, pady=5)


    def changeAxis(self, axis):
        self.axis = axis
        self.namew.setvalue('Full Rotation '+self.axis)


    def changeDirection(self, direction):
        self.direction = direction
        self.namew.setvalue('Full Rotation '+self.axis)

    def _processReturnKey(self, event):
	self.buttonBox.invoke()


    def execute(self, result):
        if result == 'Preview' or result=='OK':
	    self.preview_cb()

        if result == 'OK' or result=='Cancel':
            self.hide()

        if result == 'Copy To Clipboard':
            if self. maa is None:
                return
            
            from tkSimpleDialog import askstring

            angle = float(self.anglew.get())
            nbFrames = int(self.nbframesw.get())
            name = 'Rotation of %d degrees in %d steps about %s'%(
                angle, nbFrames, str(self.axis))

            d = self.buildMAA()
            _clipboard.addMaa(d)


    def getName(self, result):
	if result is None or result == 'Cancel':
	    self.clipboardName = None
	    self.dialog.deactivate(result)
	else:
	    if result == 'OK':
		print 'Password entered ' + self.dialog.get()
		self.dialog.deactivate()

    def buildMAA(self):
        angle = float(self.anglew.get())
        nbFrames = int(self.nbframesw.get())
        
        name = 'Rotation of %d degrees in %d steps about %s'%(
            angle, nbFrames, str(self.axis))
        
        self.maa = d = RotationMAA(
            self.object, self.objectName, angle=angle, axis=self.axis,
            nbFrames=nbFrames, name=self.namew.getvalue(),
            direction=self.directionw.get())

        return d

    
    def preview_cb(self):
        d = self.buildMAA()
        if self.recordVar.get():
            d.redrawActor.startRecording(self.filenamew.getvalue())
        d.run()
        if self.recordVar.get():
            d.redrawActor.stopRecording()


    def hide(self):
        self.dialog.deactivate()

    def show(self, event=None):
        self.dialog.activate(globalMode = 'nograb')






     

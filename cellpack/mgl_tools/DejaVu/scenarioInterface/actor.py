## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by

from Scenario2.actor import Actor, CustomActor
from Scenario2.datatypes import DataType
from Scenario2.interpolators import (
    Interpolator,
    FloatScalarInterpolator,
    BooleanInterpolator,
)
from SimPy.Simulation import now
import numpy.oldnumeric as Numeric


## class ActionWithRedraw(Action):
##     # subclass Action to have these actions set a redraw flag in the director
##     # so that the redraw process only triggers a redraw if something changed

##     def __init__(self, *args, **kw):
##         Action.__init__(self, *args, **kw)
##         self.postStep_cb = (self.setGlobalRedrawFlag, (), {})


##     def setGlobalRedrawFlag(self):
##         #print 'setting needs redraw at', now(), self._actor().name
##         self._actor()._maa().needsRedraw = True


class RedrawActor(Actor):
    def __init__(self, vi, *args, **kw):
        Actor.__init__(self, "redraw", vi)
        # self.addAction( Action() )
        self.visible = False
        self.recording = False
        self.scenarioname = "DejaVuScenario"
        self.guiVar = None

    def setValueAt(self, frame=None, off=0):
        self.setValue()

    def setValue(self, value=None):

        needsRedraw = True
        if self._maa:
            if self._maa().needsRedraw == False:
                needsRedraw = False
                if self._maa()._director and self._maa()._director().needsRedraw:
                    needsRedraw = True
        if not needsRedraw:
            return
        # print "oneRedraw from redraw actor"
        self.object.OneRedraw()
        # handle recording a frame if need be
        camera = self.object.currentCamera
        if hasattr(camera, "videoRecordingStatus"):
            if camera.videoRecordingStatus == "recording":
                camera.recordFrame()

    def onAddToDirector(self):
        gui = self._maa().gui
        if gui:
            try:
                from DejaVu.Camera import RecordableCamera

                isrecordable = True
            except:
                isrecordable = False
            if isrecordable:
                camera = self.object.currentCamera
                if isinstance(camera, RecordableCamera):
                    gui.createRecordMovieButton()

    def startRecording(self, file):
        camera = self.object.currentCamera
        camera.setVideoOutputFile(file)
        camera.setVideoParameters()
        camera.videoRecordingStatus = "recording"

    def stopRecording(self):
        self.object.currentCamera.stop()

    def clone(self):
        return RedrawActor(self.object)


def getActorName(object, propname):
    # create a name for object's actor
    objname = object.name
    import string

    if hasattr(object, "fullName"):
        names = object.fullName.split("|")
        if len(names) > 1:
            objname = string.join(names[1:], ".")
    if objname.count(" "):
        # remove whitespaces from the object's name
        objname = string.join(objname.split(), "")
    return "%s.%s" % (objname, propname)


class DejaVuActor(CustomActor):
    """
    class for DejaVu actors.
        initialValue= None  - initial value of the object's attribute (object.name),
        interp = None       - interpolator class,
        setFunction = None  - function to set the value on the object,
                              if None, object.Set(name=value) will be used
        setMethod:         method of the object to be called at each time step.
                           The function will be called using  obj.method(value)
        getFunction = None  - function that can be called to get the
                              current value of the attribute (object.name)
                              The function and its arguments have to be specified as a
                              3-tuple (func, *args, **kw). It will be called using
                              func(*(object,)+args), **kw) if it is a function
                              or func(*args, **kw) if it is a method;
                              if None, getattr(object, name) will be used to get the value
     to set the value and getattr(geom, name) to get the value
    """

    def __init__(
        self,
        name,
        object,
        initialValue=None,
        datatype=None,
        interp=None,
        setFunction=None,
        setMethod=None,
        getFunction=None,
    ):

        assert isinstance(name, str)
        self.varname = name
        if not getFunction:
            if hasattr(object, name):
                getFunction = (getattr, (name,), {})
        actorname = getActorName(object, name)
        ## objname = object.name
        ##         if objname.count(" "):
        ##                 # remove whitespaces from the object's name
        ##                 import string
        ##                 objname = string.join(objname.split(), "")
        CustomActor.__init__(
            self,
            actorname,
            object,
            initialValue,
            datatype,
            interp,
            setFunction=setFunction,
            setMethod=setMethod,
            getFunction=getFunction,
        )
        if self.hasGetFunction:
            self.recording = True
        self.guiVar = None
        self.scenarioname = "DejaVuScenario"

    def setValue(self, value):
        if self.setFunction:
            self.setFunction(*(self, value))
        elif self.setMethod:
            self.setMethod(value)
        else:
            self.object.Set(**{self.varname: value})

    def setValueAt(self, frame, off=0):
        # print 'GGGGGGGGGGGGGGG', self.name
        value = self.actions.getValue(frame - off)
        if value != "Nothing There":
            self.setValue(value)
            maa = self._maa()
            maa.needsRedraw = True
            # print 'HHHHHHHHHHHHHHHHHH', maa.name

    ##             if maa._director is not None:
    ##                 print maa._director(), 'LLLLLLLLLLLLLLLL'
    ##                 maa._director().needsRedraw = True

    def clone(self):
        if self.setMethod is not None:
            setMethod = self.setMethod.__name__
        else:
            setMethod = None
        datatype = None
        if self.datatype is not None:
            datatype = self.datatype.__class__
        newActor = self.__class__(
            self.varname,
            self.object,
            initialValue=self.initialValue,
            datatype=datatype,
            interp=self.interp,
            setFunction=self.setFunction,
            setMethod=setMethod,
        )

        newActor.getFuncTuple = self.getFuncTuple
        if self.getFuncTuple:
            newActor.hasGetFunction = True

        return newActor


from interpolators import MaterialInterpolator
from Scenario2.datatypes import (
    FloatType,
    IntType,
    BoolType,
    IntVectorType,
    FloatVectorType,
    IntVarType,
    FloatVarType,
    VarVectorType,
)


class DejaVuGeomVisibilityActor(DejaVuActor):
    """
    Actor to set geometry visibility flag
    when set to 1 we need to make sure each parent's visibility flag is 1
    else the object will not appear
    """

    def __init__(
        self,
        name,
        object,
        initialValue=None,
        datatype=DataType,
        interp=BooleanInterpolator,
        setFunction=None,
        setMethod=None,
        getFunction=None,
    ):

        DejaVuActor.__init__(
            self,
            name,
            object,
            initialValue,
            datatype,
            interp,
            getFunction=self.getValue,
        )

    def setValue(self, value):
        obj = self.object
        self.object.Set(visible=value)
        if value:  # set all parents visibility to 1
            while obj.parent:
                obj = obj.parent
                obj.Set(visible=value)
        # else:
        #    for child in obj.AllObjects():
        #       if child!=self:
        #           child.Set( visible = value)

    def getValue(self):
        # MS: maybe we should return 0 if 1 parent is not visible
        return self.object.visible


class DejaVuMaterialActor(DejaVuActor):
    def __init__(
        self,
        name,
        object,
        initialValue=None,
        datatype=DataType,
        interp=MaterialInterpolator,
        setFunction=None,
        setMethod=None,
        getFunction=None,
        mode="front",
    ):
        self.mode = mode
        DejaVuActor.__init__(
            self,
            name,
            object,
            initialValue,
            datatype,
            interp,
            getFunction=self.getValue,
        )
        self.hasGetFunction = True

    def setValue(self, value):
        object = self.object
        ##  i=0
        ##         for v,name in zip(value, ('ambi', 'emis', 'spec', 'shini')):
        ##             #if self.activeVars[i]:
        ##             object.Set(propName=name, materials=v, transparent='implicit', redo=1)
        ##             i +=1
        mat = [value[0], None, value[1], value[2], value[3], None]
        mask = [1, 0, 1, 1, 1, 0]
        if self.mode == "front":
            object.Set(rawMaterialF=mat, matMask=mask, transparent="implicit", redo=1)
        else:
            object.Set(rawMaterialB=mat, matMask=mask, transparent="implicit", redo=1)

    def getValue(self):
        if self.mode == "front":
            mat = self.object.materials[1028].prop
        else:
            mat = self.object.materials[1029].prop
        return [mat[0], mat[2], mat[3], mat[4]]

    def compareValues(self, oldval, newval):
        vvt = VarVectorType()
        fvt = FloatVectorType()
        for i in range(3):
            if not vvt.isEqual(oldval[i], newval[i]):
                return False
        if not fvt.isEqual(oldval[3], newval[3]):
            return False
        return True

    def clone(self):
        newactor = DejaVuActor.clone(self)
        newactor.mode = self.mode
        newactor.hasGetFunction = self.hasGetFunction
        return newactor


from Scenario2.interpolators import FloatVectorInterpolator, VarVectorInterpolator


class DejaVuScissorActor(DejaVuActor):
    """ This actor manages resizing of DejaVu object's scissor"""

    def __init__(
        self,
        name,
        object,
        initialValue=None,
        datatype=FloatVectorType,
        interp=FloatVectorInterpolator,
        setFunction=None,
        setMethod=None,
        getFunction=None,
    ):

        DejaVuActor.__init__(
            self,
            name,
            object,
            initialValue,
            datatype,
            interp,
            getFunction=self.getValue,
        )
        self.hasGetFunction = True
        self.varnames = ["scissorH", "scissorW", "scissorX", "scissorY"]

        self.activeVars = ["scissorH", "scissorW", "scissorX", "scissorY"]

    def setValue(self, value):
        object = self.object
        kw = {}
        for i, var in enumerate(self.varnames):
            if var in self.activeVars:
                kw[var] = value[i]
        object.Set(**kw)

    def getValue(self):
        obj = self.object
        return [
            float(obj.scissorH),
            float(obj.scissorW),
            float(obj.scissorX),
            float(obj.scissorY),
        ]


from Scenario2.interpolators import RotationInterpolator
from mglutil.math.transformation import UnitQuaternion, Transformation
from mglutil.math.rotax import mat_to_quat
from DejaVu.Camera import Camera
from math import cos, acos, sin, pi
from Scenario2.interpolators import matToQuaternion, quatToMatrix


class DejaVuRotationActor(DejaVuActor):
    """
    This actor manages rotation of DejaVu object by setting the rotation
    """

    def __init__(
        self,
        name,
        object,
        initialValue=None,
        datatype=FloatVectorType,
        interp=RotationInterpolator,
        setFunction=None,
        setMethod=None,
        getFunction=None,
    ):

        DejaVuActor.__init__(
            self,
            name,
            object,
            initialValue,
            datatype,
            interp,
            getFunction=self.getValue,
        )
        self.hasGetFunction = True

    ##     def setValue(self, value):
    ##         object = self.object
    ##         q = (value[0], Numeric.array(value[1:], 'f'))
    ##         t = Transformation(quaternion=q)
    ##         object.Set(rotation = t.getRotMatrix(shape=(16,), transpose=1))
    ##         if isinstance(object, Camera):
    ##             object.Redraw()

    ##     def getValue(self):
    ##         obj = self.object
    ##         value = self.object.rotation
    ##         if len(value)==16:
    ##             q = UnitQuaternion(mat_to_quat(value))

    ##             value = [q.real, q.pure[0], q.pure[1], q.pure[2]]
    ##             #print "in DejaVuRotationActor.getValue: ", value
    ##             return value

    def setValue(self, value):
        object = self.object
        mat = quatToMatrix(value)
        # object._setRotation(mat)
        object.Set(rotation=mat)
        if isinstance(object, Camera):
            object.Redraw()

    def getValue(self):
        mat = self.object.rotation
        quat = matToQuaternion(mat)
        return quat


class DejaVuConcatRotationActor(DejaVuRotationActor):
    """
    This actor manages rotation of DejaVu object by concatenating the rotation
    """

    def __init__(
        self,
        name,
        object,
        initialValue=None,
        datatype=FloatVectorType,
        interp=RotationInterpolator,
        setFunction=None,
        setMethod=None,
        getFunction=None,
    ):

        DejaVuRotationActor.__init__(
            self,
            name,
            object,
            initialValue,
            datatype,
            interp,
            getFunction=self.getValue,
        )
        self.hasGetFunction = True

    def setValue(self, value):
        object = self.object
        mat = quatToMatrix(value)
        object.ConcatRotation(mat)
        if isinstance(object, Camera):
            object.Redraw()


from mglutil.math.rotax import rotax
import math


class DejaVuAxisConcatRotationActor(DejaVuActor):
    """
    This actor manages rotation of DejaVu object by concatenating the rotation
    """

    def __init__(
        self,
        name,
        object,
        initialValue=None,
        datatype=FloatVectorType,
        axis=(0, 1, 0),
        interp=FloatScalarInterpolator,
        setFunction=None,
        setMethod=None,
        getFunction=None,
    ):

        DejaVuActor.__init__(self, name, object, initialValue, datatype, interp)
        self.axis = axis
        self.hasGetFunction = False

    def setValue(self, value):
        mat = rotax((0, 0, 0), self.axis, value * math.pi / 180.0)
        object = self.object
        object.ConcatRotation(mat.flatten())
        if isinstance(object, Camera):
            object.Redraw()

    def clone(self):
        newactor = DejaVuActor.clone(self)
        newactor.axis = self.axis
        newactor.hasGetFunction = self.hasGetFunction
        return newactor


class DejaVuClipZActor(DejaVuActor):
    """ This actor manages the near and far camera's atributes"""

    def __init__(
        self,
        name,
        object,
        initialValue=None,
        datatype=FloatVectorType,
        interp=FloatVectorInterpolator,
        setFunction=None,
        setMethod=None,
        getFunction=None,
    ):

        DejaVuActor.__init__(
            self,
            name,
            object,
            initialValue,
            datatype,
            interp,
            getFunction=self.getValue,
        )
        self.hasGetFunction = True
        self.varnames = ["near", "far"]

        self.activeVars = ["near", "far"]

    def setValue(self, value):
        camera = self.object
        kw = {}
        for i, var in enumerate(self.varnames):
            if var in self.activeVars:
                kw[var] = value[i]
        camera.Set(**kw)
        camera.Redraw()

    def getValue(self):
        c = self.object
        return Numeric.array(
            [
                c.near,
                c.far,
            ],
            "f",
        )


class DejaVuFogActor(DejaVuActor):
    """ This actor manages the start and end atributes of camera's fog"""

    def __init__(
        self,
        name,
        object,
        initialValue=None,
        datatype=FloatVectorType,
        interp=FloatVectorInterpolator,
        setFunction=None,
        setMethod=None,
        getFunction=None,
    ):

        DejaVuActor.__init__(
            self,
            name,
            object,
            initialValue,
            datatype,
            interp,
            getFunction=self.getValue,
        )
        self.hasGetFunction = True
        self.varnames = ["start", "end"]

        self.activeVars = ["start", "end"]

    def setValue(self, value):
        camera = self.object
        kw = {}
        for i, var in enumerate(self.varnames):
            if var in self.activeVars:
                kw[var] = value[i]
        camera.fog.Set(**kw)
        camera.Redraw()

    def getValue(self):
        c = self.object
        return Numeric.array(
            [
                c.fog.start,
                c.fog.end,
            ],
            "f",
        )


from Scenario2.interpolators import FloatVarScalarInterpolator
from interpolators import LightColorInterpolator


class DejaVuLightColorActor(DejaVuActor):
    def __init__(
        self,
        name,
        object,
        initialValue=None,
        datatype=DataType,
        interp=LightColorInterpolator,
        setFunction=None,
        setMethod=None,
        getFunction=None,
    ):

        DejaVuActor.__init__(
            self,
            name,
            object,
            initialValue,
            datatype,
            interp,
            getFunction=self.getValue,
        )
        self.varnames = ["ambient", "diffuse", "specular"]
        self.activeVars = ["ambient", "diffuse", "specular"]
        self.hasGetFunction = True

    def setValue(self, value):
        object = self.object
        kw = {}
        for v, name in zip(value, ("ambient", "diffuse", "specular")):
            if name in self.activeVars:
                kw[name] = v
        object.Set(**kw)

    def getValue(self):
        obj = self.object
        return [obj.ambient, obj.diffuse, obj.specular]

    def compareValues(self, oldval, newval):
        fvt = FloatVectorType()
        for i in range(3):
            if not fvt.isEqual(oldval[i], newval[i]):
                return False
        return True


class DejaVuSpheresRadiiActor(DejaVuActor):
    """ This actor manages the raduis attribute of spheres"""

    def __init__(
        self,
        name,
        object,
        initialValue=None,
        datatype=FloatVarType,
        interp=FloatVarScalarInterpolator,
        setFunction=None,
        setMethod=None,
        getFunction=None,
    ):

        DejaVuActor.__init__(
            self,
            name,
            object,
            initialValue,
            datatype=datatype,
            interp=interp,
            getFunction=self.getValue,
        )
        self.hasGetFunction = True
        self.varnames = ["radii"]
        self.activeVars = ["radii"]

    def setValue(self, value):
        object = self.object
        object.Set(radii=value)

    def getValue(self):
        object = self.object
        if object.oneRadius:
            return object.radius
        else:
            return object.vertexSet.radii.array.ravel()


from interpolators import TransformInterpolator


class DejaVuTransformationActor(DejaVuActor):
    def __init__(
        self,
        name,
        object,
        initialValue=None,
        datatype=DataType,
        interp=TransformInterpolator,
        setFunction=None,
        setMethod=None,
        getFunction=None,
    ):
        DejaVuActor.__init__(
            self,
            name,
            object,
            initialValue,
            datatype,
            interp,
            getFunction=self.getValue,
        )
        self.hasGetFunction = True

    def setValue(self, value):
        object = self.object
        rotation = quatToMatrix(value[0])
        object.Set(
            rotation=rotation,
            translation=value[1],
            scale=value[2],
            pivot=value[3],
            redo=False,
        )

    def getValue(self):
        obj = self.object
        rotation = matToQuaternion(obj.rotation)
        return [rotation, obj.translation[:], obj.scale[:], obj.pivot[:]]

    def compareValues(self, oldval, newval):
        fvt = FloatVectorType()
        for i in range(len(oldval)):
            if not fvt.isEqual(oldval[i], newval[i]):
                return False
        return True

    def clone(self):
        newactor = DejaVuActor.clone(self)
        newactor.hasGetFunction = self.hasGetFunction
        return newactor


def getAllSubclasses(klass):
    # recursively build a list of all sub-classes
    bases = klass.__bases__
    klassList = list(bases)
    for k in bases:
        klassList.extend(getAllSubclasses(k))
    return klassList


import inspect
from actorsDescr import actorsDescr
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
from Scenario2.interpolators import FloatScalarInterpolator, IntScalarInterpolator


def getAnimatableAttributes(object):
    # return two dicts that contain a dict for each attribute of object
    # that can be animated. The first dict is for attribute foudn in
    # actorsDescr, the second is for attributes picked up on the fly

    # merge the dict of attribute for all base classes
    d1 = {}
    for klass, d2 in actorsDescr.items():
        if isinstance(object, klass):
            d1.update(d2)

    d2 = {}
    # find all attribute that are float
    attrs = inspect.getmembers(object, lambda x: isinstance(x, float))
    for name, value in attrs:
        if d1.has_key(name):
            continue
        d2[name] = {
            "interp": FloatScalarInterpolator,
            "interpKw": {"values": [value, value]},
            "valueWidget": ThumbWheel,
            "valueWidgetKw": {"type": "float", "initialValue": value},
        }

    # find all attribute that are bool or int
    attrs = inspect.getmembers(object, lambda x: isinstance(x, int))
    for name, value in attrs:
        if d1.has_key(name):
            continue
        d2[name] = {
            "interp": IntScalarInterpolator,
            "interpKw": {"values": [value, value]},
            "valueWidget": ThumbWheel,
            "valueWidgetKw": {"type": "int", "initialValue": value},
        }
    return d1, d2


def getDejaVuActor(object, attribute):
    # return a DejaVu Actor given a DejaVu object and attribute name
    baseClasses = [object.__class__]
    baseClasses.extend(getAllSubclasses(object.__class__))
    # print 'getDejaVuActor', object,attribute
    for klass in baseClasses:
        d1 = actorsDescr.get(klass, None)
        if d1:
            d2 = d1.get(attribute, None)
            if d2:
                actorCalss, args, kw = d2["actor"]
                args = (attribute, object) + args
                actor = actorCalss(*args, **kw)

                return actor
    ##             else: # attribute not found in dictionary
    ##                 if attribute in object.keywords: # it is setable
    ##                     if hasattr(object, attribute):
    ##                         actor = DejaVuActorSetGetattr(
    ##                             object, name=actorName, setName=attribute,
    ##                             getName=attribute)
    ##                     else:
    ##                         return None # FIXME
    ##                 else:

    return None

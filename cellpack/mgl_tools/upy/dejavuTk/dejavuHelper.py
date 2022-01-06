# -*- coding: utf-8 -*-

"""
    Copyright (C) <2010>  Autin L. TSRI
    This file git_upy/dejavuTk/dejavuHelper.py is part of upy.

    upy is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    upy is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with upy.  If not, see <http://www.gnu.org/licenses/gpl-3.0.html>.
"""

# standardmodule
import os
import numpy
from PIL import Image

# DejaVu module
from cellpack.mgl_tools.upy import hostHelper
from cellpack.mgl_tools.DejaVu.Viewer import Viewer
from cellpack.mgl_tools.DejaVu.Geom import Geom
from cellpack.mgl_tools.DejaVu.Spheres import Spheres
from cellpack.mgl_tools.DejaVu.Cylinders import Cylinders
from cellpack.mgl_tools.DejaVu.Box import Box
from cellpack.mgl_tools.DejaVu.glfLabels import GlfLabels as Labels
from cellpack.mgl_tools.DejaVu.IndexedPolygons import IndexedPolygons
from cellpack.mgl_tools.DejaVu.Polylines import Polylines as dejavuPolylines
from cellpack.mgl_tools.DejaVu.Texture import Texture
import collada


# Problem instance doesnt really exist as its. Or its instance of mesh/sphere/cylinder directly.
# check autofill display
# we need to create a new class of object that will represent an instance...
class Instance:
    def __init__(self, name, geom, position=None, matrice=None):
        self.name = name
        self.geom = geom
        self.id = len(geom.instanceMatricesFortran)
        self.matrice = [
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
        ]
        self.isinstance = True
        if matrice is not None:
            self.matrice = numpy.array(matrice).reshape(
                (16,)
            )  # need to beflatten (16,)
        matrices = geom.instanceMatricesFortran.tolist()
        matrices.append(self.matrice)
        m = [numpy.array(mat).reshape((4, 4)) for mat in matrices]
        geom.Set(instanceMatrices=numpy.array(m))

    def SetTransformation(self, matrice):
        matrices = self.geom.instanceMatricesFortran.tolist()
        matrices[self.id] = numpy.array(matrice).reshape((16,))
        # print (matrices)
        m = [numpy.array(mat).reshape((4, 4)) for mat in matrices]
        print("set")
        self.geom.Set(instanceMatrices=numpy.array(m), visible=1)

    def SetTranslation(self, pos):
        pass


class dejavuHelper(hostHelper.Helper):
    """
    The DejaVu helper abstract class
    ============================
        This is the DejaVu helper Object. The helper
        give access to the basic function need for create and edit a host 3d object and scene.
    """

    # this id can probably found in c4d.symbols
    # TAG ID
    SPLINE = "kNurbsCurve"
    INSTANCE = "Dejavu.Geom"
    EMPTY = "Dejavu.Geom"
    SPHERE = "DejaVu.Spheres"
    POLYGON = "DejaVu.IndexedPolygons"
    # msutil = om.MScriptUtil()
    pb = False
    VERBOSE = 0
    DEBUG = 0
    viewer = None
    host = "dejavu"

    def __init__(self, master=None, vi=None):
        hostHelper.Helper.__init__(self)
        # we can define here some function alias
        self.nogui = False

        if master is not None:
            if type(master) is dict:
                self.viewer = master["master"]
            else:
                self.viewer = master
            if self.viewer == "nogui":
                self.nogui = True
            elif not isinstance(self.viewer, Viewer) or self.viewer is None:
                self.viewer = Viewer(master)
        if vi is not None:
            self.viewer = vi
            if self.viewer == "nogui":
                self.nogui = True
            elif not isinstance(self.viewer, Viewer) or self.viewer is None:
                print("no Viewer pass")
        if self.viewer is None:
            print("no Viewer golboals")
            dicG = globals()
            for d in dicG:
                if isinstance(dicG[d], Viewer):
                    self.viewer = dicG[d]
                    break
        if self.viewer is None:
            self.viewer = Viewer()

        # self.getCurrentScene = c4d.documents.GetActiveDocument
        if self.viewer is not None and not self.nogui:
            self.AddObject = self.viewer.AddObject
        self.hext = "dae"

    def updateAppli(self, *args, **kw):
        return self.update(*args, **kw)

    def Cube(self, *args, **kw):
        return self.box(*args, **kw)

    def Box(self, *args, **kw):
        return self.box(*args, **kw)

    def Polylines(self, *args, **kw):
        return dejavuPolylines(*args, **kw)

    def Spheres(self, *args, **kw):
        return Spheres(*args, **kw)

    def Cylinders(self, *args, **kw):
        return Cylinders(*args, **kw)

    def Geom(self, *args, **kw):
        return Geom(*args, **kw)

    def Labels(self, *args, **kw):
        return Labels(*args, **kw)

    def IndexedPolygons(self, *args, **kw):
        return IndexedPolygons(*args, **kw)

    def setViewer(self, vi):
        self.viewer = vi
        self.AddObject = self.viewer.AddObject
        self.Labels = self.viewer.Labels

    def getCurrentScene(self):
        # actually return the Viewer instance
        if self.viewer == "nogui":
            self.nogui = True
        return self.viewer

    def progressBar(self, progress=None, label=None):
        """update the progress bar status by progress value and label string
        @type  progress: Int/Float
        @param progress: the new progress
        @type  label: string
        @param label: the new message to put in the progress status
        """
        # resetProgressBar
        print("Progress ", str(progress), label)
        return

    def resetProgressBar(self):
        """reset the Progress Bar, using value"""
        return
        if hasattr(self.viewer, "Bar"):
            self.viewer.Bar.reset()
        self.update()

    def update(self):
        if self.viewer == "nogui":
            return
        vi = self.getCurrentScene()
        vi.OneRedraw()
        vi.update()

    #        vi.Redraw()

    def getType(self, object):
        return object.__module__

    def getMesh(self, m, **kw):
        if self.viewer == "nogui":
            return None
        if type(m) is str:
            m = self.getCurrentScene().findGeomsByName(m)
        if m is not None:
            return m
        else:
            return None

    def getName(self, o):
        if self.viewer == "nogui":
            return None
        if type(o) is str:
            o = self.getCurrentScene().findGeomsByName(o)
        else:
            print("getName", o, type(o))
        return o.name

    def getObject(self, name):
        obj = None
        if type(name) != str and type(name) != str:
            return name
        if self.viewer == "nogui":
            return None
        try:
            obj = self.getCurrentScene().findGeomsByName(name)
            if len(obj) == 0:
                obj = None
            else:
                for o in obj:
                    if o.name == name:
                        return o
                return None
        except Exception:
            print("problem get Object", name)
            obj = None
        return obj

    def getChilds(self, obj):
        return obj.children

    def deleteObject(self, obj):
        vi = self.getCurrentScene()
        if hasattr(obj, "isinstance"):
            self.deleteInstance(obj)
            return
        try:
            #            print obj.name
            vi.RemoveObject(obj)
        except Exception as e:
            print("problem deleting ", obj, e)

    def newEmpty(
        self, name, location=None, parentCenter=None, display=1, visible=0, **kw
    ):
        empty = Geom(name, visible=display)
        if location is not None:
            if parentCenter is not None:
                location = location - parentCenter
            empty.SetTranslation(numpy.array(location))
        parent = None
        if "parent" in kw:
            parent = kw["parent"]
        self.addObjectToScene(None, empty, parent=parent)
        return empty

    def updateMasterInstance(self, master, newMesh, **kw):
        # get the instancematrix frommaster
        # apply them to new newMesh
        pass

    def deleteInstance(self, instance):
        # pop the instance from the instanceMatrice
        # delete the object
        m = instance.geom.instanceMatricesFortran[:]
        m = numpy.delete(m, instance.id, 0)
        m = m.tolist()
        #        m.pop(instance.id)
        matrice = [numpy.array(mat).reshape((4, 4)) for mat in m]
        instance.geom.Set(instanceMatrices=numpy.array(matrice))
        del instance

    def newInstance(
        self,
        name,
        object,
        location=None,
        c4dmatrice=None,
        matrice=None,
        parent=None,
        material=None,
    ):
        object = self.getObject(object)
        if isinstance(object, Spheres):
            # create a sphere
            c = object.materials[1028].getState()["diffuse"][0][:3]
            geom = self.Spheres(
                name + "copy",
                radii=[object.radius],
                centers=[[0, 0, 0]],
                visible=1,
                inheritMaterial=False,
            )
            geom.Set(
                materials=[
                    c,
                ]
            )
            self.addObjectToScene(None, geom, parent=parent)
        elif isinstance(object, IndexedPolygons):
            geom = IndexedPolygons(
                name,
                vertices=object.getVertices(),
                faces=object.getFaces(),
                vnormals=object.getVNormals(),
                inheritMaterial=False,
            )
            geom.materials[1028].Set(object.materials[1028].getState())
            geom.materials[1029].Set(object.materials[1028].getState())
            self.addObjectToScene(None, geom, parent=parent)
        else:
            geom = Instance(name, object, position=location)
            # currentMatrices = geom.instanceMatricesFortran
            # currentMatrices.append(numpy.identity)
        if location is not None:
            self.setTranslation(geom, pos=location)
        return geom

    def setObjectMatrix(self, object, matrice, c4dmatrice=None, **kw):
        #            print (object, matrice)
        if "transpose" in kw and not hasattr(object, "isinstance"):
            if kw["transpose"]:
                matrice = numpy.array(matrice).transpose()
        object.SetTransformation(matrice)

    def concatObjectMatrix(self, object, matrice, c4dmatrice=None, local=True):
        pass

    def GetAbsPosUntilRoot(self, obj):
        return [0, 0.0, 0.0]

    def addObjectToScene(self, doc, obj, parent=None, centerRoot=True, rePos=None):
        # doc.start_undo()
        if self.nogui:
            return
        if doc is None:
            if self.viewer is None:
                print("#ERROR there is no viewer setup")
                return
            doc = self.viewer
        if parent is not None:
            if type(parent) == str:
                parent = self.getObject(parent)
            doc.AddObject(obj, parent=parent)
            if centerRoot:
                currentPos = obj.translation
                if rePos is not None:
                    parentPos = rePos
                else:
                    parentPos = self.GetAbsPosUntilRoot(obj)  # parent.GetAbsPos()
                obj.SetTranslation(currentPos - parentPos)
        else:
            #                print doc,obj
            doc.AddObject(obj)
        # verify the viewer
        if obj.viewer is None:
            obj.viewer = doc

    def addCameraToScene(self, name, Type, focal, center, sc):
        pass

    def addLampToScene(self, name, Type, rgb, dist, energy, soft, shadow, center, sc):
        pass

    def reParent(self, obj, parent):
        if self.nogui:
            return
        vi = self.getCurrentScene()
        if vi == "nogui" :
            return
        print("current hgelper is " + vi)
        parent = self.getObject(parent)
        if parent is None:
            return

        if type(obj) == list or type(obj) == tuple:
            [
                vi.ReparentObject(
                    self.getObject(o), parent, objectRetainsCurrentPosition=True
                )
                for o in obj
            ]
        else:
            obj = self.getObject(obj)
            if obj is None:
                return
            if obj.viewer is None:
                obj.viewer = vi
            vi.ReparentObject(obj, parent, objectRetainsCurrentPosition=True)

    def setInstance(self, name, object, location=None, c4dmatrice=None, matrice=None):
        return None

    def getTranslation(self, name):
        return self.getObject(name).translation  # or getCumulatedTranslation

    def setTranslation(self, name, pos=[0.0, 0.0, 0.0]):
        self.getObject(name).SetTranslation(self.FromVec(pos))

    def translateObj(self, obj, position, use_parent=True):
        if len(position) == 1:
            c = position[0]
        else:
            c = position
        # print "upadteObj"
        newPos = self.FromVec(c)

        if use_parent:
            parentPos = self.GetAbsPosUntilRoot(obj)  # parent.GetAbsPos()
            newPos = newPos - parentPos
        obj.ConcatTranslation(newPos)

    def scaleObj(self, obj, sc):
        if type(sc) is float:
            sc = [sc, sc, sc]
        # obj.scale = sc #SetScale()?
        #        obj.SetScale(numpy.array(sc))
        obj.Set(scale=numpy.array(sc))

    def rotateObj(self, obj, rot):
        # take radians, give degrees
        mat = self.eulerToMatrix(rot)
        obj.Set(rotation=numpy.array(mat).flatten())  # obj.rotation

    def getTransformation(self, geom):
        if self.nogui:
            return numpy.identity(4)
        geom = self.getObject(geom)
        return geom.GetMatrix(geom.LastParentBeforeRoot())

    def toggleDisplay(self, obj, display, **kw):
        obj = self.getObject(obj)
        if obj is None:
            return
        obj.Set(visible=display)

    def getVisibility(self, obj, editor=True, render=False, active=False):
        # 0 off, 1#on, 2 undef
        display = {0: True, 1: False, 2: True}
        if type(obj) == str:
            obj = self.getObject(obj)
        if editor and not render and not active:
            return display[obj.GetEditorMode()]
        elif not editor and render and not active:
            return display[obj.GetRenderMode()]
        elif not editor and not render and active:
            return bool(obj[906])
        else:
            return (
                display[obj.GetEditorMode()],
                display[obj.GetRenderMode()],
                bool(obj[906]),
            )

    def getCurrentSelection(
        self,
    ):
        """
        Return the current/active selected object in the document or scene
        DejaVu support only one object at a time.
        @rtype:   liste
        @return:  the list of selected object
        """
        return [self.getCurrentScene().currentObject]

    # ####################MATERIALS FUNCTION########################

    def addMaterial(self, name, color):
        return color

    def createTexturedMaterial(self, name, filename, normal=False, mat=None):
        footex = Texture()
        im = Image.open(filename)
        footex.Set(enable=1, image=im)
        return footex

    def assignMaterial(self, object, mat, texture=False):
        if texture:
            object.Set(texture=mat)
        else:
            object.Set(
                materials=[
                    mat,
                ]
            )

    def changeObjColorMat(self, obj, color):
        obj.Set(inheritMaterial=False, materials=[color], redo=1)

    def getMaterialObject(self, o):
        pass
        return None

    def getMaterial(self, mat):
        return mat

    def getAllMaterials(self):
        return []

    def getMaterialName(self, mat):
        return None

    def ObjectsSelection(self, listeObjects, typeSel="new"):
        """
        Modify the current object selection.

        @type  listeObjects: list
        @param listeObjects: list of object to joins
        @type  typeSel: string
        @param listeObjects: type of modification: new,add,...

        """
        pass

    #        dic={"add":c4d.SELECTION_ADD,"new":c4d.SELECTION_NEW}
    #        sc = self.getCurrentScene()
    #        [sc.SetSelection(x,dic[typeSel]) for x in listeObjects]

    def oneCylinder(
        self,
        name,
        head,
        tail,
        radius=None,
        instance=None,
        material=None,
        parent=None,
        color=None,
    ):
        if instance is None:
            stick = self.getObject(name)
            if stick is None:
                v = numpy.array([tail, head])
                f = numpy.arange(len(v))
                f.shape = (-1, 2)
                stick = Cylinders(
                    name, inheritMaterial=False, vertices=v, faces=f, radii=[1]
                )
                # stick = self.Cylinder(name,length=lenght,pos =head)
                self.addObjectToScene(self.getCurrentScene(), stick, parent=parent)
            else:
                v = numpy.array([tail, head])
                f = numpy.arange(len(v))
                f.shape = (-1, 2)
                stick.Set(vertices=v, faces=f, redo=1)
        else:
            stick = instance
            v = instance.vertexSet.vertices.array
            i = len(v)
            #            v = numpy.concatenate((v,numpy.array([head,tail])))
            instance.vertexSet.vertices.AddValues([head, tail])
            instance.faceSet.faces.AddValues([i, i + 1])
            r = instance.vertexSet.radii.array[0]
            instance.vertexSet.radii.AddValues(r)
            instance.Set(redo=1)
        return stick

    def Cylinder(
        self,
        name,
        radius=1.0,
        length=1.0,
        res=0,
        pos=[0.0, 0.0, 0.0],
        parent=None,
        **kw
    ):
        #        QualitySph={"0":16,"1":3,"2":4,"3":8,"4":16,"5":32}
        pos = numpy.array(pos)
        v = numpy.array([pos, pos + numpy.array([0.0, length, 0.0])])
        f = numpy.arange(len(v))
        f.shape = (-1, 2)
        baseCyl = Cylinders(
            name,
            inheritMaterial=False,
            quality=res,
            vertices=v,
            faces=f,
            radii=[radius],
        )  # , visible=1)
        # if str(res) not in QualitySph.keys():
        self.addObjectToScene(self.getCurrentScene(), baseCyl, parent=parent)
        return [baseCyl, baseCyl]

    def updateTubeMesh(self, mesh, cradius=1.0, quality=0, **kw):
        # change the radius to cradius
        mesh = self.getMesh(mesh)
        if type(mesh) is list:
            mesh = mesh[0]
        #        mesh=geom.mesh.GetDown()#should be the cylinder
        # mesh[5000]=cradius
        #        cradius = cradius*1/0.2
        # should used current Y scale too
        mesh.Set(radii=[cradius], quality=quality)

    def Sphere(
        self, name, radius=1.0, res=0, parent=None, color=None, mat=None, pos=None
    ):
        baseSphere = self.Spheres(
            name,
            radii=[
                radius,
            ],
            centers=[[0.0, 0.0, 0.0]],
            quality=res,
            inheritMaterial=False,
            visible=1,
        )
        if mat is not None:
            mat = self.getMaterial(mat)
            self.assignMaterial(mat, baseSphere)
        else:
            if color is not None:
                # color = [1.,1.,0.]
                baseSphere.Set(
                    materials=[
                        color,
                    ]
                )
        self.addObjectToScene(None, baseSphere, parent=parent)
        if pos is not None:
            self.setTranslation(baseSphere, pos)
        return [baseSphere, baseSphere]

    def instancesSphere(
        self, name, centers, radii, meshsphere, colors, scene, parent=None
    ):
        vertices = []
        for i in range(len(centers)):
            vertices.append(centers[i])
        meshsphere.Set(vertices=vertices, materials=colors, radii=radii)
        return meshsphere

    def instancesCylinder(
        self, name, points, faces, radii, mesh, colors, scene, parent=None
    ):
        mesh.Set(vertices=points, faces=faces, radii=radii, materials=colors)
        return mesh

    def FromVec(self, points, pos=True):
        return numpy.array(
            points
        )  # numpy.array(float(points[0]),float(points[1]),float(points[2]))

    #
    def ToVec(self, v, pos=True):
        return v

    def spline(self, name, points, close=0, type=1, scene=None, parent=None):
        spline = self.Polylines(name, vertices=points)  # ,faces=f)
        self.AddObject(spline, parent=parent)
        return spline, None

    def update_spline(self, name, new_points):
        spline = self.getObject(name)
        if spline is None:
            return False
        f = [[x, x + 1] for x in range(len(new_points))]
        spline.Set(vertices=new_points, faces=f)
        return True

    def Points(self, name, **kw):
        # need to add the AtomArray modifier....
        parent = None
        if "parent" in kw:
            parent = kw.pop("parent")
        from DejaVu.Points import Points

        obj = Points(name, **kw)
        self.addObjectToScene(self.getCurrentScene(), obj, parent=parent)
        return obj

    def updatePoly(self, polygon, faces=None, vertices=None):
        if type(polygon) == str:
            polygon = self.getObject(polygon)
        if polygon is None:
            return
        if vertices is not None:
            polygon.Set(vertices=vertices)
        if faces is not None:
            polygon.Set(faces=faces)

    def updateMesh(self, obj, vertices=None, faces=None, smooth=False):
        if type(obj) == str:
            obj = self.getObject(obj)
        if obj is None:
            return
        self.updatePoly(obj, faces=faces, vertices=vertices)

    def createsNmesh(
        self,
        name,
        vertices,
        vnormals,
        faces,
        smooth=False,
        material=None,
        proxyCol=False,
        color=[
            [1, 1, 1],
        ],
        **kw
    ):
        """
        This is the main function that create a polygonal mesh.

        @type  name: string
        @param name: name of the pointCloud
        @type  vertices: array
        @param vertices: list of x,y,z vertices points
        @type  vnormals: array
        @param vnormals: list of x,y,z vertex normals vector
        @type  faces: array
        @param faces: list of i,j,k indice of vertex by face
        @type  smooth: boolean
        @param smooth: smooth the mesh
        @type  material: hostApp obj
        @param material: material to apply to the mesh
        @type  proxyCol: booelan
        @param proxyCol: do we need a special object for color by vertex (ie C4D)
        @type  color: array
        @param color: r,g,b value to color the mesh

        @rtype:   hostApp obj
        @return:  the polygon object
        """
        shading = "flat"
        if smooth:
            shading = "smooth"
        PDBgeometry = IndexedPolygons(
            name,
            vertices=vertices,
            faces=faces,
            vnormals=vnormals,
            materials=color,
            shading=shading,
        )
        parent = None
        if "parent" in kw:
            parent = kw["parent"]
        self.addObjectToScene(None, PDBgeometry, parent=parent)
        return [PDBgeometry, PDBgeometry]

    def instancePolygon(
        self,
        name,
        matrices=None,
        mesh=None,
        parent=None,
        transpose=False,
        colors=None,
        **kw
    ):
        if matrices is None:
            return None
        if mesh is None:
            return None
        geom = None
        if mesh is None or not isinstance(mesh, IndexedPolygons):
            print("no mesh???", mesh, isinstance(mesh, Spheres))
            if isinstance(mesh, Spheres):
                # need only the tranlation for the matrix
                centers = [m[:3, 3] for m in matrices]
                # mesh.Set(centers=centers)
                if parent is not None:
                    self.reParent(mesh, parent)
                    parent.Set(instanceMatrices=matrices, visible=1)
                else:
                    mesh.Set(centers=centers)
                return mesh
            elif isinstance(mesh, Geom):
                if parent is not None:
                    print("instancePolygon", parent, mesh)
                    if parent != mesh:
                        self.reParent(mesh, parent)
                        parent.Set(instanceMatrices=matrices, visible=1)
                    else:
                        mesh.Set(instanceMatrices=matrices, visible=1)
                else:
                    mesh.Set(instanceMatrices=matrices, visible=1)
            # justgetthe pass mes
            geom = self.getObject(mesh)
            if geom is None:
                return
        #            return None
        else:
            geom = IndexedPolygons(
                name,
                vertices=mesh.getVertices(),
                faces=mesh.getFaces(),
                vnormals=mesh.getVNormals(),
            )
            geom.materials[1028].prop = mesh.materials[1028].prop
            geom.materials[1029].prop = mesh.materials[1029].prop
            self.addObjectToScene(None, geom, parent=parent)
        print("geom", geom)
        geom.Set(instanceMatrices=matrices, visible=1)
        #        if colors is not None :
        #            geom.Set(materials=colors, inheritMaterial=0)
        return geom

    def changeColor(
        self, obj, colors, perVertex=False, proxyObject=False, doc=None, pb=False
    ):
        mesh = self.getMesh(obj)
        mesh.Set(materials=colors, inheritMaterial=False)

    def box(
        self,
        name,
        center=[0.0, 0.0, 0.0],
        size=[1.0, 1.0, 1.0],
        cornerPoints=None,
        visible=1,
        mat=None,
        **kw
    ):
        # import numpy
        box = Box(name, frontPolyMode="fill")  # , cornerPoints=bb, visible=1
        if cornerPoints is not None:
            for i in range(3):
                size[i] = cornerPoints[1][i] - cornerPoints[0][i]
            center = (numpy.array(cornerPoints[0]) + numpy.array(cornerPoints[1])) / 2.0
            box.Set(cornerPoints=list(cornerPoints))
        else:
            box.Set(center=center, xside=size[0], yside=size[1], zside=size[2])
        # material is a liste of color per faces.
        # aMat=addMaterial("wire")
        parent = None
        if "parent" in kw:
            parent = kw["parent"]
        self.addObjectToScene(self.getCurrentScene(), box, parent=parent)
        return box, box

    def updateBox(
        self,
        box,
        center=[0.0, 0.0, 0.0],
        size=[1.0, 1.0, 1.0],
        cornerPoints=None,
        visible=1,
        mat=None,
    ):
        # import numpy
        box = self.getObject(box)
        if cornerPoints is not None:
            for i in range(3):
                size[i] = cornerPoints[1][i] - cornerPoints[0][i]
            for i in range(3):
                center[i] = (cornerPoints[0][i] + cornerPoints[1][i]) / 2.0
            box.Set(cornerPoints=list(cornerPoints))
        else:
            box.Set(center=center, xside=size[0], yside=size[1], zside=size[2])

    def getCornerPointCube(self, cube):
        if hasattr(cube, "size"):
            size = cube.side
        else:
            size = (cube.xside, cube.yside, cube.zside)
        center = cube.center
        cornerPoints = []
        # lowCorner
        lc = [
            center[0] - size[0] / 2.0,
            center[1] - size[1] / 2.0,
            center[2] - size[2] / 2.0,
        ]
        uc = [
            center[0] + size[0] / 2.0,
            center[1] + size[1] / 2.0,
            center[2] + size[2] / 2.0,
        ]
        cornerPoints = [[lc[0], lc[1], lc[2]], [uc[0], uc[1], uc[2]]]
        return cornerPoints

    def plane(
        self,
        name,
        center=[0.0, 0.0, 0.0],
        size=[1.0, 1.0],
        cornerPoints=None,
        visible=1,
        **kw
    ):
        # plane or grid
        xres = 2
        yres = 2
        if "subdivision" in kw:
            xres = kw["subdivision"][0]
            yres = kw["subdivision"][1]
            if xres == 1:
                xres = 2
            if yres == 1:
                yres = 2

        # need to build vertices/faces for the plane
        # 4corner points
        #  *--*
        #  |\ |
        #  | \|
        #  *--*
        # basic plane, no subdivision
        # what about subdivision
        vertices = [
            (-0.5, 0.5, 0.0),
            (0.5, 0.5, 0.0),
            (0.5, -0.5, 0.0),
            (-0.5, -0.5, 0.0),
        ]
        faces = ((2, 1, 0), (3, 2, 0))

        obj = IndexedPolygons(
            name,
            vertices=vertices,
            faces=faces,
            vnormals=None,
            shading="flat",
            materials=[
                [1, 0, 0],
            ],
        )

        if cornerPoints is not None:
            for i in range(3):
                size[i] = cornerPoints[1][i] - cornerPoints[0][i]
            center = (numpy.array(cornerPoints[0]) + numpy.array(cornerPoints[1])) / 2.0
        obj.translation = (float(center[0]), float(center[1]), float(center[2]))
        obj.Set(scale=(float(size[0]), float(size[1]), 1.0))

        if "material" in kw:
            self.addMaterial(name, [1.0, 1.0, 0.0])
        parent = None
        if "parent" in kw:
            parent = kw["parent"]
        self.addObjectToScene(self.getCurrentScene(), obj, parent=parent)
        return obj

    def getFace(self, face):
        return face

    def getMeshVertices(self, poly, transform=False):
        mesh = self.checkIsMesh(poly)
        return mesh.getVertices()

    def getMeshNormales(self, poly):
        mesh = self.checkIsMesh(poly)
        return mesh.getVNormals()

    def getMeshEdges(self, poly):
        return None

    def getMeshFaces(self, poly):
        mesh = self.checkIsMesh(poly)
        return mesh.getFaces()

    def grabAllIndexedPolyonginHierarchy(self, poly, all_mesh=[]):
        if not isinstance(poly, IndexedPolygons):
            if isinstance(poly, Geom):
                for child in self.getChilds(poly):
                    all_mesh = self.grabAllIndexedPolyonginHierarchy(child, all_mesh)
        else:
            all_mesh.append(poly)
        return all_mesh

    def isIndexedPolyon(self, obj):
        if not hasattr(obj, "getFaces"):
            for child in self.getChilds(obj):
                c, ipoly = self.isIndexedPolyon(child)
                if ipoly:
                    return c, True
            return None, False
        else:
            return obj, True

    def DecomposeMesh(self, poly, edit=True, copy=True, tri=True, transform=True):
        # get infos
        if not isinstance(poly, IndexedPolygons):
            if isinstance(poly, Cylinders):
                poly = poly.asIndexedPolygons()
            elif isinstance(poly, Geom):
                # getfirst child mesh recursively
                child = self.getChilds(poly)
                if len(child):
                    poly, isit = self.isIndexedPolyon(poly)
                elif isinstance(poly, Cylinders):
                    poly = poly.asIndexedPolygons()
                else:
                    return [], [], []
            else:
                return [], [], []
        faces = poly.getFaces()
        vertices = poly.getVertices()
        vnormals = poly.getVNormals()
        if transform:
            mat = poly.GetMatrix(poly.LastParentBeforeRoot())
            vertices = self.ApplyMatrix(vertices, mat)
        return faces, vertices, vnormals

    def changeColorO(self, object, colors):
        object.Set(materials=colors)

    def setRigidBody(self, *args, **kw):
        pass

    def pathDeform(self, *args, **kw):
        pass

    def updatePathDeform(self, *args, **kw):
        pass

    # ==============================================================================
    # IO / read/write 3D object, cene file etc
    # ==============================================================================
    def getColladaMaterial(self, geom, col):
        # get the bound geometries
        mat = None
        boundg = list(col.scene.objects("geometry"))
        for bg in boundg:
            #            print bg.original,geom
            if bg.original == geom:
                m = bg.materialnodebysymbol.values()
                if len(m):
                    k0 = [*bg.materialnodebysymbol][0]
                    mat = bg.materialnodebysymbol[k0].target
        return mat

    def TextureFaceCoordintesToVertexCoordinates(self, v, f, t, ti):
        textureuv_vertex = numpy.zeros((len(v), 2))
        for i, indice_verex in enumerate(f):
            for j in range(3):
                if len(ti) == (len(f) * 3):
                    indice = ti[i + j]
                else:
                    indice = ti[i][j]
                textureuv_vertex[indice_verex[j]] = t[indice]  # (t[ti[i][j]]+1.0)/2.0
        return textureuv_vertex

    def getNormals(self, f, v, n, ni):
        if len(ni.shape) == 1:
            if max(ni) == (len(v) - 1):
                return n[ni]
            else:
                return None
        normals_vertex = numpy.zeros((len(v), 3))
        for i, indice_vertex in enumerate(f):
            if len(f.shape) == 2:
                for j in range(3):
                    normals_vertex[indice_vertex[j]] = n[
                        ni[i][j]
                    ]  # (t[ti[i][j]]+1.0)/2.0
            else:
                normals_vertex[indice_vertex] = n[ni[i]]
        return normals_vertex

    def nodeToGeom(
        self,
        node,
        i,
        col,
        nodexml,
        parentxml=None,
        parent=None,
        dicgeoms=None,
        uniq=False,
    ):
        name = nodexml.get("name")
        if name is None:
            name = nodexml.get("id")
        pname = ""
        if parentxml is not None:
            pname = parentxml.get("name")
            if pname is None or pname == "":
                pname = parentxml.get("id")
        #        print "pname",name
        onode = None
        #        print "nodeToGeom type", type(node)
        if dicgeoms is None:
            dicgeoms = {}
        if type(node) == collada.scene.ExtraNode:
            return
        elif type(node) == collada.scene.GeometryNode:
            # create a mesh under parent
            g = node.geometry
            if g.id not in dicgeoms.keys():
                dicgeoms[g.id] = {}
                dicgeoms[g.id]["id"] = g.id
                onode, mesh = self.oneColladaGeom(g, col)
                dicgeoms[g.id]["node"] = onode
                dicgeoms[g.id]["mesh"] = mesh
                dicgeoms[g.id]["instances"] = []
                dicgeoms[g.id]["parentmesh"] = None
                gname = node.children[0].geometry.id

                if parentxml is not None:
                    dicgeoms[g.id]["parentmesh"] = self.getObject(parentxml.get("id"))
        else:  # collada.scene.Node
            #            print "else ",len(node.children)
            #            print "instance_geometry",nodexml.get("instance_geometry")
            # create an empty
            #            print "else ",name ,type(node),parent
            if len(node.children) == 1 and (
                type(node.children[0]) == collada.scene.GeometryNode
            ):
                # no empty just get parent name ?
                #                    print "ok one children geom ",node.children[0]
                gname = node.children[0].geometry.id
                if parentxml is not None:
                    if gname in dicgeoms.keys():
                        #                            print dicgeoms[gname]["parentmesh"]
                        if dicgeoms[gname]["parentmesh"] is None:
                            dicgeoms[gname]["parentmesh"] = self.getObject(pname)
                #                            print dicgeoms[gname]["parentmesh"]
                if uniq:
                    onode = self.newEmpty(name)
                    #                print "ok new empty name",onode, name
                    rot, trans, scale = self.Decompose4x4(
                        node.matrix.transpose().reshape(16)
                    )
                    if parent is not None and onode is not None:
                        self.reParent(onode, parent)
                    onode.Set(translation=trans)
                    onode.Set(rotation=rot)  # .reshape(4,4).transpose())
                    onode.Set(scale=scale)
                    dicgeoms[gname]["parentmesh"] = onode
            elif len(node.children) == 1 and (
                type(node.children[0]) == collada.scene.NodeNode
            ):
                # this is an instance do nothing. we are going to use instanceFortrans matrix
                gname = node.children[0].node.children[0].geometry.id
                if parentxml is not None:
                    if gname in dicgeoms.keys():
                        #                            print dicgeoms[gname]["parentmesh"]
                        if dicgeoms[gname]["parentmesh"] is None:
                            dicgeoms[gname]["parentmesh"] = self.getObject(pname)
            #                            print dicgeoms[gname]["parentmesh"]
            else:
                onode = self.newEmpty(name)
                #                print "ok new empty name",onode, name
                rot, trans, scale = self.Decompose4x4(
                    node.matrix.transpose().reshape(16)
                )
                if parent is not None and onode is not None:
                    self.reParent(onode, parent)
                onode.Set(translation=trans)
                onode.Set(rotation=rot)  # .reshape(4,4).transpose())
                onode.Set(scale=scale)
            if hasattr(node, "children") and len(node.children):
                for j, ch in enumerate(node.children):
                    dicgeoms = self.nodeToGeom(
                        ch,
                        j,
                        col,
                        ch.xmlnode,
                        parentxml=nodexml,
                        parent=onode,
                        dicgeoms=dicgeoms,
                    )
        return dicgeoms

    def transformNode(self, node, i, col, parentxmlnode, parent=None):
        name = parentxmlnode.get("name")
        #        print "pname",name
        if name is None:
            name = parentxmlnode.get("id")
        #        print "transformNode parent",name
        #        print "transformNode type", type(node)
        if type(node) == collada.scene.GeometryNode:
            pass
        elif type(node) == collada.scene.ExtraNode:
            pass
        else:
            # create an empty
            onode = self.getObject(name)
            rot, trans, scale = self.Decompose4x4(node.matrix.transpose().reshape(16))
            #                trans = [node.transforms[0].x,node.transforms[0].y,node.transforms[0].z]
            #                rot = []
            #                for i in range(1,4):
            #                    rot.extend([node.transforms[i].x,node.transforms[i].y,node.transforms[i].z,0.0])
            #                rot.extend([0.,0.,0.,1.0])
            #                print "rotation ",rot
            #                print "trans ", trans/1000.0
            #                scale = [node.transforms[4].x,node.transforms[4].y,node.transforms[4].z]
            #                onode.Set(translation = trans)#, rotation=rot*0,scale=scale)
            onode.Set(translation=trans)
            onode.Set(rotation=rot)  # .reshape(4,4).transpose())
            onode.Set(scale=scale)
            #                onode.ConcatRotation(rot)
            #                onode.ConcatTranslation(trans)
            #                onode.Set(matrix)
            self.update()
        #                print onode.translation
        if hasattr(node, "children") and len(node.children):
            for j, ch in enumerate(node.children):
                #                print "children ",ch.xmlnode.get("name")
                self.transformNode(ch, j, col, ch.xmlnode, parent=onode)

    def decomposeColladaGeom(self, g, col):
        name = g.name
        if name == "":
            name = g.id
        v = numpy.array(g.primitives[0].vertex)  # multiple primitive ?
        print("vertices nb is ", len(v))
        nf = len(g.primitives[0].vertex_index)
        sh = g.primitives[0].vertex_index.shape
        if len(sh) == 2 and sh[1] == 3:
            f = g.primitives[0].vertex_index
        else:
            f = g.primitives[0].vertex_index[: nf].reshape(int(nf / 3), 3)
        n = g.primitives[0].normal
        ni = g.primitives[0].normal_index
        vn = []
        if ni is not None:
            vn = self.getNormals(f, v, n, ni)
        return v, vn, f.tolist()

    def oneColladaGeom(self, g, col):
        name = g.name
        if name == "":
            name = g.id
        v = g.primitives[0].vertex  # multiple primitive ?
        nf = len(g.primitives[0].vertex_index)
        sh = g.primitives[0].vertex_index.shape
        if len(sh) == 2 and sh[1] == 3:
            f = g.primitives[0].vertex_index
        else:
            f = g.primitives[0].vertex_index.reshape((nf / 3, 3))
        n = g.primitives[0].normal
        ni = g.primitives[0].normal_index
        vn = []
        if ni is not None:
            vn = self.getNormals(f, v, n, ni)
        onode, mesh = self.createsNmesh(name, v, vn, f.tolist(), smooth=True)
        mesh.inheritMaterial = False
        color = [1.0, 1.0, 1.0]
        mat = self.getColladaMaterial(g, col)

        if mat is not None:
            if type(mat.effect.diffuse) == collada.material.Map:
                color = [1, 1, 1]

                impath = mat.effect.diffuse.sampler.surface.image.path
                # clean the path
                impath = impath.replace("file:////", "")

            else:
                color = mat.effect.diffuse[0:3]
                self.changeObjColorMat(mesh, color)
            matd = mesh.materials[1028]
            if (
                mat.effect.ambient is not None
                and type(mat.effect.ambient) != collada.material.Map
            ):
                matd.prop[matd.AMBI] = mat.effect.ambient[0:3]
        return onode, mesh

    def buildGeometries(self, col):
        dicgeoms = {}
        geoms = col.geometries
        meshDic = {}
        for g in geoms:
            meshDic[g.id] = {}
            dicgeoms[g.id] = {}
            dicgeoms[g.id]["geom"] = g
            dicgeoms[g.id]["id"] = g.id
            v, vn, f = self.decomposeColladaGeom(g, col)
            print("vertices nb is ", len(v))
            if self.nogui:
                # apply transformation from boundGeom
                dicgeoms[g.id]["node"] = None
                dicgeoms[g.id]["mesh"] = v, vn, f
                mat = self.getColladaMaterial(g, col)
                # print ("mat type is ",type(mat),mat, mat is not None, type(mat) is not type(None))
                if mat is not None:
                    dicgeoms[g.id]["color"] = mat.effect.diffuse[0:3]
            else:
                onode, mesh = self.oneColladaGeom(g, col)
                dicgeoms[g.id]["node"] = onode
                dicgeoms[g.id]["mesh"] = mesh
            meshDic[g.id]["mesh"] = v, vn, f
            dicgeoms[g.id]["instances"] = []
            dicgeoms[g.id]["parentmesh"] = None
        return dicgeoms, meshDic

    def read(self, filename, **kw):
        fileName, fileExtension = os.path.splitext(filename)

        if fileExtension == ".dae":
            daeDic = None
            col = collada.Collada(filename)  # , ignore=[collada.DaeUnsupportedError,
            # collada.DaeBrokenRefError])
            dicgeoms, daeDic = self.buildGeometries(col)
            boundgeoms = list(col.scene.objects("geometry"))
            for bg in boundgeoms:
                if bg.original.id in dicgeoms:
                    node = dicgeoms[bg.original.id]["node"]
                    dicgeoms[bg.original.id]["instances"].append(bg.matrix)
            # dicgeoms["col"]=col
            if self.nogui:
                return dicgeoms

            # for each nodein the scene creae an empty
            # for each primtive in the scene create an indeedPolygins-
            uniq = False
            if len(col.scene.nodes) == 1:
                uniq = True
            for i, node in enumerate(col.scene.nodes):
                # node,i,col,nodexml,parentxml=None,parent=None,dicgeoms=None
                dicgeoms = self.nodeToGeom(
                    node,
                    i,
                    col,
                    col.scene.xmlnode[i],
                    parentxml=None,
                    dicgeoms=dicgeoms,
                    uniq=uniq,
                )
            for g in dicgeoms:
                node = dicgeoms[g]["node"]
                i = dicgeoms[g]["instances"]
                #                print node,g,i
                if len(i):
                    if dicgeoms[g]["parentmesh"] is not None:
                        self.reParent(node, dicgeoms[g]["parentmesh"])
                        node.Set(instanceMatrices=i)
            return boundgeoms, dicgeoms, col, daeDic
        #            for i,node in enumerate(col.scene.nodes) :
        #                self.transformNode(node,i,col,col.scene.xmlnode[i])
        else:
            from DejaVu.IndexedPolygons import IndexedPolygonsFromFile

            geoms = IndexedPolygonsFromFile(filename, fileName)
            self.AddObject(geoms)

    #        raw_input()

    def write(self, listObj, **kw):
        pass

    # DejaVu.indexedPolygon have also this function

    def writeToFile(self, polygon, filename):
        """
        Write the given polygon mesh data (vertices, faces, normal, face normal) in the DejaVu format.

        Create two files : filename.indpolvert and filename.indpolface.

        See writeMeshToFile

        @type  polygon: hostObj/hostMesh/String
        @param polygon: the polygon to export in DejaVu format
        @type  filename: string
        @param filename: the destinaon filename.
        """
        # get shild ?
        if isinstance(polygon, IndexedPolygons):
            polygon.writeToFile(filename)

    def raycast(self, obj, point, direction, length, **kw):
        intersect = False
        if "count" in kw:
            return intersect, 0
        if "fnormal" in kw:
            return intersect, [0, 0, 0]
        if "hitpos" in kw:
            return intersect, [0, 0, 0]
        return intersect

    def raycast_test(self, obj, start, end, length, **kw):
        return

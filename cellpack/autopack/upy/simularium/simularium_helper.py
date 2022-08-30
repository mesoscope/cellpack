# -*- coding: utf-8 -*-
# standardmodule
import os
import numpy as np
import trimesh

from simulariumio import (
    TrajectoryConverter,
    TrajectoryData,
    AgentData,
    UnitData,
    MetaData,
    CameraData,
    DisplayData,
)
from simulariumio.cellpack import CellpackConverter, HAND_TYPE
from simulariumio.constants import DISPLAY_TYPE, VIZ_TYPE

from cellpack.autopack.upy import (
    hostHelper,
)
import collada


class Instance:
    def __init__(self, name, instance_id, unique_id, radius, viz_type, mesh=None):
        self.name = name
        self.radius = radius
        self.instance_id = instance_id
        self.id = unique_id
        self.isinstance = True
        self.is_static = False
        self.viz_type = viz_type
        self.time_mapping = {}
        self.mesh = mesh

    def set_static(self, is_static, position=None, rotation=None, sub_points=None):
        self.is_static = is_static
        if is_static is True:
            if self.viz_type == VIZ_TYPE.FIBER:
                self.static_sub_points = sub_points
            else:
                self.static_position = position
                self.static_rotation = rotation
        else:
            self.static_position = None
            self.static_rotation = None
            self.static_sub_points = None

    def move(self, time_point, position=None, rotation=None, sub_points=None):
        if self.viz_type == VIZ_TYPE.FIBER:
            self.time_mapping[time_point] = {
                "sub_points": sub_points,
                "n_subpoints": len(sub_points),
            }
        else:
            euler = CellpackConverter._get_euler_from_matrix(rotation, HAND_TYPE.RIGHT)
            self.time_mapping[time_point] = {"position": position, "rotation": euler}

    def increment_static(self, time_point):
        if self.is_static:
            if self.viz_type == VIZ_TYPE.FIBER:
                self.time_mapping[time_point] = {
                    "sub_points": self.static_sub_points,
                    "n_subpoints": len(self.static_sub_points),
                }
            else:
                self.time_mapping[time_point] = {
                    "position": self.static_position,
                    "rotation": self.static_rotation,
                }


class simulariumHelper(hostHelper.Helper):
    """
    The Simularium helper abstract class
    ============================
        This is the Simularium helper Object. The helper
        give access to the basic function need for create and edit a host 3d object and scene.
    """

    # this id can probably found in c4d.symbols
    # TAG ID
    DATABASE = "https://raw.githubusercontent.com/mesoscope/cellPACK_data/master/cellPACK_database_1.1.0"
    SPLINE = "kNurbsCurve"
    INSTANCE = "Simularium.Geom"
    EMPTY = "Simularium.Geom"
    SPHERE = "Simularium.Spheres"
    POLYGON = "Simularium.IndexedPolygons"
    # msutil = om.MScriptUtil()
    pb = False
    VERBOSE = 0
    DEBUG = 0
    viewer = None
    host = "simularium"

    def __init__(self, master=None, vi=None):
        hostHelper.Helper.__init__(self)
        # we can define here some function alias
        self.nogui = False
        self.time = -1
        self.scene = {}  # dict of instances in the scene
        self.agent_id_counter = 0
        self.display_data = {}
        self.scale_factor = 1 / 10.0
        self.viewer = "nogui"
        self.nogui = True
        self.hext = "dae"
        self.max_fiber_length = 0

    def clear(self):
        self.scene = {}
        self.time = -1

    def updateAppli(self, *args, **kw):
        return self.update(*args, **kw)

    def Cube(self, *args, **kw):
        return self.box(*args, **kw)

    def Box(self, *args, **kw):
        return self.box(*args, **kw)

    def Polylines(self, *args, **kw):
        return []

    def Spheres(self, *args, **kw):
        return self.sphere(*args, **kw)

    def Cylinders(self, *args, **kw):
        return self.cylinder(*args, **kw)

    def Geom(self, *args, **kw):
        pass

    def Labels(self, *args, **kw):
        pass

    def IndexedPolygons(self, *args, **kw):
        pass

    def setViewer(self, vi):
        self.viewer = vi
        self.AddObject = self.viewer.AddObject
        self.Labels = self.viewer.Labels

    def getCurrentScene(self):
        return self.scene

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

    def update(self):
        self.increment_time()

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

        return o.name

    def increment_static_objects(self):
        for name in self.scene:
            if self.scene[name].is_static:
                self.scene[name].increment_static(self.time)

    def set_object_static(self, name, position, rotation):
        obj = self.getObject(name)
        obj.set_static(True, position, rotation)

    def increment_time(self):
        self.time += 1
        self.increment_static_objects()

    def move_object(self, name, position=None, rotation=None, sub_points=None):
        self.increment_time()
        obj = self.getObject(name)
        obj.move(self.time, position, rotation, sub_points)

    def place_object(self, name, position=None, rotation=None, sub_points=None):
        obj = self.getObject(name)
        obj.move(self.time, position, rotation, sub_points)

    def getObject(self, name):
        return self.scene.get(name)

    def getChilds(self, obj):
        return obj.children

    def deleteObject(self, obj):
        vi = self.getCurrentScene()
        if hasattr(obj, "isinstance"):
            self.deleteInstance(obj)
            return
        try:
            vi.RemoveObject(obj)
        except Exception as e:
            print("problem deleting ", obj, e)

    def newEmpty(
        self, name, location=None, parentCenter=None, display=1, visible=0, **kw
    ):
        # empty = Geom(name, visible=display)
        # if location is not None:
        #     if parentCenter is not None:
        #         location = location - parentCenter
        #     empty.SetTranslation(np.array(location))
        # parent = None
        # if "parent" in kw:
        #     parent = kw["parent"]
        # self.addObjectToScene(None, empty, parent=parent)
        # return empty
        return None

    def updateMasterInstance(self, master, newMesh, **kw):
        # get the instancematrix frommaster
        # apply them to new newMesh
        pass

    def deleteInstance(self, instance):
        # pop the instance from the instanceMatrice
        # delete the object
        m = instance.geom.instanceMatricesFortran[:]
        m = np.delete(m, instance.id, 0)
        m = m.tolist()
        #        m.pop(instance.id)
        matrice = [np.array(mat).reshape((4, 4)) for mat in m]
        instance.geom.Set(instanceMatrices=np.array(matrice))
        del instance

    def add_new_instance_and_update_time(
        self,
        name,
        ingredient,
        instance_id,
        position=None,
        rotation=None,
        sub_points=None,
    ):
        self.agent_id_counter += 1
        if ingredient.Type == "Grow" or ingredient.Type == "Actine":
            viz_type = VIZ_TYPE.FIBER
        else:
            viz_type = VIZ_TYPE.DEFAULT
        new_instance = Instance(
            name,
            instance_id,
            self.agent_id_counter,
            ingredient.encapsulatingRadius,
            viz_type,
        )
        self.scene[instance_id] = new_instance
        self.move_object(instance_id, position, rotation, sub_points)

    def add_instance(
        self,
        name,
        ingredient,
        instance_id,
        radius,
        position=None,
        rotation=None,
        sub_points=None,
        mesh=None,
    ):
        self.agent_id_counter += 1
        if ingredient and self.is_fiber(ingredient.Type):
            viz_type = VIZ_TYPE.FIBER
        else:
            viz_type = VIZ_TYPE.DEFAULT

        new_instance = Instance(
            name,
            instance_id,
            self.agent_id_counter,
            radius,
            viz_type,
            mesh,
        )
        self.scene[instance_id] = new_instance
        if position is None and sub_points is None:
            return
        self.place_object(instance_id, position, rotation, sub_points)

    def setObjectMatrix(self, object, matrice, **kw):
        if "transpose" in kw and not hasattr(object, "isinstance"):
            if kw["transpose"]:
                matrice = np.array(matrice).transpose()
        object.SetTransformation(matrice)

    def concatObjectMatrix(self):
        pass

    def GetAbsPosUntilRoot(self, obj):
        return [0, 0.0, 0.0]

    def add_compartment_to_scene(
        self,
        compartment,
    ):
        display_type = DISPLAY_TYPE.SPHERE
        url = ""
        radius = compartment.encapsulatingRadius
        if compartment.meshType == "file":
            _, extension = os.path.splitext(compartment.path)
            if extension == ".obj":
                display_type = DISPLAY_TYPE.OBJ
                url = (
                    compartment.path
                    if not os.path.isfile(compartment.path)
                    else os.path.basename(compartment.path)
                )
                radius = 1
        self.display_data[compartment.name] = DisplayData(
            name=compartment.name, display_type=display_type, url=url
        )
        self.add_instance(
            compartment.name,
            None,
            compartment.number,
            radius,
            compartment.position,
            np.identity(4),
        )

    def add_object_to_scene(
        self,
        doc,
        ingredient,
        instance_id,
        position=None,
        rotation=None,
        control_points=None,
    ):
        display_type = DISPLAY_TYPE.SPHERE

        if self.is_fiber(ingredient.Type):
            if len(control_points) > self.max_fiber_length:
                self.max_fiber_length = len(control_points)
            display_type = DISPLAY_TYPE.FIBER
        elif ingredient.Type == "SingleCube":
            display_type = DISPLAY_TYPE.CUBE
        self.display_data[ingredient.name] = DisplayData(
            name=ingredient.name, display_type=display_type
        )
        if position is None and control_points is None:
            return
        self.add_new_instance_and_update_time(
            ingredient.name, ingredient, instance_id, position, rotation, control_points
        )

    def update_instance_positions_and_rotations(
        self,
        objects,
    ):
        for position, rotation, ingredient, ptInd in objects:
            instance_id = f"{ingredient.name}-{ptInd}"
            self.place_object(instance_id, position, rotation)

    def get_display_data(self, ingredient):
        ingr_name = ingredient.name
        display_type = DISPLAY_TYPE.SPHERE
        url = ""
        if ingredient.Type == "SingleCube":
            display_type = "CUBE"
        elif ingredient.Type == "SingleSphere":
            display_type = DISPLAY_TYPE.SPHERE
        elif self.is_fiber(ingredient.Type):
            display_type = DISPLAY_TYPE.FIBER
        else:
            pdb_file_name = ""
            display_type = DISPLAY_TYPE.PDB
            if ingredient.source is not None:
                pdb_file_name = ingredient.source["pdb"]
            elif ingredient.pdb is not None and ".map" not in ingredient.pdb:
                pdb_file_name = ingredient.pdb
            elif "meshFile" in ingredient:
                meshType = (
                    ingredient.meshType if ingredient.meshType is not None else "file"
                )
                if meshType == "file":
                    file_path = os.path.basename(ingredient.meshFile)
                    file_name, _ = os.path.splitext(file_path)

                elif meshType == "raw":
                    file_name = ingr_name
                url = f"{simulariumHelper.DATABASE}/geometries/{file_name}.obj"
                display_type = DISPLAY_TYPE.OBJ
            if ".pdb" in pdb_file_name:
                url = f"{simulariumHelper.DATABASE}/other/{pdb_file_name}"
            else:
                url = pdb_file_name
        return display_type, url

    @staticmethod
    def is_fiber(ingr_type):
        return ingr_type in [
            "Grow",
            "Actine",
            "MultiCylinders",
            "SingleCylinder",
        ]

    def init_scene_with_objects(
        self,
        objects,
        grid_point_positions=None,
        grid_point_compartment_ids=None,
        show_sphere_trees=False,
    ):
        self.time = 0
        for position, rotation, ingredient, ptInd in objects:
            ingr_name = ingredient.name
            sub_points = None
            if self.is_fiber(ingredient.Type):
                if ingredient.nbCurve == 0:
                    continue
                # TODO: get sub_points accurately
                if ingredient.nbCurve > self.max_fiber_length:
                    self.max_fiber_length = ingredient.nbCurve
                sub_points = ingredient.listePtLinear

            if ingr_name not in self.display_data:
                display_type, url = self.get_display_data(ingredient)
                self.display_data[ingredient.name] = DisplayData(
                    name=ingr_name, display_type=display_type, url=url
                )
            radius = ingredient.encapsulatingRadius if ingredient is not None else 10

            self.add_instance(
                ingredient.name,
                ingredient,
                f"{ingr_name}-{ptInd}",
                radius,
                position,
                rotation,
                sub_points,
            )
            if show_sphere_trees:
                if len(ingredient.positions) > 0:
                    for level in range(len(ingredient.positions)):
                        for i in range(len(ingredient.positions[level])):
                            pos = ingredient.apply_rotation(
                                rotation, ingredient.positions[level][i], position
                            )

                            self.add_instance(
                                f"{ingredient.name}-spheres",
                                ingredient,
                                f"{ingredient.name}-{ptInd}-{i}",
                                ingredient.radii[level][i],
                                pos,
                                rotation,
                                None,
                            )

        if grid_point_positions is not None:

            for index in range(len(grid_point_compartment_ids)):
                if index % 1 == 0:
                    compartment_id = grid_point_compartment_ids[index]
                    point_pos = grid_point_positions[index]
                    if compartment_id < 0:
                        name = "inside"
                    elif compartment_id > 0:
                        name = "surface"
                    else:
                        name = "outside"
                    self.display_data[name] = DisplayData(
                        name=name, display_type=DISPLAY_TYPE.SPHERE, url=""
                    )

                    self.add_instance(
                        name,
                        None,
                        f"{name}-{index}",
                        0.1,
                        point_pos,
                        np.identity(4),
                        None,
                    )

    def addCameraToScene(self):
        pass

    def addLampToScene(self):
        pass

    def reParent(self, obj, parent):
        if self.nogui:
            return
        vi = self.getCurrentScene()
        if vi == "nogui":
            return
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

    def setInstance(self):
        return None

    def getTranslation(self, name):

        return self.getObject(name).mesh.centroid  # or getCumulatedTranslation

    def setTranslation(self, name, pos=[0.0, 0.0, 0.0]):
        self.getObject(name).SetTranslation(self.FromVec(pos))

    def translateObj(self, obj, position, use_parent=True):
        if len(position) == 1:
            c = position[0]
        else:
            c = position
        newPos = self.FromVec(c)

        if use_parent:
            parentPos = self.GetAbsPosUntilRoot(obj)  # parent.GetAbsPos()
            newPos = newPos - parentPos
        obj.ConcatTranslation(newPos)

    def scaleObj(self, obj, sc):
        if type(sc) is float:
            sc = [sc, sc, sc]
        # obj.scale = sc #SetScale()?
        #        obj.SetScale(np.array(sc))
        obj.Set(scale=np.array(sc))

    def rotateObj(self, obj, rot):
        # take radians, give degrees
        mat = self.eulerToMatrix(rot)
        obj.Set(rotation=np.array(mat).flatten())  # obj.rotation

    def getTransformation(self, geom):
        if self.nogui:
            return np.identity(4)
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
        Simularium support only one object at a time.
        @rtype:   liste
        @return:  the list of selected object
        """
        return [self.getCurrentScene().currentObject]

    # ####################MATERIALS FUNCTION########################

    def addMaterial(self, name, color):
        return color

    def createTexturedMaterial(self, filename):
        pass

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
        pass

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
        instance=None,
        parent=None,
    ):
        # if instance is None:
        #     stick = self.getObject(name)
        #     if stick is None:
        #         v = np.array([tail, head])
        #         f = np.arange(len(v))
        #         f.shape = (-1, 2)
        #         stick = Cylinders(
        #             name, inheritMaterial=False, vertices=v, faces=f, radii=[1]
        #         )
        #         # stick = self.Cylinder(name,length=lenght,pos =head)
        #         self.addObjectToScene(self.getCurrentScene(), stick, parent=parent)
        #     else:
        #         v = np.array([tail, head])
        #         f = np.arange(len(v))
        #         f.shape = (-1, 2)
        #         stick.Set(vertices=v, faces=f, redo=1)
        # else:
        #     stick = instance
        #     v = instance.vertexSet.vertices.array
        #     i = len(v)
        #     #            v = np.concatenate((v,np.array([head,tail])))
        #     instance.vertexSet.vertices.AddValues([head, tail])
        #     instance.faceSet.faces.AddValues([i, i + 1])
        #     r = instance.vertexSet.radii.array[0]
        #     instance.vertexSet.radii.AddValues(r)
        #     instance.Set(redo=1)
        return None

    def cylinder(
        self,
        name,
        radius=1.0,
        length=1.0,
        res=0,
        pos=[0.0, 0.0, 0.0],
        parent=None,
        **kw,
    ):
        #        QualitySph={"0":16,"1":3,"2":4,"3":8,"4":16,"5":32}
        if "axis" in kw:
            if kw["axis"] is not None:
                axis = kw["axis"]
            else:
                axis = [0.0, 1.0, 0.0]

        pos = np.array(pos)

        principal_vector = np.array(length * axis)

        control_points = np.array([pos, pos + principal_vector])

        baseCyl = self.Cylinders(
            name,
            radii=[radius],
            inheritMaterial=False,
            quality=res,
            visible=1,
        )
        self.add_object_to_scene(
            None,
            baseCyl,
            parent=parent,
            control_points=control_points,
        )
        if pos is not None:
            self.setTranslation(baseCyl, pos)
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

    def sphere(
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
        self.add_object_to_scene(None, baseSphere, parent=parent)
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
        return np.array(
            points
        )  # np.array(float(points[0]),float(points[1]),float(points[2]))

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
        from Simularium.Points import Points

        obj = Points(name, **kw)
        self.add_object_to_scene(self.getCurrentScene(), obj, parent=parent)
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

    def instancePolygon(self, name, matrices=None, mesh=None, parent=None, **kw):
        return None

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
        **kw,
    ):
        # import np
        box = {name: name}
        if cornerPoints is not None:
            for i in range(3):
                size[i] = cornerPoints[1][i] - cornerPoints[0][i]
            center = (np.array(cornerPoints[0]) + np.array(cornerPoints[1])) / 2.0
            box.Set(cornerPoints=list(cornerPoints))
        else:
            box.Set(center=center, xside=size[0], yside=size[1], zside=size[2])
        # material is a liste of color per faces.
        # aMat=addMaterial("wire")
        parent = None
        if "parent" in kw:
            parent = kw["parent"]
        self.add_object_to_scene(self.getCurrentScene(), box, parent=parent)
        return box, box

    def updateBox(
        self,
        box,
        center=[0.0, 0.0, 0.0],
        size=[1.0, 1.0, 1.0],
        cornerPoints=None,
    ):
        # import np
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
        **kw,
    ):
        # plane or grid
        return None

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
        if not isinstance(poly, trimesh.Trimesh):
            return [], [], []
        return poly.faces, poly.vertices, poly.vertex_normals

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
            if bg.original == geom:
                m = bg.materialnodebysymbol.values()
                if len(m):
                    k0 = [*bg.materialnodebysymbol][0]
                    mat = bg.materialnodebysymbol[k0].target
        return mat

    def TextureFaceCoordintesToVertexCoordinates(self, v, f, t, ti):
        textureuv_vertex = np.zeros((len(v), 2))
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
        normals_vertex = np.zeros((len(v), 3))
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
        onode = None
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
            # create an empty
            if len(node.children) == 1 and (
                type(node.children[0]) == collada.scene.GeometryNode
            ):
                # no empty just get parent name ?
                gname = node.children[0].geometry.id
                if parentxml is not None:
                    if gname in dicgeoms.keys():
                        if dicgeoms[gname]["parentmesh"] is None:
                            dicgeoms[gname]["parentmesh"] = self.getObject(pname)
                if uniq:
                    onode = self.newEmpty(name)
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
                        if dicgeoms[gname]["parentmesh"] is None:
                            dicgeoms[gname]["parentmesh"] = self.getObject(pname)
            else:
                onode = self.newEmpty(name)
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
        if name is None:
            name = parentxmlnode.get("id")
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
            #                scale = [node.transforms[4].x,node.transforms[4].y,node.transforms[4].z]
            #                onode.Set(translation = trans)#, rotation=rot*0,scale=scale)
            onode.Set(translation=trans)
            onode.Set(rotation=rot)  # .reshape(4,4).transpose())
            onode.Set(scale=scale)
            #                onode.ConcatRotation(rot)
            #                onode.ConcatTranslation(trans)
            #                onode.Set(matrix)
            self.update()
        if hasattr(node, "children") and len(node.children):
            for j, ch in enumerate(node.children):
                self.transformNode(ch, j, col, ch.xmlnode, parent=onode)

    def decomposeColladaGeom(self, g, col):
        name = g.name
        if name == "":
            name = g.id
        v = np.array(g.primitives[0].vertex)  # multiple primitive ?
        nf = len(g.primitives[0].vertex_index)
        sh = g.primitives[0].vertex_index.shape
        if len(sh) == 2 and sh[1] == 3:
            f = g.primitives[0].vertex_index
        else:
            f = g.primitives[0].vertex_index[:nf].reshape(int(nf / 3), 3)
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

    def write(self, listObj, **kw):
        pass

    def writeToFile(self, polygon, file_name, bb):
        """
        Write to simularium file
        """
        total_steps = self.time + 1
        max_number_agents = len(self.scene)
        x_size = bb[1][0] - bb[0][0]
        y_size = bb[1][1] - bb[0][1]
        z_size = bb[1][2] - bb[0][2]
        box_adjustment = (np.array(bb[0]) + np.array(bb[1])) * self.scale_factor / 2
        box_size = [
            x_size * self.scale_factor,
            y_size * self.scale_factor,
            z_size * self.scale_factor,
        ]

        n_agents = [0 for x in range(total_steps)]
        type_names = [
            ["" for x in range(max_number_agents)] for x in range(total_steps)
        ]
        positions = [
            [[0, 0, 0] for x in range(max_number_agents)] for x in range(total_steps)
        ]
        rotations = [
            [[0, 0, 0] for x in range(max_number_agents)] for x in range(total_steps)
        ]
        viz_types = [
            [VIZ_TYPE.DEFAULT for x in range(max_number_agents)]
            for x in range(total_steps)
        ]
        unique_ids = [[0 for x in range(max_number_agents)] for x in range(total_steps)]
        radii = [[1 for x in range(max_number_agents)] for x in range(total_steps)]
        n_subpoints = [
            [0 for x in range(max_number_agents)] for x in range(total_steps)
        ]
        subpoints = [
            [
                [[0, 0, 0] for x in range(self.max_fiber_length)]
                for x in range(max_number_agents)
            ]
            for x in range(total_steps)
        ]
        for t in range(total_steps):
            n = 0
            for name in self.scene:
                obj = self.scene[name]
                if t not in obj.time_mapping:
                    continue

                data_at_time = obj.time_mapping[t]
                n_agents[t] += 1
                type_names[t][n] = obj.name
                unique_ids[t][n] = obj.id
                radii[t][n] = obj.radius * self.scale_factor
                if obj.viz_type == VIZ_TYPE.FIBER:
                    curve = data_at_time["sub_points"]
                    viz_types[t][n] = obj.viz_type
                    positions[t][n] = [0, 0, 0]
                    rotations[t][n] = [0, 0, 0]
                    scaled_control_points = np.array(curve) * self.scale_factor
                    subpoints[t][n] = scaled_control_points.tolist()
                    n_subpoints[t][n] = len(curve)
                else:
                    position = data_at_time["position"]
                    positions[t][n] = [
                        position[0] * self.scale_factor - box_adjustment[0],
                        position[1] * self.scale_factor - box_adjustment[1],
                        position[2] * self.scale_factor - box_adjustment[2],
                    ]
                    rotation = data_at_time["rotation"]
                    rotations[t][n] = rotation
                    viz_types[t][n] = obj.viz_type
                    n_subpoints[t][n] = 0
                n += 1

        camera_z_position = box_size[2] if box_size[2] > 10 else 100.0
        converted_data = TrajectoryData(
            meta_data=MetaData(
                box_size=np.array(box_size),
                camera_defaults=CameraData(
                    position=np.array([10.0, 0.0, camera_z_position]),
                    look_at_position=np.array([0.0, 0.0, 0.0]),
                    fov_degrees=60.0,
                ),
            ),
            agent_data=AgentData(
                display_data=self.display_data,
                times=1 * np.array(list(range(total_steps))),
                n_agents=np.array(n_agents),
                viz_types=np.array(viz_types),
                unique_ids=np.array(unique_ids),
                types=np.array(type_names),
                positions=np.array(positions),
                rotations=np.array(rotations),
                radii=np.array(radii),
                subpoints=np.array(subpoints),
                n_subpoints=np.array(n_subpoints),
            ),
            time_units=UnitData("ns"),  # nanoseconds
            spatial_units=UnitData("nm"),  # nanometers
        )
        TrajectoryConverter(converted_data).write_JSON(file_name)

    def raycast(self, **kw):
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

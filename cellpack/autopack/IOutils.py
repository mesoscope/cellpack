# -*- coding: utf-8 -*-
"""
Created on Sun Jan 27 09:04:10 2013

@author: Ludovic Autin
"""
import json
import os
import pickle

import numpy
from json import encoder
from collections import OrderedDict

import cellpack.autopack as autopack
import cellpack.autopack.transformation as tr
from cellpack.autopack.Recipe import Recipe
from cellpack.autopack.writers import Writer
from .ingredient.Ingredient import Ingredient
from cellpack.autopack.Serializable import (
    sCompartment,
    sIngredientGroup,
    sIngredient,
    sIngredientFiber,
)

from .ingredient.grow import (
    ActinIngredient,
    GrowIngredient,
)

encoder.FLOAT_REPR = lambda o: format(o, ".8g")


def setValueToPythonStr(value, attrname):
    if value is None:
        print(attrname, " is None !")
        return
    if attrname == "color":
        if type(value) != list and type(value) != tuple:
            if autopack.helper is not None:
                value = autopack.helper.getMaterialProperty(value, ["color"])[0]
            else:
                value = [1.0, 0.0, 0.0]
    if type(value) == numpy.ndarray:
        value = value.tolist()
    elif type(value) == list:
        for i, v in enumerate(value):
            if type(v) == numpy.ndarray:
                value[i] = v.tolist()
            elif type(v) == list:
                for j, va in enumerate(v):
                    if type(va) == numpy.ndarray:
                        v[j] = va.tolist()
    if type(value) == str:
        return "%s = '%s'" % (attrname, str(value))
    else:
        return "%s = %s" % (attrname, str(value))


def getStringValueOptions(value, attrname):
    """
    Helper function to return the given environment option as a string to
    be write in the xml file.
    """
    if value is None:
        return "None"
    if attrname == "color":
        if type(value) != list and type(value) != tuple:
            if autopack.helper is not None:
                value = autopack.helper.getMaterialProperty(value, ["color"])[0]
            else:
                value = [1.0, 0.0, 0.0]
    if type(value) == numpy.ndarray:
        value = value.tolist()
    elif type(value) == list:
        for i, v in enumerate(value):
            if type(v) == numpy.ndarray:
                value[i] = v.tolist()
            elif type(v) == list:
                for j, va in enumerate(v):
                    if type(va) == numpy.ndarray:
                        v[j] = va.tolist()
    if type(value) == str:
        value = '"' + value + '"'
    return str(value)


def updatePositionsRadii(ingr):
    toupdate = {"positions": []}
    toupdate["radii"] = []
    nLOD = len(ingr.positions)
    for i in range(nLOD):
        toupdate["positions"].append(
            {"coords": numpy.array(ingr.positions[i]).flatten().tolist()}
        )
        toupdate["radii"].append({"radii": ingr.radii[i]})
    return toupdate


class GrabResult(object):
    """Class for callbacks"""

    def __init__(self, env):
        self.collision = []
        # self.lock = thread.allocate_lock()

    def reset(self):
        self.collision = []

    def grab(self, value):
        """
        the callback function
        """
        # we must use lock here because += is not atomic
        # self.lock.acquire()
        self.collision.append(value)
        # self.lock.release()


class ExportCollada(object):
    def __init__(self, env):
        self.env = env


class IOingredientTool(object):
    # parser that can return an ingredient
    def __init__(self, env=None):
        super(IOingredientTool, self)
        self.env = env
        self.use_quaternion = False

    def read(self, filename):
        fileName, fileExtension = os.path.splitext(filename)
        if fileExtension == ".xml":
            pass  # self.load_XML(setupfile)
        elif fileExtension == ".py":  # execute ?
            pass  # return IOutils.load_Python(env,setupfile)
        elif fileExtension == ".json":
            pass  # return IOutils.load_Json(env,setupfile)

    def makeIngredientFromJson(self, env, inode=None, filename=None, recipe="Generic"):
        overwrite_dic = {}
        ingr_dic = {}
        if filename is None and inode is not None:
            if "include" in inode:
                filename = inode["include"]
            if "overwrite" in inode:
                overwrite_dic = inode["overwrite"]
        if filename is not None:
            filename = autopack.get_local_file_location(
                filename,
                # destination = recipe+os.sep+"recipe"+os.sep+"ingredients"+os.sep,
                cache="recipes",
            )
            with open(filename, "r") as fp:  # doesnt work with symbol link ?
                ingr_dic = json.load(fp)
        elif inode is not None:
            ingr_dic = inode
        else:
            print("filename is None and not ingredient dictionary provided")
            return None
        kw = ingr_dic
        # check for overwritten parameter
        if len(overwrite_dic):
            kw.update(overwrite_dic)
        ingre = self.makeIngredient(env, **kw)
        return ingre

    def ingrJsonNode(self, ingr, result=False, kwds=None, transpose=False):
        # force position instead of sphereFile
        ingdic = OrderedDict()
        if kwds is None:
            kwds = ingr.KWDS
        for k in kwds:
            v = getattr(ingr, str(k))
            #            if hasattr(v,"tolist"):
            #                v=v.tolist()
            #            ingdic[k] = v
            if v is not None:
                ingdic.update(Writer.setValueToJsonNode(v, str(k)))
        # if sphereTree file present should not use the pos-radii keyword
        # if ingr.sphereFile is not None and not result:
        # remove the position and radii key
        #    ingdic.pop("positions", None)
        #    ingdic.pop("radii", None)
        # update the positions and radii to new format
        toupdate = updatePositionsRadii(ingr)
        ingdic.update(toupdate)
        if numpy.sum(ingr.offset) != 0.0:
            if "transform" not in ingr.source:
                ingr.source["transform"] = {"offset": ingr.offset}
            else:
                ingr.source["transform"]["offset"] = ingr.offset

        # reslt ?s
        if result:
            ingdic["results"] = []
            for r in ingr.results:
                # position
                if hasattr(r[0], "tolist"):
                    r[0] = r[0].tolist()
                # rotation
                if hasattr(r[1], "tolist"):
                    r[1] = r[1].tolist()
                R = numpy.array(r[1]).tolist()  # this will not work with cellvIEW?
                if transpose:
                    R = (
                        numpy.array(r[1]).transpose().tolist()
                    )  # this will not work with cellvIEW?
                # transpose ?
                if self.use_quaternion:
                    R = tr.quaternion_from_matrix(R).tolist()
                ingdic["results"].append([r[0], R])
            if isinstance(ingr, GrowIngredient) or isinstance(ingr, ActinIngredient):
                ingdic["nbCurve"] = ingr.nbCurve
                for i in range(ingr.nbCurve):
                    lp = numpy.array(ingr.listePtLinear[i])
                    ingr.listePtLinear[i] = lp.tolist()
                    ingdic["curve" + str(i)] = ingr.listePtLinear[i]
                #            res=numpy.array(ingdic["results"]).transpose()
                #            ingdic["results"]=res.tolist()
        ingdic["name"] = ingr.composition_name
        return ingdic

    def ingrPythonNode(self, ingr, recipe="recipe"):
        inrStr = (
            "#include as follow : execfile('pathto/"
            + ingr.name
            + ".py',globals(),{'recipe':recipe_variable_name})\n"
        )
        if ingr.type == "MultiSphere":
            inrStr += (
                "from autopack.Ingredient import SingleSphereIngr, MultiSphereIngr\n"
            )
            inrStr += ingr.name + "= MultiSphereIngr( \n"
        if ingr.type == "MultiCylinder":
            inrStr += "from autopack.Ingredient import MultiCylindersIngr\n"
            inrStr += ingr.name + "= MultiCylindersIngr( \n"
        for k in ingr.KWDS:
            v = getattr(ingr, k)
            aStr = setValueToPythonStr(v, k)
            if aStr is not None:
                inrStr += aStr + ",\n"
        inrStr += ")\n"
        inrStr += recipe + ".addIngredient(" + ingr.name + ")\n"
        return inrStr

    @staticmethod
    def clean_arguments(arguments_to_include, **arguments):
        new_arguments = {}
        for index, name in enumerate(arguments):
            if name in arguments_to_include:
                new_arguments[name] = arguments[name]
        return new_arguments

    def makeIngredient(self, env, **kw):
        ingr = None
        ingredient_type = kw["type"]
        if (
            ingredient_type == "Grow"
            or ingredient_type == "Actine"
            or ingredient_type == "MultiCylinder"
        ):
            arguments = IOingredientTool.clean_arguments(GrowIngredient.ARGUMENTS, **kw)
        else:
            arguments = IOingredientTool.clean_arguments(Ingredient.ARGUMENTS, **kw)
        ingr = env.create_ingredient(**arguments)
        return ingr

    def set_recipe_ingredient(self, xmlnode, recipe):
        # get the defined ingredient
        ingrnodes = xmlnode.getElementsByTagName("ingredient")
        for ingrnode in ingrnodes:
            ingre = self.makeIngredientFromXml(inode=ingrnode)  # , recipe=self.name)
            if ingre:
                recipe.addIngredient(ingre)
            else:
                print(
                    "PROBLEM creating ingredient from ",
                    ingrnode,
                )
            # check for includes
        ingrnodes_include = xmlnode.getElementsByTagName("include")
        for inclnode in ingrnodes_include:
            xmlfile = str(inclnode.getAttribute("filename"))
            ingre = self.makeIngredientFromXml(filename=xmlfile)  # , recipe=self.name)
            if ingre:
                recipe.addIngredient(ingre)
            else:
                print("PROBLEM creating ingredient from ", ingrnode)
            # look for overwritten attribute


def addCompartments(env, compdic, i, io_ingr):
    # compdic on the form : {u'positions': [[]], u'from': u'HIV-1_0.1.6-7.json', u'rotations': [[]]}

    fname = compdic["from"]
    # retrievet the file
    filename = autopack.get_local_file_location(fname, cache="recipes")
    ninstance = len(compdic["positions"])
    with open(filename, "r") as fp:  # doesnt work with symbol link ?
        if autopack.use_json_hook:
            jsondic = json.load(
                fp, object_pairs_hook=OrderedDict
            )  # ,indent=4, separators=(',', ': ')
        else:
            jsondic = json.load(fp)
    for n in range(ninstance):
        pos = numpy.array(compdic["positions"][n])  # Vec3
        rot = numpy.array(compdic["rotations"][n])  # quaternion
        # we only extract the compartments ferom the file
        # order issue
        for cname in jsondic["compartments"]:
            comp_dic = jsondic["compartments"][cname]
            name = str(comp_dic["name"]) + "_" + str(i) + "_" + str(n)
            geom = str(comp_dic["geom"])
            rep = ""
            if "rep" in comp_dic:
                rep = str(comp_dic["rep"])
            rep_file = ""
            if "rep_file" in comp_dic:
                rep_file = str(comp_dic["rep_file"])
            if rep != "None" and len(rep) != 0 and rep != "" and rep != "":
                rname = rep_file.split("/")[-1]
                fileName, fileExtension = os.path.splitext(rname)
                if fileExtension == "":
                    fileExtension = autopack.helper.hext
                    if fileExtension == "":
                        rep_file = rep_file + fileExtension
                    else:
                        rep_file = rep_file + "." + fileExtension
            else:
                rep = None
                rep_file = None
            print("add compartment ", name, geom, rep, rep_file)
            compartment = env.create_compartment(
                name, geom, str(comp_dic["name"]), rep, rep_file
            )
            # need to transform the v,f,n to the new rotation and position
            # NOTE: we could initialize compartments with pos and rot instead
            # of transforming it every time we make a new one
            compartment.transformMesh(pos, rot)
            env.addCompartment(compartment)
            if "surface" in comp_dic:
                snode = comp_dic["surface"]
                ingrs_dic = snode["ingredients"]
                if len(ingrs_dic):
                    rSurf = Recipe(name="surf_" + str(len(env.compartments) - 1))
                    #                        rSurf = Recipe(name=o.name+"_surf")
                    for ing_name in ingrs_dic:
                        # either xref or defined
                        ing_dic = ingrs_dic[ing_name]
                        ingr = io_ingr.makeIngredientFromJson(
                            env=env, inode=ing_dic, recipe=env.name
                        )
                        rSurf.addIngredient(ingr)
                        # setup recipe
                    compartment.setSurfaceRecipe(rSurf)
            if "interior" in comp_dic:
                snode = comp_dic["interior"]
                ingrs_dic = snode["ingredients"]
                if len(ingrs_dic):
                    #                        rMatrix = Recipe(name=o.name+"_int")
                    rMatrix = Recipe(name="int_" + str(len(env.compartments) - 1))
                    for ing_name in ingrs_dic:
                        # either xref or defined
                        ing_dic = ingrs_dic[ing_name]
                        ingr = io_ingr.makeIngredientFromJson(
                            env=env, inode=ing_dic, recipe=env.name
                        )
                        rMatrix.addIngredient(ingr)
                        # setup recipe
                    compartment.setInnerRecipe(rMatrix)


def save_asPython(env, setupfile, useXref=True):
    """
    Save the current environment setup as a python script file.
    """
    io_ingr = IOingredientTool(env=env)
    env.setupfile = setupfile
    pathout = os.path.dirname(os.path.abspath(env.setupfile))
    # add the import statement
    setupStr = """
import sys
import os
#autopack
import autopack
localdir = wrkDir = autopack.__path__[0]
from autopack.Ingredient import SingleSphereIngr, MultiSphereIngr
from autopack.Ingredient import MultiCylindersIngr,GrowIngredient,ActinIngredient
from autopack.Compartment import Compartment
from autopack.Recipe import Recipe
from autopack.Environment import Environment
from autopack.Graphics import AutopackViewer as AFViewer
#access the helper
helper = autopack.helper
if helper is None :
import upy
helperClass = upy.getHelperClass()
helper =helperClass()
#create the viewer
ViewerType=autopack.helper.host
afviewer = AFViewer(ViewerType=helper.host,helper=helper)#long ?
#make some option here
afviewer.doPoints = False
afviewer.doSpheres = False
afviewer.quality = 1 #lowest quality for sphere and cylinder
afviewer.visibleMesh = True #mesh default visibility
#create the env
h1 = Environment()
"""
    setupStr += "h1.name='" + env.name + "'\n"
    for k in env.OPTIONS:
        v = getattr(env, k)
        if k == "gradients":
            v = list(env.gradients.keys())
        vstr = getStringValueOptions(v, k)  # env.setValueToXMLNode(v,options,k)
        setupStr += "h1.%s=%s\n" % (k, vstr)
    # add the boundin box
    vstr = getStringValueOptions(
        env.boundingBox, "boundingBox"
    )  # env.setValueToXMLNode(v,options,k)
    setupStr += "h1.%s=%s\n" % ("boundingBox", vstr)
    vstr = getStringValueOptions(env.version, k)  # env.setValueToXMLNode(v,options,k)
    setupStr += "h1.%s=%s\n" % ("version", vstr)

    # TODO : GRADIENT
    #        if len(env.gradients):
    #            gradientsnode=env.xmldoc.createElement("gradients")
    #            root.appendChild(gradientsnode)
    #            for gname in env.gradients:
    #                g = env.gradients[gname]
    #                grnode = env.xmldoc.createElement("gradient")
    #                gradientsnode.appendChild(grnode)
    #                grnode.setAttribute("name",str(g.name))
    #                for k in g.OPTIONS:
    #                    v = getattr(g,k)
    #                    env.setValueToXMLNode(v,grnode,k)
    #
    #        grid path information
    #        if env.grid.filename is not None or env.grid.result_filename is not None:
    #            gridnode=env.xmldoc.createElement("grid")
    #            root.appendChild(gridnode)
    #            gridnode.setAttribute("grid_storage",str(env.grid.filename))
    #            gridnode.setAttribute("grid_result",str(env.grid.result_filename))
    #
    r = env.exteriorRecipe
    if r:
        setupStr += "cytoplasme = Recipe()\n"
        for ingr in r.ingredients:
            if useXref:
                io_ingr.write(ingr, pathout + os.sep + ingr.name, ingr_format="python")
                setupStr += (
                    "execfile('"
                    + pathout
                    + os.sep
                    + ingr.name
                    + ".py',globals(),{'recipe':cytoplasme})\n"
                )
            else:
                ingrnode = io_ingr.ingrPythonNode(ingr, recipe="cytoplasme")
                setupStr += ingrnode
        setupStr += "h1.setExteriorRecipe(cytoplasme)\n"
    for o in env.compartments:
        setupStr += o.name + " = Compartment('" + o.name + "',None, None, None,\n"
        setupStr += "         filename='" + o.filename + "',\n"
        if o.representation is not None:
            setupStr += "         object_name ='" + o.representation + "',\n"
            setupStr += "         object_filename ='" + o.representation_file + "'\n"
        setupStr += "         )\n"
        setupStr += "h1.addCompartment(" + o.name + ")\n"
        rs = o.surfaceRecipe
        if rs:
            setupStr += o.name + "_surface = Recipe(name='" + o.name + "_surf')\n"
            for ingr in rs.ingredients:
                if useXref:
                    io_ingr.write(
                        ingr, pathout + os.sep + ingr.name, ingr_format="python"
                    )
                    setupStr += (
                        "execfile('"
                        + pathout
                        + os.sep
                        + ingr.name
                        + ".py',globals(),{'recipe':"
                        + o.name
                        + "_surface})\n"
                    )
                else:
                    ingrnode = io_ingr.ingrPythonNode(ingr, recipe=o.name + "_surface")
                    setupStr += ingrnode
            setupStr += o.name + ".setSurfaceRecipe(" + o.name + "_surface)\n"
        ri = o.innerRecipe
        if ri:
            setupStr += o.name + "_inner = Recipe(name='" + o.name + "_int')\n"
            for ingr in rs.ingredients:
                if useXref:
                    io_ingr.write(
                        ingr, pathout + os.sep + ingr.name, ingr_format="python"
                    )
                    setupStr += (
                        "execfile('"
                        + pathout
                        + os.sep
                        + ingr.name
                        + ".py',globals(),{'recipe':"
                        + o.name
                        + "_inner})\n"
                    )
                else:
                    ingrnode = io_ingr.ingrPythonNode(ingr, recipe=o.name + "_inner")
                    setupStr += ingrnode
            setupStr += o.name + ".setInnerRecipe(" + o.name + "_inner)\n"
    setupStr += "afviewer.SetHistoVol(h1,0,display=False)\n"
    setupStr += "afviewer.displayPreFill()\n"
    setupStr += "bbox = afviewer.helper.getObject('histvolBB')\n"
    setupStr += "if bbox is None : bbox = afviewer.helper.box('histvolBB',cornerPoints=h1.boundingBox)\n"
    setupStr += "helper = afviewer.helper\n"
    setupStr += "noGUI = False\n"
    setupStr += "try :\n"
    setupStr += "    print ('try')\n"
    setupStr += (
        "    AFGui.Set('"
        + env.name
        + "',helper=afviewer.helper,afviewer=afviewer,histoVol=h1,bbox=bbox)\n"
    )
    setupStr += "except:\n"
    setupStr += "    print ('no GUI')\n"
    setupStr += "    noGUI = True\n"
    f = open(setupfile, "w")
    f.write(setupStr)
    f.close()


def checkRotFormat(rotation, transpose):
    if numpy.array(rotation).shape == (4,):
        if transpose:
            return tr.matrix_from_quaternion(rotation).transpose()  # transpose ?
        else:
            return tr.matrix_from_quaternion(rotation)
    else:
        return rotation


def gatherResult(ingr_result, transpose, use_quaternion, type=0.0, lefthand=False):
    all_pos = []
    all_rot = []
    for r in ingr_result:
        # position
        if hasattr(r[0], "tolist"):
            r[0] = r[0].tolist()
        # rotation
        if hasattr(r[1], "tolist"):
            r[1] = r[1].tolist()
        R = numpy.array(r[1]).tolist()  # this will not work with cellvIEW?
        R = checkRotFormat(R, transpose)
        if transpose:
            R = numpy.array(R).transpose().tolist()  # this will not work with cellvIEW?
        # transpose ?
        if lefthand:
            all_pos.append([-r[0][0], r[0][1], r[0][2], type])  # ing type?
            R = tr.quaternion_from_matrix(R).tolist()
            all_rot.append([R[1], -R[2], -R[3], R[0]])
        else:
            all_pos.append([r[0][0], r[0][1], r[0][2], type])
            if use_quaternion:
                R = tr.quaternion_from_matrix(R).tolist()
            all_rot.append(R)
        # print ingr.composition_name, type, all_pos[-1], all_rot[-1]
    return all_pos, all_rot


def serializedRecipe(env, transpose, use_quaternion, result=False, lefthand=False):
    # specify the  keyword ?
    sCompartment.static_id = 0
    sIngredientFiber.static_id = 0
    sIngredient.static_id = [0, 0, 0]
    sIngredientGroup.static_id = 0
    all_pos = []
    all_rot = []
    root = sCompartment("root")
    r = env.exteriorRecipe
    if r:
        exterior = sCompartment("cytoplasme")
        proteins = None  # sIngredientGroup("proteins", 0)
        fibers = None  # sIngredientGroup("fibers", 1)
        for ingr in r.ingredients:
            nbmol = len(ingr.results)
            if len(ingr.results) == 0:
                nbmol = ingr.count
            toupdate = updatePositionsRadii(ingr)
            kwds = {
                "count": nbmol,
                "principal_vector": ingr.principal_vector,
                "molarity": ingr.molarity,
                "source": ingr.source,
                "positions": toupdate["positions"],
                "radii_lod": toupdate["radii"],
            }
            if ingr.type == "Grow":
                if fibers is None:
                    fibers = sIngredientGroup("fibers", 1)
                igr = sIngredient(ingr.composition_name, 1, **kwds)
                fibers.addIngredient(igr)
            else:
                if proteins is None:
                    proteins = sIngredientGroup("proteins", 0)
                igr = sIngredient(ingr.composition_name, 0, **kwds)
                proteins.addIngredient(igr)
            if result:
                ap, ar = gatherResult(
                    ingr.results,
                    transpose,
                    use_quaternion,
                    type=igr.ingredient_id,
                    lefthand=lefthand,
                )
                all_pos.extend(ap)
                all_rot.extend(ar)
        root.addCompartment(exterior)
        if proteins is not None:
            exterior.addIngredientGroup(proteins)
        if fibers is not None:
            exterior.addIngredientGroup(fibers)
    for o in env.compartments:
        co = sCompartment(o.name)
        rs = o.surfaceRecipe
        if rs:
            surface = sCompartment("surface")
            proteins = None  # sIngredientGroup("proteins", 0)
            fibers = None  # sIngredientGroup("fibers", 1)
            for ingr in rs.ingredients:
                nbmol = len(ingr.results)
                if len(ingr.results) == 0:
                    nbmol = ingr.count
                toupdate = updatePositionsRadii(ingr)
                kwds = {
                    "count": nbmol,
                    "principal_vector": ingr.principal_vector,
                    "molarity": ingr.molarity,
                    "source": ingr.source,
                    "positions": toupdate["positions"],
                    "radii_lod": toupdate["radii"],
                }
                if ingr.type == "Grow":
                    if fibers is None:
                        fibers = sIngredientGroup("fibers", 1)
                    igr = sIngredient(ingr.composition_name, 1, **kwds)
                    fibers.addIngredient(igr)
                else:
                    if proteins is None:
                        proteins = sIngredientGroup("proteins", 0)
                    igr = sIngredient(ingr.composition_name, 0, **kwds)
                    proteins.addIngredient(igr)
                if result:
                    ap, ar = gatherResult(
                        ingr.results,
                        transpose,
                        use_quaternion,
                        type=igr.ingredient_id,
                        lefthand=lefthand,
                    )
                    all_pos.extend(ap)
                    all_rot.extend(ar)
            co.addCompartment(surface)
            if proteins is not None:
                surface.addIngredientGroup(proteins)
            if fibers is not None:
                surface.addIngredientGroup(fibers)
        ri = o.innerRecipe
        if ri:
            interior = sCompartment("interior")
            proteins = None  # sIngredientGroup("proteins", 0)
            fibers = None  # sIngredientGroup("fibers", 1)
            for ingr in ri.ingredients:
                nbmol = len(ingr.results)
                if len(ingr.results) == 0:
                    nbmol = ingr.count
                toupdate = updatePositionsRadii(ingr)
                kwds = {
                    "count": nbmol,
                    "principal_vector": ingr.principal_vector,
                    "molarity": ingr.molarity,
                    "source": ingr.source,
                    "positions": toupdate["positions"],
                    "radii_lod": toupdate["radii"],
                }
                if ingr.type == "Grow":
                    if fibers is None:
                        fibers = sIngredientGroup("fibers", 1)
                    igr = sIngredient(ingr.composition_name, 1, **kwds)
                    fibers.addIngredient(igr)
                else:
                    if proteins is None:
                        proteins = sIngredientGroup("proteins", 0)
                    igr = sIngredient(ingr.composition_name, 0, **kwds)
                    proteins.addIngredient(igr)
                if result:
                    ap, ar = gatherResult(
                        ingr.results,
                        transpose,
                        use_quaternion,
                        type=igr.ingredient_id,
                        lefthand=lefthand,
                    )
                    all_pos.extend(ap)
                    all_rot.extend(ar)
            co.addCompartment(interior)
            if proteins is not None:
                interior.addIngredientGroup(proteins)
            if fibers is not None:
                interior.addIngredientGroup(fibers)
        root.addCompartment(co)
    data_json = root.to_JSON()
    return data_json, all_pos, all_rot


def serializedFromResult(env, transpose, use_quaternion, result=False, lefthand=False):
    all_pos = []
    all_rot = []
    root = sCompartment("root")
    r = None
    if "cytoplasme" in env:
        r = env["cytoplasme"]
    if r:
        exterior = sCompartment("cytoplasme")
        proteins = None  # sIngredientGroup("proteins", 0)
        # fibers = None  # sIngredientGroup("fibers", 1)
        for ingr_name in r["ingredients"]:
            ingr = r["ingredients"][ingr_name]
            kwds = {"count": len(ingr["results"]), "source": ingr["source"]}
            #            if ingr.type == "Grow":
            #                if fibers is None:
            #                    fibers = sIngredientGroup("fibers", 1)
            #                igr = sIngredient(ingr.composition_name, 1, **kwds)
            #                fibers.addIngredient(igr)
            #            else:
            if proteins is None:
                proteins = sIngredientGroup("proteins", 0)
            igr = sIngredient(ingr["name"], 0, **kwds)
            proteins.addIngredient(igr)
            if result:
                ap, ar = gatherResult(
                    ingr["results"],
                    transpose,
                    use_quaternion,
                    type=igr.ingredient_id,
                    lefthand=lefthand,
                )
                all_pos.extend(ap)
                all_rot.extend(ar)
        root.addCompartment(exterior)
        if proteins is not None:
            exterior.addIngredientGroup(proteins)
    #        if fibers is not None:
    #            exterior.addIngredientGroup(fibers)
    if "compartments" in env:
        for composition_name in env["compartments"]:
            o = env["compartments"][composition_name]
            co = sCompartment(composition_name)
            rs = None
            if "surface" in o:
                rs = o["surface"]
            if rs:
                surface = sCompartment("surface")
                proteins = None  # sIngredientGroup("proteins", 0)
                for ingr_name in rs["ingredients"]:
                    ingr = rs["ingredients"][ingr_name]
                    kwds = {"count": len(ingr["results"]), "source": ingr["source"]}
                    #                if ingr.type == "Grow":
                    #                    if fibers is None:
                    #                        fibers = sIngredientGroup("fibers", 1)
                    #                    igr = sIngredient(ingr.composition_name, 1, **kwds)
                    #                    fibers.addIngredient(igr)
                    #                else:
                    if proteins is None:
                        proteins = sIngredientGroup("proteins", 0)
                    igr = sIngredient(ingr["name"], 0, **kwds)
                    proteins.addIngredient(igr)
                    if result:
                        ap, ar = gatherResult(
                            ingr["results"],
                            transpose,
                            use_quaternion,
                            type=igr.ingredient_id,
                            lefthand=lefthand,
                        )
                        all_pos.extend(ap)
                        all_rot.extend(ar)
                co.addCompartment(surface)
                if proteins is not None:
                    surface.addIngredientGroup(proteins)
            #            if fibers is not None:
            #                surface.addIngredientGroup(fibers)
            ri = None
            if "interior" in o:
                ri = o["interior"]
            if ri:
                interior = sCompartment("interior")
                proteins = None  # sIngredientGroup("proteins", 0)
                for ingr_name in ri["ingredients"]:
                    ingr = ri["ingredients"][ingr_name]
                    kwds = {"count": len(ingr["results"]), "source": ingr["source"]}
                    #                if ingr.type == "Grow":
                    #                    if fibers is None:
                    #                        fibers = sIngredientGroup("fibers", 1)
                    #                    igr = sIngredient(ingr["name"], 1, **kwds)
                    #                    fibers.addIngredient(igr)
                    #                else:
                    if proteins is None:
                        proteins = sIngredientGroup("proteins", 0)
                    igr = sIngredient(ingr["name"], 0, **kwds)
                    proteins.addIngredient(igr)
                    if result:
                        ap, ar = gatherResult(
                            ingr["results"],
                            transpose,
                            use_quaternion,
                            type=igr.ingredient_id,
                            lefthand=lefthand,
                        )
                        all_pos.extend(ap)
                        all_rot.extend(ar)
                co.addCompartment(interior)
                if proteins is not None:
                    interior.addIngredientGroup(proteins)
            #            if fibers is not None:
            #                interior.addIngredientGroup(fibers)
            root.addCompartment(co)
    data_json = root.to_JSON()
    return data_json, all_pos, all_rot


def serializedRecipe_group_dic(env, transpose, use_quaternion, lefthand=False):
    # all_pos = []
    # all_rot = []
    root = sCompartment("root")
    r = env["cytoplasme"]
    if r:
        group = sIngredientGroup("cytoplasme")
        for ingr_name in r["ingredients"]:
            ingr = r["ingredients"][ingr_name]
            kwds = {"count": len(ingr["results"]), "source": ingr["source"]}
            # if ingr.type == "Grow":
            #    igr = sIngredientFiber(ingr.composition_name, **kwds)
            #    group.addIngredientFiber(igr)
            # else:
            igr = sIngredient(ingr["name"], **kwds)
            group.addIngredient(igr)
            # ap, ar = gatherResult(ingr["results"], transpose, use_quaternion, type=igr.ingredient_id, lefthand=lefthand)
            # all_pos.extend(ap)
            # all_rot.extend(ar)
        root.addIngredientGroup(group)
    for o in env["compartments"]:
        co = sCompartment(o.name)
        rs = env["compartments"][o]["surface"]
        if rs:
            group = sIngredientGroup("surface")
            for ingr_name in rs["ingredients"]:
                ingr = rs["ingredients"][ingr_name]
                kwds = {"count": len(ingr["results"]), "source": ingr["source"]}
                igr = sIngredient(ingr["name"], **kwds)
                group.addIngredient(igr)

            co.addIngredientGroup(group)
        ri = env["compartments"][o]["interior"]
        if ri:
            group = sIngredientGroup("interior")
            for ingr_name in ri["ingredients"]:
                ingr = ri["ingredients"][ingr_name]
                kwds = {"count": len(ingr["results"]), "source": ingr["source"]}
                #                if ingr.type == "Grow":
                #                    igr = sIngredientFiber(ingr.composition_name, **kwds)
                #                    group.addIngredientFiber(igr)
                #                else:
                igr = sIngredient(ingr["name"], **kwds)
                group.addIngredient(igr)

            co.addIngredientGroup(group)
        root.addCompartment(co)
    data_json = root.to_JSON()
    return data_json  # , all_pos, all_rot


def serializedRecipe_group(env, transpose, use_quaternion, lefthand=False):
    all_pos = []
    all_rot = []
    root = sCompartment("root")
    r = env.exteriorRecipe
    if r:
        group = sIngredientGroup("cytoplasme")
        for ingr in r.ingredients:
            kwds = {"count": len(ingr.results), "source": ingr.source}
            if ingr.type == "Grow":
                igr = sIngredientFiber(ingr.composition_name, **kwds)
                group.addIngredientFiber(igr)
            else:
                igr = sIngredient(ingr.composition_name, **kwds)
                group.addIngredient(igr)
            ap, ar = gatherResult(
                ingr.results,
                transpose,
                use_quaternion,
                type=igr.ingredient_id,
                lefthand=lefthand,
            )
            all_pos.extend(ap)
            all_rot.extend(ar)
        root.addIngredientGroup(group)
    for o in env.compartments:
        co = sCompartment(o.name)
        rs = o.surfaceRecipe
        if rs:
            group = sIngredientGroup("surface")
            for ingr in rs.ingredients:
                kwds = {"count": len(ingr.results), "source": ingr.source}
                if ingr.type == "Grow":
                    igr = sIngredientFiber(ingr.composition_name, **kwds)
                    group.addIngredientFiber(igr)
                else:
                    igr = sIngredient(ingr.composition_name, **kwds)
                    group.addIngredient(igr)
                ap, ar = gatherResult(
                    ingr.results,
                    transpose,
                    use_quaternion,
                    type=igr.ingredient_id,
                    lefthand=lefthand,
                )
                all_pos.extend(ap)
                all_rot.extend(ar)
            co.addIngredientGroup(group)
        ri = o.innerRecipe
        if ri:
            group = sIngredientGroup("interior")
            for ingr in ri.ingredients:
                kwds = {"count": len(ingr.results), "source": ingr.source}
                if ingr.type == "Grow":
                    igr = sIngredientFiber(ingr.composition_name, **kwds)
                    group.addIngredientFiber(igr)
                else:
                    igr = sIngredient(ingr.composition_name, **kwds)
                    group.addIngredient(igr)
                ap, ar = gatherResult(
                    ingr.results,
                    transpose,
                    use_quaternion,
                    type=igr.ingredient_id,
                    lefthand=lefthand,
                )
                all_pos.extend(ap)
                all_rot.extend(ar)
            co.addIngredientGroup(group)
        root.addCompartment(co)
    data_json = root.to_JSON()
    return data_json, all_pos, all_rot


# use as
# from autopack.IOutils import saveResultBinary
# saveResultBinary(env,"C:\\Users\\ludov\\OneDrive\\Documents\\myRecipes\\test_tr",True,True,False)
# saveResultBinary(env,"C:\\Users\\ludov\\OneDrive\\Documents\\myRecipes\\test_tr_lh",True,True,True)
# saveResultBinary(env,"C:\\Users\\ludov\\OneDrive\\Documents\\myRecipes\\test",False,True,False)
# saveResultBinary(env,"C:\\Users\\ludov\\OneDrive\\Documents\\myRecipes\\test_lh",False,True,True)
def saveResultBinaryDic(env, filename, transpose, use_quaternion, lefthand=False):
    # should follow the order of the serialized class order?
    all_pos = []
    all_rot = []
    fptr = open(filename, "wb")
    r = env["cytoplasme"]
    if r:
        for ingr_name in r["ingredients"]:
            ingr = r["ingredients"][ingr_name]
            ap, ar = gatherResult(
                ingr["results"], transpose, use_quaternion, lefthand=lefthand
            )
            all_pos.extend(ap)
            all_rot.extend(ar)
    for o in env["compartments"]:
        rs = env["compartments"][o]["surface"]
        if rs:
            for ingr_name in rs["ingredients"]:
                ingr = rs["ingredients"][ingr_name]
                ap, ar = gatherResult(
                    ingr["results"], transpose, use_quaternion, lefthand=lefthand
                )
                all_pos.extend(ap)
                all_rot.extend(ar)
        ri = env["compartments"][o]["interior"]
        if ri:
            for ingr_name in ri["ingredients"]:
                ingr = ri["ingredients"][ingr_name]
                ap, ar = gatherResult(
                    ingr["results"], transpose, use_quaternion, lefthand=lefthand
                )
                all_pos.extend(ap)
                all_rot.extend(ar)
    # write allpos
    fptr.write(numpy.array(all_pos, "f").flatten().tobytes())
    fptr.write(numpy.array(all_rot, "f").flatten().tobytes())
    fptr.close()
    return all_pos, all_rot


def toBinary(all_pos, all_rot, filename):
    fptr = open(filename, "wb")
    fptr.write(numpy.array(all_pos, "f").flatten().tobytes())
    fptr.write(numpy.array(all_rot, "f").flatten().tobytes())
    fptr.close()


def saveResultBinary(env, filename, transpose, use_quaternion, lefthand=False):
    # should follow the order of the serialized class order?
    all_pos = []
    all_rot = []
    fptr = open(filename, "wb")
    uid = 0
    r = env.exteriorRecipe
    if r:
        for ingr in r.ingredients:
            ap, ar = gatherResult(
                ingr.results, transpose, use_quaternion, lefthand=lefthand, type=uid
            )
            all_pos.extend(ap)
            all_rot.extend(ar)
            uid += 1
    for o in env.compartments:
        rs = o.surfaceRecipe
        if rs:
            for ingr in rs.ingredients:
                ap, ar = gatherResult(
                    ingr.results, transpose, use_quaternion, lefthand=lefthand, type=uid
                )
                all_pos.extend(ap)
                all_rot.extend(ar)
                uid += 1
        ri = o.innerRecipe
        if ri:
            for ingr in ri.ingredients:
                ap, ar = gatherResult(
                    ingr.results, transpose, use_quaternion, lefthand=lefthand, type=uid
                )
                all_pos.extend(ap)
                all_rot.extend(ar)
                uid += 1
    # write allpos
    fptr.write(numpy.array(all_pos, "f").flatten().tobytes())  # ?
    fptr.write(numpy.array(all_rot, "f").flatten().tobytes())
    #    numpy.array(all_pos, 'f').flatten().tofile(fptr)  # 4float position
    #    numpy.array(all_rot, 'f').flatten().tofile(fptr)  # 4flaot quaternion
    fptr.close()


def getAllPosRot(env, transpose, use_quaternion, lefthand=False):
    # should follow the order of the serialized class order?
    all_pos = []
    all_rot = []
    r = env.exteriorRecipe
    if r:
        for ingr in r.ingredients:
            ap, ar = gatherResult(
                ingr.results, transpose, use_quaternion, lefthand=lefthand
            )
            all_pos.extend(ap)
            all_rot.extend(ar)
    for o in env.compartments:
        rs = o.surfaceRecipe
        if rs:
            for ingr in rs.ingredients:
                ap, ar = gatherResult(
                    ingr.results, transpose, use_quaternion, lefthand=lefthand
                )
                all_pos.extend(ap)
                all_rot.extend(ar)
        ri = o.innerRecipe
        if ri:
            for ingr in ri.ingredients:
                ap, ar = gatherResult(
                    ingr.results, transpose, use_quaternion, lefthand=lefthand
                )
                all_pos.extend(ap)
                all_rot.extend(ar)
    # write allpos
    return all_pos, all_rot


def load_JsonString(env, astring):
    """
    Setup the environment according the given json file.
    """
    env.jsondic = json.loads(astring, object_pairs_hook=OrderedDict)
    setupFromJsonDic(
        env,
    )


def load_Json(env, setupfile):
    """
    Setup the environment according the given json file.
    """

    if setupfile is None:
        setupfile = env.setupfile
    if env.jsondic is None:
        with open(setupfile, "r") as fp:  # doesnt work with symbol link ?
            if autopack.use_json_hook:
                env.jsondic = json.load(
                    fp, object_pairs_hook=OrderedDict
                )  # ,indent=4, separators=(',', ': ')
            else:
                env.jsondic = json.load(fp)
    setupFromJsonDic(
        env,
    )


def setupFromJsonDic(
    env,
):
    env.current_path = os.path.dirname(os.path.abspath(env.setupfile))
    io_ingr = IOingredientTool(env=env)
    env.name = env.jsondic["recipe"]["name"]
    env.version = env.jsondic["recipe"]["version"]
    # is there any cutoms paths
    if "paths" in env.jsondic["recipe"]:
        env.custom_paths = env.jsondic["recipe"][
            "paths"
        ]  # list(env.jsondic["recipe"]["paths"].items())
        #        autopack.replace_path.extend(env.custom_paths)#keyWordPAth,valuePath
        autopack.updateReplacePath(env.custom_paths)
    autopack.CURRENT_RECIPE_PATH = env.current_path

    if "gradients" in env.jsondic:
        env.gradients = {}
        gradientsnode = env.jsondic["gradients"]
        if len(gradientsnode):  # number of gradients defined
            for g_name in gradientsnode:
                g_dic = gradientsnode[g_name]
                env.setGradient(
                    name=g_name,
                    mode=g_dic["mode"],
                    direction=g_dic["direction"],
                    weight_mode=g_dic["weight_mode"],
                    description=g_dic["description"],
                    pick_mode=g_dic["pick_mode"],
                    radius=g_dic["radius"],
                )

    if "grid" in env.jsondic:
        gridnode = env.jsondic["grid"]
        if len(gridnode):
            env.grid_filename = str(gridnode["grid_storage"])
            env.grid_result_filename = str(gridnode["grid_result"])

    sortkey = str.lower

    if "cytoplasme" in env.jsondic:
        ingrs_dic = env.jsondic["cytoplasme"]["ingredients"]
        if len(ingrs_dic):
            rCyto = Recipe()
            for ing_name in sorted(ingrs_dic, key=sortkey):  # ingrs_dic:
                # either xref or defined
                ing_dic = ingrs_dic[ing_name]
                ingr = io_ingr.makeIngredientFromJson(
                    env, inode=ing_dic, recipe=env.name
                )
                rCyto.addIngredient(ingr)
                # setup recipe
            env.setExteriorRecipe(rCyto)

    if "compartments" in env.jsondic:
        # use some include ?
        if len(env.jsondic["compartments"]):
            # if "include" in env.jsondic["compartments"]:
            # include all compartments from given filename.
            # transform the geometry of the compartment packing rep
            for cname in env.jsondic["compartments"]:
                if cname == "include":
                    for i, ncompart in enumerate(
                        env.jsondic["compartments"]["include"]
                    ):
                        addCompartments(env, ncompart, i, io_ingr)
                    continue
                comp_dic = env.jsondic["compartments"][cname]
                name = str(comp_dic["name"])
                geom = comp_dic["geom"]
                gname = name
                mtype = "file"
                if "meshType" in comp_dic:
                    mtype = comp_dic["meshType"]
                elif "geom_type" in comp_dic:
                    mtype = comp_dic["geom_type"]
                if "gname" in comp_dic:
                    gname = str(comp_dic["gname"])
                rep = ""
                if "rep" in comp_dic:
                    rep = str(comp_dic["rep"])
                rep_file = ""
                if "rep_file" in comp_dic:
                    rep_file = str(comp_dic["rep_file"])
                if rep != "None" and len(rep) != 0 and rep != "" and rep != "":
                    rname = rep_file.split("/")[-1]
                    fileName, fileExtension = os.path.splitext(rname)
                    if fileExtension == "":
                        fileExtension = autopack.helper.hext
                        if fileExtension == "":
                            rep_file = rep_file + fileExtension
                        else:
                            rep_file = rep_file + "." + fileExtension
                else:
                    rep = None
                    rep_file = None
                compartment = env.create_compartment(
                    name, geom, gname, rep, rep_file, mtype
                )
                env.addCompartment(compartment)
                if "surface" in comp_dic:
                    snode = comp_dic["surface"]
                    ingrs_dic = snode["ingredients"]
                    if len(ingrs_dic):
                        rSurf = Recipe(name="surf_" + str(len(env.compartments) - 1))
                        for ing_name in sorted(ingrs_dic, key=sortkey):  # ingrs_dic:
                            # either xref or defined
                            ing_dic = ingrs_dic[ing_name]
                            ingr = io_ingr.makeIngredientFromJson(
                                env=env, inode=ing_dic, recipe=env.name
                            )
                            rSurf.addIngredient(ingr)
                            # setup recipe
                        compartment.setSurfaceRecipe(rSurf)
                if "interior" in comp_dic:
                    snode = comp_dic["interior"]
                    ingrs_dic = snode["ingredients"]
                    if len(ingrs_dic):
                        #                        rMatrix = Recipe(name=o.name+"_int")
                        rMatrix = Recipe(name="int_" + str(len(env.compartments) - 1))
                        for ing_name in sorted(ingrs_dic, key=sortkey):  # ingrs_dic:
                            # either xref or defined
                            ing_dic = ingrs_dic[ing_name]
                            ingr = io_ingr.makeIngredientFromJson(
                                env=env, inode=ing_dic, recipe=env.name
                            )
                            rMatrix.addIngredient(ingr)
                            # setup recipe
                        compartment.setInnerRecipe(rMatrix)
                    # Go through all ingredient and setup the partner
    env.loopThroughIngr(env.set_partners_ingredient)
    # restore env.molecules if any resuylt was loaded
    env.loopThroughIngr(env.restore_molecules_array)


def load_MixedasJson(env, resultfilename=None, transpose=True):
    #        from upy.hostHelper import Helper as helper
    if resultfilename is None:
        resultfilename = env.result_file
    # use the current dictionary ?jsondic
    with open(resultfilename, "r") as fp:  # doesnt work with symbol link ?
        if autopack.use_json_hook:
            env.result_json = json.load(
                fp, object_pairs_hook=OrderedDict
            )  # ,indent=4, separators=(',', ': ')
        else:
            env.result_json = json.load(fp)
        # needto parse
    result = []
    orgaresult = []
    r = env.exteriorRecipe
    if r:
        if "cytoplasme" in env.result_json:
            if "ingredients" in env.result_json["cytoplasme"]:
                for ingr in r.ingredients:
                    name_ingr = ingr.name
                    if name_ingr not in env.result_json["cytoplasme"]["ingredients"]:
                        # backward compatiblity
                        if (
                            ingr.composition_name
                            not in env.result_json["cytoplasme"]["ingredients"]
                        ):
                            continue
                        else:
                            name_ingr = ingr.composition_name
                    iresults, ingrname, ingrcompNum, ptInd, rad = env.getOneIngrJson(
                        ingr, env.result_json["cytoplasme"]["ingredients"][name_ingr]
                    )
                    for r in iresults:  # what if quaternion ?
                        if len(r[1]) == 4:  # quaternion
                            if type(r[1][0]) == float:
                                if transpose:
                                    rot = tr.matrix_from_quaternion(
                                        r[1]
                                    ).transpose()  # transpose ?
                                else:
                                    rot = tr.matrix_from_quaternion(r[1])  # transpose ?
                                    #                        ingr.results.append([numpy.array(r[0]),rot])
                            else:
                                rot = numpy.array(r[1]).reshape(4, 4)
                        else:
                            rot = numpy.array(r[1]).reshape(4, 4)
                        result.append(
                            [numpy.array(r[0]), rot, ingrname, ingrcompNum, 1]
                        )
                    # organelle ingr
    for i, orga in enumerate(env.compartments):
        orgaresult.append([])
        # organelle surface ingr
        if orga.name not in env.result_json["compartments"]:
            continue
        rs = orga.surfaceRecipe
        if rs:
            if "surface" in env.result_json["compartments"][orga.name]:
                for ingr in rs.ingredients:
                    name_ingr = ingr.name
                    # replace number by name ?
                    if (
                        orga.name + "_surf_" + ingr.composition_name
                        in env.result_json["compartments"][orga.name]["surface"][
                            "ingredients"
                        ]
                    ):
                        name_ingr = orga.name + "_surf_" + ingr.composition_name
                    if (
                        name_ingr
                        not in env.result_json["compartments"][orga.name]["surface"][
                            "ingredients"
                        ]
                    ):
                        # backward compatiblity
                        if (
                            ingr.composition_name
                            not in env.result_json["compartments"][orga.name][
                                "surface"
                            ]["ingredients"]
                        ):
                            continue
                        else:
                            name_ingr = ingr.composition_name
                    iresults, ingrname, ingrcompNum, ptInd, rad = env.getOneIngrJson(
                        ingr,
                        env.result_json["compartments"][orga.name]["surface"][
                            "ingredients"
                        ][name_ingr],
                    )
                    for r in iresults:
                        rot = numpy.identity(4)
                        if len(r[1]) == 4:  # quaternion
                            if type(r[1][0]) == float:
                                if transpose:
                                    rot = tr.matrix_from_quaternion(
                                        r[1]
                                    ).transpose()  # transpose ?
                                else:
                                    rot = tr.matrix_from_quaternion(r[1])  # transpose ?
                            else:
                                rot = numpy.array(r[1]).reshape(4, 4)
                            #                        ingr.results.append([numpy.array(r[0]),rot])
                        else:
                            rot = numpy.array(r[1]).reshape(4, 4)
                        orgaresult[abs(ingrcompNum) - 1].append(
                            [numpy.array(r[0]), rot, ingrname, ingrcompNum, 1]
                        )
        # organelle matrix ingr
        ri = orga.innerRecipe
        if ri:
            if "interior" in env.result_json["compartments"][orga.name]:
                for ingr in ri.ingredients:
                    name_ingr = ingr.name
                    if (
                        orga.name + "_int_" + ingr.composition_name
                        in env.result_json["compartments"][orga.name]["interior"][
                            "ingredients"
                        ]
                    ):
                        name_ingr = orga.name + "_int_" + ingr.composition_name
                    if (
                        name_ingr
                        not in env.result_json["compartments"][orga.name]["interior"][
                            "ingredients"
                        ]
                    ):
                        # backward compatiblity
                        if (
                            ingr.composition_name
                            not in env.result_json["compartments"][orga.name][
                                "interior"
                            ]["ingredients"]
                        ):
                            continue
                        else:
                            name_ingr = ingr.composition_name
                    iresults, ingrname, ingrcompNum, ptInd, rad = env.getOneIngrJson(
                        ingr,
                        env.result_json["compartments"][orga.name]["interior"][
                            "ingredients"
                        ][name_ingr],
                    )
                    for r in iresults:
                        rot = numpy.identity(4)
                        if len(r[1]) == 4:  # quaternion
                            if type(r[1][0]) == float:
                                if transpose:
                                    rot = tr.matrix_from_quaternion(
                                        r[1]
                                    ).transpose()  # transpose ?
                                else:
                                    rot = tr.matrix_from_quaternion(r[1])  # transpose ?
                            else:
                                rot = numpy.array(r[1]).reshape(4, 4)
                            #                        ingr.results.append([numpy.array(r[0]),rot])
                        else:
                            rot = numpy.array(r[1]).reshape(4, 4)
                        orgaresult[abs(ingrcompNum) - 1].append(
                            [numpy.array(r[0]), rot, ingrname, ingrcompNum, 1]
                        )
    freePoint = []  # pickle.load(rfile)
    try:
        rfile = open(resultfilename + "_free_points", "rb")
        freePoint = pickle.load(rfile)
        rfile.close()
    except:  # noqa: E722
        pass
    return result, orgaresult, freePoint

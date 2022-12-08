# -*- coding: utf-8 -*-

"""Write out data for cellpack."""


import json
import os
import numpy
from collections import OrderedDict

from cellpack import autopack
from cellpack.autopack.firebase import save_to_firestore


class IOingredientTool(object):
    # parser that can return an ingredient
    def __init__(self, env=None):
        super(IOingredientTool, self)
        self.env = env
        self.use_quaternion = False

    def write(self, ingr, filename, ingr_format="xml", kwds=None, result=False):
        if ingr_format == "json":
            ingdic = self.ingrJsonNode(ingr, result=result, kwds=kwds)
            with open(filename + ".json", "w") as fp:  # doesnt work with symbol link ?
                json.dump(
                    ingdic, fp, indent=1, separators=(",", ":")
                )  # ,indent=4, separators=(',', ': ')
        elif ingr_format == "all":
            ingdic = self.ingrJsonNode(ingr, result=result, kwds=kwds)
            with open(filename + ".json", "w") as fp:  # doesnt work with symbol link ?
                json.dump(
                    ingdic, fp, indent=4, separators=(",", ": ")
                )  # ,indent=4, separators=(',', ': ')
            ingrnode = self.ingrPythonNode(ingr)
            f = open(filename + ".py", "w")
            f.write(ingrnode)
            f.close()


class NumpyArrayEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, numpy.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


class Writer(object):
    def __init__(self, format="simularium"):
        self.format = format

    @staticmethod
    def setValueToJsonNode(value, attrname):
        vdic = OrderedDict()
        vdic[attrname] = None
        if value is None:
            print(attrname, " is None !")
            return vdic
        if attrname == "color":
            if type(value) != list and type(value) != tuple:
                if autopack.helper is not None:
                    value = autopack.helper.getMaterialProperty(value, ["color"])[0]
                else:
                    value = [1.0, 0.0, 0.0]
        if type(value) == numpy.ndarray:
            value = value.tolist()
        elif type(value) == list or type(value) == tuple:
            if len(value) == 0:
                return vdic
            else:
                for i, v in enumerate(value):
                    if type(v) == numpy.ndarray:
                        value[i] = v.tolist()
                    elif type(v) == list or type(v) == tuple:
                        for j, va in enumerate(v):
                            if type(va) == numpy.ndarray:
                                v[j] = va.tolist()
                                # node.setAttribute(attrname,str(value))
        vdic[attrname] = value
        return vdic

    def save_as_simularium(self, env, setupfile, all_ingr_as_array, compartments):
        autopack.helper.clear()
        grid_positions = env.grid.masterGridPositions if env.show_grid_spheres else None
        compartment_ids = env.grid.compartment_ids if env.show_grid_spheres else None
        autopack.helper.init_scene_with_objects(
            all_ingr_as_array, grid_positions, compartment_ids, env.show_sphere_trees
        )
        if compartments is not None:
            for compartment in compartments:
                autopack.helper.add_compartment_to_scene(compartment)
        autopack.helper.writeToFile(None, f"{setupfile}_results", env.boundingBox)

    def save_Mixed_asJson(
        self,
        env,
        setupfile,
        useXref=True,
        kwds=None,
        result=False,
        grid=False,
        packing_options=False,
        indent=True,
        quaternion=False,
        transpose=False,
    ):
        """
        Save the current environment setup as an json file.
        env is the environment / recipe to be exported.
        """
        io_ingr = IOingredientTool(env=env)
        io_ingr.use_quaternion = quaternion
        env.setupfile = setupfile  # +".json"provide the server?
        # the output path for this recipes files
        if env.setupfile.find("http") != -1 or env.setupfile.find("ftp") != -1:
            pathout = os.path.dirname(
                os.path.abspath(autopack.retrieveFile(env.setupfile))
            )
        else:
            pathout = os.path.dirname(os.path.abspath(env.setupfile))
        if env.version is None:
            env.version = "1.0"
        env.jsondic = OrderedDict(
            {"recipe": {"name": env.name, "version": env.version}}
        )
        if env.custom_paths:
            # this was the used path at loading time
            env.jsondic["recipe"]["paths"] = env.custom_paths
        if result:
            env.jsondic["recipe"]["setupfile"] = env.setupfile
        if packing_options:
            env.jsondic["options"] = {}
            for k in env.OPTIONS:
                v = getattr(env, k)
                if k == "gradients":
                    v = list(env.gradients.keys())
                    #            elif k == "runTimeDisplay"
                env.jsondic["options"].update(self.setValueToJsonNode(v, k))
            # add the boundin box
            env.jsondic["options"].update(
                self.setValueToJsonNode(env.boundingBox, "boundingBox")
            )
        if grid:
            # grid path information
            if env.grid is not None:
                if (
                    env.grid.filename is not None
                    or env.grid.result_filename is not None
                ):
                    env.jsondic["grid"] = {
                        "grid_storage": str(env.grid.filename),
                        "grid_result": str(env.grid.result_filename),
                    }

        if packing_options:
            # gradient information
            if len(env.gradients):
                env.jsondic["gradients"] = {}
                for gname in env.gradients:
                    g = env.gradients[gname]
                    env.jsondic["gradients"][str(g.name)] = {}
                    for k in g.OPTIONS:
                        v = getattr(g, k)
                        env.jsondic["gradients"][str(g.name)].update(
                            self.setValueToJsonNode(v, k)
                        )

        r = env.exteriorRecipe
        if r:
            env.jsondic["cytoplasme"] = {}
            env.jsondic["cytoplasme"]["ingredients"] = {}
            for ingr in r.ingredients:
                if useXref and packing_options:
                    # write the json file for this ingredient
                    io_ingr.write(
                        ingr,
                        pathout + os.sep + ingr.o_name,
                        ingr_format="json",
                        kwds=kwds,
                        result=result,
                        transpose=transpose,
                    )
                    # use reference file : str(pathout+os.sep+ingr.o_name+".json")
                    ing_filename = (
                        ingr.o_name + ".json"
                    )  # autopack.revertOnePath(pathout+os.sep+ingr.o_name+".json")
                    env.jsondic["cytoplasme"]["ingredients"][ingr.o_name] = {
                        "name": ingr.o_name,
                        "include": ing_filename,
                    }
                else:
                    env.jsondic["cytoplasme"]["ingredients"][
                        ingr.o_name
                    ] = io_ingr.ingrJsonNode(
                        ingr, result=result, kwds=kwds, transpose=transpose
                    )  # {"name":ingr.o_name}
                    env.jsondic["cytoplasme"]["ingredients"][ingr.o_name][
                        "name"
                    ] = ingr.o_name
        if len(env.compartments):
            env.jsondic["compartments"] = OrderedDict()
        for o in env.compartments:
            env.jsondic["compartments"][str(o.name)] = OrderedDict()
            if packing_options:
                env.jsondic["compartments"][str(o.name)]["geom"] = str(
                    o.filename
                )  # should point to the used filename
                env.jsondic["compartments"][str(o.name)]["name"] = str(o.ref_obj)
                if o.representation is not None:
                    fileName, fileExtension = os.path.splitext(o.representation_file)
                    env.jsondic["compartments"][str(o.name)]["rep"] = str(
                        o.representation
                    )  # None
                    env.jsondic["compartments"][str(o.name)]["rep_file"] = str(fileName)
            rs = o.surfaceRecipe
            if rs:
                env.jsondic["compartments"][str(o.name)]["surface"] = {}
                env.jsondic["compartments"][str(o.name)]["surface"]["ingredients"] = {}
                for ingr in rs.ingredients:
                    if useXref and packing_options:
                        # write the json file for this ingredient
                        io_ingr.write(
                            ingr,
                            pathout + os.sep + ingr.o_name,
                            ingr_format="json",
                            result=result,
                            kwds=kwds,
                            transpose=transpose,
                        )
                        # use reference file
                        env.jsondic["compartments"][str(o.name)]["surface"][
                            "ingredients"
                        ][ingr.o_name] = {
                            "name": ingr.o_name,
                            "include": str(ingr.o_name + ".json"),
                        }
                    else:
                        env.jsondic["compartments"][str(o.name)]["surface"][
                            "ingredients"
                        ][ingr.o_name] = io_ingr.ingrJsonNode(
                            ingr, result=result, kwds=kwds, transpose=transpose
                        )  # {"name":ingr.o_name}
                        env.jsondic["compartments"][str(o.name)]["surface"][
                            "ingredients"
                        ][ingr.o_name]["name"] = ingr.o_name
            ri = o.innerRecipe
            if ri:
                env.jsondic["compartments"][str(o.name)]["interior"] = {}
                env.jsondic["compartments"][str(o.name)]["interior"]["ingredients"] = {}
                for ingr in ri.ingredients:
                    if useXref and packing_options:
                        # write the json file for this ingredient
                        io_ingr.write(
                            ingr,
                            pathout + os.sep + ingr.o_name,
                            ingr_format="json",
                            result=result,
                            kwds=kwds,
                            transpose=transpose,
                        )
                        # use reference file
                        env.jsondic["compartments"][str(o.name)]["interior"][
                            "ingredients"
                        ][ingr.o_name] = {
                            "name": ingr.o_name,
                            "include": str(ingr.o_name + ".json"),
                        }
                    else:
                        env.jsondic["compartments"][str(o.name)]["interior"][
                            "ingredients"
                        ][ingr.o_name] = io_ingr.ingrJsonNode(
                            ingr, result=result, kwds=kwds, transpose=transpose
                        )  # {"name":ingr.o_name}
                        env.jsondic["compartments"][str(o.name)]["interior"][
                            "ingredients"
                        ][ingr.o_name]["name"] = ingr.o_name
        with open(setupfile, "w") as fp:  # doesnt work with symbol link ?

            if indent:
                json.dump(
                    env.jsondic,
                    fp,
                    indent=1,
                    separators=(",", ":"),
                    cls=NumpyArrayEncoder,
                )  # ,indent=4, separators=(',', ': ')
            else:
                json.dump(
                    env.jsondic, fp, separators=(",", ":"), cls=NumpyArrayEncoder
                )  # ,indent=4, separators=(',', ': ')

    def return_object_value(data):
        for key, value in data.items():
            if isinstance(value, object):
                data[key] = vars(value)
            elif isinstance(value, dict): 
                return_object_value(value)
            else:
                data[key] = value
        return data

    def save(
        self,
        env,
        setupfile,
        kwds=None,
        result=False,
        grid=False,
        packing_options=False,
        indent=False,
        quaternion=False,
        transpose=False,
        all_ingr_as_array=None,
        compartments=None,
    ):
        output_format = self.format
        if output_format == "json":
            self.save_Mixed_asJson(
                env,
                setupfile,
                useXref=False,
                kwds=kwds,
                result=result,
                indent=indent,
                grid=grid,
                packing_options=packing_options,
                quaternion=quaternion,
                transpose=transpose,
            )
        elif output_format == "simularium":
            self.save_as_simularium(env, setupfile, all_ingr_as_array, compartments)
        else:
            print("format output " + output_format + " not recognized (json,python)")

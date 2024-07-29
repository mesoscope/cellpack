# -*- coding: utf-8 -*-

"""Write out data for cellpack."""


import json
import os
from pathlib import Path
import numpy
from collections import OrderedDict

from mdutils.mdutils import MdUtils
import pandas as pd

from cellpack import autopack
from cellpack.autopack.ingredient.grow import ActinIngredient, GrowIngredient
import cellpack.autopack.transformation as tr


def updatePositionsRadii(ingr):
    toupdate = {"positions": []}
    toupdate["radii"] = []
    if getattr(ingr, "positions", None) is not None:
        nLOD = len(ingr.positions)
        for i in range(nLOD):
            toupdate["positions"].append(
                {"coords": numpy.array(ingr.positions[i]).flatten().tolist()}
            )
            toupdate["radii"].append({"radii": ingr.radii[i]})
    return toupdate


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

    def save_as_simularium(self, env, seed_to_results_map):
        env.helper.clear()

        grid_positions = env.grid.masterGridPositions if env.show_grid_spheres else None
        compartment_ids = env.grid.compartment_ids if env.show_grid_spheres else None

        # one packing
        for _, all_ingr_as_array in seed_to_results_map.items():

            env.helper.init_scene_with_objects(
                objects=all_ingr_as_array,
                grid_point_positions=grid_positions,
                grid_point_compartment_ids=compartment_ids,
                show_sphere_trees=env.show_sphere_trees,
                grid_pt_radius=env.grid.gridSpacing / 4,
            )

        # Same for all packings
        # plots the distances used to calculate gradients
        # TODO: add an option to plot grid points for compartments and for gradients
        if grid_positions is not None and len(env.gradients):
            for _, gradient in env.gradients.items():
                env.helper.add_grid_data_to_scene(
                    f"{gradient.name}-distances",
                    grid_positions,
                    gradient.distances,
                    env.grid.gridSpacing / 4,
                )
                env.helper.add_grid_data_to_scene(
                    f"{gradient.name}-weights",
                    grid_positions,
                    gradient.weight,
                    env.grid.gridSpacing / 4,
                )
        # write to simularium format
        result_file_name = env.result_file
        is_aggregate = len(seed_to_results_map) > 1
        if is_aggregate:
            result_file_name = f"{env.result_file.split('_seed')[0]}_all"
        else:
            result_file_name = f"{env.result_file.split('_seed')[0]}_seed_{list(seed_to_results_map.keys())[0]}"
        file_name = env.helper.writeToFile(
            result_file_name, env.boundingBox, env.name, env.version
        )
        number_of_packings = env.config_data.get("number_of_packings", 1)
        open_results_in_browser = env.config_data.get("open_results_in_browser", True)
        upload_results = env.config_data.get("upload_results", True)
        if (number_of_packings == 1 or is_aggregate) and upload_results:
            autopack.helper.post_and_open_file(file_name, open_results_in_browser)

    def save_Mixed_asJson(
        self,
        env,
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
        file_name = f"{env.result_file}.json"
        # the output path for this recipes files
        if file_name.find("http") != -1 or file_name.find("ftp") != -1:
            pathout = os.path.dirname(os.path.abspath(autopack.retrieveFile(file_name)))
        else:
            pathout = os.path.dirname(os.path.abspath(file_name))
        if env.version is None:
            env.version = "1.0"
        env.jsondic = OrderedDict(
            {"recipe": {"name": env.name, "version": env.version}}
        )
        if env.custom_paths:
            # this was the used path at loading time
            env.jsondic["recipe"]["paths"] = env.custom_paths
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
                        pathout + os.sep + ingr.composition_name,
                        ingr_format="json",
                        kwds=kwds,
                        result=result,
                        transpose=transpose,
                    )
                    # use reference file : str(pathout+os.sep+ingr.composition_name+".json")
                    ing_filename = (
                        ingr.composition_name + ".json"
                    )  # autopack.revertOnePath(pathout+os.sep+ingr.composition_name+".json")
                    env.jsondic["cytoplasme"]["ingredients"][ingr.composition_name] = {
                        "name": ingr.composition_name,
                        "include": ing_filename,
                    }
                else:
                    env.jsondic["cytoplasme"]["ingredients"][
                        ingr.composition_name
                    ] = io_ingr.ingrJsonNode(
                        ingr, result=result, kwds=kwds, transpose=transpose
                    )  # {"name":ingr.composition_name}
                    env.jsondic["cytoplasme"]["ingredients"][ingr.composition_name][
                        "name"
                    ] = ingr.composition_name
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
                            pathout + os.sep + ingr.composition_name,
                            ingr_format="json",
                            result=result,
                            kwds=kwds,
                            transpose=transpose,
                        )
                        # use reference file
                        env.jsondic["compartments"][str(o.name)]["surface"][
                            "ingredients"
                        ][ingr.composition_name] = {
                            "name": ingr.composition_name,
                            "include": str(ingr.composition_name + ".json"),
                        }
                    else:
                        env.jsondic["compartments"][str(o.name)]["surface"][
                            "ingredients"
                        ][ingr.composition_name] = io_ingr.ingrJsonNode(
                            ingr, result=result, kwds=kwds, transpose=transpose
                        )  # {"name":ingr.composition_name}
                        env.jsondic["compartments"][str(o.name)]["surface"][
                            "ingredients"
                        ][ingr.composition_name]["name"] = ingr.composition_name
            ri = o.innerRecipe
            if ri:
                env.jsondic["compartments"][str(o.name)]["interior"] = {}
                env.jsondic["compartments"][str(o.name)]["interior"]["ingredients"] = {}
                for ingr in ri.ingredients:
                    if useXref and packing_options:
                        # write the json file for this ingredient
                        io_ingr.write(
                            ingr,
                            pathout + os.sep + ingr.composition_name,
                            ingr_format="json",
                            result=result,
                            kwds=kwds,
                            transpose=transpose,
                        )
                        # use reference file
                        env.jsondic["compartments"][str(o.name)]["interior"][
                            "ingredients"
                        ][ingr.composition_name] = {
                            "name": ingr.composition_name,
                            "include": str(ingr.composition_name + ".json"),
                        }
                    else:
                        env.jsondic["compartments"][str(o.name)]["interior"][
                            "ingredients"
                        ][ingr.composition_name] = io_ingr.ingrJsonNode(
                            ingr, result=result, kwds=kwds, transpose=transpose
                        )  # {"name":ingr.composition_name}
                        env.jsondic["compartments"][str(o.name)]["interior"][
                            "ingredients"
                        ][ingr.composition_name]["name"] = ingr.composition_name
        with open(file_name, "w") as fp:  # doesnt work with symbol link ?
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

    @staticmethod
    def return_object_value(data):
        for key, value in data.items():
            if isinstance(value, object):
                data[key] = vars(value)
            elif isinstance(value, dict):
                Writer.return_object_value(value)
            else:
                data[key] = value
        return data

    def save(
        self,
        env,
        kwds=None,
        result=False,
        grid=False,
        packing_options=False,
        indent=False,
        quaternion=False,
        transpose=False,
        seed_to_results_map=None,
    ):
        output_format = self.format
        if output_format == "json":
            self.save_Mixed_asJson(
                env,
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
            self.save_as_simularium(env, seed_to_results_map)
        else:
            print("format output " + output_format + " not recognized (json,python)")


class MarkdownWriter(object):
    def __init__(
        self,
        title: str,
        output_path: Path,
        output_image_location: Path,
        report_name: str,
    ):
        self.title = title
        self.output_path = output_path
        self.output_image_location = output_image_location
        self.report_md = MdUtils(
            file_name=str(self.output_path / report_name),
            title=title,
        )

    # level is the header style, can only be 1 or 2
    def add_header(self, header, level: int = 2):
        self.report_md.new_header(level=level, title=header, add_table_of_contents="n")

    def add_table(self, header, table, text_align="center"):
        self.report_md.new_header(
            level=1,
            title=header,
            add_table_of_contents="n",
        )

        header_row = table.columns.tolist()
        text_list = header_row + [
            item for sublist in table.values.tolist() for item in sublist
        ]

        total_rows = table.shape[0] + 1  # Adding 1 for the header row
        total_columns = table.shape[1]

        self.report_md.new_table(
            columns=total_columns,
            rows=total_rows,
            text=text_list,
            text_align=text_align,
        )

    def add_table_from_csv(self, header, filepath, text_align="center"):
        self.report_md.new_header(
            level=1,
            title=header,
            add_table_of_contents="n",
        )

        table = pd.read_csv(filepath)

        header_row = table.columns.tolist()
        text_list = header_row + [
            item for sublist in table.values.tolist() for item in sublist
        ]
        total_rows = table.shape[0] + 1  # Adding 1 for the header row
        total_columns = table.shape[1]

        self.report_md.new_table(
            columns=total_columns,
            rows=total_rows,
            text=text_list,
            text_align=text_align,
        )

    # Image text must be a list, if list is not same length as list of filepaths, only 1st item in image_text is used
    def add_images(self, header, image_text, filepaths):
        self.report_md.new_header(
            level=1,
            title=header,
            add_table_of_contents="n",
        )
        if len(image_text) == len(filepaths):
            for i in range(len(filepaths)):
                self.report_md.new_line(
                    self.report_md.new_inline_image(
                        text=image_text[i],
                        path=str(self.output_image_location / filepaths[i].name),
                    )
                )
        else:
            for i in range(len(filepaths)):
                self.report_md.new_line(
                    self.report_md.new_inline_image(
                        text=image_text[0],
                        path=str(self.output_image_location / filepaths[i].name),
                    )
                )
        self.report_md.new_line("")

    def add_line(self, line):
        self.report_md.new_line(line)

    def add_list(self, list_items):
        self.report_md.new_list(list_items)

    def add_inline_image(self, text, filepath):
        return self.report_md.new_inline_image(text=text, path=str(filepath))

    def write_file(self):
        self.report_md.create_md_file()

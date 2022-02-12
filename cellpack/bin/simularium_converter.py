import os
import sys
import argparse
import traceback
import numpy as np
import json
import logging

from scipy.spatial.transform import Rotation as R

from simulariumio import (
    TrajectoryConverter,
    TrajectoryData,
    AgentData,
    UnitData,
    MetaData,
    CameraData,
    DisplayData,
)
from simulariumio.constants import DISPLAY_TYPE

from cellpack.autopack.iotools_simple import RecipeLoader

###############################################################################

log = logging.getLogger()
logging.basicConfig(
    level=logging.INFO, format="[%(levelname)4s:%(lineno)4s %(asctime)s] %(message)s"
)

###############################################################################


class ConvertToSimularium(argparse.Namespace):
    DEFAULT_PACKING_RESULT = "/Users/meganriel-mehan/Dropbox/cellPack/NM_Analysis_C_rapid/results_seed_0.json"
    DEFAULT_OUTPUT_DIRECTORY = "/Users/meganriel-mehan/Dropbox/cellPack/"
    DEFAULT_INPUT_RECIPE = "/Users/meganriel-mehan/dev/allen-inst/cellPack/cellpack/cellpack/test-recipes/NM_Analysis_FigureC1.json"
    DEFAULT_GEO_TYPE = "OBJ"  # Other options: SPHERE or PDB
    DEFAULT_SCALE_FACTOR = 1.0 / 10

    def __init__(self, total_steps=1):
        # Arguments that could be passed in through the command line
        self.input_recipe = self.DEFAULT_INPUT_RECIPE
        self.packing_result = self.DEFAULT_PACKING_RESULT
        self.output = self.DEFAULT_OUTPUT_DIRECTORY
        self.recipe_name = ""
        self.scale_factor = self.DEFAULT_SCALE_FACTOR
        self.geo_type = self.DEFAULT_GEO_TYPE
        self.debug = True
        self.__parse()
        # simularium parameters
        self.total_steps = total_steps
        self.timestep = 1
        self.box_size = 1000 * self.scale_factor
        self.n_agents = [0 for x in range(total_steps)]
        self.points_per_fiber = 0
        self.type_names = [[] for x in range(total_steps)]
        self.display_data = {}
        self.positions = [[] for x in range(total_steps)]
        self.rotations = [[] for x in range(total_steps)]
        self.viz_types = [[] for x in range(total_steps)]
        self.unique_ids = [[] for x in range(total_steps)]
        self.radii = [[] for x in range(total_steps)]
        self.n_subpoints = [[] for x in range(total_steps)]
        self.subpoints = [[] for x in range(total_steps)]
        self.agent_id_counter = 0
        # stored data for processesing
        self.fiber_points = [[] for x in range(total_steps)]
        self.max_fiber_length = 0
        # defaults for missing data
        self.default_radius = 1

    def __parse(self):
        p = argparse.ArgumentParser(
            prog="convert_to_simularium",
            description="Convert cellpack result to simularium",
        )
        p.add_argument(
            "-r",
            "--input-recipe",
            action="store",
            dest="input_recipe",
            type=str,
            default=self.input_recipe,
            help="Full path for the input recipe file",
        )
        p.add_argument(
            "-p",
            "--packing-result",
            action="store",
            dest="packing_result",
            type=str,
            default=self.packing_result,
            help="Full path of the packing result file",
        )
        p.add_argument(
            "-g",
            "--geo-type",
            action="store",
            dest="geo_type",
            type=str,
            default=self.geo_type,
            help="Whether to use PDB ids or OBJs",
        )
        p.add_argument(
            "-o",
            "--output",
            action="store",
            dest="output",
            type=str,
            default=self.output,
            help="Full path for where to store the simularium file",
        )

        p.add_argument(
            "--debug",
            action="store_true",
            dest="debug",
            help=argparse.SUPPRESS,
        )
        p.parse_args(namespace=self)

    def get_bounding_box(self, recipe_data):
        options = recipe_data["options"]
        bb = options["boundingBox"]
        x_size = bb[1][0] - bb[0][0]
        y_size = bb[1][1] - bb[0][1]
        z_size = bb[1][2] - bb[0][2]
        self.box_size = [
            x_size * self.scale_factor,
            y_size * self.scale_factor,
            z_size * self.scale_factor,
        ]

    def get_ingredient_display_data(self, ingredient_data):
        if self.geo_type == "OBJ" and "meshFile" in ingredient_data:
            meshType = (
                ingredient_data["meshType"]
                if ("meshType" in ingredient_data)
                else "file"
            )
            if meshType == "file":
                file_path = os.path.basename(ingredient_data["meshFile"])
                file_name, _ = os.path.splitext(file_path)
                return {
                    "display_type": DISPLAY_TYPE.OBJ,
                    "url": f"https://raw.githubusercontent.com/mesoscope/cellPACK_data/master/cellPACK_database_1.1.0/geometries/{file_name}.obj",
                }
            elif meshType == "raw":
                file_name = ingredient_data["name"]
                return {
                    "display_type": DISPLAY_TYPE.OBJ,
                    "url": f"https://raw.githubusercontent.com/mesoscope/cellPACK_data/master/cellPACK_database_1.1.0/geometries/{file_name}.obj",
                }
        elif self.geo_type == "PDB":
            pdb_file_name = ""
            if "source" in ingredient_data:
                pdb_file_name = ingredient_data["source"]["pdb"]
            elif "pdb" in ingredient_data:
                pdb_file_name = ingredient_data["pdb"]
            if ".pdb" in pdb_file_name:
                url = f"https://raw.githubusercontent.com/mesoscope/cellPACK_data/master/cellPACK_database_1.1.0/other/{pdb_file_name}"
            else:
                url = pdb_file_name
            return {
                "display_type": DISPLAY_TYPE.PDB,
                "url": url,
            }
        else:
            display_type = (
                DISPLAY_TYPE.FIBER
                if ingredient_data["Type"] == "Grow"
                else DISPLAY_TYPE.SPHERE
            )
            return {"display_type": display_type, "url": ""}

    def get_ingredient_data(self, cytoplasm, main_container, ingredient):
        ingredient_name = None
        cytoplasm_data = None
        container_data = None
        if cytoplasm is not None:
            ingredient_name = ingredient["name"]
            ingredients = cytoplasm["ingredients"]
            try:
                cytoplasm_data = ingredients[ingredient_name]
            except Exception:
                pass
        elif main_container is not None:
            ingredient_name = ingredient["name"]
            compartment = main_container[ingredient["compartment"]]
            position = ingredient["position"]
            try:
                compartment[position]
                container_data = compartment[ingredient["position"]]["ingredients"][
                    ingredient_name
                ]
            except Exception as e:
                # Ingredient in recipe wasn't packed
                log.error(e, position, ingredient_name)
        return (ingredient_name, cytoplasm_data, container_data)

    def get_euler_from_matrix(self, data_in):
        rotation_matrix = [data_in[0][0:3], data_in[1][0:3], data_in[2][0:3]]
        euler = R.from_matrix(rotation_matrix).as_euler("XYZ", degrees=False)
        return euler

    def get_euler_from_quat(self, data_in):
        euler = R.from_quat(data_in).as_euler("ZYX", degrees=False)
        return [euler[0], euler[1], -euler[2]]

    def is_matrix(self, data_in):
        if isinstance(data_in[0], list):
            return True
        else:
            return False

    def unpack_curve(self, data, time_step_index, ingredient_name, index, agent_id):
        curve = "curve" + str(index)
        self.positions[time_step_index].append([0, 0, 0])
        self.rotations[time_step_index].append([0, 0, 0])
        self.viz_types[time_step_index].append(1001)
        self.n_agents[time_step_index] = self.n_agents[time_step_index] + 1
        self.type_names[time_step_index].append(ingredient_name)
        self.unique_ids[time_step_index].append(agent_id)
        r = (
            data["encapsulatingRadius"] * self.scale_factor
            if ("encapsulatingRadius" in data)
            else self.default_radius
        )
        self.radii[time_step_index].append(r)
        self.n_subpoints[time_step_index].append(len(data[curve]))
        scaled_control_points = np.array(data[curve]) * self.scale_factor
        self.fiber_points[time_step_index].append(scaled_control_points.tolist())
        if len(data[curve]) > self.max_fiber_length:
            if self.debug:
                print("found longer fiber, new max", len(data[curve]))
            self.max_fiber_length = len(data[curve])

    def unpack_positions(
        self,
        data,
        time_step_index,
        ingredient_name,
        index,
        agent_id,
        comp_id=0,
        left_hand=False,
    ):
        position = data["results"][index][0]
        offset = None
        offset = np.array([0, 0, 0])
        # TODO : deal with membrane ingredient transformation
        # if "source" in data:
        #     offset = np.array(data["source"]["transform"]["offset"])
        # else:
        #     offset = np.array([0, 0, 0])
        if comp_id <= 0:
            offset = offset * -1
        self.positions[time_step_index].append(
            [
                (position[0] + offset[0]) * self.scale_factor,
                (position[1] + offset[1]) * self.scale_factor,
                (position[2] + offset[2]) * self.scale_factor,
            ]
        )
        rotation_in = data["results"][index][1]
        rotation = self.get_euler(rotation_in)
        self.rotations[time_step_index].append(rotation)
        self.viz_types[time_step_index].append(1000)
        self.n_agents[time_step_index] = self.n_agents[time_step_index] + 1
        self.type_names[time_step_index].append(ingredient_name)
        self.unique_ids[time_step_index].append(agent_id)
        if "radii" in data:
            self.radii[time_step_index].append(
                data["radii"][0]["radii"][0] * self.scale_factor
            )
        elif "encapsulatingRadius" in data:
            self.radii[time_step_index].append(
                data["encapsulatingRadius"] * self.scale_factor
            )
        else:
            self.radii[time_step_index].append(self.default_radius)

        self.n_subpoints[time_step_index].append(0)

    def get_euler(self, data_in):
        if self.is_matrix(data_in):
            return self.get_euler_from_matrix(data_in)
        else:
            return self.get_euler_from_quat(data_in)

    def process_one_ingredient(
        self,
        ingredient_data,
        time_step_index,
    ):
        recipe_data = ingredient_data["recipe_data"]
        results = ingredient_data["results"]
        ingredient_key = results["name"]
        display_data = self.get_ingredient_display_data(recipe_data)
        self.display_data[ingredient_key] = DisplayData(
            name=ingredient_key,
            display_type=display_data["display_type"],
            url=display_data["url"],
        )
        left_hand = False
        if "coordsystem" in recipe_data and recipe_data["coordsystem"] == "left":
            left_hand = True
        if len(results["results"]) > 0:
            for j in range(len(results["results"])):
                self.unpack_positions(
                    results,
                    time_step_index,
                    ingredient_key,
                    j,
                    self.agent_id_counter,
                    left_hand=left_hand,
                )
                self.agent_id_counter = self.agent_id_counter + 1
        elif "nbCurve" in results and results["nbCurve"] > 0:
            for i in range(results["nbCurve"]):
                self.unpack_curve(
                    results,
                    time_step_index,
                    ingredient_key,
                    i,
                    self.agent_id_counter,
                )
                self.agent_id_counter = self.agent_id_counter + 1

    def get_positions_per_ingredient(
        self, all_ingredients, results_data_in, time_step_index
    ):
        if results_data_in["recipe"]["name"] != self.recipe_name:
            raise Exception(
                "Recipe name in results file doesn't match recipe file",
                "result:",
                results_data_in["recipe"]["name"],
                "recipe",
                self.recipe_name,
            )
        self.agent_id_counter = 0
        for ingredient_data in all_ingredients:
            self.process_one_ingredient(ingredient_data, time_step_index)

    def fill_in_empty_fiber_data(self, time_step_index):
        for viz_type in self.viz_types[time_step_index]:
            if viz_type == 1000:
                blank_value = [[0, 0, 0] for x in range(self.max_fiber_length)]
                self.subpoints[time_step_index].append(blank_value)
            elif viz_type == 1001:
                if self.debug:
                    print("adding control points")
                control_points = self.fiber_points[time_step_index].pop(0)
                while len(control_points) < self.max_fiber_length:
                    control_points.append([0, 0, 0])
                self.subpoints[time_step_index].append(control_points)


###############################################################################


def main():
    converter = ConvertToSimularium()
    dbg = converter.debug
    try:
        time_point_index = 0
        results_in = converter.packing_result
        recipe_loader = RecipeLoader(converter.input_recipe)
        recipe_data = recipe_loader.recipe_data
        packing_data = json.load(open(results_in, "r"))
        all_ingredients = recipe_loader.get_all_ingredients(packing_data)

        converter.recipe_name = recipe_data["recipe"]["name"]
        converter.get_bounding_box(recipe_data)
        box_size = converter.box_size
        converter.get_positions_per_ingredient(
            all_ingredients, packing_data, time_point_index
        )
        converter.fill_in_empty_fiber_data(time_point_index)
        if converter.debug:
            print("SUBPOINTS LENGTH", len(converter.subpoints[time_point_index]))
        camera_z_position = box_size[2] if box_size[2] > 10 else 100.0
        converted_data = TrajectoryData(
            meta_data=MetaData(
                box_size=np.array(box_size),
                camera_defaults=CameraData(
                    position=np.array([10.0, 0.0, camera_z_position]),
                    look_at_position=np.array([10.0, 0.0, 0.0]),
                    fov_degrees=60.0,
                ),
            ),
            agent_data=AgentData(
                display_data=converter.display_data,
                times=converter.timestep * np.array(list(range(converter.total_steps))),
                n_agents=np.array(converter.n_agents),
                viz_types=np.array(converter.viz_types),
                unique_ids=np.array(converter.unique_ids),
                types=np.array(converter.type_names),
                positions=np.array(converter.positions),
                rotations=np.array(converter.rotations),
                radii=np.array(converter.radii),
                subpoints=np.array(converter.subpoints),
                n_subpoints=np.array(converter.n_subpoints),
            ),
            time_units=UnitData("ns"),  # nanoseconds
            spatial_units=UnitData("nm"),  # nanometers
        )
        TrajectoryConverter(converted_data).write_JSON(
            converter.output + converter.recipe_name
        )

    except Exception as e:
        log.error("=============================================")
        if dbg:
            log.error("\n\n" + traceback.format_exc())
            log.error("=============================================")
        log.error("\n\n" + str(e) + "\n")
        log.error("=============================================")
        sys.exit(1)


###############################################################################
# Allow caller to directly run this module (usually in development scenarios)

if __name__ == "__main__":
    main()

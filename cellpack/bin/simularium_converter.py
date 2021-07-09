
import os
import sys
import argparse
import traceback

# import cellpack.autopack.transformation as tr
from collections import OrderedDict
import numpy as np
import json
import logging

from simulariumio import CustomData, AgentData, CustomConverter
###############################################################################

log = logging.getLogger()
logging.basicConfig(
    level=logging.INFO, format="[%(levelname)4s:%(lineno)4s %(asctime)s] %(message)s"
)

###############################################################################


class ConvertToSimularium(argparse.Namespace):
    DEFAULT_INPUT_DIRECTORY = "/Users/meganriel-mehan/Dropbox/cellPack/NM_Analysis_C_rapid/"
    DEFAULT_PACKING_RESULT = "results_seed_0.json"
    DEFAULT_OUTPUT_DIRECTORY = "/Users/meganriel-mehan/Dropbox/cellPack/"
    DEFAULT_RECIPE_NAME = "NM_Analysis_FigureC"

    def __init__(self, total_steps=1):
        # Arguments that could be passed in through the command line
        self.input_directory = self.DEFAULT_INPUT_DIRECTORY
        self.packing_result_file_name = self.DEFAULT_PACKING_RESULT
        self.output = self.DEFAULT_OUTPUT_DIRECTORY
        self.recipe_name = self.DEFAULT_RECIPE_NAME
        self.debug = True
        self.__parse()
        # simularium parameters
        self.total_steps = total_steps
        self.timestep = 1
        self.box_size = 1000
        self.n_agents = [0 for x in range(total_steps)]
        self.points_per_fiber = 0
        self.type_names = [[] for x in range(total_steps)]
        self.positions = [[] for x in range(total_steps)]
        self.viz_types = [[] for x in range(total_steps)]
        self.unique_ids = [[] for x in range(total_steps)]
        self.radii = [[] for x in range(total_steps)]
        self.n_subpoints = [[] for x in range(total_steps)]
        self.subpoints = [[] for x in range(total_steps)]

        self.fiber_points = [[] for x in range(total_steps)]
        self.max_fiber_length = 0
        self.main_scale = 1.0 / 100.0  # could be 1/200.0 like flex
        self.pnames_fiber = []
        self.pnames_fiber_nodes = []
        self.pnames = []

    def __parse(self):
        p = argparse.ArgumentParser(
            prog="convert_to_simularium",
            description="Convert cellpack result to simularium",
        )
        p.add_argument(
            "-i",
            "--input-directory",
            action="store",
            dest="input_directory",
            type=str,
            default=self.input_directory,
            help="Full path for where to read the cellpack results",
        )
        p.add_argument(
            "-p",
            "--packing-result",
            action="store",
            dest="packing_result_file_name",
            type=str,
            default=self.packing_result_file_name,
            help="Name of the packing result file",
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
        options = recipe_data['options']
        bb = options['boundingBox']
        x_size = bb[1][0] - bb[0][0]
        y_size = bb[1][1] - bb[0][1]
        z_size = bb[1][2] - bb[0][2]
        self.box_size = [x_size, y_size, z_size]

    def get_positions_per_ingredient(self, results_data_in, time_step_index):
        if (results_data_in["recipe"]["name"] != self.recipe_name):
            raise Exception("Recipe name in results file doesn't match recipe file")
        container = results_data_in["cytoplasme"]
        ingredients = container["ingredients"]
        id = 0
        for i in range(len(self.unique_ingredient_names)):
            # print(ingredients[ingredient_name])
            ingredient_name = self.unique_ingredient_names[i]
            data = ingredients[ingredient_name]
            if (len(data['results']) > 0):
                for j in range(len(data['results'])):
                    self.positions[time_step_index].append(data['results'][j][0])
                    self.viz_types[time_step_index].append(1000)
                    self.n_agents[time_step_index] = self.n_agents[time_step_index] + 1
                    self.type_names[time_step_index].append(ingredient_name)
                    self.unique_ids[time_step_index].append(id)
                    self.radii[time_step_index].append(data['radii'][0]['radii'][0])
                    self.n_subpoints[time_step_index].append(0)
                    id = id + 1

            elif (data['nbCurve'] is not None):
                self.positions[time_step_index].append([0, 0, 0])
                self.viz_types[time_step_index].append(1001)
                self.n_agents[time_step_index] = self.n_agents[time_step_index] + 1
                self.type_names[time_step_index].append(ingredient_name)
                self.unique_ids[time_step_index].append(id)
                self.radii[time_step_index].append(1)
                self.n_subpoints[time_step_index].append(len(data['curve0'][j]))
                self.fiber_points[time_step_index].append(data['curve0'])
                if len(data['curve0']) > self.max_fiber_length:
                    self.max_fiber_length = len(data['curve0'])
                id = id + 1

    def fill_in_empty_fiber_data(self, time_step_index):
        blank_value = [[0, 0, 0] for x in range(self.max_fiber_length)]
        for viz_type in self.viz_types[time_step_index]:
            if(viz_type == 1000):
                self.subpoints[time_step_index].append(blank_value)
            elif(viz_type == 1001):
                control_points = self.fiber_points[time_step_index].pop(0)
                self.subpoints[time_step_index].append(control_points)

    def get_all_ingredient_names(self, recipe_in):
        self.recipe_name = recipe_in["recipe"]["name"]
        container = recipe_in["cytoplasme"]
        ingredients = container["ingredients"]
        self.unique_ingredient_names = list(ingredients)


###############################################################################


def main():
    converter = ConvertToSimularium()
    dbg = converter.debug
    try:
        recipe_in = "/Users/meganriel-mehan/dev/allen-inst/cellPack/cellpack/cellpack/test-recipes/NM_Analysis_FigureC1.json"
        results_in = converter.input_directory + converter.packing_result_file_name
        recipe_data = json.load(open(recipe_in, "r"), object_pairs_hook=OrderedDict)
        converter.get_all_ingredient_names(recipe_data)
        converter.get_bounding_box(recipe_data)
        packing_data = json.load(open(results_in, "r"))
        box_size = converter.box_size
        converter.get_positions_per_ingredient(packing_data, 0)
        converter.fill_in_empty_fiber_data(0)
        print(converter.n_subpoints)
        print(converter.subpoints)
        print(len(converter.subpoints[0]))
        converted_data = CustomData(
            # meta_data=MetaData(
            #     box_size=np.array([converter.box_size, converter.box_size, converter.box_size]),
            #     camera_defaults=CameraData(
            #         position=np.array([10.0, 0.0, 200.0]),
            #         look_at_position=np.array([10.0, 0.0, 0.0]),
            #         fov_degrees=60.0,
            #     ),
            # ),
            box_size=np.array(box_size),

            agent_data=AgentData(
                times=converter.timestep * np.array(list(range(converter.total_steps))),
                n_agents=np.array(converter.n_agents),
                viz_types=np.array(converter.viz_types),
                unique_ids=np.array(converter.unique_ids),
                types=np.array(converter.type_names),
                positions=np.array(converter.positions),
                radii=np.array(converter.radii),
                subpoints=np.array(converter.subpoints),
                n_subpoints=np.array(converter.n_subpoints)

            )
            # time_units=UnitData("ns"),  # nanoseconds
            # spatial_units=UnitData("nm"),  # nanometers
        )
        CustomConverter(converted_data).write_JSON(converter.output + converter.packing_result_file_name)

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

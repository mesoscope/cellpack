
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
    DEFAULT_RECIPE_IN = 
    DEFAULT_PACKING_RESULT = "results_seed_0.json"
    DEFAULT_OUTPUT_DIRECTORY = "/Users/meganriel-mehan/Dropbox/cellPack/"

    def __init__(self, total_steps=1):
        # Arguments that could be passed in through the command line
        self.input_directory = self.DEFAULT_INPUT_DIRECTORY
        self.packing_result_file_name = self.DEFAULT_PACKING_RESULT
        self.output = self.DEFAULT_OUTPUT_DIRECTORY
        self.__parse()
        # simularium parameters
        self.total_steps = total_steps
        self.timestep = 1
        self.box_size = 100
        self.n_agents = [0 for x in range(total_steps)]
        self.points_per_fiber = 0
        self.type_names = [[] for x in range(total_steps)]
        self.positions = [[] for x in range(total_steps)]
        self.viz_types = [[] for x in range(total_steps)]
        self.unique_ids = [[] for x in range(total_steps)]
        self.radii = [[] for x in range(total_steps)]

        self.bounds = [[0.0, 0.0, 0.0], [-1.0, -1.0, -1.0]]
        self.main_scale = 1.0 / 100.0  # could be 1/200.0 like flex
        self.pnames_fiber = []
        self.pnames_fiber_nodes = []
        self.pnames = []
        self.n_subpoints = []
        self.subpoints = []

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

    def get_positions_per_ingredient(self, results_data_in, time_step_index): 
        container = results_data_in["cytoplasme"]
        ingredients = container["ingredients"]
        for i in range(len(self.unique_ingredient_names)):
            # print(ingredients[ingredient_name])
            ingredient_name = self.unique_ingredient_names[i]
            data = ingredients[ingredient_name]
            if (len(data['results']) > 0):
                for j in range(len(data['results'])):
                    id = (i * 10 * (i + 1)) + j
                    print(i, j, id)
                    self.positions[time_step_index].append(data['results'][j][0])
                    self.viz_types[time_step_index].append(1000)
                    self.n_agents[time_step_index] = self.n_agents[time_step_index] + 1
                    self.type_names[time_step_index].append(ingredient_name)
                    self.unique_ids[time_step_index].append(id)
                    self.radii[time_step_index].append(data['radii'][0]['radii'][0])

    def get_all_ingredient_names(self, recipe_in):
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
        packing_data = json.load(open(results_in, "r"))
        box_size = converter.box_size
        converter.get_positions_per_ingredient(packing_data, 0)
        converted_data = CustomData(
            # meta_data=MetaData(
            #     box_size=np.array([converter.box_size, converter.box_size, converter.box_size]),
            #     camera_defaults=CameraData(
            #         position=np.array([10.0, 0.0, 200.0]),
            #         look_at_position=np.array([10.0, 0.0, 0.0]),
            #         fov_degrees=60.0,
            #     ),
            # ),
            box_size=np.array([box_size, box_size, box_size]),

            agent_data=AgentData(
                times=converter.timestep * np.array(list(range(converter.total_steps))),
                n_agents=np.array(converter.n_agents),
                viz_types=np.array(converter.viz_types),
                unique_ids=np.array(converter.unique_ids),
                types=np.array(converter.type_names),
                positions=np.array(converter.positions),
                radii=np.array(converter.radii),
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

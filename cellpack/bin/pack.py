from enum import Enum
import fire
from os import path
import logging
import logging.config
import time

from cellpack import autopack
from cellpack.autopack import upy
from cellpack.autopack.Analysis import Analysis
from cellpack.autopack.Environment import Environment

from cellpack.autopack.loaders.config_loader import ConfigLoader
from cellpack.autopack.loaders.recipe_loader import RecipeLoader
from cellpack.autopack.loaders.analysis_config_loader import AnalysisConfigLoader
from cellpack.autopack.FirebaseHandler import FirebaseHandler
from cellpack.autopack.DBRecipeHandler import DBHandler

###############################################################################
log_file_path = path.abspath(path.join(__file__, "../../logging.conf"))
logging.config.fileConfig(log_file_path, disable_existing_loggers=False)
log = logging.getLogger()
###############################################################################


class DATABASE_IDS(Enum):
    FIREBASE = "firebase"
    GITHUB = "github"


def pack(
    recipe, config_path=None, analysis_config_path=None, db_id=DATABASE_IDS.FIREBASE
):
    """
    Initializes an autopack packing from the command line
    :param recipe: string argument, path to recipe
    :param config_path: string argument, path to packing config file
    :param analysis_config_path: string argument, path to analysis config file
    :param db_id: DATABASE_IDS enum string argument, database id

    :return: void
    """
    if db_id == DATABASE_IDS.FIREBASE:
        db = FirebaseHandler()
        db_handler = DBHandler(db)
    packing_config_data = ConfigLoader(config_path).config
    recipe_data = RecipeLoader(
        recipe, db_handler, packing_config_data["save_converted_recipe"]
    ).recipe_data
    analysis_config_data = {}
    if analysis_config_path is not None:
        analysis_config_data = AnalysisConfigLoader(analysis_config_path).config

    helper_class = upy.getHelperClass()
    helper = helper_class(vi="nogui")
    autopack.helper = helper
    env = Environment(config=packing_config_data, recipe=recipe_data)
    env.helper = helper

    afviewer = None
    if packing_config_data["save_analyze_result"]:
        analyze = Analysis(
            env=env,
            viewer=afviewer,
            result_file=None,
        )
        log.info(f"saving to {env.out_folder}")
        analyze.doloop(
            packing_config_data["number_of_packings"],
            env.boundingBox,
            plot_figures=packing_config_data.get("save_plot_figures", True),
            show_grid=packing_config_data["show_grid_plot"],
            seed_list=packing_config_data["randomness_seed"],
            config_name=packing_config_data["name"],
            recipe_version=recipe_data["version"],
            image_export_options=packing_config_data.get("image_export_options"),
            parallel=packing_config_data.get("parallel", False),
        )
        if analysis_config_path is not None:
            analyze.run_analysis_workflow(
                analysis_config=analysis_config_data,
                recipe_data=recipe_data,
            )
    else:
        env.buildGrid(rebuild=True)
        env.pack_grid(verbose=0, usePP=False)


def main():
    start_time = time.time()
    fire.Fire(pack)
    execution_time = time.time() - start_time
    print(f"The workflow took {execution_time:.2f} s to run.")


if __name__ == "__main__":
    main()

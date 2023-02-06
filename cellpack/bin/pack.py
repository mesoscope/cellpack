import fire
from os import path
import logging
import logging.config
import time

from cellpack import autopack
from cellpack.autopack import upy
from cellpack.autopack.Analysis import AnalyseAP
from cellpack.autopack.Environment import Environment

from cellpack.autopack.loaders.config_loader import ConfigLoader
from cellpack.autopack.loaders.recipe_loader import RecipeLoader

###############################################################################
log_file_path = path.abspath(path.join(__file__, "../../logging.conf"))
logging.config.fileConfig(log_file_path, disable_existing_loggers=False)
log = logging.getLogger()
###############################################################################


def pack(recipe, config=None):
    """
    Initializes an autopack packing from the command line
    :param recipe: string argument, path to recipe
    :param config: string argument, path to config file

    :return: void
    """
    config_data = ConfigLoader(config).config
    recipe_data = RecipeLoader(recipe, config_data["save_converted_recipe"]).recipe_data

    helper_class = upy.getHelperClass()
    helper = helper_class(vi="nogui")
    autopack.helper = helper

    env = Environment(config=config_data, recipe=recipe_data)
    env.helper = helper

    afviewer = None
    if config_data["save_analyze_result"]:
        analyze = AnalyseAP(env=env, viewer=afviewer, result_file=None)
        log.info(f"saving to {env.out_folder}")
        analyze.doloop(
            config_data["num_trials"],
            env.boundingBox,
            plot_figures=config_data["save_plot_figures"],
            show_grid=config_data["show_grid_plot"],
            seed_list=config_data["randomness_seed"],
            config_name=config_data["name"],
            recipe_version=recipe_data["version"],
        )
    else:
        env.buildGrid(rebuild=True)
        env.pack_grid(verbose=0, usePP=False)


def main():
    start_time = time.time()
    fire.Fire(pack)
    execution_time = time.time() - start_time
    print("The workflow took " + str(execution_time) + "s to run.")


if __name__ == "__main__":
    main()

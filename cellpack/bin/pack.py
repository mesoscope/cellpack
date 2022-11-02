import fire
from os import path
import logging
import logging.config

from cellpack import autopack
from cellpack.autopack import upy
from cellpack.autopack.Analysis import AnalyseAP
from cellpack.autopack.Environment import Environment

from cellpack.autopack.loaders.config_loader import ConfigLoader
from cellpack.autopack.loaders.recipe_loader import RecipeLoader

log = logging.getLogger(__name__)

def pack(recipe, config):
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
        output = env.out_folder
        analyze = AnalyseAP(env=env, viewer=afviewer, result_file=None)
        log.info(f"saving to {output}")
        analyze.doloop(
            1,
            env.boundingBox,
            output,
            plot=True,
            show_grid=config_data["show_grid_plot"],
        )
    else:
        env.buildGrid(rebuild=True)
        env.pack_grid(verbose=0, usePP=False)


def main():
    fire.Fire(pack)


if __name__ == "__main__":
    main()

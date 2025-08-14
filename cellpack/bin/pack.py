import fire
from pathlib import Path
import logging
import logging.config
import time
import sys

from cellpack import autopack
from cellpack.autopack import upy
from cellpack.autopack.Analysis import Analysis
from cellpack.autopack.Environment import Environment

from cellpack.autopack.loaders.config_loader import ConfigLoader
from cellpack.autopack.loaders.recipe_loader import RecipeLoader
from cellpack.autopack.loaders.analysis_config_loader import AnalysisConfigLoader
from cellpack.autopack.validation.recipe_validator import RecipeValidator

from pydantic import ValidationError
import json

###############################################################################
log_file_path = Path(__file__).parent.parent / "logging.conf"
logging.config.fileConfig(log_file_path, disable_existing_loggers=False)
log = logging.getLogger()
###############################################################################


def pack(
    recipe, config_path=None, analysis_config_path=None, docker=False, validate=True
):
    """
    Initializes an autopack packing from the command line
    :param recipe: string argument, path to recipe
    :param config_path: string argument, path to packing config file
    :param analysis_config_path: string argument, path to analysis config file
    :param docker: boolean argument, are we using docker
    :param validate: boolean argument, validate recipe before packing

    :return: void
    """
    packing_config_data = ConfigLoader(config_path, docker).config

    # validate recipe before packing
    if validate:
        try:
            with open(recipe, "r") as f:
                raw_recipe_data = json.load(f)
            RecipeValidator.validate_recipe(raw_recipe_data)
            log.info("Recipe validation passed!")
        except ValidationError as e:
            log.error(f"Recipe validation failed: {e}")
            sys.exit(1)

    recipe_data = RecipeLoader(
        recipe, packing_config_data["save_converted_recipe"], docker
    ).recipe_data
    analysis_config_data = {}
    if analysis_config_path is not None:
        analysis_config_data = AnalysisConfigLoader(analysis_config_path).config

    helper_class = upy.getHelperClass()
    helper = helper_class(vi="nogui")
    autopack.helper = helper
    env = Environment(config=packing_config_data, recipe=recipe_data)
    env.helper = helper

    if (
        packing_config_data["save_analyze_result"]
        or packing_config_data["number_of_packings"] > 1
    ):
        analyze = Analysis(
            env=env,
        )
        log.info(f"saving to {env.out_folder}")

        analyze.doloop(
            recipe_data,
            packing_config_data,
            env.boundingBox,
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

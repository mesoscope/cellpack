import logging
import logging.config
import time
from pathlib import Path

import fire

from cellpack import autopack
from cellpack.autopack import upy
from cellpack.autopack.Analysis import Analysis
from cellpack.autopack.DBRecipeHandler import DBUploader
from cellpack.autopack.Environment import Environment
from cellpack.autopack.interface_objects.database_ids import DATABASE_IDS
from cellpack.autopack.IOutils import format_time
from cellpack.autopack.loaders.analysis_config_loader import AnalysisConfigLoader
from cellpack.autopack.loaders.config_loader import ConfigLoader
from cellpack.autopack.loaders.recipe_loader import RecipeLoader

###############################################################################
log_file_path = Path(__file__).parent.parent / "logging.conf"
logging.config.fileConfig(log_file_path, disable_existing_loggers=False)
log = logging.getLogger()
###############################################################################


def pack(
    recipe,
    config_path=None,
    analysis_config_path=None,
    docker=False,
    hash=None,
):
    """
    Initializes an autopack packing from the command line
    :param recipe: string argument, path to recipe file, or a dictionary representing a recipe
    :param config_path: string argument, path to packing config file
    :param analysis_config_path: string argument, path to analysis config file
    :param docker: boolean argument, are we using docker
    :param hash: string argument, dedup hash identifier for tracking/caching results

    :return: void
    """
    packing_config_data = ConfigLoader(config_path, docker).config

    if isinstance(recipe, dict):
        # Load recipe from JSON dictionary
        recipe_loader = RecipeLoader.from_json(recipe, use_docker=docker)
    else:
        # Load recipe from file path
        recipe_loader = RecipeLoader(
            recipe, packing_config_data["save_converted_recipe"], docker
        )
    recipe_data = recipe_loader.recipe_data
    analysis_config_data = {}
    if analysis_config_path is not None:
        analysis_config_data = AnalysisConfigLoader(analysis_config_path).config

    helper_class = upy.getHelperClass()
    helper = helper_class(vi="nogui")
    autopack.helper = helper
    env = Environment(config=packing_config_data, recipe=recipe_data)
    env.helper = helper
    env.dedup_hash = hash

    log.info("Packing recipe: %s", recipe_data["name"])
    log.info("Outputs will be saved to %s", env.out_folder)

    if (
        packing_config_data["save_analyze_result"]
        or packing_config_data["number_of_packings"] > 1
    ):
        analyze = Analysis(
            env=env,
        )

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

    if docker and hash:
        handler = DATABASE_IDS.handlers().get(DATABASE_IDS.AWS)
        # temporarily using demo bucket before permissions are granted
        initialized_handler = handler(
            bucket_name="cellpack-demo",
            sub_folder_name="runs",
            region_name="us-west-2",
        )
        uploader = DBUploader(db_handler=initialized_handler)
        uploader.upload_packing_results_workflow(
            source_folder=env.out_folder,
            recipe_name=recipe_data["name"],
            dedup_hash=hash,
            config_data=packing_config_data,
            recipe_data=recipe_loader.serializable_recipe_data,
        )


def main():
    start_time = time.time()
    fire.Fire(pack)
    log.info(f"Workflow completed in {format_time(time.time() - start_time)}")


if __name__ == "__main__":
    main()

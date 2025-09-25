import logging
import logging.config
import os
import time
from pathlib import Path

import fire

from cellpack import autopack
from cellpack.autopack import upy
from cellpack.autopack.Analysis import Analysis
from cellpack.autopack.DBRecipeHandler import DBUploader
from cellpack.autopack.Environment import Environment
from cellpack.autopack.IOutils import format_time
from cellpack.autopack.interface_objects.database_ids import DATABASE_IDS
from cellpack.autopack.loaders.analysis_config_loader import AnalysisConfigLoader
from cellpack.autopack.loaders.config_loader import ConfigLoader
from cellpack.autopack.loaders.recipe_loader import RecipeLoader
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
            formatted_error = RecipeValidator.format_validation_error(e)
            log.error(formatted_error)
            return

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

    if docker:
        job_id = os.environ.get("AWS_BATCH_JOB_ID", None)
        if job_id:
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
                job_id=job_id,
            )


def main():
    start_time = time.time()
    fire.Fire(pack)
    log.info(f"Workflow completed in {format_time(time.time() - start_time)}")


if __name__ == "__main__":
    main()

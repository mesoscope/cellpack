import logging
import logging.config
import time
import uuid
import shutil
from pathlib import Path

import fire

from cellpack import autopack
from cellpack.autopack import upy
from cellpack.autopack.Analysis import Analysis
from cellpack.autopack.DBRecipeHandler import DBUploader
from cellpack.autopack.Environment import Environment
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
    upload_to_s3=False,
):
    """
    Initializes an autopack packing from the command line
    :param recipe: string argument, path to recipe
    :param config_path: string argument, path to packing config file
    :param analysis_config_path: string argument, path to analysis config file
    :param docker: boolean argument, are we using docker
    :param upload_to_s3: boolean argument, whether to upload current run's outputs to S3

    :return: void
    """
    packing_config_data = ConfigLoader(config_path, docker).config
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

    # prepare S3 upload folder
    s3_upload_folder = None
    if upload_to_s3:
        # create unique run folder for S3 upload only, run_id should be job id later on
        run_id = str(uuid.uuid4())[:8]
        parent_folder = Path(env.out_folder).parent
        unique_folder_name = f"{Path(env.out_folder).name}_run_{run_id}"
        s3_upload_folder = parent_folder / unique_folder_name
        log.debug(f"S3 upload enabled, results copied to: {s3_upload_folder}")
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

    if upload_to_s3:
        # copy results from original folder to unique S3 upload folder
        if Path(env.out_folder).exists():
            s3_upload_folder.mkdir(parents=True, exist_ok=True)
            shutil.copytree(env.out_folder, s3_upload_folder, dirs_exist_ok=True)

        upload_packing_results_to_s3(s3_upload_folder, recipe_data["name"], run_id)


def upload_packing_results_to_s3(output_folder, recipe_name, run_id):
    """
    Upload packing results to S3 using the DBUploader architecture
    :param output_folder: Path to the output folder containing results
    :param recipe_name: Name of the recipe being packed
    """
    try:
        output_path = Path(output_folder)
        if not output_path.exists():
            log.error(f"Output folder does not exist: {output_folder}")
            return

        uploader = DBUploader(db_handler=None)
        uploader.upload_outputs_to_s3(
            output_folder=output_folder, recipe_name=recipe_name, run_id=run_id
        )

    except Exception as e:
        log.error(f"S3 upload error: {e}")


def main():
    start_time = time.time()
    fire.Fire(pack)
    log.info(f"Workflow completed in {format_time(time.time() - start_time)}")


if __name__ == "__main__":
    main()

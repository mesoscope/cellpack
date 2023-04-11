"""
Run analysis code
"""

# Standard library
import os
from os import path
import logging
import logging.config

# Third party
import fire
from time import time

# Relative
from cellpack.autopack.Analysis import Analysis
from cellpack.autopack.loaders.analysis_config_loader import (
    AnalysisConfigLoader,
)
from cellpack.autopack.loaders.recipe_loader import RecipeLoader

###############################################################################
log_file_path = path.abspath(path.join(__file__, "../../logging.conf"))
logging.config.fileConfig(log_file_path, disable_existing_loggers=False)
log = logging.getLogger()
###############################################################################


def analyze(
    analysis_config_path,
    recipe_path,
):
    """
    Runs specified analyses based on the config
    :param analysis_config_path: string argument,
    path to analysis config file

    :return: void
    """
    t1 = time()
    analysis_config = AnalysisConfigLoader(analysis_config_path).config
    recipe_data = RecipeLoader(recipe_path, False).recipe_data
    os.makedirs(analysis_config["output_path"], exist_ok=True)

    for packing_result_path in analysis_config["packing_result_path_list"]:
        log.info(f"Input path: {packing_result_path}\n")
        analysis = Analysis(
            packing_results_path=packing_result_path,
            output_path=analysis_config["output_path"],
        )
        analysis.run_analysis_workflow(
            analysis_config=analysis_config,
            recipe_data=recipe_data,
        )
    t2 = time()
    print(f"time to run analysis: {t2 - t1}")


# Run directly from command line
def main():
    fire.Fire(analyze)


if __name__ == "__main__":
    main()

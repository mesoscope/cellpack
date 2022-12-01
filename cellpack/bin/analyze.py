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
from cellpack.autopack.Analysis import AnalyseAP
from cellpack.autopack.loaders.analysis_config_loader import AnalysisConfigLoader

###############################################################################
log_file_path = path.join(path.dirname(path.abspath(__file__)), "../../logging.conf")
logging.config.fileConfig(log_file_path, disable_existing_loggers=False)
log = logging.getLogger()
###############################################################################


def analyze(
    analysis_config_path,
):
    """
    Runs specified analyses based on the config
    :param analysis_config_path: string argument,
    path to analysis config file

    :return: void
    """
    t1 = time()
    analysis_config = AnalysisConfigLoader(analysis_config_path).config
    os.makedirs(analysis_config["output_path"], exist_ok=True)
    log.info(f"Input path: {analysis_config['input_path']}\n")

    analysis = AnalyseAP(
        input_path=analysis_config["input_path"],
        output_path=analysis_config["output_path"],
    )
    analysis.run_analysis_workflow(
        ingr_key=analysis_config["ingredient_key"],
        run_similarity_analysis=analysis_config["run_similarity_analysis"],
        get_parametrized_representation=analysis_config[
            "get_parametrized_representation"
        ],
        mesh_paths=analysis_config["mesh_paths"],
        save_plots=analysis_config["save_plots"],
        get_correlations=analysis_config["get_correlations"],
        max_plots_to_save=analysis_config["max_plots_to_save"],
    )
    t2 = time()
    print(f"time to run analysis: {t2 - t1}")


# Run directly from command line
def main():
    fire.Fire(analyze)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
import os
import json


class AnalysisConfigLoader(object):
    default_values = {
        "input_folder": "out/analyze/test_analyze/jitter/",
        "output_folder": "out/analyze/test_analyze/jitter/",
        "ingredient_key": "membrane_interior_peroxisome",
        "mesh_paths": {"inner": "data/mean-nuc.obj", "outer": "data/mean-membrane.obj"},
        "version": "1.0",
        "run_similarity_analysis": False,
        "get_parametrized_representation": False,
        "save_plots": False,
        "get_correlations": False,
    }

    def __init__(self, input_file_path):
        _, file_extension = os.path.splitext(input_file_path)
        self.latest_version = 1.0
        self.file_path = input_file_path
        self.file_extension = file_extension
        self.config = self._read()

    @staticmethod
    def _migrate_version(config):
        return config

    def _read(self):
        """
        Read in a Json Config file.
        """
        new_values = json.load(open(self.file_path, "r"))
        config = AnalysisConfigLoader.default_values.copy()
        config.update(new_values)
        if config["version"] != self.latest_version:
            config = AnalysisConfigLoader._migrate_version(config)
        return config

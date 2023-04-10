# -*- coding: utf-8 -*-
import os
import json


class AnalysisConfigLoader(object):
    default_values = {
        "version": "1.0.0",
        "format_version": "1.1",
        "packing_result_path": "cellpack/tests/outputs/test_partner_packing/spheresSST",
        "create_report": {
            "run_distance_analysis": True,
            "report_output_path": "cellpack/tests/outputs/test_partner_packing",
            "output_image_location": "./spheresSST/figures",
        },
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

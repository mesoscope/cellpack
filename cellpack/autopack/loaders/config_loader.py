# -*- coding: utf-8 -*-
import os

import json
from json import encoder

from cellpack.autopack.interface_objects.meta_enum import MetaEnum

encoder.FLOAT_REPR = lambda o: format(o, ".8g")


class Place_Methods(MetaEnum):
    JITTER = "jitter"
    SPHERES_SST = "spheresSST"
    PANDA_BULLET = "pandaBullet"
    PANDA_BULLET_RELAX = "pandaBulletRelax"


class Inner_Grid_Methods(MetaEnum):
    # Working inner grid methods
    RAYTRACE = "raytrace"
    SCANLINE = "scanline"
    TRIMESH = "trimesh"


class ConfigLoader(object):
    default_values = {
        "format": "simularium",
        "load_from_grid_file": False,
        "inner_grid_method": "trimesh",
        "live_packing": False,
        "num_trials": 1,
        "name": "default",
        "ordered_packing": False,
        "out": "out/",
        "overwrite_place_method": False,
        "place_method": "jitter",
        "randomness_seed": None,
        "save_analyze_result": False,
        "save_converted_recipe": False,
        "show_grid_plot": False,
        "show_sphere_trees": False,
        "spacing": None,
        "use_periodicity": False,
        "version": 1.0,
    }

    def __init__(self, input_file_path=None):
        if input_file_path is not None:
            _, file_extension = os.path.splitext(input_file_path)
            self.file_path = input_file_path
            self.file_extension = file_extension
        else:
            self.file_path = None
        self.latest_version = 1.0
        self.config = self._read()

    @staticmethod
    def _test_types(config):
        if not Place_Methods.is_member(config["place_method"]):
            raise TypeError(
                (
                    f"place_method must be one of {Place_Methods.values()}, not {config['place_method']}"
                )
            )
        if not Inner_Grid_Methods.is_member(config["inner_grid_method"]):
            raise TypeError(
                (
                    f"inner_grid_method must be one of {Inner_Grid_Methods.values()}, not {config['inner_grid_method']}"
                )
            )
        bools = [
            "live_packing",
            "ordered_packing",
            "overwrite_place_method",
            "save_analyze_result",
            "show_grid_plot",
            "use_periodicity",
            "show_sphere_trees",
        ]
        for should_be_bool in bools:
            if not isinstance(config[should_be_bool], bool):
                raise TypeError(
                    (
                        f"{should_be_bool} should be a boolean, not {config[should_be_bool]}"
                    )
                )

    @staticmethod
    def _migrate_version(config):
        return config

    def _read(self):
        """
        Read in a Json Config file.
        """
        if self.file_path is None:
            config = ConfigLoader.default_values.copy()
        else:
            new_values = json.load(open(self.file_path, "r"))
            config = ConfigLoader.default_values.copy()
            config.update(new_values)
        if config["version"] != self.latest_version:
            config = ConfigLoader._migrate_version(config)
        ConfigLoader._test_types(config)
        return config

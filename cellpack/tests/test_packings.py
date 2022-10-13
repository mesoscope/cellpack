#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Docs: https://docs.pytest.org/en/latest/example/simple.html
      https://docs.pytest.org/en/latest/plugins.html#requiring-loading-plugins-in-a-test-module-or-conftest-file
"""

import json
from cellpack import autopack
from cellpack.autopack import upy
from cellpack.autopack.Analysis import AnalyseAP

from cellpack.autopack.Environment import Environment
from cellpack.autopack.loaders.config_loader import ConfigLoader
from cellpack.autopack.loaders.recipe_loader import RecipeLoader


def test_packing_bias():
    all_pos_path = "cellpack/tests/data/all_pos.json"
    with open(all_pos_path, "r") as j:
        all_pos = json.loads(j.read())

    config_data = ConfigLoader("cellpack/tests/packing-configs/test_config.json").config
    recipe_data = RecipeLoader("cellpack/tests/recipes/test_spheres.json").recipe_data

    helper_class = upy.getHelperClass()
    helper = helper_class(vi="nogui")
    autopack.helper = helper

    env = Environment(config=config_data, recipe=recipe_data)
    env.helper = helper
    output = env.out_folder
    analyze = AnalyseAP(env=env, viewer=None, result_file=None)
    analyze.doloop(
        config_data["num_trials"],
        env.boundingBox,
        output,
        plot=True,
        show_grid=config_data["show_grid_plot"],
        seeds_i=config_data["rng_seed"],
    )
    # string indices because the data came from a json file
    assert all_pos["0"] == analyze.all_pos_dict[0]

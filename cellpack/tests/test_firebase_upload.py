#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Docs: https://docs.pytest.org/en/latest/example/simple.html
      https://docs.pytest.org/en/latest/plugins.html#requiring-loading-plugins-in-a-test-module-or-conftest-file
"""
import pytest
from cellpack.autopack.DBRecipeHandler import DBRecipeHandler
from cellpack.autopack.FirebaseHandler import FirebaseHandler
from cellpack.autopack.loaders.recipe_loader import RecipeLoader

@pytest.mark.parametrize(
    "input_data, converted_data",
    [(
        {
            "bounding_box": [[0,0,0], [1000, 1000, 1]],
            "positions": [[(0.0, 0.0, 0.0)], [(0.0, 50.0, 0.0), (43.26, -25.07, 0.0)]],
            "max_jitter": [1,1,0]
        },
        {
            "bounding_box": {"0": [0,0,0], "1": [1000, 1000,1]},
            "positions": {"0": {"0": (0.0, 0.0, 0.0)}, "1": {"0": (0.0, 50.0, 0.0), "1": (43.26, -25.07, 0.0)}},
            "max_jitter": [1,1,0]
        },
    )
    # TODO: add test case for representations object 
    ]
)

def test_flatten_and_unpack_data(input_data, converted_data):
    new_data = DBRecipeHandler.flatten_and_unpack(input_data)
    assert new_data == converted_data

@pytest.mark.parametrize(
    "position_data_db, converted_position_data",
    [(
        {
            "positions": {'0': {'0': [0.0, 0.0, 0.0]}, '1': {'0': [0.0, 50.0, 0.0], '1': [43.26, -25.07, 0.0]}}
        },
        {
            "positions": {'0': {'0': (0.0, 0.0, 0.0)}, '1': {'0': (0.0, 50.0, 0.0), '1': (43.26, -25.07, 0.0)}}
        },
    )]
)

def test_convert_position_in_representation(position_data_db, converted_position_data):
    convert_position_to_tuple = DBRecipeHandler.convert_positions_in_representation(position_data_db)
    assert convert_position_to_tuple == converted_position_data

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
NOTE: All test file names must have one of the two forms.
- `test_<XYY>.py`
- '<XYZ>_test.py'

Docs: https://docs.pytest.org/en/latest/
      https://docs.pytest.org/en/latest/goodpractices.html#conventions-for-python-test-discovery
"""

from unittest.mock import MagicMock
import pytest
from cellpack.autopack.Environment import Environment

test_config = {
    "dimension": 3,
    "format": "simularium",
    "inner_grid_method": "raytrace",
    "live_packing": False,
    "load_from_grid_file": False,
    "name": "test",
    "ordered_packing": False,
    "out": "out/",
    "overwrite_place_method": False,
    "place_method": "jitter",
    "save_analyze_result": True,
    "show_grid_plot": False,
    "show_sphere_trees": False,
    "show_sphere_trees": False,
    "spacing": None,
    "use_periodicity": False,
}


def test_is_two_d():
    # if one of the edges of the bounding box is smaller than the
    # grid spacing, it's considered 2D
    test_recipe = {
        "bounding_box": [[0, 0, 0], [100, 10, 100]],
        "name": "test",
        "objects": {"sphere_25": {"radius": 25, "type": "single_sphere"}},
        "composition": {
            "space": {"regions": {"interior": ["A"]}},
            "A": {"object": "sphere_25", "count": 1},
        },
    }

    env = Environment(config=test_config, recipe=test_recipe)
    mock = MagicMock(gridSpacing=10)
    env.grid = mock

    assert env.is_two_d()

    test_recipe["bounding_box"] = [[0, 0, 0], [40, 40, 40]]

    env = Environment(config=test_config, recipe=test_recipe)
    mock = MagicMock(gridSpacing=10)
    env.grid = mock

    assert not env.is_two_d()


@pytest.mark.parametrize(
    "ingredient_info, output",
    [
        (
            {
                "name": "test",
                "type": "single_sphere",
                "count": 1,
                "count_options": {"distribution": "uniform", "min": 1, "max": 1},
            },
            {
                "name": "test",
                "type": "single_sphere",
                "count": 1,
                "count_options": {"distribution": "uniform", "min": 1, "max": 1},
            },
        ),
        (
            {
                "name": "test",
                "type": "single_sphere",
            },
            "Ingredient info must contain a count",
        ),
        (
            {
                "name": "test",
                "type": "single_sphere",
                "count": -1,
            },
            "Ingredient count must be greater than or equal to 0",
        ),
        (
            {
                "name": "test",
                "type": "single_sphere",
                "count": 1,
                "count_options": {},
            },
            "Ingredient count options must contain a distribution",
        ),
        (
            {
                "name": "test",
                "type": "single_sphere",
                "count": 1,
                "count_options": {
                    "distribution": "invalid_distribution",
                },
            },
            "invalid_distribution is not a valid count distribution",
        ),
        (
            {
                "name": "test",
                "type": "single_sphere",
                "count": 1,
                "count_options": {
                    "distribution": "uniform",
                },
            },
            "Missing option 'min' for uniform distribution",
        ),
    ],
)
def test_validate_ingredient_info(ingredient_info, output):
    try:
        validated_info = Environment.validate_ingredient_info(ingredient_info)
        assert validated_info == output
    except Exception as e:
        assert str(e) == output

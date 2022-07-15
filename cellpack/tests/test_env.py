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
from cellpack.autopack.Environment import Environment
test_config = {
    "bounding_box": [
        [
            0,
            0,
            0
        ],
        [
            100,
            100,
            100
        ]
    ],
    "dimension": 3,
    "format": "simularium",
    "inner_grid_method": "raytrace",
    "live_packing": False,
    "ordered_packing": False,
    "out": "out/",
    "overwrite_place_method": False,
    "place_method": "jitter",
    "save_analyze_result": True,
    "show_grid_plot": False,
    "spacing": None,
    "use_periodicity": False
}


def test_is_two_d():
    # if one of the edges of the bounding box is smaller than the
    # grid spacing, it's considered 2D
    test_config["bounding_box"] = [[0, 0, 0], [100, 10, 100]]

    env = Environment(name="test", config=test_config)
    mock = MagicMock(gridSpacing=10)
    env.grid = mock

    assert env.is_two_d()

    test_config["bounding_box"] = [[0, 0, 0], [40, 40, 40]]

    env = Environment(name="test", config=test_config)
    mock = MagicMock(gridSpacing=10)
    env.grid = mock

    assert not env.is_two_d()

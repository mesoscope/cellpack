#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Docs: https://docs.pytest.org/en/latest/example/simple.html
    https://docs.pytest.org/en/latest/plugins.html#requiring-loading-plugins-in-a-test-module-or-conftest-file
"""
import pytest
from cellpack.autopack.interface_objects import GradientData


@pytest.mark.parametrize(
    "input, expected_options",
    [
        (
            (
                {},
                "gradient_name",
            ),
            {
                "mode": "X",
                "weight_mode": "linear",
                "pick_mode": "linear",
                "description": "Linear gradient in the X direction",
                "reversed": False,
                "name": "gradient_name",
                "mode_settings": {
                    "direction": [1, 0, 0],
                },
            },
        ),
        (
            (
                {
                    "mode": "radial",
                    "weight_mode": "square",
                    "description": "Square gradient in the radial direction",
                    "mode_settings": {
                        "center": [0, 0, 0],
                        "radius": 1,
                    },
                },
                "gradient_name",
            ),
            {
                "mode": "radial",
                "weight_mode": "square",
                "pick_mode": "linear",
                "description": "Square gradient in the radial direction",
                "reversed": False,
                "name": "gradient_name",
                "mode_settings": {
                    "center": [0, 0, 0],
                    "radius": 1,
                    "direction": [1, 0, 0],
                },
            },
        ),
        (
            (
                {
                    "mode": "Y",
                    "weight_mode": "cube",
                    "description": "Cubic gradient in the Y direction",
                    "reversed": True,
                },
                "gradient_name",
            ),
            {
                "mode": "Y",
                "weight_mode": "cube",
                "pick_mode": "linear",
                "description": "Cubic gradient in the Y direction",
                "reversed": True,
                "name": "gradient_name",
                "mode_settings": {"direction": [0, -1, 0]},
            },
        ),
    ],
)
def test_gradient_data(input, expected_options):
    assert GradientData(*input).data == expected_options


@pytest.mark.parametrize(
    "input, error_string",
    [
        (
            (
                {"mode": "wrong_mode"},
                "gradient_name",
            ),
            "Invalid gradient mode: wrong_mode",
        ),
        (
            (
                {"mode": "surface", "mode_settings": {"wrong_setting": True}},
                "gradient_name",
            ),
            "Missing required mode setting object for surface",
        ),
    ],
)
def test_invalid_data(input, error_string):
    try:
        GradientData(*input).data
    except ValueError as error:
        assert format(error) == error_string

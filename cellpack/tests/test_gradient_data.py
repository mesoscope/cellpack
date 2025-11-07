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
                "invert": None,
                "name": "gradient_name",
                "mode_settings": {
                    "direction": [1, 0, 0],
                },
                "weight_mode_settings": {},
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
                "invert": None,
                "name": "gradient_name",
                "mode_settings": {
                    "center": [0, 0, 0],
                    "radius": 1,
                },
                "weight_mode_settings": {},
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
                "invert": None,
                "name": "gradient_name",
                "mode_settings": {"direction": [0, -1, 0]},
                "weight_mode_settings": {},
            },
        ),
        (
            (
                {
                    "mode": "surface",
                    "weight_mode": "power",
                    "description": "power law gradient from surface",
                    "mode_settings": {
                        "object": "object_name",
                    },
                    "weight_mode_settings": {
                        "power": 2,
                    },
                },
                "gradient_name",
            ),
            {
                "mode": "surface",
                "weight_mode": "power",
                "description": "power law gradient from surface",
                "pick_mode": "linear",
                "reversed": False,
                "invert": None,
                "mode_settings": {
                    "object": "object_name",
                },
                "weight_mode_settings": {
                    "power": 2,
                },
                "name": "gradient_name",
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
        (
            (
                {
                    "mode": "surface",
                    "weight_mode": "power",
                    "mode_settings": {"object": "object_name"},
                },
                "gradient_name",
            ),
            "Missing weight mode settings for power",
        ),
    ],
)
def test_invalid_data(input, error_string):
    try:
        GradientData(*input).data
    except ValueError as error:
        assert format(error) == error_string

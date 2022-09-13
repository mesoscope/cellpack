#!/usr/bin/env python
# -*- coding: utf-8 -*-

from math import pi
import pytest

"""
Docs: https://docs.pytest.org/en/latest/example/simple.html
    https://docs.pytest.org/en/latest/plugins.html#requiring-loading-plugins-in-a-test-module-or-conftest-file
"""

from cellpack.autopack.loaders.recipe_loader import RecipeLoader

test_objects = {
    "sphere_25": {
        "type": "single_sphere",
        "inherit": "base",
        "color": [0.5, 0.5, 0.5],
        "radius": 25,
        "max_jitter": [1, 1, 0],
    },
    "base": {"jitter_attempts": 10},
    "sphere_75": {
        "inherit": "sphere_50",
        "color": [0.3, 0.5, 0.8],
        "radius": 75,
    },
    "sphere_50": {
        "inherit": "sphere_25",
        "color": [0.3, 0.5, 0.8],
        "radius": 50,
    },
}


def test_top_sort():
    sorted_nodes = RecipeLoader._topological_sort(objects=test_objects)

    assert sorted_nodes == ["base", "sphere_25", "sphere_50", "sphere_75"]


def test_resolve_objects():
    resolved_objects = RecipeLoader.resolve_inheritance(objects=test_objects)
    expected_result = {
        "sphere_25": {
            "color": [0.5, 0.5, 0.5],
            "inherit": "base",
            "jitter_attempts": 10,
            "max_jitter": [1, 1, 0],
            "radius": 25,
            "type": "single_sphere",
        },
        "base": {"jitter_attempts": 10},
        "sphere_75": {
            "color": [0.3, 0.5, 0.8],
            "inherit": "sphere_50",
            "jitter_attempts": 10,
            "max_jitter": [1, 1, 0],
            "radius": 75,
            "type": "single_sphere",
        },
        "sphere_50": {
            "color": [0.3, 0.5, 0.8],
            "inherit": "sphere_25",
            "jitter_attempts": 10,
            "max_jitter": [1, 1, 0],
            "radius": 50,
            "type": "single_sphere",
        },
    }
    # assert resolved_objects["sphere_50"]["radius"] == 50
    # TODO: add granular testing for individual objects
    assert resolved_objects == expected_result


old_ingredient = {"nbMol": 15, "encapsulatingRadius": 100, "orientBiasRotRangeMax": 12}


@pytest.mark.parametrize(
    "old_ingredient, expected_new_data",
    [
        (
            old_ingredient,
            {"count": 15, "orient_bias_range": [-pi, 12]},
        )
    ],
)
def test_migrate_ingredient(old_ingredient, expected_new_data):
    new_ingredient = RecipeLoader._migrate_ingredient(old_ingredient)
    assert expected_new_data == new_ingredient
    assert expected_new_data["count"] == old_ingredient["nbMol"]
    assert "encapsulatingRadius" not in expected_new_data


old_recipe_test_data = {
    "recipe": {
        "version": "1.1",
        "name": "test recipe",
    },
    "cytoplasme": {
        "ingredients": {
            "test_ingredient_1": {
                "Type": "SingleSphere",
                "nbMol": 15,
                "meshObject": None,
                "meshType": "file",
                "properties": {},
            },
            "test_ingredient_2": {
                "packingMode": "random",
                "packingPriority": 0,
                "encapsulatingRadius": 100,
                "name": "Sphere_radius_100",
            },
        }
    },
}


@pytest.mark.parametrize(
    "old_recipe_test_data, expected_object_dict",
    [
        (
            old_recipe_test_data,
            {
                "test_ingredient_1": {"count": 15, "type": "SingleSphere"},
                "test_ingredient_2": {"packing_mode": "random", "packing_priority": 0},
            },
        )
    ],
)
def test_get_v1_ingredients(old_recipe_test_data, expected_object_dict):
    assert expected_object_dict == RecipeLoader._get_v1_ingredients(
        old_recipe_test_data
    )

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Docs: https://docs.pytest.org/en/latest/example/simple.html
    https://docs.pytest.org/en/latest/plugins.html#requiring-loading-plugins-in-a-test-module-or-conftest-file
"""
import pytest
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
    "sphere_75": {"inherit": "sphere_50", "color": [0.3, 0.5, 0.8], "radius": 75},
    "sphere_50": {"inherit": "sphere_25", "color": [0.3, 0.5, 0.8], "radius": 50},
}


def test_top_sort():
    sorted_nodes = RecipeLoader._topological_sort(objects=test_objects)

    assert sorted_nodes == ["base", "sphere_25", "sphere_50", "sphere_75"]


def test_resolve_objects():
    resolved_objects = RecipeLoader.resolve_inheritance(objects=test_objects)
    expected_result = {
        "sphere_25": {
            "color": [0.5, 0.5, 0.5],
            "jitter_attempts": 10,
            "max_jitter": [1, 1, 0],
            "radius": 25,
            "type": "single_sphere",
        },
        "base": {"jitter_attempts": 10},
        "sphere_75": {
            "color": [0.3, 0.5, 0.8],
            "jitter_attempts": 10,
            "max_jitter": [1, 1, 0],
            "radius": 75,
            "type": "single_sphere",
        },
        "sphere_50": {
            "color": [0.3, 0.5, 0.8],
            "jitter_attempts": 10,
            "max_jitter": [1, 1, 0],
            "radius": 50,
            "type": "single_sphere",
        },
    }
    # assert resolved_objects["sphere_50"]["radius"] == 50
    # TODO: add granular testing for individual objects
    assert resolved_objects == expected_result


@pytest.mark.parametrize(
    "input_recipe_data, expected_result",
    [
        (
            {},
            "1.0",
        ),
        (
            {"format_version": "2.0.33"},
            "2.0",
        ),
        (
            {"format_version": "2.33.0"},
            "2.33",
        ),
        (
            {"format_version": "2.0"},
            "2.0",
        ),
        (
            {"format_version": "2.105"},
            "2.105",
        ),
        (
            {"format_version": "2"},
            "2.0",
        ),
        (
            {"format_version": "1"},
            "1.0",
        ),
    ],
)
def test_sanitize_format_version(expected_result, input_recipe_data):
    assert expected_result == RecipeLoader._sanitize_format_version(input_recipe_data)

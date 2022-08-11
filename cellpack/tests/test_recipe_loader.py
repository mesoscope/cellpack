#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Docs: https://docs.pytest.org/en/latest/example/simple.html
      https://docs.pytest.org/en/latest/plugins.html#requiring-loading-plugins-in-a-test-module-or-conftest-file
"""

from ..autopack.Environment import Environment
from cellpack.autopack.loaders.recipe_loader import RecipeLoader

from collections import Counter

test_objects = {
    "sphere_25": {
        "type": "single_sphere",
        "inherit": "base",
        "color": [0.5, 0.5, 0.5],
        "radius": 25,
        "jitterMax": [1, 1, 0],
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
            "jitterMax": [1, 1, 0],
            "radius": 25,
            "type": "single_sphere",
        },
        "base": {"jitter_attempts": 10},
        "sphere_75": {
            "color": [0.3, 0.5, 0.8],
            "inherit": "sphere_50",
            "jitter_attempts": 10,
            "jitterMax": [1, 1, 0],
            "radius": 75,
            "type": "single_sphere",
        },
        "sphere_50": {
            "color": [0.3, 0.5, 0.8],
            "inherit": "sphere_25",
            "jitter_attempts": 10,
            "jitterMax": [1, 1, 0],
            "radius": 50,
            "type": "single_sphere",
        },
    }
    # assert resolved_objects["sphere_50"]["radius"] == 50
    # TODO: add granular testing for individual objects
    assert resolved_objects == expected_result


def test_find_roots():
    recipe_path = "cellpack/test-recipes/v2/test_recipe_loader.json"
    recipe = RecipeLoader(recipe_path)
    root, _, _ = Environment._resolve_composition(recipe.recipe_data)
    assert root == "space"


def test_compartment_keys():
    recipe_path = "cellpack/test-recipes/v2/test_recipe_loader.json"
    recipe = RecipeLoader(recipe_path)
    _, comp_keys, _ = Environment._resolve_composition(recipe.recipe_data)
    assert Counter(comp_keys) == Counter(["space", "A", "B", "C", "D"])

def test_multiple_roots():
    recipe_path = "cellpack/test-recipes/v2/test_recipe_loader.json"
    recipe = RecipeLoader(recipe_path)
    recipe.recipe_data["composition"]["other_root"] = {
            "regions": {
                "interior": [
                    "tree",
                    "A",
                    "B",
                    "C"
                ]
            }
        }
    err_root = set(["space", "other_root"])
    try:
        Environment._resolve_composition(recipe.recipe_data)
    except Exception as err:
        assert (
            format(err)
            == f"Composition has multiple roots {err_root}"
        )

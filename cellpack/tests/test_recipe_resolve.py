#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Docs: https://docs.pytest.org/en/latest/example/simple.html
      https://docs.pytest.org/en/latest/plugins.html#requiring-loading-plugins-in-a-test-module-or-conftest-file
"""

from cellpack.autopack.loaders.recipe_loader import RecipeLoader
from cellpack.autopack.Recipe import Recipe

from collections import Counter


def test_find_roots():
    recipe_path = "cellpack/tests/recipes/v2/test_recipe_loader.json"
    recipe = RecipeLoader(recipe_path)
    root, _, _, _ = Recipe.resolve_composition(recipe.recipe_data)
    assert root == "space"


def test_compartment_keys():
    recipe_path = "cellpack/tests/recipes/v2/test_recipe_loader.json"
    recipe = RecipeLoader(recipe_path)
    _, comp_keys, _, _ = Recipe.resolve_composition(recipe.recipe_data)
    assert Counter(comp_keys) == Counter(["space", "A", "B", "C", "D"])


def test_multiple_roots():
    recipe_path = "cellpack/tests/recipes/v2/test_recipe_loader.json"
    recipe = RecipeLoader(recipe_path)
    recipe.recipe_data["composition"]["other_root"] = {
        "regions": {"interior": ["tree", "A", "B", "C"]}
    }
    err_root = ["other_root", "space"]
    try:
        Recipe.resolve_composition(recipe.recipe_data)
    except Exception as err:
        assert format(err) == f"Composition has multiple roots {err_root}"

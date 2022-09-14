#!/usr/bin/env python
# -*- coding: utf-8 -*-

from math import pi
import pytest

"""
Docs: https://docs.pytest.org/en/latest/example/simple.html
    https://docs.pytest.org/en/latest/plugins.html#requiring-loading-plugins-in-a-test-module-or-conftest-file
"""

from cellpack.autopack.loaders.recipe_loader import RecipeLoader

old_ingredient = {"nbMol": 15, "encapsulatingRadius": 100, "orientBiasRotRangeMax": 12}


@pytest.mark.parametrize(
    "old_ingredient, expected_new_data",
    [
        (
            old_ingredient,
            {
                "count": 15,
                "orient_bias_range": [-pi, 12],
                "representations": RecipeLoader.default_values["representations"],
            },
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
                "test_ingredient_1": {
                    "count": 15,
                    "type": "SingleSphere",
                    "representations": RecipeLoader.default_values["representations"],
                },
                "test_ingredient_2": {
                    "packing_mode": "random",
                    "packing_priority": 0,
                    "representations": RecipeLoader.default_values["representations"],
                },
            },
        )
    ],
)
def test_get_v1_ingredients(old_recipe_test_data, expected_object_dict):
    assert expected_object_dict == RecipeLoader._get_v1_ingredients(
        old_recipe_test_data
    )


@pytest.mark.parametrize(
    "external_sphereFile, external_result, local_sphereFile, local_result, local_sphereFile_2, local_result_2",
    [
        (
            {"sphereFile": "autoPACKserver/collisionTrees/fibrinogen.sph"},
            {
                "packing": {
                    "name": "fibrinogen.sph",
                    "format": ".sph",
                    "path": "autoPACKserver/collisionTrees",
                },
                "atomic": None,
                "mesh": None,
            },
            {"sphereFile": "fibrinogen.sph"},
            {
                "packing": {
                    "name": "fibrinogen.sph",
                    "format": ".sph",
                    "path": "",
                },
                "atomic": None,
                "mesh": None,
            },
            {"sphereFile": "/fibrinogen.sph"},
            {
                "packing": {
                    "name": "fibrinogen.sph",
                    "format": ".sph",
                    "path": "/",
                },
                "atomic": None,
                "mesh": None,
            },
        )
    ],
)
def test_create_packing_representation(
    external_sphereFile,
    external_result,
    local_sphereFile,
    local_result,
    local_sphereFile_2,
    local_result_2,
):
    assert external_result == RecipeLoader._convert_to_representations(
        external_sphereFile
    )
    assert local_result == RecipeLoader._convert_to_representations(local_sphereFile)
    assert local_result_2 == RecipeLoader._convert_to_representations(
        local_sphereFile_2
    )




@pytest.mark.parametrize(
    "external_sphereFile, external_result, local_sphereFile, local_result, local_sphereFile_2, local_result_2",
    [
        (
            {"sphereFile": "autoPACKserver/collisionTrees/fibrinogen.sph"},
            {
                "packing": {
                    "name": "fibrinogen.sph",
                    "format": ".sph",
                    "path": "autoPACKserver/collisionTrees",
                },
                "atomic": None,
                "mesh": None,
            },
            {"sphereFile": "fibrinogen.sph"},
            {
                "packing": {
                    "name": "fibrinogen.sph",
                    "format": ".sph",
                    "path": "",
                },
                "atomic": None,
                "mesh": None,
            },
            {"sphereFile": "/fibrinogen.sph"},
            {
                "packing": {
                    "name": "fibrinogen.sph",
                    "format": ".sph",
                    "path": "/",
                },
                "atomic": None,
                "mesh": None,
            },
        )
    ],
)
def test_create_packing_representation(
    external_sphereFile,
    external_result,
    local_sphereFile,
    local_result,
    local_sphereFile_2,
    local_result_2,
):
    assert external_result == RecipeLoader._convert_to_representations(
        external_sphereFile
    )
    assert local_result == RecipeLoader._convert_to_representations(local_sphereFile)
    assert local_result_2 == RecipeLoader._convert_to_representations(
        local_sphereFile_2
    )

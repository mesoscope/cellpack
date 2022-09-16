#!/usr/bin/env python
# -*- coding: utf-8 -*-

from math import pi
import pytest

"""
Docs: https://docs.pytest.org/en/latest/example/simple.html
    https://docs.pytest.org/en/latest/plugins.html#requiring-loading-plugins-in-a-test-module-or-conftest-file
"""

from cellpack.autopack.loaders.recipe_loader import RecipeLoader


@pytest.mark.parametrize(
    "old_ingredient_1, expected_result_1, old_ingredient_2, expected_result_2, old_ingredient_3,expected_result_3",
    [
        (
            {"nbMol": 15, "encapsulatingRadius": 100, "orientBiasRotRangeMax": 12},
            {
                "count": 15,
                "orient_bias_range": [-pi, 12],
                "representations": RecipeLoader.default_values["representations"],
            },
            {"nbMol": 15, "encapsulatingRadius": 100, "orientBiasRotRangeMin": 6},
            {
                "count": 15,
                "orient_bias_range": [6, pi],
                "representations": RecipeLoader.default_values["representations"],
            },
            {
                "nbMol": 15,
                "encapsulatingRadius": 100,
                "orientBiasRotRangeMin": 6,
                "orientBiasRotRangeMax": 12,
            },
            {
                "count": 15,
                "orient_bias_range": [6, 12],
                "representations": RecipeLoader.default_values["representations"],
            },
        )
    ],
)
def test_migrate_ingredient(
    old_ingredient_1,
    expected_result_1,
    old_ingredient_2,
    expected_result_2,
    old_ingredient_3,
    expected_result_3,
):
    assert expected_result_1 == RecipeLoader._migrate_ingredient(old_ingredient_1)
    assert expected_result_2 == RecipeLoader._migrate_ingredient(old_ingredient_2)
    assert expected_result_3 == RecipeLoader._migrate_ingredient(old_ingredient_3)
    assert "encapsulatingRadius" not in expected_result_1


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
    "external_sphereFile, external_sphere_result, local_sphereFile, local_sphere_result, local_sphereFile_2, local_sphere_result_2,",
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
def test_create_packing_sphere_representation(
    external_sphereFile,
    external_sphere_result,
    local_sphereFile,
    local_sphere_result,
    local_sphereFile_2,
    local_sphere_result_2,
):
    assert external_sphere_result == RecipeLoader._convert_to_representations(
        external_sphereFile
    )
    assert local_sphere_result == RecipeLoader._convert_to_representations(
        local_sphereFile
    )
    assert local_sphere_result_2 == RecipeLoader._convert_to_representations(
        local_sphereFile_2
    )


@pytest.mark.parametrize(
    "external_mesh, external_mesh_result, local_mesh, local_mesh_result",
    [
        (
            {
                "meshFile": "autoPACKserver/collisionTrees/test.obj",
                "coordsystem": None,
            },
            {
                "mesh": {
                    "name": "test.obj",
                    "format": ".obj",
                    "path": "autoPACKserver/collisionTrees",
                },
                "atomic": None,
                "packing": None,
            },
            {
                "meshFile": "test.obj",
                "coordsystem": "left",
            },
            {
                "mesh": {
                    "name": "test.obj",
                    "format": ".obj",
                    "path": "",
                    "coordinate_system": "left",
                },
                "atomic": None,
                "packing": None,
            },
        )
    ],
)
def test_create_packing_mesh_representation(
    external_mesh,
    external_mesh_result,
    local_mesh,
    local_mesh_result,
):
    assert external_mesh_result == RecipeLoader._convert_to_representations(
        external_mesh
    )
    assert local_mesh_result == RecipeLoader._convert_to_representations(local_mesh)


@pytest.mark.parametrize(
    "atomic_test_data, expected_atomic_result, atomic_test_data_1, expected_atomic_result_1",
    [
        (
            {
                "pdb": "test.pdb",
                "source": {"transform": {"center": True, "translate": [1, 1, 1]}},
            },
            {
                "atomic": {
                    "path": "default",
                    "format": ".pdb",
                    "name": "test.pdb",
                    "transform": {"center": True, "translate": [1, 1, 1]},
                },
                "packing": None,
                "mesh": None,
            },
            {"pdb": "test"},
            {
                "atomic": {
                    "id": "test",
                    "format": ".pdb",
                },
                "packing": None,
                "mesh": None,
            },
        )
    ],
)
def test_create_packing_atomic_representation(
    atomic_test_data,
    expected_atomic_result,
    atomic_test_data_1,
    expected_atomic_result_1,
):
    assert expected_atomic_result == RecipeLoader._convert_to_representations(
        atomic_test_data
    )
    assert expected_atomic_result_1 == RecipeLoader._convert_to_representations(
        atomic_test_data_1
    )

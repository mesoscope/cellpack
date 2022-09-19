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
    "old_ingredient, expected_result",
    [
        (
            {"nbMol": 15, "encapsulatingRadius": 100, "orientBiasRotRangeMax": 12},
            {
                "count": 15,
                "orient_bias_range": [-pi, 12],
                "representations": RecipeLoader.default_values["representations"],
                "partners": {},
            },
        ),
        (
            {"nbMol": 15, "encapsulatingRadius": 100, "orientBiasRotRangeMin": 6},
            {
                "count": 15,
                "orient_bias_range": [6, pi],
                "representations": RecipeLoader.default_values["representations"],
                "partners": {},
            },
        ),
        (
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
                "partners": {},
            },
        ),
    ],
)
def test_migrate_ingredient(
    old_ingredient,
    expected_result,
):
    assert expected_result == RecipeLoader._migrate_ingredient(old_ingredient)
    assert "encapsulatingRadius" not in expected_result


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
                    "partners": {},
                },
                "test_ingredient_2": {
                    "packing_mode": "random",
                    "packing_priority": 0,
                    "representations": RecipeLoader.default_values["representations"],
                    "partners": {},
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
    "sphereFile_data, sphereFile_result",
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
        ),
        (
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
        ),
        (
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
        ),
    ],
)
def test_create_packing_sphere_representation(sphereFile_data, sphereFile_result):
    assert sphereFile_result == RecipeLoader._convert_to_representations(
        sphereFile_data
    )


@pytest.mark.parametrize(
    "mesh_data, mesh_result",
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
        ),
        (
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
        ),
    ],
)
def test_create_packing_mesh_representation(
    mesh_data,
    mesh_result,
):
    assert mesh_result == RecipeLoader._convert_to_representations(mesh_data)


@pytest.mark.parametrize(
    "atomic_test_data, expected_atomic_result",
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
        ),
        (
            {"pdb": "test"},
            {
                "atomic": {
                    "id": "test",
                    "format": ".pdb",
                },
                "packing": None,
                "mesh": None,
            },
        ),
    ],
)
def test_create_packing_atomic_representation(
    atomic_test_data,
    expected_atomic_result,
):
    assert expected_atomic_result == RecipeLoader._convert_to_representations(
        atomic_test_data
    )


@pytest.mark.parametrize(
    "partners_test_data, expected_partners_result",
    [
        (
            {"partners_name": [], "proba_binding": 0.5, "name": "Sphere_radius_100"},
            {
                "names": [],
                "probability_binding": 0.5,
            },
        )
    ],
)
def test_convert_to_partners(partners_test_data, expected_partners_result):
    assert expected_partners_result == RecipeLoader._convert_to_partners(
        partners_test_data
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

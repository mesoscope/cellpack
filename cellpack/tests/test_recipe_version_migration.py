#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Docs: https://docs.pytest.org/en/latest/example/simple.html
    https://docs.pytest.org/en/latest/plugins.html#requiring-loading-plugins-in-a-test-module-or-conftest-file
"""
from math import pi
import pytest

from cellpack.autopack.interface_objects.representations import Representations
from cellpack.autopack.interface_objects.ingredient_types import INGREDIENT_TYPE
from cellpack.autopack.loaders.recipe_loader import RecipeLoader


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
    "old_ingredient, expected_result",
    [
        (
            {
                "encapsulatingRadius": 100,
                "nbMol": 15,
                "orientBiasRotRangeMax": 12,
                "proba_binding": 0.5,
                "Type": "MultiSphere",
            },
            {
                "count": 15,
                "orient_bias_range": [-pi, 12],
                "partners": {"probability_binding": 0.5},
                "representations": RecipeLoader.default_values["representations"],
                "type": INGREDIENT_TYPE.MULTI_SPHERE,
            },
        ),
        (
            {
                "encapsulatingRadius": 100,
                "nbMol": 15,
                "orientBiasRotRangeMin": 6,
                "Type": "Grow",
            },
            {
                "count": 15,
                "orient_bias_range": [6, pi],
                "representations": RecipeLoader.default_values["representations"],
                "type": INGREDIENT_TYPE.GROW,
            },
        ),
        (
            {
                "encapsulatingRadius": 100,
                "nbMol": 15,
                "orientBiasRotRangeMax": 12,
                "orientBiasRotRangeMin": 6,
                "proba_binding": 0.5,
                "radii": [[100]],
                "Type": "SingleSphere",
            },
            {
                "count": 15,
                "orient_bias_range": [6, 12],
                "partners": {"probability_binding": 0.5},
                "radius": 100,
                "representations": RecipeLoader.default_values["representations"],
                "type": INGREDIENT_TYPE.SINGLE_SPHERE,
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
        "version": "1.0",
        "name": "test_recipe",
    },
    "options": {
        "windowsSize": 10,
        "boundingBox": [[0, 0, 0], [1000, 1000, 1000]],
    },
    "cytoplasme": {
        "ingredients": {
            "A": {
                "Type": "SingleSphere",
                "radii": [[10]],
                "nbMol": 15,
                "meshObject": None,
                "meshType": "file",
                "properties": {},
                "orientBiasRotRangeMin": 6,
                "orientBiasRotRangeMax": 12,
            },
            "B": {
                "radii": [[10]],
                "packingMode": "random",
                "packingPriority": 0,
                "encapsulatingRadius": 100,
                "name": "Sphere_radius_100",
                "orientBiasRotRangeMin": 6,
            },
            "C": {
                "radii": [[10]],
                "packingPriority": 0,
                "proba_binding": 0.5,
                "name": "Sphere_radius_200",
                "orientBiasRotRangeMax": 12,
                "sphereFile": "/fibrinogen.sph",
            },
        }
    },
}


def test_get_v1_ingredient():
    ingredient_key = "A"
    ingredient_data = old_recipe_test_data["cytoplasme"]["ingredients"]["A"]
    region_list = []
    objects_dict = {}
    expected_object_data = {
        "radius": 10,
        "type": INGREDIENT_TYPE.SINGLE_SPHERE,
        "representations": RecipeLoader.default_values["representations"],
        "orient_bias_range": [6, 12],
    }
    expected_composition_data = {
        "object": ingredient_key,
        "count": 15,
    }
    RecipeLoader._get_v1_ingredient(
        ingredient_key, ingredient_data, region_list, objects_dict
    )
    assert len(region_list) == 1
    assert objects_dict[ingredient_key] == expected_object_data
    assert region_list[0] == expected_composition_data


@pytest.mark.parametrize(
    "old_recipe_test_data, expected_object_dict, expected_composition_dict",
    [
        (
            old_recipe_test_data,
            {
                "A": {
                    "type": INGREDIENT_TYPE.SINGLE_SPHERE,
                    "radius": 10,
                    "representations": RecipeLoader.default_values["representations"],
                    "orient_bias_range": [6, 12],
                },
                "B": {
                    "type": INGREDIENT_TYPE.SINGLE_SPHERE,
                    "radius": 10,
                    "packing_mode": "random",
                    "representations": RecipeLoader.default_values["representations"],
                    "orient_bias_range": [6, pi],
                },
                "C": {
                    "orient_bias_range": [-pi, 12],
                    "partners": {"probability_binding": 0.5},
                    "radius": 10,
                    "representations": {
                        "packing": {
                            "name": "fibrinogen.sph",
                            "format": ".sph",
                            "path": "/",
                        },
                        "atomic": None,
                        "mesh": None,
                    },
                    "type": INGREDIENT_TYPE.SINGLE_SPHERE,
                },
            },
            {
                "space": {
                    "regions": {
                        "interior": [
                            {"object": "A", "count": 15},
                            {"object": "B", "priority": 0},
                            {"object": "C", "priority": 0},
                        ]
                    }
                }
            },
        )
    ],
)
def test_convert_v1_to_v2(
    old_recipe_test_data, expected_object_dict, expected_composition_dict
):
    objects_dict, composition = RecipeLoader._convert_v1_to_v2(old_recipe_test_data)
    assert objects_dict == expected_object_dict
    assert composition == expected_composition_dict


@pytest.mark.parametrize(
    "converted_data, expected_data",
    [
        (
            RecipeLoader(
                input_file_path="cellpack/test-recipes/v1/test_single_spheres.json"
            ).recipe_data,
            {
                "version": "1.0",
                "format_version": "2.0",
                "name": "test_recipe",
                "bounding_box": [[0, 0, 0], [1000, 1000, 1000]],
                "objects": {
                    "A": {
                        "orient_bias_range": [6, 12],
                        "radius": 10,
                        "representations": Representations(**RecipeLoader.default_values["representations"]),
                        "type": INGREDIENT_TYPE.SINGLE_SPHERE,
                    },
                    "B": {
                        "orient_bias_range": [6, pi],
                        "packing_mode": "random",
                        "radius": 12,
                        "representations": Representations(**RecipeLoader.default_values["representations"]),
                        "type": INGREDIENT_TYPE.SINGLE_SPHERE,
                    },
                    "C": {
                        "type": "SingleSphere",
                        "radius": 100,
                        "partners": {"probability_binding": 0.5},
                        "orient_bias_range": [-pi, 12],
                        "representations": Representations(
                            packing={
                                "name": "fibrinogen.sph",
                                "format": ".sph",
                                "path": "/",
                            }
                        ),
                    },
                },
                "composition": {
                    "space": {
                        "regions": {
                            "interior": [
                                {"object": "A", "count": 15},
                                {"object": "B", "priority": 0},
                                {"object": "C", "priority": 0},
                            ]
                        }
                    }
                },
            },
        )
    ],
)
def test_migrate_version(converted_data, expected_data):
    assert converted_data["composition"] == expected_data["composition"]
    assert converted_data["composition"] == expected_data["composition"]
    assert converted_data["version"] == expected_data["version"]
    assert converted_data["format_version"] == expected_data["format_version"]
    assert converted_data["name"] == expected_data["name"]
    assert converted_data["bounding_box"] == expected_data["bounding_box"]

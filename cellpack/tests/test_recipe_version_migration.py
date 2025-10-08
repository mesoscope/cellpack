#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Docs: https://docs.pytest.org/en/latest/example/simple.html
    https://docs.pytest.org/en/latest/plugins.html#requiring-loading-plugins-in-a-test-module-or-conftest-file
"""
from math import pi
from unittest.mock import MagicMock
import pytest

from cellpack.autopack.interface_objects.representations import Representations
from cellpack.autopack.interface_objects.ingredient_types import INGREDIENT_TYPE
from cellpack.autopack.loaders.recipe_loader import CURRENT_VERSION, RecipeLoader
from cellpack.autopack.loaders.migrate_v1_to_v2 import (
    convert,
    get_representations,
    migrate_ingredient,
    get_and_store_v2_object,
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
                    "path": "github:collisionTrees",
                },
                "atomic": None,
                "mesh": None,
            },
        ),
        (
            {"sphereFile": "fibrinogen.sph"},
            {
                "packing": {"name": "fibrinogen.sph", "format": ".sph", "path": ""},
                "atomic": None,
                "mesh": None,
            },
        ),
        (
            {"sphereFile": "/fibrinogen.sph"},
            {
                "packing": {"name": "fibrinogen.sph", "format": ".sph", "path": "/"},
                "atomic": None,
                "mesh": None,
            },
        ),
    ],
)
def test_create_packing_sphere_representation(sphereFile_data, sphereFile_result):
    assert sphereFile_result == get_representations(sphereFile_data)


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
                    "path": "github:collisionTrees",
                },
                "atomic": None,
                "packing": None,
            },
        ),
        (
            {"meshFile": "test.obj", "coordsystem": "left"},
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
    assert mesh_result == get_representations(mesh_data)


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
                "atomic": {"id": "test", "format": ".pdb"},
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
    assert expected_atomic_result == get_representations(atomic_test_data)


@pytest.mark.parametrize(
    "old_ingredient, expected_result",
    [
        (
            {
                "encapsulatingRadius": 100,
                "nbMol": 15,
                "orientBiasRotRangeMin": -pi,
                "orientBiasRotRangeMax": pi,
                "partners_name": [],
                "proba_binding": 0.5,
                "Type": "MultiSphere",
            },
            {
                "count": 15,
                "orient_bias_range": [-pi, pi],
                "representations": RecipeLoader.default_values["representations"],
                "type": INGREDIENT_TYPE.MULTI_SPHERE,
            },
        ),
        (
            {
                "encapsulatingRadius": 100,
                "nbMol": 15,
                "orientBiasRotRangeMin": -pi,
                "Type": "Grow",
            },
            {
                "count": 15,
                "orient_bias_range": [-pi, pi],
                "representations": RecipeLoader.default_values["representations"],
                "type": INGREDIENT_TYPE.GROW,
            },
        ),
        (
            {
                "encapsulatingRadius": 100,
                "nbMol": 15,
                "orientBiasRotRangeMax": pi,
                "orientBiasRotRangeMin": -pi,
                "proba_binding": 0.5,
                "radii": [[100]],
                "Type": "SingleSphere",
            },
            {
                "count": 15,
                "orient_bias_range": [-pi, pi],
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
    assert expected_result == migrate_ingredient(old_ingredient)
    assert "encapsulatingRadius" not in expected_result


old_recipe_test_data = {
    "recipe": {
        "version": "1.0",
        "name": "test_recipe",
    },
    "options": {"windowsSize": 10, "boundingBox": [[0, 0, 0], [1000, 1000, 1000]]},
    "cytoplasme": {
        "ingredients": {
            "A": {
                "Type": "SingleSphere",
                "radii": [[10]],
                "nbMol": 15,
                "meshObject": None,
                "meshType": "file",
                "properties": {},
                "orientBiasRotRangeMin": -pi,
                "orientBiasRotRangeMax": pi,
            },
            "B": {
                "radii": [[10]],
                "packingMode": "random",
                "packingPriority": 0,
                "encapsulatingRadius": 100,
                "name": "Sphere_radius_100",
                "orientBiasRotRangeMin": -pi,
            },
            "C": {
                "radii": [[10]],
                "packingPriority": 0,
                "proba_binding": 0.5,
                "name": "Sphere_radius_200",
                "orientBiasRotRangeMax": pi,
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
        "orient_bias_range": [-pi, pi],
    }
    expected_composition_data = {
        "object": ingredient_key,
        "count": 15,
    }
    get_and_store_v2_object(ingredient_key, ingredient_data, region_list, objects_dict)
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
                    "orient_bias_range": [-pi, pi],
                },
                "B": {
                    "type": INGREDIENT_TYPE.SINGLE_SPHERE,
                    "radius": 10,
                    "packing_mode": "random",
                    "representations": RecipeLoader.default_values["representations"],
                    "orient_bias_range": [-pi, pi],
                },
                "C": {
                    "orient_bias_range": [-pi, -pi],
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
    new_recipe = convert(old_recipe_test_data)
    assert new_recipe["objects"] == expected_object_dict
    assert new_recipe["composition"] == expected_composition_dict


@pytest.mark.parametrize(
    "converted_data, expected_data",
    [
        (
            RecipeLoader(
                input_file_path="cellpack/tests/recipes/v1/test_single_spheres.json"
            ).recipe_data,
            {
                "version": "1.0",
                "format_version": CURRENT_VERSION,
                "name": "test_single_sphere",
                "bounding_box": [[0, 0, 0], [500, 500, 500]],
                "objects": {
                    "A": {
                        "orient_bias_range": [12 - 2 * pi, 6 - 2 * pi],
                        "radius": 20,
                        "representations": Representations(
                            **RecipeLoader.default_values["representations"]
                        ),
                        "type": INGREDIENT_TYPE.SINGLE_SPHERE,
                    },
                    "B": {
                        "orient_bias_range": [-pi, 6 - 2 * pi],
                        "packing_mode": "random",
                        "radius": 40,
                        "representations": Representations(
                            **RecipeLoader.default_values["representations"]
                        ),
                        "type": INGREDIENT_TYPE.SINGLE_SPHERE,
                    },
                    "C": {
                        "type": INGREDIENT_TYPE.SINGLE_SPHERE.value,
                        "radius": 200,
                        "orient_bias_range": [-pi, 12 - 2 * pi],
                        "representations": Representations(
                            **RecipeLoader.default_values["representations"]
                        ),
                    },
                },
                "composition": {
                    "space": {
                        "regions": {
                            "interior": [
                                {"object": "A", "count": 50},
                                {"object": "B", "count": 30, "priority": 0},
                                {"object": "C", "count": 3, "priority": 0},
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
    assert converted_data["version"] == expected_data["version"]
    assert converted_data["format_version"] == expected_data["format_version"]
    assert converted_data["name"] == expected_data["name"]
    assert converted_data["bounding_box"] == expected_data["bounding_box"]


def test_migrate_version_error():
    not_a_format_version = "0.0"
    with pytest.raises(
        ValueError, match=f"{not_a_format_version} is not a format version we support"
    ):
        RecipeLoader._migrate_version(None, {"format_version": not_a_format_version})


@pytest.mark.parametrize(
    "converted_compartment_data, expected_compartment_data",
    [
        (
            RecipeLoader(
                input_file_path="cellpack/tests/recipes/v1/test_compartment.json"
            ).recipe_data,
            {
                "version": "1.0",
                "format_version": "2.0",
                "name": "test_compartment",
                "bounding_box": [[-0.6, -0.5, -0.25], [0.6, 0.5, 0.15]],
                "objects": {
                    "sphere_exterior": {
                        "jitter_attempts": 20,
                        "rotation_range": 6.2831,
                        "max_jitter": [1, 1, 0],
                        "perturb_axis_amplitude": 0.1,
                        "color": [
                            0.498,
                            0.498,
                            0.498,
                        ],
                        "is_attractor": False,
                        "principal_vector": [1, 0, 0],
                        "packing_mode": "random",
                        "type": INGREDIENT_TYPE.SINGLE_SPHERE,
                        "rejection_threshold": 100,
                        "place_method": "jitter",
                        "rotation_axis": None,
                        "use_rotation_axis": False,
                        "orient_bias_range": [
                            (-3.1415927 + pi) % (2 * pi) - pi,
                            (-3.1415927 + pi) % (2 * pi) - pi,
                        ],
                        "representations": Representations(
                            **RecipeLoader.default_values["representations"]
                        ),
                        "radius": 1,
                    },
                    "compartment_A": {
                        "type": INGREDIENT_TYPE.MESH,
                        "orient_bias_range": [-pi, -pi],
                        "representations": Representations(
                            mesh={
                                "path": "cellpack/test/geometry",
                                "name": "membrane_1.obj",
                                "format": ".obj",
                            }
                        ),
                    },
                    "sphere_surface": {
                        "jitter_attempts": 20,
                        "rotation_range": 6.2831,
                        "max_jitter": [1, 1, 0],
                        "perturb_axis_amplitude": 0.1,
                        "color": [0.306, 0.45100001, 0.81599998],
                        "is_attractor": False,
                        "principal_vector": [1, 0, 0],
                        "packing_mode": "random",
                        "type": INGREDIENT_TYPE.SINGLE_SPHERE,
                        "rejection_threshold": 100,
                        "place_method": "jitter",
                        "rotation_axis": None,
                        "use_rotation_axis": False,
                        "orient_bias_range": [
                            (-3.1415927 + pi) % (2 * pi) - pi,
                            (-3.1415927 + pi) % (2 * pi) - pi,
                        ],
                        "representations": Representations(
                            **RecipeLoader.default_values["representations"]
                        ),
                        "radius": 1.0,
                    },
                    "sphere_inside": {
                        "jitter_attempts": 20,
                        "rotation_range": 6.2831,
                        "max_jitter": [1, 1, 0],
                        "perturb_axis_amplitude": 0.1,
                        "color": [0.306, 0.45100001, 0.81599998],
                        "is_attractor": False,
                        "principal_vector": [1, 0, 0],
                        "packing_mode": "random",
                        "type": INGREDIENT_TYPE.SINGLE_SPHERE,
                        "rejection_threshold": 100,
                        "place_method": "jitter",
                        "rotation_axis": None,
                        "use_rotation_axis": False,
                        "orient_bias_range": [
                            (-3.1415927 + pi) % (2 * pi) - pi,
                            (-3.1415927 + pi) % (2 * pi) - pi,
                        ],
                        "representations": Representations(
                            **RecipeLoader.default_values["representations"]
                        ),
                        "radius": 1.25,
                    },
                },
                "composition": {
                    "space": {
                        "regions": {
                            "interior": [
                                {
                                    "object": "sphere_exterior",
                                    "count": 20,
                                    "priority": 0,
                                },
                                "compartment_A",
                            ]
                        }
                    },
                    "compartment_A": {
                        "object": "compartment_A",
                        "regions": {
                            "surface": [
                                {"object": "sphere_surface", "count": 20, "priority": 0}
                            ],
                            "interior": [
                                {"object": "sphere_inside", "count": 200, "priority": 0}
                            ],
                        },
                    },
                },
            },
        )
    ],
)
def test_convert_compartment(converted_compartment_data, expected_compartment_data):
    assert converted_compartment_data["version"] == expected_compartment_data["version"]
    assert (
        converted_compartment_data["composition"]
        == expected_compartment_data["composition"]
    )
    assert converted_compartment_data["name"] == expected_compartment_data["name"]
    for obj in converted_compartment_data["objects"]:
        data = converted_compartment_data["objects"][obj]
        mock_rep = MagicMock()
        mock_partners = MagicMock()
        data["representations"] = mock_rep
        data["partners"] = mock_partners
        expected_compartment_data["objects"][obj]["representations"] = mock_rep
        expected_compartment_data["objects"][obj]["partners"] = mock_partners
        assert (
            converted_compartment_data["objects"][obj]
            == expected_compartment_data["objects"][obj]
        )

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


# tests for the firebase recipe loader
downloaded_data_from_firebase = {
    "version": "linear",
    "format_version": "2.1",
    "composition": {
        "membrane": {
            "count": 1,
            "regions": {
                "interior": [
                    {
                        "count": 121,
                        "object": {
                            "gradient": {
                                "mode": "surface",
                                "name": "nucleus_surface_gradient",
                            },
                            "name": "peroxisome",
                        },
                    },
                    {
                        "count": 1,
                        "regions": {"interior": []},
                        "object": {
                            "name": "mean_nucleus",
                            "partners": {"all_partners": []},
                        },
                        "name": "nucleus",
                    },
                ]
            },
            "object": {
                "name": "mean_membrane",
                "type": "mesh",
            },
            "name": "membrane",
        },
        "nucleus": {
            "count": 1,
            "regions": {"interior": []},
            "object": {
                "name": "mean_nucleus",
                "partners": {"all_partners": []},
            },
            "name": "nucleus",
        },
        "bounding_area": {
            "count": None,
            "regions": {
                "interior": [
                    {
                        "count": 1,
                        "regions": {
                            "interior": [
                                {
                                    "count": 121,
                                    "object": {
                                        "gradient": {
                                            "mode": "surface",
                                            "name": "nucleus_surface_gradient",
                                        },
                                        "name": "peroxisome",
                                    },
                                },
                                {
                                    "count": 1,
                                    "regions": {"interior": []},
                                    "object": {
                                        "name": "mean_nucleus",
                                        "partners": {"all_partners": []},
                                    },
                                    "name": "nucleus",
                                },
                            ]
                        },
                        "object": {
                            "name": "mean_membrane",
                            "type": "mesh",
                        },
                        "name": "membrane",
                    }
                ]
            },
            "name": "bounding_area",
        },
    },
    "version": "linear",
    "bounding_box": [[-110, -45, -62], [110, 45, 62]],
    "name": "test_recipe",
}


compiled_firebase_recipe_example = {
    "name": "test_recipe",
    "format_version": "2.1",
    "version": "linear",
    "bounding_box": [[-110, -45, -62], [110, 45, 62]],
    "objects": {
        "mean_membrane": {
            "name": "mean_membrane",
            "type": "mesh",
        },
        "peroxisome": {
            "name": "peroxisome",
            "gradient": "nucleus_surface_gradient",
        },
        "mean_nucleus": {
            "name": "mean_nucleus",
            "partners": {"all_partners": []},
        },
    },
    "gradients": [
        {
            "name": "nucleus_surface_gradient",
            "mode": "surface",
        }
    ],
    "composition": {
        "bounding_area": {"regions": {"interior": ["membrane"]}},
        "membrane": {
            "count": 1,
            "object": "mean_membrane",
            "regions": {
                "interior": [{"object": "peroxisome", "count": 121}, "nucleus"]
            },
        },
        "nucleus": {
            "count": 1,
            "object": "mean_nucleus",
            "regions": {"interior": []},
        },
    },
}


@pytest.fixture
def sort_data_from_composition():
    return RecipeLoader._collect_and_sort_data(
        downloaded_data_from_firebase["composition"]
    )


def test_collect_and_sort_data(sort_data_from_composition):
    objects, gradients, composition = sort_data_from_composition
    assert objects == compiled_firebase_recipe_example["objects"]
    assert gradients == {
        "nucleus_surface_gradient": {
            "name": "nucleus_surface_gradient",
            "mode": "surface",
        }
    }
    assert composition == compiled_firebase_recipe_example["composition"]


def test_compile_recipe_from_firebase(sort_data_from_composition):
    objects, gradients, composition = sort_data_from_composition
    compiled_recipe = RecipeLoader._compile_recipe_from_firebase(
        downloaded_data_from_firebase, objects, gradients, composition
    )
    assert compiled_recipe == compiled_firebase_recipe_example


def test_get_grad_and_obj():
    obj_data = {
        "gradient": {
            "mode": "surface",
            "name": "nucleus_surface_gradient",
        },
        "name": "peroxisome",
    }
    obj_dict = {
        "peroxisome": {
            "gradient": {
                "mode": "surface",
                "name": "nucleus_surface_gradient",
            },
            "name": "peroxisome",
        }
    }
    grad_dict = {}
    obj_dict, grad_dict = RecipeLoader._get_grad_and_obj(obj_data, obj_dict, grad_dict)
    assert obj_dict == {
        "peroxisome": {"gradient": "nucleus_surface_gradient", "name": "peroxisome"}
    }
    assert grad_dict == {
        "nucleus_surface_gradient": {
            "mode": "surface",
            "name": "nucleus_surface_gradient",
        }
    }

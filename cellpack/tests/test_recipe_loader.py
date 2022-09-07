#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
        "jitter_max": [1, 1, 0],
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
            "jitter_max": [1, 1, 0],
            "radius": 25,
            "type": "single_sphere",
        },
        "base": {"jitter_attempts": 10},
        "sphere_75": {
            "color": [0.3, 0.5, 0.8],
            "inherit": "sphere_50",
            "jitter_attempts": 10,
            "jitter_max": [1, 1, 0],
            "radius": 75,
            "type": "single_sphere",
        },
        "sphere_50": {
            "color": [0.3, 0.5, 0.8],
            "inherit": "sphere_25",
            "jitter_attempts": 10,
            "jitter_max": [1, 1, 0],
            "radius": 50,
            "type": "single_sphere",
        },
    }
    # assert resolved_objects["sphere_50"]["radius"] == 50
    # TODO: add granular testing for individual objects
    assert resolved_objects == expected_result

old_ingredient_should_be_renamed = {
            "nbJitter": 20,
            "jitterMax": [
                1,
                1,
                0
            ],
            "perturbAxisAmplitude": 0.1,
            "isAttractor": False,
            "principalVector": [
                1,
                0,
                0
            ],
            "Type": "SingleSphere",
            "nbMol": 15,
            "packingMode": "random",
            "packingPriority": 0,
            "placeType": "jitter",
            "rejectionThreshold": 100,
            "rotAxis": None,
            "rotRange": 6.2831,
            "useRotAxis": False
        }

@pytest.mark.parametrize(
    "old_ingredient_data, expected_new_data",
    [
        (
            old_ingredient_should_be_renamed,
            {'count': 15,
            'is_attractor': False,
            'max_jitter': [1, 1, 0],
            'num_jitter': 20,
            'packing_mode': 'random',
            'packing_priority': 0,
            'perturb_axis_amplitude': 0.1,
            'place_type': 'jitter',
            'principal_vector': [1, 0, 0],
            'rejection_threshold': 100,
            'rotation_axis': None,
            'rotation_range': 6.2831,
            'type': 'SingleSphere',
            'use_rotation_axis': False}
        )
    ]

)


def test_migrate_ingredient(old_ingredient_data, expected_new_data):
    new_ingredient = RecipeLoader._migrate_ingredient(old_ingredient_data)
    assert new_ingredient == expected_new_data
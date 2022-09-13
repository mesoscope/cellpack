#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Docs: https://docs.pytest.org/en/latest/example/simple.html
      https://docs.pytest.org/en/latest/plugins.html#requiring-loading-plugins-in-a-test-module-or-conftest-file
"""

import os
from cellpack import autopack
import numpy as np

from cellpack.autopack.interface_objects.representations import Representations

pdb_id = "1234"

test_mesh_obj = {"path": "test_path/", "name": "test.obj", "format": "obj"}

test_pdb_id_obj = {
    "id": pdb_id,
}

test_pdb_id_obj_with_offset = {"id": pdb_id, "transform": {"translate": [10, 10, 10]}}
test_pdb_url_obj = {"path": "test_path/", "name": "test.pdb", "format": "pdb"}

test_sphere_tree_obj = {
    "path": "cellpack/test-geometry/",
    "name": "test.sph",
    "format": "sph",
}

test_sphere_tree_unpacked_obj = {"positions": [[[1, 0, 0]]], "radii": [[10]]}


def test_mesh():
    representations = Representations(mesh=test_mesh_obj)
    assert representations.has_mesh()
    assert representations.get_mesh_path() == "test_path/test.obj"


def test_mesh_missing():
    representations = Representations()
    assert not representations.has_mesh()
    assert representations.get_mesh_path() is None


def test_pdb_id():
    representations = Representations(atomic=test_pdb_id_obj)
    assert representations.has_pdb()
    assert representations.get_pdb_path() == pdb_id


def test_pdb_url():
    representations = Representations(atomic=test_pdb_url_obj)
    assert representations.has_pdb()
    assert representations.get_pdb_path() == "test_path/test.pdb"


def test_sphere_tree():
    autopack.current_recipe_path = os.path.dirname(".")
    representations = Representations(packing=test_sphere_tree_obj)
    positions, radii = representations.get_spheres()
    assert len(positions) > 0
    assert len(radii) > 0


def test_unpacked_sphere_tree():
    autopack.current_recipe_path = os.path.dirname(".")
    representations = Representations(packing=test_sphere_tree_unpacked_obj)
    positions, radii = representations.get_spheres()
    assert len(positions) > 0
    assert len(radii) > 0
    assert positions == [[[1, 0, 0]]]


def test_set_active():
    representations = Representations(mesh=test_mesh_obj, atomic=test_pdb_id)
    representations.set_active("atomic")
    assert representations.get_active() == "atomic"
    assert representations.get_active_data() == test_pdb_id


def test_get_adjusted_position():
    starting_position = [1, 1, 1]
    representations = Representations(
        mesh=test_mesh_obj, atomic=test_pdb_id_obj_with_offset
    )
    # if the representation used has a transform, should move the starting position
    representations.set_active("atomic")
    adjusted_position = representations.get_adjusted_position(
        starting_position, np.eye(4)
    )
    for i in range(len(adjusted_position)):
        assert adjusted_position[i] != starting_position[i]

    # if the representation used doesn't a transform, should return the same starting position
    representations.set_active("mesh")
    adjusted_position = representations.get_adjusted_position(
        starting_position, np.eye(4)
    )
    for i in range(len(adjusted_position)):
        assert adjusted_position[i] == starting_position[i]

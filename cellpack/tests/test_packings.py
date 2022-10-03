#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Docs: https://docs.pytest.org/en/latest/example/simple.html
      https://docs.pytest.org/en/latest/plugins.html#requiring-loading-plugins-in-a-test-module-or-conftest-file
"""

import os
import json


def test_packing_bias():
    os.system(
        "pack -r cellpack/tests/recipes/test_spheres.json -c cellpack/tests/packing-configs/test_config.json"
    )
    all_pos_path = "cellpack/tests/outputs/test_spheres/jitter/all_pos.json"
    with open(all_pos_path, "r") as j:
        all_pos = json.loads(j.read())
    expected_pos_path = "cellpack/tests/data/all_pos.json"
    with open(expected_pos_path, "r") as j:
        expected_pos = json.loads(j.read())
    assert all_pos == expected_pos

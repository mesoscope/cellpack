#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
NOTE: All test file names and functions must have one of the two forms.
- `test_<XYY>.py`
- '<XYZ>_test.py'

Docs: https://docs.pytest.org/en/latest/
      https://docs.pytest.org/en/latest/goodpractices.html#conventions-for-python-test-discovery
"""

from cellpack.autopack.loaders.config_loader import ConfigLoader


# If you only have a single condition you need to test, a single test is _okay_
# but parametrized tests are encouraged
def test_over_write_default_data():
    config = ConfigLoader("cellpack/tests/data/config.json").config
    assert config["place_method"] == "spheresSST"


def test_wrong_place_method():
    config = ConfigLoader.default_values.copy()
    config["place_method"] = "error"
    try:
        ConfigLoader._test_types(config)
    except TypeError as error:
        assert format(error) == "place_method must be one of ['jitter', 'spheresSST', 'pandaBullet', 'pandaBulletRelax'], not error"


def test_not_bool():
    config = ConfigLoader.default_values.copy()
    config["use_periodicity"] = "error"
    try:
        ConfigLoader._test_types(config)
    except TypeError as error:
        assert format(error) == "use_periodicity should be a boolean, not error"

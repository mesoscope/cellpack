#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
NOTE: All test file names must have one of the two forms.
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


def test_will_error_out():
    try:
        ConfigLoader("cellpack/tests/data/error_place_method.json").config
    except TypeError:
        print(TypeError)

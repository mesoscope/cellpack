# -*- coding: utf-8 -*-

"""Top-level package for cellPack."""

__author__ = "Megan Riel-Mehan"
__email__ = "meganr@alleninstitute.org"
# Do not edit this string manually, always use bumpversion
# Details in CONTRIBUTING.md
__version__ = "0.2.3"

from .example import Example  # noqa: F401


def get_module_version():
    return __version__

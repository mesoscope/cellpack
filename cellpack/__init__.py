# -*- coding: utf-8 -*-

"""Top-level package for cellPack."""

__author__ = "Megan Riel-Mehan"
__email__ = "meganr@alleninstitute.org"
# Do not edit this string manually, always use bumpversion
# Details in CONTRIBUTING.md
__version__ = "1.0.3"

from .autopack.loaders.recipe_loader import RecipeLoader  # noqa: F401


def get_module_version():
    return __version__

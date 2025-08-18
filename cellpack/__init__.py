# -*- coding: utf-8 -*-

"""Top-level package for cellPACK."""

__author__ = "Megan Riel-Mehan"
__email__ = "meganr@alleninstitute.org"
# Do not edit this string manually, always use bumpversion
# Details in CONTRIBUTING.md
__version__ = "v1.1.1"


import logging
import logging.config
from pathlib import Path

# This is required by simulariumio which imports RecipeLoader directly from cellpack
from cellpack.autopack.loaders.recipe_loader import RecipeLoader  # noqa: F401

log_file_path = Path(__file__).parent / "logging.conf"
if not log_file_path.exists():
    raise FileNotFoundError(f"Logging configuration file not found: {log_file_path}")

logging.config.fileConfig(log_file_path, disable_existing_loggers=True)
log = logging.getLogger("autopack")
log.propagate = False

# disable existing loggers
logging.getLogger("xmlschema").setLevel(logging.WARNING)


def get_module_version():
    return __version__

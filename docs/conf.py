# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "cellPACK"
copyright = "2025, Megan Riel-Mehan, Saurabh Mogre, Ruge Li, Allison Scibisz"
author = "Megan Riel-Mehan, Saurabh Mogre, Ruge Li, Allison Scibisz"
release = "1.1.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.mathjax",
    "myst_parser",
]


myst_enable_extensions = [
    "deflist",
    "colon_fence",
    "linkify",
    "substitution",
    "tasklist",
]

# Control napoleon
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_use_ivar = True
napoleon_use_param = False

source_suffix = {
    ".rst": "restructuredtext",
    ".txt": "markdown",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "archive"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]

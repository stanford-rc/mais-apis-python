# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import pathlib
import os
import sys

# Get the path to this config file, and convert to an absolute path.
# Then, use that to work out the path to the `src` dir, and add it.
conf_path = pathlib.Path(__file__).resolve()
src_path = conf_path.parent / 'src'
sys.path.insert(0, str(src_path))

# -- Project information -----------------------------------------------------

project = 'Stanford MaIS APIs'
copyright = '2021, The Board of Trustees of the Leland Stanford Junior University'
author = 'Stanford Research Computing Center'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
#    'stanford_theme',
    'sphinx_rtd_theme',
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
]

# Intersphinx mappings
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'requests': ('https://docs.python-requests.org/en/master', None),
}

# Autodoc configuration
autodoc_default_options = {
    'member-order': 'bysource',
}

# Add any paths that contain templates here, relative to this directory.
templates_path = []

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
#html_theme = 'stanford_theme'
#html_theme_path = [stanford_theme.get_html_theme_path()]
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []

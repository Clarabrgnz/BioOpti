"""Sphinx configuration."""

# This file is execfile()d with the current directory set to its containing dir.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import os
import shutil
import sys
from importlib.metadata import metadata

# -- Path setup 

__location__ = os.path.dirname(__file__)

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.join(__location__, "../../src"))

# -- Run sphinx-apidoc 
# This hack is necessary since RTD does not issue `sphinx-apidoc` before running
# `sphinx-build -b html . _build/html`. See Issue:
# https://github.com/readthedocs/readthedocs.org/issues/1139
# DON'T FORGET: Check the box "Install your project inside a virtualenv
# Additionally it helps us to avoid running apidoc manually

try:  # for Sphinx >= 1.7
    from sphinx.ext import apidoc
except ImportError:
    from sphinx import apidoc

output_dir = os.path.join(__location__, "api")
module_dir = os.path.join(__location__, "../../src/bioopti")
# Clean up old generated files
shutil.rmtree(output_dir, ignore_errors=True)

# Invoke sphinx-apidoc
try:
    import sphinx
    cmd = f"sphinx-apidoc --implicit-namespaces -f -o {output_dir} {module_dir}"
    args = cmd.split()[1:]  # drop the “sphinx-apidoc” part
    apidoc.main(args)
except Exception as e:
    print(f"Running sphinx-apidoc failed: {e}")

# -- Project information -----------------------------------------------------

_md = metadata("BioOpti")
project   = _md["Name"]
author    = _md["Author-email"].split("<", 1)[0].strip()
copyright = f"2024, {author}"
version   = _md["Version"]
release   = ".".join(version.split(".")[:2])

# -- General configuration ---------------------------------------------------

extensions = [
    "myst_parser",              # Markdown support
    "sphinx_copybutton",        # “Copy” buttons on code blocks
    "sphinx.ext.autodoc",       # Pull in docstrings
    "sphinx.ext.intersphinx",   # Link to other projects’ docs
    "sphinx.ext.viewcode",      # Add links to source code
    "sphinx.ext.autosectionlabel",  # Auto‑generate labels for sections
]

# -- MyST Parser configuration -----------------------------------------------

# Generate HTML anchors for headings up to level 3 (##, ###)
myst_heading_anchors = 3

# Promote the first Markdown heading to the document title
myst_title_to_header = True

# Suppress MyST warnings for:
#  • missing cross‑ref targets (“xref-missing”)
#  • documents starting at H2 instead of H1 (“header”)
myst_suppress_warnings = [
    "xref-missing",
    "header",
]

# -- (Optional) Sphinx core warning suppressions -----------------------------

# If you ever need to silence core Sphinx warnings, you can list them here.
suppress_warnings = []

# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
html_static_path = ["_static"]

# -- Intersphinx configuration ----------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master", None),
}
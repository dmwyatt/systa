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
import os
import sys

import commonmark

sys.path.insert(0, os.path.abspath("../"))
sys.path.insert(0, os.path.abspath("../src"))
# sys.path.insert(0, os.path.abspath(os.path.join("..", "..", "src")))


# -- Project information -----------------------------------------------------

project = "systa"
copyright = "2021, Dustin Wyatt"
author = "Dustin Wyatt"

# The full version, including alpha/beta/rc tags
release = "0.0.1"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_book_theme"

html_theme_options = {
    "repository_url": "https://github.com/dmwyatt/systa",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_edit_page_button": True,
    "repository_branch": "dev",
    "path_to_docs": "docs/source",
    "home_page_in_toc": True,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]


rst_prolog = """
.. role:: python(code)
    :language: python
"""

autodoc_typehints = "description"
autoclass_content = "both"

autodoc_type_aliases = {
    "EventRangesType": "systa.events.types.EventRangesType",
    "EventRangeType": "systa.events.types.EventRangeType",
    "EventType": "systa.events.types.EventType",
    "EventsTypes": "systa.events.types.EventsType",
    "EventTypeNamesType": "systa.events.types.EventTypeNamesType",
    "WindowLookupType": "systa.windows.WindowLookupType",
    "ObjIdType": "systa.events.types.ObjIdType",
}

doctest_global_setup = """
import subprocess
import time
from systa.windows import current_windows
current_notepads = current_windows["Untitled - Notepad"]
for np in current_notepads:
    np.exists = False
notepad_process = subprocess.Popen(["notepad.exe"])
time.sleep(.3)
"""

doctest_global_cleanup = """
notepad_process.kill()
from systa.events.store import callback_store
callback_store.clear_store()
"""

autosectionlabel_prefix_document = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pynput": ("https://pynput.readthedocs.io/en/latest", None),
}


def docstring(app, what, name, obj, options, lines):
    if len(lines) > 1 and lines[0] == "@&ismd":
        md = "\n".join(lines[1:])
        ast = commonmark.Parser().parse(md)
        rst = commonmark.ReStructuredTextRenderer().render(ast)
        lines.clear()
        lines += rst.splitlines()


def setup(app):
    app.connect("autodoc-process-docstring", docstring)

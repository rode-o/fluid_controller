# controller_interface/src/utils/path_utils.py

import os
import sys

def resource_path(relative_path: str) -> str:
    """
    Returns the absolute path to a resource. Works for development environments
    and for PyInstaller bundles, which use a temp folder with _MEIPASS.

    If you use something like:
        pyinstaller --add-data "controller_interface/resources/*;resources"
    then your files are in "resources/" at runtime inside the PyInstaller bundle.

    Usage:
        full_path = resource_path("resources/salvus_full_logo_color.png")
    """
    if hasattr(sys, '_MEIPASS'):
        # Running in PyInstaller-built executable
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
    else:
        # Running in a normal Python environment
        base_path = os.path.dirname(__file__)

    return os.path.join(base_path, relative_path)

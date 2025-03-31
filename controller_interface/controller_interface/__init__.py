# controller_interface/__init__.py
"""
Exports everything from the subpackages for top-level imports.
"""

# model
from .model.analysis import analyze_data
from .model.flow_volume_tracker import FlowVolumeTracker
from .model.run_manager import RunManager
from .model.serial_worker import SerialWorker

# controller
from .controller.ui_controller import UiController  # <--- Updated

# utils
from .utils.logging_utils import logger
from .utils.path_utils import resource_path

# view
from .view.panels.control import TuningControlPanel
from .view.panels.live_data import LiveDataPanel
from .view.plots.plot_manager import TuningPlotManager
from .view.views.home import HomeView
from .view.views.main_window import MainWindow
from .view.views.ui import PidTuningView
from .view.widgets.themed_button import ThemedButton

__all__ = [
    # model
    "analyze_data",
    "FlowVolumeTracker",
    "RunManager",
    "SerialWorker",
    # controller
    "UiController",        # <--- Updated
    # utils
    "logger",
    "resource_path",
    # view
    "TuningControlPanel",
    "LiveDataPanel",
    "TuningPlotManager",
    "HomeView",
    "MainWindow",
    "PidTuningView",
    "ThemedButton",
]

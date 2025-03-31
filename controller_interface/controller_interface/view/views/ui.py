# controller_interface/view/views/ui.py

import time

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QMessageBox,
    QLabel, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap

# Example aggregator import:
# from controller_interface import (
#     UiController,
#     TuningControlPanel,
#     LiveDataPanel,
#     TuningPlotManager,
#     ThemedButton,
#     resource_path
# )

# Or if you want direct imports (both are valid):
from controller_interface.controller.ui_controller import UiController
from controller_interface.view.panels.control import TuningControlPanel
from controller_interface.view.panels.live_data import LiveDataPanel
from controller_interface.view.plots.plot_manager import TuningPlotManager
from controller_interface.view.widgets.themed_button import ThemedButton
from controller_interface.utils.path_utils import resource_path


class PidTuningView(QWidget):
    """
    A QWidget for advanced PID monitoring and data logging.
    The logic is now in UiController. This class sets up the UI,
    delegates start/stop to the controller, and updates real-time graphs.
    """

    goHomeSignal = pyqtSignal()  # for navigating back home

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings

        # Create the run controller
        self.controller = UiController()
        self.controller.new_data_signal.connect(self._on_new_data)
        self.controller.error_signal.connect(self._on_error)
        self.controller.finished_signal.connect(self._on_finished)

        # UI components
        self.tuning_panel = TuningControlPanel(settings=self.settings)
        self.live_data_panel = LiveDataPanel()
        self.tuning_plot_manager = None

        # We'll track local start time in the UI for plotting
        self.start_time = None

        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        hbox_main = QHBoxLayout()

        # Left column
        left_vbox = QVBoxLayout()
        left_vbox.addWidget(self.tuning_panel, stretch=0)
        left_vbox.addWidget(self.live_data_panel, stretch=0)

        # Logo container
        logo_container = QVBoxLayout()
        logo_container.setContentsMargins(30, 125, 30, 125)

        self.lbl_logo = QLabel()
        self.lbl_logo.setScaledContents(True)
        self.lbl_logo.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        logo_path = resource_path("resources/salvus_full_logo_color.png")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            self.lbl_logo.setPixmap(pixmap)
        else:
            self.lbl_logo.setText("Logo not found")

        logo_container.addWidget(self.lbl_logo)
        left_vbox.addLayout(logo_container, stretch=1)

        left_container = QWidget()
        left_container.setLayout(left_vbox)
        hbox_main.addWidget(left_container, stretch=1)

        # Right column
        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        self.tuning_plot_manager = TuningPlotManager(plot_layout)
        hbox_main.addWidget(plot_container, stretch=9)

        main_layout.addLayout(hbox_main)

        # Bottom row: Home button
        bottom_row = QHBoxLayout()
        bottom_row.addStretch(1)
        self.btn_home = ThemedButton("Home", is_dark=True)
        self.btn_home.clicked.connect(self._on_home_clicked)
        bottom_row.addWidget(self.btn_home)
        main_layout.addLayout(bottom_row)

        self.setLayout(main_layout)

        # Connect panel signals
        self.tuning_panel.startSignal.connect(self._on_start_clicked)
        self.tuning_panel.stopSignal.connect(self._on_stop_clicked)
        self.tuning_panel.stabilityChanged.connect(self._on_stability_changed)

    def _load_settings(self):
        if not self.settings:
            return
        last_port = self.settings.value("tuning_last_port", "")
        if last_port:
            idx = self.tuning_panel.port_combo.findText(last_port)
            if idx >= 0:
                self.tuning_panel.port_combo.setCurrentIndex(idx)

        last_baud = self.settings.value("tuning_last_baud", "115200")
        idx_baud = self.tuning_panel.baud_combo.findText(last_baud)
        if idx_baud >= 0:
            self.tuning_panel.baud_combo.setCurrentIndex(idx_baud)

        last_tw = self.settings.value("tuning_time_window", 10.0, type=float)
        self.tuning_panel.time_window_spin.setValue(last_tw)
        self.tuning_panel.load_settings()

    def _save_settings(self):
        if not self.settings:
            return
        self.settings.setValue("tuning_last_port", self.tuning_panel.get_port())
        self.settings.setValue("tuning_last_baud", self.tuning_panel.get_baud())
        self.settings.setValue("tuning_time_window", self.tuning_panel.get_time_window())
        self.tuning_panel.save_settings()

    # -----------------------------------------------------------
    # Navigation
    # -----------------------------------------------------------
    def _on_home_clicked(self):
        self.goHomeSignal.emit()

    # -----------------------------------------------------------
    # Start/Stop
    # -----------------------------------------------------------
    def _on_start_clicked(self):
        self._save_settings()
        port = self.tuning_panel.get_port()
        if port == "No ports found":
            QMessageBox.warning(self, "No Port", "No valid port selected.")
            return

        baud_str = self.tuning_panel.get_baud()
        try:
            baud = int(baud_str)
        except ValueError:
            QMessageBox.warning(self, "Invalid Baud", "Not an integer.")
            return

        time_window = self.tuning_panel.get_time_window()
        data_root = self.tuning_panel.get_data_root()
        if not data_root:
            QMessageBox.warning(self, "No Data Dir", "Please pick a data directory.")
            return

        test_name = self.tuning_panel.get_test_name() or "untitled"

        # Start the run via the controller
        self.controller.start_capture(port, baud, data_root, test_name, time_window)

        # Initialize local plot
        self.tuning_plot_manager.start_run()
        self.tuning_plot_manager.set_time_window(time_window)
        self.start_time = time.time()

        # UI feedback
        self.tuning_panel.btn_start.setEnabled(False)
        self.tuning_panel.btn_stop.setEnabled(True)

        QMessageBox.information(
            self,
            "Capture",
            f"Started streaming on {port} @ {baud} (time={time_window}s)\n"
            f"Logging to: {data_root}"
        )

    def _on_stop_clicked(self):
        self.controller.stop_capture()

    # -----------------------------------------------------------
    # Stability
    # -----------------------------------------------------------
    def _on_stability_changed(self, stable: bool):
        self.controller.set_stability(stable)

    # -----------------------------------------------------------
    # Controller Signals
    # -----------------------------------------------------------
    def _on_new_data(self, data_dict):
        """
        Called whenever the controller emits new_data_signal.
        We update the plot and the LiveDataPanel.
        """
        # Update plot based on local start_time
        if self.start_time is not None:
            elapsed = time.time() - self.start_time
            self.tuning_plot_manager.update_data(data_dict, elapsed)

        # For live data panel
        flow_val_ml_min = float(data_dict.get("flow", 0.0))
        setpt = float(data_dict.get("setpt", 0.0))
        temp = float(data_dict.get("temp", 0.0))
        volt = float(data_dict.get("volt", 0.0))
        bubble_bool = bool(data_dict.get("bubble", False))
        total_flow_ml = self.controller.flow_tracker.get_total_volume_ml()  # optional direct attribute usage

        self.live_data_panel.update_data(
            setpt_val=setpt,
            flow_val=flow_val_ml_min,
            temp_val=temp,
            volt_val=volt,
            bubble_bool=bubble_bool,
            p_val=float(data_dict.get("P", 0.0)),
            i_val=float(data_dict.get("I", 0.0)),
            d_val=float(data_dict.get("D", 0.0)),
            pid_out_val=float(data_dict.get("pidOut", 0.0)),
            error_pct=data_dict.get("errorPct", None),
            on_state=data_dict.get("on", None),
            mode_val=data_dict.get("mode", None),
            p_gain=data_dict.get("pGain", None),
            i_gain=data_dict.get("iGain", None),
            d_gain=data_dict.get("dGain", None),
            filtered_err=data_dict.get("filteredErr", None),
            current_alpha=data_dict.get("currentAlpha", None),
            total_flow_ml=total_flow_ml
        )

    def _on_error(self, msg):
        QMessageBox.critical(self, "Capture Error", msg)
        # Could handle partial-run logic here

    def _on_finished(self):
        """
        Called when the controller signals that capture/analysis is done.
        """
        self.tuning_panel.btn_start.setEnabled(True)
        self.tuning_panel.btn_stop.setEnabled(False)
        QMessageBox.information(self, "Analysis Complete", "Analysis complete.")

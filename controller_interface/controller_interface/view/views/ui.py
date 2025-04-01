# controller_interface/view/views/ui.py

import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QMessageBox,
    QLabel, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap

# Ensure this import is present so Qt resources are registered:
import controller_interface.resources.resources_rc

from controller_interface.controller.ui_controller import UiController
from controller_interface.view.panels.control import TuningControlPanel
from controller_interface.view.panels.live_data import LiveDataPanel
from controller_interface.view.plots.plot_manager import TuningPlotManager
from controller_interface.view.widgets.themed_button import ThemedButton


class AspectRatioLabel(QLabel):
    """
    A QLabel that automatically scales its pixmap to fit the current size,
    while preserving aspect ratio.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._original_pixmap = None

    def setPixmap(self, pixmap: QPixmap):
        """
        Store the original QPixmap so we can scale it dynamically.
        """
        self._original_pixmap = pixmap
        self._update_scaled_pixmap()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scaled_pixmap()

    def _update_scaled_pixmap(self):
        """
        Scale the original pixmap to fit this label's current size,
        preserving aspect ratio.
        """
        if self._original_pixmap is None:
            return

        label_size = self.size()
        scaled = self._original_pixmap.scaled(
            label_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        super().setPixmap(scaled)


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

        # We'll store data_root/test_name here for the final message
        self.current_data_root = None
        self.current_test_name = None

        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        hbox_main = QHBoxLayout()

        # -----------------------
        # Left column
        # -----------------------
        left_vbox = QVBoxLayout()
        left_vbox.setAlignment(Qt.AlignTop)

        # Tuning Panel
        self.tuning_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        left_vbox.addWidget(self.tuning_panel, 0, Qt.AlignTop)

        # Live Data Panel
        self.live_data_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        left_vbox.addWidget(self.live_data_panel, 0, Qt.AlignTop)

        # Optional: keep them pinned at the top
        left_vbox.addStretch(1)

        # Logo label
        self.lbl_logo = AspectRatioLabel()
        self.lbl_logo.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        self.lbl_logo.setAlignment(Qt.AlignCenter)

        pixmap = QPixmap(":/salvus_full_logo_color.png")
        if pixmap.isNull():
            self.lbl_logo.setText("Logo not found")
        else:
            self.lbl_logo.setPixmap(pixmap)

        left_vbox.addWidget(self.lbl_logo, 0, Qt.AlignCenter)

        # Another stretch below
        left_vbox.addStretch(1)

        # Left container
        left_container = QWidget()
        left_container.setLayout(left_vbox)
        # "Maximum" horizontally so the column doesn't expand beyond needed
        left_container.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        hbox_main.addWidget(left_container)

        # -----------------------
        # Right column (plots)
        # -----------------------
        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        self.tuning_plot_manager = TuningPlotManager(plot_layout)

        plot_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        hbox_main.addWidget(plot_container)

        main_layout.addLayout(hbox_main)

        # Bottom row: Home button
        bottom_row = QHBoxLayout()
        bottom_row.addStretch(1)
        self.btn_home = ThemedButton("Home", is_dark=True)
        self.btn_home.clicked.connect(self._on_home_clicked)
        bottom_row.addWidget(self.btn_home)
        main_layout.addLayout(bottom_row)

        self.setLayout(main_layout)

        # Connect signals
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
        fluid_density = self.tuning_panel.get_fluid_density()

        # Store these for reference in _on_finished
        self.current_data_root = data_root
        self.current_test_name = test_name

        self.controller.start_capture(port, baud, data_root, test_name, time_window, fluid_density)

        # Initialize local plot
        self.tuning_plot_manager.start_run()
        self.tuning_plot_manager.set_time_window(time_window)
        self.start_time = time.time()

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
        if self.start_time is not None:
            elapsed = time.time() - self.start_time
            self.tuning_plot_manager.update_data(data_dict, elapsed)

        flow_val_ml_min = float(data_dict.get("flow", 0.0))
        setpt = float(data_dict.get("setpt", 0.0))
        temp = float(data_dict.get("temp", 0.0))
        volt = float(data_dict.get("volt", 0.0))
        bubble_bool = bool(data_dict.get("bubble", False))
        total_flow_ml = self.controller.flow_tracker.get_total_volume_ml()

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

    def _on_finished(self):
        """
        Called when the controller signals that capture/analysis is done.
        We'll enable the Start button, disable the Stop button, and show
        more specific info in the message box.
        """
        self.tuning_panel.btn_start.setEnabled(True)
        self.tuning_panel.btn_stop.setEnabled(False)

        # Calculate elapsed time
        elapsed_time = 0.0
        if self.start_time is not None:
            elapsed_time = time.time() - self.start_time

        # Get total volume from the flow tracker (if available)
        total_flow_ml = 0.0
        if hasattr(self.controller, 'flow_tracker'):
            total_flow_ml = self.controller.flow_tracker.get_total_volume_ml()

        # Retrieve the test name / data root we stored in _on_start_clicked
        test_name = self.current_test_name or "untitled"
        data_root = self.current_data_root or "(unknown)"

        # Compose a more informative message
        msg = (
            "Analysis complete.\n\n"
            f"Test Name: {test_name}\n"
            f"Data Directory: {data_root}\n"
            f"Elapsed Time: {elapsed_time:.2f} seconds\n"
            f"Total Flow: {total_flow_ml:.2f} mL\n"
        )

        QMessageBox.information(self, "Analysis Complete", msg)

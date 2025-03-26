import os
import sys
import time
import getpass
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QMessageBox,
    QLabel, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap

from controller_interface.core.serial_worker import SerialWorker
from controller_interface.core.flow_volume_tracker import FlowVolumeTracker
from controller_interface.core.run_manager import RunManager
from controller_interface.gui.panels.tuning_control_panel import TuningControlPanel
from controller_interface.gui.panels.live_data_panel import LiveDataPanel
from controller_interface.gui.plots.tuning_plot_manager import TuningPlotManager
from controller_interface.gui.widgets.themed_button import ThemedButton


def resource_path(relative_path: str) -> str:
    """
    Returns the absolute path to a resource. Works for dev environments
    and for PyInstaller bundles, which use a temp folder with _MEIPASS.
    If you used `--add-data="SRC;resources"` in PyInstaller,
    then your file is in "_MEIPASS/resources".
    """
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS  # type: ignore
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)


class PidTuningView(QWidget):
    """
    A QWidget for advanced PID monitoring and data logging.
    - Always runs post-analysis at the end of capture.
    - Logs extended columns (pGain, iGain, dGain, etc.) to CSV.
    - Updates LiveDataPanel for real-time flow, setpt, PID terms, etc.
    - Includes a userStable toggle from TuningControlPanel.
    - Passes user-selected fluidDensity and final flow volume to post-analysis.
    """

    goHomeSignal = pyqtSignal()  # for navigating back home

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings

        # Thread & run manager references
        self.serial_thread = None
        self.run_manager = None
        self.start_time = None

        # Track on->off transitions
        self.last_on_state = None

        # Local bool for userStable
        self.data_is_stable = False

        # Flow volume (no JSON persistence)
        self.flow_tracker = FlowVolumeTracker()

        # Panels
        self.tuning_panel = TuningControlPanel(settings=self.settings)
        self.live_data_panel = LiveDataPanel()

        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        # Top-level layout: a vertical layout
        main_layout = QVBoxLayout(self)

        # ------------------------------------------------------------------
        # Main content area: a horizontal layout
        #   Left side: vertical layout with:
        #       1) TuningControlPanel
        #       2) LiveDataPanel
        #       3) A "logo container" that fills leftover vertical space.
        #   Right side: TuningPlotManager occupying the rest of the width.
        # ------------------------------------------------------------------
        hbox_main = QHBoxLayout()

        # -- LEFT COLUMN --
        left_vbox = QVBoxLayout()

        # 1) TuningControlPanel
        left_vbox.addWidget(self.tuning_panel, stretch=0)

        # 2) LiveDataPanel
        left_vbox.addWidget(self.live_data_panel, stretch=0)

        #
        # 3) "Logo container" that expands to fill leftover space
        #
        logo_container = QVBoxLayout()
        # Add 30px left/right margin, 125px top/bottom (adjust as you like)
        logo_container.setContentsMargins(30, 125, 30, 125)

        self.lbl_logo = QLabel()
        # Scale image to fit
        self.lbl_logo.setScaledContents(True)
        # "Ignored" => can shrink/grow with the container
        self.lbl_logo.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        # Build the path to the logo. 
        # NOTE: If you used --add-data="src\controller_interface\resources\salvus_full_logo_color.png;resources"
        # then the file is in "resources/salvus_full_logo_color.png" at runtime
        # inside the PyInstaller bundle folder.
        logo_path = resource_path("resources/salvus_full_logo_color.png")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            self.lbl_logo.setPixmap(pixmap)
        else:
            self.lbl_logo.setText("Logo not found")
            print(f"[DEBUG] Could not load logo at: {logo_path}")

        logo_container.addWidget(self.lbl_logo)

        # Add the container w/ stretch=1, so it fills leftover space
        left_vbox.addLayout(logo_container, stretch=1)

        # Put the left_vbox into a QWidget and add it
        left_container = QWidget()
        left_container.setLayout(left_vbox)
        # The entire left column can have a smaller stretch factor if you want
        hbox_main.addWidget(left_container, stretch=1)

        # -- RIGHT COLUMN: real-time plot --
        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        self.tuning_plot_manager = TuningPlotManager(plot_layout)
        hbox_main.addWidget(plot_container, stretch=9)

        # Add the entire hbox_main (left+right) to main_layout
        main_layout.addLayout(hbox_main)

        # ------------------------------------------------------------------
        # Bottom row: "Home" button
        # ------------------------------------------------------------------
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

    # ----------------------------------------------------------------
    # Loading Settings
    # ----------------------------------------------------------------
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

    # ----------------------------------------------------------------
    # Saving Settings
    # ----------------------------------------------------------------
    def _save_settings(self):
        if not self.settings:
            return
        self.settings.setValue("tuning_last_port", self.tuning_panel.get_port())
        self.settings.setValue("tuning_last_baud", self.tuning_panel.get_baud())
        self.settings.setValue("tuning_time_window", self.tuning_panel.get_time_window())
        self.tuning_panel.save_settings()

    # ---------------------------------------------------
    # Navigation
    # ---------------------------------------------------
    def _on_home_clicked(self):
        self.goHomeSignal.emit()

    # ---------------------------------------------------
    # Start/Stop signals
    # ---------------------------------------------------
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
        self._start_capture(port, baud, time_window)

    def _on_stop_clicked(self):
        self._stop_capture()

    # ---------------------------------------------------
    # Stability toggling
    # ---------------------------------------------------
    def _on_stability_changed(self, stable: bool):
        """
        Called whenever user toggles "Mark Data as Stable" in TuningControlPanel.
        We store it in a local boolean to write to the CSV each row.
        """
        print(f"[DEBUG] userStable toggled => {stable}")
        self.data_is_stable = stable

    # ---------------------------------------------------
    # Capture logic
    # ---------------------------------------------------
    def _start_capture(self, port, baud, time_window):
        if self.serial_thread:
            QMessageBox.information(self, "PID", "Already capturing data.")
            return

        data_root = self.tuning_panel.get_data_root()
        if not data_root:
            QMessageBox.warning(self, "No Data Dir", "Please pick a data directory.")
            return

        test_name = self.tuning_panel.get_test_name() or "untitled"
        user_name = getpass.getuser()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.run_manager = RunManager(data_root)
        self.run_manager.create_run_folders(test_name, user_name, timestamp)
        self.run_manager.open_csv(test_name, user_name, timestamp)

        self.tuning_plot_manager.start_run()
        self.tuning_plot_manager.set_time_window(time_window)

        self.serial_thread = SerialWorker(port, baud)
        self.serial_thread.signals.new_data.connect(self._on_new_data)
        self.serial_thread.signals.finished.connect(self._on_finished)
        self.serial_thread.signals.error.connect(self._on_error)
        self.serial_thread.start()

        self.start_time = time.time()

        self.tuning_panel.btn_start.setEnabled(False)
        self.tuning_panel.btn_stop.setEnabled(True)

        QMessageBox.information(
            self,
            "Capture",
            f"Started streaming on {port} @ {baud} (time={time_window}s)\n"
            f"Logging to: {self.run_manager.get_run_folder()}"
        )

    def _stop_capture(self):
        if self.serial_thread:
            self.serial_thread.stop()

    def _on_new_data(self, data_dict):
        # Possibly handle on->off transitions
        on_state = data_dict.get("on", None)
        if self.last_on_state is False and on_state is True:
            self.flow_tracker.reset_volume()

        # Flow is mL/min from the sensor
        flow_val_ml_min = float(data_dict.get("flow", 0.0))
        self.flow_tracker.update_volume(flow_val_ml_min)

        # If logging to CSV
        if self.run_manager:
            row = [
                data_dict.get("timeMs", 0),
                flow_val_ml_min,
                data_dict.get("setpt", 0.0),
                data_dict.get("temp", 0.0),
                data_dict.get("bubble", False),
                data_dict.get("volt", 0.0),
                data_dict.get("on", False),
                data_dict.get("errorPct", 0.0),
                data_dict.get("pidOut", 0.0),
                data_dict.get("P", 0.0),
                data_dict.get("I", 0.0),
                data_dict.get("D", 0.0),
                data_dict.get("pGain", 0.0),
                data_dict.get("iGain", 0.0),
                data_dict.get("dGain", 0.0),
                data_dict.get("filteredErr", 0.0),
                data_dict.get("currentAlpha", 0.0),
                self.flow_tracker.get_total_volume_ml(),
                self.data_is_stable
            ]
            self.run_manager.write_csv_row(row)

        # Update the plot
        elapsed = time.time() - self.start_time if self.start_time else 0.0
        self.tuning_plot_manager.update_data(data_dict, elapsed)

        # Update the live data panel
        total_flow_ml = self.flow_tracker.get_total_volume_ml()
        self.live_data_panel.update_data(
            setpt_val=float(data_dict.get("setpt", 0.0)),
            flow_val=flow_val_ml_min,
            temp_val=float(data_dict.get("temp", 0.0)),
            volt_val=float(data_dict.get("volt", 0.0)),
            bubble_bool=bool(data_dict.get("bubble", False)),
            p_val=float(data_dict.get("P", 0.0)),
            i_val=float(data_dict.get("I", 0.0)),
            d_val=float(data_dict.get("D", 0.0)),
            pid_out_val=float(data_dict.get("pidOut", 0.0)),
            error_pct=data_dict.get("errorPct", None),
            on_state=on_state,
            mode_val=data_dict.get("mode", None),
            p_gain=data_dict.get("pGain", None),
            i_gain=data_dict.get("iGain", None),
            d_gain=data_dict.get("dGain", None),
            filtered_err=data_dict.get("filteredErr", None),
            current_alpha=data_dict.get("currentAlpha", None),
            total_flow_ml=total_flow_ml
        )

        self.last_on_state = on_state

    def _on_finished(self):
        if self.run_manager:
            folder_path = self.run_manager.get_run_folder()
            self.run_manager.close_csv()

            # Grab user-selected density
            fluid_density = self.tuning_panel.get_fluid_density()
            final_flow = self.flow_tracker.get_total_volume_ml()

            # Pass both fluid_density and total_flow into run_post_analysis
            self.run_manager.run_post_analysis(
                fluid_density=fluid_density,
                total_flow=final_flow
            )

            QMessageBox.information(
                self,
                "Analysis Complete",
                f"Analysis complete.\nResults in:\n{folder_path}"
            )
            self.run_manager = None

        if self.serial_thread:
            self.serial_thread = None

        self.tuning_panel.btn_start.setEnabled(True)
        self.tuning_panel.btn_stop.setEnabled(False)

    def _on_error(self, msg):
        QMessageBox.critical(self, "Capture Error", msg)
        self._on_finished()

import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QMessageBox,
    QSplitter, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal

from controller_interface.core.serial_worker import SerialWorker
from controller_interface.core.flow_volume_tracker import FlowVolumeTracker
from controller_interface.gui.panels.tuning_control_panel import TuningControlPanel
from controller_interface.gui.panels.live_data_panel import LiveDataPanel
from controller_interface.gui.plots.tuning_plot_manager import TuningPlotManager
from controller_interface.gui.widgets.themed_button import ThemedButton

class PidTuningView(QWidget):
    """
    A QWidget for advanced PID monitoring.

    This version:
      - Resets volume each time the device transitions from OFF -> ON.
      - Leaves volume unchanged when the device goes from ON -> OFF.
      - Device flow is in mL/min, but FlowVolumeTracker uses liters internally.
    """

    goHomeSignal = pyqtSignal()  # for returning to Home

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.serial_thread = None
        self.start_time = None

        # Keep track of the last known on/off state
        # None means we haven't received any data yet
        self.last_on_state = None

        # FlowVolumeTracker: stores volume internally in liters
        self.flow_tracker = FlowVolumeTracker(data_file="flow_volume.json")

        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ========== TOP CONTAINER: Tuning + Live Data ==========
        top_container = QWidget()
        top_hbox = QHBoxLayout(top_container)
        top_hbox.setContentsMargins(0, 0, 0, 0)

        self.tuning_panel = TuningControlPanel()
        self.live_data_panel = LiveDataPanel()

        top_hbox.addWidget(self.tuning_panel, stretch=2)
        top_hbox.addWidget(self.live_data_panel, stretch=1)

        top_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        splitter.addWidget(top_container)

        # ========== PLOT CONTAINER ==========
        plot_container = QWidget()
        plot_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        plot_layout = QVBoxLayout(plot_container)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        self.tuning_plot_manager = TuningPlotManager(plot_layout)
        splitter.addWidget(plot_container)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 7)

        main_layout.addWidget(splitter)

        # ========== BOTTOM ROW: Home Button ==========
        bottom_row = QHBoxLayout()
        bottom_row.addStretch(1)
        self.btn_home = ThemedButton("Home", is_dark=True)
        self.btn_home.clicked.connect(self._on_home_clicked)
        bottom_row.addWidget(self.btn_home)
        main_layout.addLayout(bottom_row)

        self.setLayout(main_layout)

        # Connect TuningControlPanel signals
        self.tuning_panel.startSignal.connect(self._on_start_clicked)
        self.tuning_panel.stopSignal.connect(self._on_stop_clicked)

    # ------------------- Load/Save QSettings -------------------
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

    def _save_settings(self):
        if not self.settings:
            return
        self.settings.setValue("tuning_last_port", self.tuning_panel.get_port())
        self.settings.setValue("tuning_last_baud", self.tuning_panel.get_baud())
        self.settings.setValue("tuning_time_window", self.tuning_panel.get_time_window())

    # ------------------- Start/Stop Signals -------------------
    def _on_start_clicked(self):
        """Called when TuningControlPanel emits startSignal."""
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
        """Called when TuningControlPanel emits stopSignal."""
        self._stop_capture()

    # ------------------- Navigation -------------------
    def _on_home_clicked(self):
        self.goHomeSignal.emit()

    # ------------------- Start/Stop Capture Logic -------------------
    def _start_capture(self, port, baud, time_window):
        if self.serial_thread is not None:
            QMessageBox.information(self, "PID", "Already capturing data.")
            return

        self.tuning_plot_manager.start_run()
        self.tuning_plot_manager.set_time_window(time_window)

        self.serial_thread = SerialWorker(port, baud)
        self.serial_thread.signals.new_data.connect(self._on_new_data)
        self.serial_thread.signals.finished.connect(self._on_finished)
        self.serial_thread.signals.error.connect(self._on_error)
        self.serial_thread.start()

        self.start_time = time.time()

        # Toggle button states
        self.tuning_panel.btn_start.setEnabled(False)
        self.tuning_panel.btn_stop.setEnabled(True)

        QMessageBox.information(
            self, "Capture",
            f"Started streaming on {port} @ {baud} (time window={time_window}s)."
        )

    def _stop_capture(self):
        if self.serial_thread:
            self.serial_thread.stop()
        # We'll re-enable start in _on_finished()

    # ------------------- Thread Callbacks -------------------
    def _on_new_data(self, data_dict):
        """
        Called when SerialWorker emits 'new_data'.

        The device's flow is in mL/min, but FlowVolumeTracker uses liters internally.
        We only reset volume when the device transitions from OFF -> ON.
        """

        # 1) Update the plot
        elapsed = time.time() - self.start_time if self.start_time else 0.0
        self.tuning_plot_manager.update_data(data_dict, elapsed)

        # 2) Grab on_state from data (True => on, False => off)
        on_state = data_dict.get("on", None)

        # 3) If device transitions from OFF -> ON, reset volume
        if self.last_on_state is False and on_state is True:
            self.flow_tracker.reset_volume()

        # 4) Parse flow in mL/min, convert to L/min
        flow_val_ml_min = float(data_dict.get("flow", 0.0))
        flow_val_l_min = flow_val_ml_min / 1000.0

        # 5) Update volume in liters
        self.flow_tracker.update_volume(flow_val_l_min)

        # 6) Retrieve total volume in liters, convert to mL
        total_volume_liters = self.flow_tracker.get_total_volume_ml()
        total_volume_ml = total_volume_liters * 1000.0

        # 7) Extract other fields
        setpt_val = float(data_dict.get("setpt", 0.0))
        temp_val  = float(data_dict.get("temp",  0.0))
        volt_val  = float(data_dict.get("volt",  0.0))
        bubble    = bool(data_dict.get("bubble", False))
        p_val     = float(data_dict.get("P",     0.0))
        i_val     = float(data_dict.get("I",     0.0))
        d_val     = float(data_dict.get("D",     0.0))
        out_val   = float(data_dict.get("pidOut",0.0))

        error_pct = data_dict.get("errorPct", None)
        mode_val  = data_dict.get("mode", None)
        p_gain    = data_dict.get("pGain", None)
        i_gain    = data_dict.get("iGain", None)
        d_gain    = data_dict.get("dGain", None)
        filt_err  = data_dict.get("filteredErr", None)
        alpha_val = data_dict.get("currentAlpha", None)

        # 8) Update LiveDataPanel
        self.live_data_panel.update_data(
            flow_val=flow_val_ml_min,
            total_flow_ml=total_volume_ml,
            setpt_val=setpt_val,
            temp_val=temp_val,
            volt_val=volt_val,
            bubble_bool=bubble,
            p_val=p_val,
            i_val=i_val,
            d_val=d_val,
            pid_out_val=out_val,
            error_pct=error_pct,
            on_state=on_state,
            mode_val=mode_val,
            p_gain=p_gain,
            i_gain=i_gain,
            d_gain=d_gain,
            filtered_err=filt_err,
            current_alpha=alpha_val
        )

        # 9) Remember on_state for next iteration
        self.last_on_state = on_state

    def _on_finished(self):
        self.serial_thread = None
        self.tuning_panel.btn_start.setEnabled(True)
        self.tuning_panel.btn_stop.setEnabled(False)
        QMessageBox.information(self, "Capture", "Data streaming stopped.")

    def _on_error(self, msg):
        QMessageBox.critical(self, "Capture Error", msg)
        self._on_finished()

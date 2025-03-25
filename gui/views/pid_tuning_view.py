import time
import getpass
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QMessageBox,
    QSplitter, QSizePolicy, QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSignal

from controller_interface.core.serial_worker import SerialWorker
from controller_interface.core.flow_volume_tracker import FlowVolumeTracker
from controller_interface.core.run_manager import RunManager
from controller_interface.gui.panels.tuning_control_panel import TuningControlPanel
from controller_interface.gui.panels.live_data_panel import LiveDataPanel
from controller_interface.gui.plots.tuning_plot_manager import TuningPlotManager
from controller_interface.gui.widgets.themed_button import ThemedButton


class PidTuningView(QWidget):
    """
    A QWidget for advanced PID monitoring and data logging.

    - Resets volume each time the device transitions from OFF -> ON.
    - Leaves volume unchanged when device goes from ON -> OFF.
    - Flow is in mL/min, but FlowVolumeTracker uses liters internally.
    - Uses RunManager to create a subfolder and log data to CSV for each run.
    """

    goHomeSignal = pyqtSignal()  # Signal to navigate back home

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings

        # Thread & logging
        self.serial_thread = None
        self.run_manager = None

        # Time tracking
        self.start_time = None

        # Last on/off state (None means unknown yet)
        self.last_on_state = None

        # Flow volume tracking (internally stores liters)
        self.flow_tracker = FlowVolumeTracker(data_file="flow_volume.json")

        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        """
        Build the layout:
          - Top half: TuningControlPanel + LiveDataPanel (side by side).
          - Bottom half: Plot area in a QSplitter.
          - Row with "Home" button at the very bottom.
        """
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ========== TOP: Tuning panel + Live data ==========

        top_container = QWidget()
        top_hbox = QHBoxLayout(top_container)
        top_hbox.setContentsMargins(0, 0, 0, 0)

        self.tuning_panel = TuningControlPanel()   # Contains get_data_root() if you implemented it
        self.live_data_panel = LiveDataPanel()

        top_hbox.addWidget(self.tuning_panel, stretch=2)
        top_hbox.addWidget(self.live_data_panel, stretch=1)

        top_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        splitter.addWidget(top_container)

        # ========== BOTTOM: Plot container ==========

        plot_container = QWidget()
        plot_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        plot_layout = QVBoxLayout(plot_container)
        plot_layout.setContentsMargins(0, 0, 0, 0)

        self.tuning_plot_manager = TuningPlotManager(plot_layout)
        splitter.addWidget(plot_container)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 7)

        main_layout.addWidget(splitter)

        # ========== Very Bottom: "Home" button ==========

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
        """
        Load persistent settings for port, baud, time window, etc.
        Adjust if you also want to load data_root or test_name.
        """
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

        # If TuningControlPanel has a data root line, you can load:
        # saved_data_root = self.settings.value("tuning_data_root", "")
        # if saved_data_root:
        #     self.tuning_panel.set_data_root(saved_data_root)

    def _save_settings(self):
        """
        Save user selections to QSettings.
        """
        if not self.settings:
            return
        self.settings.setValue("tuning_last_port", self.tuning_panel.get_port())
        self.settings.setValue("tuning_last_baud", self.tuning_panel.get_baud())
        self.settings.setValue("tuning_time_window", self.tuning_panel.get_time_window())

        # If TuningControlPanel has a data root or test name:
        # if self.tuning_panel.get_data_root():
        #     self.settings.setValue("tuning_data_root", self.tuning_panel.get_data_root())

    # ------------------- Start/Stop Signals -------------------
    def _on_start_clicked(self):
        """
        Called when TuningControlPanel emits startSignal.
        """
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
        """
        Called when TuningControlPanel emits stopSignal.
        """
        self._stop_capture()

    # ------------------- Navigation -------------------
    def _on_home_clicked(self):
        self.goHomeSignal.emit()

    # ------------------- Start/Stop Capture + Logging -------------------
    def _start_capture(self, port, baud, time_window):
        """
        Initiate capture:
          - Prompt for data root (if not set).
          - Prompt for test name.
          - Create a subfolder (via RunManager).
          - Start the serial thread + plotting.
        """
        if self.serial_thread:
            QMessageBox.information(self, "PID", "Already capturing data.")
            return

        # 1) Get data directory from panel
        if hasattr(self.tuning_panel, "get_data_root"):
            data_root = self.tuning_panel.get_data_root()
        else:
            data_root = None

        if not data_root:
            QMessageBox.warning(self, "No Data Dir", "Please pick a data directory first.")
            return

        # 2) Prompt for test name
        last_test_name = self.settings.value("tuning_test_name", "untitled") if self.settings else "untitled"
        test_name, ok = QInputDialog.getText(
            self, "Test Name", "Enter a test name:", text=last_test_name
        )
        if not ok or not test_name.strip():
            test_name = "untitled"
        else:
            # save to QSettings so it defaults next time
            if self.settings:
                self.settings.setValue("tuning_test_name", test_name.strip())

        # 3) Create folder + open CSV
        user_name = getpass.getuser()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.run_manager = RunManager(data_root)
        self.run_manager.create_run_folders(test_name, user_name, timestamp)
        self.run_manager.open_csv(test_name, user_name, timestamp)

        # 4) Setup the Plot
        self.tuning_plot_manager.start_run()
        self.tuning_plot_manager.set_time_window(time_window)

        # 5) Serial Worker
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
            self,
            "Capture",
            f"Started streaming on {port} @ {baud} (time window={time_window}s)\n"
            f"Logging to: {self.run_manager.get_run_folder()}"
        )

    def _stop_capture(self):
        if self.serial_thread:
            self.serial_thread.stop()

    # ------------------- Thread Callbacks -------------------
    def _on_new_data(self, data_dict):
        """
        Called whenever SerialWorker emits 'new_data'.
        We log to CSV, update plots, track volume, etc.
        """

        # 1) Log row to CSV if run_manager is active
        if self.run_manager:
            row = [
                data_dict.get("timeMs", 0),
                data_dict.get("flow", 0.0),
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
            ]
            self.run_manager.write_csv_row(row)

        # 2) Plot update
        elapsed = time.time() - self.start_time if self.start_time else 0.0
        self.tuning_plot_manager.update_data(data_dict, elapsed)

        # 3) Volume tracking
        on_state = data_dict.get("on", None)
        if self.last_on_state is False and on_state is True:
            self.flow_tracker.reset_volume()

        flow_val_ml_min = float(data_dict.get("flow", 0.0))
        flow_val_l_min = flow_val_ml_min / 1000.0
        self.flow_tracker.update_volume(flow_val_l_min)

        total_volume_liters = self.flow_tracker.get_total_volume_ml()
        total_volume_ml = total_volume_liters * 1000.0

        # 4) Extract other fields for the live data panel
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

        # 5) Update live data panel
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

        # Store the last on_state
        self.last_on_state = on_state

    def _on_finished(self):
        """
        Called when the serial thread is done (either normally or due to error).
        Close the CSV if run_manager is active, do analysis if desired, etc.
        """
        if self.run_manager:
            self.run_manager.close_csv()

            # If you want post-analysis:
            # stable_w = self.tuning_panel.get_stable_window()  # or however you store it
            # thresh   = self.tuning_panel.get_stable_threshold()
            # fluid_d  = 1.0  # or a spinbox for fluid density
            # self.run_manager.run_post_analysis(stable_w, thresh, fluid_d)
            #
            # run_folder = self.run_manager.get_run_folder()
            # QMessageBox.information(self, "Analysis Complete",
            #                         f"Results in:\n{run_folder}")

            self.run_manager = None

        # Clean up
        self.serial_thread = None
        self.tuning_panel.btn_start.setEnabled(True)
        self.tuning_panel.btn_stop.setEnabled(False)

        QMessageBox.information(self, "Capture", "Data streaming stopped.")

    def _on_error(self, msg):
        """
        Called if the serial thread hits an error (e.g. port error).
        """
        QMessageBox.critical(self, "Capture Error", msg)
        self._on_finished()

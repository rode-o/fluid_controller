import os
import time
import getpass
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QMessageBox,
    QInputDialog, QFileDialog, QSplitter, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal

# Core & panels
from controller_interface.core.run_manager import RunManager
from controller_interface.core.serial_worker import SerialWorker
from controller_interface.gui.panels.controls_panel import ControlsPanel
from controller_interface.gui.panels.live_data_panel import LiveDataPanel
from controller_interface.gui.plots.plot_manager import PlotManager

# Minimal ThemedButton (no paintEvent override)
from controller_interface.gui.widgets.themed_button import ThemedButton


class DataStreamerView(QWidget):
    """
    A QWidget for real-time data streaming, placed inside a QStackedWidget.

    Layout approach:
      - A QSplitter (vertical) divides:
         (A) Top container: ControlsPanel + LiveDataPanel (3:1 side-by-side).
         (B) PlotManager area.
      - A bottom row (outside splitter) has a "Home" button.
      - This allows the user to drag-resize the vertical splitter as needed.

    The 'live_data_panel' receives data from on_new_data(...).
    """

    goHomeSignal = pyqtSignal()  # Emitted when user clicks "Home"

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings  # QSettings from MainWindow

        # runtime references
        self.run_manager   = None
        self.serial_thread = None
        self.start_time    = None

        # UI elements
        self.controls_panel  = None
        self.live_data_panel = None
        self.plot_manager    = None
        self.btn_home        = None

        self._init_ui()

    def _init_ui(self):
        """
        Build the layout with a QSplitter for top/bottom sections:
          top => (ControlsPanel + LiveDataPanel)
          bottom => PlotManager
        And then a bottom row for the Home button.
        """
        # Main vertical layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # Create a vertical splitter
        splitter = QSplitter(Qt.Vertical)
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ------------------- TOP WIDGET: ControlsPanel + LiveDataPanel -------------------
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        self.controls_panel = ControlsPanel(self.settings)
        self.live_data_panel = LiveDataPanel()

        # Place controls and live data side-by-side in a 3:1 ratio
        top_layout.addWidget(self.controls_panel, stretch=3)
        top_layout.addWidget(self.live_data_panel, stretch=1)

        splitter.addWidget(top_widget)

        # ------------------- BOTTOM WIDGET: PlotManager -------------------
        # If PlotManager is a "widget-based" approach, we can embed it in another widget:
        plot_widget = QWidget()
        plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        plot_layout = QVBoxLayout(plot_widget)
        plot_layout.setContentsMargins(0, 0, 0, 0)

        # PlotManager expects a layout parent; pass in plot_layout
        self.plot_manager = PlotManager(plot_layout)
        splitter.addWidget(plot_widget)

        # Assign stretch factors so top is smaller by default
        # e.g. top=3, bottom=6 => top ~ 1/3, bottom ~ 2/3 initially
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 6)

        # Add the splitter to our main layout
        self.main_layout.addWidget(splitter)

        # ------------------- BOTTOM ROW: "Home" button -------------------
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch(1)

        self.btn_home = ThemedButton("Home", is_dark=True)
        self.btn_home.clicked.connect(self._on_home_clicked)
        bottom_layout.addWidget(self.btn_home)

        self.main_layout.addLayout(bottom_layout)

        # Connect signals from ControlsPanel
        self.controls_panel.startCaptureSignal.connect(self.start_capture)
        self.controls_panel.stopCaptureSignal.connect(self.stop_capture)
        self.controls_panel.changeDirSignal.connect(self.change_save_dir)

    # --------------------------------------------------------------------------
    # "Home" button
    # --------------------------------------------------------------------------
    def _on_home_clicked(self):
        self.goHomeSignal.emit()

    # --------------------------------------------------------------------------
    # Change data directory
    # --------------------------------------------------------------------------
    def change_save_dir(self):
        new_dir = QFileDialog.getExistingDirectory(self, "Select Data Directory", os.getcwd())
        if new_dir:
            self.settings.setValue("data_root", new_dir)
            self.controls_panel.set_data_root(new_dir)

    # --------------------------------------------------------------------------
    # Start capture
    # --------------------------------------------------------------------------
    def start_capture(self):
        data_root = self.settings.value("data_root", None)
        if not data_root:
            self.change_save_dir()
            data_root = self.settings.value("data_root", None)
            if not data_root:
                QMessageBox.warning(self, "No Data Root", "You must set a data directory.")
                return

        # Prompt for test name
        last_test_name = self.settings.value("last_test_name", "untitled")
        test_name, ok = QInputDialog.getText(
            self, "Test Name", "Enter a test name:", text=last_test_name
        )
        if not ok or not test_name.strip():
            test_name = "untitled"
        else:
            self.settings.setValue("last_test_name", test_name.strip())

        user_name = getpass.getuser()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create RunManager
        self.run_manager = RunManager(data_root)
        self.run_manager.create_run_folders(test_name, user_name, timestamp)
        self.run_manager.open_csv(test_name, user_name, timestamp)

        # Save all control panel settings
        self.controls_panel.save_settings()

        # Retrieve Plot Window from Controls Panel
        time_window = float(self.controls_panel.time_window_spin.value())
        self.plot_manager.set_time_window(time_window)

        # Reset the plots for a new run
        self.plot_manager.start_run()
        self.start_time = time.time()

        # Launch SerialWorker
        selected_port = self.controls_panel.get_port()
        if selected_port == "No ports found":
            QMessageBox.warning(self, "No Port", "No valid port.")
            return

        try:
            baud = int(self.controls_panel.get_baud())
        except ValueError:
            QMessageBox.warning(self, "Invalid Baud", "Not an integer.")
            return

        self.controls_panel.enable_start(False)
        self.controls_panel.enable_stop(True)

        self.serial_thread = SerialWorker(selected_port, baud)
        self.serial_thread.signals.new_data.connect(self.on_new_data)
        self.serial_thread.signals.finished.connect(self.on_serial_finished)
        self.serial_thread.signals.error.connect(self.on_serial_error)
        self.serial_thread.start()

        QMessageBox.information(self, "Capture Started",
                                f"Logging to: {self.run_manager.get_run_folder()}")

    # --------------------------------------------------------------------------
    # Stop capture
    # --------------------------------------------------------------------------
    def stop_capture(self):
        if self.serial_thread:
            self.serial_thread.stop()

    def on_serial_error(self, msg):
        QMessageBox.critical(self, "Serial Error", msg)
        self.on_serial_finished()

    def on_serial_finished(self):
        """
        Called when the serial thread is done (either normally or due to error).
        Safely handle the run_manager if it exists, and run post-analysis only if
        we actually have a valid run manager.
        """
        if self.run_manager:
            self.run_manager.close_csv()
            QMessageBox.information(self, "Capture Stopped", "Capture finished.")
            self.controls_panel.enable_start(True)
            self.controls_panel.enable_stop(False)
            self.serial_thread = None

            # Run post-analysis
            stable_w = self.controls_panel.stable_window_spin.value()
            thresh   = self.controls_panel.stable_threshold_spin.value()
            fluid_d  = self.controls_panel.fluid_density_spin.value()

            self.run_manager.run_post_analysis(stable_w, thresh, fluid_d)

            run_folder = self.run_manager.get_run_folder()
            QMessageBox.information(self, "Analysis Complete",
                                    f"Results in:\n{run_folder}")

            self.run_manager = None
        else:
            QMessageBox.information(self, "Capture Stopped", "Capture finished.")
            self.controls_panel.enable_start(True)
            self.controls_panel.enable_stop(False)
            self.serial_thread = None

    # --------------------------------------------------------------------------
    # Handle incoming data
    # --------------------------------------------------------------------------
    def on_new_data(self, data_dict):
        """
        Called whenever the serial thread produces new data.
        We log to CSV, update the LiveDataPanel, and feed data to PlotManager.

        'data_dict' might have:
          flow, setpt, temp, volt, bubble, errorPct, pidOut, P, I, D, ...
        """
        # Write row to CSV (if run_manager is open)
        row = [
            data_dict.get("timeMs",    0),
            data_dict.get("flow",      0.0),
            data_dict.get("setpt",     0.0),
            data_dict.get("temp",      0.0),
            data_dict.get("bubble",    False),
            data_dict.get("volt",      0.0),
            data_dict.get("on",        False),
            data_dict.get("errorPct",  0.0),
            data_dict.get("pidOut",    0.0),
            data_dict.get("P",         0.0),
            data_dict.get("I",         0.0),
            data_dict.get("D",         0.0),
        ]
        if self.run_manager:
            self.run_manager.write_csv_row(row)

        # Extract fields for LiveDataPanel
        flow_val    = float(data_dict.get("flow",   0.0))
        setpt_val   = float(data_dict.get("setpt",  0.0))
        temp_val    = float(data_dict.get("temp",   0.0))
        volt_val    = float(data_dict.get("volt",   0.0))
        bubble_bool = bool(data_dict.get("bubble",  False))

        p_val   = float(data_dict.get("P",       0.0))
        i_val   = float(data_dict.get("I",       0.0))
        d_val   = float(data_dict.get("D",       0.0))
        pid_out = float(data_dict.get("pidOut",  0.0))

        error_pct     = data_dict.get("errorPct", None)
        on_state      = data_dict.get("on", None)
        mode_val      = data_dict.get("mode", None)
        p_gain        = data_dict.get("pGain", None)
        i_gain        = data_dict.get("iGain", None)
        d_gain        = data_dict.get("dGain", None)
        filtered_err  = data_dict.get("filtErr", None)
        current_alpha = data_dict.get("alpha", None)
        total_flow_ml = data_dict.get("totalVolume", None)

        # Update LiveDataPanel with the above fields
        self.live_data_panel.update_data(
            setpt_val,
            flow_val,
            temp_val,
            volt_val,
            bubble_bool,
            p_val=p_val,
            i_val=i_val,
            d_val=d_val,
            pid_out_val=pid_out,
            error_pct=error_pct,
            on_state=on_state,
            mode_val=mode_val,
            p_gain=p_gain,
            i_gain=i_gain,
            d_gain=d_gain,
            filtered_err=filtered_err,
            current_alpha=current_alpha,
            total_flow_ml=total_flow_ml
        )

        # Convert device time to local "elapsed_s" for PlotManager
        if self.start_time:
            current_time = time.time()
            elapsed_s = current_time - self.start_time
        else:
            elapsed_s = 0.0

        # Pass data to PlotManager
        self.plot_manager.update_data(data_dict, elapsed_s)

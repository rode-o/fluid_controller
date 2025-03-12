import os
import time
import getpass
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QMessageBox,
    QInputDialog, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal

# Core & panels
from controller_interface.core.run_manager import RunManager
from controller_interface.core.serial_worker import SerialWorker
from controller_interface.gui.panels.controls_panel import ControlsPanel
from controller_interface.gui.panels.live_data_panel import LiveDataPanel
# Make sure plot_manager.py has the updated logic for bubble line + time window
from controller_interface.gui.plots.plot_manager import PlotManager

# Minimal ThemedButton (no paintEvent override)
from controller_interface.gui.widgets.themed_button import ThemedButton

class DataStreamerView(QWidget):
    """
    A QWidget for real-time data streaming. Placed inside a QStackedWidget.
      - Shows flow, setpt, volt, temp, bubble in PlotManager (no PID terms).
      - Displays P, I, D, pidOut in LiveDataPanel.
      - Logs data to CSV but doesn't plot PID terms here.
      - Has a "Home" button at the bottom to return to the home view,
        with dynamic rounding, padding, etc. in resizeEvent.
    """

    goHomeSignal = pyqtSignal()  # Signal emitted when user clicks "Home"

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
        # Main vertical layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # 1) Top row: ControlsPanel + LiveDataPanel side-by-side
        self.top_row = QHBoxLayout()
        self.controls_panel  = ControlsPanel(self.settings)
        self.live_data_panel = LiveDataPanel()

        self.top_row.addWidget(self.controls_panel)
        self.top_row.addWidget(self.live_data_panel)
        # e.g., 3:1 width ratio
        self.top_row.setStretch(0, 3)
        self.top_row.setStretch(1, 1)
        self.main_layout.addLayout(self.top_row)

        # 2) Middle: PlotManager
        self.plot_manager = PlotManager(self.main_layout)  
        # Make sure your 'plot_manager.py' has the bubble + time_window logic

        # 3) Bottom: "Home" button
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
    # Re-sizing logic
    # --------------------------------------------------------------------------
    def resizeEvent(self, event):
        super().resizeEvent(event)

        total_height = self.height()

        # Let's make the top row ~10% of total height
        top_row_height = int(total_height * 0.10)
        self.controls_panel.setFixedHeight(top_row_height)
        self.live_data_panel.setFixedHeight(top_row_height)

        # The PlotManager + bottom button fill the remainder
        # Now handle the Home button
        home_height = max(40, int(total_height * 0.03))

        font_size = max(12, home_height // 2)
        pad_vert = int(home_height * 0.15)
        pad_horz = int(home_height * 0.3)
        corner_radius = home_height // 2

        # Style snippet for the home button
        home_style = f"""
            QPushButton {{
                font-size: {font_size}px;
                padding: {pad_vert}px {pad_horz}px;
                border-radius: {corner_radius}px;
            }}
        """
        self.btn_home.setFixedHeight(home_height)
        self.btn_home.setStyleSheet(self.btn_home.styleSheet() + home_style)

    # --------------------------------------------------------------------------
    # Navigation: "Home" button
    # --------------------------------------------------------------------------
    def _on_home_clicked(self):
        self.goHomeSignal.emit()

    # --------------------------------------------------------------------------
    # Change data directory
    # --------------------------------------------------------------------------
    def change_save_dir(self):
        from PyQt5.QtWidgets import QFileDialog
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

        self.run_manager = RunManager(data_root)
        self.run_manager.create_run_folders(test_name, user_name, timestamp)
        self.run_manager.open_csv(test_name, user_name, timestamp)

        # Save all control panel settings
        self.controls_panel.save_settings()

        # --------------------- Retrieve Plot Window from Controls Panel ---------------------
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

    # --------------------------------------------------------------------------
    # Handle incoming data
    # --------------------------------------------------------------------------
    def on_new_data(self, data_dict):
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
            data_dict.get("D",         0.0)
        ]
        if self.run_manager:
            self.run_manager.write_csv_row(row)

        # Update LiveDataPanel
        flow_val    = float(data_dict.get("flow", 0.0))
        setpt_val   = float(data_dict.get("setpt", 0.0))
        temp_val    = float(data_dict.get("temp",  0.0))
        volt_val    = float(data_dict.get("volt",  0.0))
        bubble_bool = bool(data_dict.get("bubble", False))

        p_val   = float(data_dict.get("P",       0.0))
        i_val   = float(data_dict.get("I",       0.0))
        d_val   = float(data_dict.get("D",       0.0))
        pid_out = float(data_dict.get("pidOut",  0.0))

        self.live_data_panel.update_data(
            setpt_val, flow_val, temp_val, volt_val, bubble_bool,
            p_val, i_val, d_val, pid_out
        )

        # Convert timeMs to "elapsed_s" for PlotManager
        if self.start_time:
            current_time = time.time()
            elapsed_s = current_time - self.start_time
        else:
            elapsed_s = 0.0

        # Pass data to PlotManager, which handles bubble= setpt if True, etc.
        self.plot_manager.update_data(data_dict, elapsed_s)

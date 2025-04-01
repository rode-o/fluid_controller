# controller_interface/controller/ui_controller.py

import time
import getpass
from datetime import datetime
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal

from controller_interface.model.flow_volume_tracker import FlowVolumeTracker
from controller_interface.model.run_manager import RunManager
from controller_interface.model.serial_worker import SerialWorker
from controller_interface.utils.logging_utils import logger

class UiController(QObject):
    """
    Orchestrates capturing data from SerialWorker, logging to CSV with RunManager,
    tracking flow volume, and running post-analysis.
    Emits signals so the UI can respond to events (new data, errors, finished).
    """

    new_data_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.serial_thread: Optional[SerialWorker] = None
        self.run_manager: Optional[RunManager] = None
        self.flow_tracker = FlowVolumeTracker()

        # For tracking userStable
        self.data_is_stable: bool = False

        # For tracking on->off transitions
        self.last_on_state: Optional[bool] = None

        # For timing (when run started)
        self.start_time: Optional[float] = None

        # We'll store fluid density after user picks it in the UI
        self._fluid_density: float = 1.0

    def start_capture(
        self,
        port: str,
        baud: int,
        data_root: str,
        test_name: str,
        time_window: float,
        fluid_density: float
    ) -> None:
        """
        Start capturing from the serial port at (port, baud), 
        create run folders under data_root using test_name, user_name, 
        and a timestamp, and begin logging to CSV.

        fluid_density: the user-selected density from the UI (e.g. 0.977).
        """
        if self.serial_thread:
            logger.warning("Attempted to start capture but already capturing.")
            return

        # Store user fluid density locally
        self._fluid_density = fluid_density

        user_name = getpass.getuser()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Set up RunManager
        self.run_manager = RunManager(data_root)
        self.run_manager.create_run_folders(test_name, user_name, timestamp)
        self.run_manager.open_csv(test_name, user_name, timestamp)
        logger.info("Run folders created and CSV opened for capture.")

        # Start SerialWorker
        self.serial_thread = SerialWorker(port, baud)
        self.serial_thread.signals.new_data.connect(self._on_new_data)
        self.serial_thread.signals.finished.connect(self._on_finished)
        self.serial_thread.signals.error.connect(self._on_error)
        self.serial_thread.start()

        self.start_time = time.time()
        logger.info(f"Started SerialWorker on port={port}, baud={baud}")

    def stop_capture(self) -> None:
        """
        Signal the SerialWorker thread to stop.
        """
        if self.serial_thread:
            logger.info("Stopping capture...")
            self.serial_thread.stop()

    def set_stability(self, stable: bool) -> None:
        """
        Used by the UI to mark data as stable or not.
        Will be stored in CSV rows for each new_data event.
        """
        self.data_is_stable = stable

    def _on_new_data(self, data_dict: dict) -> None:
        """
        Callback when SerialWorker has parsed a new JSON line.
        We update flow volume, write CSV row, then emit new_data_signal.
        """
        on_state = data_dict.get("on", None)
        if self.last_on_state is False and on_state is True:
            self.flow_tracker.reset_volume()
        self.last_on_state = on_state

        # Calculate flow volume
        flow_val_ml_min = float(data_dict.get("flow", 0.0))
        self.flow_tracker.update_volume(flow_val_ml_min)

        # -------------------------------------------------------
        # 1) Compute the new time columns
        # -------------------------------------------------------
        now = time.time()
        abs_time_iso = datetime.fromtimestamp(now).isoformat()
        if self.start_time is not None:
            delta_s = now - self.start_time
        else:
            delta_s = 0.0

        rel_time_ms  = delta_s * 1000.0
        rel_time_sec = delta_s
        rel_time_min = delta_s / 60.0

        # -------------------------------------------------------
        # 2) Build the row in the correct order:
        #    absTimeISO, relTimeMs, relTimeSec, relTimeMin, timeMs, ...
        # -------------------------------------------------------
        row = [
            abs_time_iso,                       # absTimeISO
            rel_time_ms,                        # relTimeMs
            rel_time_sec,                       # relTimeSec
            rel_time_min,                       # relTimeMin
            data_dict.get("timeMs", 0),         # timeMs
            flow_val_ml_min,                    # flow
            data_dict.get("setpt", 0.0),        # setpt
            data_dict.get("temp", 0.0),         # temp
            data_dict.get("bubble", False),     # bubble
            data_dict.get("volt", 0.0),         # volt
            data_dict.get("on", False),         # on
            data_dict.get("errorPct", 0.0),     # errorPct
            data_dict.get("pidOut", 0.0),       # pidOut
            data_dict.get("P", 0.0),            # P
            data_dict.get("I", 0.0),            # I
            data_dict.get("D", 0.0),            # D
            data_dict.get("pGain", 0.0),        # pGain
            data_dict.get("iGain", 0.0),        # iGain
            data_dict.get("dGain", 0.0),        # dGain
            data_dict.get("filteredErr", 0.0),  # filteredErr
            data_dict.get("currentAlpha", 0.0), # currentAlpha
            self.flow_tracker.get_total_volume_ml(),  # totalVolume
            self.data_is_stable                 # userStable
        ]

        # -------------------------------------------------------
        # 3) Write to CSV
        # -------------------------------------------------------
        if self.run_manager:
            self.run_manager.write_csv_row(row)

        # Finally emit the signal for the UI
        self.new_data_signal.emit(data_dict)

    def _on_finished(self) -> None:
        """
        Called when the SerialWorker stops. Closes CSV, does post-analysis,
        then emits finished_signal.
        """
        if self.run_manager:
            folder_path = self.run_manager.get_run_folder()
            self.run_manager.close_csv()

            # Use the fluid_density from user UI, defaulting to 1.0 if not set
            final_flow = self.flow_tracker.get_total_volume_ml()
            self.run_manager.run_post_analysis(
                fluid_density=self._fluid_density,
                total_flow=final_flow
            )
            logger.info(f"Post-analysis done. Results in: {folder_path}")
            self.run_manager = None

        if self.serial_thread:
            self.serial_thread = None

        self.finished_signal.emit()

    def _on_error(self, msg: str) -> None:
        """
        Called if SerialWorker encounters an error.
        We finalize run and emit an error_signal for the UI.
        """
        logger.error(f"SerialWorker error: {msg}")
        self._on_finished()
        self.error_signal.emit(msg)

# controller_interface/model/serial_worker.py

import json
import serial
from threading import Event
from PyQt5.QtCore import QThread, pyqtSignal, QObject

# If you prefer aggregator imports, do:
# from controller_interface import logger
# Otherwise, direct import from utils:
from controller_interface.utils.logging_utils import logger

class SerialWorkerSignals(QObject):
    """
    Signals used by the SerialWorker to communicate with the main GUI or controller.
    """
    new_data = pyqtSignal(dict)  # entire JSON line as a dict
    finished = pyqtSignal()
    error = pyqtSignal(str)


class SerialWorker(QThread):
    """
    Reads lines from a serial port, parses JSON,
    and emits the parsed data via new_data signal.
    """

    def __init__(self, port: str, baud: int, parent=None):
        super().__init__(parent)
        self.port = port
        self.baud = baud
        self.signals = SerialWorkerSignals()
        self.stop_event = Event()
        self.ser = None

    def run(self) -> None:
        """
        Main thread loop that opens the serial port, reads lines, decodes JSON,
        and emits signals for new data, errors, or completion.
        """
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            logger.info(f"Opened serial port {self.port} at {self.baud} baud.")

            while not self.stop_event.is_set():
                line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                if line:
                    try:
                        data = json.loads(line)
                        # ex. {"timeMs":10000,"flow":0.1,"setpt":0.8,"temp":24.5,"bubble":false,"volt":3.2,"on":true}
                        self.signals.new_data.emit(data)
                    except (ValueError, json.JSONDecodeError):
                        # Not valid JSON; ignore or log debug info
                        pass
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.signals.finished.emit()
            logger.info("SerialWorker stopped.")

    def stop(self) -> None:
        """
        Requests the thread to stop by setting an event flag.
        The run() loop checks stop_event and exits gracefully.
        """
        self.stop_event.set()

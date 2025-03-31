# app/core/serial_worker.py

import json
import serial
from threading import Event
from PyQt5.QtCore import QThread, pyqtSignal, QObject

class SerialWorkerSignals(QObject):
    """
    Signals used by the SerialWorker to communicate with the main GUI.
    """
    new_data = pyqtSignal(dict)  # entire JSON line as dict
    finished = pyqtSignal()
    error = pyqtSignal(str)

class SerialWorker(QThread):
    """
    Reads lines from the serial port, parses JSON,
    emits the parsed data as a dict via new_data.
    """
    def __init__(self, port, baud, parent=None):
        super().__init__(parent)
        self.port = port
        self.baud = baud
        self.signals = SerialWorkerSignals()
        self.stop_event = Event()

    def run(self):
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            print(f"[INFO] Opened woot woot {self.port} at {self.baud} baud.")

            while not self.stop_event.is_set():
                line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                if line:
                    try:
                        data = json.loads(line)
                        # ex: {"timeMs":10000,"flow":0.1,"setpt":0.8,"temp":24.5,"bubble":false,"volt":3.2,"on":true}
                        self.signals.new_data.emit(data)
                    except (ValueError, json.JSONDecodeError):
                        pass  # not valid JSON, ignore
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            if hasattr(self, "ser") and self.ser.is_open:
                self.ser.close()
            self.signals.finished.emit()
            print("[INFO] SerialWorker stopped.")

    def stop(self):
        self.stop_event.set()

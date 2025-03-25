# tuning_control_panel.py

import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QDoubleSpinBox
)
from PyQt5.QtCore import pyqtSignal
from controller_interface.gui.widgets.themed_button import ThemedButton

class TuningControlPanel(QGroupBox):
    """
    A QGroupBox for tuning or monitoring controls:
      - Port selection, Refresh button
      - Baud combo
      - Time Window spin box
      - Start / Stop
    
    Now: we no longer toggle the button states in here; 
    we only emit signals so the parent view can do the toggling.
    """

    startSignal = pyqtSignal()
    stopSignal  = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Tuning Control Panel")

        layout = QVBoxLayout(self)

        # Row 1: Port / Refresh
        row1 = QHBoxLayout()
        self.port_combo = QComboBox()
        row1.addWidget(self.port_combo)

        self.btn_refresh = ThemedButton("Refresh Ports", is_dark=False)
        row1.addWidget(self.btn_refresh)
        self.btn_refresh.clicked.connect(self._on_refresh_ports_clicked)
        layout.addLayout(row1)

        # Row 2: Baud
        row2 = QHBoxLayout()
        lbl_baud = QLabel("Baud:")
        row2.addWidget(lbl_baud)

        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600","19200","38400","57600","115200","230400"])
        row2.addWidget(self.baud_combo)
        layout.addLayout(row2)

        # Row 3: Time Window
        row3 = QHBoxLayout()
        lbl_tw = QLabel("Time Window (s):")
        row3.addWidget(lbl_tw)
        self.time_window_spin = QDoubleSpinBox()
        self.time_window_spin.setRange(0.0, 9999.0)
        self.time_window_spin.setDecimals(1)
        self.time_window_spin.setValue(10.0)  # default 10 seconds, e.g.
        row3.addWidget(self.time_window_spin)
        layout.addLayout(row3)

        # Row 4: Start / Stop
        row4 = QHBoxLayout()
        self.btn_start = ThemedButton("Start", is_dark=True)
        self.btn_stop  = ThemedButton("Stop",  is_dark=False)
        self.btn_stop.setEnabled(False)

        # No toggling here; we just emit signals
        self.btn_start.clicked.connect(self._on_start_clicked)
        self.btn_stop.clicked.connect(self._on_stop_clicked)

        row4.addWidget(self.btn_start)
        row4.addWidget(self.btn_stop)
        layout.addLayout(row4)

        # Refresh ports initially
        self.refresh_ports()
        self.setLayout(layout)

    def _on_refresh_ports_clicked(self):
        self.refresh_ports()

    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        if not ports:
            self.port_combo.addItem("No ports found")
        else:
            for p in ports:
                self.port_combo.addItem(p.device)

    def _on_start_clicked(self):
        """
        We no longer toggle self.btn_start/self.btn_stop here.
        We just emit the signal so the parent can decide.
        """
        self.startSignal.emit()

    def _on_stop_clicked(self):
        """
        Same: no toggling of our button states here.
        """
        self.stopSignal.emit()

    def get_port(self):
        return self.port_combo.currentText()

    def get_baud(self):
        return self.baud_combo.currentText()

    def get_time_window(self):
        return self.time_window_spin.value()

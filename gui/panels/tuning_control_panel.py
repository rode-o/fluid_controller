# tuning_control_panel.py

import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QDoubleSpinBox, QPushButton, QFileDialog, QLineEdit, QFrame
)
from PyQt5.QtCore import pyqtSignal, Qt
from controller_interface.gui.widgets.themed_button import ThemedButton
import os

class TuningControlPanel(QGroupBox):
    """
    A QGroupBox for tuning/monitoring controls, now with directory + test name.
    """

    startSignal = pyqtSignal()
    stopSignal  = pyqtSignal()
    changeDirSignal = pyqtSignal()  # optional, if you want external logic

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Tuning Control Panel")

        layout = QVBoxLayout(self)

        # 1) Row: Port / Refresh
        row1 = QHBoxLayout()
        self.port_combo = QComboBox()
        row1.addWidget(self.port_combo)

        self.btn_refresh = ThemedButton("Refresh Ports", is_dark=False)
        row1.addWidget(self.btn_refresh)
        self.btn_refresh.clicked.connect(self._on_refresh_ports_clicked)
        layout.addLayout(row1)

        # 2) Row: Baud
        row2 = QHBoxLayout()
        lbl_baud = QLabel("Baud:")
        row2.addWidget(lbl_baud)

        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600","19200","38400","57600","115200","230400"])
        row2.addWidget(self.baud_combo)
        layout.addLayout(row2)

        # 3) Row: Time Window
        row3 = QHBoxLayout()
        lbl_tw = QLabel("Time Window (s):")
        row3.addWidget(lbl_tw)
        self.time_window_spin = QDoubleSpinBox()
        self.time_window_spin.setRange(0.0, 9999.0)
        self.time_window_spin.setDecimals(1)
        self.time_window_spin.setValue(10.0)  # default
        row3.addWidget(self.time_window_spin)
        layout.addLayout(row3)

        # 4) Row: Data Root + Change Dir
        row4 = QHBoxLayout()
        lbl_dir = QLabel("Data Root:")
        row4.addWidget(lbl_dir)

        self.lbl_data_root = QLabel("(No directory)")
        self.lbl_data_root.setFrameShape(QFrame.Box)
        self.lbl_data_root.setFrameShadow(QFrame.Sunken)
        self.lbl_data_root.setLineWidth(2)
        row4.addWidget(self.lbl_data_root, stretch=1)

        self.btn_change_dir = ThemedButton("Change Dir", is_dark=False)
        row4.addWidget(self.btn_change_dir)
        self.btn_change_dir.clicked.connect(self._on_change_dir_clicked)
        layout.addLayout(row4)

        # 5) Row: Test Name (prefix)
        row5 = QHBoxLayout()
        lbl_test = QLabel("Test Name:")
        row5.addWidget(lbl_test)
        self.line_test_name = QLineEdit()
        self.line_test_name.setPlaceholderText("e.g. test1, runXYZ, etc.")
        row5.addWidget(self.line_test_name)
        layout.addLayout(row5)

        # 6) Row: Start / Stop
        row6 = QHBoxLayout()
        self.btn_start = ThemedButton("Start", is_dark=True)
        self.btn_stop  = ThemedButton("Stop",  is_dark=False)
        self.btn_stop.setEnabled(False)

        self.btn_start.clicked.connect(self._on_start_clicked)
        self.btn_stop.clicked.connect(self._on_stop_clicked)

        row6.addWidget(self.btn_start)
        row6.addWidget(self.btn_stop)
        layout.addLayout(row6)

        self.setLayout(layout)

        # Initial refresh
        self.refresh_ports()

        # Data root path in memory
        self.data_root = None

    # --------------------------------------------------------------
    #   Port refresh
    # --------------------------------------------------------------
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

    # --------------------------------------------------------------
    #   Change Directory
    # --------------------------------------------------------------
    def _on_change_dir_clicked(self):
        # E.g., open a QFileDialog
        new_dir = QFileDialog.getExistingDirectory(
            self, "Select Data Directory", os.getcwd()
        )
        if new_dir:
            self.set_data_root(new_dir)

        # If you want a signal, emit it:
        # self.changeDirSignal.emit()

    def set_data_root(self, directory_path):
        self.data_root = directory_path
        self.lbl_data_root.setText(directory_path)

    def get_data_root(self):
        return self.data_root

    # --------------------------------------------------------------
    #   Test Name
    # --------------------------------------------------------------
    def get_test_name(self):
        return self.line_test_name.text().strip()

    def set_test_name(self, text):
        self.line_test_name.setText(text)

    # --------------------------------------------------------------
    #   Start / Stop
    # --------------------------------------------------------------
    def _on_start_clicked(self):
        self.startSignal.emit()

    def _on_stop_clicked(self):
        self.stopSignal.emit()

    # --------------------------------------------------------------
    #   Public getters
    # --------------------------------------------------------------
    def get_port(self):
        return self.port_combo.currentText()

    def get_baud(self):
        return self.baud_combo.currentText()

    def get_time_window(self):
        return self.time_window_spin.value()

import os
import serial.tools.list_ports

from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSpinBox, QDoubleSpinBox, QFrame, QSizePolicy, QPushButton
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont

class ControlsPanel(QGroupBox):
    """
    A QGroupBox with:
      - Row 1: Port/baud/data root, refresh, change dir
      - Row 2: stable window, threshold, plot window, fluid density
      - Row 3: start/stop buttons
    """

    startCaptureSignal = pyqtSignal()
    stopCaptureSignal  = pyqtSignal()
    changeDirSignal    = pyqtSignal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setTitle("Controls")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.settings  = settings
        self.data_root = None
        self.last_port = None
        self.last_baud = None

        self._init_ui()
        self.load_settings()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Panel-wide font for labels
        base_font = QFont()
        base_font.setPointSize(12)
        self.setFont(base_font)

        # ------------------- ROW 1 -------------------
        row1 = QHBoxLayout()
        row1.setSpacing(30)

        # (1) Port label + combo
        h_port = QHBoxLayout()
        h_port.setSpacing(5)
        lbl_port = QLabel("Port:")
        self.port_combo = QComboBox()
        h_port.addWidget(lbl_port)
        h_port.addWidget(self.port_combo)
        row1.addLayout(h_port)

        # (2) Refresh button
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.refresh_ports)
        self.btn_refresh.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_refresh.setMinimumHeight(40)
        row1.addWidget(self.btn_refresh)

        # (3) Baud label + combo
        h_baud = QHBoxLayout()
        h_baud.setSpacing(5)
        lbl_baud = QLabel("Baud:")
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200", "230400"])
        h_baud.addWidget(lbl_baud)
        h_baud.addWidget(self.baud_combo)
        row1.addLayout(h_baud)

        # (4) Data Root label + display label
        h_dr = QHBoxLayout()
        h_dr.setSpacing(5)
        lbl_dr = QLabel("Data Root:")
        self.lbl_dir = QLabel("(No directory)")
        self.lbl_dir.setFrameShape(QFrame.Box)
        self.lbl_dir.setFrameShadow(QFrame.Sunken)
        self.lbl_dir.setLineWidth(2)
        h_dr.addWidget(lbl_dr)
        h_dr.addWidget(self.lbl_dir)
        row1.addLayout(h_dr)

        # (5) Change Dir button
        self.btn_change_dir = QPushButton("Change Dir")
        self.btn_change_dir.clicked.connect(self._on_change_dir_clicked)
        self.btn_change_dir.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_change_dir.setMinimumHeight(40)
        row1.addWidget(self.btn_change_dir)

        main_layout.addLayout(row1)

        # ------------------- ROW 2 -------------------
        row2 = QHBoxLayout()
        row2.setSpacing(50)

        # (1) Stable Window label + spin
        h_sw = QHBoxLayout()
        h_sw.setSpacing(5)
        lbl_sw = QLabel("Stable Window:")
        self.stable_window_spin = QSpinBox()
        self.stable_window_spin.setRange(1, 9999)
        h_sw.addWidget(lbl_sw)
        h_sw.addWidget(self.stable_window_spin)
        row2.addLayout(h_sw)

        # (2) Threshold label + spin
        h_thr = QHBoxLayout()
        h_thr.setSpacing(5)
        lbl_thr = QLabel("Threshold:")
        self.stable_threshold_spin = QDoubleSpinBox()
        self.stable_threshold_spin.setRange(0.0, 9999.0)
        self.stable_threshold_spin.setDecimals(3)
        h_thr.addWidget(lbl_thr)
        h_thr.addWidget(self.stable_threshold_spin)
        row2.addLayout(h_thr)

        # (3) Plot Window label + spin
        h_pw = QHBoxLayout()
        h_pw.setSpacing(5)
        lbl_pw = QLabel("Plot Window(ss):")
        self.time_window_spin = QDoubleSpinBox()
        self.time_window_spin.setRange(0.1, 9999)
        self.time_window_spin.setDecimals(1)
        h_pw.addWidget(lbl_pw)
        h_pw.addWidget(self.time_window_spin)
        row2.addLayout(h_pw)

        # (4) Fluid Density label + spin
        h_fd = QHBoxLayout()
        h_fd.setSpacing(5)
        lbl_fd = QLabel("Fluid Density:")
        self.fluid_density_spin = QDoubleSpinBox()
        self.fluid_density_spin.setRange(0.1, 10.0)
        self.fluid_density_spin.setDecimals(3)
        h_fd.addWidget(lbl_fd)
        h_fd.addWidget(self.fluid_density_spin)
        row2.addLayout(h_fd)

        main_layout.addLayout(row2)

        # ------------------- ROW 3 -------------------
        row3 = QHBoxLayout()
        row3.setSpacing(30)

        self.btn_start = QPushButton("Start")
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setEnabled(False)
        self.btn_start.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_stop.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_start.setMinimumHeight(40)
        self.btn_stop.setMinimumHeight(40)

        self.btn_start.clicked.connect(self._on_start_clicked)
        self.btn_stop.clicked.connect(self._on_stop_clicked)

        row3.addWidget(self.btn_start)
        row3.addWidget(self.btn_stop)

        main_layout.addLayout(row3)

        # Apply a simple, fixed style to all buttons
        button_style = """
            QPushButton {
                background-color: #D3D3D3;
                color: black;
                font-size: 14px;
                padding: 5px 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #C0C0C0;
            }
        """
        self.btn_refresh.setStyleSheet(button_style)
        self.btn_change_dir.setStyleSheet(button_style)
        self.btn_start.setStyleSheet(button_style)
        self.btn_stop.setStyleSheet(button_style)

    # -------------------------------------------------------------------------
    #                           UI Logic
    # -------------------------------------------------------------------------
    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        if not ports:
            self.port_combo.addItem("No ports found")
        else:
            for p in ports:
                self.port_combo.addItem(p.device)

    def _on_change_dir_clicked(self):
        self.changeDirSignal.emit()

    def _on_start_clicked(self):
        self.save_settings()
        self.startCaptureSignal.emit()

    def _on_stop_clicked(self):
        self.stopCaptureSignal.emit()

    def load_settings(self):
        if not self.settings:
            return

        self.data_root = self.settings.value("data_root", None)
        if self.data_root:
            self.lbl_dir.setText(self.data_root)

        self.last_port = self.settings.value("last_port", "")
        self.last_baud = self.settings.value("last_baud", "9600")

        self.stable_window_spin.setValue(int(self.settings.value("stable_window", 10)))
        self.stable_threshold_spin.setValue(float(self.settings.value("stable_threshold", 0.05)))
        self.time_window_spin.setValue(float(self.settings.value("time_window", 2.0)))
        self.fluid_density_spin.setValue(float(self.settings.value("fluid_density", 1.0)))

        self.refresh_ports()
        if self.last_port:
            idx = self.port_combo.findText(self.last_port)
            if idx >= 0:
                self.port_combo.setCurrentIndex(idx)

        idx_baud = self.baud_combo.findText(self.last_baud)
        if idx_baud >= 0:
            self.baud_combo.setCurrentIndex(idx_baud)

    def save_settings(self):
        if not self.settings:
            return
        self.settings.setValue("data_root", self.data_root if self.data_root else "")
        self.settings.setValue("last_port", self.get_port())
        self.settings.setValue("last_baud", self.get_baud())
        self.settings.setValue("stable_window", self.stable_window_spin.value())
        self.settings.setValue("stable_threshold", self.stable_threshold_spin.value())
        self.settings.setValue("time_window", self.time_window_spin.value())
        self.settings.setValue("fluid_density", self.fluid_density_spin.value())

    def set_data_root(self, path):
        self.data_root = path
        self.lbl_dir.setText(path)

    def get_port(self):
        return self.port_combo.currentText()

    def get_baud(self):
        return self.baud_combo.currentText()

    def enable_start(self, enable: bool):
        self.btn_start.setEnabled(enable)

    def enable_stop(self, enable: bool):
        self.btn_stop.setEnabled(enable)

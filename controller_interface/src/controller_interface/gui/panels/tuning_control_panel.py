import os
import serial.tools.list_ports

from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QDoubleSpinBox, QFileDialog, QLineEdit, QFrame
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont

from controller_interface.gui.widgets.themed_button import ThemedButton

class TuningControlPanel(QGroupBox):
    """
    A QGroupBox with:
      - Port selection, baud, time window
      - Data Root + Test Name row
      - Fluid Density input
      - Start/Stop
      - A 'Mark Stable' toggle (checkable push button).
    
    We do NOT set a global style sheet so ThemedButton's colors won't be overridden.
    Instead, we set a 10pt font in Python code for the entire panel.
    """

    startSignal = pyqtSignal()
    stopSignal  = pyqtSignal()
    stabilityChanged = pyqtSignal(bool)

    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.setTitle("Tuning Control Panel")
        self.settings = settings
        self.data_root = None

        # Force the entire QGroupBox to 10pt by code
        font = self.font()
        font.setPointSize(10)
        self.setFont(font)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # 1) Row: Port / Refresh
        row1 = QHBoxLayout()
        self.port_combo = QComboBox()
        row1.addWidget(self.port_combo)

        self.btn_refresh = ThemedButton("Refresh Ports", is_dark=False)
        row1.addWidget(self.btn_refresh)
        self.btn_refresh.clicked.connect(self._on_refresh_ports_clicked)
        main_layout.addLayout(row1)

        # 2) Row: Baud
        row2 = QHBoxLayout()
        lbl_baud = QLabel("Baud:")
        row2.addWidget(lbl_baud)
        self.baud_combo = QComboBox()
        self.baud_combo.addItems([
            "9600", "19200", "38400", "57600",
            "115200", "230400"
        ])
        row2.addWidget(self.baud_combo)
        main_layout.addLayout(row2)

        # 3) Row: Time Window
        row3 = QHBoxLayout()
        lbl_tw = QLabel("Time Window (s):")
        row3.addWidget(lbl_tw)
        self.time_window_spin = QDoubleSpinBox()
        self.time_window_spin.setRange(0.0, 9999.0)
        self.time_window_spin.setDecimals(1)
        self.time_window_spin.setValue(10.0)
        row3.addWidget(self.time_window_spin)
        main_layout.addLayout(row3)

        # 4) Data Root + Test Name + Change Dir
        row4 = QHBoxLayout()
        lbl_dir = QLabel("Data Root:")
        row4.addWidget(lbl_dir)

        self.lbl_data_root = QLabel("(No directory)")
        self.lbl_data_root.setFrameShape(QFrame.Box)
        self.lbl_data_root.setFrameShadow(QFrame.Sunken)
        self.lbl_data_root.setLineWidth(2)
        row4.addWidget(self.lbl_data_root, stretch=2)

        lbl_test = QLabel("Test Name:")
        row4.addWidget(lbl_test)

        self.line_test_name = QLineEdit()
        self.line_test_name.setPlaceholderText("e.g. test_run_01")
        row4.addWidget(self.line_test_name, stretch=1)

        self.btn_change_dir = ThemedButton("Change Dir", is_dark=False)
        row4.addWidget(self.btn_change_dir)
        self.btn_change_dir.clicked.connect(self._on_change_dir_clicked)
        main_layout.addLayout(row4)

        # 5) Fluid Density
        row_density = QHBoxLayout()
        lbl_density = QLabel("Fluid Density (g/mL):")
        row_density.addWidget(lbl_density)

        self.fluid_density_spin = QDoubleSpinBox()
        self.fluid_density_spin.setRange(0.0, 5.0)
        self.fluid_density_spin.setDecimals(3)
        self.fluid_density_spin.setValue(1.000)
        row_density.addWidget(self.fluid_density_spin)
        main_layout.addLayout(row_density)

        # 6) Checkable push button for "Mark Data as Stable"
        row5 = QHBoxLayout()
        self.btn_stable = ThemedButton("Mark Data as Stable", is_dark=False)
        self.btn_stable.setCheckable(True)
        self.btn_stable.setChecked(False)
        self.btn_stable.toggled.connect(self._on_stable_toggled)
        row5.addWidget(self.btn_stable)
        main_layout.addLayout(row5)

        # 7) Row: Start/Stop
        row6 = QHBoxLayout()
        self.btn_start = ThemedButton("Start", is_dark=True)
        self.btn_stop  = ThemedButton("Stop", is_dark=False)
        self.btn_stop.setEnabled(False)

        self.btn_start.clicked.connect(self._on_start_clicked)
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        row6.addWidget(self.btn_start)
        row6.addWidget(self.btn_stop)
        main_layout.addLayout(row6)

        self.setLayout(main_layout)

        # Refresh ports initially
        self.refresh_ports()

    # ----------------------------------------------------------------
    # Load/save logic
    # ----------------------------------------------------------------
    def load_settings(self):
        """Load any previously stored settings."""
        if self.settings:
            root = self.settings.value("tuning_data_root", "")
            if root:
                self.set_data_root(root)

            test_name = self.settings.value("tuning_test_name", "")
            if test_name:
                self.set_test_name(test_name)

            last_density = float(self.settings.value("tuning_fluid_density", 1.0))
            self.fluid_density_spin.setValue(last_density)

    def save_settings(self):
        """Persist user selections to self.settings."""
        if self.settings:
            if self.data_root:
                self.settings.setValue("tuning_data_root", self.data_root)
            if self.get_test_name():
                self.settings.setValue("tuning_test_name", self.get_test_name())

            self.settings.setValue("tuning_fluid_density", self.get_fluid_density())

    # ----------------------------------------------------------------
    # Stable toggle
    # ----------------------------------------------------------------
    def _on_stable_toggled(self, checked: bool):
        """Emits stabilityChanged(bool) when toggled."""
        self.stabilityChanged.emit(checked)

    # ----------------------------------------------------------------
    # Directory logic
    # ----------------------------------------------------------------
    def _on_change_dir_clicked(self):
        from PyQt5.QtWidgets import QFileDialog
        new_dir = QFileDialog.getExistingDirectory(self, "Select Data Directory", os.getcwd())
        if new_dir:
            self.set_data_root(new_dir)

    def set_data_root(self, path):
        self.data_root = path
        self.lbl_data_root.setText(path)

    def get_data_root(self):
        return self.data_root

    # ----------------------------------------------------------------
    # Test name
    # ----------------------------------------------------------------
    def get_test_name(self):
        return self.line_test_name.text().strip()

    def set_test_name(self, text):
        self.line_test_name.setText(text)

    # ----------------------------------------------------------------
    # Ports
    # ----------------------------------------------------------------
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

    # ----------------------------------------------------------------
    # Start/Stop
    # ----------------------------------------------------------------
    def _on_start_clicked(self):
        self.save_settings()
        self.startSignal.emit()

    def _on_stop_clicked(self):
        self.stopSignal.emit()

    # ----------------------------------------------------------------
    # Fluid density
    # ----------------------------------------------------------------
    def get_fluid_density(self):
        return self.fluid_density_spin.value()

    # ----------------------------------------------------------------
    # Public getters
    # ----------------------------------------------------------------
    def get_port(self):
        return self.port_combo.currentText()

    def get_baud(self):
        return self.baud_combo.currentText()

    def get_time_window(self):
        return self.time_window_spin.value()

    def is_stable_marked(self):
        return self.btn_stable.isChecked()

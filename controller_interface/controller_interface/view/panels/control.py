# controller_interface/view/panels/control.py

import os
import serial.tools.list_ports

from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QDoubleSpinBox, QFileDialog, QLineEdit, QFrame, QSizePolicy
)
from PyQt5.QtCore import pyqtSignal, Qt, QSettings
from PyQt5.QtGui import QFont, QPalette, QColor

from controller_interface.view.widgets.themed_button import ThemedButton

TITLE_COLOR_RGB = (29, 154, 221)
TITLE_FONT_SIZE = 12
CHILD_FONT_SIZE = 12

class TuningControlPanel(QGroupBox):
    """
    A QGroupBox with:
      - Port selection, baud, time window
      - Data Root in its own row (displays only the last path element)
      - Test Name on its own row
      - "Change Dir" on its own row
      - Fluid Density input
      - Start/Stop
      - A 'Mark Stable' toggle.
    """

    startSignal = pyqtSignal()
    stopSignal = pyqtSignal()
    stabilityChanged = pyqtSignal(bool)

    def __init__(self, parent=None, settings: QSettings | None = None):
        super().__init__(parent)
        self.setTitle("Tuning Control Panel")
        self.settings = settings
        self.data_root: str | None = None

        # -----------------------
        # 1) Title font & color
        # -----------------------
        title_font = QFont()
        title_font.setPointSize(TITLE_FONT_SIZE)
        title_font.setBold(True)
        self.setFont(title_font)

        palette = self.palette()
        palette.setColor(self.foregroundRole(), QColor(*TITLE_COLOR_RGB))
        self.setPalette(palette)

        # -----------------------
        # 2) Child font
        # -----------------------
        self.child_font = QFont()
        self.child_font.setPointSize(CHILD_FONT_SIZE)
        self.child_font.setBold(False)

        # -----------------------
        # Main layout
        # -----------------------
        main_layout = QVBoxLayout(self)
        # Keep margins small to avoid unnecessary space
        main_layout.setContentsMargins(5, 5, 5, 5)
        # Reduce spacing from 20 -> 8 or 10 so it doesn't look too large
        main_layout.setSpacing(10)

        # Row 1: Port / Refresh
        row1 = QHBoxLayout()
        self.port_combo = QComboBox(font=self.child_font)
        row1.addWidget(self.port_combo)

        self.btn_refresh = ThemedButton("Refresh Ports", is_dark=False)
        self.btn_refresh.setFont(self.child_font)
        self.btn_refresh.clicked.connect(self._on_refresh_ports_clicked)
        row1.addWidget(self.btn_refresh)
        main_layout.addLayout(row1)

        # Row 2: Baud
        row2 = QHBoxLayout()
        lbl_baud = QLabel("Baud:", font=self.child_font)
        row2.addWidget(lbl_baud)

        self.baud_combo = QComboBox(font=self.child_font)
        self.baud_combo.addItems([
            "9600", "19200", "38400", "57600",
            "115200", "230400"
        ])
        row2.addWidget(self.baud_combo)
        main_layout.addLayout(row2)

        # Row 3: Time Window
        row3 = QHBoxLayout()
        lbl_tw = QLabel("Time Window (s):", font=self.child_font)
        row3.addWidget(lbl_tw)

        self.time_window_spin = QDoubleSpinBox(font=self.child_font)
        self.time_window_spin.setRange(0.0, 9999.0)
        self.time_window_spin.setDecimals(1)
        self.time_window_spin.setValue(10.0)
        row3.addWidget(self.time_window_spin)
        main_layout.addLayout(row3)

        # Row 4: Data Root
        row4 = QHBoxLayout()
        lbl_dir = QLabel("Data Root:", font=self.child_font)
        row4.addWidget(lbl_dir)

        self.lbl_data_root = QLabel("(No directory)", font=self.child_font)
        self.lbl_data_root.setFrameShape(QFrame.Box)
        self.lbl_data_root.setFrameShadow(QFrame.Sunken)
        self.lbl_data_root.setLineWidth(2)
        row4.addWidget(self.lbl_data_root, stretch=2)
        main_layout.addLayout(row4)

        # Row 5: Test Name
        row5 = QHBoxLayout()
        lbl_test = QLabel("Test Name:", font=self.child_font)
        row5.addWidget(lbl_test)

        self.line_test_name = QLineEdit(font=self.child_font)
        self.line_test_name.setPlaceholderText("e.g. test_run_01")
        row5.addWidget(self.line_test_name)
        main_layout.addLayout(row5)

        # Row 6: Change Dir button
        row6 = QHBoxLayout()
        self.btn_change_dir = ThemedButton("Change Dir", is_dark=False)
        self.btn_change_dir.setFont(self.child_font)
        self.btn_change_dir.clicked.connect(self._on_change_dir_clicked)
        row6.addWidget(self.btn_change_dir)
        main_layout.addLayout(row6)

        # Row 7: Fluid Density
        row_density = QHBoxLayout()
        lbl_density = QLabel("Fluid Density (g/mL):", font=self.child_font)
        row_density.addWidget(lbl_density)

        self.fluid_density_spin = QDoubleSpinBox(font=self.child_font)
        self.fluid_density_spin.setRange(0.0, 5.0)
        self.fluid_density_spin.setDecimals(3)
        self.fluid_density_spin.setValue(1.000)
        row_density.addWidget(self.fluid_density_spin)
        main_layout.addLayout(row_density)

        # Row 8: Mark Data as Stable
        row_stable = QHBoxLayout()
        self.btn_stable = ThemedButton("Mark Data as Stable", is_dark=False)
        self.btn_stable.setFont(self.child_font)
        self.btn_stable.setCheckable(True)
        self.btn_stable.setChecked(False)
        self.btn_stable.toggled.connect(self._on_stable_toggled)
        row_stable.addWidget(self.btn_stable)
        main_layout.addLayout(row_stable)

        # Row 9: Start / Stop
        row_startstop = QHBoxLayout()
        self.btn_start = ThemedButton("Start", is_dark=True)
        self.btn_start.setFont(self.child_font)
        self.btn_stop = ThemedButton("Stop", is_dark=False)
        self.btn_stop.setFont(self.child_font)
        self.btn_stop.setEnabled(False)

        self.btn_start.clicked.connect(self._on_start_clicked)
        self.btn_stop.clicked.connect(self._on_stop_clicked)

        row_startstop.addWidget(self.btn_start)
        row_startstop.addWidget(self.btn_stop)
        main_layout.addLayout(row_startstop)

        # Set a size policy that does not expand more than necessary
        # horizontally or vertically.
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        self.setLayout(main_layout)

        # Initial port refresh
        self.refresh_ports()

    # ----------------------------------------------------------------
    # Load/save logic
    # ----------------------------------------------------------------
    def load_settings(self) -> None:
        """Load any previously stored settings."""
        if self.settings:
            root = self.settings.value("tuning_data_root", "")
            if root:
                self.set_data_root(str(root))

            test_name = self.settings.value("tuning_test_name", "")
            if test_name:
                self.set_test_name(str(test_name))

            last_density_str = self.settings.value("tuning_fluid_density", "1.0")
            try:
                last_density = float(last_density_str)
                self.fluid_density_spin.setValue(last_density)
            except ValueError:
                pass

    def save_settings(self) -> None:
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
    def _on_stable_toggled(self, checked: bool) -> None:
        """Emits stabilityChanged(bool) when toggled."""
        self.stabilityChanged.emit(checked)

    # ----------------------------------------------------------------
    # Directory logic
    # ----------------------------------------------------------------
    def _on_change_dir_clicked(self) -> None:
        new_dir = QFileDialog.getExistingDirectory(
            self, "Select Data Directory", os.getcwd()
        )
        if new_dir:
            self.set_data_root(new_dir)

    def set_data_root(self, path: str) -> None:
        """
        Sets data_root internally and updates the label to display
        only the last element of the path.
        Tooltip shows the entire path.
        """
        self.data_root = path
        last_part = os.path.basename(path.strip("/\\"))
        if not last_part:
            last_part = path

        self.lbl_data_root.setText(last_part)
        self.lbl_data_root.setToolTip(path)

    def get_data_root(self) -> str | None:
        return self.data_root

    # ----------------------------------------------------------------
    # Test name
    # ----------------------------------------------------------------
    def get_test_name(self) -> str:
        return self.line_test_name.text().strip()

    def set_test_name(self, text: str) -> None:
        self.line_test_name.setText(text)

    # ----------------------------------------------------------------
    # Ports
    # ----------------------------------------------------------------
    def _on_refresh_ports_clicked(self) -> None:
        self.refresh_ports()

    def refresh_ports(self) -> None:
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
    def _on_start_clicked(self) -> None:
        self.save_settings()
        self.startSignal.emit()

    def _on_stop_clicked(self) -> None:
        self.stopSignal.emit()

    # ----------------------------------------------------------------
    # Fluid density
    # ----------------------------------------------------------------
    def get_fluid_density(self) -> float:
        return self.fluid_density_spin.value()

    # ----------------------------------------------------------------
    # Public getters
    # ----------------------------------------------------------------
    def get_port(self) -> str:
        return self.port_combo.currentText()

    def get_baud(self) -> str:
        return self.baud_combo.currentText()

    def get_time_window(self) -> float:
        return self.time_window_spin.value()

    def is_stable_marked(self) -> bool:
        return self.btn_stable.isChecked()

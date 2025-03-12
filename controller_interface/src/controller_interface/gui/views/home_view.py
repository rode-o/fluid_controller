import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap

from controller_interface.gui.widgets.themed_button import ThemedButton


def resource_path(relative_path):
    """
    Return the absolute path to a resource, whether we're running in a development
    environment or within a PyInstaller one-file/one-folder bundle.
    """
    # If we are running inside a PyInstaller bundle
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    # Otherwise, assume we're running in normal Python
    return os.path.join(os.path.dirname(__file__), relative_path)


class HomeView(QWidget):
    goDataStreamSignal = pyqtSignal()
    goPidTuningSignal = pyqtSignal()

    themeSelectedSignal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # ============ 1) THEME ROW (TOP) ============
        theme_row = QHBoxLayout()
        theme_row.addStretch(1)

        self.theme_combo = QComboBox()
        self.theme_combo.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.theme_combo.addItem("Dark Purple", userData="purple")
        self.theme_combo.addItem("Deep Blue", userData="blue")
        self.theme_combo.addItem("Soothing Green", userData="green")
        self.theme_combo.addItem("Light Gray", userData="gray")
        self.theme_combo.addItem("Dark Gray", userData="dark_gray")
        self.theme_combo.addItem("Vivid Red", userData="vivid_red")

        self.theme_combo.currentIndexChanged.connect(self.on_theme_combo_changed)
        theme_row.addWidget(self.theme_combo)
        main_layout.addLayout(theme_row, 0)

        # ============ 2) BODY LAYOUT (occupies the rest) ============
        body_layout = QVBoxLayout()

        top_spacer = QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)
        body_layout.addSpacerItem(top_spacer)

        # ---------- LOGO ----------
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)

        # Use resource_path to find the PNG in dev OR PyInstaller runtime
        logo_path = resource_path("resources/salvus_leaf_logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(
                300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.logo_label.setPixmap(pixmap)
        else:
            self.logo_label.setText("LOGO not found!")

        body_layout.addWidget(self.logo_label, 0, Qt.AlignCenter)

        mid_spacer = QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)
        body_layout.addSpacerItem(mid_spacer)

        # ---------- BUTTON ROW ----------
        button_row = QHBoxLayout()
        left_spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum)
        right_spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.btn_data_stream = ThemedButton("Streamer", is_dark=True)
        self.btn_pid_tuning = ThemedButton("Tuner", is_dark=False)

        self.btn_data_stream.clicked.connect(self.goDataStreamSignal.emit)
        self.btn_pid_tuning.clicked.connect(self.goPidTuningSignal.emit)

        button_row.addItem(left_spacer)
        button_row.addWidget(self.btn_data_stream)
        button_row.addWidget(self.btn_pid_tuning)
        button_row.addItem(right_spacer)

        button_row.setStretch(0, 1)
        button_row.setStretch(1, 1)
        button_row.setStretch(2, 1)
        button_row.setStretch(3, 1)

        body_layout.addLayout(button_row, 0)

        bottom_spacer = QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)
        body_layout.addSpacerItem(bottom_spacer)

        main_layout.addLayout(body_layout, 1)

    # ----------------------------------------------------------------
    # 1/10th Sizing + Round corners in HomeView
    # ----------------------------------------------------------------
    def resizeEvent(self, event):
        super().resizeEvent(event)

        total_height = self.height()
        # 1/10 the window height, min 40
        button_height = max(40, int(total_height * 0.1))

        # Dynamic text size
        font_size = max(8, button_height // 4)

        # Extra padding
        pad_vert = int(button_height * 0.2)
        pad_horz = int(button_height * 0.3)

        # Round corners => half the button height
        corner_radius = button_height // 2

        # Build style snippet
        style_snippet = f"""
            QPushButton {{
                font-size: {font_size}px;
                padding: {pad_vert}px {pad_horz}px;
                border-radius: {corner_radius}px;
            }}
        """

        # Apply to both buttons
        self.btn_data_stream.setFixedHeight(button_height)
        self.btn_data_stream.setStyleSheet(
            self.btn_data_stream.styleSheet() + style_snippet
        )

        self.btn_pid_tuning.setFixedHeight(button_height)
        self.btn_pid_tuning.setStyleSheet(
            self.btn_pid_tuning.styleSheet() + style_snippet
        )

    # ----------------------------------------------------------------
    #                        THEME METHODS
    # ----------------------------------------------------------------
    def on_theme_combo_changed(self, index):
        chosen_data = self.theme_combo.itemData(index)
        if chosen_data:
            self.themeSelectedSignal.emit(chosen_data)

    def set_theme_combo(self, theme_name):
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == theme_name:
                self.theme_combo.setCurrentIndex(i)
                break

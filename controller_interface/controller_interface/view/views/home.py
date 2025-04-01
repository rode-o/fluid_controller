# controller_interface/view/views/home.py

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QPixmap

# Import your Qt Resource file so embedded images are registered
import controller_interface.resources.resources_rc

from controller_interface.view.widgets.themed_button import ThemedButton


class HomeView(QWidget):
    """
    A home view with a single large button that displays a logo icon.
    Clicking it emits goPidTuningSignal.
    """

    goPidTuningSignal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        print("[DEBUG] HomeView constructor invoked.")

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Body layout: top spacer, button row, bottom spacer
        body_layout = QVBoxLayout()
        top_spacer = QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)
        body_layout.addSpacerItem(top_spacer)

        # Single button row
        button_row = QHBoxLayout()
        button_row.addStretch(1)

        self.btn_pid_tuning = ThemedButton("", is_dark=False)
        self.btn_pid_tuning.clicked.connect(self._on_pid_tuning_clicked)

        # Use the Qt resource path
        logo_path = ":/salvus_full_logo_color.png"

        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            print("[DEBUG] Found embedded logo resource:", logo_path)
            self.btn_pid_tuning.setToolTip("Open Tuning View")
            self.btn_pid_tuning.setIcon(QIcon(logo_path))
        else:
            self.btn_pid_tuning.setText("Logo Not Found")
            print(f"[DEBUG] Logo not found at resource path {logo_path}")

        button_row.addWidget(self.btn_pid_tuning)
        button_row.addStretch(1)
        body_layout.addLayout(button_row, 0)

        bottom_spacer = QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)
        body_layout.addSpacerItem(bottom_spacer)

        main_layout.addLayout(body_layout, 1)

    def resizeEvent(self, event):
        """
        Enlarges the button and icon significantly.
        - 20% of the window's height for the button
        - Icon ~100% of that
        """
        super().resizeEvent(event)
        print(f"[DEBUG] HomeView resizeEvent -> size={self.width()}x{self.height()}")

        total_height = self.height()

        # Make the button ~20% of the window height, min 80
        button_height = max(80, int(total_height * 0.2))

        # The icon at ~100% of button height
        icon_size = max(40, int(button_height * 1.0))

        font_size = max(8, button_height // 4)
        pad_vert = int(button_height * 0.2)
        pad_horz = int(button_height * 0.3)
        corner_radius = button_height // 2

        style_snippet = f"""
            QPushButton {{
                font-size: {font_size}px;
                padding: {pad_vert}px {pad_horz}px;
                border-radius: {corner_radius}px;
            }}
        """
        self.btn_pid_tuning.setFixedHeight(button_height)
        self.btn_pid_tuning.setStyleSheet(
            self.btn_pid_tuning.styleSheet() + style_snippet
        )

        self.btn_pid_tuning.setIconSize(QSize(icon_size, icon_size))

    def _on_pid_tuning_clicked(self):
        print("[DEBUG] Tuner button (logo) clicked -> emitting goPidTuningSignal")
        self.goPidTuningSignal.emit()

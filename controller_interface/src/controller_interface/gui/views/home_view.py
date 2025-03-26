import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QPixmap

from controller_interface.gui.widgets.themed_button import ThemedButton

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

        # Attempt to load a local .png as icon
        this_dir = os.path.dirname(__file__)
        logo_rel_path = os.path.join(
            this_dir, "..", "..",
            "resources",
            "18915def-9726-452b-acb8-d54b328a7818.png"
        )
        logo_path = os.path.abspath(logo_rel_path)
        if os.path.exists(logo_path):
            self.btn_pid_tuning.setToolTip("Open Tuning View")
            icon = QIcon(logo_path)
            self.btn_pid_tuning.setIcon(icon)
        else:
            self.btn_pid_tuning.setText("Logo Not Found")
            print(f"[DEBUG] Logo path not found at: {logo_path}")

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
        - icon ~80% of that
        """
        super().resizeEvent(event)
        print(f"[DEBUG] HomeView resizeEvent -> size={self.width()}x{self.height()}")

        total_height = self.height()

        # Make the button ~20% of the window height, min 80
        button_height = max(80, int(total_height * 0.2))

        # The icon at ~80% of button height
        icon_size = max(40, int(button_height * 1.0))

        # Font size or other styling
        font_size = max(8, button_height // 4)
        pad_vert = int(button_height * 0.2)
        pad_horz = int(button_height * 0.3)
        corner_radius = button_height // 2

        # Additional snippet appended to the existing style
        style_snippet = f"""
            QPushButton {{
                font-size: {font_size}px;
                padding: {pad_vert}px {pad_horz}px;
                border-radius: {corner_radius}px;
            }}
        """
        # Update button's height
        self.btn_pid_tuning.setFixedHeight(button_height)
        # Merge the style snippet
        self.btn_pid_tuning.setStyleSheet(
            self.btn_pid_tuning.styleSheet() + style_snippet
        )

        # Also update icon size
        self.btn_pid_tuning.setIconSize(QSize(icon_size, icon_size))

    def _on_pid_tuning_clicked(self):
        print("[DEBUG] Tuner button (logo) clicked -> emitting goPidTuningSignal")
        self.goPidTuningSignal.emit()

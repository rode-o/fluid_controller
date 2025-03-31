# controller_interface/view/views/home.py

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon

# Direct subpackage import from your existing code:
from controller_interface.view.widgets.themed_button import ThemedButton
# Use the shared resource_path from your utils:
from controller_interface.utils.path_utils import resource_path


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

        # Use shared resource_path to find the logo
        logo_path = resource_path("resources/salvus_full_logo_color.png")

        if os.path.exists(logo_path):
            print("[DEBUG] Found logo at:", logo_path)
            self.btn_pid_tuning.setToolTip("Open Tuning View")
            self.btn_pid_tuning.setIcon(QIcon(logo_path))
        else:
            self.btn_pid_tuning.setText("Logo Not Found")
            print(f"[DEBUG] Logo path not found: {logo_path}")

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
        - Icon ~80% of that
        """
        super().resizeEvent(event)
        print(f"[DEBUG] HomeView resizeEvent -> size={self.width()}x{self.height()}")

        total_height = self.height()

        # Make the button ~20% of the window height, min 80
        button_height = max(80, int(total_height * 0.2))

        # The icon at ~100% of button height (or your preference)
        icon_size = max(40, int(button_height * 1.0))

        # Font size or other styling
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
        # Update button's height
        self.btn_pid_tuning.setFixedHeight(button_height)
        # Merge the style snippet
        self.btn_pid_tuning.setStyleSheet(
            self.btn_pid_tuning.styleSheet() + style_snippet
        )

        # Update icon size
        self.btn_pid_tuning.setIconSize(QSize(icon_size, icon_size))

    def _on_pid_tuning_clicked(self):
        print("[DEBUG] Tuner button (logo) clicked -> emitting goPidTuningSignal")
        self.goPidTuningSignal.emit()

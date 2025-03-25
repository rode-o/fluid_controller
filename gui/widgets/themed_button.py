# themed_button.py
from PyQt5.QtWidgets import QPushButton, QSizePolicy
from PyQt5.QtCore import Qt

class ThemedButton(QPushButton):
    """
    A minimal ThemedButton that:
      - Applies only background & text color in _apply_base_style(),
      - No paintEvent overrides (so no repeated style lines),
      - Leaves corner-radius, padding, font-size to be overridden by the parent code.
    """

    def __init__(self, text="", is_dark=True, parent=None):
        super().__init__(text, parent)
        self._is_dark = is_dark

        # Let layout or parent code define final size
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._apply_base_style()

    def _apply_base_style(self):
        """Just sets color (bg_color, text_color). No padding, no corner rounding here."""
        if self._is_dark:
            bg_color = "#333"  # dark
            text_color = "#eee"
        else:
            bg_color = "#ddd"  # light
            text_color = "#111"

        style = f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """
        self.setStyleSheet(style)

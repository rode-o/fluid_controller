# themed_button.py
from PyQt5.QtWidgets import QPushButton, QSizePolicy
from PyQt5.QtCore import Qt

class ThemedButton(QPushButton):
    """
    A ThemedButton that:
      - Applies a 10pt font, corner-radius, padding in a base style,
      - Chooses background/text colors in normal, hover, pressed, and checked states,
      - Distinguishes between a 'dark' variant and a 'light' variant.
    """

    def __init__(self, text="", is_dark=True, parent=None):
        super().__init__(text, parent)
        self._is_dark = is_dark

        # Let layout or parent code define final size
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._apply_base_style()

    def _apply_base_style(self):
        """
        Sets normal, hover, pressed, and (optionally) checked states.
        If you want the button to use the checked state, call setCheckable(True).
        """

        # Common styling for both variants:
        base_style = """
            font-size: 10pt;
            border-radius: 8px;
            padding: 10px 20px;
            border: none;
        """

        if self._is_dark:
            # DARK variant
            normal_bg   = "#333"
            text_color  = "#eee"
            hover_bg    = "#444"
            pressed_bg  = "#222"
            checked_bg  = "#2ecc71"  # bright green
        else:
            # EVEN MORE GRAY light variant
            normal_bg   = "#e0e0e0"
            text_color  = "#333"
            hover_bg    = "#d0d0d0"
            pressed_bg  = "#bfbfbf"
            checked_bg  = "#7a7a7a"

        style = f"""
        QPushButton {{
            {base_style}
            background-color: {normal_bg};
            color: {text_color};
        }}
        /* Hover */
        QPushButton:hover {{
            background-color: {hover_bg};
        }}
        /* Pressed */
        QPushButton:pressed {{
            background-color: {pressed_bg};
        }}
        /* Checked (toggle) */
        QPushButton:checked {{
            background-color: {checked_bg};
            color: #fff; /* keep text white if toggled */
        }}
        """

        self.setStyleSheet(style)

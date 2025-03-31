# app/gui/themes/dark_purple.py

from PyQt5.QtWidgets import QStyleFactory
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
import os

def set_dark_purple_mode(app):
    """
    A 'dark purple' theme using a shared common.qss for structure
    and additional color overrides for #DarkButton / #LightButton.
    """
    # 1) Set Fusion style, build a palette if you want
    app.setStyle(QStyleFactory.create("Fusion"))

    palette = QPalette()
    # Example palette (adjust to taste)
    window_color = QColor(40, 0, 60)
    base_color   = QColor(25, 0, 40)
    text_color   = Qt.white

    palette.setColor(QPalette.Window, window_color)
    palette.setColor(QPalette.WindowText, text_color)
    palette.setColor(QPalette.Base, base_color)
    palette.setColor(QPalette.AlternateBase, window_color)
    palette.setColor(QPalette.ToolTipBase, text_color)
    palette.setColor(QPalette.ToolTipText, text_color)
    palette.setColor(QPalette.Text, text_color)
    palette.setColor(QPalette.Button, window_color)
    palette.setColor(QPalette.ButtonText, text_color)
    palette.setColor(QPalette.BrightText, Qt.red)

    highlight_color = QColor(80, 30, 120)
    palette.setColor(QPalette.Highlight, highlight_color)
    palette.setColor(QPalette.HighlightedText, Qt.black)

    palette.setColor(QPalette.Link, QColor(150, 100, 200))
    palette.setColor(QPalette.Disabled, QPalette.Text, Qt.darkGray)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, Qt.darkGray)

    app.setPalette(palette)

    # 2) Load common structural QSS
    common_path = os.path.join(os.path.dirname(__file__), "common.qss")
    with open(common_path, "r", encoding="utf-8") as f:
        base_qss = f.read()

    # 3) Append color overrides for #DarkButton, #LightButton, etc.
    color_overrides = """
    QPushButton#DarkButton {
        background-color: #333;
        color: #fff;
        border: 2px solid #444;
    }
    QPushButton#DarkButton:hover {
        background-color: #444;
    }
    QPushButton#DarkButton:pressed {
        background-color: #222;
    }

    QPushButton#LightButton {
        background-color: #eee;
        color: #333;
        border: 2px solid #666;
    }
    QPushButton#LightButton:hover {
        background-color: #ddd;
    }
    QPushButton#LightButton:pressed {
        background-color: #bbb;
    }

    /* Example menu, toolbar, etc. if you want them purple-themed as well */
    QMenuBar {
        background-color: rgb(60, 0, 80);
        color: white;
    }
    QMenuBar::item:selected {
        background-color: rgb(90, 20, 110);
    }
    /* ... more purple menu styling ... */
    """

    # 4) Apply final combined QSS
    app.setStyleSheet(base_qss + color_overrides)

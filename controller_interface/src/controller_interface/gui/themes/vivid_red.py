# app/gui/themes/vivid_red.py

from PyQt5.QtWidgets import QStyleFactory
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
import os

def set_vivid_red_mode(app):
    app.setStyle(QStyleFactory.create("Fusion"))

    palette = QPalette()
    window_color = QColor(90, 0, 0)
    base_color   = QColor(70, 0, 0)
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
    palette.setColor(QPalette.BrightText, Qt.yellow)

    highlight_color = QColor(120, 20, 20)
    palette.setColor(QPalette.Highlight, highlight_color)
    palette.setColor(QPalette.HighlightedText, Qt.black)

    palette.setColor(QPalette.Link, QColor(255, 150, 150))
    palette.setColor(QPalette.Disabled, QPalette.Text, Qt.darkGray)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, Qt.darkGray)

    app.setPalette(palette)

    common_path = os.path.join(os.path.dirname(__file__), "common.qss")
    with open(common_path, "r", encoding="utf-8") as f:
        base_qss = f.read()

    color_overrides = """
    QPushButton#DarkButton {
        background-color: rgb(130, 10, 10);
        color: white;
        border: 2px solid rgb(150, 40, 40);
    }
    QPushButton#DarkButton:hover {
        background-color: rgb(150, 40, 40);
    }
    QPushButton#DarkButton:pressed {
        background-color: rgb(110, 0, 0);
    }

    QPushButton#LightButton {
        background-color: rgb(255, 210, 210);
        color: #333;
        border: 2px solid #999;
    }
    QPushButton#LightButton:hover {
        background-color: rgb(255, 190, 190);
    }
    QPushButton#LightButton:pressed {
        background-color: rgb(240, 160, 160);
    }
    """

    app.setStyleSheet(base_qss + color_overrides)

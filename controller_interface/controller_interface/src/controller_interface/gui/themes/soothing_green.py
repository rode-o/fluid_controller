# app/gui/themes/soothing_green.py

from PyQt5.QtWidgets import QStyleFactory
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
import os

def set_soothing_green_mode(app):
    app.setStyle(QStyleFactory.create("Fusion"))

    palette = QPalette()
    window_color = QColor(15, 30, 15)
    base_color   = QColor(10, 25, 10)
    text_color   = QColor(200, 255, 200)

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

    highlight_color = QColor(40, 80, 40)
    palette.setColor(QPalette.Highlight, highlight_color)
    palette.setColor(QPalette.HighlightedText, Qt.black)

    palette.setColor(QPalette.Link, QColor(120, 200, 120))
    palette.setColor(QPalette.Disabled, QPalette.Text, Qt.darkGray)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, Qt.darkGray)

    app.setPalette(palette)

    common_path = os.path.join(os.path.dirname(__file__), "common.qss")
    with open(common_path, "r", encoding="utf-8") as f:
        base_qss = f.read()

    color_overrides = """
    QPushButton#DarkButton {
        background-color: rgb(30, 60, 30);
        color: rgb(200,255,200);
        border: 2px solid rgb(40, 80, 40);
    }
    QPushButton#DarkButton:hover {
        background-color: rgb(40, 80, 40);
    }
    QPushButton#DarkButton:pressed {
        background-color: rgb(20, 40, 20);
    }

    QPushButton#LightButton {
        background-color: rgb(180, 220, 180);
        color: #333;
        border: 2px solid #666;
    }
    QPushButton#LightButton:hover {
        background-color: rgb(160, 200, 160);
    }
    QPushButton#LightButton:pressed {
        background-color: rgb(140, 180, 140);
    }
    """

    app.setStyleSheet(base_qss + color_overrides)

# app/gui/themes/deep_blue.py

from PyQt5.QtWidgets import QStyleFactory
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
import os

def set_deep_blue_mode(app):
    app.setStyle(QStyleFactory.create("Fusion"))

    palette = QPalette()
    window_color = QColor(20, 20, 50)
    base_color   = QColor(15, 15, 40)
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

    highlight_color = QColor(60, 60, 120)
    palette.setColor(QPalette.Highlight, highlight_color)
    palette.setColor(QPalette.HighlightedText, Qt.black)

    palette.setColor(QPalette.Link, QColor(120, 150, 200))
    palette.setColor(QPalette.Disabled, QPalette.Text, Qt.darkGray)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, Qt.darkGray)

    app.setPalette(palette)

    common_path = os.path.join(os.path.dirname(__file__), "common.qss")
    with open(common_path, "r", encoding="utf-8") as f:
        base_qss = f.read()

    color_overrides = """
    QPushButton#DarkButton {
        background-color: rgb(30, 30, 60);
        color: #fff;
        border: 2px solid rgb(50, 50, 80);
    }
    QPushButton#DarkButton:hover {
        background-color: rgb(50, 50, 80);
    }
    QPushButton#DarkButton:pressed {
        background-color: rgb(20, 20, 40);
    }

    QPushButton#LightButton {
        background-color: rgb(220, 230, 255);
        color: #333;
        border: 2px solid #555;
    }
    QPushButton#LightButton:hover {
        background-color: rgb(200, 210, 230);
    }
    QPushButton#LightButton:pressed {
        background-color: rgb(180, 190, 210);
    }
    """

    app.setStyleSheet(base_qss + color_overrides)

# app/gui/themes/light_gray.py

from PyQt5.QtWidgets import QStyleFactory
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
import os

def set_light_gray_mode(app):
    app.setStyle(QStyleFactory.create("Fusion"))

    palette = QPalette()
    window_color = QColor(230, 230, 230)
    base_color   = QColor(245, 245, 245)
    text_color   = QColor(50, 50, 50)

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

    highlight_color = QColor(180, 180, 180)
    palette.setColor(QPalette.Highlight, highlight_color)
    palette.setColor(QPalette.HighlightedText, Qt.black)

    palette.setColor(QPalette.Link, QColor(0, 100, 200))
    palette.setColor(QPalette.Disabled, QPalette.Text, Qt.darkGray)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, Qt.darkGray)

    app.setPalette(palette)

    common_path = os.path.join(os.path.dirname(__file__), "common.qss")
    with open(common_path, "r", encoding="utf-8") as f:
        base_qss = f.read()

    color_overrides = """
    QPushButton#DarkButton {
        background-color: rgb(150,150,150);
        color: #fff;
        border: 2px solid rgb(90, 90, 90);
    }
    QPushButton#DarkButton:hover {
        background-color: rgb(130,130,130);
    }
    QPushButton#DarkButton:pressed {
        background-color: rgb(110,110,110);
    }

    QPushButton#LightButton {
        background-color: rgb(235,235,235);
        color: #333;
        border: 2px solid #777;
    }
    QPushButton#LightButton:hover {
        background-color: rgb(220,220,220);
    }
    QPushButton#LightButton:pressed {
        background-color: rgb(200,200,200);
    }
    """

    app.setStyleSheet(base_qss + color_overrides)

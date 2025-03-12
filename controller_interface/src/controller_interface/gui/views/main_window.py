# app/gui/views/main_window.py

import os
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget
from PyQt5.QtCore import QSettings

from controller_interface.gui.views.home_view import HomeView
from controller_interface.gui.views.data_streamer_view import DataStreamerView
from controller_interface.gui.views.pid_tuning_view import PidTuningView

# Theme modules
from controller_interface.gui.themes.dark_purple import set_dark_purple_mode
from controller_interface.gui.themes.deep_blue import set_deep_blue_mode
from controller_interface.gui.themes.soothing_green import set_soothing_green_mode
from controller_interface.gui.themes.light_gray import set_light_gray_mode
from controller_interface.gui.themes.dark_gray import set_dark_gray_mode
from controller_interface.gui.themes.vivid_red import set_vivid_red_mode

class MainWindow(QMainWindow):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.setWindowTitle("PID Interface (Stacked)")

        # QSettings for user prefs
        self.settings = QSettings("MyCompany", "PIDInterface")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

        # Create sub-widgets/pages
        self.home_view = HomeView()
        self.data_streamer_view = DataStreamerView(self.settings)
        self.pid_tuning_view    = PidTuningView(self.settings)

        self.stacked_widget.addWidget(self.home_view)          # index 0
        self.stacked_widget.addWidget(self.data_streamer_view) # index 1
        self.stacked_widget.addWidget(self.pid_tuning_view)    # index 2

        # Connect signals for page navigation
        self.home_view.goDataStreamSignal.connect(self.goto_data_streamer)
        self.home_view.goPidTuningSignal.connect(self.goto_pid_tuning)

        # Connect theme selection signal
        self.home_view.themeSelectedSignal.connect(self.on_theme_selected)

        # If data_streamer_view, pid_tuning_view have goHomeSignal
        self.data_streamer_view.goHomeSignal.connect(self.goto_home)
        self.pid_tuning_view.goHomeSignal.connect(self.goto_home)

        # Start on Home
        self.stacked_widget.setCurrentIndex(0)

        # 1) Load last-used theme from QSettings
        saved_theme = self.settings.value("selected_theme", "")
        # 2) If it's valid, apply it and set combo
        if saved_theme in ["purple","blue","green","gray","dark_gray","vivid_red"]:
            self.apply_theme(saved_theme)
            # Update the combo in HomeView to match
            self.home_view.set_theme_combo(saved_theme)
        else:
            # If none saved, default to something, e.g. "purple"
            self.apply_theme("purple")
            self.home_view.set_theme_combo("purple")

    def goto_data_streamer(self):
        self.stacked_widget.setCurrentIndex(1)

    def goto_pid_tuning(self):
        self.stacked_widget.setCurrentIndex(2)

    def goto_home(self):
        self.stacked_widget.setCurrentIndex(0)

    def on_theme_selected(self, theme_name):
        """
        Called when user picks a new theme from the HomeView combo.
        """
        self.apply_theme(theme_name)
        self.settings.setValue("selected_theme", theme_name)

    def apply_theme(self, theme_name):
        """
        Helper method to apply the theme function to self.app.
        """
        if theme_name == "purple":
            set_dark_purple_mode(self.app)
        elif theme_name == "blue":
            set_deep_blue_mode(self.app)
        elif theme_name == "green":
            set_soothing_green_mode(self.app)
        elif theme_name == "gray":
            set_light_gray_mode(self.app)
        elif theme_name == "dark_gray":
            set_dark_gray_mode(self.app)
        elif theme_name == "vivid_red":
            set_vivid_red_mode(self.app)
        else:
            print("Unknown theme:", theme_name)

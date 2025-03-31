# controller_interface/view/views/main_window.py

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget
from PyQt5.QtCore import QSettings

# Direct subpackage imports for your views and themes
from controller_interface.view.views.home import HomeView
from controller_interface.view.views.ui import PidTuningView
from controller_interface.view.themes.dark_gray import set_dark_gray_mode


class MainWindow(QMainWindow):
    """
    A QMainWindow with a QStackedWidget having two pages:
      - HomeView (index=0)
      - PidTuningView (index=1)

    We have removed the theme selection logic.
    It just applies dark gray on startup.
    """

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.setWindowTitle("PID Interface (Stacked)")

        # Debug
        print("[DEBUG] MainWindow constructor called in:", __file__)

        # QSettings for user prefs
        self.settings = QSettings("MyCompany", "PIDInterface")
        print("[DEBUG] QSettings loaded from MyCompany/PIDInterface.")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

        # Create sub-widgets/pages
        print("[DEBUG] Creating HomeView...")
        self.home_view = HomeView()

        print("[DEBUG] Creating PidTuningView...")
        self.pid_tuning_view = PidTuningView(self.settings)

        self.stacked_widget.addWidget(self.home_view)       # index 0
        self.stacked_widget.addWidget(self.pid_tuning_view) # index 1

        # Connect signals for page navigation
        self.home_view.goPidTuningSignal.connect(self.goto_pid_tuning)
        self.pid_tuning_view.goHomeSignal.connect(self.goto_home)

        # Start on Home
        self.stacked_widget.setCurrentIndex(0)
        print("[DEBUG] StackedWidget initial index=0 => HomeView shown.")

        # Hard-code the dark gray theme
        print("[DEBUG] Forcing dark gray theme now.")
        set_dark_gray_mode(self.app)

    def goto_pid_tuning(self):
        print("[DEBUG] goto_pid_tuning() -> setCurrentIndex(1)")
        self.stacked_widget.setCurrentIndex(1)

    def goto_home(self):
        print("[DEBUG] goto_home() -> setCurrentIndex(0)")
        self.stacked_widget.setCurrentIndex(0)

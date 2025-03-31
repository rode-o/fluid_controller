# app/main.py

import sys
from PyQt5.QtWidgets import QApplication
from controller_interface import MainWindow

def main():
    app = QApplication(sys.argv)

    # Pass 'app' to MainWindow
    window = MainWindow(app)
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

"""
SmartBell SD Card Manager
Manages MP3 files on SD card for DFPlayer Mini.
Syncs sound names to ESP32 via WiFi.
"""

import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SmartBell Manager")
    app.setOrganizationName("SmartBell")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
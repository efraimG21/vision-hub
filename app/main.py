
import multiprocessing
import sys
import os
from PySide6.QtWidgets import QApplication
from __init__ import RECORDINGS_DIR, APP_NAME
from services.logger import get_logger
from widgets.main_window import MainWindow

def main():
    logger = get_logger(__name__)
    try:
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)

        os.makedirs(RECORDINGS_DIR, exist_ok=True)

        window = MainWindow()
        window.show()
        #window.showFullScreen()
        sys.exit(app.exec())

    except Exception as e:
        logger.warning(f'Error: {e}')

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
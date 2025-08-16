
import os
import platform

from PySide6.QtCore import Qt, QSettings, QTimer, QThreadPool
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget,
    QMessageBox, QDialog, QLabel
)

from app import RECORDINGS_DIR, APP_NAME

from app.services.logger import get_logger
from app.services.refresh import RefreshTask
from app.widgets.battery_widget import BatteryWidget
from app.widgets.home_widget import HomeWidget
from app.widgets.media_player_widget import MediaPlayerWidget
from app.widgets.pin_dialog import PinDialog
from app.widgets.settings_widget import SettingsWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setStyleSheet("""
            QWidget {
                background-color:rgb(41, 41, 40);
            }
        """)
        self.settings = QSettings(APP_NAME, "AxisApp")
        self.correct_pin = self.settings.value("admin_pin", "1234")

        self.logger = get_logger("MainWindow")

        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        self.stack = QStackedWidget()

        self.home = HomeWidget()
        self.settings_page = SettingsWidget()
        self.media_player_page = MediaPlayerWidget(RECORDINGS_DIR)

        self.stack.addWidget(self.home)
        self.stack.addWidget(self.settings_page)
        self.stack.addWidget(self.media_player_page)

        nav_bar = QVBoxLayout()
        nav_bar.setAlignment(Qt.AlignTop)
        nav_bar.setSpacing(15)
        nav_bar.setContentsMargins(10, 20, 10, 10)

        nav_widget = QWidget()
        nav_widget.setLayout(nav_bar)
        nav_widget.setFixedWidth(200)
        nav_widget.setStyleSheet("background-color: #2c2c2c;")


        self.home_btn = QPushButton("Home")
        self.refresh_btn = QPushButton("Refresh Videos")
        self.recording_btn = QPushButton("Start Recording")
        self.media_player_btn = QPushButton("Media Player")
        self.settings_btn = QPushButton("Settings")
        self.shutdown_btn = QPushButton("Shutdown")

        self.nav_buttons = {
            0: self.home_btn,
            1: self.settings_btn,
            2: self.media_player_btn
        }

        for btn in (self.home_btn, self.refresh_btn, self.recording_btn, self.media_player_btn, self.settings_btn, self.shutdown_btn):
            btn.setStyleSheet(self.inactive_style())
            btn.setCursor(Qt.PointingHandCursor)

        self.threadpool = QThreadPool()
        self.refresh_btn.clicked.connect(self.on_refresh_clicked)

        self.home_btn.clicked.connect(lambda: self.switch_page(0))
        self.settings_btn.clicked.connect(self.try_access_settings)
        self.recording_btn.clicked.connect(self.toggle_recording)
        self.media_player_btn.clicked.connect(lambda: self.switch_page(2))
        self.shutdown_btn.clicked.connect(self.confirm_shutdown)

        nav_bar.addWidget(self.home_btn)
        nav_bar.addWidget(self.refresh_btn)
        nav_bar.addWidget(self.recording_btn)
        nav_bar.addWidget(self.media_player_btn)
        nav_bar.addWidget(self.settings_btn)
        nav_bar.addStretch()
        nav_bar.addWidget(self.shutdown_btn)

        main_layout.addWidget(self.stack, 1)
        main_layout.addWidget(nav_widget)

        self.switch_page(0)

        self._recording = False

        # Battery widgets setup
        self.battery_widget = BatteryWidget()
        self.battery_widget.setParent(self.stack)
        self.battery_widget.setGeometry(20, -10, 70, 35) # x, y, w, h
        self.battery_widget.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.battery_widget.raise_()

        # Recording indicator setup (red dot)
        self.recording_dot = QLabel(self.stack)
        self.recording_dot.setFixedSize(14, 14)
        self.recording_dot.setStyleSheet("""
            background-color: red;
            border-radius: 7px;
        """)
        self.recording_dot.move(self.battery_widget.x() + self.battery_widget.width() + 10,
                                self.battery_widget.y() + 12)
        self.recording_dot.setVisible(False)
        self.recording_dot.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.recording_dot.raise_()

    def on_refresh_clicked(self):
        # 1) Disable button for 4 seconds and show busy text
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("Refreshing…")
        QTimer.singleShot(4000, self._reenable_refresh_btn)

        # 2) Start background task that *signals* the main thread to refresh each panel
        task = RefreshTask(self.home.panels)
        task.signals.refresh_panel.connect(self._refresh_one_panel)  # runs in main thread
        task.signals.finished.connect(self._refresh_finished)
        self.threadpool.start(task)

    def _refresh_one_panel(self, panel):
        # Safe: this runs in the GUI thread
        panel.video_label.setText("Refreshing...")
        panel.refresh_video()

    def _refresh_finished(self):
        # Optional: log or update UI; button re-enable is handled by the timer above
        self.logger.debug("Refresh task finished")

    def _reenable_refresh_btn(self):
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("Refresh Videos")

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        self.update_nav_styles(index)

    def update_nav_styles(self, active_index):
        for index, btn in self.nav_buttons.items():
            btn.setStyleSheet(self.active_style() if index == active_index else self.inactive_style())

    def active_style(self):
        return """
            QPushButton {
                background-color: #0078d4;
                color: white;
                font-size: 18px;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
        """

    def inactive_style(self):
        return """
            QPushButton {
                background-color: #444;
                color: white;
                font-size: 18px;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """

    def refresh_all_videos(self):
        for panel in self.home.panels:
            panel.video_label.setText("Refreshing...")
            panel.refresh_video()

    def toggle_recording(self):
        if not hasattr(self, "_recording"):
            self._recording = False

        if not self._recording:
            for panel in self.home.panels:
                panel.start_recording_thread()
            self._recording = True
            self.recording_btn.setText("Stop Recording")
            self.recording_dot.setVisible(True)
        else:
            self.logger.debug(f'trying to stop recording')
            for panel in self.home.panels:
                panel.stop_recording()
            self._recording = False
            self.recording_btn.setText("Start Recording")
            self.recording_dot.setVisible(False)

    def confirm_shutdown(self):
        msg_box = QMessageBox(
            QMessageBox.Question,
            "Confirm Shutdown",
            "Are you sure you want to shut down the system?",
            QMessageBox.Yes | QMessageBox.No,
            self
        )

        msg_box.setStyleSheet("""
            QMessageBox {
                color: white;
                font-size: 16px;
            }
            QLabel{
                color: white;
            }
            QPushButton {
                background-color: #444;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        reply = msg_box.exec()

        if reply == QMessageBox.Yes:
            self.shutdown_system()

    def close_stream(self):
        #TODO: make close for recording, streaming;
        pass

    def shutdown_system(self):
        system = platform.system()
        if system == "Windows":
            os.system("shutdown /s /t 1")
        elif system in ["Linux", "Darwin"]:
            try:
                if hasattr(os, "geteuid") and os.geteuid() != 0:
                    QMessageBox.critical(self, "Permission Denied", "Please run the application as root to shutdown.") # TODO: in white color
                    return
                os.system("shutdown -h now")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Shutdown failed: {str(e)}")
        else:
            QMessageBox.warning(self, "Unsupported OS", "Shutdown not supported on this OS.") # TODO: in white color

    def try_access_settings(self):
        dialog = PinDialog(self, correct_pin=self.correct_pin)
        if dialog.exec() == QDialog.Accepted:
            self.switch_page(1)

    def closeEvent(self, event):
        for panel in self.home.panels:
            if panel.video_thread and panel.video_thread.isRunning():
                panel.video_thread.stop()
                panel.stop_recording()
        super().closeEvent(event)


import datetime
import os

import ping3
from queue import Queue

import cv2
from PySide6.QtCore import Qt, QSettings, Signal, QSize
from PySide6.QtGui import QPixmap, QImage, QMouseEvent, QTouchEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy

from app import AXIS_PASSWORD, AXIS_USER_NAME, RECORDINGS_DIR, APP_NAME
from app.services.logger import get_logger
from app.widgets.video_recorder_thread import VideoRecorder
from app.widgets.video_capture_thread import VideoCaptureThread

NO_IP = "Does not have an assigned IP address."

class PanelWidget(QWidget):
    doubleClicked = Signal(str)

    def __init__(self, title, stream_ip, panel_index):
        super().__init__()

        self.logger = get_logger('PanelWidget')

        self.title = title
        self.stream_ip = stream_ip
        self.video_url = f'rtsp://{AXIS_USER_NAME}:{AXIS_PASSWORD}@{stream_ip}/axis-media/media.amp' if stream_ip else None
        self.panel_index = panel_index

        self.settings = QSettings(APP_NAME, "AxisApp")

        self._scale_factor = 1.0
        self._user_zoomed = False
        self.current_pixmap = None

        self._is_recording = False
        self._frame_recording_queue = Queue(maxsize=500)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(title)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: white; font-size: 16px;")
        self.layout.addWidget(self.label)

        self.video_label = QLabel("Starting camera...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; color: white;")
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.video_label)

        self.video_thread = None
        self.recorder = None
        self.video_cap: cv2.VideoCapture | None = None

        if self.video_url:
            self.start_video_thread()
        else:
            self.video_label.setText(NO_IP)

        self.setMinimumSize(QSize(500, 340)) # TODO: try to make responsive not by size this is the value of 'self.current_pixmap'
        self.setAttribute(Qt.WA_AcceptTouchEvents, True)


    def set_cap(self, video_capture):
        self.video_cap = video_capture

        if self._is_recording and (not self.recorder):
            self.logger.debug(f'starting recording after pressing button.')
            self.start_recording_thread()

    def ping_test(self):
        try:
            response = ping3.ping(dest_addr=self.stream_ip, timeout=2)
            return not response
        except ping3.errors.PingError:
            self.logger.warning(f'A ping error raised for {self.stream_ip}.')
            return False

    def on_frame_received(self, frame):
        if frame is None:
            self.video_label.setText("Camera failed to open.")
            self.video_thread.stop()
            self.video_thread.wait()
            self.video_thread = None
            return

        if self._is_recording and self._frame_recording_queue.not_full:
            self._frame_recording_queue.put(frame)

        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.current_pixmap = QPixmap.fromImage(qt_image)
        self.update_scaled_pixmap()

    def update_scaled_pixmap(self):
        if not self.current_pixmap:
            return

        if self._user_zoomed:
            base_size = self.current_pixmap.size()
            desired_width = base_size.width() * self._scale_factor
            desired_height = base_size.height() * self._scale_factor
            scaled_pixmap = self.current_pixmap.scaled(
                int(desired_width),
                int(desired_height),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        else:
            target_size = self.video_label.size()
            scaled_pixmap = self.current_pixmap.scaled(
                target_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

        self.video_label.setPixmap(scaled_pixmap)

    def start_video_thread(self):
        self.video_thread = VideoCaptureThread(self.video_url)
        self.video_thread.frame_received.connect(self.on_frame_received)
        self.video_thread.cap_capture_signal.connect(self.set_cap)
        self.video_thread.start()

    def start_recording_thread(self):
        self._is_recording = True
        if not self.video_url:
            self.logger.warning("No video URL for recording.")
            return
        if (not self.video_thread) or (not  self.video_cap):
            self.logger.warning("No video capture for recording.")
            return

        width = int(self.video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self.video_cap.get(cv2.CAP_PROP_FPS)
        self.logger.debug(f'width: {width}, height: {height}, fps: {fps}')
        if fps <= 1:
            fps = 25  # fallback

        filename = f"{self.title.replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        output_path = os.path.join(RECORDINGS_DIR, filename)
        self.recorder = VideoRecorder(
                                output_path=output_path,
                                frame_queue=self._frame_recording_queue,
                                fps=fps,
                                width=width,
                                height=height,
                                panel_name=self.title
                            )
        self.recorder.start()
        self.logger.info(f"Started recording: {output_path}")

    def stop_recording(self):
        self._is_recording = False

        if self.recorder:
            if self.recorder.isRunning():
                self.recorder.stop()
                self.recorder.wait()
            self.recorder = None


        self.logger.info(f"Stopped recording: {self.title}")

    def refresh_video(self):
        if self.video_thread:
            if self.video_thread.isRunning():
                self.video_thread.stop()
                self.video_thread.wait()
            self.video_thread = None


        ip_addbase = self.settings.value(f'device_{self.panel_index}/ip')
        nickname = self.settings.value(f"device_{self.panel_index}/name")
        self.logger.debug(f'Ip Address after refresh: {ip_addbase}')

        self.stream_ip = ip_addbase if ip_addbase else None
        self.video_url = f'rtsp://{AXIS_USER_NAME}:{AXIS_PASSWORD}@{self.stream_ip}/axis-media/media.amp' if self.stream_ip else None
        self.title = nickname if nickname else f'Panel {self.panel_index + 1}'
        self.label.setText(self.title)

        if self.video_url:
            self.start_video_thread()
        else:
            self.video_label.setText(NO_IP)


    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self._scale_factor = 1.0
        self._user_zoomed = False
        self.update_scaled_pixmap()
        self.doubleClicked.emit(self.title)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._user_zoomed:
            self.update_scaled_pixmap()

    def touchEvent(self, event: QTouchEvent):
        self.logger.debug(f'event: {event.touchPoints()}')

    def closeEvent(self, event):
        if self.video_thread.isRunning():
            self.video_thread.stop()
            self.video_thread.wait()
        event.accept()
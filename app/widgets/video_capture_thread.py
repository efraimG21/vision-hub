

import cv2
import time

from PySide6.QtCore import Signal, QThread

from app.services.logger import get_logger
from app.services.safe_video_capture import open_capture


class VideoCaptureThread(QThread):
    frame_received = Signal(object)
    video_error = Signal(str)
    cap_capture_signal = Signal(object)

    def __init__(self, video_source):
        super().__init__()
        self.video_source = video_source
        self.cap: cv2.VideoCapture | None = None
        self.running = False
        self.logger = get_logger('VideoThread')
        self.ret_none_counter = 0

    def run(self):
        try:
            self.logger.info(f'trying video capture for: {self.video_source}')
            self.cap = open_capture(self.video_source)
            if not self.cap:
                self.logger.warning(f'Failed to open video source for: {self.video_source}')
                return

            self.cap_capture_signal.emit(self.cap)

            self.running = True
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 0)
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    self.running = False
                    self.logger.debug('Frame read failed, skipping...')
                    continue
                self.frame_received.emit(frame)
        except Exception as e:
            self.logger.exception(f'Exception in video thread: {e}')
            self.video_error.emit(str(e))
        finally:
            if self.cap:
                self.cap.release()
                self.cap = None
            self.logger.info('Video thread stopped and camera released.')


    def stop(self):
        self.running = False

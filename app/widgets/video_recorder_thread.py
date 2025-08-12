
import time
from datetime import datetime
from queue import Queue
import cv2
from PySide6.QtCore import QThread

from app.services.logger import get_logger


class VideoRecorder(QThread):
    def __init__(self, panel_name, output_path, frame_queue: Queue, fps, width, height, parent=None):
        super().__init__(parent)
        self.panel_name = panel_name
        self.output_path = output_path
        self.frame_queue = frame_queue
        self.running = False
        self.fps = fps
        self.width = width
        self.height = height
        self.logger = get_logger('VideoRecorder')

    def run(self):
        self.running = True
        writer = None
        print(self.output_path, self.fps, (self.width, self.height))
        try:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(self.output_path, fourcc, self.fps, (self.width, self.height))

            while self.running:
                if self.frame_queue.empty():
                    print('queue is empty')
                    time.sleep(0.05)
                    continue

                frame = self.frame_queue.get()
                now = datetime.now()
                cv2.putText(frame, f'{self.panel_name} {now.strftime('%y-%m-%d')} {now.strftime('%H:%M')}'
                            ,(10,10), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255),1, cv2.LINE_AA)
                writer.write(frame)

        except Exception as e:
            self.logger.warning(f'Exception a curr in the recording of the {self.stream_url} as : {e}')

        finally:
            while not self.frame_queue.empty():
                self.frame_queue.get()
            if writer:
                writer.release()
                self.logger.info(f"Recording saved: {self.output_path}")

    def stop(self):
        self.running = False
        self.wait()

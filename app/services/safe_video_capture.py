

import multiprocessing
import cv2

from services.logger import get_logger

logger = get_logger(__name__)

def _try_open_worker(video_url, queue):
    cap = cv2.VideoCapture(0)
    queue.put(True if cap.isOpened() else False)
    cap.release()

def open_capture(video_url, timeout=5):
    if multiprocessing.current_process().name != 'MainProcess':
        return None

    queue = multiprocessing.Queue(maxsize=1)
    process = multiprocessing.Process(target=_try_open_worker, args=(video_url, queue))
    process.start()
    process.join(timeout)
    if process.is_alive():
        process.terminate()
        process.join(timeout=0.5)
        logger.info(f"Timeout occurred while opening {video_url}")
        return None

    result = queue.get()
    return cv2.VideoCapture(0) if result else None





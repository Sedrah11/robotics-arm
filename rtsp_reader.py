# rtsp_reader.py
import time
import cv2
import queue
import threading


def _drop_oldest_and_put(q: queue.Queue, item):
    
    try:
        q.put_nowait(item)
    except queue.Full:
        try:
            _ = q.get_nowait()
        except queue.Empty:
            pass
        try:
            q.put_nowait(item)
        except queue.Full:
            pass


class RTSPReader(threading.Thread):
    def __init__(self, rtsp_url: str, frame_q: queue.Queue, target_fps: int,
                 reconnect_backoff: float = 2.0):
        super().__init__(daemon=True)
        self.rtsp_url = rtsp_url
        self.frame_q = frame_q
        self.target_fps = max(1, int(target_fps))
        self.reconnect_backoff = reconnect_backoff

        self._stop_event = threading.Event()
        self.cap = None

    def stop(self):
        self._stop_event.set()

    def _connect(self):
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass

        self.cap = cv2.VideoCapture(self.rtsp_url)
        return self.cap.isOpened()

    def run(self):
        period = 1.0 / self.target_fps
        while not self._stop_event.is_set():
            if self.cap is None or not self.cap.isOpened():
                ok = self._connect()
                if not ok:
                    print("[RTSP] Failed to connect. Retrying...")
                    time.sleep(self.reconnect_backoff)
                    continue
                print("[RTSP] Connected.")

            t0 = time.time()
            ret, frame = self.cap.read()
            if not ret or frame is None:
                print("[RTSP] Read failed. Reconnecting...")
                try:
                    self.cap.release()
                except Exception:
                    pass
                self.cap = None
                time.sleep(self.reconnect_backoff)
                continue

            _drop_oldest_and_put(self.frame_q, frame)

            dt = time.time() - t0
            sleep_time = period - dt
            if sleep_time > 0:
                time.sleep(sleep_time)

        # cleanup
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
        print("[RTSP] Stopped.")

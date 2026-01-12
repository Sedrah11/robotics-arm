# detector.py
import time
import cv2
import numpy as np
from ultralytics import YOLO
from typing import Optional


class YOLODetector:
    def __init__(self, model_path: str, resize_width: Optional[int] = None):
        self.model = YOLO(model_path)
        self.resize_width = resize_width

    def _maybe_resize(self, frame: np.ndarray) -> np.ndarray:
        if self.resize_width is None:
            return frame

        h, w = frame.shape[:2]
        if w <= self.resize_width:
            return frame

        new_w = self.resize_width
        new_h = int(h * (new_w / w))
        return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

    def infer_and_annotate(self, frame: np.ndarray) -> np.ndarray:
        frame = self._maybe_resize(frame)

        results = self.model(frame, verbose=True)[0]

        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            name = results.names.get(cls_id, str(cls_id))

            label = f"{name} {conf:.2f}"

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame,
                label,
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
                cv2.LINE_AA
            )

        cv2.putText(
            frame,
            time.strftime("%H:%M:%S"),
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )
        # cv2.imshow("image", frame)
        # cv2.waitKey("q")
    
    # 4. Close all open windows
        # cv2.destroyAllWindows()
        return frame

    @staticmethod
    def encode_jpeg(frame: np.ndarray, quality: int = 80) -> bytes:
        ok, buf = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, int(quality)]
        )
        if not ok:
            return b""
        return buf.tobytes()

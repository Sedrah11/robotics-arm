# config.py


# INPUT MODE

USE_RTSP = True   



# RTSP CONFIG

RTSP_URL = "rtsp://admin:qss2030qss@192.168.100.180:554/stream1"


RECONNECT_BACKOFF_SEC = 3.0



# YOLO CONFIG

MODEL_PATH = "models/best.pt"
CONF_THRESHOLD = 0.4

RESIZE_WIDTH = 960



# STREAMING / PERFORMANCE

QUEUE_SIZE = 2
TARGET_FPS = 75
JPEG_QUALITY = 80



# SERVER CONFIG

HOST = "0.0.0.0"
PORT = 8001


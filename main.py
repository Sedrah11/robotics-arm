# main.py
import asyncio
import queue
import uvicorn

from config import (
    RTSP_URL, MODEL_PATH, HOST, PORT,
    QUEUE_SIZE, TARGET_FPS, JPEG_QUALITY,
    RECONNECT_BACKOFF_SEC, RESIZE_WIDTH,
    USE_RTSP,
)

from rtsp_reader import RTSPReader
from detector import YOLODetector
from streamer import WSBroadcaster


async def inference_loop(frame_q: queue.Queue, detector: YOLODetector, ws: WSBroadcaster):
    loop = asyncio.get_event_loop()
    while True:
        frame = await loop.run_in_executor(None, frame_q.get)
        annotated = detector.infer_and_annotate(frame)
        jpeg = detector.encode_jpeg(annotated, quality=JPEG_QUALITY)
        if jpeg:
            await ws.update_latest(jpeg)


async def start_background_tasks(ws: WSBroadcaster, frame_q: queue.Queue):
    detector = YOLODetector(MODEL_PATH, resize_width=RESIZE_WIDTH)
    asyncio.create_task(inference_loop(frame_q, detector, ws))
    asyncio.create_task(ws.broadcast_loop(target_fps=TARGET_FPS))


def run():
    frame_q = queue.Queue(maxsize=QUEUE_SIZE)

    #  Web server ALWAYS starts
    ws = WSBroadcaster()

    @ws.app.on_event("startup")
    async def _startup():
        await start_background_tasks(ws, frame_q)

    #  RTSP starts ONLY if enabled
    if USE_RTSP:
        reader = RTSPReader(
            rtsp_url=RTSP_URL,
            frame_q=frame_q,
            target_fps=TARGET_FPS,
            reconnect_backoff=RECONNECT_BACKOFF_SEC,
        )
        reader.start()
    else:
        print("[INFO] USE_RTSP=False → Web server will run without camera.")

    uvicorn.run(ws.app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    run()

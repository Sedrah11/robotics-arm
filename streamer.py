# streamer.py

import asyncio
import os
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles


class WSBroadcaster:
    def __init__(self):
        self.app = FastAPI()

        #   path to /static (fixes 404 on Windows/VS Code)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        static_dir = os.path.join(base_dir, "static")

        print(f"[INFO] Static dir: {static_dir}")

        self.app.mount("/static", StaticFiles(directory=static_dir), name="static")

        self.clients = set()
        self.latest_jpeg: Optional[bytes] = None
        self.latest_lock = asyncio.Lock()

        @self.app.get("/")
        async def root():
            return HTMLResponse(
                "<h3>Server running. Open <a href='/static/index.html'>/static/index.html</a></h3>"
            )

        @self.app.websocket("/ws")
        async def ws_endpoint(ws: WebSocket):
            await ws.accept()
            self.clients.add(ws)
            print(f"[WS] Client connected. Total: {len(self.clients)}")

            try:
                while True:
                    await ws.receive_text()
            except WebSocketDisconnect:
                pass
            finally:
                self.clients.discard(ws)
                print(f"[WS] Client disconnected. Total: {len(self.clients)}")

    async def update_latest(self, jpeg_bytes: bytes):
        if not self.clients:
            return

        dead = []
        for ws in list(self.clients):
            try:
                await ws.send_bytes(jpeg_bytes)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.clients.discard(ws)


    async def broadcast_loop(self, target_fps: int = 25):
        period = 1.0 / max(1, int(target_fps))

        while True:
            start = asyncio.get_event_loop().time()

            async with self.latest_lock:
                data = self.latest_jpeg

            if data and self.clients:
                dead = []
                for ws in list(self.clients):
                    try:
                        await asyncio.gather(
                            *[ws.send_bytes(data) for ws in list(self.clients)],
                            return_exceptions=True
                        )
                    except Exception:
                        dead.append(ws)

                for ws in dead:
                    self.clients.discard(ws)

            elapsed = asyncio.get_event_loop().time() - start
            sleep_time = period - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

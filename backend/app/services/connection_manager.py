"""
Minimal WebSocket connection manager for broadcasting live telemetry.

Kept intentionally simple: a single in-process list of active connections.
This is appropriate for a single-process demo/college-project deployment
(the same one this whole app already assumes — SQLite, no worker pool).
It is not a distributed pub/sub system, which is not needed here.
"""
import asyncio
import json
import logging

from fastapi import WebSocket

logger = logging.getLogger("cyber_twin.live")


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.append(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            if websocket in self._connections:
                self._connections.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        payload = json.dumps(message, default=str)
        dead: list[WebSocket] = []
        async with self._lock:
            connections = list(self._connections)
        for ws in connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    if ws in self._connections:
                        self._connections.remove(ws)

    @property
    def active_count(self) -> int:
        return len(self._connections)


manager = ConnectionManager()

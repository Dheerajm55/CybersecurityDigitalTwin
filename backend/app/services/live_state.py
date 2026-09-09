"""
In-memory control state for the live telemetry background loop.

A single-process flag is sufficient here — this app already assumes a
single-process/SQLite deployment (see ARCHITECTURE.md), so there is no
need for a shared/distributed state store for a "paused" boolean.
"""
import asyncio


class LiveState:
    def __init__(self) -> None:
        self.paused: bool = False
        self.interval_seconds: float = 8.0
        self._task: asyncio.Task | None = None

    def set_task(self, task: asyncio.Task) -> None:
        self._task = task

    def cancel(self) -> None:
        if self._task:
            self._task.cancel()


live_state = LiveState()

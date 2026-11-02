"""WebSocket client from the body (Pi) to the brain (Mac).

Messages are JSON objects with a "type" field.
  brain -> body: ping {t}, drive {left, right}, stop, estop, reset
  body -> brain: hello, pong {t}, telemetry {...}, event {text}
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Awaitable, Callable

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed, InvalidHandshake, InvalidURI

from body.motors import DriveController

log = logging.getLogger("torq.link")

PROTOCOL_VERSION = 1


class BodyLink:
    def __init__(
        self,
        urls: list[str],
        motors: DriveController,
        telemetry: Callable[[], Awaitable[dict]],
        telemetry_interval_s: float = 0.5,
        camera_port: int | None = None,
    ) -> None:
        self.urls = urls
        self.motors = motors
        self._telemetry = telemetry
        self._telemetry_interval_s = telemetry_interval_s
        self._camera_port = camera_port
        self._ws: ClientConnection | None = None
        self.connected_url: str | None = None

    async def send_event(self, text: str) -> None:
        ws = self._ws
        if ws is None:
            return
        try:
            await ws.send(json.dumps({"type": "event", "text": text}))
        except ConnectionClosed:
            pass  # the session loop notices and reconnects

    def handle(self, msg: dict) -> dict | None:
        """Apply one brain message. Returns a reply to send, if any."""
        kind = msg.get("type")
        if kind == "ping":
            return {"type": "pong", "t": msg.get("t")}
        if kind == "drive":
            try:
                left, right = float(msg["left"]), float(msg["right"])
            except (KeyError, TypeError, ValueError):
                return {"type": "event", "text": "ERR bad drive message"}
            if not self.motors.drive(left, right):
                return {"type": "event", "text": "drive refused: e-stop or fault active"}
            return None
        if kind == "stop":
            self.motors.stop()
        elif kind == "estop":
            self.motors.estop()
        elif kind == "reset":
            self.motors.reset()
        else:
            return {"type": "event", "text": f"ERR unknown message type: {kind!r}"}
        return None

    async def _session(self, ws: ClientConnection) -> None:
        await ws.send(json.dumps({
            "type": "hello", "role": "body", "version": PROTOCOL_VERSION,
            "camera_port": self._camera_port,
        }))

        async def push_telemetry() -> None:
            while True:
                data = await self._telemetry()
                data["motors"] = self.motors.status()
                await ws.send(json.dumps({"type": "telemetry", **data}))
                await asyncio.sleep(self._telemetry_interval_s)

        pusher = asyncio.create_task(push_telemetry())
        try:
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    log.warning("ignoring non-JSON message")
                    continue
                if not isinstance(msg, dict):
                    continue
                reply = self.handle(msg)
                if reply is not None:
                    await ws.send(json.dumps(reply))
        finally:
            pusher.cancel()
            try:
                await pusher
            except (asyncio.CancelledError, ConnectionClosed):
                pass

    async def run(self) -> None:
        backoff = 0.5
        while True:
            for url in self.urls:
                try:
                    async with connect(url, open_timeout=3, ping_interval=1, ping_timeout=2) as ws:
                        log.info("connected to brain at %s", url)
                        self._ws, self.connected_url = ws, url
                        backoff = 0.5
                        try:
                            await self._session(ws)
                        except ConnectionClosed:
                            pass
                except (OSError, InvalidHandshake, InvalidURI, asyncio.TimeoutError) as exc:
                    log.debug("could not reach %s: %s", url, exc)
                    continue
                finally:
                    if self._ws is not None:
                        # Link lost: never keep driving without a brain.
                        self.motors.stop()
                        log.warning("brain link lost; motors stopped")
                    self._ws, self.connected_url = None, None
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 5.0)

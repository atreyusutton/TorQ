"""TorQ brain: runs on the Mac.

Two listeners:
  - body port (default 8765, all interfaces): the Pi connects to /body
  - UI port (default 8000, localhost only): dashboard page and its /ws socket
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import math
import time
from pathlib import Path

import yaml
from aiohttp import WSMsgType, web

from brain.state import RobotState

log = logging.getLogger("torq.brain")

ROOT = Path(__file__).resolve().parent
DASHBOARD = ROOT / "dashboard"
DEFAULT_CONFIG = ROOT.parent / "config.yaml"
STATUS_INTERVAL_S = 0.2


class Brain:
    def __init__(self, ping_interval_s: float = 1.0) -> None:
        self.state = RobotState()
        self.body_ws: web.WebSocketResponse | None = None
        self.ui_clients: set[web.WebSocketResponse] = set()
        self.ping_interval_s = ping_interval_s

    # ---- talking to the body ---------------------------------------------

    async def send_body(self, msg: dict) -> bool:
        ws = self.body_ws
        if ws is None or ws.closed:
            return False
        try:
            await ws.send_json(msg)
            return True
        except ConnectionError as exc:
            log.warning("send to body failed: %s", exc)
            return False

    async def body_handler(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse(heartbeat=2.0)
        await ws.prepare(request)

        if self.body_ws is not None and not self.body_ws.closed:
            log.warning("new body connection replaces the old one")
            await self.body_ws.close()
        self.body_ws = ws
        s = self.state
        s.body_connected, s.body_addr, s.rtt_ms = True, request.remote, None
        s.log(f"body connected from {request.remote}")
        log.info("body connected from %s", request.remote)

        pinger = asyncio.create_task(self._ping_body(ws))
        try:
            async for msg in ws:
                if msg.type != WSMsgType.TEXT:
                    continue
                try:
                    data = json.loads(msg.data)
                except json.JSONDecodeError:
                    log.warning("non-JSON from body ignored")
                    continue
                self._on_body_message(data)
        finally:
            pinger.cancel()
            if self.body_ws is ws:
                self.body_ws = None
                s.body_connected, s.rtt_ms = False, None
                s.log("body disconnected")
                log.warning("body disconnected")
        return ws

    def _on_body_message(self, data: dict) -> None:
        s = self.state
        kind = data.get("type")
        if kind == "hello":
            s.camera_port = data.get("camera_port")
            if s.estop:
                # A restarted body forgets its e-stop; re-apply it.
                asyncio.get_running_loop().create_task(self.send_body({"type": "estop"}))
        elif kind == "pong":
            t = data.get("t")
            if isinstance(t, (int, float)):
                s.rtt_ms = round((time.monotonic() - t) * 1000, 1)
        elif kind == "telemetry":
            s.telemetry = {k: v for k, v in data.items() if k != "type"}
            motors = s.telemetry.get("motors") or {}
            # An e-stop can be raised from either side but only cleared by
            # an explicit reset from the dashboard.
            if motors.get("estop"):
                s.estop = True
        elif kind == "event":
            s.log(str(data.get("text")))

    async def _ping_body(self, ws: web.WebSocketResponse) -> None:
        while not ws.closed:
            try:
                await ws.send_json({"type": "ping", "t": time.monotonic()})
            except ConnectionError:
                return
            await asyncio.sleep(self.ping_interval_s)

    # ---- the dashboard ------------------------------------------------------

    async def ui_handler(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse(heartbeat=5.0)
        await ws.prepare(request)
        self.ui_clients.add(ws)
        try:
            await ws.send_json(self.state.to_json())
            async for msg in ws:
                if msg.type != WSMsgType.TEXT:
                    continue
                try:
                    data = json.loads(msg.data)
                except json.JSONDecodeError:
                    continue
                await self._on_ui_message(data)
        finally:
            self.ui_clients.discard(ws)
            # A closed dashboard must not leave the robot moving.
            if not self.ui_clients:
                await self.send_body({"type": "stop"})
        return ws

    async def _on_ui_message(self, data: dict) -> None:
        s = self.state
        kind = data.get("type")
        if kind == "drive":
            left, right = data.get("left"), data.get("right")
            if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (left, right)):
                return
            if s.estop:
                return
            if not s.manual:
                s.manual = True
                s.log("manual override ON")
            await self.send_body({
                "type": "drive",
                "left": max(-1.0, min(1.0, float(left))),
                "right": max(-1.0, min(1.0, float(right))),
            })
        elif kind == "stop":
            await self.send_body({"type": "stop"})
        elif kind == "estop":
            s.estop = True
            s.log("E-STOP")
            await self.send_body({"type": "estop"})
        elif kind == "reset":
            s.estop = False
            s.log("e-stop reset")
            await self.send_body({"type": "reset"})
        elif kind == "manual":
            s.manual = bool(data.get("on"))
            s.log(f"manual override {'ON' if s.manual else 'OFF'}")
            if not s.manual:
                await self.send_body({"type": "stop"})

    async def broadcast_status(self) -> None:
        while True:
            if self.ui_clients:
                payload = self.state.to_json()
                for ws in list(self.ui_clients):
                    try:
                        await ws.send_json(payload)
                    except ConnectionError:
                        self.ui_clients.discard(ws)
            await asyncio.sleep(STATUS_INTERVAL_S)


async def index(request: web.Request) -> web.FileResponse:
    return web.FileResponse(DASHBOARD / "index.html")


def make_apps(brain: Brain) -> tuple[web.Application, web.Application]:
    body_app = web.Application()
    body_app.router.add_get("/body", brain.body_handler)

    ui_app = web.Application()
    ui_app.router.add_get("/", index)
    ui_app.router.add_get("/ws", brain.ui_handler)
    ui_app.router.add_static("/static/", DASHBOARD)
    return body_app, ui_app


async def start(brain: Brain, cfg: dict) -> list[web.AppRunner]:
    body_app, ui_app = make_apps(brain)
    runners = []
    for app, host, port in (
        (body_app, cfg["body_host"], cfg["body_port"]),
        (ui_app, cfg["ui_host"], cfg["ui_port"]),
    ):
        runner = web.AppRunner(app)
        await runner.setup()
        await web.TCPSite(runner, host, port).start()
        runners.append(runner)
    return runners


async def amain(config_path: Path) -> None:
    cfg = yaml.safe_load(config_path.read_text())["brain"]
    brain = Brain(ping_interval_s=cfg.get("ping_interval_s", 1.0))
    runners = await start(brain, cfg)
    log.info("dashboard: http://%s:%s  body port: %s", cfg["ui_host"], cfg["ui_port"], cfg["body_port"])
    try:
        await brain.broadcast_status()
    finally:
        for r in runners:
            await r.cleanup()


def main() -> None:
    p = argparse.ArgumentParser(description="TorQ brain (Mac)")
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        asyncio.run(amain(args.config))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

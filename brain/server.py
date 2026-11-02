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

import anthropic
import yaml
from aiohttp import WSMsgType, web
from dotenv import load_dotenv

from brain.claude import ClaudeConfig, Conversation
from brain.memory import JobMemory
from brain.speech import SpeechToText, TextToSpeech
from brain.state import RobotState
from brain.tools import ToolContext
from brain.voice import MIC_FRAME, Assistant

log = logging.getLogger("torq.brain")

ROOT = Path(__file__).resolve().parent
DASHBOARD = ROOT / "dashboard"
REPO = ROOT.parent
DEFAULT_CONFIG = REPO / "config.yaml"
STATUS_INTERVAL_S = 0.2


class Brain:
    def __init__(self, ping_interval_s: float = 1.0) -> None:
        self.state = RobotState()
        self.body_ws: web.WebSocketResponse | None = None
        self.ui_clients: set[web.WebSocketResponse] = set()
        self.ping_interval_s = ping_interval_s
        self.assistant: Assistant | None = None
        self.memory: JobMemory | None = None
        self.claude_ready = False

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

    async def send_body_bytes(self, data: bytes) -> bool:
        ws = self.body_ws
        if ws is None or ws.closed:
            return False
        try:
            await ws.send_bytes(data)
            return True
        except ConnectionError as exc:
            log.warning("send to body failed: %s", exc)
            return False

    async def stop_robot(self) -> None:
        await self.send_body({"type": "stop"})

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
                if msg.type == WSMsgType.BINARY:
                    if msg.data[:1] == bytes([MIC_FRAME]) and self.assistant:
                        self.assistant.on_mic_audio(msg.data[1:])
                    continue
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
        elif kind == "mic_end" and self.assistant:
            self.assistant.on_mic_end()
        elif kind == "speak_done" and self.assistant:
            self.assistant.on_speak_done()

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
            await ws.send_json(self.status_json())
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
        elif kind == "chat" and self.assistant:
            text = data.get("text")
            if isinstance(text, str) and len(text) <= 2000:
                await self.assistant.ask_text(text)
        elif kind == "talk" and self.assistant:
            if data.get("on"):
                await self.assistant.talk_start()
            else:
                await self.assistant.talk_stop()
        elif kind == "hush" and self.assistant:
            await self.assistant.interrupt()
        elif kind == "new_chat" and self.assistant:
            await self.assistant.interrupt()
            self.assistant.reset()
        elif kind == "manual":
            s.manual = bool(data.get("on"))
            s.log(f"manual override {'ON' if s.manual else 'OFF'}")
            if not s.manual:
                await self.send_body({"type": "stop"})

    def status_json(self) -> dict:
        payload = self.state.to_json()
        payload["claude_ready"] = self.claude_ready
        payload["chat"] = list(self.assistant.chat) if self.assistant else []
        payload["job"] = self.memory.summary() if self.memory else None
        return payload

    async def broadcast_status(self) -> None:
        while True:
            if self.ui_clients:
                payload = self.status_json()
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


def setup_assistant(brain: Brain, full_cfg: dict) -> list[asyncio.Task]:
    """Wire up Claude, speech, and job memory. Returns warm-up tasks."""
    voice_cfg = full_cfg["voice"]
    load_dotenv(REPO / ".env")  # read-only; never written
    try:
        client = anthropic.AsyncAnthropic()
        if not (client.api_key or client.auth_token):
            log.error("no ANTHROPIC_API_KEY found; add it to %s and restart the brain", REPO / ".env")
            brain.state.log("Claude not configured: add ANTHROPIC_API_KEY to .env and restart the brain")
            client = None
        brain.claude_ready = client is not None
    except anthropic.AnthropicError as exc:
        log.error("Claude not configured (%s). Add ANTHROPIC_API_KEY to %s", exc, REPO / ".env")
        client = None
        brain.state.log("Claude not configured: add ANTHROPIC_API_KEY to .env")

    brain.memory = JobMemory(REPO / "data" / "job.json")
    conversation = Conversation(
        client,
        ClaudeConfig.from_dict(full_cfg.get("claude", {})),
        ToolContext(memory=brain.memory, stop_robot=brain.stop_robot),
    )
    stt = SpeechToText(voice_cfg["stt_model"], REPO / "data" / "whisper", voice_cfg.get("stt_hint"))
    tts = TextToSpeech(REPO / voice_cfg["tts_voice"])
    brain.assistant = Assistant(
        brain.state, conversation, stt, tts, brain.send_body, brain.send_body_bytes,
        mic_rate=voice_cfg.get("mic_rate", 16000),
    )

    async def warm(name: str, coro) -> None:
        try:
            await coro
            log.info("%s ready", name)
        except Exception as exc:
            log.exception("%s failed to load", name)
            brain.state.log(f"{name} failed to load: {exc}")

    return [
        asyncio.create_task(warm("speech-to-text", stt.warm_up())),
        asyncio.create_task(warm("text-to-speech", tts.warm_up())),
    ]


async def amain(config_path: Path) -> None:
    full_cfg = yaml.safe_load(config_path.read_text())
    cfg = full_cfg["brain"]
    brain = Brain(ping_interval_s=cfg.get("ping_interval_s", 1.0))
    warmups = setup_assistant(brain, full_cfg)
    runners = await start(brain, cfg)
    log.info("dashboard: http://%s:%s  body port: %s", cfg["ui_host"], cfg["ui_port"], cfg["body_port"])
    try:
        await brain.broadcast_status()
    finally:
        for t in warmups:
            t.cancel()
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

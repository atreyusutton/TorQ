"""What TorQ is doing right now. The brain owns this; the Pi only renders it."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum


class Mode(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    DRIVING = "driving"   # Claude is moving the robot
    MANUAL = "manual"     # keyboard has the controls
    ERROR = "error"       # link lost, e-stop, or drive fault


@dataclass
class RobotState:
    body_connected: bool = False
    body_addr: str | None = None
    camera_port: int | None = None
    rtt_ms: float | None = None
    telemetry: dict = field(default_factory=dict)
    manual: bool = False
    estop: bool = False
    activity: Mode = Mode.IDLE  # set by the voice/Claude pipeline later
    events: deque = field(default_factory=lambda: deque(maxlen=50))

    def log(self, text: str) -> None:
        self.events.append({"t": time.time(), "text": text})

    @property
    def drive_fault(self) -> str | None:
        return (self.telemetry.get("motors") or {}).get("fault")

    @property
    def arduino_connected(self) -> bool:
        return bool((self.telemetry.get("motors") or {}).get("connected"))

    def mode(self) -> Mode:
        if not self.body_connected or self.estop or self.drive_fault:
            return Mode.ERROR
        if self.activity != Mode.IDLE:
            return self.activity  # listening / thinking / speaking matter most to the user
        if self.manual:
            return Mode.MANUAL
        return Mode.IDLE

    def camera_url(self) -> str | None:
        if not (self.body_connected and self.body_addr and self.camera_port):
            return None
        return f"http://{self.body_addr}:{self.camera_port}/stream"

    def to_json(self) -> dict:
        return {
            "type": "status",
            "mode": self.mode().value,
            "body_connected": self.body_connected,
            "body_addr": self.body_addr,
            "arduino_connected": self.arduino_connected,
            "camera_url": self.camera_url(),
            "rtt_ms": self.rtt_ms,
            "manual": self.manual,
            "estop": self.estop,
            "fault": self.drive_fault,
            "telemetry": self.telemetry,
            "events": list(self.events)[-15:],
        }

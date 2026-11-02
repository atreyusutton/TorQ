"""Drive control: talks to the Arduino drive firmware over USB serial.

Safety layers, from the outside in:
  1. Commands older than command_timeout_ms are dropped and the motors stop.
  2. The link handler calls stop() whenever the brain connection drops.
  3. Every PWM value is clamped to max_pwm here, and max_pwm is also
     programmed into the Arduino as its speed limit.
  4. The Arduino firmware has its own 300 ms watchdog and an AVR hardware
     watchdog, so motors stop even if this process dies.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from dataclasses import dataclass
from typing import Callable, Protocol

log = logging.getLogger("torq.motors")


class Transport(Protocol):
    """Byte stream to the Arduino. pyserial's Serial fits this shape."""

    def write(self, data: bytes) -> int | None: ...
    def readline(self) -> bytes: ...  # returns b"" on timeout
    def close(self) -> None: ...


@dataclass(frozen=True)
class MotorConfig:
    max_pwm: int = 200
    min_pwm: int = 60
    trim_left: float = 1.0
    trim_right: float = 1.0
    command_timeout_ms: int = 300
    resend_ms: int = 100

    @classmethod
    def from_dict(cls, d: dict) -> "MotorConfig":
        cfg = cls(**{k: d[k] for k in cls.__dataclass_fields__ if k in d})
        if not 0 < cfg.max_pwm <= 255:
            raise ValueError(f"motors.max_pwm must be 1..255, got {cfg.max_pwm}")
        if not 0 <= cfg.min_pwm <= cfg.max_pwm:
            raise ValueError(f"motors.min_pwm must be 0..max_pwm, got {cfg.min_pwm}")
        return cfg


def to_pwm(value: float, trim: float, cfg: MotorConfig) -> int:
    """Map a -1..1 speed to a signed PWM in -max_pwm..max_pwm.

    Nonzero speeds start at min_pwm so slow commands don't stall the tracks.
    """
    v = max(-1.0, min(1.0, value * trim))
    if abs(v) < 0.01:
        return 0
    pwm = cfg.min_pwm + abs(v) * (cfg.max_pwm - cfg.min_pwm)
    pwm = min(cfg.max_pwm, round(pwm))
    return pwm if v > 0 else -pwm


def to_firmware_value(pwm: int, cfg: MotorConfig) -> int:
    """The firmware scales D values by L/255, and L is set to max_pwm."""
    return max(-255, min(255, round(pwm * 255 / cfg.max_pwm)))


class DriveController:
    def __init__(
        self,
        open_transport: Callable[[], Transport],
        cfg: MotorConfig,
        on_event: Callable[[str], None] | None = None,
        boot_wait_s: float = 2.0,
    ) -> None:
        self._open_transport = open_transport
        self.cfg = cfg
        self._on_event = on_event or (lambda e: None)
        self._boot_wait_s = boot_wait_s

        self._transport: Transport | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._pong = asyncio.Event()

        self.connected = False
        self.estopped = False
        self.fault: str | None = None
        self._target = (0, 0)          # firmware D values
        self._target_stamp = 0.0       # monotonic time of last drive command
        self.last_status: dict | None = None

    # ---- commands from the link -------------------------------------------

    def drive(self, left: float, right: float) -> bool:
        """Set track speeds (-1..1). Returns False if driving is locked out."""
        if self.estopped or self.fault:
            return False
        l_pwm = to_pwm(left, self.cfg.trim_left, self.cfg)
        r_pwm = to_pwm(right, self.cfg.trim_right, self.cfg)
        self._target = (to_firmware_value(l_pwm, self.cfg), to_firmware_value(r_pwm, self.cfg))
        self._target_stamp = time.monotonic()
        self._send_drive()
        return True

    def stop(self) -> None:
        self._target = (0, 0)
        self._send("S")

    def estop(self) -> None:
        self.estopped = True
        self._target = (0, 0)
        self._send("E")

    def reset(self) -> None:
        self.estopped = False
        self.fault = None
        self._target = (0, 0)
        self._send("R")

    def status(self) -> dict:
        return {
            "connected": self.connected,
            "estop": self.estopped,
            "fault": self.fault,
            "target": list(self._target),
            "firmware": self.last_status,
        }

    # ---- serial plumbing --------------------------------------------------

    def _send(self, line: str) -> None:
        if self._transport is None:
            return
        try:
            self._transport.write((line + "\n").encode())
        except OSError as exc:
            log.error("serial write failed: %s", exc)
            self._drop_transport()

    def _send_drive(self) -> None:
        l, r = self._target
        if l == 0 and r == 0:
            self._send("S")
        else:
            self._send(f"D {l} {r}")

    def _drop_transport(self) -> None:
        t, self._transport = self._transport, None
        self.connected = False
        if t is not None:
            try:
                t.close()
            except OSError as exc:
                log.warning("serial close failed: %s", exc)

    def _handle_line(self, line: str) -> None:
        if not line:
            return
        if line == "PONG":
            self._pong.set()
        elif line.startswith("STATUS "):
            parts = line.split()
            try:
                l, r, limit, estop, ma_l, ma_r = (int(p) for p in parts[1:7])
            except ValueError:
                log.warning("bad STATUS line: %r", line)
                return
            self.last_status = {
                "pwm": [l, r], "limit": limit, "estop": bool(estop), "ma": [ma_l, ma_r],
            }
        elif line.startswith("FAULT"):
            self.fault = line
            self._target = (0, 0)
            log.error("arduino: %s", line)
            self._on_event(line)
        elif line in ("WDT", "ESTOP") or line.startswith("ERR") or line.startswith("READY"):
            log.info("arduino: %s", line)
            self._on_event(line)

    def _reader(self, transport: Transport, loop: asyncio.AbstractEventLoop) -> None:
        """Runs in a thread: blocking reads, handed to the event loop."""
        while self._transport is transport:
            try:
                raw = transport.readline()
            except OSError as exc:
                log.error("serial read failed: %s", exc)
                loop.call_soon_threadsafe(self._drop_transport)
                return
            if raw:
                line = raw.decode(errors="replace").strip()
                loop.call_soon_threadsafe(self._handle_line, line)

    async def _handshake(self) -> bool:
        # Opening the port resets the Uno; give the bootloader time to hand over.
        await asyncio.sleep(self._boot_wait_s)
        for _ in range(5):
            self._pong.clear()
            self._send("P")
            try:
                await asyncio.wait_for(self._pong.wait(), 0.5)
            except asyncio.TimeoutError:
                continue
            self._send(f"L {self.cfg.max_pwm}")
            self._send("S")
            return True
        return False

    async def run(self) -> None:
        """Keep the Arduino connected; resend drive commands; poll status."""
        self._loop = asyncio.get_running_loop()
        while True:
            try:
                transport = await asyncio.to_thread(self._open_transport)
            except OSError as exc:
                log.warning("arduino not available (%s); retrying in 2 s", exc)
                await asyncio.sleep(2)
                continue

            self._transport = transport
            threading.Thread(target=self._reader, args=(transport, self._loop), daemon=True).start()
            if not await self._handshake():
                log.error("arduino did not answer ping; reopening")
                self._drop_transport()
                await asyncio.sleep(1)
                continue

            self.connected = True
            if self.estopped:
                self._send("E")
            log.info("arduino connected")
            await self._serve(transport)
            log.warning("arduino disconnected")

    async def _serve(self, transport: Transport) -> None:
        resend = self.cfg.resend_ms / 1000
        timeout = self.cfg.command_timeout_ms / 1000
        ticks = 0
        while self._transport is transport:
            moving = self._target != (0, 0)
            if moving and time.monotonic() - self._target_stamp > timeout:
                log.info("drive commands stopped arriving; stopping")
                self.stop()
            elif moving:
                self._send_drive()
            ticks += 1
            if ticks % 5 == 0:
                self._send("?")
            await asyncio.sleep(resend)

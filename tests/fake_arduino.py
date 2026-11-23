"""In-memory stand-in for the Uno drive firmware, speaking the same serial protocol."""

from __future__ import annotations

import queue
import threading
import time


class FakeArduino:
    WATCHDOG_S = 0.3

    def __init__(self) -> None:
        self._out: queue.Queue[bytes] = queue.Queue()
        self._lock = threading.Lock()
        self.received: list[str] = []
        self.pwm = (0, 0)
        self.limit = 160
        self.latched = False
        self.closed = False
        self._last_drive = 0.0
        self._out.put(b"READY torq-drive fake\n")
        threading.Thread(target=self._watchdog, daemon=True).start()

    # Transport interface ---------------------------------------------------

    def write(self, data: bytes) -> int:
        for line in data.decode().splitlines():
            self._handle(line.strip())
        return len(data)

    def readline(self) -> bytes:
        try:
            return self._out.get(timeout=0.1)
        except queue.Empty:
            return b""

    def close(self) -> None:
        self.closed = True

    # Firmware behaviour ------------------------------------------------------

    def _reply(self, text: str) -> None:
        self._out.put((text + "\n").encode())

    def _handle(self, line: str) -> None:
        if not line:
            return
        with self._lock:
            self.received.append(line)
            parts = line.split()
            cmd = parts[0]
            if cmd == "D":
                if self.latched:
                    self._reply("ERR latched, send R")
                    return
                l, r = int(parts[1]), int(parts[2])
                self.pwm = (l * self.limit // 255, r * self.limit // 255)
                self._last_drive = time.monotonic()
            elif cmd == "S":
                self.pwm = (0, 0)
                self._reply("OK STOP")
            elif cmd == "E":
                self.pwm, self.latched = (0, 0), True
                self._reply("ESTOP")
            elif cmd == "R":
                self.pwm, self.latched = (0, 0), False
                self._reply("OK RESET")
            elif cmd == "L":
                self.limit = int(parts[1])
                self._reply(f"OK L {self.limit}")
            elif cmd == "P":
                self._reply("PONG")
            elif cmd == "?":
                self._reply(f"STATUS {self.pwm[0]} {self.pwm[1]} {self.limit} {int(self.latched)} 41 41")
            else:
                self._reply(f"ERR unknown command: {line}")

    def _watchdog(self) -> None:
        while not self.closed:
            with self._lock:
                if self.pwm != (0, 0) and time.monotonic() - self._last_drive > self.WATCHDOG_S:
                    self.pwm = (0, 0)
                    self._reply("WDT")
            time.sleep(0.02)

    def drive_commands(self) -> list[str]:
        with self._lock:
            return [c for c in self.received if c.startswith("D ")]

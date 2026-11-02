"""Mic capture and speaker playback on the Pi, using ALSA's arecord/aplay."""

from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable

log = logging.getLogger("torq.audio")

MAX_VOLUME = 90  # percent; the USB speaker cuts out above this


class Mic:
    """Records 16-bit mono PCM while on; hands chunks to a callback."""

    CHUNK = 3200  # 100 ms at 16 kHz

    def __init__(self, device: str, rate: int, on_chunk: Callable[[bytes], Awaitable[None]],
                 on_end: Callable[[], Awaitable[None]]) -> None:
        self.device, self.rate = device, rate
        self._on_chunk, self._on_end = on_chunk, on_end
        self._proc: asyncio.subprocess.Process | None = None
        self._reader: asyncio.Task | None = None

    @property
    def active(self) -> bool:
        return self._proc is not None

    async def start(self) -> None:
        if self._proc is not None:
            return
        self._proc = await asyncio.create_subprocess_exec(
            "arecord", "-q", "-D", self.device, "-f", "S16_LE", "-r", str(self.rate), "-c", "1", "-t", "raw",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        self._reader = asyncio.create_task(self._read(self._proc))
        log.info("mic on")

    async def _read(self, proc: asyncio.subprocess.Process) -> None:
        assert proc.stdout is not None
        try:
            while chunk := await proc.stdout.read(self.CHUNK):
                await self._on_chunk(chunk)
        finally:
            rc = await proc.wait()
            if rc not in (0, -15):  # -15: we terminated it
                err = (await proc.stderr.read()).decode().strip() if proc.stderr else ""
                log.error("arecord exited %s: %s", rc, err)
            await self._on_end()

    async def stop(self) -> None:
        proc, reader = self._proc, self._reader
        self._proc, self._reader = None, None
        if proc is None:
            return
        if proc.returncode is None:
            proc.terminate()
        if reader is not None:
            await reader  # drains the last audio, then reports the end
        log.info("mic off")


class Speaker:
    """Plays a stream of 16-bit mono PCM through aplay."""

    def __init__(self, device: str, on_done: Callable[[], Awaitable[None]],
                 card: str | None = None, volume: int = MAX_VOLUME) -> None:
        self.device = device
        self._on_done = on_done
        self._card, self._volume = card, volume
        self._proc: asyncio.subprocess.Process | None = None
        self._waiter: asyncio.Task | None = None

    @property
    def active(self) -> bool:
        return self._proc is not None

    async def start(self, rate: int) -> None:
        await self.cancel()
        if self._card:
            # The USB speaker resets on power dips and comes back at its own
            # default volume, so re-apply ours before every utterance.
            await set_volume(self._card, self._volume)
        self._proc = await asyncio.create_subprocess_exec(
            "aplay", "-q", "-D", self.device, "-f", "S16_LE", "-r", str(rate), "-c", "1", "-t", "raw",
            stdin=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        self._waiter = asyncio.create_task(self._wait(self._proc))

    async def _wait(self, proc: asyncio.subprocess.Process) -> None:
        rc = await proc.wait()
        if rc not in (0, -15, -9):
            err = (await proc.stderr.read()).decode().strip() if proc.stderr else ""
            log.error("aplay exited %s: %s", rc, err)
        if self._proc is proc:
            self._proc = None
        await self._on_done()

    async def write(self, pcm: bytes) -> None:
        proc = self._proc
        if proc is None or proc.stdin is None:
            return
        try:
            proc.stdin.write(pcm)
            await proc.stdin.drain()
        except (BrokenPipeError, ConnectionResetError) as exc:
            log.warning("speaker pipe closed: %s", exc)

    async def end(self) -> None:
        """No more audio: let what's queued finish playing."""
        proc = self._proc
        if proc is not None and proc.stdin is not None and not proc.stdin.is_closing():
            proc.stdin.close()

    async def cancel(self) -> None:
        proc, waiter = self._proc, self._waiter
        self._proc, self._waiter = None, None
        if proc is not None and proc.returncode is None:
            proc.kill()
        if waiter is not None:
            await waiter


async def set_volume(card: str, percent: int) -> None:
    percent = max(0, min(MAX_VOLUME, percent))
    proc = await asyncio.create_subprocess_exec(
        "amixer", "-q", "-c", card, "sset", "PCM", f"{percent}%",
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE,
    )
    _out, err = await proc.communicate()
    if proc.returncode != 0:
        log.error("could not set speaker volume: %s", err.decode().strip())
    else:
        log.debug("speaker volume %d%%", percent)

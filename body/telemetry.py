"""Pi health readings for the dashboard: temperature, supply voltage, Wi-Fi."""

from __future__ import annotations

import asyncio
import logging
import re
import shutil
from pathlib import Path

log = logging.getLogger("torq.telemetry")

THERMAL = Path("/sys/class/thermal/thermal_zone0/temp")
WIRELESS = Path("/proc/net/wireless")


def cpu_temp_c() -> float | None:
    try:
        return int(THERMAL.read_text().strip()) / 1000
    except (OSError, ValueError):
        return None


def wifi_dbm() -> int | None:
    try:
        for line in WIRELESS.read_text().splitlines():
            if line.strip().startswith("wlan0:"):
                return int(float(line.split()[3]))
    except (OSError, ValueError, IndexError):
        return None
    return None


async def _vcgencmd(*args: str) -> str | None:
    if shutil.which("vcgencmd") is None:
        return None
    proc = await asyncio.create_subprocess_exec(
        "vcgencmd", *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    out, err = await proc.communicate()
    if proc.returncode != 0:
        log.warning("vcgencmd %s failed: %s", " ".join(args), err.decode().strip())
        return None
    return out.decode()


async def supply_volts() -> float | None:
    out = await _vcgencmd("pmic_read_adc", "EXT5V_V")
    m = re.search(r"=([\d.]+)V", out or "")
    return round(float(m.group(1)), 2) if m else None


async def throttled() -> str | None:
    out = await _vcgencmd("get_throttled")
    return out.strip().split("=")[-1] if out else None


class Telemetry:
    """Caches the slow vcgencmd readings; fast ones are read every call."""

    def __init__(self) -> None:
        self._volts: float | None = None
        self._throttled: str | None = None

    async def refresh_slow(self) -> None:
        self._volts = await supply_volts()
        self._throttled = await throttled()

    def snapshot(self) -> dict:
        return {
            "cpu_temp_c": cpu_temp_c(),
            "wifi_dbm": wifi_dbm(),
            "supply_v": self._volts,
            "throttled": self._throttled,
        }

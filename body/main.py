"""TorQ body: runs on the Pi. Connects the Arduino drive to the brain."""

from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

import serial
import yaml

from body.audio_io import MAX_VOLUME, set_volume
from body.link import BodyLink
from body.motors import DriveController, MotorConfig
from body.telemetry import Telemetry

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config.yaml"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="TorQ body (Pi)")
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("--brain", action="append", help="brain WebSocket URL; overrides config, repeatable")
    p.add_argument("--serial", help="Arduino serial port; overrides config")
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args()


async def amain(args: argparse.Namespace) -> None:
    cfg = yaml.safe_load(args.config.read_text())
    body_cfg = cfg["body"]
    voice_cfg = cfg.get("voice", {})
    port = args.serial or body_cfg["serial_port"]

    def open_serial() -> serial.Serial:
        try:
            return serial.Serial(port, 115200, timeout=0.2)
        except serial.SerialException as exc:
            raise OSError(str(exc)) from exc

    link: BodyLink | None = None

    def on_arduino_event(text: str) -> None:
        if link is not None:
            asyncio.get_running_loop().create_task(link.send_event(f"arduino: {text}"))

    motors = DriveController(open_serial, MotorConfig.from_dict(cfg["motors"]), on_event=on_arduino_event)
    telemetry = Telemetry()

    async def read_telemetry() -> dict:
        return telemetry.snapshot()

    async def refresh_slow_telemetry() -> None:
        while True:
            await telemetry.refresh_slow()
            await asyncio.sleep(5)

    link = BodyLink(
        args.brain or body_cfg["brain_urls"],
        motors,
        read_telemetry,
        telemetry_interval_s=body_cfg.get("telemetry_interval_s", 0.5),
        camera_port=body_cfg.get("camera_port"),
        mic_device=voice_cfg.get("mic_device"),
        mic_rate=voice_cfg.get("mic_rate", 16000),
        speaker_device=voice_cfg.get("speaker_device"),
        speaker_card=voice_cfg.get("speaker_card"),
        speaker_volume=voice_cfg.get("speaker_volume", MAX_VOLUME),
    )
    if voice_cfg.get("speaker_card"):
        await set_volume(voice_cfg["speaker_card"], voice_cfg.get("speaker_volume", MAX_VOLUME))
    await asyncio.gather(motors.run(), link.run(), refresh_slow_telemetry())


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(amain(args))


if __name__ == "__main__":
    main()

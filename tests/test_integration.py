"""Brain server + body + fake Arduino, wired together over real sockets."""

from __future__ import annotations

import asyncio
import contextlib
import socket
import time

import aiohttp
import pytest

from body.link import BodyLink
from body.motors import DriveController, MotorConfig, to_firmware_value, to_pwm
from brain.server import Brain, start
from tests.fake_arduino import FakeArduino

MOTOR_CFG = MotorConfig(max_pwm=200, min_pwm=60, command_timeout_ms=300, resend_ms=50)


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


async def wait_for(predicate, timeout=3.0, interval=0.02):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        await asyncio.sleep(interval)
    return False


@contextlib.asynccontextmanager
async def running_system():
    body_port, ui_port = free_port(), free_port()
    cfg = {"body_host": "127.0.0.1", "body_port": body_port, "ui_host": "127.0.0.1", "ui_port": ui_port}

    brain = Brain(ping_interval_s=0.2)
    runners = await start(brain, cfg)
    broadcaster = asyncio.create_task(brain.broadcast_status())

    arduino = FakeArduino()
    motors = DriveController(lambda: arduino, MOTOR_CFG, boot_wait_s=0.05)

    async def telemetry():
        return {"cpu_temp_c": 40.0}

    link = BodyLink([f"ws://127.0.0.1:{body_port}/body"], motors, telemetry, telemetry_interval_s=0.1, camera_port=8080)
    body_tasks = [asyncio.create_task(motors.run()), asyncio.create_task(link.run())]

    session = aiohttp.ClientSession()
    ui = await session.ws_connect(f"http://127.0.0.1:{ui_port}/ws")
    try:
        assert await wait_for(lambda: brain.state.body_connected and motors.connected), "body never came up"
        yield brain, motors, arduino, ui, runners
    finally:
        await ui.close()
        await session.close()
        for t in body_tasks + [broadcaster]:
            t.cancel()
        await asyncio.gather(*body_tasks, broadcaster, return_exceptions=True)
        for r in runners:
            await r.cleanup()
        arduino.close()


def test_speed_mapping_respects_limits():
    assert to_pwm(0, 1.0, MOTOR_CFG) == 0
    assert to_pwm(0.001, 1.0, MOTOR_CFG) == 0
    assert to_pwm(0.05, 1.0, MOTOR_CFG) == 67          # lifted above min_pwm
    assert to_pwm(1.0, 1.0, MOTOR_CFG) == 200
    assert to_pwm(5.0, 1.0, MOTOR_CFG) == 200          # clamped
    assert to_pwm(-1.0, 1.0, MOTOR_CFG) == -200
    assert to_pwm(0.9, 1.5, MOTOR_CFG) == 200          # trim can't exceed max
    assert to_firmware_value(200, MOTOR_CFG) == 255    # firmware scales by L=max_pwm
    assert to_firmware_value(-200, MOTOR_CFG) == -255


async def test_ping_and_telemetry_reach_dashboard():
    async with running_system() as (brain, _motors, _arduino, ui, _):
        assert await wait_for(lambda: brain.state.rtt_ms is not None)
        msg = await ui.receive_json(timeout=2)
        assert msg["type"] == "status"
        assert await wait_for(lambda: brain.state.telemetry.get("cpu_temp_c") == 40.0)
        assert brain.state.camera_url() == "http://127.0.0.1:8080/stream"
        assert await wait_for(lambda: brain.state.arduino_connected)


async def test_drive_from_dashboard_reaches_arduino_then_times_out():
    async with running_system() as (brain, _motors, arduino, ui, _):
        await ui.send_json({"type": "drive", "left": 1.0, "right": 0.5})
        assert await wait_for(lambda: arduino.pwm != (0, 0))
        assert arduino.drive_commands()[-1] == f"D 255 {to_firmware_value(to_pwm(0.5, 1, MOTOR_CFG), MOTOR_CFG)}"
        assert arduino.limit == 200
        assert brain.state.manual, "driving from the keyboard turns manual override on"

        # No more commands: the body must stop on its own within the timeout.
        assert await wait_for(lambda: arduino.pwm == (0, 0), timeout=1.0)


async def test_estop_locks_out_driving_until_reset():
    async with running_system() as (brain, motors, arduino, ui, _):
        await ui.send_json({"type": "estop"})
        assert await wait_for(lambda: arduino.latched)
        sent_before = len(arduino.drive_commands())
        await ui.send_json({"type": "drive", "left": 1, "right": 1})
        await asyncio.sleep(0.3)
        assert len(arduino.drive_commands()) == sent_before
        assert arduino.pwm == (0, 0)

        await ui.send_json({"type": "reset"})
        assert await wait_for(lambda: not arduino.latched and not motors.estopped)
        await ui.send_json({"type": "drive", "left": 0.5, "right": 0.5})
        assert await wait_for(lambda: arduino.pwm != (0, 0))


async def test_brain_going_away_stops_motors():
    async with running_system() as (brain, motors, arduino, ui, runners):
        await ui.send_json({"type": "drive", "left": 1, "right": 1})
        assert await wait_for(lambda: arduino.pwm != (0, 0))
        # Keep commanding from the body's side so only the link drop can stop it.
        motors._target_stamp = time.monotonic() + 60
        await runners[0].cleanup()   # brain's body port goes down
        assert await wait_for(lambda: arduino.pwm == (0, 0), timeout=3.0)
        assert "S" in arduino.received


async def test_closing_dashboard_stops_robot():
    async with running_system() as (brain, motors, arduino, ui, _):
        await ui.send_json({"type": "drive", "left": 1, "right": 1})
        assert await wait_for(lambda: arduino.pwm != (0, 0))
        motors._target_stamp = time.monotonic() + 60
        await ui.close()
        assert await wait_for(lambda: arduino.pwm == (0, 0), timeout=2.0)


@pytest.mark.parametrize("bad", [
    {"type": "drive", "left": "fast", "right": 1},
    {"type": "drive", "left": float("nan"), "right": 1},
    {"type": "drive"},
])
async def test_dashboard_rejects_bad_drive_messages(bad):
    async with running_system() as (_brain, _motors, arduino, ui, _):
        await ui.send_str(__import__("json").dumps(bad))
        await asyncio.sleep(0.3)
        assert arduino.drive_commands() == []

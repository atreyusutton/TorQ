"""Tools Claude can call. Inputs are validated here before anything runs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Awaitable, Callable

from brain.memory import JobMemory

# Order is fixed so the tools prefix stays cacheable.
TOOLS = [
    {
        "name": "get_vehicle_info",
        "description": "Get the vehicle we're working on (year, make, model, engine) and the job notes so far.",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "set_vehicle",
        "description": "Record which vehicle we're working on, when the user tells you. Use null for unknown year or engine.",
        "input_schema": {
            "type": "object",
            "properties": {
                "year": {"type": ["integer", "null"]},
                "make": {"type": "string"},
                "model": {"type": "string"},
                "engine": {"type": ["string", "null"]},
            },
            "required": ["year", "make", "model", "engine"],
            "additionalProperties": False,
        },
    },
    {
        "name": "save_note",
        "description": "Save a short note to the current job, such as a spec you looked up, a part number, or what's been done.",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
            "additionalProperties": False,
        },
    },
    {
        "name": "stop",
        "description": "Stop the robot's motors immediately. Use whenever the user says stop, halt, or wait about movement.",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
]

for _tool in TOOLS:
    # Stream tool inputs as they're generated; we validate them below.
    _tool["eager_input_streaming"] = True


class ToolInputError(ValueError):
    pass


def _validate(name: str, args: object) -> dict:
    if not isinstance(args, dict):
        raise ToolInputError("input must be an object")
    if name in ("get_vehicle_info", "stop"):
        return {}
    if name == "save_note":
        text = args.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ToolInputError("text must be a non-empty string")
        return {"text": text.strip()[:500]}
    if name == "set_vehicle":
        year, make, model, engine = (args.get(k) for k in ("year", "make", "model", "engine"))
        if year is not None and not (isinstance(year, int) and 1900 <= year <= 2100):
            raise ToolInputError("year must be an integer 1900-2100 or null")
        if not (isinstance(make, str) and make.strip() and isinstance(model, str) and model.strip()):
            raise ToolInputError("make and model must be non-empty strings")
        if engine is not None and not isinstance(engine, str):
            raise ToolInputError("engine must be a string or null")
        return {"year": year, "make": make.strip(), "model": model.strip(), "engine": engine}
    raise ToolInputError(f"unknown tool {name!r}")


@dataclass
class ToolContext:
    memory: JobMemory
    stop_robot: Callable[[], Awaitable[None]]


async def run_tool(name: str, args: object, ctx: ToolContext) -> tuple[str, bool]:
    """Returns (result text, is_error)."""
    try:
        clean = _validate(name, args)
    except ToolInputError as exc:
        return json.dumps({"error": f"INVALID_INPUT: {exc}"}), True

    if name == "get_vehicle_info":
        return json.dumps(ctx.memory.summary()), False
    if name == "set_vehicle":
        v = ctx.memory.set_vehicle(**clean)
        return json.dumps({"ok": True, "vehicle": v}), False
    if name == "save_note":
        count = ctx.memory.add_note(clean["text"])
        return json.dumps({"ok": True, "notes": count}), False
    if name == "stop":
        await ctx.stop_robot()
        return json.dumps({"ok": True, "motors": "stopped"}), False
    return json.dumps({"error": "unknown tool"}), True

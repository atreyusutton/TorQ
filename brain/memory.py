"""The current job: which vehicle we're working on and notes taken along the way."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

log = logging.getLogger("torq.memory")


class JobMemory:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.vehicle: dict | None = None
        self.notes: list[dict] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            log.error("could not read %s, starting a fresh job: %s", self.path, exc)
            return
        self.vehicle = data.get("vehicle")
        self.notes = data.get("notes", [])

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"vehicle": self.vehicle, "notes": self.notes}, indent=2))
        tmp.replace(self.path)

    def set_vehicle(self, year: int | None, make: str, model: str, engine: str | None) -> dict:
        self.vehicle = {"year": year, "make": make, "model": model, "engine": engine}
        self._save()
        return self.vehicle

    def add_note(self, text: str) -> int:
        self.notes.append({"t": time.time(), "text": text})
        self._save()
        return len(self.notes)

    def clear(self) -> None:
        self.vehicle, self.notes = None, []
        self._save()

    def vehicle_line(self) -> str:
        v = self.vehicle
        if not v:
            return "No vehicle set."
        parts = [str(v.get("year") or ""), v.get("make", ""), v.get("model", "")]
        line = " ".join(p for p in parts if p).strip()
        if v.get("engine"):
            line += f", {v['engine']}"
        return line

    def summary(self) -> dict:
        return {"vehicle": self.vehicle_line() if self.vehicle else None, "notes": [n["text"] for n in self.notes]}

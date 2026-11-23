"""Stand-ins for Claude, Whisper, Piper, and the Pi's mic/speaker."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace


def text_block(text):
    return SimpleNamespace(type="text", text=text)


def tool_block(name, args, id="toolu_1"):
    return SimpleNamespace(type="tool_use", id=id, name=name, input=args)


class FakeStream:
    def __init__(self, blocks, stop_reason, delay):
        self._blocks, self._stop, self._delay = blocks, stop_reason, delay

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def __aiter__(self):
        return self._events()

    async def _events(self):
        for b in self._blocks:
            if b.type == "text":
                for word in b.text.split(" "):
                    await asyncio.sleep(self._delay)
                    yield SimpleNamespace(type="text", text=word + " ")

    async def get_final_message(self):
        usage = SimpleNamespace(input_tokens=10, output_tokens=5, cache_read_input_tokens=0, cache_creation_input_tokens=0)
        return SimpleNamespace(content=self._blocks, stop_reason=self._stop, usage=usage, model="fake")


class FakeClaude:
    """Returns scripted turns in order; records every request."""

    def __init__(self, turns, delay=0.0):
        self.turns = list(turns)   # each: (blocks, stop_reason)
        self.requests = []
        self.delay = delay
        self.beta = SimpleNamespace(messages=SimpleNamespace(stream=self._stream))

    def _stream(self, **kwargs):
        # Snapshot messages: the conversation list keeps growing after the call.
        self.requests.append({**kwargs, "messages": list(kwargs["messages"])})
        blocks, stop = self.turns.pop(0)
        return FakeStream(blocks, stop, self.delay)


class FakeSTT:
    def __init__(self, text):
        self.text = text
        self.heard = None

    async def warm_up(self):
        pass

    async def transcribe(self, pcm, rate=16000):
        self.heard = pcm
        return self.text


class FakeTTS:
    sample_rate = 22050

    def __init__(self):
        self.spoken = []

    async def warm_up(self):
        pass

    async def synthesize(self, text):
        self.spoken.append(text)
        return b"\x00\x01" * 1000


class FakeMic:
    def __init__(self, link):
        self.link = link
        self.active = False
        self._task = None

    async def start(self):
        self.active = True

        async def stream():
            while self.active:
                await self.link._send_mic(b"\x10\x00" * 1600)
                await asyncio.sleep(0.02)

        self._task = asyncio.create_task(stream())

    async def stop(self):
        if not self.active:
            return
        self.active = False
        await self._task
        await self.link._send_mic_end()


class FakeSpeaker:
    def __init__(self):
        self.received = bytearray()
        self.events = []
        self.active = False

    async def start(self, rate):
        self.events.append(("start", rate))
        self.active = True

    async def write(self, pcm):
        self.received.extend(pcm)

    async def end(self):
        self.events.append(("end",))
        self.active = False

    async def cancel(self):
        self.events.append(("cancel",))
        self.active = False

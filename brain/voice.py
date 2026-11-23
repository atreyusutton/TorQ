"""The conversation loop: push-to-talk audio or typed text in, spoken answer out."""

from __future__ import annotations

import asyncio
import itertools
import logging
from collections import deque
from typing import Awaitable, Callable

from brain.claude import ClaudeUnavailable, Conversation
from brain.speech import SentenceChunker, SpeechToText, TextToSpeech
from brain.state import Mode, RobotState

log = logging.getLogger("torq.voice")

MIC_FRAME = 0x01      # body -> brain: 16-bit mono PCM from the mic
SPEAKER_FRAME = 0x02  # brain -> body: 16-bit mono PCM for the speaker
AUDIO_CHUNK = 8192    # bytes per speaker frame


class Assistant:
    def __init__(
        self,
        state: RobotState,
        conversation: Conversation,
        stt: SpeechToText,
        tts: TextToSpeech,
        send_body: Callable[[dict], Awaitable[bool]],
        send_body_bytes: Callable[[bytes], Awaitable[bool]],
        mic_rate: int = 16000,
    ) -> None:
        self.state = state
        self.conversation = conversation
        self.stt = stt
        self.tts = tts
        self._send_body = send_body
        self._send_body_bytes = send_body_bytes
        self.mic_rate = mic_rate

        self.chat: deque[dict] = deque(maxlen=40)
        self._ids = itertools.count(1)
        self._task: asyncio.Task | None = None
        self._listening = False
        self._mic = bytearray()
        self._mic_done = asyncio.Event()

    # ---- chat log shown on the dashboard ----------------------------------

    def _add(self, role: str, text: str, done: bool = True) -> dict:
        entry = {"id": next(self._ids), "role": role, "text": text, "done": done}
        self.chat.append(entry)
        return entry

    # ---- inputs ---------------------------------------------------------------

    async def ask_text(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        await self.interrupt()
        self._add("user", text)
        self._task = asyncio.create_task(self._respond(text))

    async def talk_start(self) -> None:
        await self.interrupt()
        self._mic = bytearray()
        self._mic_done.clear()
        self._listening = True
        self.state.activity = Mode.LISTENING
        if not await self._send_body({"type": "listen", "on": True}):
            self._listening = False
            self.state.activity = Mode.IDLE
            self._add("system", "The robot isn't connected, so I can't hear you. Type instead.")

    async def talk_stop(self) -> None:
        if not self._listening:
            return
        self._listening = False
        await self._send_body({"type": "listen", "on": False})
        self._task = asyncio.create_task(self._transcribe_and_respond())

    def on_mic_audio(self, pcm: bytes) -> None:
        if self._listening or not self._mic_done.is_set():
            self._mic.extend(pcm)

    def on_mic_end(self) -> None:
        self._mic_done.set()

    def on_speak_done(self) -> None:
        if self.state.activity == Mode.SPEAKING and (self._task is None or self._task.done()):
            self.state.activity = Mode.IDLE

    async def interrupt(self) -> None:
        """Cut off whatever TorQ is doing: thinking, speaking, or listening."""
        task, self._task = self._task, None
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:  # already logged inside the task
                pass
        if self.state.activity in (Mode.THINKING, Mode.SPEAKING):
            await self._send_body({"type": "speak_cancel"})
        self.state.activity = Mode.IDLE

    def reset(self) -> None:
        self.conversation.reset()
        self.chat.clear()
        self._add("system", "Started a new conversation.")

    # ---- pipeline -------------------------------------------------------------

    async def _transcribe_and_respond(self) -> None:
        self.state.activity = Mode.THINKING
        try:
            await asyncio.wait_for(self._mic_done.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            log.warning("mic end marker never arrived; using what we have")
        audio = bytes(self._mic)
        seconds = len(audio) / 2 / self.mic_rate
        try:
            text = await self.stt.transcribe(audio, self.mic_rate)
        except Exception as exc:
            log.exception("transcription failed")
            self._add("system", f"Speech recognition failed: {exc}")
            self.state.activity = Mode.IDLE
            return
        log.info("heard %.1fs of audio: %r", seconds, text)
        if not text:
            self._add("system", "Didn't catch that. Hold T while you talk.")
            self.state.activity = Mode.IDLE
            return
        self._add("user", text)
        await self._respond(text)

    async def _respond(self, text: str) -> None:
        self.state.activity = Mode.THINKING
        entry = self._add("torq", "", done=False)
        chunker = SentenceChunker()
        sentences: asyncio.Queue[str | None] = asyncio.Queue()
        speaker = asyncio.create_task(self._speak(sentences))

        async def on_text(chunk: str) -> None:
            entry["text"] += chunk
            for s in chunker.feed(chunk):
                await sentences.put(s)

        async def on_tool(name: str) -> None:
            log.info("claude is using %s", name)

        try:
            await self.conversation.ask(text, on_text, on_tool)
        except ClaudeUnavailable as exc:
            msg = str(exc)
            entry["text"] += (" " if entry["text"] else "") + msg
            for s in chunker.feed(" " + msg):
                await sentences.put(s)
        except asyncio.CancelledError:
            speaker.cancel()
            entry["text"] += " [interrupted]"
            entry["done"] = True
            raise
        except Exception:
            log.exception("unexpected error answering")
            msg = "Something went wrong on my end. Check the brain log."
            entry["text"] += (" " if entry["text"] else "") + msg
            for s in chunker.feed(" " + msg):
                await sentences.put(s)
        for s in chunker.flush():
            await sentences.put(s)
        await sentences.put(None)
        entry["done"] = True
        try:
            await speaker
        except asyncio.CancelledError:
            speaker.cancel()
            raise

    async def _speak(self, sentences: asyncio.Queue) -> None:
        started = False
        try:
            while (sentence := await sentences.get()) is not None:
                try:
                    pcm = await self.tts.synthesize(sentence)
                except Exception:
                    log.exception("speech synthesis failed for %r", sentence)
                    continue
                if not started:
                    started = await self._send_body({"type": "speak_start", "rate": self.tts.sample_rate})
                    if not started:
                        continue  # no robot connected: text only
                    self.state.activity = Mode.SPEAKING
                for i in range(0, len(pcm), AUDIO_CHUNK):
                    await self._send_body_bytes(bytes([SPEAKER_FRAME]) + pcm[i:i + AUDIO_CHUNK])
        finally:
            if started:
                await self._send_body({"type": "speak_end"})
            elif self.state.activity in (Mode.THINKING, Mode.SPEAKING):
                self.state.activity = Mode.IDLE

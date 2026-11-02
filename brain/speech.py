"""Local speech: Whisper speech-to-text, Piper text-to-speech, and sentence chunking."""

from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path

import numpy as np

log = logging.getLogger("torq.speech")

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+|\n+")


class SentenceChunker:
    """Collects streamed text and yields whole sentences, so speech can start early."""

    def __init__(self, min_chars: int = 12) -> None:
        self._buf = ""
        self._min = min_chars

    def feed(self, text: str) -> list[str]:
        self._buf += text
        out = []
        while True:
            m = None
            for cand in _SENTENCE_END.finditer(self._buf):
                if cand.start() >= self._min:
                    m = cand
                    break
            if m is None:
                return out
            sentence, self._buf = self._buf[: m.start()].strip(), self._buf[m.end():]
            if sentence:
                out.append(sentence)

    def flush(self) -> list[str]:
        rest, self._buf = self._buf.strip(), ""
        return [rest] if rest else []


class SpeechToText:
    def __init__(self, model_name: str, download_root: Path, hint: str | None = None) -> None:
        self._model_name = model_name
        self._download_root = download_root
        self._hint = hint
        self._model = None
        self._lock = asyncio.Lock()

    def _load(self):
        from faster_whisper import WhisperModel

        if self._model is None:
            log.info("loading whisper %s", self._model_name)
            self._model = WhisperModel(
                self._model_name, device="cpu", compute_type="int8", download_root=str(self._download_root)
            )
        return self._model

    async def warm_up(self) -> None:
        async with self._lock:
            await asyncio.to_thread(self._load)

    async def transcribe(self, pcm16: bytes, sample_rate: int = 16000) -> str:
        if len(pcm16) < sample_rate * 2 // 4:  # under a quarter second
            return ""
        audio = np.frombuffer(pcm16, dtype=np.int16).astype(np.float32) / 32768.0
        if sample_rate != 16000:
            idx = np.arange(0, len(audio), sample_rate / 16000)
            audio = np.interp(idx, np.arange(len(audio)), audio).astype(np.float32)

        def run() -> str:
            model = self._load()
            segments, _info = model.transcribe(
                audio, language="en", beam_size=1, vad_filter=True, initial_prompt=self._hint
            )
            return " ".join(s.text for s in segments).strip()

        async with self._lock:
            return await asyncio.to_thread(run)


class TextToSpeech:
    def __init__(self, voice_path: Path) -> None:
        self._voice_path = voice_path
        self._voice = None
        self.sample_rate = 22050

    def _load(self):
        from piper import PiperVoice

        if self._voice is None:
            if not self._voice_path.exists():
                raise FileNotFoundError(f"Piper voice not found at {self._voice_path}")
            self._voice = PiperVoice.load(str(self._voice_path))
            self.sample_rate = self._voice.config.sample_rate
        return self._voice

    async def warm_up(self) -> None:
        await asyncio.to_thread(self._load)

    async def synthesize(self, text: str) -> bytes:
        """Mono 16-bit PCM at self.sample_rate."""

        def run() -> bytes:
            voice = self._load()
            return b"".join(chunk.audio_int16_bytes for chunk in voice.synthesize(text))

        return await asyncio.to_thread(run)

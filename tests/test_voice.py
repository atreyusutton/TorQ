"""Voice and chat: dashboard -> brain -> (fake) Claude -> (fake) TTS -> body speaker, over real sockets."""

from __future__ import annotations

import asyncio
import contextlib

import aiohttp

from body.link import BodyLink
from body.motors import DriveController
from brain.claude import ClaudeConfig, Conversation, pick_model
from brain.memory import JobMemory
from brain.server import Brain, start
from brain.speech import SentenceChunker
from brain.state import Mode
from brain.tools import ToolContext
from brain.voice import Assistant
from tests.fake_arduino import FakeArduino
from tests.fakes_voice import FakeClaude, FakeMic, FakeSpeaker, FakeSTT, FakeTTS, text_block, tool_block
from tests.test_integration import MOTOR_CFG, free_port, wait_for

CFG = ClaudeConfig(fast_model="fast", smart_model="smart", diagnostic_words=["why", "noise", "won't"])


@contextlib.asynccontextmanager
async def voice_system(turns, stt_text="", delay=0.0, tmp_path=None):
    body_port, ui_port = free_port(), free_port()
    cfg = {"body_host": "127.0.0.1", "body_port": body_port, "ui_host": "127.0.0.1", "ui_port": ui_port}
    brain = Brain(ping_interval_s=0.2)
    brain.memory = JobMemory(tmp_path / "job.json")
    claude = FakeClaude(turns, delay=delay)
    stt, tts = FakeSTT(stt_text), FakeTTS()
    convo = Conversation(claude, CFG, ToolContext(memory=brain.memory, stop_robot=brain.stop_robot))
    brain.assistant = Assistant(brain.state, convo, stt, tts, brain.send_body, brain.send_body_bytes)
    brain.claude_ready = True
    runners = await start(brain, cfg)
    broadcaster = asyncio.create_task(brain.broadcast_status())

    arduino = FakeArduino()
    motors = DriveController(lambda: arduino, MOTOR_CFG, boot_wait_s=0.05)

    async def telemetry():
        return {}

    link = BodyLink([f"ws://127.0.0.1:{body_port}/body"], motors, telemetry, telemetry_interval_s=0.1)
    speaker = FakeSpeaker()
    link.speaker, link.mic = speaker, FakeMic(link)
    tasks = [asyncio.create_task(motors.run()), asyncio.create_task(link.run())]

    session = aiohttp.ClientSession()
    ui = await session.ws_connect(f"http://127.0.0.1:{ui_port}/ws")
    try:
        assert await wait_for(lambda: brain.state.body_connected and motors.connected)
        yield brain, claude, stt, tts, speaker, arduino, ui
    finally:
        await ui.close()
        await session.close()
        for t in tasks + [broadcaster]:
            t.cancel()
        await asyncio.gather(*tasks, broadcaster, return_exceptions=True)
        for r in runners:
            await r.cleanup()
        arduino.close()


def chat_of(brain, role):
    return [m for m in brain.assistant.chat if m["role"] == role]


def last_reply(brain) -> str:
    replies = chat_of(brain, "torq")
    return replies[-1]["text"] if replies else ""


def test_sentence_chunker_waits_for_whole_sentences():
    c = SentenceChunker(min_chars=10)
    assert c.feed("Lug nuts on a Civic are ") == []
    assert c.feed("eighty foot-pounds. Tighten in a star") == ["Lug nuts on a Civic are eighty foot-pounds."]
    assert c.feed(" pattern.") == []
    assert c.flush() == ["Tighten in a star pattern."]
    assert c.flush() == []


def test_diagnostic_questions_route_to_smart_model():
    assert pick_model("what's the torque spec for lug nuts", CFG)[0] == "fast"
    assert pick_model("why is my belt squealing", CFG)[0] == "smart"
    assert pick_model("the car won't start", CFG)[0] == "smart"
    assert pick_model("anything", CFG, has_image=True)[0] == "smart"
    assert pick_model("whynot", CFG)[0] == "fast"  # whole words only


async def test_typed_question_is_answered_and_spoken_on_the_pi(tmp_path):
    turns = [([text_block("Eighty foot-pounds. Use a star pattern.")], "end_turn")]
    async with voice_system(turns, tmp_path=tmp_path) as (brain, claude, _stt, tts, speaker, _a, ui):
        await ui.send_json({"type": "chat", "text": "torque for civic lug nuts?"})
        assert await wait_for(lambda: speaker.events[-1:] == [("end",)])
        assert chat_of(brain, "torq")[-1]["text"].strip() == "Eighty foot-pounds. Use a star pattern."
        assert chat_of(brain, "torq")[-1]["done"]
        assert tts.spoken == ["Eighty foot-pounds.", "Use a star pattern."]
        assert speaker.events[0] == ("start", 22050)
        assert len(speaker.received) == 2 * 2000   # both sentences' audio arrived
        req = claude.requests[0]
        assert req["model"] == "fast" and "fallbacks" not in req
        assert req["system"][0]["cache_control"] == {"type": "ephemeral"}
        # The dashboard sees the conversation.
        assert await wait_for(lambda: brain.status_json()["chat"][-1]["done"])


async def test_smart_model_gets_server_side_fallback(tmp_path):
    turns = [([text_block("Probably a worn belt tensioner.")], "end_turn")]
    async with voice_system(turns, tmp_path=tmp_path) as (_b, claude, *_rest):
        ui = _rest[-1]
        await ui.send_json({"type": "chat", "text": "why is there a squealing noise"})
        assert await wait_for(lambda: claude.requests)
        assert claude.requests[0]["model"] == "smart"
        assert claude.requests[0]["fallbacks"] == "default"


async def test_tool_call_sets_vehicle_then_answers(tmp_path):
    turns = [
        ([tool_block("set_vehicle", {"year": 2015, "make": "Honda", "model": "Civic", "engine": None})], "tool_use"),
        ([text_block("Got it, a 2015 Civic.")], "end_turn"),
    ]
    async with voice_system(turns, tmp_path=tmp_path) as (brain, claude, _stt, _tts, _spk, _a, ui):
        await ui.send_json({"type": "chat", "text": "I'm working on a 2015 Honda Civic"})
        assert await wait_for(lambda: len(claude.requests) == 2 and chat_of(brain, "torq") and chat_of(brain, "torq")[-1]["done"])
        assert brain.memory.vehicle_line() == "2015 Honda Civic"
        result_turn = claude.requests[1]["messages"][-1]
        assert result_turn["role"] == "user"
        assert result_turn["content"][0]["type"] == "tool_result"
        assert result_turn["content"][0]["tool_use_id"] == "toolu_1"
        assert not result_turn["content"][0]["is_error"]


async def test_invalid_tool_input_is_reported_not_run(tmp_path):
    turns = [
        ([tool_block("set_vehicle", {"year": "soon", "make": "", "model": "Civic", "engine": None})], "tool_use"),
        ([text_block("Which make is it?")], "end_turn"),
    ]
    async with voice_system(turns, tmp_path=tmp_path) as (brain, claude, *_r):
        ui = _r[-1]
        await ui.send_json({"type": "chat", "text": "set the car"})
        assert await wait_for(lambda: len(claude.requests) == 2)
        assert brain.memory.vehicle is None
        assert claude.requests[1]["messages"][-1]["content"][0]["is_error"]


async def test_stop_tool_stops_the_motors(tmp_path):
    turns = [([tool_block("stop", {})], "tool_use"), ([text_block("Stopped.")], "end_turn")]
    async with voice_system(turns, tmp_path=tmp_path) as (_b, claude, _s, _t, _spk, arduino, ui):
        before = arduino.received.count("S")
        await ui.send_json({"type": "chat", "text": "stop!"})
        assert await wait_for(lambda: arduino.received.count("S") > before)


async def test_push_to_talk_transcribes_and_answers(tmp_path):
    turns = [([text_block("Firing order is one eight four three six five seven two.")], "end_turn")]
    async with voice_system(turns, stt_text="firing order small block chevy", tmp_path=tmp_path) as (
        brain, claude, stt, _tts, speaker, _a, ui
    ):
        await ui.send_json({"type": "talk", "on": True})
        assert await wait_for(lambda: brain.state.activity == Mode.LISTENING)
        await asyncio.sleep(0.15)
        await ui.send_json({"type": "talk", "on": False})
        assert await wait_for(lambda: speaker.events[-1:] == [("end",)])
        assert stt.heard and len(stt.heard) >= 3200        # mic audio made it to the brain
        assert chat_of(brain, "user")[-1]["text"] == "firing order small block chevy"
        assert claude.requests[0]["messages"][-1] == {"role": "user", "content": "firing order small block chevy"}


async def test_empty_transcript_does_not_call_claude(tmp_path):
    async with voice_system([], stt_text="", tmp_path=tmp_path) as (brain, claude, *_r):
        ui = _r[-1]
        await ui.send_json({"type": "talk", "on": True})
        await asyncio.sleep(0.1)
        await ui.send_json({"type": "talk", "on": False})
        assert await wait_for(lambda: chat_of(brain, "system"))
        assert claude.requests == []
        assert brain.state.activity == Mode.IDLE


async def test_new_question_interrupts_the_current_answer(tmp_path):
    long_answer = " ".join(["word"] * 200) + "."
    turns = [([text_block(long_answer)], "end_turn"), ([text_block("Short answer.")], "end_turn")]
    async with voice_system(turns, delay=0.01, tmp_path=tmp_path) as (brain, claude, _s, _t, speaker, _a, ui):
        await ui.send_json({"type": "chat", "text": "tell me everything"})
        assert await wait_for(lambda: len(last_reply(brain)) > 20)
        await ui.send_json({"type": "chat", "text": "never mind"})
        assert await wait_for(lambda: last_reply(brain).strip() == "Short answer.")
        assert chat_of(brain, "torq")[0]["text"].endswith("[interrupted]")


async def test_missing_api_key_is_explained_not_crashed(tmp_path):
    async with voice_system([], tmp_path=tmp_path) as (brain, *_r):
        ui = _r[-1]
        brain.assistant.conversation.client = None
        await ui.send_json({"type": "chat", "text": "hello"})
        assert await wait_for(lambda: any("API key" in m["text"] for m in chat_of(brain, "torq")))

"""Talking to Claude: model routing, streaming, the tool loop, and conversation history."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Awaitable, Callable

import anthropic

from brain.tools import TOOLS, ToolContext, run_tool

log = logging.getLogger("torq.claude")

FALLBACK_BETA = "server-side-fallback-2026-07-01"

# Frozen so it caches. Anything that changes per turn goes in the messages.
SYSTEM_PROMPT = """You are TorQ, a small tracked robot that helps people work on their cars in a home garage. \
You roll around next to them, listen, and answer out loud through a speaker while their hands are busy.

How to answer:
- Your words are spoken aloud by text-to-speech. Write plain spoken sentences: no markdown, lists, \
headings, emoji, or symbols like ° or ±. Say units in words ("eighty foot-pounds", "ten millimeter").
- Be brief. Lead with the answer: one to three short sentences is ideal. Offer more detail only if asked.
- Specs vary by year, engine, and trim. If the vehicle matters and you don't know it, call get_vehicle_info, \
and if none is set, ask which vehicle. When the user tells you the vehicle, call set_vehicle.
- If you're not confident in a number, say so plainly and suggest checking the service manual or the \
sticker, rather than guessing. Wrong torque specs break parts.
- Mention safety when it really matters (jack stands, hot coolant, disconnecting the battery), in a few words.
- Save useful facts with save_note: specs you gave, part numbers, what's been done.
- If the user says stop, halt, or wait about the robot moving, call stop right away.
- The user may be speaking through a microphone in a noisy garage, so their words can be mis-transcribed. \
If a request seems garbled, make a sensible guess or ask briefly."""


@dataclass
class ClaudeConfig:
    fast_model: str = "claude-haiku-5-5"
    smart_model: str = "claude-sonnet-5-5"
    fast_effort: str = "low"
    smart_effort: str = "medium"
    max_tokens: int = 8000
    max_tool_rounds: int = 6
    diagnostic_words: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "ClaudeConfig":
        return cls(**{k: d[k] for k in cls.__dataclass_fields__ if k in d})


class ClaudeUnavailable(RuntimeError):
    """A problem the user should hear about, with a speakable message."""


def pick_model(text: str, cfg: ClaudeConfig, has_image: bool = False) -> tuple[str, str]:
    """Return (model, effort). Images and diagnostic questions go to the smart model."""
    lowered = text.lower()
    diagnostic = any(re.search(rf"\b{re.escape(w.lower())}\b", lowered) for w in cfg.diagnostic_words)
    if has_image or diagnostic:
        return cfg.smart_model, cfg.smart_effort
    return cfg.fast_model, cfg.fast_effort


class Conversation:
    def __init__(self, client: anthropic.AsyncAnthropic | None, cfg: ClaudeConfig, tools_ctx: ToolContext) -> None:
        self.client = client
        self.cfg = cfg
        self.tools_ctx = tools_ctx
        # Append-only: assistant turns are stored exactly as returned (thinking blocks included).
        self.messages: list[dict] = []

    def reset(self) -> None:
        self.messages = []

    async def ask(
        self,
        text: str,
        on_text: Callable[[str], Awaitable[None]],
        on_tool: Callable[[str], Awaitable[None]] | None = None,
    ) -> str:
        """Send a user turn, stream reply text through on_text, run tools. Returns the full reply text."""
        if self.client is None:
            raise ClaudeUnavailable("I can't reach Claude yet. Add your Anthropic API key to the dot env file.")

        model, effort = pick_model(text, self.cfg)
        log.info("asking %s (effort %s): %r", model, effort, text)
        self.messages.append({"role": "user", "content": text})

        reply_parts: list[str] = []

        async def emit(chunk: str) -> None:
            reply_parts.append(chunk)
            await on_text(chunk)

        for _round in range(self.cfg.max_tool_rounds):
            final = await self._stream_turn(model, effort, emit)
            self.messages.append({"role": "assistant", "content": final.content})

            if final.stop_reason == "refusal":
                log.warning("refusal: %s", getattr(final, "stop_details", None))
                await emit(" Sorry, I can't help with that one.")
                return "".join(reply_parts)

            tool_uses = [b for b in final.content if b.type == "tool_use"]
            if not tool_uses:
                return "".join(reply_parts)
            if final.stop_reason == "max_tokens":
                # A truncated tool input can parse as a valid partial object; don't run it.
                raise ClaudeUnavailable("My answer got cut off. Try asking a shorter question.")

            results = []
            for block in tool_uses:
                if on_tool:
                    await on_tool(block.name)
                content, is_error = await run_tool(block.name, block.input, self.tools_ctx)
                log.info("tool %s -> %s", block.name, content)
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": content, "is_error": is_error})
            # All results for one assistant turn go back in a single user message.
            self.messages.append({"role": "user", "content": results})
            if reply_parts and not reply_parts[-1].endswith((" ", "\n")):
                await emit(" ")

        raise ClaudeUnavailable("I got stuck going back and forth with my tools. Try asking again.")

    async def _stream_turn(self, model: str, effort: str, emit: Callable[[str], Awaitable[None]]):
        kwargs = dict(
            model=model,
            max_tokens=self.cfg.max_tokens,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            tools=TOOLS,
            messages=self.messages,
            output_config={"effort": effort},
            cache_control={"type": "ephemeral"},  # also cache the growing conversation
            betas=[FALLBACK_BETA],
        )
        if model == self.cfg.smart_model:
            # Server-side retry on another model if a safety classifier declines.
            # Haiku has no server-side fallback, so it's only sent for the smart model.
            kwargs["fallbacks"] = "default"

        json_retries = 0
        while True:
            try:
                async with self.client.beta.messages.stream(**kwargs) as stream:
                    async for event in stream:
                        if event.type == "text":
                            await emit(event.text)
                    final = await stream.get_final_message()
                usage = final.usage
                log.info(
                    "%s done: stop=%s in=%s cache_read=%s cache_write=%s out=%s",
                    final.model, final.stop_reason, usage.input_tokens,
                    usage.cache_read_input_tokens, usage.cache_creation_input_tokens, usage.output_tokens,
                )
                return final
            except ValueError:
                # Tool-input JSON the SDK couldn't parse at all (eager input streaming).
                # No tool_use_id to answer, so re-issue the turn, bounded.
                json_retries += 1
                if json_retries > 2:
                    raise ClaudeUnavailable("I had trouble forming that answer. Please ask again.")
                log.warning("unparseable tool input; retrying turn")
            except anthropic.AuthenticationError as exc:
                raise ClaudeUnavailable("Claude rejected my API key. Check the key in the dot env file.") from exc
            except anthropic.PermissionDeniedError as exc:
                raise ClaudeUnavailable("My API key isn't allowed to use that model.") from exc
            except anthropic.NotFoundError as exc:
                raise ClaudeUnavailable(f"Claude says model {model} doesn't exist.") from exc
            except anthropic.RateLimitError as exc:
                raise ClaudeUnavailable("I'm being rate limited. Give me a minute.") from exc
            except anthropic.BadRequestError as exc:
                log.error("bad request: %s", exc)
                raise ClaudeUnavailable("Claude couldn't process that request.") from exc
            except anthropic.APIStatusError as exc:
                log.error("API error %s: %s", exc.status_code, exc)
                raise ClaudeUnavailable("Claude is having trouble right now. Try again in a moment.") from exc
            except anthropic.APIConnectionError as exc:
                raise ClaudeUnavailable("I can't reach Claude. Check the internet connection.") from exc
            except anthropic.AnthropicError as exc:
                # e.g. no credentials configured at all
                log.error("claude client error: %s", exc)
                raise ClaudeUnavailable("I can't reach Claude yet. Add your Anthropic API key to the dot env file.") from exc

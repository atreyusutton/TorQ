# TorQ

**A tracked garage robot that talks, sees, and helps you work on your car. Powered by Claude.**

TorQ rolls up next to you while you're under the hood. Ask it for a torque spec, a firing order, or "what's this part?" and point the camera at it. It listens, looks, and answers out loud so your hands stay on the wrench.

> Status: early build. Hardware is assembled, software is being wired up.

---

## What it does (goals)

- **Hands-free Q&A.** Talk to it like a shop buddy. It answers through the speaker.
- **Sees what you see.** Snaps a photo on request and sends it to Claude for identification or diagnosis ("is this belt cracked?", "which connector is the MAF?").
- **Drives itself around the car.** Claude can call tools like `drive`, `turn`, and `look` to reposition the camera.
- **Remembers the job.** Keeps notes on the current vehicle and task so you don't repeat yourself.
- **Fast.** Every stage streams. Speech starts playing before Claude finishes its answer.
- **Shows its state.** An LED ring tells you if TorQ is listening, thinking, or talking, so you know when to speak.
- **Live camera view.** Watch what TorQ sees from a browser on your Mac.
- **Manual drive.** Take over the tracks with your keyboard any time.

---

## Hardware

| Part | Notes |
|---|---|
| Raspberry Pi 5 (4GB RAM, 32GB storage) | The body. Runs I/O, motors, and safety. |
| 2x DC motors + tracks | Tank-style steering |
| Motor driver | TBD (needs one between Pi GPIO and motors) |
| Battery | TBD: separate rails for motors and Pi recommended |
| USB webcam | Vision input |
| USB microphone | Voice input |
| Speaker | Voice output |
| 4x LEDs (blue, yellow, green, red) + 330 ohm resistors | Status lights, phase 1 |
| WS2812 / NeoPixel ring (later) | Status lights, phase 2. Goes on the SPI pin |

---

## Architecture

TorQ is split into a **body** and a **brain**.

```
 ┌──────────── TorQ (Pi 5) ─────────────┐        ┌────────── Laptop (brain) ──────────┐
 │                                      │        │                                    │
 │  mic ──► wake word + VAD ──┐         │  audio │  speech-to-text (streaming)        │
 │                            ├────────────────► │         │                          │
 │  webcam ──► JPEG on request┘         │  frames│         ▼                          │
 │                                      │        │  orchestrator ◄──► Claude API      │
 │  speaker ◄── audio playback ◄──────────────── │         │        (tool use,        │
 │                                      │  audio │         ▼         vision)          │
 │  motors ◄── motor controller ◄───────────────-│  text-to-speech (streaming)        │
 │               ▲                      │commands│                                    │
 │         safety watchdog              │        │  job notes / vehicle memory        │
 └──────────────────────────────────────┘        └────────────────────────────────────┘
                      WebSocket over home LAN or Tailscale
```

### Body (Pi 5)

Does the cheap, time-critical stuff only:

- Wake word and voice activity detection (so we only stream audio when someone is talking)
- Capture and compress camera frames when asked
- Play audio chunks as they arrive
- Drive the motors
- **Safety watchdog:** if the link to the brain drops for more than ~500 ms, motors stop. Always local, never depends on the network.

### Brain (laptop)

- Streaming speech-to-text
- Orchestrator: builds the conversation, calls Claude, executes tool calls
- Streaming text-to-speech, chunked by sentence
- Vehicle and job memory (current car, what we're working on, specs already looked up)

### Dashboard (browser on the Mac)

A small web page served by the brain at `http://localhost:8000`:

- Live camera feed
- Current state (idle, listening, thinking, speaking, manual)
- Live transcript and Claude's replies
- Keyboard drive controls
- Link health: ping time, battery voltage, Wi-Fi signal

### Why not SSH for everything?

SSH is for development: deploying code, tailing logs, restarting services. The live robot traffic (audio, frames, motor commands) goes over a **persistent WebSocket**, which is lower overhead and easier to stream through.

---

## Claude integration

- **Model routing**
  - Fast model (Haiku class) for quick chat and simple lookups
  - Stronger model (Sonnet class) when an image is involved or the question is diagnostic
  - Model IDs live in `config.yaml`; check the [Anthropic models page](https://docs.claude.com/en/docs/about-claude/models) for current names
- **Streaming responses** so TTS can start on the first sentence
- **Prompt caching** on the system prompt and vehicle context to cut latency and cost
- **Tool use** for robot actions

### Tools exposed to Claude (draft)

| Tool | What it does |
|---|---|
| `drive(direction, distance_cm)` | Move forward or back |
| `turn(degrees)` | Pivot in place |
| `take_photo()` | Grab a frame and attach it to the conversation |
| `stop()` | Halt motors immediately |
| `save_note(text)` | Add to the current job notes |
| `get_vehicle_info()` | Return year/make/model/engine for the active car |

Motor tools are clamped on the Pi side (max speed, max distance per call) no matter what the model asks for.

---

## Status lights

The brain owns the state machine and tells the Pi which state it's in. The Pi only renders the LEDs, so they stay in sync with what's actually happening.

### Phase 1: plain LEDs (now)

Four LEDs on GPIO, one resistor each. Code is in `body/leds.py`.

| LED | BCM pin | Physical pin |
|---|---|---|
| Blue | GPIO17 | 11 |
| Yellow | GPIO27 | 13 |
| Green | GPIO22 | 15 |
| Red | GPIO23 | 16 |
| All grounds | GND | 9, 14, or 20 |

Wiring per LED: `GPIO -> 330 ohm -> LED + (long leg)`, `LED - (short leg) -> GND`.

| State | Light | Meaning for you |
|---|---|---|
| Idle | Green slow breathing | Say "Hey TorQ" |
| Listening | Blue solid | Talk now |
| Thinking | Yellow fast blink | Wait |
| Speaking | Green solid | Wait, or say "stop" (later) |
| Driving (Claude) | Yellow solid | Robot is moving on its own |
| Manual override | Blue slow blink | You have the controls |
| Link lost / error | Red fast blink | Motors are stopped |

Test it on the Pi:

```bash
pip install gpiozero lgpio
python body/leds.py --demo              # cycles every state, 3 s each
python body/leds.py --state thinking    # hold one state
```

### Phase 2: NeoPixel ring (later)

Same states, richer patterns (spinning amber for thinking, green that pulses with the audio). `leds.py` gets a `RingLeds` class with the same `set_state()` method, so the rest of the code doesn't change.

Short audio cues back up the lights: a chirp when it starts listening and a softer one when it stops, so you don't have to look.

**Mic handling:** the mic is muted while TorQ speaks so it doesn't hear itself. Barge-in ("TorQ, stop") is a later feature that needs echo cancellation.

**Ring wiring note (phase 2):** the usual `rpi_ws281x` library does not work on the Pi 5. Drive the ring over SPI (GPIO10 / MOSI) with `adafruit-circuitpython-neopixel-spi`, or hang a Pi Pico / Arduino off USB serial and send it state names. A level shifter (74AHCT125) from the Pi's 3.3V to the ring's 5V data line makes it reliable. Power the ring from the 5V rail, not a GPIO pin.

---

## Live camera view

The Pi serves a low-res **MJPEG stream** straight from the camera, separate from the high-res frames sent to Claude.

- Stream: `http://torq.local:8080/stream` (or the Tailscale name)
- Default 640x480 at 15 fps to go easy on Wi-Fi
- Embedded in the dashboard, or open it directly in any browser
- `take_photo()` still grabs a full-resolution frame for Claude

MJPEG is simple and works in every browser. If latency is a problem later, swap to WebRTC (for example with `mediamtx`).

---

## Manual drive

Keyboard control from the dashboard. Manual mode always beats Claude.

| Key | Action |
|---|---|
| `W` / `S` | Forward / reverse |
| `A` / `D` | Pivot left / right |
| `W`+`A`, `W`+`D` | Arc turns |
| `Shift` (hold) | Slow / precise mode |
| `1` to `5` | Speed limit |
| `Space` | **Stop** |
| `M` | Toggle manual override on / off |
| `Esc` | **E-stop**: kill motors, disable all driving until reset |

How it stays safe:

- **Hold to drive.** The browser resends the current command every 100 ms while a key is held. When you let go, or the tab loses focus, commands stop.
- **Pi watchdog.** No drive command for 300 ms means motors stop. Same rule covers a dropped link.
- **Override lock.** While manual mode is on, Claude's `drive` and `turn` tools return "manual override active" instead of moving.
- **Speed clamps** live on the Pi, so a bad command from anywhere can't exceed them.

---

## Networking

| Where | Plan |
|---|---|
| Home | Pi and laptop on the same LAN. Lowest latency. |
| School / anywhere else | [Tailscale](https://tailscale.com) on both devices. Gets around client isolation and captive-portal weirdness on campus networks. Phone hotspot as backup. |
| Garage with weak signal | Wi-Fi extender or mesh node near the work area. Metal car bodies eat signal. |

---

## Latency budget (target)

| Stage | Target |
|---|---|
| End of speech detected | ~300 ms after you stop talking |
| Speech-to-text final | < 300 ms |
| Claude first token | model dependent, aim < 1 s for fast model |
| First audio out | < 2 s from end of your sentence |

---

## Repo layout (planned)

```
torq/
├── body/            # runs on the Pi
│   ├── audio_io.py
│   ├── camera.py
│   ├── motors.py
│   ├── watchdog.py
│   ├── leds.py      # renders state on the LED ring
│   ├── stream.py    # MJPEG camera server
│   └── link.py      # WebSocket client
├── brain/           # runs on the laptop
│   ├── server.py    # WebSocket server
│   ├── stt.py
│   ├── tts.py
│   ├── claude.py    # API calls, tool loop, model routing
│   ├── tools.py
│   ├── state.py     # idle / listening / thinking / speaking / manual
│   ├── memory.py
│   └── dashboard/   # web UI: camera, transcript, keyboard drive
│       ├── index.html
│       └── drive.js
├── config.yaml
└── README.md
```

---

## Getting started

```bash
# brain (laptop)
cd brain
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...
python server.py

# body (Pi)
cd body
pip install -r requirements.txt
python main.py --brain ws://<laptop-ip-or-tailscale-name>:8765
```

Then open `http://localhost:8000` on the Mac for the dashboard.

Never commit your API key. Keep it in an env var or a `.env` file listed in `.gitignore`.

---

## Roadmap

- [ ] Pi talks to laptop over WebSocket, round-trip ping
- [ ] Motor control with watchdog and speed limits
- [ ] Dashboard with keyboard drive and E-stop
- [ ] MJPEG camera stream in the dashboard
- [ ] Plain LEDs wired up, `leds.py --demo` works
- [ ] LED states driven from the brain
- [ ] Swap to NeoPixel ring
- [ ] Mic audio streams to laptop, transcript prints
- [ ] Claude answers text questions, TTS plays on the Pi
- [ ] Wake word ("Hey TorQ") with listen/stop chirps
- [ ] `take_photo` tool with vision
- [ ] Claude drive tools, locked out during manual override
- [ ] Vehicle profiles and job notes
- [ ] Standalone mode (Pi talks to cloud directly when the laptop isn't around)
- [ ] Service manual / spec lookup

---

## License

TBD

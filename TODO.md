# TorQ TODO

## Done
- [x] Pi 5 headless setup (`ssh torq`, Wi-Fi + Ethernet to Mac, Pi Connect backup)
- [x] Arduino drive firmware with watchdog, E-stop, ramping, overcurrent cutoff, active braking
- [x] Pi ↔ Mac WebSocket link with ping (`body/link.py`, `brain/server.py`)
- [x] Motor control with speed clamps, trim, min PWM, command timeout (`body/motors.py`)
- [x] Dashboard with keyboard drive and E-stop (`http://localhost:8000`)
- [x] MJPEG camera stream (ustreamer, `:8080/stream`) in the dashboard
- [x] Body auto-starts on the Pi (systemd: `torq-body`, `torq-camera`)
- [x] Integration tests (`.venv/bin/python -m pytest`)

## Next
- [ ] Replace stripped left gearmotor (Greartisan 12V 100RPM 37mm), rerun direction/current test
- [ ] Tune `motors.min_pwm` and `trim_left`/`trim_right` on the floor
- [ ] Wire 4 status LEDs, write `body/leds.py` (`--demo`, `--state`), drive from brain state
- [ ] Mic audio streams to Mac, transcript prints (local STT: faster-whisper)
- [ ] Claude answers text questions, TTS plays on the Pi (local TTS: Piper; speaker max 90%)
- [ ] Wake word ("Hey TorQ") with listen/stop chirps
- [ ] `take_photo` tool with vision (decide: full-res grab vs. ustreamer snapshot)
- [ ] Claude drive tools, locked out during manual override
- [ ] Vehicle profiles and job notes
- [ ] NeoPixel ring (SPI already enabled)

## How to run
- Brain (Mac): `.venv/bin/python -m brain.server`, then open http://localhost:8000
- Deploy body to Pi: `scripts/deploy-body.sh`
- Pi logs: `ssh torq journalctl -fu torq-body`

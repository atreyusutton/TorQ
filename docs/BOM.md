# TorQ — Parts List

Prices are approximate US street prices for one unit. Order **everything in week 1** —
shipping on servos is routinely 2–4 weeks, which is a quarter of a 12-week project.

---

## Core build

### Brains
| Part | Why | ~$ |
|---|---|---|
| Raspberry Pi 5, 4GB | Runs the screen, browser, video decode and local embedding search. 2GB is tight once Chromium and `mpv` are both up | 60 |
| 256GB USB SSD **or** A2 microSD | Manual page images run ~400MB per manual. Do not use the 32GB card from a starter kit | 25 |
| RP2350 (Pico 2) | Real-time motor and servo loop. Keeps the robot safe if the Pi wedges | 5 |

### Head
| Part | Why | ~$ |
|---|---|---|
| Pi Camera Module 3 Wide | Autofocus matters — it's your inspection magnifier as well as your camera | 35 |
| 2× GC9A01 240×240 round LCD | The eyes. Best emotion-per-dollar part in the build | 16 |
| COB LED ring + driver | Work light, coaxial with the lens so it lights exactly what it films | 8 |
| BNO085 IMU | Pick-up/tilt detection **and** the digital angle gauge | 20 |

### Belly
| Part | Why | ~$ |
|---|---|---|
| 7in DSI **touchscreen** (1024×600) | The main interface. **Buy the touch version** — +$15 now, a panel swap later | 60 |
| Spring counterbalance + hinge hardware | So the hinge servo isn't holding screen weight all day | 6 |

### Motion — 4 servos, one bus
| Part | Why | ~$ |
|---|---|---|
| 2× Feetech STS3215 | **Neck tilt** and **belly hinge** — the two load-bearing joints | 36 |
| 2× Feetech STS3032 | Head pan, head tilt | 24 |
| FE-URT-1 servo bus adapter | One daisy-chained wire for all four joints | 8 |
| 2× N20 encoder gearmotor, 1:100 | Tracks. Encoders give closed-loop speed and straight-line driving | 20 |
| TB6612FNG motor driver | Skip the L298N — the voltage drop at 7.4V is brutal | 5 |

> Keep **all four servos in the STS protocol family.** Do not mix in SCS-series parts —
> debugging a servo bus alongside everything else is a bad week.

### Senses and sound
| Part | Why | ~$ |
|---|---|---|
| 3× VL53L1X ToF | One forward, two down at the track nose for cliff detection | 24 |
| I2S mic (INMP441) | Mount it high in the head, away from motor whine | 8 |
| MAX98357A I2S amp + 5W speaker | **Buy the good speaker.** Chirps sound fine on a cheap driver; speech does not | 15 |
| Rubber push-to-talk button | Hit it with a knuckle. Garages are loud and voice will fail sometimes | 4 |

### Power
| Part | Why | ~$ |
|---|---|---|
| 4× 18650 + BMS + holder (2S2P) | ~25Wh | 30 |
| Buck converters 5V/5A + 6V/5A + bulk caps | **Separate rails.** Servo inrush browning out the Pi is the #1 killer of Pi robots | 15 |
| MAX17048 fuel gauge | So it knows when it's tired | 6 |

### Body
| Part | Why | ~$ |
|---|---|---|
| Neodymium magnets — tray + sweeper strip | Parts tray on top; removable sled underneath that collects dropped screws | 10 |
| Bearings, M3 hardware, JST connectors, wire | **Connectors, not solder joints** — every soldered wire is one you must desolder to change anything | 30 |
| PETG + TPU filament | Body in PETG, track pads and jaw-side grips in TPU | 30 |

### Core subtotal — **≈ $495**

---

## Spares — buy these too (~$57)

You *will* strip a servo horn and burn a driver. If the replacement is three weeks
out, you lose three weeks. This is the best money in the build.

| Part | ~$ |
|---|---|
| 2× spare servo (1 large, 1 small) | 30 |
| 2× spare motor driver | 10 |
| 2× spare buck converter | 12 |
| Spare Pico 2 | 5 |

---

## Optional

| Part | Why | ~$ |
|---|---|---|
| ELM327 Bluetooth OBD-II dongle | Read trouble codes, then show the matching manual page. Best value-per-dollar upgrade available. **1996+ vehicles only** | 15 |
| Hailo-8L AI HAT | On-device vision for v2. The Pi's PCIe slot stays free for it | 70 |

---

## Totals and honest budget drift

| | ~$ |
|---|---|
| Core | 495 |
| + Spares | 552 |
| + OBD-II dongle | 567 |

The original target was $400, and it drifted. Where it went: the touchscreen upgrade,
256GB of storage for manual pages, a 4GB Pi instead of 2GB, the good speaker, the mic
and button, the fuel gauge and the magnets. Every one of those came from a decision
made deliberately in this project — but it's still drift, and worth naming.

**To get back near $400:** a 5in screen instead of 7in (−$25), microSD instead of SSD
(−$10), a 2GB Pi (−$15), and skip the fuel gauge (−$6) → **≈ $439 core.** That's the
honest floor without giving up anything structural.

**Not on the cut list at any price:** separate power rails, encoders on the motors,
cliff sensors, and the spares kit. Those four are what stand between you and a
project that dies in week 6.

---

## Software (all free)

`build123d` (parametric CAD) · Python + asyncio · Chromium kiosk for the belly ·
`yt-dlp` + `mpv` (video) · `picamera2` · `sqlite` + a local embedding model
(retrieval) · `pymupdf` + `tesseract` (manual ingest) · Claude API (~$4/month —
see `LLM.md`) · optional `piper` (local TTS), `openWakeWord` + `vosk` (voice)

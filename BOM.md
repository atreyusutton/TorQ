# TorQ — Parts List

**v2 — hands-held screen, stock chillibasket chassis.**
v1 (belly screen, custom body) is archived at `_archive/BOM-v1-belly-screen.md`.

Prices are approximate US street prices for one unit. Order **everything in week 1** —
shipping on servos is routinely 2–4 weeks, which is a quarter of a 12-week project.

---

## What changed in v2, and why

Three decisions drove this list:

1. **The chassis is the [chillibasket WALL·E](https://www.printables.com/model/408363-wall-e) as-published.** We inherit his body CAD, his assembly PDF and his Arduino motion code instead of writing them. That deletes the two largest schedule risks in `PLAN.md`.
2. **The screen moved from the belly to the hands.** This is a strictly better idea than v1 and it solves a problem we had: a hands-held screen needs **no chest surgery**, so the body stays stock. It also puts the screen at a height you can aim, and Wall-E holding something up in both hands is the most in-character pose he has.
3. **The screen dropped to 5".** Not a budget cut — a load cut. Every gram in the hands is torque at the shoulder and forward tip-over on the tracks.

The cost of moving the screen to the hands is that **the arms are now structural.** Stock arms are pressure-fit posable plastic; ours carry ~280g out in front of the robot. That is where the new money in this list goes.

---

## Core build

### Brains and storage
| Part | Why | ~$ |
|---|---|---|
| Raspberry Pi 5, 4GB | Runs the screen, browser, video decode and local embedding search. 2GB is tight once Chromium and `mpv` are both up | 60 |
| 256GB USB SSD **or** A2 microSD | Manual page images run ~400MB per manual. Do not use the 32GB card from a starter kit | 25 |
| Arduino Uno | Chillibasket's motion firmware targets it. Using his board means using his working code | 12 |
| Motor driver shield | Same reason — it's what his sketch drives | 13 |

> We are deliberately **not** substituting a Pico 2 here. The whole point of taking his
> chassis is taking his firmware with it. Swap the board and you inherit the CAD but
> re-debug the motion loop, which is the expensive half.

### The screen and the path to it
| Part | Why | ~$ |
|---|---|---|
| 5in DSI **touchscreen** (800×480) | The main interface. **Buy the touch version.** 5in is the ceiling for a hands-held panel at 41% scale | 40 |
| **2× DSI FFC ribbon, 22-pin → 15-pin, 300mm** | Pi 5 uses the 22-pin 0.5mm connector; most 5in panels are 15-pin 1mm. **Buy two** — see the warning below | 12 |
| Screen carrier frame hardware — M2.5 standoffs, nylon washers | The printed carrier the hands actually grip | 8 |
| Magnetic dock pads, chest | Screen parks flat against his chest when driving. Protects the panel, pulls the CG back over the tracks | 6 |

> ### ⚠ The ribbon cable is the weakest part in this list
>
> A DSI flex cable crossing a moving shoulder joint will eventually fail — flex cables
> are rated for a limited number of bend cycles and a shoulder is thousands. Two
> mitigations, both cheap:
>
> - **Route the cable through the shoulder pivot axis so it twists rather than bends.**
>   Costs nothing, buys an order of magnitude in cycles.
> - **Buy the spare now.** A $6 cable that's three weeks out in week 10 is a dead project.
>
> **The lower-risk alternative, worth considering:** mount the Pi 5 *on the screen
> carrier*, behind the panel. It's 85×56mm and it fits. Then the DSI cable is 100mm and
> never moves, and the only thing crossing the shoulder is 5V power and one USB lead to
> the Arduino. This is the more robust design. It costs you a heavier hand assembly
> (~46g) and a longer power run. **[assumed: you want the ribbon-through-the-arm version
> since you asked for the cable — both are priced here, pick one at assembly time]**

### Arms — now load-bearing
| Part | Why | ~$ |
|---|---|---|
| 2× Feetech STS3215 | **Shoulder lift.** MG90S will not hold 280g out on a lever arm — it will buzz, creep and strip. This is the one place stock servos are not enough | 36 |
| FE-URT-1 servo bus adapter | Drives both STS servos off the Pi on one wire | 8 |
| 2× 4mm carbon fibre tube + M3 hardware | Runs inside each printed arm. Printed PETG arms alone will creep under a static load over weeks | 8 |
| Shoulder bearings (608 / flanged) | Takes the radial load off the servo shaft | 8 |

> **Sync the arms or they fight each other.** Two arms holding one rigid screen is a
> closed loop — if the servos disagree by two degrees they lever against each other
> until something strips. Simplest fix that costs nothing: **drive one arm, let the
> other idle on a free pivot**, and let the screen's own hand joints self-align.

### Head, vision and sensing
| Part | Why | ~$ |
|---|---|---|
| Camera | **You already have this — no purchase.** See the caveat below | 0 |
| 7× MG90S micro servo | Eyes, head pan, neck. Exactly his stock list, so his code drives them unchanged | 20 |
| PCA9685 I²C servo board | Same — what his build expects | 10 |
| BNO085 IMU | Pick-up/tilt detection **and** the digital angle gauge | 20 |

> **Camera caveat:** if what you have is a generic USB webcam, it's fine for presence
> and framing, but it is fixed-focus — and that **kills the magnifier feature** in
> `CAPABILITIES.md`, which needs to focus at 5–10cm. If the magnifier matters, budget
> **$35 for a Pi Camera Module 3 Wide** (listed under Optional). If it doesn't, the
> camera you have is genuinely fine and this line stays $0.

### Light
| Part | Why | ~$ |
|---|---|---|
| COB LED ring + driver | Coaxial with the lens, so it lights exactly what the camera films — how borescopes do it | 8 |
| 3W high-CRI LED flood + constant-current driver | **The flashlight.** Aimed with the head, switchable from the screen. High-CRI matters: cheap cool-white LEDs make fluid colours unreadable, and telling ATF from coolant by colour is a real diagnostic | 10 |
| 2× MOSFET driver module | The Pi's GPIO cannot source LED current. Don't skip these | 6 |
| Detachable magnetic COB work light | Docks on the magnetic tray, comes off in your hand when you need to get under something the robot can't reach. Zero integration, zero software, genuinely the most-used light on the robot | 12 |

> Two lights, two jobs: the ring is for **what the camera sees**, the flood is for
> **what you see**. Wiring them to one switch would make both worse.

### Drivetrain
| Part | Why | ~$ |
|---|---|---|
| 2× 12V geared motor, 100–150RPM, ⌀37mm | His printed treads are designed around this exact motor. Substituting means re-CADing the drive sprockets | 30 |
| Motor driver, 12V / 3A continuous | Sized for the above. Skip the L298N | 12 |

### Power
| Part | Why | ~$ |
|---|---|---|
| 3S2P 18650 pack + BMS + holder | **12V, not the 7.4V in v1** — the geared motors need it. ~38Wh | 40 |
| Buck converters 12V→5V/5A + 12V→6V/5A + bulk caps | **Separate rails.** Servo inrush browning out the Pi is the #1 killer of Pi robots | 18 |
| MAX17048 fuel gauge | So it knows when it's tired | 6 |

### Sound and input
| Part | Why | ~$ |
|---|---|---|
| I2S mic (INMP441) | Mount it high in the head, away from motor whine | 8 |
| MAX98357A I2S amp + 5W speaker | **Buy the good speaker.** Chirps sound fine on a cheap driver; speech does not | 15 |
| Rubber push-to-talk button | Hit it with a knuckle. Garages are loud and voice will fail sometimes | 4 |
| 3× VL53L1X ToF | One forward, two down at the track nose for cliff detection | 24 |

### Body
| Part | Why | ~$ |
|---|---|---|
| Neodymium magnets — tray + sweeper strip | Parts tray on top; removable sled underneath that collects dropped screws | 10 |
| Rear counterweight (steel/lead shot) | He holds 280g out front on tracks. Move the CG back or he noses over on a ramp | 5 |
| Bearings, M3 hardware, JST connectors, wire | **Connectors, not solder joints** — every soldered wire is one you must desolder to change anything | 30 |
| PETG + TPU filament, ~3kg | **310 parts.** This is not the 1kg spool you have. Body in PETG, track pads in TPU | 60 |

### Core subtotal — **≈ $584**

---

## Spares — buy these too (~$48)

You *will* strip a servo horn and burn a driver. If the replacement is three weeks
out, you lose three weeks. This is the best money in the build.

| Part | ~$ |
|---|---|
| Spare STS3215 (the shoulder — highest-load part on the robot) | 18 |
| 2× spare MG90S | 6 |
| 2× spare motor driver | 12 |
| 2× spare buck converter | 12 |

*(The spare DSI ribbon is already in the core list. It's not optional.)*

---

## Optional

| Part | Why | ~$ |
|---|---|---|
| Pi Camera Module 3 Wide | **Only if you want the magnifier.** Autofocus is what makes it an inspection camera rather than a webcam | 35 |
| ELM327 Bluetooth OBD-II dongle | Read trouble codes, then show the matching manual page. Best value-per-dollar upgrade available. **1996+ vehicles only** | 15 |
| Hailo-8L AI HAT | On-device vision for v2. The Pi's PCIe slot stays free for it | 70 |

---

## Totals

| | ~$ |
|---|---|
| Core | 584 |
| + Spares | 632 |
| + Camera Module 3 (if you want the magnifier) | 667 |
| + OBD-II dongle | 682 |

### Where this differs from v1's $495

| Change | Δ |
|---|---|
| 7in screen → 5in | −20 |
| Belly hinge hardware deleted (no belly screen) | −6 |
| N20 motors + 2S pack → 12V geared motors + 3S pack | +25 |
| Arms made structural (2× STS3215, carbon, bearings) | +28 |
| DSI ribbon + spare, screen carrier, magnetic dock | +26 |
| The flashlight and its drivers | +28 |
| Arduino Uno + shield (his firmware) | +25 |
| Filament 1kg → 3kg (310 parts) | +30 |
| Camera (already owned) | −35 |
| Rear counterweight | +5 |

The build got *more* expensive and *less* risky. That's the trade we chose.

---

## The three things most likely to go wrong

1. **The ribbon cable across the shoulder.** Mitigated with a twist route and a spare. Consider the Pi-behind-the-screen layout instead.
2. **The arms sagging or the servos stripping.** Mitigated with carbon spars and STS3215s — but *measure the actual finished screen assembly weight before you trust this list*. If it comes in over ~350g, the arms need a mechanical rest position they lock into, not a servo holding load all day.
3. **A month of printing.** 310 parts, largest at 14h. This starts week 1, in parallel with everything else. It is not a week-4 activity.

---

## Software (all free)

Chillibasket's Arduino sketch + Python control stack (motion — inherited) ·
Python + asyncio · Chromium kiosk for the screen · `yt-dlp` + `mpv` (video) ·
`picamera2` or `opencv` (camera) · `sqlite` + a local embedding model (retrieval) ·
`pymupdf` + `tesseract` (manual ingest) · Claude API (~$4/month — see `LLM.md`) ·
optional `piper` (local TTS), `openWakeWord` + `vosk` (voice)

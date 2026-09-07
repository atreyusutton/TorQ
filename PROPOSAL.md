# TorQ — Proposal to the Group

**Replaces:** the composting trash robot
**Timeline:** 12 weeks, unchanged · **Budget:** ~$500, unchanged
**Status:** proposed — read it, then tell me what you think

---

## The short version

I want us to build **TorQ: a tracked robot that stores our service manuals and puts
the right page in front of you.**

Ask it a torque spec, it finds the page and displays it on a hinged screen in its
belly, tilted up to your eyeline. It's also a lit inspection magnifier for reading
part numbers, it picks up dropped fasteners with a magnet, and it runs timers for
torque sequences and cure times.

The chassis, drive, power, compute and sensors are **the same robot we already
planned**. What changes is what it carries and what it does. This is a payload swap,
not a restart — roughly 70% of the build is untouched.

---

## Why the composting robot doesn't work

Two of these are physics and calendar facts, not opinions. Either one alone kills it.

### 1. Composting has a minimum mass we cannot put on a robot

Thermophilic composting — the kind that actually breaks material down — needs the
pile at 55–65 °C. That heat is **metabolic**: the microbes make it, and the pile has
to insulate itself to hold it. The standard minimum for a self-sustaining hot pile is
about **one cubic yard, roughly 250 kg.**

A few-liter vessel on a robot has far too much surface area for its volume. It sits
at ambient and does nothing. Heat it electrically instead and our **25 Wh** battery
is gone in under an hour, against a process that runs for weeks.

> Composting wants to be stationary, massive and insulated. A robot has to be light
> and moving. Those requirements are directly opposed.

### 2. The validation cycle is longer than the project

A hot compost cycle is **4–8 weeks**. We have **12**, minus fabrication and bring-up.

That's **one** observation of whether it works, arriving at or after the deadline.
No measure → adjust → measure. We'd be handing in an untested machine and reporting
whatever it happened to do.

### 3. Collection depends on grasping — and it's a single point of failure

Picking up waste means grasping unknown, irregular objects: a multi-DOF arm, inverse
kinematics, grasp planning, and closed-loop visual servoing, because tracks slip and
dead reckoning can't reach grasping tolerance.

If it doesn't work, the robot has **no function at all**. And the physics don't close
anyway — realistic payload at our budget is **50–150 g**. A drink can, a bottle and a
food container all exceed that.

### 4. None of us can check our own work in that domain

Carbon-to-nitrogen ratios, moisture, aeration — we'd be guessing at requirements, with
no way to tell a good decision from a bad one and no ground truth to correct us.

**Together:** partial completion has no value. A composter that never finishes a cycle
isn't a partial composter, it's a bin. Nothing degrades gracefully — which is the one
property a fixed deadline demands.

---

## How TorQ works

### The governing rule

**It never shows a value without showing where the value came from.**

A wrong torque figure damages an engine or loses a wheel. So the system's job is not
to *know* the answer — it's to **find the page** and put it on screen so you can
verify it yourself. Everything below is built around making that structural rather
than aspirational.

### Phase 1 — Ingest (on a laptop, once per manual)

```
PDF ──► render every page to PNG          (pymupdf)
    ──► extract text; OCR the scans       (tesseract)
    ──► chunk per page, embed             (bge-small, local)
    ──► sqlite: {manual, page, text, embedding, png}
    ──► [optional] vision pass over table pages → structured torque rows
    ──► copy the folder to the robot
```

This runs on a real computer, **never on the Pi** — OCR and embedding a 400-page scan
is slow, and nobody is waiting on it. The robot only ever does lookup and display.

The optional vision pass is where a model earns the most and is safest: it extracts
torque tables into structured rows we can **eyeball once against the page and then
trust forever**, instead of a model improvising a number live.

### Phase 2 — Query (on the robot)

```
question  ──► embed locally on the Pi
          ──► top-k pages by similarity, filtered by vehicle
          ──► SHOW THE PAGE IMAGE on the belly
          ──► if online: model reads those pages, returns a plain-English
               answer + a structured citation (exact page number)
          ──► if offline: hit the pre-extracted spec table — instant, no model
```

Questions arrive three ways: typed on your phone, tapped on the belly, or spoken.

### Why this is safe

The citation isn't prose the model writes and we hope is honest — the API returns
**`page_location` as a structured field**. We render that page next to the answer.
A wrong answer becomes *visible* instead of silent.

### It degrades instead of breaking

| State | What you get |
|---|---|
| Everything working | Plain-English answer + the cited manual page |
| No internet | Pre-extracted spec table + the page image. **Faster than online** |
| Nothing matches | The retrieved page, you read it yourself |
| Retrieval broken | Still a mobile display you can drive around |

There is no single point of failure anywhere in that ladder.

---

## The hardware

### Two brains, on purpose

| | Part | Job |
|---|---|---|
| Cortex | Raspberry Pi 5, 4GB | Screen, web app, camera, retrieval, WiFi, model calls |
| Cerebellum | RP2350 (Pico 2) | 200 Hz control loop, servo bus, motor PID, encoders, cliff watchdog, e-stop |

They talk over USB serial at ~50 Hz with a small binary protocol.

**Why split:** Linux cannot hold a real-time loop. The microcontroller keeps the robot
safe — stops at cliffs, holds servo positions, cuts the motors — even if the Pi
reboots, hangs, or we crash it while developing. This is what stops a bug from
becoming a robot on the floor.

### Drive

2 × N20 gearmotors (1:100) with magnetic encoders, TB6612FNG driver, closed-loop
velocity PID on the MCU. Printed sprockets, idlers and road wheels with TPU track pads.

**3 × VL53L1X time-of-flight:** one forward for obstacles, two pointed down at the
track nose for cliff detection — so it can't drive off a bench.

Encoders are non-negotiable: without them it can't drive in a straight line.

### Head — 3 servos

Pan, neck tilt, head tilt. Carries:

- **Pi Camera Module 3 Wide** (autofocus) — filming, the inspection magnifier, reading
  part numbers and VIN plates
- **COB LED ring, coaxial with the lens** — lights exactly what the camera sees, the
  way a borescope does. Aiming the head aims both at once
- **2 × GC9A01 round LCDs** — the eyes
- Perlin-noise idle motion and variable blink, so it doesn't read as broken when still

### Belly — 1 servo

7″ DSI **touchscreen** on a spring-counterbalanced hinge. Tilts to your eyeline —
a robot on the floor and a robot on the bench need very different angles, and a fixed
screen is unreadable half the time.

The counterbalance matters: without it the servo holds screen weight all day, heats
up, and drains the battery.

### Everything else

- **BNO085 IMU** — detects being picked up or tilted, *and* doubles as a digital
  angle gauge for driveline and pinion work
- **INMP441 mic**, mounted high and away from motor whine, plus a **rubber
  push-to-talk button** you can hit with a knuckle, because shops are loud
- **MAX98357A amp + 5 W speaker** — buy the good one; chirps forgive a cheap driver,
  speech doesn't
- **Magnets:** a parts tray on the top deck, and a removable sled underneath that
  sweeps up dropped screws as it drives

### Power — where these builds die

2S2P 18650 pack, ~25 Wh, with **separate rails**: 5 V/5 A for the Pi, 6 V for the
servo bus, common ground, fat bulk caps on the servo rail. MAX17048 fuel gauge.

**Servo inrush browning out the Pi is the number one killer of Raspberry Pi robots.**
If we get this wrong we spend the term chasing mystery reboots through a closed
chassis. It's the first thing we prove on the bench and the last thing we compromise.

### Four moving joints, total

Head pan · neck tilt · head tilt · belly hinge. No arms, no gripper, no legs.
The earlier designs had nine. Every joint we deleted is a bracket, a wire, a tuning
session and a failure mode we don't spend the term on.

---

## The software

| Layer | Choice | Why |
|---|---|---|
| Robot service | Python + asyncio, internal event bus | Simple, no ROS ceremony we don't need |
| Firmware | C or MicroPython on the Pico | The real-time half |
| Belly UI | **Chromium kiosk → localhost** | Every feature is a web page; fast to build |
| Phone UI | **The same web app** at `torq.local` | One codebase, two surfaces. Type on your phone, read on the belly |
| Video | `yt-dlp` + `mpv` | Not an embedded browser player — hardware decoded, caches, survives bad shop WiFi |
| Camera | `picamera2` | H.264 hardware encode |
| Retrieval | `sqlite` + local embeddings | Runs offline |
| Ingest | `pymupdf` + `tesseract` | Laptop-side |
| CAD | `build123d` | Parametric — one config file drives every dimension |

**No ROS 2.** Nav2 and tf2 are a lot of ceremony for a robot that doesn't need
SLAM-grade navigation, and the setup cost would eat weeks we don't have.

---

## What carries over from the compost build

**Unchanged (~70%):** tracked base and chassis · closed-loop velocity from encoders ·
the Pi + microcontroller split · dual-rail power and brownout work · IMU · ToF cliff
and obstacle sensing · camera · articulated head · parametric CAD · idle motion

**Removed (all risk reduction):** arm · gripper · inverse kinematics · grasp planning ·
onboard bioreactor · heating · moisture and temperature control

**Added:** hinged display · document retrieval over ingested PDFs · offline-first data
architecture · grounded citation

---

## The 12-week plan

| Week | Work | Done when |
|---|---|---|
| 1 | **Order everything**, including spares. Start CAD | Parts are paid for |
| 2 | **Manual ingest + search on a laptop.** Web app skeleton | Type a query, get the right page. No robot needed |
| 3 | Parts arrive. Bench rig: Pi + Pico + one servo + one eye | Command a servo from Python on the Pi |
| 4 | Head on the bench: 3 DOF, eyes, LED ring, idle motion | **It feels alive on the desk** |
| 5 | Power: battery, dual rails, caps. Motors on the bench | Servos slam and the Pi doesn't reboot |
| 6 | Drivetrain: tracks, velocity loop, cliff sensors, joystick | Drives straight, stops at an edge |
| 7 | Chassis integration — head on base, wiring, untethered | Drives around the shop |
| 8 | **Slack week** | Back on schedule |
| 9 | Belly: screen, hinge, counterbalance. Search on the real panel | Read a spec off its belly |
| 10 | **Model-backed answers with citations**, then voice, then video. **FREEZE** | Ask in plain English, get number + page |
| 11 | Reliability only. Crashes, connectors, heat, battery life | Runs a full job unattended |
| 12 | Polish, shell, README, demo | Done |

**Two rules I'd ask us to hold:** week 8 stays empty, and week 10 is a hard feature
freeze. The last two weeks make what exists reliable — that's the difference between
a project and a demo.

### Four workstreams we can run in parallel

| Track | Owns | Starts | Needs parts? |
|---|---|---|---|
| **A — Mechanical** | build123d body, tracks, head, hinge, print iteration | Week 1 | No |
| **B — Electronics/firmware** | Power rails, Pico loop, servo bus, sensors, USB protocol | Week 3 | Yes |
| **C — Data/retrieval** | Ingest pipeline, search, spec extraction | **Week 1** | **No** |
| **D — Interface** | Web app, belly UI, phone UI, player, timers | Week 2 | No |

**Track C is the important one.** It's the whole product, it's the riskiest software,
and it needs **no hardware at all** — so somebody can start it on day one while we're
all waiting on shipping. If it fails we find out in week 2 with ten weeks to recover,
instead of week 9 with none.

A and B converge at week 7 (integration). C and D converge at week 9 (belly).

---

## What ships, even if things go wrong

**Week 9 — the floor. This must land.**
Drives, won't fall off a bench, tilts its screen, finds the manual page, magnifies a
part number, picks up dropped screws, runs timers. **No voice, no video, no language
model** — and still a real tool.

**Week 10 — the priority.** Plain-English answers with cited pages. ~$4/month to run.

**Week 10 — droppable.** Voice, then video. Separate bets; losing either breaks
nothing under it.

**After.** OBD-II trouble codes chained to the manual's diagnostic page. Digital angle
gauge. Reading specs aloud. The personality layer.

**If we fall behind, we cut in this order** — decided now, while we're calm: video
search → photo log → voice → motorized hinge → the model. Never the manual search or
the screen.

---

## Parts and budget

**≈ $495 core, ≈ $552 with spares, ≈ $567 with an OBD-II dongle.** Full line-by-line
list in `BOM.md`.

Two things I'd push on:

- **Order in week 1, all at once.** Servo lead times run 2–4 weeks. That's a quarter
  of our project spent waiting if we're slow.
- **Buy the ~$57 spares kit.** We *will* strip a servo horn and burn a driver. A
  three-week replacement wait costs us three weeks. It's the best money in the build.

Four things I don't think we should cut at any price: separate power rails, motor
encoders, cliff sensors, and the spares kit. Those are what stand between us and a
project that dies in week six.

---

## Where I stand

I'm attached to this one. I've put the work in because I think it's the right call for
us, and I'd rather say that straight than pretend I'm neutral about it.

It's still our project, though — so if you don't like it, I'm not asking you to just
go along with it. **Bring an alternative worked out to the same level:**

- What hardware it needs, down to a parts list and a budget
- What software it needs, and which part is the hardest
- A 12-week schedule with the risky work scheduled early
- Where it fails, and what still ships when it does

Put that on the table and if it's better than this, I'll build yours.

What I'd rather we didn't do is pick something on the strength of the idea alone and
find out in week eight that the physics or the calendar don't allow it. That's exactly
what happened to the compost robot, and the only reason it cost us nothing is that we
caught it in week zero.

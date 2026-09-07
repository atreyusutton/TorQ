# TorQ — What It Can Be, and What Must Land

Two questions answered here: **what is the smallest TorQ that's still worth having**
(so the deadline is safe), and **what else this exact hardware can do** without
buying anything new.

---

## Part 1: The three tiers

### Tier 0 — THE FLOOR. Lands week 9. This must happen.

> **A rolling, tilting screen that shows you the right page of your service manual,
> plus a magnifying inspection camera and a magnet that picks up your dropped screws.**

| Capability | Needs |
|---|---|
| Drives under phone teleop, won't fall off a bench | tracks, encoders, cliff ToF |
| Head moves, eyes animate, reads as alive | 3 servos, LCD eyes |
| Belly screen tilts to your eyeline | hinge servo |
| **Manual page lookup** — type on phone, read page on belly | Pi + storage + week-2 software |
| **Live camera magnifier** on the belly | camera + LED ring |
| Magnetic parts tray + floor sweeper sled | magnets, no motors |
| Timers, counters, unit conversion | screen |
| Chirps and idle motion | speaker |

**No voice. No YouTube. No LLM at all** — pure retrieval, showing the page.

That is still a genuinely useful shop tool and a charming object on your bench. If
everything after week 9 fails, you shipped something real. **This is the definition
of acceptable, and the schedule puts it three weeks before the deadline.**

### Tier 1 — THE TARGET. Week 10, then freeze. **In this order.**

- **1a. The LLM** — natural-language spec lookup answering off the manual page, with
  **native API citations** giving the exact page number. See `LLM.md`. This is the
  priority; it goes first and it is cut last.
- **1b. Voice commands** + push-to-talk
- **1c. YouTube playback** via `yt-dlp` + `mpv`

Each is **independently droppable** and none breaks anything below it — Tier 1 is
three separate bets, not one. The ordering is what matters: if only one of the three
lands, it should be the LLM.

### Tier 2 — IF YOU'RE AHEAD. Week 8 slack, or post-deadline.

`piper` TTS for reading specs aloud · OBD-II integration · VIN scan · photo job log ·
the drive/affect personality system

*(Vision-model table extraction moved **up** — it's laptop-side ingest work with no
hardware dependency, so it can start from week 2. See `LLM.md`.)*

---

## Part 2: What else this hardware can do

Everything below needs **no new robot hardware**. You already have: a Pi 5, an
autofocus camera with a coaxial LED ring on a 3-axis neck, a 7in screen, tracks with
encoders, a very good IMU, ToF sensors, a mic, a speaker, magnets, Bluetooth, and
a phone UI.

### The six best ones, ranked by value ÷ effort

**1. Inspection magnifier — the best free feature in the project**

Head camera + LED ring + belly screen = a live magnified, lit view. Module 3
autofocuses close. Read tiny part numbers, casting marks, date stamps, corroded
stampings, VIN plates. Squinting at a part number in a dark engine bay is a *daily*
mechanic problem, and this is essentially "show the camera on the screen with a zoom
slider." **A day of work. Possibly the thing you use most.**

**2. OBD-II — best value per dollar in the entire project**

A **$15 ELM327 Bluetooth dongle** plugs into the car's port and talks to the Pi's
built-in Bluetooth. `python-OBD` does the rest. That gets you:

- **Read trouble codes** — and then **look the code up in your manual library and
  show the diagnostic page.** This chains your two systems together and is exactly
  what a mechanic actually wants.
- Live data on the belly while it idles: coolant temp, RPM, fuel trims, O2 sensors.
- Freeze-frame capture, and clearing codes.

*Caveat:* OBD-II is 1996+ vehicles only. If you're mostly in older iron, this does
nothing for you — which is worth knowing before you buy the dongle. Also, cheap
ELM327 clones vary a lot in quality; get a reputable one.

**3. Digital angle gauge / level — replaces a real $60 tool, for free**

The BNO085's static tilt accuracy is genuinely good (well under a degree once
calibrated — it's *yaw* that drifts, not tilt). Set the robot on a surface and read
the angle on the belly. Driveline and pinion angles, checking a lift is level, ride
height corner-to-corner, setting a bench. Perfect use of a sensor you're buying for
personality reasons anyway.

**4. On-screen 1:1 reference tools — trivial, used constantly**

The screen has a known pixel pitch, so you can draw things at **exact physical
scale**: a thread pitch gauge, a bolt-diameter chart, socket size comparison,
a ruler. Hold the bolt against the glass. Plus unit conversion (ft-lb ↔ Nm,
in ↔ mm, AF ↔ metric socket equivalents), which you need ten times a day.
**Hours of work, not days.**

**5. Remote eyes — the robot goes where your head can't**

The web UI already runs on your phone at `torq.local`. So: drive TorQ under the car
or behind the engine, and **watch the camera on your phone** while steering the head.
An inspection camera on tracks. This costs *nothing* — it's the teleop and camera
you already built, pointed at a different use.

**6. VIN scan → auto-filtered manuals**

Read the VIN (barcode on the door jamb, or OCR the plate), decode it with NHTSA's
free public API, and now every spec lookup is **pre-filtered to that exact vehicle**.
Removes the most annoying part of searching and makes wrong-vehicle answers much less
likely — which matters given the whole liability concern around specs.

### Also possible, lower priority

| Idea | Notes |
|---|---|
| Part number OCR → search | Point at a casting number, it reads and looks it up |
| Voice notes | "Note: need a new gasket." Transcribe later. Needs mic only |
| Autonomous floor sweep | "TorQ, sweep" — patterns across the floor with the magnet sled |
| Engine sound capture | Record a knock or squeal to compare, or send to someone |
| Per-vehicle maintenance log | What you did, when, at what mileage |
| Timelapse of a job | Camera already there |
| Wiring diagrams / exploded views | Free once the manual library exists — same pages, different query |
| Fluid capacities, fill specs | Same |
| Torque sequence diagrams + bolt counter | Shows the pattern *and* counts your bolts |

---

## Part 3: One ordering decision to make in week 1

**Buy the touchscreen version of the belly panel.**

It's roughly **+$15** and it's the difference between a display and an interface.
Not buying it is irreversible without replacing the panel and probably re-cutting the
bezel; buying it and never using it costs $15 and nothing else.

The counter-argument is real — greasy fingers smear glass, and you'll often use voice
or your phone instead. But thin nitrile works fine on capacitive panels, a knuckle
works, and even as a *backup* input for the days voice fails, it's worth it. This is
the buy-the-cheap-option-early rule, and it expires the day you place the order.

---

## Why the tiering makes the deadline safe

The floor is **built from the bottom up**, and each layer is useful on its own:

```
tracks + head       -> a charming object that drives          (week 7)
+ screen            -> a shop display on wheels               (week 9)
+ manual search     -> THE PRODUCT. Acceptable landing.       (week 9)
+ camera magnifier  -> the thing you reach for daily          (week 9)
- - - - - - - - - - - - - freeze line - - - - - - - - - - - - -
+ voice             -> hands-free                             (week 10, droppable)
+ YouTube           -> how-tos                                (week 10, droppable)
+ OBD-II            -> codes to manual page                   (stretch)
```

Nothing above the freeze line is load-bearing for anything below it. You can lose all
of Tier 1 and still have a robot worth owning — which is exactly the property you
want three months out.

# TorQ — The Mechanic's Assistant

**Pivot, 2026-09-07.** TorQ is no longer a generic pet robot. It's a shop assistant
that happens to have a personality. The name was right all along: **TorQ = torque specs.**

---

## The form (confirmed)

- **Tracks as feet** — confirmed, unchanged. Wall-E silhouette, solved locomotion.
- **Head with camera** — 3 DOF (pan, neck tilt, head tilt). It films, it looks at you,
  it looks at what you're working on.
- **Belly on a hinge, like Wall-E** — but the belly is a **screen**, and the hinge
  tilts it to your eyeline.

---

## Decision: screen, not scoop. Kill the pickup idea entirely.

You floated both. They compete for the same real estate, and for this product the
screen wins overwhelmingly.

**Why the scoop dies:**
- Scooping works on socks and marbles. In a garage the things you want moved are
  heavy, greasy, and irregular. A tracked robot with a ~150g payload is not moving
  your parts, and pretending otherwise wastes weeks.
- It costs motors, alignment problems, and failure modes — on a 12-week clock.
- It competes with the screen for the entire front of the robot.

**Why the hinge survives anyway, with a *better* reason than it had before:**

A robot sitting on the garage floor needs to angle its display steeply up at you.
A robot on the bench needs it near vertical. A fixed screen is unreadable half the
time. So the hinge earns its motor as an **ergonomic** feature, not a storage one —
and it preserves the Wall-E belly-opening silhouette you wanted.

Bonus: the screen tilting up to face you when you speak is the single most *alive*
moment in the whole design, and it's also the robot's primary interface. That's a
rare case where charm and function are the same motor.

**What you lose:** physical interaction, which is where a lot of pet charm lived.
**Mitigation:** the head, the light, and the arms carry the charm now. And a
**magnetic parts tray on the top deck** gives you the "holds things" feeling for
$0 and zero motors — while solving a mechanic's actual #1 annoyance, which is
losing fasteners. You drop bolts in from standing height without bending down or
aiming. Do this.

---

## The arms

You said stationary or simple. Agreed — and here's where I'd land.

### The options

| | What it is | Servos | Verdict |
|---|---|---|---|
| A | Fully static, printed solid | 0 | Cheapest, but reads as *machine*, not creature |
| B | Static shell, **friction ball joints** you pose by hand | 0 | Good. Free "hold this" posture |
| C | **1 powered DOF (shoulder pitch) + friction joint below** | 2 | **Recommended** |
| D | 2 powered DOF per arm (the old plan) | 4 | Not worth it without a gripper |

### Recommendation: option C

**One powered joint per arm — shoulder pitch — with a hand-posable friction joint
below it.**

The reasoning is a single observation: **static arms make a robot read as a machine;
one moving joint makes it read as alive.** That gap is enormous and it costs about
$24 and roughly zero software, because a 1-DOF arm is just keyframe playback — no
kinematics, nothing to solve. Shoulder pitch alone gets you waving, pointing at the
screen, both arms up in celebration, and a slow droop when it's idle or "sad."

The friction joint below it means you can physically pose the forearm to hold or
prop something, permanently, with no motor holding load.

### Give each arm a job

- **Right arm: a COB LED work light.** After tools, light is a mechanic's #1 physical
  need. The 1 DOF pitch aims it up or down; the robot rotating its body aims it
  left/right. This also creates a nice division of labor — **the head films, the arm
  lights** — so you're not asking one part to do two jobs at once.
- **Left hand: a magnet.** Hold a socket, stick a bolt to it. Costs a dollar.

Two conductors run down the right arm for the LED. That's the only added wiring.

---

## What it actually does

### 1. Hands-free video — the core feature

You're under a car with greasy hands following a procedure. Pausing means a greasy
phone. TorQ plays the video on its belly and takes voice commands: *pause, back
thirty, slower, full screen, next step.*

> **This makes voice v1-critical, not a v2 nicety.** It is the entire point.

The good news: this is **command voice, not conversational voice.** A wake word plus
~15 fixed phrases is a solved, offline, days-of-work problem (openWakeWord + Vosk
with a constrained grammar). Conversational LLM voice is the hard thing, and you
don't need it. Don't confuse the two.

**Garage caveat:** shops are loud — compressors, radios, impact wrenches. Speech
recognition will fail sometimes. So: put a **big rubber push-to-talk button on the
top deck** you can hit with a knuckle or an elbow. Always-available fallback, and
honestly it may become the primary input. Cheap insurance.

**Playback implementation note:** don't embed YouTube in a browser — it's finicky on
a Pi and fails offline. Use **`yt-dlp` + `mpv`**: far more reliable, hardware-decoded,
and it caches, so the video still works when the shop WiFi drops. Search via yt-dlp.

### 2. Filming your disassembly — the sleeper killer feature

Taking something apart and not remembering how it goes back together is *the*
universal mechanic pain. TorQ films continuously while you work. You say
*"TorQ, mark that"* and it bookmarks the moment. Reassembly time, the belly shows
your bookmarks **in reverse order** with thumbnails.

Even simpler and nearly as good: **"TorQ, photo."** Snap, timestamp, append to a job
log. Reverse-order gallery for reassembly. No ML, no video scrubbing, trivially
reliable — build this first and add video on top.

### 3. Torque specs

Look up "2015 Civic lug nut torque" and put it on the belly, big.

**Be careful here, and design for it:** a wrong torque spec means a damaged head or a
wheel coming off. There is no free reliable spec API — it's a web lookup. So the rule
is: **never display a spec without its source on screen**, and frame it as *found*,
not *known*. This is the least reliable feature in the product and the UI should say
so. Also keep a local user-editable table for the specs you look up often, which is
both faster and more trustworthy than a live query.

### 4. Timers and counters

Torque sequences (*bolt 3 of 10, criss-cross*), cure times, brake bleed cycles,
oil drain. Trivial to build, genuinely useful, and it makes the screen earn its
place even with no internet.

### 5. It repositions itself

The tracks finally have a job: come when called, turn to face you, back up so you can
see the screen from under the car. This is where the pet behaviors become *useful*
behaviors, which is the best possible outcome for the affect system.

---

## Architecture consequence: the screen is a local web app

Run the belly as a **fullscreen browser pointed at localhost.** Every "app" — player,
timer, job log, spec lookup — is a web page.

Two big wins for a 12-week clock:
1. Fast to build and iterate, and you already know how to do it.
2. **The same UI is your phone UI** at `torq.local`. One codebase, two surfaces. Type
   the awkward stuff (a search query, a vehicle) on your phone; watch it on the belly.

---

## Revised joint count: 6 servos

| Joint | Count |
|---|---|
| Head pan, neck tilt, head tilt | 3 |
| Belly screen hinge | 1 |
| Shoulder pitch x2 | 2 |
| **Total** | **6** |

Down from 9 in the original plan and 8 after the mouth-gripper idea. **Deleted:**
the jaw, the fin-ray grippers, the shoulder roll, the elbows. Every one of those was
a motor, a bracket, a wire, and a tuning session.

That reclaimed time is what pays for the screen and the voice work — which is why
this pivot is roughly **scope-neutral, not scope-creep**, despite adding features.

### Mechanical cautions from the screen

1. **Tipping.** A ~7in screen with its frame is 300–400g, mounted high and forward,
   on a hinge. That is the worst possible place for mass on a tracked robot.
   **Battery goes low and rearward**, and consider a slightly longer/deeper track
   base than the original sketch. Check that it can't tip when the screen tilts fully
   forward.
2. **Hinge load.** Don't let a servo hold that weight continuously — it heats and
   draws current all day. Add a **spring counterbalance** sized so the panel is near
   neutral, so the servo only has to nudge it. Use a strong STS3215-class servo here.
3. **Power and runtime.** Screen plus video decode plus WiFi is real draw. Runtime
   drops to maybe 1–1.5h. **This is fine** — it's a shop tool that lives near an
   outlet. Relax the battery target, make the dock good, and let it run plugged in.
   That's a genuine constraint relief, not a compromise.

---

## Budget delta

| Change | ~$ |
|---|---|
| **Remove** jaw servo, 2 arm servos, gripper hardware | −40 |
| **Add** 7in DSI screen | +45 |
| **Add** belly hinge servo (STS3215) + counterbalance spring | +20 |
| **Add** COB LED + driver + wiring | +8 |
| **Add** mic (2-mic) + push-to-talk button | +12 |
| **Add** better speaker for a loud room | +5 |
| **Net** | **≈ +$50 → ~$445** |

Slightly over the $400 target. Honest trims if you want it back under: a 5in screen
instead of 7in (−$20), and skip the 4-mic array entirely in favor of the
push-to-talk button (already assumed above — in a loud garage, direction-of-arrival
is unreliable anyway and PTT is more robust). Add the mic array in v2 if you miss
"it turns toward your voice."

---

## What the personality is for now

Don't drop the affect system — but point it at the job. The drives still decay and
compete, except now:

- It notices you've been on the same bolt for ten minutes and offers the spec.
- It looks where your hands are, with the light on.
- It gets bored and idles with Perlin head motion when the job's done.
- It reacts when you pick it up or move it.

**A useful thing with a personality is a stronger product than either alone.** The
screen carries the utility; the head, the light, and the arms carry the charm.

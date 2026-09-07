# Request to Change Project Scope

**Project:** TorQ (formerly: autonomous composting trash robot)
**Date:** 2026-09-07
**Timeline:** unchanged — 12 weeks, delivery at end of term
**Budget:** unchanged — ~$500

---

## The request

I'm requesting approval to change my project's **application** while keeping its
platform, timeline, and budget.

**From:** a mobile robot that collects waste and composts it onboard.
**To:** a mobile robot that answers automotive service questions by retrieving and
displaying the correct page of a service manual.

The chassis, drive system, compute architecture, power design, sensors, and the
articulated head are **unchanged**. What changes is what the robot carries and what
it does with it. I'm asking to swap a payload, not to restart a project.

I'm making this request now, in week zero, because the two blocking problems below
are structural — they don't get better with more effort, and finding them in week
eight would cost me the term.

---

## Why the original concept doesn't close

Four constraints. The first two are physical and scheduling facts rather than
matters of judgment, and either one alone is disqualifying.

### 1. Composting has a minimum mass a mobile robot cannot carry

Thermophilic composting — the kind that actually breaks material down on a useful
timescale — requires the pile to hold 55–65 °C. That heat is **metabolic**, produced
by the microbes themselves, and retaining it requires the pile to insulate itself.
The standard minimum for a self-sustaining hot pile is about **one cubic yard**,
roughly 250 kg of material.

A robot-scale vessel of a few liters has far too much surface area for its volume to
hold metabolic heat. It sits at ambient temperature and does not compost.

The alternative is to supply the heat electrically. The robot's battery is about
**25 Wh**. Holding even a small insulated vessel above ambient would consume that in
under an hour, and composting runs for weeks.

**Composting wants to be stationary, massive, and insulated. A robot needs to be
light and moving. These requirements are directly opposed** — the platform is close
to the worst available choice for the process.

### 2. The validation cycle is longer than the project

A hot compost cycle takes **4–8 weeks** under active management. The project is
**12 weeks**, of which the first several go to fabrication and bring-up.

That yields **at most one** observation of whether the system works, arriving at or
after the deadline. There is no measure → adjust → measure loop. I would be
submitting an untested machine and calling the result whatever it happened to be.

### 3. Collection depends on grasping, which is the highest-risk task in hobby robotics

Picking up waste means grasping objects of unknown, irregular geometry. That requires
a multi-DOF arm, inverse kinematics, grasp planning, and closed-loop visual servoing —
because tracked drive slips, so dead reckoning cannot reach grasping tolerance.

Two things make this worse than a normal hard task:

- **It is a single point of failure.** If grasping doesn't work, the robot has no
  function at all. There is no partial credit.
- **The physics don't close at this scale.** Realistic payload for servos in this
  budget is **50–150 g**. A drink can, a bottle, a food container all exceed that.
  Even a fully working gripper would handle a subset of household waste small enough
  that the robot isn't useful.

### 4. I cannot evaluate my own decisions in this domain

My background is automotive and mechanical work, not waste biology. Setting
requirements for carbon-to-nitrogen ratio, moisture, and aeration would be guesswork,
so I couldn't tell a good design decision from a bad one — and I'm not the user, so
I'd have no ground truth to correct me.

### The compounding problem

Individually these are hard. Together they mean **partial completion has no value.**
A composter that never completes a cycle isn't a partial composter — it's a bin.
Nothing degrades gracefully, which is the property a fixed deadline most requires.

---

## What I'm proposing instead

**TorQ: a tracked robot that stores a library of automotive service manuals and puts
the right page in front of you.**

You ask for a torque spec; it finds the page in your manuals and displays it on a
hinged screen in its body, tilted up to your eyeline. It also works as a lit
inspection magnifier for reading part numbers, collects dropped fasteners with a
magnet, and runs timers for torque sequences and cure times.

The governing rule: **it never shows a value without showing its source.** A wrong
torque figure damages an engine or loses a wheel, so the system's job is not to
*know* the answer — it is to *find the page* and display it for the user to verify.

### It inverts every constraint above

| Constraint | Composting robot | TorQ |
|---|---|---|
| Core difficulty | Manipulating the physical world | Retrieving information |
| Domain knowledge | Requires research in a new field | Already held |
| Validation cycle | 4–8 weeks | ~1 second |
| Failure mode | No function at all | Still displays the manual page |
| Payload physics | Doesn't close at this scale | No payload required |
| Evaluator | Not the user | Is the user |

The decisive one is the fourth. TorQ **degrades gracefully at every level**: if the
language model is unavailable it falls back to a local database; if that misses it
shows the retrieved page image; if retrieval fails it's still a mobile display you
can drive. There is no single point of failure.

---

## What carries over

This is why I'm requesting a change of application rather than a new project.

**Unchanged (~70% of the build):**
tracked drive base and chassis · closed-loop velocity control from motor encoders ·
split-brain compute (Linux for high-level work, a microcontroller holding the
real-time loop) · dual-rail power design and brownout mitigation · IMU · time-of-flight
cliff and obstacle sensing · camera · articulated head · parametric CAD approach ·
idle-motion and expression work

**Removed (all risk reduction):**
arm · gripper · inverse kinematics · grasp planning · onboard bioreactor · heating ·
moisture and temperature control for compost

**Added:**
hinged display · document retrieval over ingested PDFs · offline-first data
architecture · grounded citation of sources

Moving joints drop from nine to four. Every deleted joint is a bracket, a wire, a
tuning session, and a failure mode I no longer have to spend the term on.

---

## On whether this is less ambitious

I want to address this directly, because it's the fair question to ask.

**The robotics content is unchanged.** Drive control, closed-loop velocity from
encoder feedback, sensor fusion, the real-time/Linux split, cliff and obstacle
safety behaviour, and a three-axis articulated head are all still in scope — they
were never the part at risk.

What I removed was the part that was **unachievable at this scale and timeline**, not
the part that was instructive. Grasping arbitrary objects with a 100 g payload budget
would not have taught me manipulation; it would have taught me that it doesn't fit.

What I added is real systems work: an ingestion pipeline over scanned documents, a
retrieval system that must run offline, and an architecture whose central design
constraint is that **a wrong answer must be impossible to present as a confident
one.** Designing for verifiable correctness in a safety-relevant context is a harder
and more transferable problem than the one it replaced.

---

## Evidence this is ready to start

- **12-week schedule** with a defined slack week and a **feature freeze at week 10**,
  leaving the final two weeks for reliability rather than new work.
- **A defined minimum acceptable deliverable at week 9** — three weeks before the
  deadline — that ships with no voice control, no video, and no language model, and
  is still a functioning tool.
- **A complete parts list at ~$495**, including a spares kit, ordered in week 1
  because component lead times are 2–4 weeks.
- **The highest-risk software task is scheduled for week 2**, before any hardware
  work, because it needs none and because failing early leaves ten weeks to recover.
- **A pre-planned cut order**, so scope decisions under schedule pressure are made
  now rather than in the final weeks.

The single new technical risk is extracting torque tables from scanned PDF pages,
where text extraction handles table layout poorly. It is mitigated structurally:
displaying the page image to the user routes around the problem entirely rather than
requiring it to be solved.

---

## Request

I'm asking for approval to proceed with TorQ, on the original timeline and budget,
retaining the existing chassis, drive, power, and compute design.

I would rather change the application in week zero on the strength of two structural
constraints than discover them in week eight and have nothing to submit.

Supporting documents: `STORY.md` (concept), `PLAN.md` (12-week schedule and cut
order), `BOM.md` (parts), `CAPABILITIES.md` (deliverable tiers), `LLM.md` (retrieval
and citation architecture).

# TorQ — 12-Week Plan to a Finished Robot

**Hard deadline: 3 months. The goal is FINISHED, not maximal.**
A robot that does four things reliably beats one that does nine things badly and
sits half-assembled on the deadline. Everything below is organized around that.

---

> **PIVOT (2026-09-07, later): TorQ is a mechanic's shop assistant.** The belly is a
> hinged **screen**, there are **no arms and no gripper** (the mouth-gripper section
> below is superseded), and the product is **searchable service manuals with the page
> shown**. **4 servos total.** Read `CONCEPT.md` first. The DOF explainer, the
> irreversibility guide, the ordering advice, the do-not-do list, and the week-10
> freeze below all still stand.

---

## The one-paragraph version

Order every part in week 1 (shipping is your biggest hidden risk). Build the head
first, on the bench, so the robot feels alive by week 4 while you still have energy.
Fight the power/brownout battle in the middle, where there's slack. Freeze features
at week 10 — no exceptions — and spend the last two weeks making what exists reliable.

---

## Degrees of freedom, plainly

A **degree of freedom (DOF)** is one independent way something can move. Roughly:
**one DOF = one motor.**

- Your elbow: 1 DOF (bend).
- Your shoulder: 3 DOF (raise/lower, in/out, rotate).
- A door: 1 DOF. A door on a sliding track: 2 DOF.

### The rule that actually matters

**DOF used for expression is cheap. DOF used to reach a point in space is expensive.**

| Job | What the software has to do | Cost |
|---|---|---|
| Wave an arm | Play back a list of angles you recorded | Hours |
| Cock the head when curious | Play back angles | Hours |
| Reach out and grab that specific cup | Solve *inverse kinematics*: work backwards from "gripper goes HERE" to "each joint goes to angle X" — then correct continuously with the camera because the base slipped | Weeks |

Inverse kinematics is where hobby robot projects die. Not the wiring, not the CAD.
Every DOF you add to a **reaching** chain multiplies that difficulty. Every DOF you
add to an **expression** chain just adds one more number in a keyframe.

**So: be generous with expressive DOF. Be ruthless with reaching DOF.**

---

## Why hardware doesn't go backward

Software you got wrong: rewrite it, reload, the robot is physically unchanged.
Cost: an afternoon.

Hardware you got wrong: re-CAD the part, re-print (4–14 hours), disassemble the
things already bolted and tuned around it, re-wire, possibly re-check the power
budget, reassemble, re-tune. Cost: **one to two weeks.** On a 12-week clock, two
teardowns is 25% of your project.

### Concrete example

Say at week 9 you decide the head must tilt further down to reach the floor.

- **If you planned for it:** the neck servo already has the range and the bracket
  already has clearance. Change one number, reprint one small bracket. **1 day.**
- **If you didn't:** the neck bracket, head shell, servo choice, and wire routing
  all change. The bigger servo doesn't fit the bracket, which is glued into the
  shell you printed in one piece. **1–2 weeks.**

Same decision. 10x different cost. The difference was made in week 3.

### The principle: buy the cheap options early

When something is cheap to add now and expensive to add later, **add it now**,
even if you don't need it yet:

- [ ] Extra range of motion in every joint (costs nothing — just don't design it out)
- [ ] Servos one size stronger than the calculation says (costs ~$5 each)
- [ ] Spare mounting holes / a mounting grid on flat surfaces (costs nothing)
- [ ] **Connectors, not solder joints** — every soldered wire is one you must
      desolder to change anything. JST connectors everywhere.
- [ ] Wire slack and service loops — a taut wire means you can't open the robot
      to work on it without unplugging things
- [ ] **Head removable as one unit** (a connector at the neck, not wires through it)
- [ ] Print the body as **modules bolted to a frame**, never one giant part.
      One broken thing = reprint one small part, not 14 hours.

This is NOT "add everything." Extra hardware costs weight, current, wiring, and
things that break. Add options only where you have a concrete idea you might use them.

---

## ~~The mouth is the gripper~~ — SUPERSEDED, see `CONCEPT.md`

*The mouth gripper is dead along with all manipulation. Kept below because the
reasoning — that reaching DOF is what costs weeks — is exactly why the current
design has no gripper at all. The eye-in-hand argument now applies to the head
camera filming your work.*

### Original reasoning

Your MicroDuck observation is correct and it's the highest-value change available.

**Pick things up with the mouth, not the arms.** Reasons, in order of importance:

1. **It deletes the hardest software problem.** No arm IK. "Grab it" becomes:
   center the object in the camera, drive forward, tilt head down, close jaw.
   That is the *same control loop as looking at something*, which you're building
   anyway. Days of work, not weeks.
2. **The camera is in the head, right next to the mouth.** This is called
   *eye-in-hand*, and it's the easiest possible arrangement for grabbing things
   you can see. With arms, the eye and the hand are on different limbs and you
   have to calibrate the relationship between them — a genuinely annoying,
   multi-day problem that simply vanishes here.
3. **One motor.** A jaw is 1 DOF.
4. **It's more pet-like, not less.** A dog brings you things in its mouth. This
   *strengthens* the concept instead of compromising it.

Wall-E-ness is preserved: his arms are ~90% expressive anyway, and his torso
opens like a mouth. A hinged lower jaw on the head reads as both.

### Consequence: go symmetric on the arms

The only reason for the asymmetric 4-DOF right arm was future manipulation.
If the mouth manipulates, that reason is gone.

| | Old plan | New plan |
|---|---|---|
| Right arm | 4 DOF (shoulder pitch, roll, elbow, gripper) | 2 DOF (shoulder pitch, elbow) |
| Left arm | 2 DOF | 2 DOF |
| Head | 3 DOF | 3 DOF (pan, neck tilt, head tilt) |
| Jaw | — | 1 DOF |
| **Total** | **9 servos** | **8 servos** |

Shoulder pitch + elbow already gives you: waving, pointing, reaching up, covering
the eyes, drooping when sad. That is a full expressive vocabulary.

### Two cautions on the mouth

- **Head mass is now the enemy.** The head carries 2 round LCDs, the camera, and
  a jaw. An object in the mouth sits at the end of the neck — a lever arm — so the
  neck tilt servo carries `weight x distance`. **Use the strong STS3215-class
  servos for neck tilt and head pan.** Keep the battery low in the base or a
  tracked robot with a heavy head will tip forward when it leans down.
- **Set payload expectations now:** a sock, a small toy, a marker, a ball.
  Roughly 50–150g. Not a mug, not anything with liquid in it.
- Print TPU pads on the jaw faces. Compliance means it grips without needing
  precise force control.

---

## The 12-week schedule

| Week | Work | Done when |
|---|---|---|
| **1** | **ORDER EVERYTHING** (see below). Start CAD in build123d. | Parts are paid for. Nothing else matters in week 1. |
| **2** | **Manual ingest + search, entirely on your laptop.** PDF -> page PNGs -> OCR -> embeddings -> sqlite -> query. Plus the web app skeleton. | **You can type "2015 Civic lug torque" and get the right manual page.** No robot required. |
| **3** | Parts arrive. Bench rig: Pi + Pico + one servo + one eye on a wall supply. Prove the USB protocol and servo bus. | You can command a servo angle from Python on the Pi. |
| **4** | Head assembled on the bench: 3 DOF, eyes, LED ring, Perlin idle motion, blinking. | **The head feels alive on your desk.** Motivational checkpoint. |
| **5** | Power. Battery, dual buck rails, bulk caps. Motors + drivers on the bench. | Servos slam to position and the Pi does not reboot. |
| **6** | Drivetrain: tracks, closed-loop velocity, cliff sensors, web joystick. Magnet sled + parts tray. | It drives straight, stops at a table edge, and picks up a dropped screw. |
| **7** | Chassis integration — head on base, wiring, battery in, untethered. | It drives around the shop with a living head. |
| **8** | **SLACK WEEK.** Something will have gone wrong by now. | Back on schedule. |
| **9** | **Belly: screen, hinge, counterbalance.** Port the week-2 search onto the real panel. | You ask it for a spec and read the manual page off its belly. |
| **10** | Video playback (`yt-dlp` + `mpv`), timers/counters, voice commands + push-to-talk. **FEATURE FREEZE at the end of this week.** | It plays a how-to and you control it without touching it. |
| **11** | Reliability only. Every crash, loose connector, overheating servo. Battery life measured. Cable management. | It runs a full job unattended without intervention. |
| **12** | Polish, shell cosmetics, README, demo video. | Done. |

### Why the main feature is in week 2

Manual search needs **no robot hardware at all** — it's a laptop program. So it goes
as early as possible, for two reasons:

1. **It's the riskiest software in the project.** Torque specs live in tables, and
   text extraction mangles tables. Finding that out in week 2 leaves ten weeks to
   solve it. Finding out in week 9 ends the project.
2. It's the whole product. If it doesn't work, you want to know before you've spent
   $450 and printed a chassis around it.

Everything in weeks 3–8 is a *body for the thing you already built in week 2.*

### The affect system still moves to v2 — take the trade

Dropping the arms bought back real time, and it went straight into the manual
library rather than into slack. The **drive/affect system** stays in v2.

What survives in v1 is the cheap 80%: **Perlin idle motion, blinking, and look-at**
(week 4 and week 7). That is most of what makes it feel alive. What moves out is
**behavior arbitration** — competing drives, acting unprompted. That's charm, and
charm is exactly what you defer when the product has a job and a deadline.

**Do not** try to keep it by deleting week 8.

### If you fall behind, cut in this exact order

Decide the sacrifice order **now**, while you're calm, not in week 11 while you're
not. Cut from the top:

1. **Video playback** -> local files only, no YouTube search. `mpv` on a file is
   trivial; search, download and caching is the fiddly part.
2. **The LLM summary line** -> pure retrieval. Show the manual page with no
   plain-English answer over it. Slightly less magic, still the whole point, and it
   removes the network dependency entirely.
3. **Motorized belly hinge** -> friction hinge you set by hand. Design the boss to
   accept the servo later. (The buy-the-option rule doing its job.)
4. **Voice input** -> push-to-talk button plus on-screen buttons only.
5. **Photo job log** -> already a stretch; drop it without ceremony.

Note what is *not* on this list: the manual search itself, and the screen. Those are
the product. Everything above exists to be sacrificed for them.

### If you're AHEAD, add in this order

Week 8 slack survives more often than people expect. Spend it on these, not on
something new:

1. **`piper` TTS for reading specs aloud** (~2 days) — genuinely useful when you're
   under a car and can't see the belly. It must speak the number *and* the source.
2. **Photo-per-step job log** — reverse-order reassembly gallery.
3. **Vision-model table extraction at ingest** — turns manual pages into structured
   torque rows. Big upgrade, entirely optional.
4. **Drive/affect system** — the personality layer from `BRAINSTORM.md`.

---

## Order in week 1 — including spares

Shipping is the risk nobody budgets for. Overseas servos are commonly 2–4 weeks.
On a 12-week clock that's a quarter of your project spent waiting.

**Order everything at once, in week 1, before the CAD is finished.** You know the
part list; the CAD adapts to the parts, not the other way around.

**Buy spares.** You *will* strip a servo horn, burn a motor driver, and kill a buck
converter. If the replacement is 3 weeks out, you lose 3 weeks.

| Spare | ~$ | Why |
|---|---|---|
| 2x spare servos (1 large, 1 small) | 30 | Stripped gears are routine |
| 2x spare motor driver | 10 | Easiest thing to blow up |
| 2x spare buck converter | 12 | Second easiest |
| Spare Pico 2 | 5 | Trivial insurance |
| **Total** | **~$57** | Best money in the build |

Also verify before ordering: stay **within the STS servo protocol family** across
all 8 servos. Do not mix in SCS-series parts. Debugging a servo bus while also
debugging everything else is a bad week.

---

## Do NOT do these things

1. **Do not build legs.** You noticed MicroDuck's feet have many motors — that is
   the part *not* to copy. Bipedal walking is a research problem that eats entire
   projects. Tracks are solved. This single choice is most of the difference
   between finishing and not finishing.
2. **Do not do SLAM or mapping.** Reactive obstacle avoidance is enough for a pet.
3. **Do not put voice/LLM in the 3-month scope.** It's a pure software bolt-on that
   touches no mechanics. It's the perfect v2 and a terrible v1.
4. **Do not do arm inverse kinematics.** The mouth exists now.
5. **Do not use PWM hobby servos to save money.** You lose backdrive teaching and
   petting detection — two of your best features — and they buzz, which kills the
   pet illusion.
6. **Do not print the body as one part.** Modules on a frame.
7. **Do not skip the week-3 bench rig.** Every Pi robot that mysteriously reboots
   is losing the power fight, and it's miserable to debug through a closed chassis.
8. **Do not put the battery high in the body.** Low and centered, or it tips.
9. **Do not add "one more feature" in week 11.**

---

## What "great MVP with room to grow" looks like here

The room to grow is bought with **hardware options and software architecture**,
not with unfinished features:

- The servo bus has spare IDs and the power rail has headroom -> add joints later.
- The Pi has the PCIe connector free -> add the Hailo AI HAT for vision in v2.
- The behavior system loads from a `skills/` folder -> add abilities without
  touching the core.
- The CAD is parametric from a config file -> change proportions without redrawing.
- Connectors everywhere -> the robot can be opened and changed in v2 without a rebuild.

That is what "room to make it really good" actually means. It is not a half-built arm.

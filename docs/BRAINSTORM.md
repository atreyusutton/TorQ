# TorQ — Design Brainstorm (recovered)

> Recovered 2026-09-07 from session transcripts `15a34a21` / `350a8c71` (2026-09-07 17:42–17:53).
> Concept: a small customizable personal robot that is more pet than tool — Wall-E-shaped,
> tracks for drive, cute head with camera, little arms. Programmable and trainable.

> **SUPERSEDED IN PART (2026-09-07, later):** the arms section below is out of date.
> The gripper moved to a **jaw in the head** (MicroDuck-style), arms became symmetric
> 2 DOF expression-only, and the servo count dropped 9 -> 8. See `PLAN.md` for the
> current joint list, the reasoning, and the 12-week schedule. Everything else here
> — power, split-brain architecture, affect system, CAD approach — still stands.

---

## Decisions locked (your answers)

| Question | Your answer |
|---|---|
| Budget ceiling for first working TorQ | **~$400 sweet spot** |
| Chassis fabrication | **3D printer, but Claude drives the CAD** |
| Arms: manipulate or emote? | **Leaning "one of each"** (asymmetric) — flagged time-vs-MVP as worth more discussion |
| What v1 proves first | **Motion + expression** |

Resolution reached on the arms question: build the asymmetric hardware now, ship v1 with
**zero manipulation code**. See "The arms" below.

---

## Hardware

**Split brain — the one non-negotiable architectural call.**

| Layer | Part | Job |
|---|---|---|
| Cortex | Raspberry Pi 5 (4/8GB) + Hailo-8L AI HAT (13 TOPS) | vision, voice, personality, LLM |
| Cerebellum | RP2350 (Pico 2) or ESP32-S3 | motor PID, servo bus, IMU, e-stop, battery |

Linux can't hold a real-time loop. The MCU runs a 200Hz control loop and keeps the robot safe
if the Pi reboots or wedges. They talk over USB CDC at ~50Hz with a small binary protocol.
Don't put micro-ROS on the MCU; not worth the weight.

**Drive:** 2x N20 gearmotors (~1:100) with magnetic encoders, driven by DRV8833 or TB6612FNG.
Skip L298N — the voltage drop is brutal at 7.4V. Encoders buy closed-loop velocity, straight-line
driving, and dead reckoning. Tracks: printed sprocket + idler + road wheels, TPU track pads.

**Servos — the highest-leverage choice.** Use **serial bus servos with position feedback**
(Feetech STS3215, or SCS0009 for small joints) instead of PWM hobby servos:
1. One daisy-chained wire for all joints instead of 12 signal lines.
2. Torque control and quieter operation — cheap servo buzz *destroys* the pet illusion.
3. **You can read position while the servo is limp.** That gives petting detection (someone moved
   the head, it reacts) and *teaching by backdriving* — physically pose the arms, it records
   keyframes. That single feature is the best "train it" story.

**Head:** 3 DOF (pan, neck tilt, head tilt). The third axis gives the head-cock — disproportionately
huge for cuteness.

**Eyes:** 2x GC9A01 240x240 circular SPI LCDs behind binocular lenses. ~$8 each, best
emotion-per-dollar part in the build. Camera in the bridge or one eye — Pi Camera Module 3 Wide.

**Arms:** fin-ray compliant fingers printed in TPU — one actuator, grabs irregular objects,
forgiving of bad grasp planning. Realistic payload at this scale: 50–150g. Arms are ~80%
expression, 20% manipulation.

**Senses that make it feel alive:**
- BNO085 IMU -> detects being picked up, tilted, shaken. Enormous personality payoff for $20.
- VL53L5CX ToF (8x8 zones) forward + 2 downward for cliff detection at the track nose.
- ReSpeaker 4-mic array -> direction of arrival. Robot turning toward your voice is genuine magic.
- MAX98357A I2S DAC + 3W speaker for Wall-E vocalizations.
- Motor current sensing -> stall detection -> "I'm stuck" behavior.

**Power — where these projects die.** 2S 18650 pack (4 cells, 2S2P, ~25Wh) -> **separate buck
rails**: 5V/5A for the Pi, 6–7.4V direct for the servo bus, common ground, fat bulk caps on the
servo rail. Servo inrush browning out the Pi is the #1 failure mode in Pi robots. Add INA219 or
MAX17048 for fuel gauge. Charging dock with pogo pins, styled as a solar panel, obviously.

Runtime: ~1.5–2h with Pi 5 + Hailo pulling ~10W.

---

## Software

**Skip ROS 2 for v1.** Nav2/tf2 is a lot of ceremony for a robot that doesn't need SLAM-grade
navigation. Use a plain asyncio service with an internal event bus, and put **Zenoh** on the
outside for tooling — it's what ROS 2 is migrating to anyway, so the escape hatch stays open.

```
reflex loop     10-50ms   MCU + Pi     obstacle, cliff, balance, touch
perception      15-30fps  Hailo        faces, people, objects, gaze target
drive/affect    2-10Hz    Pi           energy, curiosity, social, boredom, comfort
deliberation    1-3s      Claude API   intent, conversation, novel situations
```

**The pet-ness does not come from the LLM.** Most "AI robot pet" projects are a chatbot with
wheels and they feel dead. What makes it a pet is a **drive system**: internal state variables
that decay over time and get satisfied by events — boredom rises when nothing happens, social
need rises when ignored, energy drops as the battery drains. Behaviors score themselves against
current drives, highest score wins, hysteresis so it doesn't dither. That's ethology, and it's
what makes a robot seem to *want* things.

The LLM sits on top at low frequency, gets summarized world state plus memory, and emits
high-level intents through tool calls — `look_at()`, `approach()`, `pick_up()`, `express(emotion)`.
**The reflex layer never blocks on the network. Ever.**

**Idle motion is mandatory.** Perlin noise on head joints, variable blink rate, occasional
saccades and look-arounds, a subtle breathing bob. A robot that freezes when idle reads as
broken, not resting.

**Four mechanisms for "train it better":**
1. **Backdrive teaching** — pose the arms by hand, it records keyframes. Best feature to ship.
2. **Good robot / bad robot** feedback adjusting behavior utility weights. Simple, legible, satisfying.
3. **Few-shot object learning** — show it your keys, CLIP/DINOv2 embedding, now it knows "keys".
4. **Skill plugins** — a `skills/` folder users drop Python into, plus LLM-authored skills sandboxed.

Plus a web UI served off the Pi at `torq.local`: live camera, joystick, personality sliders,
memory browser, skill installer.

---

## The arms: buy the hardware, defer the software  
*(SUPERSEDED — see `PLAN.md`. Kept for the reasoning, which still explains why reaching DOF is expensive.)*

The time cost of arms **isn't the servos or the CAD** — it's inverse kinematics, grasp planning,
and visual servoing. A gripper that reliably picks up a real object is easily 10x the work of an
arm that gestures well. That's the part that eats weeks.

DOF count is a *hardware* decision you can't cheaply reverse; manipulation is a *software*
decision you can defer indefinitely. So:

> **Build the asymmetric arms now. Ship v1 with zero manipulation code.** Both arms run purely
> as expression channels — the right arm's extra joints just give a richer gesture vocabulary.

Cost of buying that option: ~**$35 in extra servos and one evening of CAD**. In exchange,
manipulation later becomes a pure software project on hardware that already exists, instead of
a teardown.

- **Backdrive teaching gives you "manipulation" in v1 with no IK at all.** Physically pose the
  arm, it records joint keyframes, it replays them. A real, demoable pick-up motion without a
  line of kinematics — and it fits the pet framing: it has *taught tricks*, not a motion planner.
- **The real blocker on autonomous grasping isn't the arm, it's the base.** Tracks slip, so
  odometry will be genuinely bad — you cannot dead-reckon to grasping tolerance. Real autonomous
  pick-up needs closed-loop visual servoing off the camera. That's the multi-week item, a v3 concern.

Mechanical note while it's cheap to fix: **double-support the shoulder pitch axis** — servo horn
one side, bearing the other. Single-sided horns sag and develop wobble; a droopy arm reads as broken.

**Final arm layout:** right = shoulder pitch, shoulder roll, elbow, gripper (4).
Left = shoulder pitch, elbow (2). Head = pan, neck tilt, head tilt (3). Nine joints, one serial bus.

---

## BOM at ~$400

v1 is motion + expression, which needs **no AI accelerator and no mic array**. Cutting both puts
$85 back into servos and filament, and neither is on the critical path.

| Part | ~$ |
|---|---|
| Raspberry Pi 5 (2GB fine for v1) | 50 |
| Pi Camera Module 3 Wide | 35 |
| RP2350 Pico 2 (motion MCU) | 5 |
| 2x N20 encoder gearmotors 1:100 | 20 |
| TB6612FNG driver | 5 |
| 2x Feetech STS3215 (shoulder R, head pan) | 36 |
| 7x Feetech STS3032 (light joints) | 84 |
| 2x GC9A01 round LCD eyes | 16 |
| BNO085 IMU | 20 |
| VL53L1X ToF x3 (front + 2 cliff) | 24 |
| MAX98357A + 3W speaker | 10 |
| 4x 18650 + BMS + holder | 30 |
| Buck converters (5V/5A, 6V/5A) + caps | 15 |
| PETG + TPU, bearings, M3 hardware, wire | 45 |
| | **~$395** |

Deferred to v2: Hailo AI HAT (+$70), 4-mic array (+$25).

**BOM revision:** with the mouth-gripper change, servos become 2x STS3215 (neck tilt,
head pan — they carry the head *and* whatever it's holding) + 6x STS3032 (head tilt,
jaw, 2x shoulder, 2x elbow). Roughly $108, and the ~$12 saved plus more should go
straight into the spare-parts kit in `PLAN.md`.

Verify before ordering:
- Stay **within the STS protocol family** across all nine servos (STS3215 and STS3032 share it;
  mixing in SCS-series is documented as possible but don't debug a bus alongside everything else).
- Check physical clearance if you later stack the AI HAT — it takes the PCIe connector but the
  standoffs get crowded.

---

## CAD approach

Drive it in **build123d** — Python, parametric, real B-rep geometry, exports STL for printing
*and* STEP for pulling into Fusion to tweak by hand. Everything dimensioned off a config file:
track length, wheel diameter, servo model, arm segment lengths. Change one number, regenerate
the whole robot. That's what makes "customizable" real rather than aspirational.

---

## Build plan to v1

| # | Milestone | Proves |
|---|---|---|
| 0 | Bench rig — Pi + Pico + 1 motor + 1 servo + 1 eye on the desk | Protocol, power rails, no brownouts |
| 1 | Drivetrain — tracks, closed-loop velocity, web joystick | Drives straight, doesn't fall off tables |
| 2 | Head + eyes — 3 DOF, animated eyes, Perlin idle motion | **It feels alive standing still** |
| 3 | Affect system — drives, behavior arbitration | It does things unprompted |
| 4 | Arms as expression + backdrive teaching | Gestures, taught tricks |

Milestone 0 is unglamorous and where real care belongs. Every Pi robot that mysteriously reboots
is losing that fight, and it's miserable to debug once there's a chassis in the way.

---

## Open next step

Scaffold the repo: `firmware/` (Pico control loop), `torq/` (Python service, event bus, affect
system), `cad/` (build123d parametric body), plus `SPEC.md` and `TODO.md` tracking milestones.
Start with milestone 0 wired end to end, so there's something to flash the day parts arrive.

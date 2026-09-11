# TorQ — Parts List

**v3 — full stock BOM + our swaps. Hands-held 6.25in screen.**
v1 (belly screen, custom body) is archived at `_archive/BOM-v1-belly-screen.md`.

Two parts below. **Part 1** is Simon Bluett's ([chillibasket](https://wired.chillibasket.com/3d-printed-wall-e/))
published parts list, complete and unedited, including the things we don't use —
so you can see exactly what the stock build is before we touch it. **Part 2** is
every change we make to it.

Order **everything in week 1.** Shipping on servos is routinely 2–4 weeks, which is
a quarter of a 12-week project. Printing also starts week 1 — 310 parts is over a
month of machine time and it is not a week-4 activity.

---

# Part 1 — The stock chillibasket BOM, complete

Everything he specifies. The **Us** column is what we do with it.

### Fasteners and linkages
| Qty | Part | ~$ | Us |
|---|---|---|---|
| 14 | M3 bolt, 10mm | — | ✅ Keep |
| 12 | M3 bolt, 20mm | — | ✅ Keep |
| 2 | M3 bolt, 6mm | — | ✅ Keep |
| 26 | M3 nut | — | ✅ Keep |
| 3 | Paper clip (servo linkages) | 0 | ✅ Keep |
| | *M3 assortment, buy a boxed kit — we need more than stock* | 10 | |

### Optical
| Qty | Part | ~$ | Us |
|---|---|---|---|
| 2 | Plano-convex lens, ⌀31.5–32.5mm (the eyes) | 12 | ✅ Keep |

### Servos and motors
| Qty | Part | ~$ | Us |
|---|---|---|---|
| 7 | MG90S high-torque micro servo | 20 | ⚠️ **Keep 5, swap 2** — see below |
| 2 | 12V DC geared motor, 100–150RPM, ⌀37mm, off-centre output shaft | 30 | ✅ Keep |

> His 7 servos are: **2× eye raise/lower** (independent), **1× head rotate**,
> **1× neck up/down**, **1× neck raise/lower**, **2× arm up/down at the shoulder**.
> The **2 shoulder servos are the ones we swap.** Buy all 7 anyway — they're $3 each
> and the two you displace become your spares.

### Control electronics
| Qty | Part | ~$ | Us |
|---|---|---|---|
| 1 | Arduino Uno | 12 | ✅ Keep |
| 1 | Motor Controller Shield (Rev3) | 13 | ✅ Keep |
| 1 | i²c servo controller board (PCA9685) | 10 | ✅ Keep |
| 1 | Raspberry Pi | 35 | 🔄 **Swap** → Pi 5 4GB |
| 1 | 12V → 5V DC buck converter | 6 | 🔄 **Swap** → dual rail, 5A |

### Power
| Qty | Part | ~$ | Us |
|---|---|---|---|
| 1 | 12V DC battery pack (he suggests 2200mAh 11.1V 30C LiPo) | 22 | 🔄 **Swap** → 3S2P 18650 |
| 1 | LiPo battery charger | 25 | 🔄 **Swap** → BMS + charger |
| 5 pr | XT60 battery connectors | 8 | ✅ Keep |

### Optional in his build
| Qty | Part | ~$ | Us |
|---|---|---|---|
| 1 | USB camera | 15 | ✅ **Keep — you already have this** |
| 1 | Small speaker | 5 | 🔄 **Swap** → I²S amp + 5W driver |
| 1 | 1.3in OLED display, i²c | 8 | ✅ **Keep** — it becomes the solar charge indicator |
| — | Resistors, 100kΩ + 47kΩ (battery monitoring divider) | 2 | ❌ **Skip** — superseded by the fuel gauge |

> ### What the OLED is, and why we're keeping it
>
> In his build the 1.3in i²c OLED is a **status readout** — it pairs with those two
> resistors, which form a voltage divider feeding the Arduino's ADC, so the Arduino
> can measure pack voltage and print it. Battery level, basically.
>
> I had this down as *skip* — we have a 6.25in touchscreen, why keep a 1.3in one.
> That was wrong, for three reasons:
>
> 1. **The big screen is in his hands, and it won't always be awake or docked.** A
>    status readout you have to pick the screen up to see isn't a status readout.
> 2. **It survives the Pi.** It hangs off the *Arduino*, not the Pi. If the Pi wedges
>    mid-boot or a card goes bad, the OLED still tells you the robot has power and the
>    motion board is alive. That is the difference between a five-minute diagnosis and
>    an afternoon.
> 3. **His body already has a hole for it.** He deliberately left a recess in the chest
>    for WALL·E's **solar charge indicator** — the little bar that fills up as he
>    charges in the film. Put the OLED there and drive it with real pack percentage
>    from the fuel gauge, and the most screen-accurate detail on the robot is also the
>    most useful one. Free — the cavity is already in the STL.
>
> **Keep it. $8.** Drop the two resistors, though: the MAX17048 fuel gauge does the
> same job properly over i²c, and a divider on an ADC drifts with temperature.

### Stock build total — **≈ $233** plus filament
*(Sanity check: Printed Droid lists this build at $200–300. We're in the right place.)*

---

# Part 2 — Our swaps and additions

### 2a. Swaps — replacing a stock part

| Stock part | Replaced with | Why | ~$ |
|---|---|---|---|
| Raspberry Pi | **Pi 5, 4GB** | Runs Chromium, `mpv` video decode and the local embedding search at once. 2GB is tight | 60 |
| 12V→5V buck ×1 | **12V→5V/5A + 12V→6V/5A + bulk caps** | **Separate rails.** Servo inrush browning out the Pi is the #1 killer of Pi robots | 18 |
| 11.1V LiPo + charger | **3S2P 18650 pack + ≥20A BMS + holder + 12.6V charger** | **67Wh vs his 24Wh** — roughly 3 hours of use instead of 1. Also a protected pack you can leave on a shelf in a garage. See the power budget below | 50 |
| Small speaker | **MAX98357A I²S amp + 5W speaker** | **Buy the good speaker.** Chirps sound fine on a cheap driver; speech does not | 15 |
| 2× MG90S (shoulders) | **2× Feetech STS3215 + FE-URT-1 bus adapter** | The shoulders now carry a screen. See the arm section | 44 |

### 2b. The screen and the path to it

| Part | Why | ~$ |
|---|---|---|
| **Waveshare 6.25in DSI touch, 720×1560** | Your ~14cm target. **159mm diagonal, 144 × 66.5mm active.** Single DSI ribbon — one cable across the shoulder instead of two | 50 |
| **2× DSI FFC ribbon, 22-pin → 15-pin, 300mm** | Pi 5 uses the 22-pin 0.5mm connector; the panel is 15-pin. **Buy two** | 12 |
| Screen carrier hardware — M2.5 standoffs, nylon washers | The printed frame the hands actually grip | 8 |
| Magnetic dock pads, chest | Screen parks flat on his chest when driving. Protects the glass, pulls the CG back over the tracks | 6 |

> ### On "close to 14cm"
>
> I read that as **diagonal**. Here's the honest picture at that size, because it
> shapes the product:
>
> | Panel | Diagonal | Active area | Interface | ~$ |
> |---|---|---|---|---|
> | 5in DSI, 1024×600 | 127mm | 108 × 65mm | 1 ribbon | 40 |
> | **6.25in DSI, 720×1560** ← chosen | **159mm** | **144 × 66.5mm** | **1 ribbon** | **50** |
> | 5.5in AMOLED, 1080×1920 | **140mm — exact** | 68 × 122mm | HDMI **+** USB | 95 |
>
> **Everything in this size class is a phone panel**, so it's tall and narrow (9:16
> or thinner) rather than page-shaped. Mounted **portrait**, the 6.25in gives you a
> 66.5 × 144mm reading column — which is to say, roughly a phone, which is exactly
> how people already read PDFs on their feet. That's fine.
>
> The 5.5in AMOLED hits 14cm exactly and looks better, but it's **HDMI + USB**:
> two cables across a moving shoulder instead of one, and nearly double the price.
> Given the ribbon is already the most failure-prone thing on this robot, I went
> with the single-cable part and overshot your target by 19mm. **Say the word if
> you'd rather have exactly 14cm and I'll swap it back** — it's a one-line change.

> ### ⚠ The ribbon cable is still the weakest part in this list
>
> A DSI flex crossing a moving joint will eventually fail; flex cables are rated for
> a limited number of bend cycles and a shoulder is thousands.
>
> - **Route it through the shoulder pivot axis so it twists rather than bends.** Free, and worth an order of magnitude in cycles.
> - **The spare is in the core list, not the spares list.** A $6 cable that's three weeks out in week 10 is a dead project.
> - **Lower-risk alternative:** mount the Pi 5 *on the screen carrier*, behind the panel (85×56mm — it fits). The DSI run becomes 100mm and never moves; only 5V and one USB cross the shoulder. Costs ~46g in the hands. Decide at assembly.

### 2c. Arms — now load-bearing

The finished screen assembly lands around **250–330g** depending on where the Pi goes.
Stock arms are not built for that: the shoulders are MG90S, and the **elbow and wrist
joints are pressure-fit** — posable by hand, which means they creep under a steady load.

| Part | Why | ~$ |
|---|---|---|
| 2× Feetech STS3215 *(counted in swaps above)* | Shoulder lift. MG90S will buzz, creep and strip under 300g on a lever arm | — |
| 2× 4mm carbon fibre tube + M3 hardware | Runs inside each printed arm. PETG alone creeps under sustained load over weeks | 8 |
| Shoulder bearings (flanged) | Takes radial load off the servo shaft | 8 |
| 2× spring plunger detent | **The arms lock into the raised position mechanically.** The servo lifts; the detent holds. A servo holding 300g static all day is a servo you replace | 8 |
| M3 bolt + nyloc pivots for elbow/wrist | Replaces the pressure-fit joints so you can set friction and it stays set | 4 |

> **Sync the arms or they fight each other.** Two arms holding one rigid screen is a
> closed kinematic loop — if the servos disagree by two degrees they lever against
> each other until something strips. Free fix: **drive one arm, let the other idle
> on a free pivot**, and let the wrist joints self-align.

### 2d. Light

| Part | Why | ~$ |
|---|---|---|
| COB LED ring + driver | Coaxial with the lens, so it lights exactly what the camera films — how borescopes do it | 8 |
| 3W high-CRI LED flood + constant-current driver | **The flashlight.** Aimed with the head, switched from the screen. High-CRI matters: cheap cool-white makes fluid colours unreadable, and telling ATF from coolant by colour is a real diagnostic | 10 |
| 2× MOSFET driver module | Pi GPIO cannot source LED current. Don't skip these | 6 |
| Detachable magnetic COB work light | Docks on the parts tray, comes off in your hand for where the robot can't reach. Zero integration, zero software, and probably the most-used light on the machine | 12 |

> Two fixed lights, two jobs: the ring is for **what the camera sees**, the flood is
> for **what you see**. One switch for both would make both worse.

### 2e. Sensing, audio and input — all additions

| Part | Why | ~$ |
|---|---|---|
| BNO085 IMU | Pick-up/tilt detection **and** the digital angle gauge | 20 |
| 3× VL53L1X ToF | One forward, two down at the track nose for cliff detection | 24 |
| I²S mic (INMP441) | Mount it high in the head, away from motor whine | 8 |
| Rubber push-to-talk button | Hit it with a knuckle. Garages are loud and voice will fail sometimes | 4 |
| MAX17048 fuel gauge | Replaces his resistor divider. So it knows when it's tired | 6 |

### 2f. Storage and body — all additions

| Part | Why | ~$ |
|---|---|---|
| 256GB USB SSD **or** A2 microSD | Manual page images run ~400MB per manual. Not the 32GB card from a starter kit | 25 |
| Neodymium magnets — tray + sweeper strip | Parts tray on top; removable sled underneath that collects dropped screws | 10 |
| Rear counterweight (steel/lead shot) | 300g held out front on tracks wants to nose over on a ramp | 5 |
| JST connectors, wire, misc bearings | **Connectors, not solder joints** — every soldered wire is one you must desolder to change anything | 30 |
| PETG + TPU filament, ~3kg | **310 parts.** This is not the 1kg spool you have. Body PETG, track pads TPU | 60 |

---

# Power budget — do we need a better battery?

**Yes, and it's already in the list — but I had the capacity wrong above, so here's
the arithmetic.**

### What the robot actually draws, at 12V

| Load | Typical | Worst case |
|---|---|---|
| Pi 5 + SSD (Chromium + video decode) | 8W | 25W |
| 6.25in DSI screen | 2.5W | 3W |
| 5× MG90S (head/eyes) | 1.5W | 20W all moving |
| 2× STS3215 (shoulders — detents hold, so they idle) | 0.5W | 36W lifting |
| 2× drive motors (amortised over ~20% driving) | 2W | 70W both stalled |
| Lights (duty-cycled) | 2W | 5W |
| Audio amp | 1W | 5W |
| Arduino + sensors + OLED | 1.5W | 2W |
| **Total** | **≈ 19W** | **≈ 165W (never sustained)** |

### What that means for runtime

| Pack | Capacity | Usable | Runtime at 19W |
|---|---|---|---|
| His 2200mAh 11.1V LiPo | 24Wh | ~19Wh | **≈ 1 hour** |
| **3S2P 18650, 3000mAh cells** | **67Wh** | **~57Wh** | **≈ 3 hours** |

One hour is not a shop session. Three is. **That's the answer: yes, and the 3S2P
pack in §2a is it.**

### The spec that actually bites — and it isn't capacity

Look at the worst-case column. Motors stalling while the servos lift and the Pi is
busy can pull **10–12A** for a second or two. Two things have to survive that:

- **The BMS must be rated ≥20A continuous.** Most cheap 3S BMS boards are 8–10A.
  A 10A board doesn't sag under that peak — it *trips*, cutting all power, which
  hard-reboots the Pi mid-task and can corrupt the card. This is the single most
  common way a build like this fails intermittently and takes a week to diagnose.
- **The cells must be high-drain**, ≥10A each: Samsung 30Q, Molicel P26A, Sony VTC6.
  Recovered laptop-pack 18650s are typically rated ~2A and will sag hard enough to
  brown out the 5V rail.

Cheap insurance on top of both: **the bulk capacitors already in §2a**, sitting right
at the motor driver and the servo rail, to absorb the inrush before it reaches the pack.

> **If you'd rather keep his LiPo:** it works, it's lighter, and it's cheaper. You get
> about an hour, you need a proper balance charger and somewhere fire-safe to store it,
> and there's no BMS protecting it from over-discharge. For a robot that lives in a
> garage and gets picked up mid-task, I'd take the 18650 pack.

---

# Totals

| | ~$ |
|---|---|
| Stock parts we keep (§1) | 123 |
| Swaps (§2a) | 187 |
| Screen + ribbon path (§2b) | 76 |
| Arms (§2c) | 28 |
| Light (§2d) | 36 |
| Sensing, audio, input (§2e) | 62 |
| Storage and body (§2f) | 130 |
| **Core total** | **≈ 642** |

### Spares — buy these too (~$42)

You *will* strip a servo horn and burn a driver. Three weeks of shipping in week 10
loses you the project. Best money in the build.

| Part | ~$ |
|---|---|
| Spare STS3215 (highest-load part on the robot) | 18 |
| 2× spare motor driver | 12 |
| 2× spare buck converter | 12 |
| *2× spare MG90S* | *free — the two the shoulders displaced* |
| *Spare DSI ribbon* | *already in the core list. Not optional* |

### Optional

| Part | Why | ~$ |
|---|---|---|
| Pi Camera Module 3 Wide | **Only if you want the magnifier.** Your USB camera is fixed-focus, and the magnifier needs to focus at 5–10cm | 35 |
| ELM327 Bluetooth OBD-II dongle | Read trouble codes, then show the matching manual page. Best value-per-dollar upgrade available. **1996+ vehicles only** | 15 |
| Hailo-8L AI HAT | On-device vision for v2. The Pi's PCIe slot stays free for it | 70 |

### Running totals

| | ~$ |
|---|---|
| Core | 642 |
| + Spares | 684 |
| + Camera Module 3 (if you want the magnifier) | 719 |
| + OBD-II dongle | 734 |

**The honest drift:** stock is $233. We're at $642 — we have roughly tripled it.
Where it went, in order: the screen and its cable path ($76), the Pi 5 and storage
($85), 3kg of filament ($60), sensing we added that he never had ($62), lighting
($36), and the arms becoming structural ($72 including the servo swap). Every one of
those traces to a decision in `CONCEPT.md`. None of it is padding — but $642 is the
number to take to the group, not $400.

---

# The three things most likely to go wrong

1. **The ribbon cable across the shoulder.** Twist route, buy the spare, or move the Pi onto the screen carrier and stop crossing the joint with display signals at all.
2. **The arms.** The spring detents are what make this survivable — a servo must never be the thing holding the screen up. **Weigh your finished carrier before you trust the STS3215 sizing.** Over ~400g and the arm geometry needs rethinking, which is cheap now and a two-week teardown in week 9.
3. **A month of printing.** 310 parts, largest at 14h each, starting week 1 in parallel with everything else.

---

# Software (all free)

Chillibasket's Arduino sketch + Python control stack (motion — inherited) ·
Python + asyncio · Chromium kiosk for the screen · `yt-dlp` + `mpv` (video) ·
`opencv` / `picamera2` (camera) · `sqlite` + a local embedding model (retrieval) ·
`pymupdf` + `tesseract` (manual ingest) · Claude API (~$4/month — see `LLM.md`) ·
optional `piper` (local TTS), `openWakeWord` + `vosk` (voice)

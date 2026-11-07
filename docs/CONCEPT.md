# TorQ — The Mechanic's Assistant

**TorQ = torque specs.** A tracked shop assistant with a hinged screen belly, an
articulated head, and a library of your service manuals it can actually cite.

---

## Form (locked)

- **Tracks as feet** — confirmed.
- **Head** — 3 DOF (pan, neck tilt, head tilt). Camera + work light. All the
  movement in the robot lives here.
- **Hinged belly screen** — tilts to your eyeline. Wall-E silhouette preserved.
- **No arms.** No gripper. No scoop.
- **Magnets** for picking up hardware (see below).

### Four servos. That's the whole robot.

| Joint | Count |
|---|---|
| Head pan, neck tilt, head tilt | 3 |
| Belly screen hinge | 1 |
| **Total** | **4** |

Down from 9 → 8 → 6 → **4**. This is now a genuinely buildable machine on a 12-week
clock, and the reclaimed time goes into the manual library, which is the product.

### Dropping the arms improved the lighting

The plan had been "head films, arm lights." With no arms, the light moves onto the
head — and that's **better**, not a compromise. Put a **LED ring around the camera
lens**, coaxial with it. Now the light points exactly where the camera looks, which
is how borescopes and inspection cameras work, and it means aiming the head aims
both at once. One less thing to coordinate.

---

## The magnets

You said magnetic base — there are two different features here and both are worth
having, because both cost zero motors and zero software.

**1. Magnetic parts tray, top deck.** You drop bolts in from standing height without
bending or aiming. Solves a mechanic's actual #1 annoyance: losing fasteners.

**2. Magnet sweeper, underside/front.** A strip of neodymium magnets low at the
front. It drives across the shop floor and collects dropped screws, washers, and
clips. This gives the tracks a *second job* and it is exactly the kind of small
useful thing that makes a robot feel worth having.

Two honest cautions on the sweeper:
- **It will collect swarf.** In a car garage that's fine. Near a grinder or a mill
  it becomes a steel-wool hedgehog. Mount the magnet strip so it's **removable and
  wipeable** — a printed sled that clips off, not magnets bonded into the chassis.
- Give it a **release**: a small lever or sliding plate that pushes the hardware off
  the magnet into your hand. Scraping screws off a bare neodymium strip is annoying
  enough that you'd stop using it. Still zero motors.

---

## The main feature: your manuals, searchable, with the page shown

This is the product. Everything else is support.

> **"TorQ, lug nut torque on a 2015 Civic."**
> Belly screen shows: **80 ft-lb** — and underneath it, *the actual scanned page from
> the service manual*, with the torque table right there.

### The architecture that makes this trustworthy: retrieval first, LLM second

A wrong torque spec means a damaged head or a wheel leaving the car. So the design
rule is:

> **The LLM's job is to find the page, never to be the source of the number.**

Query → find the right manual page → **display the page image**. The language model
sits on top and adds a one-line plain-English answer with its citation. Three things
fall out of this for free:

1. **You can see it's right.** The table is on screen next to the answer.
2. **It works offline.** Retrieval is local. Shop WiFi dies, you still get the page.
   Only the optional summary needs network.
3. **Being wrong is visible, not silent** — the worst failure mode is eliminated by
   construction rather than by prompt engineering.

### How to build it

**Ingest on your laptop, never on the Pi.** This is the important practical call.
OCR and embedding a 400-page scanned manual is slow; do it once on a real computer
and copy the result over. The Pi only ever does lookup and display.

```
laptop:  PDF ──> render each page to PNG (pymupdf)
              ──> extract text; if the page is a scan with no text layer, OCR it
              ──> chunk per page/section, embed (bge-small or all-MiniLM)
              ──> sqlite: {manual, page, text, embedding, png_path}
              ──> rsync the folder to the Pi

TorQ:    query ──> embed locally (MiniLM runs fine on a Pi 5)
              ──> top-k pages by similarity, filtered by vehicle if known
              ──> show the page PNG on the belly, scrolled to the match
              ──> (optional, if online) LLM reads the page text, writes one line
```

**The genuine technical risk is tables.** Torque specs live in tables, and text
extraction mangles table layout badly — this is the part that will eat your time,
not the embedding or the search. Two mitigations, in order:

1. **Show the page image and let the human read the table.** This is why the
   page-first design isn't just safer, it's *easier*. It routes around the hard
   problem entirely.
2. Later, at ingest time, run a vision model over table pages to extract structured
   rows. Nice upgrade. Not v1.

**Storage:** page images add up — a 400-page manual at 150dpi is roughly 400MB, so a
handful of manuals is several GB. **Buy a 256GB card or a USB SSD**, not the 32GB
card that comes in a starter kit. Cheap now, annoying later.

---

## Everything else, in priority order

1. **Manual lookup** — above. The product.
2. **Video playback** — YouTube how-tos and local files on the belly. Use
   **`yt-dlp` + `mpv`**, not an embedded browser player: hardware-decoded, far more
   reliable on a Pi, and it caches so it survives bad shop WiFi.
3. **Timers and counters** — torque sequences (*bolt 3 of 10, criss-cross*), cure
   times, bleed cycles, oil drain. Trivial, useful, works with no internet.
4. **Photo-per-step job log** *(stretch)* — say "photo" at each step of a teardown,
   get a reverse-order gallery for reassembly. Cheap and high value if time allows.
5. **It repositions itself** — comes when called, turns so you can see the screen.

---

## Architecture: the belly is a local web app

Run the screen as a **fullscreen browser pointed at localhost.** Every feature —
manual search, player, timers, job log — is a web page.

Two wins on a 12-week clock:
1. Fast to build and iterate.
2. **The same UI is your phone UI** at `torq.local`. Type the awkward stuff (a query,
   a vehicle) on your phone; read it on the belly.

---

## Voice: yes, addable later — if you buy three things now

You asked whether voice can come later if you tire of prerecorded noises. **Yes.**
But separate two things that get conflated:

| | What it is | Add later? |
|---|---|---|
| **Voice OUT** | It talks to you (vs. Wall-E chirps) | **Yes — pure software** |
| **Voice IN** | You talk to it (wake word + commands) | **Yes — mostly software** |

Both are software swaps with **no mechanical consequence** — *provided the hardware
underneath them exists.* Buy these three now, because they're the parts you can't
retrofit without a teardown:

1. **A decent speaker and amp — not a tiny one.** Beeps and chirps sound fine on a
   cheap 3W speaker. *Speech does not*, especially in a loud shop. If you fit a
   tinny driver now, the day you switch on speech it'll be unintelligible and you'll
   be pulling the robot apart. Buy the better speaker while it's a $5 decision.
2. **A mic mount and wire run in the head** — even if you don't populate it. And
   decide *placement* now: **high on the head, away from the drive motors**, with a
   foam windscreen. A mic buried in a chassis next to servo whine is worthless, and
   moving it later means re-cutting the shell.
3. **The push-to-talk button and its GPIO line.** You already want this as a backup.
   Run it in week 1.

That's about **$20 and one evening of CAD** to keep both doors open. Textbook case of
the buy-cheap-options-early rule.

### Ship the chirps, and don't be in a hurry to replace them

Prerecorded Wall-E noises aren't a placeholder — for personality they're **better
than speech**. Chirps make it a character; a talking robot is a smart speaker with
tracks. Plenty of people ship TTS and regret flattening their robot into Alexa.

The one place speech genuinely earns its place is **reading a spec aloud when you're
under the car and can't see the screen.** If that's the version you want, `piper`
runs locally on a Pi 5, sounds decent, and is roughly a two-day job — so it's on the
*if you're ahead* list, not the cut list. Rule if you add it: it speaks the number
**and** names the source. Never a bare number.

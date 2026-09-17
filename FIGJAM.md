# TorQ — FigJam Sticky Notes

One block = one sticky. Paste a whole column into FigJam and it splits on the blank
lines. Suggested colours in each heading.

---

## Column 1 — WHAT IT IS  *(yellow)*

**TorQ = torque specs**
A small tracked robot that lives in your garage and knows your service manuals.

**Shape**
Wall-E shaped, toolbox sized. Drives to where you're working and tilts its belly screen up to your eyeline.

**The one rule**
It never shows you a number without showing you the page the number came from.

**The demo**
"Lug nut torque, 2015 Civic" → **80 ft-lb**, plus the actual scanned manual page with the table on it.

**The whole machine**
4 servos, 1 screen, 1 camera, 1 magnet. No arms, no gripper, no legs — all cut on purpose.

**Also does**
Lit magnifier for dark engine bays · magnet that sweeps up dropped screws · timers for torque sequences and cure times · plays how-to videos.

**What it is NOT**
Not a mechanic. Not a parts fetcher. Not a chatbot that guesses specs from memory.

---

## Column 2 — WHO IT'S FOR  *(green)*

**Home and independent mechanics**
The person under their own car on a Saturday with no subscription software.

**Me — I'm the customer**
Every design question has an answer I already have. No research phase.

**Anyone whose hands are too dirty to touch a phone or a laptop**

**People sitting on old manuals**
Factory PDFs and scanned paper books nobody has made searchable.

**Shops with bad WiFi**
Core lookup is 100% offline. Only the optional summary needs a connection.

**Not for**
Dealer techs who already have OEM software. Not for people who want a pet robot — it has a face, but it has a job.

---

## Column 3 — HOW IT WORKS  *(blue)*

**1. Load your manuals**
PDFs get processed once on a laptop. Every page becomes a searchable image. The heavy work never runs on the robot.

**2. Ask**
Type on your phone at `torq.local`, tap the belly screen, or speak to it.

**3. Find**
A local search finds the right page. No internet required.

**4. Show**
The page image goes up on the belly screen, answer called out, source named.

**5. Summarise (optional)**
Online, a language model reads *that page* and gives a plain-English answer with a citation to the page number.

**Retrieval first, LLM second**
The model's job is to find the page, never to be the source of the number. Wrong specs must be visible, not silent.

**Offline by default**
Step 5 is the only part that needs internet. Everything under it still works when the shop WiFi drops — which it will.

**The body**
Tracks drive it over. A 3-DOF head aims the camera and its LED ring together. The 4th servo tilts the screen.

**One app, two screens**
The belly is a fullscreen browser on localhost, so the same web app is also the phone UI.

---

## Column 4 — SCOPE & TIMELINE  *(orange)*

**The clock**
12 weeks, hard deadline ~7 Dec 2026. Budget ~$430–445.

**Tier 0 — must ship (week 9)**
Drives under phone teleop, animated head, tilting screen, manual lookup by pure retrieval (no LLM at all), magnifier, magnets, timers, chirps.

**Tier 1 — nice to have (week 10, then freeze)**
Voice commands, YouTube playback, LLM summary line. Each is independently droppable.

**Tier 2 — only if there's slack**
TTS voice, OBD-II, VIN scan, photo-per-step job log.

**Known hard part**
Torque specs live in tables, and text extraction mangles tables. Showing the page image routes around the problem entirely.

**Why not the composting robot**
Two unknown domains stacked, a feedback loop measured in weeks, and I wasn't the customer. A half-finished composter is a bucket. A half-finished TorQ is still a rolling screen that shows you the right page.

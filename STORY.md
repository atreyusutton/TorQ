# TorQ — What It Is, and Why

Canonical copy for the website and for explaining the project to someone new.

---

## What it is (short)

**TorQ is a small tracked robot that lives in your garage and knows your service
manuals.**

Ask it the lug nut torque on a 2015 Civic and it shows you the number — *and the
actual page from the manual it came from* — on a screen in its belly. It's Wall-E
shaped, about the size of a toolbox, and it drives over to where you're working and
tilts its screen up so you can read it from the floor.

## What it is (one more layer)

It has a camera in its head that doubles as a lit magnifier for reading part numbers
in a dark engine bay. It has a magnet on its underside that picks up the screws you
drop. It plays how-to videos on its belly. It runs timers for torque sequences and
cure times. And it has a face, because you're going to be looking at it all day.

## What we're trying to achieve

Every mechanic already has the information they need. It's in a manual on a shelf, a
PDF on a laptop across the shop, or a YouTube video on a phone you can't touch
because your hands are covered in oil.

**TorQ is an attempt to put that information where the work actually happens** — at
arm's length, on the floor, under the car — and make it reachable without clean hands.

The strict rule the whole design is built around: **it never shows you a number
without showing you where the number came from.** A wrong torque spec means a damaged
head or a wheel leaving the car. So TorQ's job isn't to *know* the answer, it's to
*find the page* — and then put that page in front of you so you can see it's right.

---

## Why not the composting trash robot

The first version of this was a Wall-E trash robot that composts. I moved away from
it, and the reason is the most useful thing I've worked out so far.

**A composting robot has to be good at the physical world.** It has to collect
material, handle it, and manage a biological process — moisture, carbon-nitrogen
ratios, thermophilic phases — that I'd have had to research from scratch. That's two
unknown domains stacked on each other: robotics, which I don't know, and composting,
which I also don't know. Picking things up is *also* the single thing that kills
hobby robot projects. Every hard part was a hard part I couldn't shortcut.

**It has no feedback loop.** Compost takes weeks to evaluate. You cannot iterate on
something you can't measure until next month.

**And I'm not the customer.** I couldn't have told you whether a feature was any good.

TorQ inverts all three:

- **I know what a mechanic needs, because I am one.** Every design question has an
  answer I already have. No research phase.
- **The hard problem is knowing things, not handling things** — and knowing things is
  what a small computer is genuinely good at. That one swap deleted the grasping
  problem, the arms, and most of the mechanical risk.
- **The feedback loop is one second.** It either found the right spec or it didn't.

And the part that matters most on a deadline: **a half-finished composter is a
bucket. A half-finished TorQ is still a rolling screen that shows you a manual page.**
It's useful before it's finished.

> **The principle: don't build a robot that solves a problem you'd have to research.
> Build one that solves a problem you have.**

I kept the Wall-E shape. What people love about Wall-E was never the trash.

---

## How it works, in plain terms

1. **You load your manuals.** PDFs — factory service manuals, old scanned books —
   get processed once on a laptop: every page becomes a searchable image.
2. **You ask a question**, by typing on your phone, tapping the belly, or speaking.
3. **TorQ finds the page** using a local search that works with no internet.
4. **It shows you the page**, with the answer called out and the source named.
5. **If it's online**, a language model reads that page and gives you a plain-English
   answer — with a citation pointing at the exact page number it read.

Step 5 is the only part that needs the internet. Everything below it still works when
the shop WiFi drops, which it will.

---

## Where it is now

A three-month build, designed around a hard deadline and a deliberately small
machine: **four motors, one screen, one camera, one magnet.** No arms, no gripper,
no legs — every one of those was considered and cut on purpose, because the things
that kill projects like this are moving parts and problems you haven't solved before.

The floor it has to hit — the version that ships even if everything optional falls
over — is a robot that drives, tilts its screen up at you, and shows you the right
page of your manual. Everything past that is upside.

# TorQ — The LLM Layer

**Priority: first thing after the MVP lands.** Tier 1a, ahead of voice and YouTube.

Verified against the bundled `claude-api` skill (models/pricing cached 2026-06-24).
Language is Python, matching the rest of `torq/`.

---

## The finding that changes the design: native citations

The Messages API has **built-in citations** for documents. Enable them on a document
block and the response comes back split into text blocks, each carrying a `citations`
array with `cited_text` and — for PDFs — a **`page_location` with
`start_page_number` / `end_page_number`**.

That is *exactly* the requirement we set for this product:

> Never display a spec without its source.

We were going to hand-roll that. We don't have to. The model returns the page number
it read the number off, and TorQ renders that page image on the belly. The citation
isn't something we ask the model to produce in prose and hope it's honest about —
it's a structured field.

**This makes the safety property mechanical rather than aspirational**, which is the
whole reason the manual feature is worth building at all.

---

## Architecture: two different LLM calls, doing two different jobs

### Call 1 — Ingest (laptop, once per manual, offline)

Extract torque tables into structured rows. Uses **structured outputs** so the JSON
is schema-valid by construction.

```python
import anthropic, json
client = anthropic.Anthropic()

TORQUE_SCHEMA = {
    "type": "object",
    "properties": {
        "specs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "fastener":  {"type": "string"},
                    "value":     {"type": "number"},
                    "unit":      {"type": "string", "enum": ["ft-lb", "in-lb", "Nm"]},
                    "stage":     {"type": "string"},
                    "notes":     {"type": "string"},
                    "page":      {"type": "integer"},
                },
                "required": ["fastener", "value", "unit", "page"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["specs"],
    "additionalProperties": False,
}

resp = client.messages.create(
    model="claude-opus-5",
    max_tokens=16000,
    thinking={"type": "adaptive"},
    output_config={"format": {"type": "json_schema", "schema": TORQUE_SCHEMA}},
    messages=[{"role": "user", "content": [
        {"type": "document",
         "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64}},
        {"type": "text", "text": "Extract every torque specification in this section."},
    ]}],
)
specs = json.loads(next(b.text for b in resp.content if b.type == "text"))["specs"]
```

This is where the LLM earns the most, and it's the **safest** place to use one:
the output is a table you can eyeball once against the manual page, and then it's
trustworthy forever. Far better than a model improvising a number at query time.

**Run it through the Batch API** — ingest is not latency-sensitive, and batches are
**50% off**. `client.messages.batches.create(requests=[{custom_id, params}, ...])`,
poll until `processing_status == "ended"`, then key results by `custom_id`
(they come back in any order).

### Call 2 — Query (on the robot, per lookup, online)

Retrieve candidate pages locally, then send **only those pages** with citations on.

```python
resp = client.messages.create(
    model="claude-opus-5",
    max_tokens=1024,
    thinking={"type": "adaptive"},
    output_config={"effort": "medium"},
    system="Answer only from the provided manual pages. If the spec is not present, say so.",
    messages=[{"role": "user", "content": [
        {"type": "document",
         "source": {"type": "base64", "media_type": "application/pdf", "data": page_pdf_b64},
         "title": "2015 Civic Service Manual",
         "citations": {"enabled": True}},
        {"type": "text", "text": "What is the wheel lug nut torque?"},
    ]}],
)

for block in resp.content:
    if block.type == "text":
        for c in getattr(block, "citations", None) or []:
            # c.cited_text, c.document_title, c.start_page_number
            show_manual_page(c.start_page_number)
```

**Gotcha, verified:** citations are **incompatible with `output_config.format`** —
using both returns a 400. That's fine here because they're two separate calls with
two separate jobs: ingest gets structured output, query gets citations. Don't try to
merge them.

---

## What this costs (real numbers, not vibes)

Pricing from the skill's cached table: **Claude Opus 5 — $5/M input, $25/M output.**

| | Tokens | Cost |
|---|---|---|
| **One spec lookup** | ~2,000 in / ~150 out | **~$0.014** |
| 10 lookups/day, a month | | **~$4/month** |
| 20 lookups/day, a month | | **~$8/month** |
| **Ingesting one manual** (~80 table pages, vision) | ~160K in / ~32K out | ~$1.60 |
| Same, **via Batch API (-50%)** | | **~$0.80, one time** |

So: **under five dollars a month to run, under a dollar per manual to load.** The
LLM being "built in" is not a cost problem at this volume — build it the way you
want it and don't compromise the design to save cents.

*(These are Anthropic first-party API rates. Model IDs are complete as written —
`claude-opus-5`, never with a date suffix appended.)*

---

## The offline story — and why it's good

The Pi will sometimes have no WiFi. That's a garage.

**Do not** try to solve this with a local LLM on the Pi. A 3-4B model quantized on a
Pi 5 must first read a full page of OCR text, and prompt processing is the bottleneck
— realistically **30-60 seconds per answer**. That's unusable for something you ask
while holding a wrench, and it's a lot of work to get there.

The good answer is the architecture you already have:

| State | What happens |
|---|---|
| **Online** | Full path — retrieval + LLM answer with page citations |
| **Offline** | The **pre-extracted structured spec table** from ingest. Instant lookup, no model, no network |
| **Offline, nothing matches** | Show the retrieved manual **page image**. Retrieval is local |

Offline mode is *faster* than online mode, because it's a database query. The LLM
adds natural-language understanding and edge cases, not the baseline capability.
Nothing degrades to broken.

---

## Build it behind one interface

```python
class SpecProvider(Protocol):
    def lookup(self, query: str, vehicle: Vehicle | None) -> SpecAnswer: ...
```

Three implementations — `LocalTableProvider` (offline, no model),
`ClaudeProvider` (the real one), and `NullProvider` (MVP, retrieval only, ships in
Tier 0). The robot picks at runtime based on connectivity.

This is the software equivalent of the buy-the-option rule: **the MVP ships with
`NullProvider` and nothing about it is throwaway.** Adding the LLM later is
registering a different implementation, not a rewrite. That's precisely what "LLM
first after MVP" needs to be cheap.

---

## Where this sits in the plan

| | |
|---|---|
| **Tier 0 (wk 9)** | Retrieval only. Type a query, get the manual page. `NullProvider`. |
| **Tier 1a (wk 10)** | **LLM lookup with native citations.** ← first thing after MVP |
| **Tier 1b** | Voice commands |
| **Tier 1c** | YouTube |

Ingest-time extraction is **laptop work with no hardware dependency**, so it can
start any time from week 2 onward and doesn't consume robot schedule at all.

---

## Later, if you want it: the diagnostic assistant

Once the manual library, OBD-II, and the camera exist, the pieces are in place for
something genuinely useful: *"it cranks but won't catch, here's the code I pulled."*
Claude reasons over the trouble code, the relevant manual pages, and your
description, and shows you the diagnostic tree page.

That's the real destination, and it's reachable **because** the boring parts —
ingested manuals, cited pages, a code reader — got built first. Not a v1 goal.

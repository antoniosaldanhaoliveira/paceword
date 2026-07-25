---
name: pt-property-market-scan
description: Run the daily/weekly Portuguese property market sweep for a buyer — define the search strategy (property type, 15–20 km zone, purpose), build and refresh saved-search URLs across Idealista, Imovirtual, Casa Sapo, OLX and Facebook Marketplace, harvest new listings and price drops, and study €/m² patterns for an area. Use this skill whenever the user mentions searching, monitoring, scanning or "checking alerts" for property, land, plots, terrenos, quintas, ruins or houses in Portugal, asks what a zone costs per square meter, asks to set up or tune property alerts, or asks for today's/this week's new listings — even if they don't name a portal. Also use it when starting a new property search and no buyer profile exists yet.
---

# Portuguese Property Market Scan

This skill runs the research loop that separates buyers who spot underpriced
property from buyers who scroll aimlessly: a narrow, fixed search zone, watched
consistently, with every listing recorded so you learn the market's rhythm.

The single most important idea: **the value comes from repetition inside a small
area, not from casting a wide net.** A buyer who has seen every plot within 15 km
for two months can price a new listing in ten seconds. Keep the user focused on
that, and push back gently when they want to add a fifth region before they know
the first one.

## Workflow

### 1. Load or create the buyer profile

The profile drives everything else. It lives at `$PROPERTY_WORKSPACE/profile.yaml`
(default workspace: `~/property-portugal/`). If it does not exist, create it from
`references/profile-template.yaml` by interviewing the user — but only ask what
you actually need, and offer sensible defaults rather than making them fill in a
form.

A profile holds one or more **named searches**. Each search is a separate zone
with its own property types, budget and €/m² baseline:

```bash
python scripts/build_search_urls.py --profile ... --list          # what exists
python scripts/build_search_urls.py --profile ... --search algarve-plots
```

Running several searches in parallel is fine and often sensible — plots in the
Algarve and ruins in Alentejo are genuinely different markets and a buyer may
want both. What does not work is a single wide search: the method's edge comes
from the depth of one small area, and a 100 km "zone" produces a median that
describes nowhere.

So when the user wants more coverage, add a second *narrow* search rather than
widening an existing one. Be honest about the cost, though — each search needs
its own 60–80 listings before its numbers mean anything, so three searches is
three times the runway, not three times the coverage. Two or three active at once
is realistic; six is a way of never finishing any of them. Searches can be paused
with `active: false` without losing their history.

The three decisions that matter for each search, from the guide:

- **Property type** — one or two, not seven. Urban land, rustic land,
  house/apartment, ruin, tourism land, modular. Each has a completely different
  due-diligence path, so a buyer chasing all of them learns none of them.
- **Geographic zone** — one anchor town plus a 15–20 km radius. If the user names
  a whole region ("the Algarve", "Alentejo"), narrow it to concelhos/freguesias
  before searching; otherwise the €/m² statistics you build later are noise.
- **Purpose** — living, renting, tourism, or building. This decides which red
  flags are fatal versus tolerable. A north-facing slope is a minor annoyance for
  a farm and a serious problem for a house you plan to live in.

Also capture: budget range (and whether it is price-in-hand or includes taxes and
works), minimum land/built area, and any absolute deal-breakers.

### 2. Build the search URLs

Run `scripts/build_search_urls.py` against the profile. It emits one saved-search
URL per portal per search, with that search's filters applied:

```bash
python scripts/build_search_urls.py --profile $PROPERTY_WORKSPACE/profile.yaml
python scripts/build_search_urls.py --profile ... --search alentejo-ruins
python scripts/build_search_urls.py --profile ... --portal idealista --format markdown
```

Tell the user to name each portal alert after its search. With two or three
searches running, unlabelled alert mail becomes an undifferentiated stream and
the sorting cost is what makes people stop reading it.

Portal-specific slugs, filter parameters and quirks are documented in
`references/portals.md` — read it before hand-editing any URL, because each site
encodes location differently (Idealista uses geographic slugs, Casa Sapo uses
district paths, OLX uses category + region IDs).

**Set up the email alerts.** This is the intake channel the guide recommends and
it is also the intake channel that keeps you on the right side of the portals'
terms of service. Give the user the URLs, and tell them to create the saved
search + daily email alert on each portal while logged in. Automated bulk
scraping of Idealista is against its terms and gets IP-blocked quickly; the alert
emails and the listing pages the user actually opens are the reliable path.

Cross-check portals in this order of yield: Idealista (broadest), Imovirtual,
Casa Sapo, then OLX and Facebook Marketplace — the last two are where private
owners with no agent post, which is exactly where rural bargains hide and where
listing quality is worst.

### 3. Harvest new listings

Each run, collect the day's candidates from whatever intake the user has:

- Alert emails or listing links they paste
- Listing pages fetched individually with WebFetch (one at a time, at human pace)
- `WebSearch` for the area when you want breadth rather than a specific portal

For each listing, extract the fields in `references/listing-fields.md` and write
them as JSON, then hand off to the **pt-property-tracker** skill to record them
with `ingest --search <name>` so it lands in the right baseline. Sweep with
`--search <name>` too — a sweep without it speaks for every search at once and
will mark the other searches' listings as disappeared.
Do not invent values you could not read — leave a field null and note it. A
guessed plot size silently corrupts every €/m² average you compute afterwards.

Two extractions are worth the effort even though they take a moment:

- **Price per m²** — of *land* for plots, of *built area* for houses. Keep them in
  separate columns; mixing them is the most common way a buyer convinces
  themselves something is cheap.
- **The listing's own contradictions** — description says "with ruin" but the
  documents section says rustic with no building; says "buildable" but gives no
  construction index. These contradictions are the guide's core warning about
  agents relaying unverified owner claims, and they are the highest-signal thing
  in a listing.

### 4. Study the market

After roughly 20–30 listings in a zone, run the statistics (the tracker skill's
`stats` command) and interpret rather than dump numbers:

- The median €/m² for the zone, split by property type
- Where the new listing sits against that median
- What has been sitting unsold for 90+ days, and what disappeared within a week —
  the first tells you the ceiling, the second tells you the real market price

Spread this over days. The guide is explicit that concentrated binge research
produces fatigue and anchoring bias; a listing looks cheap mostly because of what
you looked at immediately before it.

### 5. Produce the run output

End every scan with a short digest, not a table dump. With several searches
active, give each its own section and lead with whichever one actually has
something in it — a fixed order buries the interesting search behind the quiet
one on most days:

```markdown
## Property scan — {date} — {search name} — {zone}

**New since last run:** {n}   **Price drops:** {n}   **Disappeared:** {n}

### Worth your attention
1. {title} — €{price} ({€/m²}) — {one line on why it stands out vs the zone median}
   {url}
   ⚠ {any contradiction or red flag spotted}

### Price drops
- {title}: €{old} → €{new} ({pct}%, {days} days on market) — {negotiation read}

### Market note
{one or two sentences on what shifted in the zone, or "nothing material"}
```

Rank by deviation from the zone median adjusted for the profile's deal-breakers —
not by raw cheapness. The cheapest plot in a zone is usually cheap for a reason
that shows up later in due diligence.

### 6. Keep it consistent

The guide's real key is doing this for 2–3 months. Each run, note the streak and
how many listings each zone has accumulated (`tracker.py searches` gives the
overview). Around 60–80 tracked listings in one zone, tell the user they have
crossed into "you can now price this area yourself" territory — that milestone is
the whole point of the exercise, and it is worth naming when they reach it.

With several searches running, watch for one going stale: if a search has
produced nothing new for weeks, either its filters are too tight or its market is
genuinely thin. Say which you think it is and offer to loosen the budget, widen
the type, or pause it — quietly scanning a dead zone every morning is how the
whole habit starts to feel pointless.

When a listing survives this stage and the user wants to go further, hand off to
the **pt-property-due-diligence** skill before they visit or make an offer.

## Visit logging

When the user visits properties, capture notes into the tracker rather than
letting them evaporate: what the agent said (and whether it contradicts the
documents), access condition, neighbours, noise, orientation checked on site,
and photos' location. The guide's point about visits is that they build intuition
and a local agent network — so also record which agent showed it, because
off-market deals come through those relationships later.

## Reference files

- `references/portals.md` — per-portal URL structure, filters, quirks, yield
- `references/profile-template.yaml` — the buyer profile schema, commented
- `references/listing-fields.md` — the fields to extract from every listing

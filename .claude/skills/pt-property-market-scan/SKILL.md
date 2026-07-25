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

The three decisions that matter, from the guide:

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
URL per portal with the profile's filters applied:

```bash
python scripts/build_search_urls.py --profile ~/property-portugal/profile.yaml
python scripts/build_search_urls.py --profile ... --portal idealista --format markdown
```

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
them as JSON, then hand off to the **pt-property-tracker** skill to record them.
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

End every scan with a short digest, not a table dump:

```markdown
## Property scan — {date} — {zone}

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
how many listings the zone has accumulated. Around 60–80 tracked listings in one
zone, tell the user they have crossed into "you can now price this area yourself"
territory — that milestone is the whole point of the exercise, and it is worth
naming when they reach it.

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
